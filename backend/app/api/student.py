from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User, UserRole
from app.models.chat import ChatSession

router = APIRouter()

@router.get("/profile")
async def get_student_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current student's profile"""
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "user": current_user,
        "profile": current_user.student_profile
    }

@router.get("/sessions")
async def get_my_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all chat sessions for current student"""
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Access denied")
    
    sessions = db.query(ChatSession).filter(
        ChatSession.student_id == current_user.student_profile.id
    ).all()
    
    return sessions