# app/models/conversation_state.py
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class ConversationState(Base):
    """Track conversation mediation state per session"""
    __tablename__ = "conversation_states"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), unique=True, index=True)
    
    # Strategy tracking
    failed_strategies = Column(JSON, default=list)  # List of failed strategy names
    current_strategy = Column(String(50), nullable=True)
    attempt_count = Column(Integer, default=0)
    
    # Comprehension tracking
    comprehension_history = Column(JSON, default=list)  # ["confused", "partial", "understood"]
    last_comprehension_level = Column(String(20), default="initial")
    
    # Conversation context
    current_instruction = Column(Text, nullable=True)
    conversation_summary = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    session = relationship("ChatSession", back_populates="conversation_state")

    def add_failed_strategy(self, strategy: str):
        """Add a strategy to failed list"""
        if self.failed_strategies is None:
            self.failed_strategies = []
        if strategy not in self.failed_strategies:
            self.failed_strategies.append(strategy)
            
    def update_comprehension(self, level: str):
        """Update comprehension tracking"""
        if self.comprehension_history is None:
            self.comprehension_history = []
        self.comprehension_history.append(level)
        self.last_comprehension_level = level
        
    def get_failed_strategies(self) -> list:
        """Get list of failed strategies"""
        return self.failed_strategies or []
        
    def reset_for_new_instruction(self):
        """Reset state for new instruction"""
        self.failed_strategies = []
        self.current_strategy = None
        self.attempt_count = 0
        self.comprehension_history = []
        self.last_comprehension_level = "initial"