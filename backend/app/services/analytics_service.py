# app/services/analytics_service.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.analytics import InteractionLog, SessionAnalytics, EventType, StudentProgress
from app.models.chat import ChatSession, ChatMessage
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json

class AnalyticsService:
    @staticmethod
    def log_event(
        db: Session,
        session_id: int,
        user_id: int,
        event_type: EventType,
        event_data: Dict[str, Any] = None,
        response_time_ms: int = None
    ):
        """Log any interaction event"""
        log = InteractionLog(
            session_id=session_id,
            user_id=user_id,
            event_type=event_type,
            event_data=event_data or {},
            response_time_ms=response_time_ms,
            input_length=event_data.get('input_length') if event_data else None,
            output_length=event_data.get('output_length') if event_data else None
        )
        db.add(log)
        db.commit()
        
        # Update session analytics in real-time
        AnalyticsService._update_session_analytics(db, session_id, event_type, event_data)
    
    @staticmethod
    def _update_session_analytics(
        db: Session,
        session_id: int,
        event_type: EventType,
        event_data: Dict[str, Any] = None
    ):
        """Update session analytics based on events"""
        analytics = db.query(SessionAnalytics).filter(
            SessionAnalytics.session_id == session_id
        ).first()
        
        if not analytics:
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            analytics = SessionAnalytics(
                session_id=session_id,
                student_id=session.student_id if session else None
            )
            db.add(analytics)
        
        # Update counters based on event type
        if event_type == EventType.MESSAGE_SENT:
            analytics.student_messages += 1
            analytics.total_messages += 1
        elif event_type == EventType.AI_RESPONSE:
            analytics.ai_messages += 1
            analytics.total_messages += 1
        elif event_type == EventType.ASSISTANCE_REQUESTED:
            assistance_type = event_data.get('assistance_type') if event_data else None
            if assistance_type == 'breakdown':
                analytics.breakdown_count += 1
            elif assistance_type == 'example':
                analytics.example_count += 1
            elif assistance_type == 'explain':
                analytics.explain_count += 1
        elif event_type == EventType.TASK_UPLOADED:
            analytics.tasks_uploaded += 1
        elif event_type == EventType.TEACHER_CALLED:
            analytics.teacher_calls += 1
        elif event_type == EventType.ERROR_OCCURRED:
            analytics.errors_encountered += 1
        
        db.commit()
    
    @staticmethod
    def finalize_session_analytics(db: Session, session_id: int):
        """Calculate final metrics when session ends"""
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            return
        
        analytics = db.query(SessionAnalytics).filter(
            SessionAnalytics.session_id == session_id
        ).first()
        
        if not analytics:
            return
        
        # Calculate duration
        if session.ended_at and session.started_at:
            analytics.total_duration_seconds = int(
                (session.ended_at - session.started_at).total_seconds()
            )
        
        # Calculate average response time
        response_times = db.query(InteractionLog.response_time_ms).filter(
            InteractionLog.session_id == session_id,
            InteractionLog.response_time_ms.isnot(None)
        ).all()
        
        if response_times:
            analytics.average_response_time_ms = sum(rt[0] for rt in response_times) / len(response_times)
        
        # Calculate average satisfaction
        ratings = db.query(ChatMessage.satisfaction_rating).filter(
            ChatMessage.session_id == session_id,
            ChatMessage.satisfaction_rating.isnot(None)
        ).all()
        
        if ratings:
            analytics.average_satisfaction = sum(r[0] for r in ratings) / len(ratings)
        
        # Calculate learning progress score (simplified version)
        # Higher score = fewer assistance requests relative to messages
        if analytics.total_messages > 0:
            assistance_ratio = (analytics.breakdown_count + analytics.example_count + analytics.explain_count) / analytics.total_messages
            analytics.learning_progress_score = max(0, min(100, (1 - assistance_ratio) * 100))
        
        analytics.completed_successfully = analytics.errors_encountered == 0
        
        db.commit()
    
    @staticmethod
    def get_student_analytics(db: Session, student_id: int, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive analytics for a student"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get all sessions for the student
        sessions = db.query(SessionAnalytics).filter(
            SessionAnalytics.student_id == student_id,
            SessionAnalytics.session.has(ChatSession.started_at >= cutoff_date)
        ).all()
        
        if not sessions:
            return {"message": "No data available"}
        
        # Aggregate metrics
        total_sessions = len(sessions)
        total_time = sum(s.total_duration_seconds or 0 for s in sessions)
        total_messages = sum(s.total_messages for s in sessions)
        
        # Calculate trends
        daily_progress = db.query(
            func.date(ChatSession.started_at).label('date'),
            func.count(SessionAnalytics.id).label('sessions'),
            func.avg(SessionAnalytics.learning_progress_score).label('avg_progress')
        ).join(
            ChatSession, SessionAnalytics.session_id == ChatSession.id
        ).filter(
            SessionAnalytics.student_id == student_id,
            ChatSession.started_at >= cutoff_date
        ).group_by(
            func.date(ChatSession.started_at)
        ).all()
        
        return {
            "summary": {
                "total_sessions": total_sessions,
                "total_time_minutes": total_time // 60,
                "total_messages": total_messages,
                "average_session_duration_minutes": (total_time / total_sessions) // 60 if total_sessions > 0 else 0,
                "average_messages_per_session": total_messages / total_sessions if total_sessions > 0 else 0,
            },
            "assistance_usage": {
                "breakdown": sum(s.breakdown_count for s in sessions),
                "example": sum(s.example_count for s in sessions),
                "explain": sum(s.explain_count for s in sessions),
            },
            "progress_trend": [
                {
                    "date": str(day.date),
                    "sessions": day.sessions,
                    "average_progress": float(day.avg_progress) if day.avg_progress else 0
                }
                for day in daily_progress
            ],
            "engagement_metrics": {
                "average_satisfaction": sum(s.average_satisfaction or 0 for s in sessions if s.average_satisfaction) / len([s for s in sessions if s.average_satisfaction]) if any(s.average_satisfaction for s in sessions) else None,
                "teacher_calls": sum(s.teacher_calls for s in sessions),
                "tasks_uploaded": sum(s.tasks_uploaded for s in sessions),
                "error_rate": sum(s.errors_encountered for s in sessions) / total_sessions if total_sessions > 0 else 0
            }
        }
    
    @staticmethod
    def export_research_data(db: Session, start_date: datetime = None, end_date: datetime = None) -> List[Dict[str, Any]]:
        """Export comprehensive data for research analysis"""
        query = db.query(InteractionLog).join(ChatSession).join(SessionAnalytics)
        
        if start_date:
            query = query.filter(InteractionLog.timestamp >= start_date)
        if end_date:
            query = query.filter(InteractionLog.timestamp <= end_date)
        
        logs = query.all()
        
        # Format for export (CSV/Excel friendly)
        export_data = []
        for log in logs:
            session_analytics = db.query(SessionAnalytics).filter(
                SessionAnalytics.session_id == log.session_id
            ).first()
            
            export_data.append({
                "timestamp": log.timestamp.isoformat(),
                "session_id": log.session_id,
                "user_id": log.user_id,
                "event_type": log.event_type.value,
                "response_time_ms": log.response_time_ms,
                "input_length": log.input_length,
                "output_length": log.output_length,
                "event_data": json.dumps(log.event_data) if log.event_data else None,
                # Session-level metrics
                "session_total_duration": session_analytics.total_duration_seconds if session_analytics else None,
                "session_total_messages": session_analytics.total_messages if session_analytics else None,
                "session_learning_progress": session_analytics.learning_progress_score if session_analytics else None,
            })
        
        return export_data