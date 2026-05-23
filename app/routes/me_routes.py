"""
Student self-service endpoints — all require role=STUDENT.
Each endpoint automatically scopes to the logged-in student's own data.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.core.database import get_db
from app.core.auth import get_current_user, require_roles
from app.models.models import User, UserRole, Student, Attendance, AssignedSurvey, AssignedSurveyStatus, SurveyResponse, SurveyAnswer
from app.schemas.schemas import (
    StudentResponse, AttendanceResponse, AttendancePercentageResponse,
    SurveyDetailedResponse, StudentProgressResponse, AssignedSurveyResponse,
    SurveySubmitRequest,
)
from app.services import attendance_service, analytics_service, survey_service

router = APIRouter(prefix="/me", tags=["student-portal"])


def _get_student(db: Session, user: User) -> Student:
    student = db.query(Student).filter(
        Student.user_id == user.id,
        Student.is_active == True,
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found for this account")
    return student


@router.get("/profile", response_model=StudentResponse)
def my_profile(
    current_user: User = Depends(require_roles([UserRole.STUDENT])),
    db: Session = Depends(get_db),
):
    return _get_student(db, current_user)


@router.get("/attendance", response_model=List[AttendanceResponse])
def my_attendance(
    skip: int = Query(0, ge=0),
    limit: int = Query(30, ge=1, le=100),
    current_user: User = Depends(require_roles([UserRole.STUDENT])),
    db: Session = Depends(get_db),
):
    student = _get_student(db, current_user)
    return attendance_service.get_student_attendance(
        db, student_id=student.id, institution_id=student.institution_id,
        skip=skip, limit=limit,
    )


@router.get("/attendance/summary", response_model=AttendancePercentageResponse)
def my_attendance_summary(
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2000),
    current_user: User = Depends(require_roles([UserRole.STUDENT])),
    db: Session = Depends(get_db),
):
    student = _get_student(db, current_user)
    return attendance_service.get_student_attendance_risk(
        db, student_id=student.id, institution_id=student.institution_id,
        month=month, year=year,
    )


@router.get("/performance", response_model=StudentProgressResponse)
def my_performance(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2000),
    current_user: User = Depends(require_roles([UserRole.STUDENT])),
    db: Session = Depends(get_db),
):
    student = _get_student(db, current_user)
    return analytics_service.get_student_progress(
        db, student_id=student.id, month=month, year=year,
        institution_id=student.institution_id,
    )


@router.get("/surveys", response_model=List[SurveyDetailedResponse])
def my_surveys(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_roles([UserRole.STUDENT])),
    db: Session = Depends(get_db),
):
    student = _get_student(db, current_user)
    return survey_service.get_student_surveys(
        db, student_id=student.id, institution_id=student.institution_id,
        skip=skip, limit=limit,
    )


@router.get("/surveys/pending", response_model=List[AssignedSurveyResponse])
def my_pending_surveys(
    current_user: User = Depends(require_roles([UserRole.STUDENT])),
    db: Session = Depends(get_db),
):
    student = _get_student(db, current_user)
    return db.query(AssignedSurvey).filter(
        AssignedSurvey.student_id == student.id,
        AssignedSurvey.status == AssignedSurveyStatus.PENDING,
    ).order_by(AssignedSurvey.created_at.desc()).all()


@router.post("/surveys/submit", response_model=SurveyDetailedResponse, status_code=201)
def submit_my_survey(
    survey: SurveySubmitRequest,
    current_user: User = Depends(require_roles([UserRole.STUDENT])),
    db: Session = Depends(get_db),
):
    """
    Student submits their own self-assessment. Requires a pending AssignedSurvey
    for the same month/year, and survey_type must be STUDENT.
    """
    from app.models.models import SurveyType
    student = _get_student(db, current_user)

    if str(survey.student_id) != str(student.id):
        raise HTTPException(status_code=403, detail="You can only submit surveys for yourself")

    if survey.survey_type != SurveyType.STUDENT:
        raise HTTPException(status_code=400, detail="Students can only submit STUDENT type surveys")

    assignment = db.query(AssignedSurvey).filter(
        AssignedSurvey.student_id == student.id,
        AssignedSurvey.month == survey.month,
        AssignedSurvey.year == survey.year,
        AssignedSurvey.status == AssignedSurveyStatus.PENDING,
    ).first()
    if not assignment:
        raise HTTPException(
            status_code=400,
            detail="No pending survey assignment found for this period. Ask your instructor to assign one.",
        )

    result = survey_service.submit_survey(
        db, survey_data=survey,
        institution_id=student.institution_id,
        user_id=current_user.id,
    )

    assignment.status = AssignedSurveyStatus.COMPLETED
    db.commit()
    return result
