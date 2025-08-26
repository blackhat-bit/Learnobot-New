# app/models/user.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base

class UserRole(str, enum.Enum):
    STUDENT = "student"
    TEACHER = "teacher"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    teacher_profile = relationship("TeacherProfile", back_populates="user", uselist=False)
    student_profile = relationship("StudentProfile", back_populates="user", uselist=False)
    chat_messages = relationship("ChatMessage", back_populates="user")

class TeacherProfile(Base):
    __tablename__ = "teacher_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    full_name = Column(String, nullable=False)
    school = Column(String)
    
    # Relationships
    user = relationship("User", back_populates="teacher_profile")
    students = relationship("StudentProfile", back_populates="teacher")

class StudentProfile(Base):
    __tablename__ = "student_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    teacher_id = Column(Integer, ForeignKey("teacher_profiles.id"))
    full_name = Column(String, nullable=False)
    grade = Column(String)
    difficulty_level = Column(Integer, default=3)  # 1-5 scale
    difficulties_description = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="student_profile")
    teacher = relationship("TeacherProfile", back_populates="students")
    tasks = relationship("Task", back_populates="student")