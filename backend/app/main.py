# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, chat, teacher, student
from app.core.database import engine
from app.models import user, chat as chat_models, task
from app.config import settings

# Create database tables
user.Base.metadata.create_all(bind=engine)
chat_models.Base.metadata.create_all(bind=engine)
task.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_PREFIX}/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_PREFIX}/auth", tags=["auth"])
app.include_router(chat.router, prefix=f"{settings.API_PREFIX}/chat", tags=["chat"])
app.include_router(teacher.router, prefix=f"{settings.API_PREFIX}/teacher", tags=["teacher"])
app.include_router(student.router, prefix=f"{settings.API_PREFIX}/student", tags=["student"])

@app.get("/")
def read_root():
    return {"message": "Welcome to LearnoBot API"}

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

class ChatMessageCreate(ChatMessageBase):
    assistance_type: Optional[AssistanceType] = None

class ChatMessage(ChatMessageBase):
    id: int
    timestamp: datetime
    satisfaction_rating: Optional[int] = None
    
    class Config:
        orm_mode = True

class ChatSessionCreate(BaseModel):
    mode: InteractionMode = InteractionMode.PRACTICE

class ChatSession(BaseModel):
    id: int
    mode: InteractionMode
    started_at: datetime
    ended_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class TaskUpload(BaseModel):
    image_base64: str
    session_id: int

class RatingSatisfaction(BaseModel):
    message_id: int
    rating: int  # 1-5