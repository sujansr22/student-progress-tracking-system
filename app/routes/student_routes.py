from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.auth import get_current_user, require_roles
from app.core.dependencies import require_active_subscription
from app.schemas.schemas import StudentCreate, StudentUpdate, StudentResponse, StudentExportResponse
from app.services import student_service, audit_service
from app.models.models import User, UserRole
from app.core.limiter import limiter

router = APIRouter(prefix="/students", tags=["students"])

@router.post("/", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
def create_student(
    request: Request,
    student: StudentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.INSTRUCTOR])),
    _sub: User = Depends(require_active_subscription),
):
    return student_service.create_student(db, student, current_user.institution_id, current_user.id)

@router.get("/", response_model=List[StudentResponse])
def read_students(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    academic_year_id: int = Query(None),
    class_id: int = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.INSTRUCTOR]))
):
    return student_service.get_students(
        db, current_user.institution_id,
        academic_year_id=academic_year_id, class_id=class_id,
        skip=skip, limit=limit,
    )

@router.get("/{student_id}", response_model=StudentResponse)
def read_student(
    student_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.INSTRUCTOR]))
):
    audit_service.log_action(
        db,
        user_id=current_user.id,
        action="READ",
        entity="Student",
        action_type="READ",
        ip_address=request.client.host
    )
    db.commit()

    db_student = student_service.get_student(db, student_id, current_user.institution_id)
    if db_student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return db_student

@router.put("/{student_id}", response_model=StudentResponse)
def update_student(
    student_id: UUID,
    student: StudentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.INSTRUCTOR]))
):
    db_student = student_service.update_student(db, student_id, student, current_user.institution_id)
    if db_student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return db_student

@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(
    student_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.INSTRUCTOR]))
):
    student_service.delete_student(db, student_id, current_user.institution_id, performed_by=current_user.id)
    return None


@router.get("/{student_id}/export", response_model=StudentExportResponse)
def export_student(
    student_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN]))
):
    audit_service.log_action(
        db,
        user_id=current_user.id,
        action="EXPORT",
        entity="Student",
        action_type="READ",
        ip_address=request.client.host
    )
    db.commit()

    institution_id = None if current_user.role == UserRole.SUPER_ADMIN else current_user.institution_id
    return student_service.export_student_data(db, student_id, institution_id)


@router.delete("/{student_id}/purge", status_code=status.HTTP_204_NO_CONTENT)
def purge_student(
    student_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN]))
):
    """
    Permanently delete all PII for a student. GDPR/DPDP right-to-erasure.
    This cannot be undone. Export data first if needed.
    """
    audit_service.log_action(
        db,
        user_id=current_user.id,
        action="PURGE_INITIATED",
        entity="Student",
        action_type="DELETE",
        ip_address=request.client.host
    )
    db.commit()

    institution_id = None if current_user.role == UserRole.SUPER_ADMIN else current_user.institution_id
    student_service.hard_purge_student(db, student_id, institution_id, performed_by=current_user.id)
    return None
