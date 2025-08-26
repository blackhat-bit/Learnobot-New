# app/services/chat_service.py
from sqlalchemy.orm import Session
from app.models.chat import ChatSession, ChatMessage, InteractionMode, MessageRole
from app.models.task import Task
from app.ai.chains.instruction_chain import InstructionProcessor
from app.ai.mediation_strategies import MediationManager, MediationStrategy
from typing import Optional
import logging

logger = logging.getLogger(__name__)

instruction_processor = InstructionProcessor()
mediation_manager = MediationManager()

async def create_session(db: Session, student_id: int, mode: InteractionMode) -> ChatSession:
    """Create a new chat session"""
    session = ChatSession(
        student_id=student_id,
        mode=mode
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

async def process_message(
    db: Session,
    session_id: int,
    user_id: int,
    message: str,
    assistance_type: Optional[str] = None
) -> ChatMessage:
    """Process a user message and generate AI response"""
    
    # Save user message
    user_message = ChatMessage(
        session_id=session_id,
        user_id=user_id,
        role=MessageRole.USER,
        content=message
    )
    db.add(user_message)
    db.commit()
    
    # Get session details
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    student = session.student
    
    # Prepare student context
    student_context = {
        "name": student.full_name,
        "grade": student.grade,
        "difficulty_level": student.difficulty_level,
        "difficulties": student.difficulties_description
    }
    
    # Generate AI response based on mode and assistance type
    if session.mode == InteractionMode.PRACTICE:
        if assistance_type == "breakdown":
            ai_response = instruction_processor.breakdown_instruction(
                message, student.difficulty_level
            )
        elif assistance_type == "example":
            ai_response = instruction_processor.provide_example(
                message, "main concept"
            )
        elif assistance_type == "explain":
            ai_response = instruction_processor.explain_instruction(
                message, student.difficulty_level
            )
        else:
            # Analyze and provide appropriate help
            analysis = instruction_processor.analyze_instruction(message, student_context)
            ai_response = analysis["analysis"]
    else:
        # Test mode - limited assistance
        # Check previous attempts
        previous_attempts = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id,
            ChatMessage.role == MessageRole.ASSISTANT
        ).count()
        
        if previous_attempts >= 3:
            ai_response = "You've reached the maximum number of attempts for this test question. Please move to the next question or ask your teacher for help."
        else:
            # Provide minimal assistance
            strategy = mediation_manager.get_next_strategy([], "test")
            ai_response = mediation_manager.apply_strategy(
                strategy, message, instruction_processor
            )
    
    # Save AI response
    ai_message = ChatMessage(
        session_id=session_id,
        user_id=user_id,
        role=MessageRole.ASSISTANT,
        content=ai_response
    )
    db.add(ai_message)
    db.commit()
    db.refresh(ai_message)
    
    return ai_message

async def process_task_image(
    db: Session,
    session_id: int,
    student_id: int,
    image_data: bytes,
    extracted_text: str
) -> Task:
    """Process an uploaded task image"""
    
    # Save task
    task = Task(
        student_id=student_id,
        extracted_text=extracted_text,
        processed_text=extracted_text  # Could add translation here if needed
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    
    # Create a message with the extracted text
    await process_message(
        db=db,
        session_id=session_id,
        user_id=student_id,
        message=f"I need help with this task: {extracted_text}"
    )
    
    return task

def rate_message(db: Session, message_id: int, rating: int, user_id: int):
    """Rate an AI message"""
    message = db.query(ChatMessage).filter(
        ChatMessage.id == message_id,
        ChatMessage.role == MessageRole.ASSISTANT
    ).first()
    
    if not message:
        raise ValueError("Message not found or not an AI response")
    
    message.satisfaction_rating = rating
    db.commit()
    
    return {"message": "Rating saved successfully"}

async def call_teacher(db: Session, session_id: int, student_id: int):
    """Send a help request notification to the teacher"""
    # In a real implementation, this would send a push notification
    # For now, we'll just log it
    logger.info(f"Teacher called by student {student_id} in session {session_id}")
    
    # You could also save this to a notifications table
    return {"message": "Teacher has been notified"}