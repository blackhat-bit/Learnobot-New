# app/models/analytics.py
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base

class EventType(str, enum.Enum):
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    MESSAGE_SENT = "message_sent"
    AI_RESPONSE = "ai_response"
    ASSISTANCE_REQUESTED = "assistance_requested"
    TASK_UPLOADED = "task_uploaded"
    RATING_GIVEN = "rating_given"
    TEACHER_CALLED = "teacher_called"
    MODE_SWITCHED = "mode_switched"
    ERROR_OCCURRED = "error_occurred"

class InteractionLog(Base):
    """Detailed log of every interaction for research analysis"""
    __tablename__ = "interaction_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    event_type = Column(Enum(EventType), index=True)
    event_data = Column(JSON)  # Flexible data storage
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Performance metrics
    response_time_ms = Column(Integer, nullable=True)  # Time to generate response
    input_length = Column(Integer, nullable=True)  # Length of user input
    output_length = Column(Integer, nullable=True)  # Length of AI response
    
    # Relationships
    session = relationship("ChatSession")
    user = relationship("User")

class SessionAnalytics(Base):
    """Aggregated analytics per session"""
    __tablename__ = "session_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), unique=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"))
    
    # Time metrics
    total_duration_seconds = Column(Integer)
    active_duration_seconds = Column(Integer)  # Excluding idle time
    average_response_time_ms = Column(Float)
    
    # Interaction counts
    total_messages = Column(Integer, default=0)
    student_messages = Column(Integer, default=0)
    ai_messages = Column(Integer, default=0)
    
    # Assistance usage
    breakdown_count = Column(Integer, default=0)
    example_count = Column(Integer, default=0)
    explain_count = Column(Integer, default=0)
    
    # Other metrics
    tasks_uploaded = Column(Integer, default=0)
    teacher_calls = Column(Integer, default=0)
    average_satisfaction = Column(Float, nullable=True)
    errors_encountered = Column(Integer, default=0)
    
    # Calculated at session end
    completed_successfully = Column(Boolean, default=False)
    learning_progress_score = Column(Float, nullable=True)  # 0-100
    
    # Relationships
    session = relationship("ChatSession", uselist=False)
    student = relationship("StudentProfile")

class StudentProgress(Base):
    """Track student progress over time"""
    __tablename__ = "student_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"))
    date = Column(DateTime, default=datetime.utcnow)
    
    # Daily metrics
    sessions_count = Column(Integer, default=0)
    total_interaction_time = Column(Integer, default=0)  # seconds
    tasks_completed = Column(Integer, default=0)
    
    # Performance indicators
    average_response_accuracy = Column(Float, nullable=True)  # If we implement accuracy checking
    independence_score = Column(Float, nullable=True)  # Less help needed over time
    engagement_score = Column(Float, nullable=True)  # Based on interaction patterns
    
    # Mode usage
    practice_mode_time = Column(Integer, default=0)
    test_mode_time = Column(Integer, default=0)
    
    # Relationships
    student = relationship("StudentProfile")
