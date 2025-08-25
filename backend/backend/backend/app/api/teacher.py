from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func

from app.core.database import get_db
from app.core.dependencies import get_current_teacher
from app.models.user import User
from app.models.task import Task, TaskSubmission
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskBase,
    TaskSummary,
    TaskDetail,
    TaskSubmissionSummary,
    TaskSubmissionDetail,
    TaskSubmissionGrade,
    TaskAnalytics
)
from app.schemas.user import UserPublic

router = APIRouter()


@router.post("/tasks", response_model=TaskDetail, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    current_teacher: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Create a new task/assignment."""
    
    db_task = Task(
        title=task_data.title,
        description=task_data.description,
        instructions=task_data.instructions,
        task_type=task_data.task_type,
        subject=task_data.subject,
        difficulty_level=task_data.difficulty_level,
        estimated_duration=task_data.estimated_duration,
        max_points=task_data.max_points,
        teacher_id=current_teacher.id,
        course_code=task_data.course_code,
        due_date=task_data.due_date,
        late_submission_allowed=task_data.late_submission_allowed,
        ai_assistance_enabled=task_data.ai_assistance_enabled,
        ai_hint_level=task_data.ai_hint_level,
        auto_feedback_enabled=task_data.auto_feedback_enabled,
        resources=task_data.resources,
        rubric=task_data.rubric
    )
    
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    return db_task


@router.get("/tasks", response_model=List[TaskSummary])
async def get_teacher_tasks(
    current_teacher: User = Depends(get_current_teacher),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None),
    subject: Optional[str] = Query(None)
):
    """Get tasks created by the teacher."""
    
    query = db.query(Task).filter(Task.teacher_id == current_teacher.id)
    
    if status:
        query = query.filter(Task.status == status)
    
    if subject:
        query = query.filter(Task.subject == subject)
    
    tasks = query.order_by(desc(Task.created_at)).offset(skip).limit(limit).all()
    
    # Add submission count for each task
    task_summaries = []
    for task in tasks:
        submission_count = db.query(TaskSubmission).filter(TaskSubmission.task_id == task.id).count()
        
        task_summaries.append(TaskSummary(
            id=task.id,
            title=task.title,
            task_type=task.task_type,
            status=task.status,
            due_date=task.due_date,
            max_points=task.max_points,
            submission_count=submission_count,
            created_at=task.created_at
        ))
    
    return task_summaries


@router.get("/tasks/{task_id}", response_model=TaskDetail)
async def get_task(
    task_id: int,
    current_teacher: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get a specific task."""
    
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.teacher_id == current_teacher.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return task


@router.put("/tasks/{task_id}", response_model=TaskDetail)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    current_teacher: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Update a task."""
    
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.teacher_id == current_teacher.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Update fields if provided
    for field, value in task_data.dict(exclude_unset=True).items():
        setattr(task, field, value)
    
    db.commit()
    db.refresh(task)
    
    return task


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: int,
    current_teacher: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Delete a task."""
    
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.teacher_id == current_teacher.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    db.delete(task)
    db.commit()
    
    return {"message": "Task deleted successfully"}


@router.get("/tasks/{task_id}/submissions", response_model=List[TaskSubmissionSummary])
async def get_task_submissions(
    task_id: int,
    current_teacher: User = Depends(get_current_teacher),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: Optional[str] = Query(None)
):
    """Get submissions for a task."""
    
    # Verify task ownership
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.teacher_id == current_teacher.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    query = db.query(TaskSubmission).options(
        joinedload(TaskSubmission.student)
    ).filter(TaskSubmission.task_id == task_id)
    
    if status:
        query = query.filter(TaskSubmission.status == status)
    
    submissions = query.order_by(desc(TaskSubmission.created_at)).offset(skip).limit(limit).all()
    
    # Format response
    submission_summaries = []
    for submission in submissions:
        submission_summaries.append(TaskSubmissionSummary(
            id=submission.id,
            student_id=submission.student_id,
            student_name=submission.student.full_name,
            status=submission.status,
            score=submission.score,
            submitted_at=submission.submitted_at,
            graded_at=submission.graded_at
        ))
    
    return submission_summaries


@router.get("/tasks/{task_id}/submissions/{submission_id}", response_model=TaskSubmissionDetail)
async def get_submission(
    task_id: int,
    submission_id: int,
    current_teacher: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get a specific submission."""
    
    # Verify task ownership
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.teacher_id == current_teacher.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    submission = db.query(TaskSubmission).filter(
        TaskSubmission.id == submission_id,
        TaskSubmission.task_id == task_id
    ).first()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    return submission


@router.post("/tasks/{task_id}/submissions/{submission_id}/grade")
async def grade_submission(
    task_id: int,
    submission_id: int,
    grade_data: TaskSubmissionGrade,
    current_teacher: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Grade a submission."""
    
    # Verify task ownership
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.teacher_id == current_teacher.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    submission = db.query(TaskSubmission).filter(
        TaskSubmission.id == submission_id,
        TaskSubmission.task_id == task_id
    ).first()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    # Validate score
    if grade_data.score > task.max_points:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Score cannot exceed maximum points ({task.max_points})"
        )
    
    # Update submission with grade
    submission.score = grade_data.score
    submission.max_score = task.max_points
    submission.grade_percentage = f"{(grade_data.score / task.max_points) * 100:.1f}%"
    submission.teacher_feedback = grade_data.teacher_feedback
    submission.feedback_summary = grade_data.feedback_summary
    submission.status = "graded"
    submission.graded_at = func.now()
    
    db.commit()
    
    return {"message": "Submission graded successfully"}


@router.get("/tasks/{task_id}/analytics", response_model=TaskAnalytics)
async def get_task_analytics(
    task_id: int,
    current_teacher: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get analytics for a task."""
    
    # Verify task ownership
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.teacher_id == current_teacher.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Get submission statistics
    submissions = db.query(TaskSubmission).filter(TaskSubmission.task_id == task_id).all()
    
    total_submissions = len(submissions)
    completed_submissions = len([s for s in submissions if s.status in ["submitted", "graded"]])
    
    # Calculate average score
    graded_submissions = [s for s in submissions if s.score is not None]
    average_score = sum(s.score for s in graded_submissions) / len(graded_submissions) if graded_submissions else None
    
    # Calculate completion rate
    completion_rate = (completed_submissions / total_submissions * 100) if total_submissions > 0 else 0
    
    # Calculate average time spent
    timed_submissions = [s for s in submissions if s.time_spent is not None]
    average_time_spent = sum(s.time_spent for s in timed_submissions) / len(timed_submissions) if timed_submissions else None
    
    # AI usage statistics
    ai_usage_stats = {
        "total_hints_used": sum(s.ai_hints_used for s in submissions),
        "students_using_ai": len([s for s in submissions if s.ai_hints_used > 0]),
        "average_hints_per_student": sum(s.ai_hints_used for s in submissions) / total_submissions if total_submissions > 0 else 0
    }
    
    return TaskAnalytics(
        total_submissions=total_submissions,
        completed_submissions=completed_submissions,
        average_score=average_score,
        completion_rate=completion_rate,
        average_time_spent=average_time_spent,
        ai_usage_stats=ai_usage_stats
    )


@router.get("/students", response_model=List[UserPublic])
async def get_students(
    current_teacher: User = Depends(get_current_teacher),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500)
):
    """Get list of students (for teachers to see who can be assigned tasks)."""
    
    students = db.query(User).filter(
        User.role == "student",
        User.is_active == True
    ).offset(skip).limit(limit).all()
    
    return students


@router.get("/dashboard")
async def get_teacher_dashboard(
    current_teacher: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get teacher dashboard statistics."""
    
    # Get basic counts
    total_tasks = db.query(Task).filter(Task.teacher_id == current_teacher.id).count()
    active_tasks = db.query(Task).filter(
        Task.teacher_id == current_teacher.id,
        Task.status == "published"
    ).count()
    
    # Get submission counts
    total_submissions = db.query(TaskSubmission).join(Task).filter(
        Task.teacher_id == current_teacher.id
    ).count()
    
    pending_grading = db.query(TaskSubmission).join(Task).filter(
        Task.teacher_id == current_teacher.id,
        TaskSubmission.status == "submitted"
    ).count()
    
    # Recent activity (last 7 days)
    from datetime import datetime, timedelta
    recent_date = datetime.utcnow() - timedelta(days=7)
    
    recent_submissions = db.query(TaskSubmission).join(Task).filter(
        Task.teacher_id == current_teacher.id,
        TaskSubmission.created_at >= recent_date
    ).count()
    
    return {
        "total_tasks": total_tasks,
        "active_tasks": active_tasks,
        "total_submissions": total_submissions,
        "pending_grading": pending_grading,
        "recent_submissions": recent_submissions
    }
