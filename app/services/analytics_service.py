from sqlalchemy.orm import Session
from app.services import attendance_service, survey_service
from app.models.models import ProgressLevel, Student, SurveyType
from app.schemas.schemas import StudentProgressResponse
from fastapi import HTTPException, status
from typing import Optional

def _calculate_progress_level(score: float) -> ProgressLevel:
    if score >= 80:
        return ProgressLevel.THRIVING
    elif score >= 65:
        return ProgressLevel.STABLE
    elif score >= 50:
        return ProgressLevel.NEEDS_ATTENTION
    else:
        return ProgressLevel.CRITICAL

def get_student_progress(db: Session, student_id: int, month: int, year: int, institution_id: Optional[int] = None):
    # Verify student exists and handle multi-tenancy
    student_query = db.query(Student).filter(Student.id == student_id, Student.is_active == True)
    if institution_id:
        student_query = student_query.filter(Student.institution_id == institution_id)
    student = student_query.first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found or access denied"
        )

    # 1. Fetch Attendance Percentage
    attendance_percentage = None
    try:
        att_data = attendance_service.get_student_attendance_risk(db, student_id, institution_id, month, year)
        # Check if any attendance records exist for that month (total_days > 0)
        if att_data.total_days > 0:
            attendance_percentage = att_data.attendance_percentage
    except HTTPException:
        pass

    # 2. Fetch Instructor Survey Percentage
    instructor_surveys = survey_service.get_student_surveys(db, student_id, institution_id, month, year)
    instructor_survey_percentage = None
    for s in instructor_surveys:
        if s.survey_type == SurveyType.INSTRUCTOR:
            instructor_survey_percentage = float(s.percentage)
            break
            
    # 3. Fetch Student Survey Percentage
    student_survey_percentage = None
    for s in instructor_surveys: # Shared query in survey_service
        if s.survey_type == SurveyType.STUDENT:
            student_survey_percentage = float(s.percentage)
            break

    # 4. Integrity Check & Calculate Weighted Score
    # If any essential component is missing, return INSUFFICIENT_DATA
    if attendance_percentage is None or instructor_survey_percentage is None or student_survey_percentage is None:
        return StudentProgressResponse(
            student_id=student.id,
            student_name=f"{student.first_name} {student.last_name}",
            month=month,
            year=year,
            attendance_percentage=round(attendance_percentage or 0.0, 2),
            instructor_survey_percentage=round(instructor_survey_percentage or 0.0, 2),
            student_survey_percentage=round(student_survey_percentage or 0.0, 2),
            final_progress_score=None,
            progress_level=ProgressLevel.INSUFFICIENT_DATA
        )

    # Formula: (Att * 0.3) + (InstSurv * 0.4) + (StudSurv * 0.3)
    final_score = (
        (attendance_percentage * 0.30) +
        (instructor_survey_percentage * 0.40) +
        (student_survey_percentage * 0.30)
    )
    
    return StudentProgressResponse(
        student_id=student.id,
        student_name=f"{student.first_name} {student.last_name}",
        month=month,
        year=year,
        attendance_percentage=round(attendance_percentage, 2),
        instructor_survey_percentage=round(instructor_survey_percentage, 2),
        student_survey_percentage=round(student_survey_percentage, 2),
        final_progress_score=round(final_score, 2),
        progress_level=_calculate_progress_level(final_score)
    )
