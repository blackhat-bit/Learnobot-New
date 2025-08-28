# app/api/analytics.py
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from datetime import datetime, timedelta
import csv
import io
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User, UserRole
from app.models.chat import ChatSession
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
    
    # Create CSV in memory
    output = io.StringIO()
    if data:
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=learnobot_analytics_{datetime.now().strftime('%Y%m%d')}.csv"
        }
    )

@router.get("/summary/teacher/{teacher_id}")
async def get_teacher_summary(
    teacher_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get summary analytics for all students under a teacher"""
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get all students for this teacher
    from app.models.user import StudentProfile
    students = db.query(StudentProfile).filter(
        StudentProfile.teacher_id == teacher_id
    ).all()
    
    summary = []
    for student in students:
        analytics = AnalyticsService.get_student_analytics(db, student.id, 30)
        summary.append({
            "student_id": student.id,
            "student_name": student.full_name,
            "analytics": analytics
        })
    
    return summary

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
