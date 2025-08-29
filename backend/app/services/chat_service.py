# app/services/chat_service.py - UPDATED WITH ANALYTICS
from sqlalchemy.orm import Session
from app.models.chat import ChatSession, ChatMessage, InteractionMode, MessageRole
from app.models.task import Task
from app.ai.chains.instruction_chain import InstructionProcessor
from app.ai.mediation_strategies import MediationManager, MediationStrategy
from app.services.analytics_service import AnalyticsService
from app.models.analytics import EventType
from typing import Optional
from datetime import datetime
import logging
import time

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
    
    # Log session start
    AnalyticsService.log_event(
        db=db,
        session_id=session.id,
        user_id=session.student.user_id,
        event_type=EventType.SESSION_START,
        event_data={"mode": mode.value}
    )
    
    return session

async def end_session(db: Session, session_id: int):
    """End a chat session and finalize analytics"""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if session:
        session.ended_at = datetime.utcnow()
        db.commit()
        
        # Log session end
        AnalyticsService.log_event(
            db=db,
            session_id=session_id,
            user_id=session.student.user_id,
            event_type=EventType.SESSION_END,
            event_data={"duration_seconds": (session.ended_at - session.started_at).total_seconds()}
        )
        
        # Finalize analytics
        AnalyticsService.finalize_session_analytics(db, session_id)

async def process_message(
    db: Session,
    session_id: int,
    user_id: int,
    message: str,
    assistance_type: Optional[str] = None
) -> ChatMessage:
    """Process a user message and generate AI response"""
    
    # Track timing
    start_time = time.time()
    
    # Log message sent event
    AnalyticsService.log_event(
        db=db,
        session_id=session_id,
        user_id=user_id,
        event_type=EventType.MESSAGE_SENT,
        event_data={
            "input_length": len(message),
            "assistance_type": assistance_type
        }
    )
    
    # Log assistance request if applicable
    if assistance_type:
        AnalyticsService.log_event(
            db=db,
            session_id=session_id,
            user_id=user_id,
            event_type=EventType.ASSISTANCE_REQUESTED,
            event_data={"assistance_type": assistance_type}
        )
    
    # Save user message
    user_message = ChatMessage(
        session_id=session_id,
        user_id=user_id,
        role=MessageRole.USER,
        content=message
    )
    db.add(user_message)
    db.commit()
    
    try:
        # Get session details
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        student = session.student
        
        # Prepare student context
        student_context = {
            "name": student.full_name,
            "grade": student.grade,
            "difficulty_level": student.difficulty_level,
            "difficulties": student.difficulties_description,
            "language_preference": student.user.language_preference
        }
        
        # Generate AI response based on mode and assistance type
        language_pref = student.user.language_preference
        
        if session.mode == InteractionMode.PRACTICE:
            if assistance_type == "breakdown":
                ai_response = instruction_processor.breakdown_instruction(
                    message, student.difficulty_level, language_pref
                )
            elif assistance_type == "example":
                ai_response = instruction_processor.provide_example(
                    message, "main concept", language_pref
                )
            elif assistance_type == "explain":
                ai_response = instruction_processor.explain_instruction(
                    message, student.difficulty_level, language_pref
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
                ai_response = "הגעת למספר המקסימלי של ניסיונות עזרה לשאלה זו. אנא עבור לשאלה הבאה או פנה למורה שלך."
            else:
                # Provide minimal assistance
                strategy = mediation_manager.get_next_strategy([], "test")
                ai_response = mediation_manager.apply_strategy(
                    strategy, message, instruction_processor
                )
        
        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Log AI response event
        AnalyticsService.log_event(
            db=db,
            session_id=session_id,
            user_id=user_id,
            event_type=EventType.AI_RESPONSE,
            event_data={
                "output_length": len(ai_response),
                "mode": session.mode.value,
                "provider": getattr(instruction_processor, 'provider', 'default')
            },
            response_time_ms=response_time_ms
        )
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        
        # Log error
        AnalyticsService.log_event(
            db=db,
            session_id=session_id,
            user_id=user_id,
            event_type=EventType.ERROR_OCCURRED,
            event_data={"error": str(e), "error_type": type(e).__name__}
        )
        
        ai_response = "מצטער, נתקלתי בבעיה. אנא נסה שוב או פנה למורה."
    
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
    
    # Log task upload event
    AnalyticsService.log_event(
        db=db,
        session_id=session_id,
        user_id=student_id,
        event_type=EventType.TASK_UPLOADED,
        event_data={
            "image_size": len(image_data),
            "extracted_text_length": len(extracted_text)
        }
    )
    
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
        message=f"אני צריך עזרה עם המשימה הזו: {extracted_text}"
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
    
    # Log rating event
    AnalyticsService.log_event(
        db=db,
        session_id=message.session_id,
        user_id=user_id,
        event_type=EventType.RATING_GIVEN,
        event_data={"rating": rating, "message_id": message_id}
    )
    
    return {"message": "Rating saved successfully"}

async def call_teacher(db: Session, session_id: int, student_id: int):
    """Send a help request notification to the teacher"""
    
    # Log teacher call event
    AnalyticsService.log_event(
        db=db,
        session_id=session_id,
        user_id=student_id,
        event_type=EventType.TEACHER_CALLED,
        event_data={"timestamp": datetime.utcnow().isoformat()}
    )
    
    # In a real implementation, this would send a push notification
    # For now, we'll just log it
    logger.info(f"Teacher called by student {student_id} in session {session_id}")
    
    # You could also save this to a notifications table
    return {"message": "Teacher has been notified"}

# Additional analytics helpers

def get_session_summary(db: Session, session_id: int) -> dict:
    """Get a summary of a session for quick review"""
    from app.models.analytics import SessionAnalytics
    
    analytics = db.query(SessionAnalytics).filter(
        SessionAnalytics.session_id == session_id
    ).first()
    
    if not analytics:
        return {"error": "No analytics found for this session"}
    
    return {
        "duration_minutes": analytics.total_duration_seconds // 60 if analytics.total_duration_seconds else 0,
        "messages": analytics.total_messages,
        "assistance_used": {
            "breakdown": analytics.breakdown_count,
            "example": analytics.example_count,
            "explain": analytics.explain_count
        },
        "average_response_time_ms": analytics.average_response_time_ms,
        "satisfaction": analytics.average_satisfaction,
        "progress_score": analytics.learning_progress_score,
        "teacher_interventions": analytics.teacher_calls,
        "errors": analytics.errors_encountered
    }