# app/api/analytics.py
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import csv
import io
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User, UserRole
from app.models.chat import ChatSession, ChatMessage
from app.services.analytics_service import AnalyticsService
from app.models.analytics import SessionAnalytics, StudentProgress

router = APIRouter()

@router.get("/student/{student_id}")
async def get_student_analytics(
    student_id: int,
    days: int = Query(30, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get analytics for a specific student"""
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    analytics = AnalyticsService.get_student_analytics(db, student_id, days)
    return analytics

@router.get("/session/{session_id}")
async def get_session_analytics(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed analytics for a specific session"""
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    analytics = db.query(SessionAnalytics).filter(
        SessionAnalytics.session_id == session_id
    ).first()
    
    if not analytics:
        raise HTTPException(status_code=404, detail="Session analytics not found")
    
    return analytics

@router.get("/export/csv")
async def export_analytics_csv(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export analytics data as CSV for research"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can export data")
    
    # Get export data
    data = AnalyticsService.export_research_data(db, start_date, end_date)
    
    # Create CSV in memory with proper UTF-8 encoding
    output = io.StringIO()
    if data:
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    
    output.seek(0)
    
    # Add UTF-8 BOM for proper Hebrew text display in Excel
    csv_content = output.getvalue()
    csv_bytes = '\uFEFF' + csv_content  # Add BOM
    csv_bytes_encoded = csv_bytes.encode('utf-8')
    
    return StreamingResponse(
        io.BytesIO(csv_bytes_encoded),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename=learnobot_analytics_{datetime.now().strftime('%Y%m%d')}.csv"
        }
    )

@router.get("/export/students/csv")
async def export_students_csv(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export student data with analytics as CSV for Excel analysis"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can export student data")
    
    from app.models.user import StudentProfile
    
    # Get all students (admin only)
    students = db.query(StudentProfile).all()
    
    # Prepare data for CSV export
    export_data = []
    for student in students:
        # Get analytics for this student
        analytics = AnalyticsService.get_student_analytics(db, student.id, days=30)
        
        # Extract summary data
        summary = analytics.get('summary', {}) if isinstance(analytics, dict) else {}
        engagement = analytics.get('engagement_metrics', {}) if isinstance(analytics, dict) else {}
        assistance = analytics.get('assistance_usage', {}) if isinstance(analytics, dict) else {}
        
        # Create row data
        row_data = {
            "student_id": student.id,
            "student_name": student.full_name,
            "grade": student.grade,
            "difficulty_level": student.difficulty_level,
            "difficulties_description": student.difficulties_description,
            "teacher_id": student.teacher_id,
            # Analytics data
            "total_sessions": summary.get('total_sessions', 0),
            "total_time_minutes": summary.get('total_time_minutes', 0),
            "total_messages": summary.get('total_messages', 0),
            "average_session_duration_minutes": summary.get('average_session_duration_minutes', 0),
            "average_messages_per_session": summary.get('average_messages_per_session', 0),
            "average_satisfaction_rating": engagement.get('average_satisfaction', 'N/A'),
            "teacher_calls": engagement.get('teacher_calls', 0),
            "tasks_uploaded": engagement.get('tasks_uploaded', 0),
            "error_rate": engagement.get('error_rate', 0),
            # Assistance usage
            "breakdown_requests": assistance.get('breakdown', 0),
            "example_requests": assistance.get('example', 0),
            "explain_requests": assistance.get('explain', 0),
            "total_assistance_requests": assistance.get('breakdown', 0) + assistance.get('example', 0) + assistance.get('explain', 0),
        }
        
        export_data.append(row_data)
    
    # Create CSV in memory
    output = io.StringIO()
    if export_data:
        writer = csv.DictWriter(output, fieldnames=export_data[0].keys())
        writer.writeheader()
        writer.writerows(export_data)
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=learnobot_students_{datetime.now().strftime('%Y%m%d')}.csv"
        }
    )

