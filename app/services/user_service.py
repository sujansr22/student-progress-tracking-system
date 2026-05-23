from sqlalchemy.orm import Session
from app.models.models import User
from app.schemas.schemas import UserCreate
from app.core.auth import get_password_hash

from app.services import audit_service

def create_user(db: Session, user: UserCreate, performed_by: int):
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        role=user.role,
        institution_id=user.institution_id
    )
    db.add(db_user)
    
    # Audit logging
    audit_service.log_action(db, performed_by, "CREATE", "User")
    
    db.commit()
    db.refresh(db_user)
    return db_user

from datetime import datetime

# ... create_user ...

def get_users(db: Session, institution_id: int = None, skip: int = 0, limit: int = 20):
    limit = min(limit, 100)
    query = db.query(User).filter(User.is_active == True)
    if institution_id:
        query = query.filter(User.institution_id == institution_id)
    return query.offset(skip).limit(limit).all()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email, User.is_active == True).first()

def delete_user(db: Session, user_id: int):
    db_user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not db_user:
        return None
    
    db_user.is_active = False
    db_user.deleted_at = datetime.utcnow()
    db.commit()
    return db_user
