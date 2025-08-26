# app/api/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.config import settings
from app.schemas.user import UserCreate, User, Token, UserLogin
from app.models.user import User as UserModel, UserRole, TeacherProfile, StudentProfile

router = APIRouter()

@router.post("/register", response_model=User)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user (student or teacher)"""
    
    # Check if user exists
    existing_user = db.query(UserModel).filter(
        (UserModel.username == user_data.username) | 
        (UserModel.email == user_data.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username or email already registered"
        )
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    db_user = UserModel(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        role=user_data.role,
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create profile based on role
    if user_data.role == UserRole.TEACHER:
        teacher_profile = TeacherProfile(
            user_id=db_user.id,
            full_name=user_data.full_name,
            school=user_data.school
        )
        db.add(teacher_profile)
    elif user_data.role == UserRole.STUDENT:
        # Find teacher if specified
        teacher_id = None
        if user_data.teacher_username:
            teacher_user = db.query(UserModel).filter(
                UserModel.username == user_data.teacher_username,
                UserModel.role == UserRole.TEACHER
            ).first()
            
            if not teacher_user:
                # Rollback user creation if teacher not found
                db.delete(db_user)
                db.commit()
                raise HTTPException(
                    status_code=404,
                    detail=f"Teacher with username '{user_data.teacher_username}' not found"
                )
            
            if teacher_user.teacher_profile:
                teacher_id = teacher_user.teacher_profile.id
        
        student_profile = StudentProfile(
            user_id=db_user.id,
            teacher_id=teacher_id,
            full_name=user_data.full_name,
            grade=user_data.grade,
            difficulty_level=user_data.difficulty_level or 3,
            difficulties_description=user_data.difficulties_description
        )
        db.add(student_profile)
    
    db.commit()
    return db_user

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    """Login with username and password"""
    
    # Find user
    user = db.query(UserModel).filter(UserModel.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value}, 
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer"
    }

@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: UserModel = Depends(get_current_user)
):
    """Get current user information"""
    return current_user

@router.post("/logout")
async def logout():
    """Logout endpoint (for frontend to clear tokens)"""
    # In a JWT-based system, logout is handled client-side
    # This endpoint exists for frontend convenience
    return {"message": "Logged out successfully"}

@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    
    # Verify old password
    if not verify_password(old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=400,
            detail="Incorrect password"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(new_password)
    db.commit()
    
    return {"message": "Password updated successfully"}