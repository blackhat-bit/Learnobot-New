from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, validator
from enum import Enum


class TaskType(str, Enum):
    ASSIGNMENT = "assignment"
    QUIZ = "quiz"
    PROJECT = "project"
    DISCUSSION = "discussion"
    READING = "reading"


class TaskStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class SubmissionStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    GRADED = "graded"
    RETURNED = "returned"


# Task schemas
class TaskCreate(BaseModel):
    title: str
    description: str
    instructions: Optional[str] = None
    task_type: TaskType = TaskType.ASSIGNMENT
    subject: Optional[str] = None
    difficulty_level: Optional[str] = None
    estimated_duration: Optional[int] = None  # in minutes
    max_points: int = 100
    course_code: Optional[str] = None
    due_date: Optional[datetime] = None
    late_submission_allowed: bool = True
    ai_assistance_enabled: bool = True
    ai_hint_level: str = "medium"
    auto_feedback_enabled: bool = True
    resources: Optional[List[Dict[str, Any]]] = None
    rubric: Optional[Dict[str, Any]] = None

    @validator('title')
    def validate_title(cls, v):
        if len(v.strip()) < 1:
            raise ValueError('Title cannot be empty')
        if len(v) > 255:
            raise ValueError('Title must be no more than 255 characters')
        return v.strip()

    @validator('max_points')
    def validate_max_points(cls, v):
        if v <= 0:
            raise ValueError('Max points must be greater than 0')
        if v > 1000:
            raise ValueError('Max points cannot exceed 1000')
        return v

    @validator('ai_hint_level')
    def validate_ai_hint_level(cls, v):
        if v not in ['low', 'medium', 'high']:
            raise ValueError('AI hint level must be low, medium, or high')
        return v


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    task_type: Optional[TaskType] = None
    status: Optional[TaskStatus] = None
    subject: Optional[str] = None
    difficulty_level: Optional[str] = None
    estimated_duration: Optional[int] = None
    max_points: Optional[int] = None
    course_code: Optional[str] = None
    due_date: Optional[datetime] = None
    late_submission_allowed: Optional[bool] = None
    ai_assistance_enabled: Optional[bool] = None
    ai_hint_level: Optional[str] = None
    auto_feedback_enabled: Optional[bool] = None
    resources: Optional[List[Dict[str, Any]]] = None
    rubric: Optional[Dict[str, Any]] = None


class TaskBase(BaseModel):
    id: int
    title: str
    description: str
    task_type: TaskType
    status: TaskStatus
    subject: Optional[str] = None
    difficulty_level: Optional[str] = None
    estimated_duration: Optional[int] = None
    max_points: int
    course_code: Optional[str] = None
    due_date: Optional[datetime] = None
    late_submission_allowed: bool
    ai_assistance_enabled: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaskSummary(BaseModel):
    id: int
    title: str
    task_type: TaskType
    status: TaskStatus
    due_date: Optional[datetime] = None
    max_points: int
    submission_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class TaskDetail(TaskBase):
    instructions: Optional[str] = None
    teacher_id: int
    ai_hint_level: str
    auto_feedback_enabled: bool
    resources: Optional[List[Dict[str, Any]]] = None
    rubric: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


# Task Submission schemas
class TaskSubmissionCreate(BaseModel):
    content: Optional[str] = None
    file_urls: Optional[List[str]] = None

    @validator('content')
    def validate_content(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError('Content cannot be empty if provided')
        return v


class TaskSubmissionUpdate(BaseModel):
    content: Optional[str] = None
    file_urls: Optional[List[str]] = None
    status: Optional[SubmissionStatus] = None


class TaskSubmissionGrade(BaseModel):
    score: int
    teacher_feedback: Optional[str] = None
    feedback_summary: Optional[Dict[str, Any]] = None

    @validator('score')
    def validate_score(cls, v):
        if v < 0:
            raise ValueError('Score cannot be negative')
        return v


class TaskSubmissionBase(BaseModel):
    id: int
    task_id: int
    student_id: int
    status: SubmissionStatus
    score: Optional[int] = None
    max_score: Optional[int] = None
    grade_percentage: Optional[str] = None
    attempt_number: int
    time_spent: Optional[int] = None
    ai_hints_used: int
    started_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    graded_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TaskSubmissionDetail(TaskSubmissionBase):
    content: Optional[str] = None
    file_urls: Optional[List[str]] = None
    teacher_feedback: Optional[str] = None
    ai_feedback: Optional[str] = None
    feedback_summary: Optional[Dict[str, Any]] = None
    ai_interactions: Optional[List[Dict[str, Any]]] = None


class TaskSubmissionSummary(BaseModel):
    id: int
    student_id: int
    student_name: str
    status: SubmissionStatus
    score: Optional[int] = None
    submitted_at: Optional[datetime] = None
    graded_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Analytics schemas
class TaskAnalytics(BaseModel):
    total_submissions: int
    completed_submissions: int
    average_score: Optional[float] = None
    completion_rate: float
    average_time_spent: Optional[float] = None
    ai_usage_stats: Dict[str, Any] = {}


class StudentTaskProgress(BaseModel):
    task_id: int
    task_title: str
    status: SubmissionStatus
    score: Optional[int] = None
    due_date: Optional[datetime] = None
    time_spent: Optional[int] = None
    progress_percentage: float = 0.0
