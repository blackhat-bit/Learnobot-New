# app/models/notification.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base

class NotificationType(str, enum.Enum):
    TEACHER_CALL = "teacher_call"
    SYSTEM_ALERT = "system_alert"
    SESSION_COMPLETE = "session_complete"

class NotificationPriority(str, enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class TeacherNotification(Base):
    __tablename__ = "teacher_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teacher_profiles.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=True)
    
    type = Column(Enum(NotificationType), nullable=False, default=NotificationType.TEACHER_CALL)
    priority = Column(Enum(NotificationPriority), nullable=False, default=NotificationPriority.NORMAL)
    
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    
    is_read = Column(Boolean, default=False)
    is_handled = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime, nullable=True)
    handled_at = Column(DateTime, nullable=True)
    
    # Optional metadata for additional context
    extra_data = Column(Text, nullable=True)  # JSON string
    
    # Relationships
    teacher = relationship("TeacherProfile", back_populates="notifications")
    student = relationship("StudentProfile", back_populates="teacher_notifications")
    
    def to_dict(self):
        return {
            "id": self.id,
            "teacher_id": self.teacher_id,
            "student_id": self.student_id,
            "session_id": self.session_id,
            "type": self.type.value,
            "priority": self.priority.value,
            "title": self.title,
            "message": self.message,
            "is_read": self.is_read,
            "is_handled": self.is_handled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "handled_at": self.handled_at.isoformat() if self.handled_at else None,
            "metadata": self.extra_data,
            "student_name": self.student.full_name if self.student else None,
        }

# Add reverse relationship to existing models
from app.models.user import TeacherProfile, StudentProfile

TeacherProfile.notifications = relationship("TeacherNotification", back_populates="teacher")
StudentProfile.teacher_notifications = relationship("TeacherNotification", back_populates="student")