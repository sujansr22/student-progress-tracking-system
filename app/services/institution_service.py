from sqlalchemy.orm import Session
from app.models.models import Institution
from app.schemas.schemas import InstitutionCreate

from app.services import audit_service

def create_institution(db: Session, institution: InstitutionCreate, performed_by: int):
    db_institution = Institution(name=institution.name)
    db.add(db_institution)
    
    # Audit logging
    audit_service.log_action(db, performed_by, "CREATE", "Institution")
    
    db.commit()
    db.refresh(db_institution)
    return db_institution

from datetime import datetime

# ... create_institution ...

def get_institutions(db: Session, skip: int = 0, limit: int = 20):
    limit = min(limit, 100)
    return db.query(Institution).filter(Institution.is_active == True).offset(skip).limit(limit).all()

def get_institution(db: Session, institution_id: int):
    return db.query(Institution).filter(Institution.id == institution_id, Institution.is_active == True).first()

def delete_institution(db: Session, institution_id: int):
    db_inst = get_institution(db, institution_id)
    if not db_inst:
        return None
    
    db_inst.is_active = False
    db_inst.deleted_at = datetime.utcnow()
    db.commit()
    return db_inst
