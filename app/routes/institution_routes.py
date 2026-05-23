from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.auth import require_roles
from app.schemas.schemas import InstitutionCreate, InstitutionResponse
from app.services import institution_service
from app.models.models import User, UserRole

router = APIRouter(prefix="/institutions", tags=["institutions"])

@router.post("/", response_model=InstitutionResponse, status_code=status.HTTP_201_CREATED)
def create_institution(
    institution: InstitutionCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_roles([UserRole.SUPER_ADMIN]))
):
    return institution_service.create_institution(db, institution, current_user.id)

@router.get("/", response_model=List[InstitutionResponse])
def read_institutions(
    skip: int = Query(0, ge=0), 
    limit: int = Query(20, ge=1, le=100), 
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_roles([UserRole.SUPER_ADMIN]))
):
    return institution_service.get_institutions(db, skip, limit)
