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

@router.get("/export/students/csv")
async def export_students_csv(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export student data with analytics as CSV for Excel analysis"""
    if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
        raise HTTPException(status_code=403, detail="Only admins and teachers can export student data")
    
    from app.models.user import StudentProfile
    
    # Get all students (admin sees all, teachers see only their students)
    if current_user.role == UserRole.ADMIN:
        students = db.query(StudentProfile).all()
    else:
        students = db.query(StudentProfile).filter(
            StudentProfile.teacher_id == current_user.teacher_profile.id
        ).all()
    
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
            "teacher_id": student.teacher_id
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
