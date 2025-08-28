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
    
    # Admin can create sessions for testing - use first student as proxy
    if current_user.role == UserRole.ADMIN:
        # Find any student for admin testing
        from app.models.user import StudentProfile
        test_student = db.query(StudentProfile).first()
        if not test_student:
            raise HTTPException(status_code=400, detail="No students available for admin testing")
        
        return await chat_service.create_session(
            db=db,
            student_id=test_student.id,
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
        assistance_type=message.assistance_type
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
    
    # Save task and process with AI
    task = await chat_service.process_task_image(
        db=db,
        session_id=session_id,
        student_id=current_user.student_profile.id,
        image_data=content,
        extracted_text=extracted_text
    )
    
    return {
        "task_id": task.id,
        "extracted_text": extracted_text,
        "message": "Task uploaded successfully. How can I help you with this?"
    }

@router.post("/messages/{message_id}/rate")
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

@router.post("/call-teacher/{session_id}")
async def call_teacher(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a help request to the teacher"""
    return await chat_service.call_teacher(
        db=db,
        session_id=session_id,
        student_id=current_user.student_profile.id
    )

# ===== ADMIN TESTING & MANAGEMENT ENDPOINTS =====
# Full control for project manager testing and monitoring

@router.get("/admin/all-sessions")
async def get_all_sessions_admin(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Admin: Get ALL chat sessions across all students for testing/monitoring"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    from app.models.chat import ChatSession
    from app.models.user import StudentProfile
    
    sessions = db.query(ChatSession).join(
        StudentProfile, ChatSession.student_id == StudentProfile.id
    ).all()
    
    return [
        {
            "session_id": session.id,
            "student_id": session.student_id,
            "student_name": session.student.full_name if session.student else "Unknown",
            "mode": session.mode,
            "started_at": session.started_at,
            "ended_at": session.ended_at,
            "is_active": session.ended_at is None,
            "message_count": len(session.messages) if session.messages else 0
        }
        for session in sessions
    ]

@router.get("/admin/session/{session_id}/full-log")
async def get_session_full_log_admin(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Admin: Get complete session log including all messages for testing/analysis"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    from app.models.chat import ChatSession, ChatMessage
    
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at).all()
    
    return {
        "session": {
            "id": session.id,
            "student_id": session.student_id,
            "student_name": session.student.full_name if session.student else "Unknown",
            "mode": session.mode,
            "started_at": session.started_at,
            "ended_at": session.ended_at
        },
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "assistance_type": msg.assistance_type,
                "created_at": msg.created_at,
                "response_time_seconds": msg.response_time_seconds
            }
            for msg in messages
        ],
        "total_messages": len(messages)
    }

@router.post("/admin/impersonate-student/{student_id}/session")
async def create_session_as_student_admin(
    student_id: int,
    session_data: chat_schemas.ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Admin: Create a session impersonating a specific student for testing"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Verify student exists
    from app.models.user import StudentProfile
    student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    return await chat_service.create_session(
        db=db,
        student_id=student_id,
        mode=session_data.mode
    )

@router.get("/admin/system-status")
async def get_system_status_admin(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Admin: Get comprehensive system status for monitoring"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    from app.models.user import User, StudentProfile, TeacherProfile
    from app.models.chat import ChatSession
    from app.ai.multi_llm_manager import multi_llm_manager
    
    # Count users
    total_users = db.query(User).count()
    total_students = db.query(StudentProfile).count()
    total_teachers = db.query(TeacherProfile).count()
    
    # Count sessions
    total_sessions = db.query(ChatSession).count()
    active_sessions = db.query(ChatSession).filter(ChatSession.ended_at.is_(None)).count()
    
    # LLM status
    llm_providers = multi_llm_manager.get_available_providers()
    
    return {
        "users": {
            "total": total_users,
            "students": total_students,
            "teachers": total_teachers,
            "admins": total_users - total_students - total_teachers
        },
        "sessions": {
            "total": total_sessions,
            "active": active_sessions,
            "completed": total_sessions - active_sessions
        },
        "llm": {
            "active_provider": multi_llm_manager.active_provider,
            "available_providers": llm_providers,
            "total_providers": len(llm_providers)
        },
        "system": {
            "status": "operational",
            "backend_version": "1.0.0"
        }
    }