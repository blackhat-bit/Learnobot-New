from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func

from app.core.database import get_db
from app.core.dependencies import get_current_student
from app.models.user import User
from app.models.task import Task, TaskSubmission
from app.schemas.task import (
    TaskBase,
    TaskSummary,
    TaskSubmissionCreate,
    TaskSubmissionUpdate,
    TaskSubmissionBase,
    TaskSubmissionDetail,
    StudentTaskProgress
)

router = APIRouter()


@router.get("/tasks", response_model=List[TaskSummary])
async def get_available_tasks(
    current_student: User = Depends(get_current_student),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    subject: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    """Get available tasks for the student."""
    
    query = db.query(Task).filter(Task.status == "published")
    
    if subject:
        query = query.filter(Task.subject == subject)
    
    tasks = query.order_by(desc(Task.created_at)).offset(skip).limit(limit).all()
    
    # Add submission count and student's submission status
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


@router.get("/tasks/{task_id}", response_model=TaskBase)
async def get_task(
    task_id: int,
    current_student: User = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Get a specific task."""
    
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.status == "published"
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or not available"
        )
    
    return task


@router.post("/tasks/{task_id}/submissions", response_model=TaskSubmissionBase, status_code=status.HTTP_201_CREATED)
async def create_submission(
    task_id: int,
    submission_data: TaskSubmissionCreate,
    current_student: User = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Create or update a task submission."""
    
    # Verify task exists and is available
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.status == "published"
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or not available"
        )
    
    # Check if submission already exists
    existing_submission = db.query(TaskSubmission).filter(
        TaskSubmission.task_id == task_id,
        TaskSubmission.student_id == current_student.id
    ).first()
    
    if existing_submission:
        # Update existing submission
        existing_submission.content = submission_data.content
        existing_submission.file_urls = submission_data.file_urls
        existing_submission.status = "in_progress"
        existing_submission.attempt_number += 1
        
        db.commit()
        db.refresh(existing_submission)
        return existing_submission
    else:
        # Create new submission
        db_submission = TaskSubmission(
            task_id=task_id,
            student_id=current_student.id,
            content=submission_data.content,
            file_urls=submission_data.file_urls,
            status="in_progress",
            max_score=task.max_points,
            started_at=func.now()
        )
        
        db.add(db_submission)
        db.commit()
        db.refresh(db_submission)
        
        return db_submission


@router.get("/tasks/{task_id}/submissions/my", response_model=TaskSubmissionDetail)
async def get_my_submission(
    task_id: int,
    current_student: User = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Get student's own submission for a task."""
    
    submission = db.query(TaskSubmission).filter(
        TaskSubmission.task_id == task_id,
        TaskSubmission.student_id == current_student.id
    ).first()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No submission found for this task"
        )
    
    return submission


@router.put("/tasks/{task_id}/submissions/my", response_model=TaskSubmissionDetail)
async def update_my_submission(
    task_id: int,
    submission_data: TaskSubmissionUpdate,
    current_student: User = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Update student's own submission."""
    
    submission = db.query(TaskSubmission).filter(
        TaskSubmission.task_id == task_id,
        TaskSubmission.student_id == current_student.id
    ).first()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No submission found for this task"
        )
    
    # Don't allow updates to graded submissions
    if submission.status == "graded":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update graded submission"
        )
    
    # Update fields if provided
    for field, value in submission_data.dict(exclude_unset=True).items():
        setattr(submission, field, value)
    
    db.commit()
    db.refresh(submission)
    
    return submission


