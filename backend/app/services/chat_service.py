# app/services/chat_service.py - UPDATED WITH ANALYTICS
from sqlalchemy.orm import Session
from app.models.chat import ChatSession, ChatMessage, InteractionMode, MessageRole
from app.models.task import Task
from app.ai.chains.instruction_chain import InstructionProcessor
from app.ai.mediation_strategies import MediationManager, MediationStrategy
from app.services.hebrew_mediation_service import hebrew_mediation_service
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
        
        # Cleanup Hebrew mediation resources
        hebrew_mediation_service.cleanup_session(session_id)

async def process_message(
    db: Session,
    session_id: int,
    user_id: int,
    message: str,
    assistance_type: Optional[str] = None,
    provider: Optional[str] = None
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
    
    # Save user message and commit immediately
    user_message = ChatMessage(
        session_id=session_id,
        user_id=user_id,
        role=MessageRole.USER,
        content=message
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    # Get session data and close the database session before AI processing
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    student = session.student
    student_context = {
        "name": student.full_name,
        "grade": student.grade,
        "difficulty_level": student.difficulty_level,
        "difficulties": student.difficulties_description,
        "language_preference": student.user.language_preference
    }
    mode = session.mode
    language_pref = student.user.language_preference
    
    try:
        # AI processing happens here WITHOUT holding database session
        
        # Track AI generation time separately from educational delay
        ai_generation_start = time.time()
        
        # Check if Hebrew mediation should be used (only for local models)
        if hebrew_mediation_service.should_use_mediation(session, assistance_type, provider):
            # Use sophisticated Hebrew mediation system
            mediation_result = hebrew_mediation_service.process_mediated_response(
                db=db,
                session_id=session_id,
                instruction=message,
                student_response=message,  # Pass the actual student message
                provider=provider,
                assistance_type=assistance_type
            )
            
            ai_response = mediation_result["response"]
            ai_generation_time = time.time() - ai_generation_start
            
            # Log mediation strategy used
            AnalyticsService.log_event(
                db=db,
                session_id=session_id,
                user_id=user_id,
                event_type=EventType.AI_RESPONSE,
                event_data={
                    "strategy_used": mediation_result["strategy_used"],
                    "comprehension_level": mediation_result["comprehension_level"],
                    "attempt_count": mediation_result["attempt_count"],
                    "mediation_system": "hebrew_chain"
                }
            )
            
        elif session.mode == InteractionMode.PRACTICE:
            # Student Selection mode - use existing simple logic
            if assistance_type == "breakdown":
                ai_response = instruction_processor.breakdown_instruction(
                    message, student.difficulty_level, language_pref, provider
                )
            elif assistance_type == "example":
                ai_response = instruction_processor.provide_example(
                    message, "main concept", language_pref, provider
                )
            elif assistance_type == "explain":
                ai_response = instruction_processor.explain_instruction(
                    message, student.difficulty_level, language_pref, provider
                )
            else:
                # Fallback to analysis
                analysis = instruction_processor.analyze_instruction(message, student_context, provider)
                ai_response = analysis["analysis"]
            
            ai_generation_time = time.time() - ai_generation_start
        else:
            # Test mode fallback (shouldn't reach here if mediation is working)
            previous_attempts = db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id,
                ChatMessage.role == MessageRole.ASSISTANT
            ).count()
            
            if previous_attempts >= 3:
                ai_response = "הגעת למספר המקסימלי של ניסיונות עזרה לשאלה זו. אנא עבור לשאלה הבאה או פנה למורה שלך."
            else:
                strategy = mediation_manager.get_next_strategy([], "test")
                ai_response = mediation_manager.apply_strategy(
                    strategy, message, instruction_processor
                )
            
            ai_generation_time = time.time() - ai_generation_start
        
        # Educational response delay removed for better user experience
        # Models now respond immediately after generation
        
        # Calculate total response time (including delay)
        total_time = time.time() - start_time
        response_time_ms = int(total_time * 1000)
        
        # Log AI response event
        AnalyticsService.log_event(
            db=db,
            session_id=session_id,
            user_id=user_id,
            event_type=EventType.AI_RESPONSE,
            event_data={
                "output_length": len(ai_response),
                "mode": session.mode.value,
                "provider": getattr(instruction_processor, 'provider', 'default'),
                "ai_generation_time_ms": int(ai_generation_time * 1000),
                "educational_delay_seconds": 0,  # Delay removed for better UX
                "total_response_time_ms": response_time_ms
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
    
    # Save AI response using a fresh database session
    from app.core.database import SessionLocal
    ai_db = SessionLocal()
    try:
        ai_message = ChatMessage(
            session_id=session_id,
            user_id=user_id,
            role=MessageRole.ASSISTANT,
            content=ai_response
        )
        ai_db.add(ai_message)
        ai_db.commit()
        ai_db.refresh(ai_message)
    finally:
        ai_db.close()
    
    # Schedule automatic teacher notification check after 5 minutes if no student response
    import threading
    from functools import partial
    
    def delayed_teacher_notification():
        """Check if student responded within 5 minutes, if not, notify teacher"""
        import time
        time.sleep(300)  # Wait 5 minutes (300 seconds)
        
        # Check if student has sent any messages since this AI response
        try:
            from app.core.database import SessionLocal
            with SessionLocal() as check_db:
                recent_student_message = check_db.query(ChatMessage).filter(
                    ChatMessage.session_id == session_id,
                    ChatMessage.role == MessageRole.USER,
                    ChatMessage.timestamp > ai_message.timestamp
                ).first()
                
                if not recent_student_message:
                    # No student response in 5 minutes - notify teacher
                    session = check_db.query(ChatSession).filter(ChatSession.id == session_id).first()
                    if session and session.student:
                        student = session.student
                        from app.models.notification import TeacherNotification, NotificationType, NotificationPriority
                        
                        # Create automatic notification
                        auto_notification = TeacherNotification(
                            teacher_id=student.teacher_id,
                            student_id=student.user_id,
                            session_id=session_id,
                            type=NotificationType.SYSTEM_ALERT,
                            priority=NotificationPriority.NORMAL,
                            title="התלמיד לא הגיב במשך 5 דקות",
                            message=f"{student.full_name} לא הגיב לבוט במשך יותר מ-5 דקות. ייתכן שהוא צריך עזרה נוספת.",
                            extra_data=f'{{"auto_generated": true, "last_ai_message_id": {ai_message.id}, "minutes_without_response": 5}}'
                        )
                        
                        check_db.add(auto_notification)
                        check_db.commit()
                        logger.info(f"Automatic teacher notification created for inactive student {student.user_id} in session {session_id}")
        except Exception as e:
            logger.error(f"Error creating automatic teacher notification: {e}")
    
    # Start the background check (only if student has a teacher assigned)
    try:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if session and session.student and session.student.teacher_id:
            notification_thread = threading.Thread(target=delayed_teacher_notification)
            notification_thread.daemon = True  # Thread will die when main program exits
            notification_thread.start()
    except Exception as e:
        logger.warning(f"Could not start automatic notification thread: {e}")
    
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
    from app.models.notification import TeacherNotification, NotificationType, NotificationPriority
    from app.models.user import StudentProfile
    
    # Get student information
    student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if not student:
        raise ValueError("Student not found")
    
    if not student.teacher_id:
        raise ValueError("Student is not assigned to a teacher")
    
    # Create notification record
    notification = TeacherNotification(
        teacher_id=student.teacher_id,
        student_id=student_id,
        session_id=session_id,
        type=NotificationType.TEACHER_CALL,
        priority=NotificationPriority.HIGH,
        title="בקשת עזרה מתלמיד",
        message=f"{student.full_name} מבקש עזרה במהלך השיחה עם הבוט",
        extra_data=f'{{"timestamp": "{datetime.utcnow().isoformat()}", "session_id": {session_id}}}'
    )
    
    db.add(notification)
    db.commit()
    db.refresh(notification)
    
    # Log teacher call event for analytics
    AnalyticsService.log_event(
        db=db,
        session_id=session_id,
        user_id=student_id,
        event_type=EventType.TEACHER_CALLED,
        event_data={
            "timestamp": datetime.utcnow().isoformat(),
            "notification_id": notification.id
        }
    )
    
    # TODO: In a production implementation, this would send a real-time push notification
    # For now, we create a database record that teachers can check
    logger.info(f"Teacher call notification created: {notification.id} for student {student_id} in session {session_id}")
    
    return {
        "message": "הודעה נשלחה למורה",
        "notification_id": notification.id,
        "teacher_id": student.teacher_id,
        "timestamp": notification.created_at.isoformat()
    }

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