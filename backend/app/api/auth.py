# app/api/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import verify_password, get_password_hash, create_access_token
from app.config import settings
from app.schemas.user import UserCreate, User, Token, UserLogin, UserProfileUpdate, PasswordChange
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

@router.get("/me")
async def get_current_user_info(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user information with profile data"""
    # Convert user to dict
    user_dict = {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role.value if hasattr(current_user.role, 'value') else current_user.role,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
        "language_preference": current_user.language_preference,
        "timezone": current_user.timezone,
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
    }
    
    # Add teacher_profile if exists
    if current_user.teacher_profile:
        user_dict["teacher_profile"] = {
            "id": current_user.teacher_profile.id,
            "full_name": current_user.teacher_profile.full_name,
            "school": current_user.teacher_profile.school,
            "profile_image_url": current_user.teacher_profile.profile_image_url,
        }
    else:
        user_dict["teacher_profile"] = None
    
    # Add student_profile if exists
    if current_user.student_profile:
        user_dict["student_profile"] = {
            "id": current_user.student_profile.id,
            "teacher_id": current_user.student_profile.teacher_id,
            "full_name": current_user.student_profile.full_name,
            "grade": current_user.student_profile.grade,
            "difficulty_level": current_user.student_profile.difficulty_level,
            "difficulties_description": current_user.student_profile.difficulties_description,
            "profile_image_url": current_user.student_profile.profile_image_url,
        }
    else:
        user_dict["student_profile"] = None
    
    return user_dict

@router.post("/logout")
async def logout():
    """Logout endpoint (for frontend to clear tokens)"""
    # In a JWT-based system, logout is handled client-side
    # This endpoint exists for frontend convenience
    return {"message": "Logged out successfully"}

@router.put("/profile", response_model=User)
async def update_profile(
    profile_data: UserProfileUpdate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile information"""
    
    # Check if email is already taken by another user
    if profile_data.email and profile_data.email != current_user.email:
        existing_user = db.query(UserModel).filter(
            UserModel.email == profile_data.email,
            UserModel.id != current_user.id
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered by another user"
            )
        
        # Update user email
        current_user.email = profile_data.email
    
    # Update profile based on role
    if current_user.role == UserRole.STUDENT and current_user.student_profile:
        if profile_data.full_name:
            current_user.student_profile.full_name = profile_data.full_name
    elif current_user.role == UserRole.TEACHER and current_user.teacher_profile:
        if profile_data.full_name:
            current_user.teacher_profile.full_name = profile_data.full_name
    
    db.commit()
    db.refresh(current_user)
    
    return current_user

@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    
    # Verify old password
    if not verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=400,
            detail="Incorrect password"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    
    return {"message": "Password updated successfully"}

@router.get("/teachers")
async def get_available_teachers(db: Session = Depends(get_db)):
    """Get list of available teachers for student registration"""
    
    teachers = db.query(UserModel).filter(
        UserModel.role == UserRole.TEACHER,
        UserModel.is_active == True
    ).all()
    
    return [
        {
            "id": teacher.id,
            "username": teacher.username,
            "full_name": teacher.teacher_profile.full_name if teacher.teacher_profile else teacher.username,
            "school": teacher.teacher_profile.school if teacher.teacher_profile else None
        }
        for teacher in teachers
    ]