from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Text, JSON, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class TaskStatus(enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class TaskType(enum.Enum):
    ASSIGNMENT = "assignment"
    QUIZ = "quiz"
    PROJECT = "project"
    DISCUSSION = "discussion"
    READING = "reading"


class SubmissionStatus(enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    GRADED = "graded"
    RETURNED = "returned"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    instructions = Column(Text, nullable=True)
    
    # Task configuration
    task_type = Column(Enum(TaskType), nullable=False, default=TaskType.ASSIGNMENT)
    status = Column(Enum(TaskStatus), nullable=False, default=TaskStatus.DRAFT)
    subject = Column(String(100), nullable=True)
    difficulty_level = Column(String(20), nullable=True)
    estimated_duration = Column(Integer, nullable=True)  # in minutes
    max_points = Column(Integer, default=100)
    
    # Teacher and course info
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_code = Column(String(20), nullable=True)
    
    # Deadlines
    due_date = Column(DateTime(timezone=True), nullable=True)
    late_submission_allowed = Column(Boolean, default=True)
    
    # AI assistance configuration
    ai_assistance_enabled = Column(Boolean, default=True)
    ai_hint_level = Column(String(20), default="medium")  # low, medium, high
    auto_feedback_enabled = Column(Boolean, default=True)
    
    # Resources and materials
    resources = Column(JSON, nullable=True)  # List of resource URLs, files, etc.
    rubric = Column(JSON, nullable=True)  # Grading rubric
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    teacher = relationship("User", back_populates="tasks", foreign_keys=[teacher_id])
    submissions = relationship("TaskSubmission", back_populates="task", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', type='{self.task_type.value}')>"


class TaskSubmission(Base):
    __tablename__ = "task_submissions"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Submission content
    content = Column(Text, nullable=True)
    file_urls = Column(JSON, nullable=True)  # List of submitted file URLs
    
    # Status and grading
    status = Column(Enum(SubmissionStatus), nullable=False, default=SubmissionStatus.NOT_STARTED)
    score = Column(Integer, nullable=True)
    max_score = Column(Integer, nullable=True)
    grade_percentage = Column(String(10), nullable=True)
    
    # Feedback
    teacher_feedback = Column(Text, nullable=True)
    ai_feedback = Column(Text, nullable=True)
    feedback_summary = Column(JSON, nullable=True)  # Structured feedback data
    
    # Attempt tracking
    attempt_number = Column(Integer, default=1)
    time_spent = Column(Integer, nullable=True)  # in minutes
    
    # AI assistance tracking
    ai_hints_used = Column(Integer, default=0)
    ai_interactions = Column(JSON, nullable=True)  # Track AI help sessions
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    graded_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    task = relationship("Task", back_populates="submissions")
    student = relationship("User", back_populates="task_submissions")
    
    def __repr__(self):
        return f"<TaskSubmission(id={self.id}, task_id={self.task_id}, student_id={self.student_id}, status='{self.status.value}')>"
