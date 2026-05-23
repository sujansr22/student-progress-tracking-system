from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime
from sqlalchemy import func
from app.models.models import AcademicYear, Student
from app.schemas.schemas import AcademicYearCreate, AcademicYearUpdate
from datetime import date

def validate_academic_year_dates(start_date: date, end_date: date):
    """Business rule: start_date must be before end_date."""
    if start_date >= end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before end_date"
        )

def create_academic_year(db: Session, academic_year: AcademicYearCreate, institution_id: int):
    validate_academic_year_dates(academic_year.start_date, academic_year.end_date)
    
    db_academic_year = AcademicYear(
        **academic_year.model_dump(),
        institution_id=institution_id
    )
    
    try:
        db.add(db_academic_year)
        db.commit()
        db.refresh(db_academic_year)
        return db_academic_year
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating academic year: {str(e)}"
        )

def activate_academic_year(db: Session, institution_id: int, academic_year_id: int):
    """
    Enterprise activation logic:
    1. Verify the academic year belongs to the institution.
    2. Deactivate all other years for that institution in a transaction.
    3. Activate the target year.
    """
    target_year = db.query(AcademicYear).filter(
        AcademicYear.id == academic_year_id,
        AcademicYear.institution_id == institution_id
    ).first()
    
    if not target_year:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic year not found for this institution"
        )
    
    try:
        # Deactivate all other years for this institution
        db.query(AcademicYear).filter(
            AcademicYear.institution_id == institution_id,
            AcademicYear.id != academic_year_id
        ).update({"is_active": False})
        
        # Activate target year
        target_year.is_active = True
        
        db.commit()
        db.refresh(target_year)
        return target_year
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate academic year: {str(e)}"
        )

def delete_academic_year(db: Session, institution_id: int, academic_year_id: int):
    """
    STRICT SERVICE POLICY: Physical deletion of AcademicYear is blocked to preserve history.
    This function performs a SOFT-DELETE (closure) by setting is_active=False.
    """
    db_academic_year = db.query(AcademicYear).filter(
        AcademicYear.id == academic_year_id,
        AcademicYear.institution_id == institution_id
    ).first()
    
    if not db_academic_year:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic year not found"
        )
    
    # Business Rule: Check for dependencies before soft-deletion if required, 
    # but the primary goal is to prevent hard-deletion.
    # The database RESTRICT constraint will prevent physical deletion if classes exist.
    
    try:
        # Physical delete is explicitly forbidden
        # db.delete(db_academic_year)  <-- THIS IS BLOCKED
        
        db_academic_year.is_active = False
        db_academic_year.deleted_at = func.now()
        db.commit()
        db.refresh(db_academic_year)
        return {"detail": "Academic year has been soft-closed/deactivated"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not deactivate academic year: {str(e)}"
        )

def get_academic_years(db: Session, institution_id: int):
    return db.query(AcademicYear).filter(AcademicYear.institution_id == institution_id).all()
