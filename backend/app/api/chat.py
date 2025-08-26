# app/api/chat.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas import chat as chat_schemas
from app.services import chat_service, ocr_service
from app.models.user import User
import base64

router = APIRouter()

@router.post("/sessions", response_model=chat_schemas.ChatSession)
async def create_chat_session(
    session_data: chat_schemas.ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new chat session"""
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can create chat sessions")
    
    return chat_service.create_session(
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