from uuid import UUID
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import require_roles
from app.schemas.schemas import StudentProgressResponse
from app.services import analytics_service, audit_service
from app.models.models import User, UserRole

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/student/{student_id}/progress", response_model=StudentProgressResponse)
def get_student_progress_analytics(
    student_id: UUID,
    request: Request,
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2000),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.INSTRUCTOR, UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN]))
):
    # Audit logging (Read)
    audit_service.log_action(
        db, 
        user_id=current_user.id, 
        action="READ", 
        entity="Analytics", 
        action_type="READ", 
        ip_address=request.client.host
    )
    db.commit()

    target_institution_id = None
    if current_user.role != UserRole.SUPER_ADMIN:
        target_institution_id = current_user.institution_id
        
    return analytics_service.get_student_progress(
        db, 
        student_id=student_id, 
        month=month, 
        year=year, 
        institution_id=target_institution_id
    )
