from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.models import SchoolClass, AcademicYear, Student
from app.schemas.schemas import SchoolClassCreate
from typing import List

def check_academic_year_anchoring(db: Session, institution_id: int, academic_year_id: int):
    """
    Business rule: Class must belong to same institution as academic year.
    And: Cannot create class in inactive academic year.
    """
    academic_year = db.query(AcademicYear).filter(
        AcademicYear.id == academic_year_id,
        AcademicYear.institution_id == institution_id
    ).first()
    
    if not academic_year:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic year not found for this institution"
        )
    
    if not academic_year.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create class in an inactive academic year"
        )
    
    return academic_year

def create_class(db: Session, school_class: SchoolClassCreate, institution_id: int):
    # Anchor check
    check_academic_year_anchoring(db, institution_id, school_class.academic_year_id)
    
    # Auto-generate class_label (Requirement 5)
    class_label = school_class.class_label or f"Grade {school_class.grade}-{school_class.section}"
    
    class_data = school_class.model_dump()
    class_data["class_label"] = class_label
    
    db_class = SchoolClass(
        **class_data,
        institution_id=institution_id
    )
    
    try:
        db.add(db_class)
        db.commit()
        db.refresh(db_class)
        return db_class
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating class: {str(e)}"
        )

def get_classes(db: Session, institution_id: int, academic_year_id: int = None):
    query = db.query(SchoolClass).filter(SchoolClass.institution_id == institution_id)
    if academic_year_id:
        query = query.filter(SchoolClass.academic_year_id == academic_year_id)
    return query.all()

def deactivate_class(db: Session, institution_id: int, class_id: int):
    """
    Requirement: Soft deactivate instead of delete.
    """
    db_class = db.query(SchoolClass).filter(
        SchoolClass.id == class_id,
        SchoolClass.institution_id == institution_id
    ).first()
    
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    db_class.is_active = False
    db.commit()
    db.refresh(db_class)
    return db_class

def delete_class(db: Session, institution_id: int, class_id: int):
    """
    Business rule: Cannot delete class if students exist.
    """
    db_class = db.query(SchoolClass).filter(
        SchoolClass.id == class_id,
        SchoolClass.institution_id == institution_id
    ).first()
    
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    # Check for students (Requirement 3)
    student_exists = db.query(Student).filter(Student.class_id == class_id).first()
    if student_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete class because it has assigned students. Please reassign students first or deactivate the class."
        )
    
    try:
        db.delete(db_class)
        db.commit()
        return {"detail": "Class deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not delete class: {str(e)}"
        )
