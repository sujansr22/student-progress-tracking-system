from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from app.models.models import ClassInstructorMap, User, SchoolClass, AcademicYear, Subscription, UserRole
from app.schemas.schemas import ClassInstructorMapCreate
from app.services import audit_service
from datetime import datetime
from uuid import UUID

def validate_mapping_requirements(db: Session, institution_id: int, instructor_id: int, class_id: int, academic_year_id: int):
    """
    Strict validation for Instructor-Class mapping.
    """
    # 1. Instructor Check
    instructor = db.query(User).filter(User.id == instructor_id, User.institution_id == institution_id).first()
    if not instructor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instructor not found")
    if instructor.role != UserRole.INSTRUCTOR:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="User must have the INSTRUCTOR role to be mapped to a class"
        )

    # 2. Academic Year Check
    academic_year = db.query(AcademicYear).filter(
        AcademicYear.id == academic_year_id, 
        AcademicYear.institution_id == institution_id
    ).first()
    if not academic_year:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Academic year not found for this institution")

    # 3. Class Check
    school_class = db.query(SchoolClass).filter(
        SchoolClass.id == class_id, 
        SchoolClass.institution_id == institution_id
    ).first()
    if not school_class:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found for this institution")
    
    # 4. Class-Year Alignment Check
    if school_class.academic_year_id != academic_year_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="The class does not belong to the specified academic year"
        )

    # 5. Subscription Check
    subscription = db.query(Subscription).filter(
        Subscription.institution_id == institution_id,
        Subscription.is_active == True,
        Subscription.end_date >= datetime.now().date()
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Institution has no active subscription. Cannot create new mappings."
        )

    return instructor, school_class, academic_year

def create_mapping(db: Session, mapping: ClassInstructorMapCreate, institution_id: int, performed_by: int):
    # Strict validation
    validate_mapping_requirements(
        db, 
        institution_id, 
        mapping.instructor_id, 
        mapping.class_id, 
        mapping.academic_year_id
    )
    
    # Unique check per year (already in unique constraint but checked for better UX)
    existing = db.query(ClassInstructorMap).filter(
        ClassInstructorMap.instructor_id == mapping.instructor_id,
        ClassInstructorMap.class_id == mapping.class_id,
        ClassInstructorMap.academic_year_id == mapping.academic_year_id
    ).first()
    
    if existing:
        if existing.is_active:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mapping already exists and is active")
        else:
             # Re-activate if needed or update? Business rules say yearly history.
             # If it exists but is inactive, we could reactivate it.
             existing.is_active = True
             db.commit()
             db.refresh(existing)
             return existing

    db_mapping = ClassInstructorMap(
        **mapping.model_dump(),
        institution_id=institution_id
    )
    
    try:
        db.add(db_mapping)
        db.commit()
        db.refresh(db_mapping)
        
        # Audit logging
        audit_service.log_action(db, performed_by, "CREATE", "ClassInstructorMap", action_type="CREATE")
        
        return db_mapping
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error creating instructor mapping: {str(e)}"
        )

def deactivate_mapping(db: Session, mapping_id: UUID, institution_id: int, performed_by: int):
    """
    Soft deactivation of mapping.
    """
    db_mapping = db.query(ClassInstructorMap).filter(
        ClassInstructorMap.id == mapping_id,
        ClassInstructorMap.institution_id == institution_id
    ).first()
    
    if not db_mapping:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mapping not found")
    
    db_mapping.is_active = False
    
    try:
        db.commit()
        # Audit logging
        audit_service.log_action(db, performed_by, "DEACTIVATE", "ClassInstructorMap", action_type="UPDATE")
        return {"detail": "Mapping deactivated successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error deactivating mapping: {str(e)}"
        )

def get_mappings_for_instructor(db: Session, instructor_id: int, institution_id: int, academic_year_id: int = None):
    query = db.query(ClassInstructorMap).filter(
        ClassInstructorMap.instructor_id == instructor_id,
        ClassInstructorMap.institution_id == institution_id
    )
    if academic_year_id:
        query = query.filter(ClassInstructorMap.academic_year_id == academic_year_id)
        
    return query.options(
        joinedload(ClassInstructorMap.school_class),
        joinedload(ClassInstructorMap.academic_year)
    ).all()

def get_mappings_for_class(db: Session, class_id: int, institution_id: int):
    return db.query(ClassInstructorMap).filter(
        ClassInstructorMap.class_id == class_id,
        ClassInstructorMap.institution_id == institution_id
    ).options(joinedload(ClassInstructorMap.instructor)).all()
