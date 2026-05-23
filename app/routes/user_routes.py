from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.auth import require_roles
from app.core.dependencies import require_active_subscription
from app.schemas.schemas import UserCreate, UserResponse
from app.services import user_service
from app.models.models import User, UserRole

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN])),
    _sub: User = Depends(require_active_subscription),
):
    # SCHOOL_ADMIN can only create instructors for their own institution
    if current_user.role == UserRole.SCHOOL_ADMIN:
        if user.role != UserRole.INSTRUCTOR:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="School admins can only create instructors"
            )
        if user.institution_id != current_user.institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only create users for your own institution"
            )
    
    # Check if user already exists
    db_user = user_service.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    return user_service.create_user(db, user, current_user.id)

@router.get("/", response_model=List[UserResponse])
def read_users(
    skip: int = Query(0, ge=0), 
    limit: int = Query(20, ge=1, le=100), 
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_roles([UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN]))
):
    institution_id = None
    if current_user.role == UserRole.SCHOOL_ADMIN:
        institution_id = current_user.institution_id
    
    return user_service.get_users(db, institution_id=institution_id, skip=skip, limit=limit)
