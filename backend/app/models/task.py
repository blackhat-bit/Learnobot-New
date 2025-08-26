# app/models/task.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

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