# app/schemas/chat.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from enum import Enum

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"

class InteractionMode(str, Enum):
    PRACTICE = "practice"
    TEST = "test"

class AssistanceType(str, Enum):
    BREAKDOWN = "breakdown"
    EXAMPLE = "example"
    EXPLAIN = "explain"

class ChatMessageBase(BaseModel):
    content: str
    role: MessageRole

class ChatMessageCreate(BaseModel):
    content: str
    assistance_type: Optional[AssistanceType] = None
    provider: Optional[str] = None  # Allow specifying which LLM provider to use

class ChatMessage(ChatMessageBase):
    id: int
    timestamp: datetime
    satisfaction_rating: Optional[int] = None
    
    class Config:
        from_attributes = True #orm_mode

class ChatSessionCreate(BaseModel):
    mode: InteractionMode = InteractionMode.PRACTICE
    preferred_provider: Optional[str] = None  # Default LLM provider for this session

class ChatSession(BaseModel):
    id: int
    mode: InteractionMode
    started_at: datetime
    ended_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class TaskUpload(BaseModel):
    image_base64: str
    session_id: int

class RatingSatisfaction(BaseModel):
    message_id: int
    rating: int  # 1-5