@router.get("/summary/teacher/{teacher_id}")
async def get_teacher_summary(
    teacher_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard summary for teacher/manager"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"=== DASHBOARD SUMMARY === Teacher ID: {teacher_id}, User: {current_user.username}, Role: {current_user.role}")
    
    from app.models.user import StudentProfile, TeacherProfile
    from app.models.analytics import SessionAnalytics
    
    # Admin/Manager can see all data, Teachers only their students
    if current_user.role == UserRole.ADMIN:
        # Get all students for admin
        total_students = db.query(StudentProfile).count()
        students_query = db.query(StudentProfile)
        logger.info(f"ADMIN - Total students: {total_students}")
    elif current_user.role == UserRole.TEACHER:
        # Verify teacher_id matches current user or allow viewing own data
        if current_user.teacher_profile and current_user.teacher_profile.id != teacher_id:
            # Teacher trying to access another teacher's data
            raise HTTPException(status_code=403, detail="Access denied")
        
        total_students = db.query(StudentProfile).filter(
            StudentProfile.teacher_id == teacher_id
        ).count()
        students_query = db.query(StudentProfile).filter(
            StudentProfile.teacher_id == teacher_id
        )
        logger.info(f"TEACHER - Total students for teacher_id {teacher_id}: {total_students}")
    else:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get student IDs for filtering sessions
    student_ids = [s.id for s in students_query.all()]
    logger.info(f"Student IDs: {student_ids}")
    
    # Get today's date range
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    logger.info(f"Date range: {today_start} to {today_end}")
    
    # Count today's sessions
    today_sessions = db.query(ChatSession).filter(
        ChatSession.student_id.in_(student_ids),
        ChatSession.started_at >= today_start,
        ChatSession.started_at < today_end
    ).count() if student_ids else 0
    logger.info(f"Today's sessions: {today_sessions}")
    
    # Count help requests (teacher calls) from today's sessions
    if student_ids:
        session_ids = [s.id for s in db.query(ChatSession).filter(
            ChatSession.student_id.in_(student_ids),
            ChatSession.started_at >= today_start,
            ChatSession.started_at < today_end
        ).all()]
        logger.info(f"Session IDs for today: {session_ids}")
        
        help_requests = db.query(func.sum(SessionAnalytics.teacher_calls)).filter(
            SessionAnalytics.session_id.in_(session_ids)
        ).scalar() or 0
        logger.info(f"Help requests: {help_requests}")
    else:
        help_requests = 0
        logger.info("No students, help_requests = 0")
    
    result = {
        "total_students": total_students,
        "today_sessions": today_sessions,
        "help_requests": int(help_requests)
    }
    logger.info(f"=== RETURNING === {result}")
    
    return result

@router.get("/research/patterns")
async def get_research_patterns(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get patterns for research analysis"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Analyze patterns like:
    # - Most effective assistance types
    # - Time of day patterns
    # - Session length vs. progress correlation
    # - Error patterns
    
    # Convert SQLAlchemy results to serializable dictionaries
    assistance_query = db.query(
        SessionAnalytics.learning_progress_score,
        SessionAnalytics.breakdown_count,
        SessionAnalytics.example_count,
        SessionAnalytics.explain_count
    ).filter(
        SessionAnalytics.learning_progress_score.isnot(None)
    ).all()
    
    time_query = db.query(
        func.extract('hour', ChatSession.started_at).label('hour'),
        func.count(ChatSession.id).label('count'),
        func.avg(SessionAnalytics.learning_progress_score).label('avg_progress')
    ).join(
        SessionAnalytics, ChatSession.id == SessionAnalytics.session_id
    ).group_by(
        func.extract('hour', ChatSession.started_at)
    ).all()
    
    mode_query = db.query(
        ChatSession.mode,
        func.count(ChatSession.id).label('count'),
        func.avg(SessionAnalytics.total_duration_seconds).label('avg_duration'),
        func.avg(SessionAnalytics.learning_progress_score).label('avg_progress')
    ).join(
        SessionAnalytics, ChatSession.id == SessionAnalytics.session_id
    ).group_by(
        ChatSession.mode
    ).all()
    
    patterns = {
        "assistance_effectiveness": [
            {
                "progress_score": float(row.learning_progress_score) if row.learning_progress_score else 0,
                "breakdown_count": int(row.breakdown_count) if row.breakdown_count else 0,
                "example_count": int(row.example_count) if row.example_count else 0,
                "explain_count": int(row.explain_count) if row.explain_count else 0
            }
            for row in assistance_query
        ],
        
        "time_patterns": [
            {
                "hour": int(row.hour) if row.hour else 0,
                "session_count": int(row.count) if row.count else 0,
                "avg_progress": float(row.avg_progress) if row.avg_progress else 0
            }
            for row in time_query
        ],
        
        "mode_comparison": [
            {
                "mode": str(row.mode) if row.mode else "unknown",
                "session_count": int(row.count) if row.count else 0,
                "avg_duration": float(row.avg_duration) if row.avg_duration else 0,
                "avg_progress": float(row.avg_progress) if row.avg_progress else 0
            }
            for row in mode_query
        ]
    }
    
    return patterns

@router.get("/students", response_model=List[Dict[str, Any]])
async def get_all_students(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get students for analytics - Admin sees all, Teachers see only their assigned students"""
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    from app.models.user import StudentProfile
    
    if current_user.role == UserRole.ADMIN:
        # Admin sees all students (including admin testing profiles)
        students = db.query(StudentProfile).all()
    else:
        # Teachers only see their assigned students (excludes admin testing profiles)
        students = db.query(StudentProfile).filter(
            StudentProfile.teacher_id == current_user.teacher_profile.id
        ).all()
    
    return [
        {
            "id": student.id,
            "user_id": student.user_id,
            "full_name": student.full_name,
            "grade": student.grade,
            "difficulty_level": student.difficulty_level,
            "difficulties_description": student.difficulties_description,
            "teacher_id": student.teacher_id,
            "profile_image_url": student.profile_image_url
        }
        for student in students
    ]

@router.put("/students/{student_id}")
async def update_student_profile(
    student_id: int,
    student_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update student profile - Admin and Teacher access"""
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    from app.models.user import StudentProfile
    
    # Find the student
    student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Update allowed fields
    if 'full_name' in student_data:
        student.full_name = student_data['full_name']
    if 'grade' in student_data:
        student.grade = student_data['grade']
    if 'difficulty_level' in student_data:
        student.difficulty_level = student_data['difficulty_level']
    if 'difficulties_description' in student_data:
        student.difficulties_description = student_data['difficulties_description']
    
    try:
        db.commit()
        db.refresh(student)
        
        return {
            "id": student.id,
            "user_id": student.user_id,
            "full_name": student.full_name,
            "grade": student.grade,
            "difficulty_level": student.difficulty_level,
            "difficulties_description": student.difficulties_description,
            "teacher_id": student.teacher_id
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update student: {str(e)}")

# Archive endpoints
@router.get("/archive/conversations")
async def get_conversations_archive(
    student_id: Optional[int] = Query(None),
    days: int = Query(30, description="Number of days to retrieve"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get conversation history for archive - Teachers see their students, Admins see all"""
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    from app.models.user import StudentProfile
    
    # Build query for sessions
    try:
        query = db.query(ChatSession).join(
            StudentProfile, 
            ChatSession.student_id == StudentProfile.id
        )
        
        # Add date filter
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(ChatSession.started_at >= cutoff_date)
        
        # Filter by access permissions
        if current_user.role == UserRole.TEACHER:
            if hasattr(current_user, 'teacher_profile') and current_user.teacher_profile:
                query = query.filter(StudentProfile.teacher_id == current_user.teacher_profile.id)
            else:
                # If no teacher profile, return empty result
                return []
        
        # Filter by specific student if requested
        if student_id:
            query = query.filter(ChatSession.student_id == student_id)
        
        sessions = query.order_by(ChatSession.started_at.desc()).all()
    except Exception as e:
        print(f"Database query error in conversations archive: {e}")
        raise HTTPException(status_code=500, detail="Database query failed")
    
    # Format conversation data
    conversations = []
    for session in sessions:
        # Get messages for this session
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).order_by(ChatMessage.timestamp).all()
        
        conversation = {
            "session_id": session.id,
            "student_id": session.student_id,
            "student_name": session.student.full_name,
            "mode": session.mode.value,
            "started_at": session.started_at.isoformat(),
            "ended_at": session.ended_at.isoformat() if session.ended_at else None,
            "message_count": len(messages),
            "duration_minutes": round((session.ended_at - session.started_at).total_seconds() / 60, 1) if session.ended_at else None,
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role.value,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "satisfaction_rating": msg.satisfaction_rating
                }
                for msg in messages
            ]
        }
        conversations.append(conversation)
    
    return conversations

@router.get("/archive/student-progress/{student_id}")
async def get_student_progress_archive(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed progress history for a student"""
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get student profile
    from app.models.user import StudentProfile
    student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Check access permissions
    if current_user.role == UserRole.TEACHER:
        if hasattr(current_user, 'teacher_profile') and current_user.teacher_profile:
            if student.teacher_id != current_user.teacher_profile.id:
                raise HTTPException(status_code=403, detail="Access denied")
        else:
            raise HTTPException(status_code=403, detail="No teacher profile found")
    
    # Get progress data over time (last 90 days with weekly aggregation)
    from sqlalchemy import func
    cutoff_date = datetime.utcnow() - timedelta(days=90)
    
    try:
        weekly_progress = db.query(
            func.extract('week', ChatSession.started_at).label('week'),
            func.extract('year', ChatSession.started_at).label('year'),
            func.count(ChatSession.id).label('sessions'),
            func.avg(SessionAnalytics.learning_progress_score).label('avg_progress'),
            func.sum(SessionAnalytics.total_duration_seconds).label('total_time'),
            func.avg(SessionAnalytics.average_satisfaction).label('avg_satisfaction')
        ).join(
            SessionAnalytics, ChatSession.id == SessionAnalytics.session_id
        ).filter(
            ChatSession.student_id == student_id,
            ChatSession.started_at >= cutoff_date
        ).group_by(
            func.extract('week', ChatSession.started_at),
            func.extract('year', ChatSession.started_at)
        ).order_by('year', 'week').all()
    except Exception as e:
        print(f"Database query error in student progress archive: {e}")
        # Return basic student data with empty progress
        weekly_progress = []
    
    progress_data = [
        {
            "week": int(row.week),
            "year": int(row.year),
            "sessions": int(row.sessions),
            "avg_progress_score": float(row.avg_progress) if row.avg_progress else 0,
            "total_time_minutes": round(float(row.total_time) / 60, 1) if row.total_time else 0,
            "avg_satisfaction": float(row.avg_satisfaction) if row.avg_satisfaction else None
        }
        for row in weekly_progress
    ]
    
    return {
        "student": {
            "id": student.id,
            "name": student.full_name,
            "grade": student.grade,
            "difficulty_level": student.difficulty_level,
            "difficulties_description": student.difficulties_description
        },
        "progress_timeline": progress_data,
        "overall_stats": AnalyticsService.get_student_analytics(db, student_id, 90)
    }

@router.get("/archive/reports/summary")
async def get_summary_report(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate summary report for archive"""
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Set default date range if not provided
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    from app.models.user import StudentProfile
    
    # Base query for sessions
    try:
        sessions_query = db.query(ChatSession).join(
            StudentProfile,
            ChatSession.student_id == StudentProfile.id
        )
        
        # Filter by date range
        sessions_query = sessions_query.filter(
            ChatSession.started_at >= start_date,
            ChatSession.started_at <= end_date
        )
        
        # Filter by access permissions
        if current_user.role == UserRole.TEACHER:
            if hasattr(current_user, 'teacher_profile') and current_user.teacher_profile:
                sessions_query = sessions_query.filter(
                    StudentProfile.teacher_id == current_user.teacher_profile.id
                )
            else:
                # Return empty data if no teacher profile
                return {
                    "period": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "days": (end_date - start_date).days
                    },
                    "summary": {
                        "total_sessions": 0,
                        "unique_students": 0,
                        "total_time_hours": 0,
                        "total_messages": 0,
                        "teacher_calls": 0,
                        "tasks_uploaded": 0,
                        "avg_progress_score": 0,
                        "avg_satisfaction_rating": None
                    },
                    "daily_breakdown": []
                }
        
        sessions = sessions_query.all()
    except Exception as e:
        print(f"Database query error in summary report: {e}")
        sessions = []
    
    # Calculate summary statistics
    total_sessions = len(sessions)
    total_students = len(set(s.student_id for s in sessions))
    
    # Get analytics data
    analytics_data = db.query(SessionAnalytics).filter(
        SessionAnalytics.session_id.in_([s.id for s in sessions])
    ).all()
    
    total_time_seconds = sum(a.total_duration_seconds or 0 for a in analytics_data)
    total_messages = sum(a.total_messages or 0 for a in analytics_data)
    teacher_calls = sum(a.teacher_calls or 0 for a in analytics_data)
    tasks_uploaded = sum(a.tasks_uploaded or 0 for a in analytics_data)
    
    # Calculate averages
    avg_progress = sum(a.learning_progress_score or 0 for a in analytics_data) / len(analytics_data) if analytics_data else 0
    # Calculate average satisfaction safely
    satisfaction_data = [a for a in analytics_data if a.average_satisfaction is not None]
    avg_satisfaction = sum(a.average_satisfaction for a in satisfaction_data) / len(satisfaction_data) if satisfaction_data else None
    
    return {
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days": (end_date - start_date).days
        },
        "summary": {
            "total_sessions": total_sessions,
            "unique_students": total_students,
            "total_time_hours": round(total_time_seconds / 3600, 1),
            "total_messages": total_messages,
            "teacher_calls": teacher_calls,
            "tasks_uploaded": tasks_uploaded,
            "avg_progress_score": round(avg_progress, 1),
            "avg_satisfaction_rating": round(avg_satisfaction, 1) if avg_satisfaction else None
        },
        "daily_breakdown": [
            # This would be filled with daily statistics - simplified for now
        ]
    }

@router.get("/export/comprehensive-csv")
async def export_comprehensive_csv(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export comprehensive analytics data as CSV with all metrics"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can export comprehensive data")
    
    # Set default date range if not provided
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    from app.models.user import StudentProfile
    
    # Get all relevant data
    try:
        sessions_query = db.query(ChatSession).join(
            StudentProfile,
            ChatSession.student_id == StudentProfile.id
        ).filter(
            ChatSession.started_at >= start_date,
            ChatSession.started_at <= end_date
        )
        
        # Admin only - no filtering needed
        
        sessions = sessions_query.all()
    except Exception as e:
        print(f"Database query error in comprehensive CSV export: {e}")
        sessions = []
    
    # Prepare comprehensive CSV data
    export_data = []
    for session in sessions:
        # Get analytics for this session
        analytics = db.query(SessionAnalytics).filter(
            SessionAnalytics.session_id == session.id
        ).first()
        
        # Get messages count for this session
        message_count = db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).count()
        
        # Calculate duration if session ended
        duration_seconds = None
        duration_minutes = None
        if session.ended_at and session.started_at:
            duration_seconds = int((session.ended_at - session.started_at).total_seconds())
            duration_minutes = round(duration_seconds / 60, 2)
        
        # Determine if session completed successfully
        # A session is considered successful if it ended and has messages
        completed_successfully = session.ended_at is not None and message_count > 0
        
        # Get satisfaction rating from messages
        satisfaction_ratings = db.query(ChatMessage.satisfaction_rating).filter(
            ChatMessage.session_id == session.id,
            ChatMessage.satisfaction_rating.isnot(None)
        ).all()
        average_satisfaction = None
        if satisfaction_ratings:
            ratings = [r[0] for r in satisfaction_ratings if r[0] is not None]
            if ratings:
                average_satisfaction = round(sum(ratings) / len(ratings), 2)
        
        # Create comprehensive row
        row_data = {
            "session_id": session.id,
            "student_id": session.student_id,
            "student_name": session.student.full_name,
            "grade": session.student.grade,
            "difficulty_level": session.student.difficulty_level,
            "teacher_id": session.student.teacher_id,
            "mode": session.mode.value,
            "started_at": session.started_at.isoformat(),
            "ended_at": session.ended_at.isoformat() if session.ended_at else None,
            "duration_seconds": analytics.total_duration_seconds if analytics else duration_seconds,
            "duration_minutes": round(analytics.total_duration_seconds / 60, 2) if analytics and analytics.total_duration_seconds else duration_minutes,
            "total_messages": analytics.total_messages if analytics else message_count,
            "student_messages": analytics.student_messages if analytics else message_count // 2,  # Rough estimate
            "ai_messages": analytics.ai_messages if analytics else message_count // 2,  # Rough estimate
            "teacher_calls": analytics.teacher_calls if analytics else 0,
            "tasks_uploaded": analytics.tasks_uploaded if analytics else 0,
            "errors_encountered": analytics.errors_encountered if analytics else 0,
            "breakdown_requests": analytics.breakdown_count if analytics else 0,
            "example_requests": analytics.example_count if analytics else 0,
            "explain_requests": analytics.explain_count if analytics else 0,
            "total_assistance_requests": (analytics.breakdown_count or 0) + (analytics.example_count or 0) + (analytics.explain_count or 0) if analytics else 0,
            "learning_progress_score": analytics.learning_progress_score if analytics else (85.0 if completed_successfully else 50.0),  # Default based on completion
            "average_satisfaction": analytics.average_satisfaction if analytics else average_satisfaction,
            "average_response_time_ms": analytics.average_response_time_ms if analytics else 2000,  # Default 2 seconds
            "completed_successfully": analytics.completed_successfully if analytics else completed_successfully,
            "difficulties_description": session.student.difficulties_description or "לא צוין",
        }
        
        export_data.append(row_data)
    
    # Create CSV in memory with proper UTF-8 encoding
    output = io.StringIO()
    if export_data:
        writer = csv.DictWriter(output, fieldnames=export_data[0].keys())
        writer.writeheader()
        writer.writerows(export_data)
    
    output.seek(0)
    
    # Add UTF-8 BOM for proper Hebrew text display in Excel
    csv_content = output.getvalue()
    csv_bytes = '\uFEFF' + csv_content  # Add BOM
    csv_bytes_encoded = csv_bytes.encode('utf-8')
    
    return StreamingResponse(
        io.BytesIO(csv_bytes_encoded),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename=learnobot_comprehensive_{datetime.now().strftime('%Y%m%d')}.csv"
        }
    )
