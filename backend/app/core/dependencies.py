from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_token
from app.models.user import User
from app.schemas.user import UserRole

# HTTP Bearer token scheme
security = HTTPBearer()


def get_current_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Get the current authenticated user.
    
    Args:
        db: Database session
        credentials: HTTP Bearer credentials
    
    Returns:
        Current user object
    
    Raises:
        HTTPException: If user is not found or token is invalid
    """
    token = credentials.credentials
    user_id = verify_token(token)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current active user.
    
    Args:
        current_user: Current user from get_current_user
    
    Returns:
        Current active user
    
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def get_current_teacher(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get the current user if they are a teacher.
    
    Args:
        current_user: Current active user
    
    Returns:
        Current teacher user
    
    Raises:
        HTTPException: If user is not a teacher
    """
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Teacher role required."
        )
    return current_user


def get_current_student(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get the current user if they are a student.
    
    Args:
        current_user: Current active user
    
    Returns:
        Current student user
    
    Raises:
        HTTPException: If user is not a student
    """
    if current_user.role not in [UserRole.STUDENT, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Student role required."
        )
    return current_user


def get_current_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get the current user if they are an admin.
    
    Args:
        current_user: Current active user
    
    Returns:
        Current admin user
    
    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin role required."
        )
    return current_user


def get_optional_current_user(
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    )
) -> Optional[User]:
    """
    Get the current user optionally (no error if no token provided).
    
    Args:
        db: Database session
        credentials: Optional HTTP Bearer credentials
    
    Returns:
        Current user object or None
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        user_id = verify_token(token)
        user = db.query(User).filter(User.id == user_id).first()
        return user if user and user.is_active else None
    except HTTPException:
        return None
