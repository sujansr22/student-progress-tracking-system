from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.auth import require_roles
from app.core.dependencies import require_active_subscription
from app.schemas.schemas import SurveySubmitRequest, SurveyDetailedResponse
from app.services import survey_service, audit_service
from app.models.models import User, UserRole
from app.core.limiter import limiter

router = APIRouter(prefix="/survey", tags=["survey"])

@router.post("/submit", response_model=SurveyDetailedResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
def submit_survey(
    request: Request,
    survey: SurveySubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.INSTRUCTOR])),
    _sub: User = Depends(require_active_subscription),
):
    return survey_service.submit_survey(
        db,
        survey_data=survey,
        institution_id=current_user.institution_id,
        user_id=current_user.id
    )

@router.get("/student/{student_id}", response_model=List[SurveyDetailedResponse])
def get_student_surveys(
    student_id: UUID,
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2000),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.INSTRUCTOR, UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN]))
):
    # Audit logging (Read)
    audit_service.log_action(
        db, 
        user_id=current_user.id, 
        action="READ", 
        entity="Survey", 
        action_type="READ", 
        ip_address=request.client.host
    )
    db.commit()

    target_institution_id = None
    if current_user.role != UserRole.SUPER_ADMIN:
        target_institution_id = current_user.institution_id
        
    return survey_service.get_student_surveys(
        db, 
        student_id=student_id, 
        institution_id=target_institution_id,
        month=month,
        year=year,
        skip=skip,
        limit=limit
    )
