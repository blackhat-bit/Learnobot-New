from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, validator


# Chat schemas
class ChatCreate(BaseModel):
    title: str
    subject: Optional[str] = None
    difficulty_level: Optional[str] = None
    learning_objectives: Optional[List[str]] = None

    @validator('title')
    def validate_title(cls, v):
        if len(v) < 1:
            raise ValueError('Title cannot be empty')
        if len(v) > 255:
            raise ValueError('Title must be no more than 255 characters')
        return v

    @validator('difficulty_level')
    def validate_difficulty_level(cls, v):
        if v and v not in ['beginner', 'intermediate', 'advanced']:
            raise ValueError('Difficulty level must be beginner, intermediate, or advanced')
        return v


class ChatUpdate(BaseModel):
    title: Optional[str] = None
    subject: Optional[str] = None
    difficulty_level: Optional[str] = None
    learning_objectives: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ChatBase(BaseModel):
    id: int
    title: str
    subject: Optional[str] = None
    difficulty_level: Optional[str] = None
    learning_objectives: Optional[List[str]] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChatSummary(BaseModel):
    id: int
    title: str
    subject: Optional[str] = None
    message_count: int
    last_message_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Chat Message schemas
class ChatMessageCreate(BaseModel):
    content: str
    message_type: str = "text"
    file_url: Optional[str] = None
    file_type: Optional[str] = None

    @validator('content')
    def validate_content(cls, v):
        if len(v.strip()) < 1:
            raise ValueError('Message content cannot be empty')
        if len(v) > 50000:
            raise ValueError('Message content too long')
        return v

    @validator('message_type')
    def validate_message_type(cls, v):
        allowed_types = ['text', 'image', 'file', 'audio', 'video']
        if v not in allowed_types:
            raise ValueError(f'Message type must be one of: {", ".join(allowed_types)}')
        return v


class ChatMessageUpdate(BaseModel):
    content: Optional[str] = None
    feedback_rating: Optional[int] = None
    understanding_level: Optional[str] = None

    @validator('feedback_rating')
    def validate_feedback_rating(cls, v):
        if v is not None and (v < 1 or v > 5):
            raise ValueError('Feedback rating must be between 1 and 5')
        return v

    @validator('understanding_level')
    def validate_understanding_level(cls, v):
        if v and v not in ['confused', 'partial', 'good', 'excellent']:
            raise ValueError('Understanding level must be confused, partial, good, or excellent')
        return v


class ChatMessageBase(BaseModel):
    id: int
    content: str
    role: str
    message_type: str
    file_url: Optional[str] = None
    file_type: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatMessageDetail(ChatMessageBase):
    tokens_used: Optional[int] = None
    model_used: Optional[str] = None
    confidence_score: Optional[str] = None
    feedback_rating: Optional[int] = None
    understanding_level: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ChatWithMessages(ChatBase):
    messages: List[ChatMessageBase] = []


# AI Response schemas
class AIResponse(BaseModel):
    content: str
    model_used: str
    tokens_used: int
    confidence_score: Optional[str] = None
    suggestions: Optional[List[str]] = None
    follow_up_questions: Optional[List[str]] = None


# Chat Analytics schemas
class ChatAnalytics(BaseModel):
    total_messages: int
    user_messages: int
    ai_messages: int
    average_response_time: Optional[float] = None
    topics_discussed: List[str] = []
    learning_progress: Optional[Dict[str, Any]] = None
