from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from app.models.models import Student, AcademicYear, SchoolClass, SurveyResponse, SurveyAnswer, Attendance
from app.schemas.schemas import StudentCreate, StudentUpdate
from app.services import audit_service
from datetime import datetime
from uuid import UUID

def get_students(db: Session, institution_id: int, academic_year_id: int = None, class_id: int = None, skip: int = 0, limit: int = 20):
    limit = min(limit, 100)
    query = db.query(Student).filter(
        Student.institution_id == institution_id,
        Student.is_active == True
    )
    
    if academic_year_id:
        query = query.filter(Student.academic_year_id == academic_year_id)
    if class_id:
        query = query.filter(Student.class_id == class_id)
        
    # Eager loading to avoid N+1 issues
    return query.options(
        joinedload(Student.school_class),
    ).offset(skip).limit(limit).all()

def get_student(db: Session, student_id: UUID, institution_id: int):
    return db.query(Student).filter(
        Student.id == student_id, 
        Student.institution_id == institution_id,
        Student.is_active == True
    ).first()

def validate_student_relations(db: Session, institution_id: int, academic_year_id: int, class_id: int):
    """
    Requirement: Strictly validate relations between institution, academic year, and class.
    """
    academic_year = db.query(AcademicYear).filter(
        AcademicYear.id == academic_year_id,
        AcademicYear.institution_id == institution_id
    ).first()
    
    if not academic_year:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid academic year for this institution"
        )
        
    if not academic_year.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot enroll students in an inactive academic year"
        )

    school_class = db.query(SchoolClass).filter(
        SchoolClass.id == class_id,
        SchoolClass.institution_id == institution_id,
        SchoolClass.academic_year_id == academic_year_id
    ).first()
    
    if not school_class:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid class. The class must belong to the institution and the selected academic year."
        )
    
    return academic_year, school_class

def create_student(db: Session, student: StudentCreate, institution_id: int, performed_by: int):
    # Requirement: Strict relational validation
    validate_student_relations(db, institution_id, student.academic_year_id, student.class_id)
    
    # Requirement: Unique student_unique_id per institution
    existing_id = db.query(Student).filter(
        Student.institution_id == institution_id,
        Student.student_unique_id == student.student_unique_id
    ).first()
    
    if existing_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Student with unique ID {student.student_unique_id} already exists in this institution"
        )
    
    # Requirement: Prevent duplicate email across system (or institution, but unique=True in model)
    existing_email = db.query(Student).filter(Student.email == student.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A student with this email already exists"
        )

    db_student = Student(
        **student.model_dump(),
        institution_id=institution_id
    )
    
    try:
        db.add(db_student)
        db.commit()
        db.refresh(db_student)
        
        # Audit logging
        audit_service.log_action(db, performed_by, "CREATE", "Student", action_type="CREATE")
        
        return db_student
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating student: {str(e)}"
        )

def update_student(db: Session, student_id: UUID, student: StudentUpdate, institution_id: int):
    db_student = get_student(db, student_id, institution_id)
    if not db_student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    
    student_data = student.model_dump(exclude_unset=True)
    for key, value in student_data.items():
        setattr(db_student, key, value)
    
    try:
        db.commit()
        db.refresh(db_student)
        return db_student
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating student: {str(e)}"
        )

def delete_student(db: Session, student_id: UUID, institution_id: int, performed_by: int):
    """
    Soft delete — marks student inactive, preserves all records for analytics integrity.
    Blocked if survey or attendance data exists (use purge for full removal).
    """
    db_student = get_student(db, student_id, institution_id)
    if not db_student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    survey_exists = db.query(SurveyResponse).filter(SurveyResponse.student_id == student_id).first()
    if survey_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot soft-delete a student with existing survey responses. Use /purge to permanently remove all data."
        )

    attendance_exists = db.query(Attendance).filter(Attendance.student_id == student_id).first()
    if attendance_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot soft-delete a student with existing attendance records. Use /purge to permanently remove all data."
        )

    db_student.is_active = False
    db_student.deleted_at = datetime.utcnow()

    try:
        db.commit()
        audit_service.log_action(db, performed_by, "SOFT_DELETE", "Student", action_type="DELETE")
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error deleting student: {str(e)}")


def export_student_data(db: Session, student_id: UUID, institution_id: int):
    """
    GDPR/DPDP data export — returns all data held about a student.
    Institution-scoped: includes soft-deleted students so they can export before purge.
    """
    query = db.query(Student).filter(Student.id == student_id)
    if institution_id is not None:
        query = query.filter(Student.institution_id == institution_id)
    db_student = query.first()

    if not db_student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    attendance = db.query(Attendance).filter(
        Attendance.student_id == student_id
    ).order_by(Attendance.date.desc()).all()

    surveys = db.query(SurveyResponse).filter(
        SurveyResponse.student_id == student_id
    ).options(joinedload(SurveyResponse.answers)).order_by(SurveyResponse.created_at.desc()).all()

    return {
        "exported_at": datetime.utcnow(),
        "student": db_student,
        "attendance_records": attendance,
        "survey_responses": surveys,
    }


def hard_purge_student(db: Session, student_id: UUID, institution_id: int, performed_by: int):
    """
    GDPR/DPDP hard delete — permanently and irreversibly removes all PII for a student.
    Requires SCHOOL_ADMIN or SUPER_ADMIN. Cannot be undone.
    """
    query = db.query(Student).filter(Student.id == student_id)
    if institution_id is not None:
        query = query.filter(Student.institution_id == institution_id)
    db_student = query.first()

    if not db_student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    # Audit before deletion — record cannot be written after student is gone
    audit_service.log_action(
        db, performed_by,
        f"HARD_PURGE student_id={student_id}",
        "Student",
        action_type="DELETE"
    )
    db.commit()

    # Delete in FK-safe order: answers → responses → attendance → student
    survey_ids = [r.id for r in db.query(SurveyResponse.id).filter(SurveyResponse.student_id == student_id).all()]
    if survey_ids:
        db.query(SurveyAnswer).filter(SurveyAnswer.survey_response_id.in_(survey_ids)).delete(synchronize_session=False)
        db.query(SurveyResponse).filter(SurveyResponse.student_id == student_id).delete(synchronize_session=False)

    db.query(Attendance).filter(Attendance.student_id == student_id).delete(synchronize_session=False)
    db.delete(db_student)

    try:
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Purge failed: {str(e)}")
