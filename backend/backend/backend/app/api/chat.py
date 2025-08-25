from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, get_optional_current_user
from app.models.user import User
from app.models.chat import Chat, ChatMessage
from app.schemas.chat import (
    ChatCreate,
    ChatUpdate,
    ChatBase,
    ChatSummary,
    ChatWithMessages,
    ChatMessageCreate,
    ChatMessageUpdate,
    ChatMessageBase,
    ChatMessageDetail,
    AIResponse,
    ChatAnalytics
)
from app.services.chat_service import ChatService

router = APIRouter()


@router.post("/", response_model=ChatBase, status_code=status.HTTP_201_CREATED)
async def create_chat(
    chat_data: ChatCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new chat session."""
    
    db_chat = Chat(
        user_id=current_user.id,
        title=chat_data.title,
        subject=chat_data.subject,
        difficulty_level=chat_data.difficulty_level,
        learning_objectives=chat_data.learning_objectives
    )
    
    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)
    
    return db_chat


@router.get("/", response_model=List[ChatSummary])
async def get_user_chats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    is_active: Optional[bool] = Query(None)
):
    """Get user's chat sessions."""
    
    query = db.query(Chat).filter(Chat.user_id == current_user.id)
    
    if is_active is not None:
        query = query.filter(Chat.is_active == is_active)
    
    chats = query.order_by(desc(Chat.updated_at)).offset(skip).limit(limit).all()
    
    # Add message count and last message time
    chat_summaries = []
    for chat in chats:
        message_count = db.query(ChatMessage).filter(ChatMessage.chat_id == chat.id).count()
        last_message = db.query(ChatMessage).filter(ChatMessage.chat_id == chat.id).order_by(desc(ChatMessage.created_at)).first()
        
        chat_summaries.append(ChatSummary(
            id=chat.id,
            title=chat.title,
            subject=chat.subject,
            message_count=message_count,
            last_message_at=last_message.created_at if last_message else None,
            created_at=chat.created_at
        ))
    
    return chat_summaries


@router.get("/{chat_id}", response_model=ChatWithMessages)
async def get_chat(
    chat_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific chat with its messages."""
    
    chat = db.query(Chat).options(
        joinedload(Chat.messages)
    ).filter(
        Chat.id == chat_id,
        Chat.user_id == current_user.id
    ).first()
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    return chat


@router.put("/{chat_id}", response_model=ChatBase)
async def update_chat(
    chat_id: int,
    chat_data: ChatUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a chat session."""
    
    chat = db.query(Chat).filter(
        Chat.id == chat_id,
        Chat.user_id == current_user.id
    ).first()
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    # Update fields if provided
    for field, value in chat_data.dict(exclude_unset=True).items():
        setattr(chat, field, value)
    
    db.commit()
    db.refresh(chat)
    
    return chat


@router.delete("/{chat_id}")
async def delete_chat(
    chat_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a chat session."""
    
    chat = db.query(Chat).filter(
        Chat.id == chat_id,
        Chat.user_id == current_user.id
    ).first()
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    db.delete(chat)
    db.commit()
    
    return {"message": "Chat deleted successfully"}


@router.post("/{chat_id}/messages", response_model=AIResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    chat_id: int,
    message_data: ChatMessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send a message in a chat and get AI response."""
    
    chat = db.query(Chat).filter(
        Chat.id == chat_id,
        Chat.user_id == current_user.id
    ).first()
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    # Create user message
    user_message = ChatMessage(
        chat_id=chat_id,
        content=message_data.content,
        role="user",
        message_type=message_data.message_type,
        file_url=message_data.file_url,
        file_type=message_data.file_type
    )
    
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    
    # Get AI response using chat service
    chat_service = ChatService(db)
    ai_response = await chat_service.get_ai_response(chat_id, message_data.content)
    
    # Create AI message
    ai_message = ChatMessage(
        chat_id=chat_id,
        content=ai_response.content,
        role="assistant",
        message_type="text",
        model_used=ai_response.model_used,
        tokens_used=ai_response.tokens_used,
        confidence_score=ai_response.confidence_score
    )
    
    db.add(ai_message)
    db.commit()
    
    # Update chat's updated_at timestamp
    chat.updated_at = user_message.created_at
    db.commit()
    
    return ai_response


@router.get("/{chat_id}/messages", response_model=List[ChatMessageBase])
async def get_chat_messages(
    chat_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500)
):
    """Get messages from a chat."""
    
    chat = db.query(Chat).filter(
        Chat.id == chat_id,
        Chat.user_id == current_user.id
    ).first()
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    messages = db.query(ChatMessage).filter(
        ChatMessage.chat_id == chat_id
    ).order_by(ChatMessage.created_at).offset(skip).limit(limit).all()
    
    return messages


@router.get("/{chat_id}/messages/{message_id}", response_model=ChatMessageDetail)
async def get_message(
    chat_id: int,
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific message."""
    
    # Verify chat ownership
    chat = db.query(Chat).filter(
        Chat.id == chat_id,
        Chat.user_id == current_user.id
    ).first()
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    message = db.query(ChatMessage).filter(
        ChatMessage.id == message_id,
        ChatMessage.chat_id == chat_id
    ).first()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    return message


@router.put("/{chat_id}/messages/{message_id}", response_model=ChatMessageDetail)
async def update_message(
    chat_id: int,
    message_id: int,
    message_data: ChatMessageUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a message (typically for feedback)."""
    
    # Verify chat ownership
    chat = db.query(Chat).filter(
        Chat.id == chat_id,
        Chat.user_id == current_user.id
    ).first()
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    message = db.query(ChatMessage).filter(
        ChatMessage.id == message_id,
        ChatMessage.chat_id == chat_id
    ).first()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    # Update fields if provided
    for field, value in message_data.dict(exclude_unset=True).items():
        setattr(message, field, value)
    
    db.commit()
    db.refresh(message)
    
    return message


@router.get("/{chat_id}/analytics", response_model=ChatAnalytics)
async def get_chat_analytics(
    chat_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get analytics for a chat."""
    
    chat = db.query(Chat).filter(
        Chat.id == chat_id,
        Chat.user_id == current_user.id
    ).first()
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    # Get message statistics
    messages = db.query(ChatMessage).filter(ChatMessage.chat_id == chat_id).all()
    
    total_messages = len(messages)
    user_messages = len([m for m in messages if m.role == "user"])
    ai_messages = len([m for m in messages if m.role == "assistant"])
    
    # Calculate average response time (placeholder)
    avg_response_time = None  # Would need more sophisticated tracking
    
    # Extract topics (placeholder - would use NLP)
    topics_discussed = []
    
    # Learning progress (placeholder)
    learning_progress = {}
    
    return ChatAnalytics(
        total_messages=total_messages,
        user_messages=user_messages,
        ai_messages=ai_messages,
        average_response_time=avg_response_time,
        topics_discussed=topics_discussed,
        learning_progress=learning_progress
    )
