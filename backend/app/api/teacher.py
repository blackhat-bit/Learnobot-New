from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User, UserRole, StudentProfile
from app.models.chat import ChatSession, ChatMessage

router = APIRouter()

@router.get("/students")
async def get_students(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all students assigned to this teacher"""
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(status_code=403, detail="Access denied")
    
    students = db.query(StudentProfile).filter(
        StudentProfile.teacher_id == current_user.teacher_profile.id
    ).all()
    
    return students

@router.get("/students/{student_id}/sessions")
async def get_student_sessions(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all chat sessions for a specific student"""
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Verify student belongs to teacher
    student = db.query(StudentProfile).filter(
        StudentProfile.id == student_id,
        StudentProfile.teacher_id == current_user.teacher_profile.id
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    sessions = db.query(ChatSession).filter(
        ChatSession.student_id == student_id
    ).all()
    
    return sessions

@router.get("/notifications")
async def get_teacher_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get pending help requests from students"""
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # In a real implementation, you'd have a notifications table
    # For now, return mock data
    return {
        "notifications": [],
        "message": "No pending help requests"
    }