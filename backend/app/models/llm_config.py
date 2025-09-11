# app/models/llm_config.py
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class LLMProvider(Base):
    __tablename__ = "llm_providers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    type = Column(String)  # "local" or "online"
    is_active = Column(Boolean, default=True)
    is_deactivated = Column(Boolean, default=False)  # For admin to deactivate models
    api_key = Column(String, nullable=True)  # Encrypted in production
    config = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    configs = relationship("LLMConfig", back_populates="provider")
    # Note: LLMTestLog uses string provider name, not FK relationship

class LLMConfig(Base):
    __tablename__ = "llm_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("llm_providers.id"))
    name = Column(String, index=True)  # e.g., "practice_mode", "test_mode"
    model = Column(String)
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=2048)
    top_p = Column(Float, default=0.9)
    system_prompt = Column(Text)
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    provider = relationship("LLMProvider", back_populates="configs")
    creator = relationship("User")

class LLMTestLog(Base):
    __tablename__ = "llm_test_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"))
    provider = Column(String)  # Provider name as string
    model = Column(String)
    prompt = Column(Text)
    response_text = Column(Text)
    response_time = Column(Float)  # in seconds
    tokens_used = Column(Integer, nullable=True)
    cost = Column(Float, nullable=True)  # for paid APIs
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("ChatSession")
    # Note: Uses string provider name, not FK relationship to LLMProvider
