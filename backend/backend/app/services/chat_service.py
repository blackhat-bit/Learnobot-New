from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import asyncio
import json

from app.models.chat import Chat, ChatMessage
from app.models.llm_config import LLMConfig
from app.schemas.chat import AIResponse
from app.ai.llm_manager import LLMManager
from app.config import settings


class ChatService:
    """Service for chat functionality and AI interactions."""
    
    def __init__(self, db: Session):
        self.db = db
        self.llm_manager = LLMManager()
    
    def create_chat(self, user_id: int, title: str, **kwargs) -> Chat:
        """Create a new chat session."""
        
        chat = Chat(
            user_id=user_id,
            title=title,
            **kwargs
        )
        
        self.db.add(chat)
        self.db.commit()
        self.db.refresh(chat)
        
        return chat
    
    def get_user_chats(self, user_id: int, skip: int = 0, limit: int = 50) -> List[Chat]:
        """Get user's chat sessions."""
        
        return self.db.query(Chat).filter(
            Chat.user_id == user_id
        ).order_by(Chat.updated_at.desc()).offset(skip).limit(limit).all()
    
    def get_chat_by_id(self, chat_id: int, user_id: int) -> Optional[Chat]:
        """Get a specific chat by ID."""
        
        return self.db.query(Chat).filter(
            Chat.id == chat_id,
            Chat.user_id == user_id
        ).first()
    
    def add_user_message(self, chat_id: int, content: str, **kwargs) -> ChatMessage:
        """Add a user message to a chat."""
        
        message = ChatMessage(
            chat_id=chat_id,
            content=content,
            role="user",
            **kwargs
        )
        
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        
        return message
    
    def add_ai_message(self, chat_id: int, content: str, **kwargs) -> ChatMessage:
        """Add an AI message to a chat."""
        
        message = ChatMessage(
            chat_id=chat_id,
            content=content,
            role="assistant",
            **kwargs
        )
        
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        
        return message
    
    async def get_ai_response(self, chat_id: int, user_message: str) -> AIResponse:
        """Get AI response for a user message."""
        
        # Get chat context
        chat = self.db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat not found"
            )
        
        # Get chat history
        messages = self.db.query(ChatMessage).filter(
            ChatMessage.chat_id == chat_id
        ).order_by(ChatMessage.created_at).limit(20).all()  # Last 20 messages
        
        # Prepare conversation context
        conversation_history = []
        for msg in messages:
            conversation_history.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Add current user message
        conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Get appropriate LLM configuration
        llm_config = self._get_llm_config_for_chat(chat)
        
        # Generate AI response
        try:
            response = await self.llm_manager.generate_response(
                messages=conversation_history,
                config=llm_config,
                chat_context={
                    "subject": chat.subject,
                    "difficulty_level": chat.difficulty_level,
                    "learning_objectives": chat.learning_objectives
                }
            )
            
            return AIResponse(
                content=response["content"],
                model_used=response["model_used"],
                tokens_used=response["tokens_used"],
                confidence_score=response.get("confidence_score"),
                suggestions=response.get("suggestions", []),
                follow_up_questions=response.get("follow_up_questions", [])
            )
        
        except Exception as e:
            # Fallback response
            return AIResponse(
                content="I apologize, but I'm experiencing technical difficulties. Please try again in a moment.",
                model_used="fallback",
                tokens_used=0,
                confidence_score="low"
            )
    
    def _get_llm_config_for_chat(self, chat: Chat) -> LLMConfig:
        """Get appropriate LLM configuration for a chat."""
        
        # Try to get subject-specific configuration
        if chat.subject:
            config = self.db.query(LLMConfig).filter(
                LLMConfig.is_active == True,
                LLMConfig.subject_specializations.contains([chat.subject])
            ).first()
            
            if config:
                return config
        
        # Get default configuration
        default_config = self.db.query(LLMConfig).filter(
            LLMConfig.is_default == True,
            LLMConfig.is_active == True
        ).first()
        
        if default_config:
            return default_config
        
        # Fallback to any active configuration
        fallback_config = self.db.query(LLMConfig).filter(
            LLMConfig.is_active == True
        ).first()
        
        if not fallback_config:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No active LLM configuration available"
            )
        
        return fallback_config
    
    def update_message_feedback(self, message_id: int, feedback_data: Dict[str, Any]) -> ChatMessage:
        """Update message with user feedback."""
        
        message = self.db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        # Update feedback fields
        for key, value in feedback_data.items():
            if hasattr(message, key):
                setattr(message, key, value)
        
        self.db.commit()
        self.db.refresh(message)
        
        return message
    
    def get_chat_analytics(self, chat_id: int) -> Dict[str, Any]:
        """Get analytics for a chat."""
        
        messages = self.db.query(ChatMessage).filter(ChatMessage.chat_id == chat_id).all()
        
        total_messages = len(messages)
        user_messages = len([m for m in messages if m.role == "user"])
        ai_messages = len([m for m in messages if m.role == "assistant"])
        
        # Calculate engagement metrics
        avg_message_length = sum(len(m.content) for m in messages) / total_messages if total_messages > 0 else 0
        
        # Extract topics (simple keyword extraction)
        topics = self._extract_topics_from_messages(messages)
        
        # Calculate learning progress indicators
        learning_progress = self._assess_learning_progress(messages)
        
        return {
            "total_messages": total_messages,
            "user_messages": user_messages,
            "ai_messages": ai_messages,
            "average_message_length": avg_message_length,
            "topics_discussed": topics,
            "learning_progress": learning_progress
        }
    
    def _extract_topics_from_messages(self, messages: List[ChatMessage]) -> List[str]:
        """Extract topics from chat messages (simplified)."""
        
        # This is a simplified implementation
        # In a real system, you might use NLP libraries like spaCy or NLTK
        
        common_words = set([
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "up", "about", "into", "through", "during",
            "before", "after", "above", "below", "between", "among", "within",
            "is", "are", "was", "were", "be", "being", "been", "have", "has", "had",
            "do", "does", "did", "will", "would", "could", "should", "may", "might",
            "can", "must", "shall", "this", "that", "these", "those", "i", "you",
            "he", "she", "it", "we", "they", "me", "him", "her", "us", "them"
        ])
        
        word_count = {}
        
        for message in messages:
            if message.role == "user":
                words = message.content.lower().split()
                for word in words:
                    word = word.strip(".,!?;:")
                    if len(word) > 3 and word not in common_words:
                        word_count[word] = word_count.get(word, 0) + 1
        
        # Return top 10 topics
        sorted_topics = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
        return [topic[0] for topic in sorted_topics[:10]]
    
    def _assess_learning_progress(self, messages: List[ChatMessage]) -> Dict[str, Any]:
        """Assess learning progress from chat messages."""
        
        # Simple progress assessment based on message patterns
        user_messages = [m for m in messages if m.role == "user"]
        
        if not user_messages:
            return {"status": "no_activity", "confidence": "low"}
        
        # Look for question patterns
        questions = len([m for m in user_messages if "?" in m.content])
        total_user_messages = len(user_messages)
        
        question_ratio = questions / total_user_messages if total_user_messages > 0 else 0
        
        # Simple heuristic for engagement
        if question_ratio > 0.5:
            progress_status = "highly_engaged"
        elif question_ratio > 0.3:
            progress_status = "moderately_engaged"
        else:
            progress_status = "low_engagement"
        
        return {
            "status": progress_status,
            "question_ratio": question_ratio,
            "total_interactions": total_user_messages,
            "confidence": "medium"
        }
    
    def delete_chat(self, chat_id: int, user_id: int) -> bool:
        """Delete a chat and all its messages."""
        
        chat = self.db.query(Chat).filter(
            Chat.id == chat_id,
            Chat.user_id == user_id
        ).first()
        
        if not chat:
            return False
        
        self.db.delete(chat)
        self.db.commit()
        
        return True
    
    def archive_chat(self, chat_id: int, user_id: int) -> bool:
        """Archive a chat (set as inactive)."""
        
        chat = self.db.query(Chat).filter(
            Chat.id == chat_id,
            Chat.user_id == user_id
        ).first()
        
        if not chat:
            return False
        
        chat.is_active = False
        self.db.commit()
        
        return True