@router.post("/tasks/{task_id}/submissions/my/submit")
async def submit_task(
    task_id: int,
    current_student: User = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Submit a task for grading."""
    
    submission = db.query(TaskSubmission).filter(
        TaskSubmission.task_id == task_id,
        TaskSubmission.student_id == current_student.id
    ).first()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No submission found for this task"
        )
    
    if submission.status == "submitted":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task already submitted"
        )
    
    if submission.status == "graded":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task already graded"
        )
    
    # Submit the task
    submission.status = "submitted"
    submission.submitted_at = func.now()
    
    db.commit()
    
    return {"message": "Task submitted successfully"}


@router.get("/submissions", response_model=List[TaskSubmissionBase])
async def get_my_submissions(
    current_student: User = Depends(get_current_student),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None)
):
    """Get student's submissions."""
    
    query = db.query(TaskSubmission).filter(TaskSubmission.student_id == current_student.id)
    
    if status:
        query = query.filter(TaskSubmission.status == status)
    
    submissions = query.order_by(desc(TaskSubmission.created_at)).offset(skip).limit(limit).all()
    
    return submissions


@router.get("/submissions/{submission_id}", response_model=TaskSubmissionDetail)
async def get_submission(
    submission_id: int,
    current_student: User = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Get a specific submission."""
    
    submission = db.query(TaskSubmission).filter(
        TaskSubmission.id == submission_id,
        TaskSubmission.student_id == current_student.id
    ).first()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    return submission


@router.get("/progress", response_model=List[StudentTaskProgress])
async def get_progress(
    current_student: User = Depends(get_current_student),
    db: Session = Depends(get_db),
    subject: Optional[str] = Query(None)
):
    """Get student's learning progress."""
    
    # Get all published tasks
    query = db.query(Task).filter(Task.status == "published")
    
    if subject:
        query = query.filter(Task.subject == subject)
    
    tasks = query.all()
    
    progress_list = []
    for task in tasks:
        # Get student's submission for this task
        submission = db.query(TaskSubmission).filter(
            TaskSubmission.task_id == task.id,
            TaskSubmission.student_id == current_student.id
        ).first()
        
        if submission:
            # Calculate progress percentage based on status
            progress_percentage = {
                "not_started": 0.0,
                "in_progress": 50.0,
                "submitted": 90.0,
                "graded": 100.0,
                "returned": 100.0
            }.get(submission.status.value, 0.0)
            
            progress_list.append(StudentTaskProgress(
                task_id=task.id,
                task_title=task.title,
                status=submission.status,
                score=submission.score,
                due_date=task.due_date,
                time_spent=submission.time_spent,
                progress_percentage=progress_percentage
            ))
        else:
            # No submission yet
            progress_list.append(StudentTaskProgress(
                task_id=task.id,
                task_title=task.title,
                status="not_started",
                score=None,
                due_date=task.due_date,
                time_spent=None,
                progress_percentage=0.0
            ))
    
    return progress_list


@router.get("/dashboard")
async def get_student_dashboard(
    current_student: User = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Get student dashboard statistics."""
    
    # Get submission statistics
    total_submissions = db.query(TaskSubmission).filter(
        TaskSubmission.student_id == current_student.id
    ).count()
    
    completed_submissions = db.query(TaskSubmission).filter(
        TaskSubmission.student_id == current_student.id,
        TaskSubmission.status.in_(["submitted", "graded"])
    ).count()
    
    graded_submissions = db.query(TaskSubmission).filter(
        TaskSubmission.student_id == current_student.id,
        TaskSubmission.status == "graded",
        TaskSubmission.score.isnot(None)
    ).all()
    
    # Calculate average score
    average_score = None
    if graded_submissions:
        total_score = sum(s.score for s in graded_submissions)
        total_max_score = sum(s.max_score for s in graded_submissions)
        average_score = (total_score / total_max_score * 100) if total_max_score > 0 else 0
    
    # Get pending tasks (available but not started)
    available_tasks = db.query(Task).filter(Task.status == "published").count()
    started_tasks = db.query(TaskSubmission).filter(
        TaskSubmission.student_id == current_student.id
    ).count()
    pending_tasks = available_tasks - started_tasks
    
    # Recent activity (last 7 days)
    from datetime import datetime, timedelta
    recent_date = datetime.utcnow() - timedelta(days=7)
    
    recent_submissions = db.query(TaskSubmission).filter(
        TaskSubmission.student_id == current_student.id,
        TaskSubmission.created_at >= recent_date
    ).count()
    
    return {
        "total_submissions": total_submissions,
        "completed_submissions": completed_submissions,
        "average_score": average_score,
        "pending_tasks": pending_tasks,
        "recent_activity": recent_submissions
    }
