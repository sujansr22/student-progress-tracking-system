"""
Instructor assigns self-assessment surveys to students.
Students see pending assignments via /me/surveys/pending.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.auth import require_roles
from app.core.dependencies import require_active_subscription
from app.models.models import User, UserRole, Student, AssignedSurvey, AssignedSurveyStatus
from app.schemas.schemas import AssignedSurveyCreate, AssignedSurveyResponse

router = APIRouter(prefix="/assigned-surveys", tags=["assigned-surveys"])


@router.post("/", response_model=AssignedSurveyResponse, status_code=status.HTTP_201_CREATED)
def assign_survey(
    body: AssignedSurveyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.INSTRUCTOR])),
    _sub: User = Depends(require_active_subscription),
):
    student = db.query(Student).filter(
        Student.id == body.student_id,
        Student.institution_id == current_user.institution_id,
        Student.is_active == True,
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found in your institution")

    existing = db.query(AssignedSurvey).filter(
        AssignedSurvey.student_id == body.student_id,
        AssignedSurvey.month == body.month,
        AssignedSurvey.year == body.year,
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Survey already assigned for this student in {body.month}/{body.year}",
        )

    assignment = AssignedSurvey(
        student_id=body.student_id,
        assigned_by=current_user.id,
        institution_id=current_user.institution_id,
        month=body.month,
        year=body.year,
        due_date=body.due_date,
        status=AssignedSurveyStatus.PENDING,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.get("/", response_model=List[AssignedSurveyResponse])
def list_assigned_surveys(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.INSTRUCTOR, UserRole.SCHOOL_ADMIN])),
):
    query = db.query(AssignedSurvey).filter(
        AssignedSurvey.institution_id == current_user.institution_id,
    )
    if current_user.role == UserRole.INSTRUCTOR:
        query = query.filter(AssignedSurvey.assigned_by == current_user.id)
    return query.order_by(AssignedSurvey.created_at.desc()).offset(skip).limit(limit).all()


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_assignment(
    assignment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.INSTRUCTOR])),
):
    assignment = db.query(AssignedSurvey).filter(
        AssignedSurvey.id == assignment_id,
        AssignedSurvey.assigned_by == current_user.id,
        AssignedSurvey.status == AssignedSurveyStatus.PENDING,
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found or already completed")
    db.delete(assignment)
    db.commit()
    return None
