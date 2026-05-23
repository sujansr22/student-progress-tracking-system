from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.auth import require_roles
from app.core.dependencies import require_active_subscription
from app.schemas.schemas import AttendanceCreate, AttendanceResponse, AttendanceSummaryResponse, AttendancePercentageResponse
from app.services import attendance_service, audit_service
from app.models.models import User, UserRole
from app.core.limiter import limiter

router = APIRouter(prefix="/attendance", tags=["attendance"])

@router.post("/mark", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("60/minute")
def mark_attendance(
    request: Request,
    attendance: AttendanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.INSTRUCTOR])),
    _sub: User = Depends(require_active_subscription),
):
    return attendance_service.mark_attendance(
        db,
        attendance_data=attendance,
        institution_id=current_user.institution_id,
        user_id=current_user.id
    )

@router.get("/student/{student_id}", response_model=List[AttendanceResponse])
def get_student_attendance(
    student_id: UUID,
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.INSTRUCTOR, UserRole.SCHOOL_ADMIN]))
):
    # Audit logging (Read)
    audit_service.log_action(
        db, 
        user_id=current_user.id, 
        action="READ", 
        entity="Attendance", 
        action_type="READ", 
        ip_address=request.client.host
    )
    db.commit()

    # Multi-tenant isolation is handled in the service
    return attendance_service.get_student_attendance(
        db, 
        student_id=student_id, 
        institution_id=current_user.institution_id, 
        skip=skip, 
        limit=limit
    )

@router.get("/institution/summary", response_model=List[AttendanceSummaryResponse])
def get_institution_summary(
    institution_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN]))
):
    target_institution_id = None
    
    if current_user.role == UserRole.SCHOOL_ADMIN:
        # SCHOOL_ADMIN is locked to their own institution
        target_institution_id = current_user.institution_id
    elif current_user.role == UserRole.SUPER_ADMIN:
        # SUPER_ADMIN can optionally filter
        target_institution_id = institution_id
        
    return attendance_service.get_institution_attendance_summary(db, institution_id=target_institution_id, skip=skip, limit=limit)

@router.get("/student/{student_id}/percentage", response_model=AttendancePercentageResponse)
def get_student_percentage(
    student_id: UUID,
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2000),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.INSTRUCTOR, UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN]))
):
    target_institution_id = None
    if current_user.role != UserRole.SUPER_ADMIN:
        target_institution_id = current_user.institution_id
        
    return attendance_service.get_student_attendance_risk(
        db, 
        student_id=student_id, 
        institution_id=target_institution_id,
        month=month,
        year=year
    )

@router.get("/institution/high-risk", response_model=List[AttendancePercentageResponse])
def get_high_risk_students(
    institution_id: Optional[int] = Query(None),
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2000),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN]))
):
    target_institution_id = None
    if current_user.role == UserRole.SCHOOL_ADMIN:
        target_institution_id = current_user.institution_id
    elif current_user.role == UserRole.SUPER_ADMIN:
        target_institution_id = institution_id
        
    return attendance_service.get_high_risk_students(
        db, 
        institution_id=target_institution_id,
        month=month,
        year=year,
        skip=skip,
        limit=limit
    )
