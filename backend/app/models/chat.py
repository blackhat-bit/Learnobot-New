from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Learning context
    subject = Column(String(100), nullable=True)
    difficulty_level = Column(String(20), nullable=True)  # beginner, intermediate, advanced
    learning_objectives = Column(JSON, nullable=True)  # List of learning goals
    
    # Metadata
    metadata = Column(JSON, nullable=True)  # Additional flexible data
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="chats")
    messages = relationship("ChatMessage", back_populates="chat", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Chat(id={self.id}, title='{self.title}', user_id={self.user_id})>"


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)
    content = Column(Text, nullable=False)
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    
    # Message metadata
    message_type = Column(String(50), default="text")  # text, image, file, etc.
    file_url = Column(String(255), nullable=True)
    file_type = Column(String(50), nullable=True)
    
    # AI processing metadata
    tokens_used = Column(Integer, nullable=True)
    model_used = Column(String(100), nullable=True)
    confidence_score = Column(String(10), nullable=True)  # For AI responses
    
    # Learning analytics
    feedback_rating = Column(Integer, nullable=True)  # 1-5 rating from user
    understanding_level = Column(String(20), nullable=True)  # confused, partial, good, excellent
    
    # Additional data
    metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    chat = relationship("Chat", back_populates="messages")
    
    def __repr__(self):
        return f"<ChatMessage(id={self.id}, chat_id={self.chat_id}, role='{self.role}')>"
