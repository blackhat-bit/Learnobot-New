# app/api/upload.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pathlib import Path
import shutil
import uuid
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User, UserRole, TeacherProfile, StudentProfile
from app.config import settings

router = APIRouter()

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads/profile_pictures")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Allowed file extensions and max file size
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def validate_image_file(file: UploadFile) -> bool:
    """Validate uploaded image file"""
    # Check file extension
    file_extension = Path(file.filename or "").suffix.lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check file size (FastAPI doesn't provide content-length reliably, so we'll check during read)
    return True

def save_upload_file(file: UploadFile, destination: Path) -> None:
    """Save uploaded file to destination"""
    try:
        with destination.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    finally:
        file.file.close()

@router.post("/profile-picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload profile picture for current user"""
    
    # Validate file
    validate_image_file(file)
    
    # Check file size
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 5MB")
    
    try:
        # Generate unique filename
        file_extension = Path(file.filename or "").suffix.lower()
        unique_filename = f"{current_user.id}_{uuid.uuid4().hex}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename
        
        # Save file
        save_upload_file(file, file_path)
        
        # Update user profile with image URL
        image_url = f"/uploads/profile_pictures/{unique_filename}"
        
        if current_user.role == UserRole.TEACHER:
            teacher_profile = db.query(TeacherProfile).filter(
                TeacherProfile.user_id == current_user.id
            ).first()
            if teacher_profile:
                # Remove old profile picture if exists
                if teacher_profile.profile_image_url:
                    old_file = UPLOAD_DIR / Path(teacher_profile.profile_image_url).name
                    if old_file.exists():
                        old_file.unlink()
                
                teacher_profile.profile_image_url = image_url
        
        elif current_user.role == UserRole.ADMIN:
            # Admins use teacher profile for management interface
            teacher_profile = db.query(TeacherProfile).filter(
                TeacherProfile.user_id == current_user.id
            ).first()
            if teacher_profile:
                # Remove old profile picture if exists
                if teacher_profile.profile_image_url:
                    old_file = UPLOAD_DIR / Path(teacher_profile.profile_image_url).name
                    if old_file.exists():
                        old_file.unlink()
                
                teacher_profile.profile_image_url = image_url
        
        elif current_user.role == UserRole.STUDENT:
            student_profile = db.query(StudentProfile).filter(
                StudentProfile.user_id == current_user.id
            ).first()
            if student_profile:
                # Remove old profile picture if exists
                if student_profile.profile_image_url:
                    old_file = UPLOAD_DIR / Path(student_profile.profile_image_url).name
                    if old_file.exists():
                        old_file.unlink()
                
                student_profile.profile_image_url = image_url
        
        else:
            # Clean up uploaded file since user role is not supported
            file_path.unlink()
            raise HTTPException(status_code=403, detail="Only students, teachers, and admins can upload profile pictures")
        
        db.commit()
        
        return {
            "message": "Profile picture uploaded successfully",
            "image_url": image_url,
            "filename": unique_filename
        }
        
    except Exception as e:
        db.rollback()
        # Clean up uploaded file if database operation failed
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to upload profile picture: {str(e)}")

@router.delete("/profile-picture")
async def delete_profile_picture(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete current user's profile picture"""
    
    try:
        image_url = None
        
        if current_user.role == UserRole.TEACHER:
            teacher_profile = db.query(TeacherProfile).filter(
                TeacherProfile.user_id == current_user.id
            ).first()
            
            if not teacher_profile:
                # Create teacher profile if it doesn't exist
                teacher_profile = TeacherProfile(
                    user_id=current_user.id,
                    full_name=current_user.full_name or f"Teacher {current_user.username}",
                    school="Unknown School"
                )
                db.add(teacher_profile)
                db.commit()
                db.refresh(teacher_profile)
            
            if teacher_profile.profile_image_url:
                image_url = teacher_profile.profile_image_url
                teacher_profile.profile_image_url = None
        
        elif current_user.role == UserRole.ADMIN:
            # Admins use teacher profile for management interface
            teacher_profile = db.query(TeacherProfile).filter(
                TeacherProfile.user_id == current_user.id
            ).first()
            
            if not teacher_profile:
                # Create teacher profile for admin if it doesn't exist
                teacher_profile = TeacherProfile(
                    user_id=current_user.id,
                    full_name=current_user.full_name or f"Admin {current_user.username}",
                    school="Admin Panel"
                )
                db.add(teacher_profile)
                db.commit()
                db.refresh(teacher_profile)
            
            if teacher_profile.profile_image_url:
                image_url = teacher_profile.profile_image_url
                teacher_profile.profile_image_url = None
        
        elif current_user.role == UserRole.STUDENT:
            student_profile = db.query(StudentProfile).filter(
                StudentProfile.user_id == current_user.id
            ).first()
            if student_profile and student_profile.profile_image_url:
                image_url = student_profile.profile_image_url
                student_profile.profile_image_url = None
        
        else:
            raise HTTPException(status_code=403, detail="Only students, teachers, and admins can delete profile pictures")
        
        if not image_url:
            raise HTTPException(status_code=404, detail="No profile picture found")
        
        # Remove file from filesystem
        file_path = UPLOAD_DIR / Path(image_url).name
        if file_path.exists():
            file_path.unlink()
        
        db.commit()
        
        return {"message": "Profile picture deleted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete profile picture: {str(e)}")

@router.get("/profile-picture")
async def get_profile_picture_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's profile picture info"""
    
    image_url = None
    
    if current_user.role == UserRole.TEACHER:
        teacher_profile = db.query(TeacherProfile).filter(
            TeacherProfile.user_id == current_user.id
        ).first()
        
        if not teacher_profile:
            # Create teacher profile if it doesn't exist
            teacher_profile = TeacherProfile(
                user_id=current_user.id,
                full_name=current_user.full_name or f"Teacher {current_user.username}",
                school="Unknown School"
            )
            db.add(teacher_profile)
            db.commit()
            db.refresh(teacher_profile)
        
        image_url = teacher_profile.profile_image_url
    
    elif current_user.role == UserRole.ADMIN:
        # Admins use teacher profile for management interface
        teacher_profile = db.query(TeacherProfile).filter(
            TeacherProfile.user_id == current_user.id
        ).first()
        
        if not teacher_profile:
            # Create teacher profile for admin if it doesn't exist
            teacher_profile = TeacherProfile(
                user_id=current_user.id,
                full_name=current_user.full_name or f"Admin {current_user.username}",
                school="Admin Panel"
            )
            db.add(teacher_profile)
            db.commit()
            db.refresh(teacher_profile)
        
        image_url = teacher_profile.profile_image_url
    
    elif current_user.role == UserRole.STUDENT:
        student_profile = db.query(StudentProfile).filter(
            StudentProfile.user_id == current_user.id
        ).first()
        if student_profile:
            image_url = student_profile.profile_image_url
    
    return {
        "image_url": image_url,
        "has_image": image_url is not None
    }

@router.post("/student-profile-picture/{student_id}")
async def upload_student_profile_picture(
    student_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload profile picture for a student (Teacher/Admin only)"""
    
    # Check if current user is teacher or admin
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Only teachers and admins can upload student profile pictures")
    
    # Validate file
    validate_image_file(file)
    
    # Check file size
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 5MB")
    
    try:
        # Find the student
        student_profile = db.query(StudentProfile).filter(
            StudentProfile.id == student_id
        ).first()
        
        if not student_profile:
            raise HTTPException(status_code=404, detail="Student not found")
        
        # Check if teacher has access to this student (for teachers, not admins)
        if current_user.role == UserRole.TEACHER:
            teacher_profile = db.query(TeacherProfile).filter(
                TeacherProfile.user_id == current_user.id
            ).first()
            if not teacher_profile or student_profile.teacher_id != teacher_profile.id:
                raise HTTPException(status_code=403, detail="You don't have permission to edit this student")
        
        # Generate unique filename
        file_extension = Path(file.filename or "").suffix.lower()
        unique_filename = f"student_{student_id}_{uuid.uuid4().hex}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename
        
        # Save file
        save_upload_file(file, file_path)
        
        # Update student profile with image URL
        image_url = f"/uploads/profile_pictures/{unique_filename}"
        
        # Remove old profile picture if exists
        if student_profile.profile_image_url:
            old_file = UPLOAD_DIR / Path(student_profile.profile_image_url).name
            if old_file.exists():
                old_file.unlink()
        
        student_profile.profile_image_url = image_url
        db.commit()
        
        return {
            "message": "Student profile picture uploaded successfully",
            "image_url": image_url,
            "filename": unique_filename
        }
        
    except Exception as e:
        db.rollback()
        # Clean up uploaded file if database operation failed
        if 'file_path' in locals() and file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to upload student profile picture: {str(e)}")

@router.delete("/student-profile-picture/{student_id}")
async def delete_student_profile_picture(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete profile picture for a student (Teacher/Admin only)"""
    
    # Check if current user is teacher or admin
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Only teachers and admins can delete student profile pictures")
    
    try:
        # Find the student
        student_profile = db.query(StudentProfile).filter(
            StudentProfile.id == student_id
        ).first()
        
        if not student_profile:
            raise HTTPException(status_code=404, detail="Student not found")
        
        # Check if teacher has access to this student (for teachers, not admins)
        if current_user.role == UserRole.TEACHER:
            teacher_profile = db.query(TeacherProfile).filter(
                TeacherProfile.user_id == current_user.id
            ).first()
            if not teacher_profile or student_profile.teacher_id != teacher_profile.id:
                raise HTTPException(status_code=403, detail="You don't have permission to edit this student")
        
        if not student_profile.profile_image_url:
            raise HTTPException(status_code=404, detail="No profile picture found for this student")
        
        # Remove file from filesystem
        file_path = UPLOAD_DIR / Path(student_profile.profile_image_url).name
        if file_path.exists():
            file_path.unlink()
        
        # Update database
        student_profile.profile_image_url = None
        db.commit()
        
        return {"message": "Student profile picture deleted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete student profile picture: {str(e)}")