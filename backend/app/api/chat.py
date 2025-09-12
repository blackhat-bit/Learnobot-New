# app/api/chat.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas import chat as chat_schemas
from app.services import chat_service, ocr_service
from app.models.user import User, UserRole
import base64

router = APIRouter()

@router.post("/sessions", response_model=chat_schemas.ChatSession)
async def create_chat_session(
    session_data: chat_schemas.ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new chat session - Students and Admins allowed"""
    
    # Admin can create sessions for testing - create virtual admin student profile
    if current_user.role == UserRole.ADMIN:
        from app.models.user import StudentProfile
        
        # Check if admin already has a virtual student profile
        admin_student_profile = db.query(StudentProfile).filter(
            StudentProfile.user_id == current_user.id
        ).first()
        
        if not admin_student_profile:
            # Create virtual student profile for admin testing
            admin_student_profile = StudentProfile(
                user_id=current_user.id,
                full_name=f"Admin Testing ({current_user.username})",
                grade="Admin",
                difficulty_level=5,  # Advanced level for admin
                difficulties_description="Admin testing account"
            )
            db.add(admin_student_profile)
            db.commit()
            db.refresh(admin_student_profile)
        
        return await chat_service.create_session(
            db=db,
            student_id=admin_student_profile.id,
            mode=session_data.mode
        )
    
    # Regular student flow
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Only students and admins can create chat sessions")
    
    if not current_user.student_profile:
        raise HTTPException(status_code=400, detail="Student profile not found")
    
    return await chat_service.create_session(
        db=db,
        student_id=current_user.student_profile.id,
        mode=session_data.mode
    )

@router.post("/sessions/{session_id}/messages", response_model=chat_schemas.ChatMessage)
async def send_message(
    session_id: int,
    message: chat_schemas.ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message in a chat session and get AI response"""
    return await chat_service.process_message(
        db=db,
        session_id=session_id,
        user_id=current_user.id,
        message=message.content,
        assistance_type=message.assistance_type,
        provider=message.provider
    )

@router.post("/sessions/{session_id}/upload-task")
async def upload_task(
    session_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload an image of a task for OCR processing"""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Read file content
    content = await file.read()
    
    # Process with OCR
    extracted_text = await ocr_service.extract_text(content)
    
    # Process with Hebrew mediation if text was extracted successfully
    if extracted_text and not extracted_text.startswith("לא הצלחתי") and not extracted_text.startswith("שגיאה"):
        # Save task
        task = await chat_service.process_task_image(
            db=db,
            session_id=session_id,
            student_id=current_user.student_profile.id,
            image_data=content,
            extracted_text=extracted_text
        )
        
        # Process extracted text through Hebrew mediation system
        ai_response = await chat_service.process_message(
            db=db,
            session_id=session_id,
            user_id=current_user.id,
            message=f"זהו הטקסט מהתמונה: {extracted_text}",
            assistance_type=None,  # Trigger Hebrew mediation
            provider=None
        )
        
        return {
            "task_id": task.id,
            "extracted_text": extracted_text,
            "ai_response": ai_response.content,
            "message": "קראתי את התמונה בהצלחה!"
        }
    else:
        # OCR failed, return error message  
        return {
            "task_id": None,
            "extracted_text": extracted_text,
            "ai_response": None,
            "message": extracted_text
        }

@router.put("/messages/{message_id}/rate")
async def rate_message(
    message_id: int,
    rating_data: chat_schemas.RatingSatisfaction,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rate an AI response"""
    return chat_service.rate_message(
        db=db,
        message_id=message_id,
        rating=rating_data.rating,
        user_id=current_user.id
    )

@router.post("/sessions/{session_id}/end")
async def end_chat_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """End a chat session"""
    
    # Check if session exists and user has access
    from app.models.chat import ChatSession
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check permissions
    if current_user.role == UserRole.ADMIN:
        # Admin can end any session
        pass
    elif current_user.role == UserRole.STUDENT:
        # Student can only end their own sessions
        if not current_user.student_profile or session.student_id != current_user.student_profile.id:
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        raise HTTPException(status_code=403, detail="Only students and admins can end sessions")
    
    # End the session
    await chat_service.end_session(db=db, session_id=session_id)
    
    return {"message": "Session ended successfully"}

@router.post("/call-teacher/{session_id}")
async def call_teacher(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a help request to the teacher"""
    
    # Handle admin users - they can call teacher for any session (including their own)
    if current_user.role == UserRole.ADMIN:
        # Get the session to find the student (could be admin's own virtual profile)
        from app.models.chat import ChatSession
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        student_id = session.student_id
    else:
        # Regular student flow
        if current_user.role != UserRole.STUDENT:
            raise HTTPException(status_code=403, detail="Only students and admins can call teachers")
        
        if not current_user.student_profile:
            raise HTTPException(status_code=400, detail="Student profile not found")
        
        student_id = current_user.student_profile.id
    
    return await chat_service.call_teacher(
        db=db,
        session_id=session_id,
        student_id=student_id
    )

