# app/models/task.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base

class InteractionType(str, enum.Enum):
    """Types of interactions students can have with tasks"""
    HELP_REQUEST = "help_request"  # Student asks for help
    BREAKDOWN = "breakdown"        # Student requests task breakdown
    EXAMPLE = "example"           # Student asks for examples  
    EXPLANATION = "explanation"   # Student asks for explanation
    FEEDBACK = "feedback"         # Student provides feedback

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"))
    original_image_url = Column(String)  # Path to uploaded image
    extracted_text = Column(Text)
    processed_text = Column(Text)  # After translation if needed
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    student = relationship("StudentProfile", back_populates="tasks")
    interactions = relationship("TaskInteraction", back_populates="task")

class TaskInteraction(Base):
    """Track all interactions students have with tasks for research analytics"""
    __tablename__ = "task_interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    student_id = Column(Integer, ForeignKey("student_profiles.id"))
    interaction_type = Column(Enum(InteractionType))
    
    # Interaction content
    student_input = Column(Text)  # What the student asked/said
    ai_response = Column(Text)    # What the AI responded
    
    # Metadata for research
    timestamp = Column(DateTime, default=datetime.utcnow)
    response_time_ms = Column(Integer, nullable=True)  # How long AI took to respond
    satisfaction_rating = Column(Integer, nullable=True)  # 1-5 rating if student provides feedback
    
    # Relationships
    task = relationship("Task", back_populates="interactions")
    student = relationship("StudentProfile")