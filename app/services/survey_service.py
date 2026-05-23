from sqlalchemy.orm import Session
from app.models.models import SurveyResponse, SurveyAnswer, Student, SurveyType, User
from app.schemas.schemas import SurveySubmitRequest, SurveyDetailedResponse
from fastapi import HTTPException, status
from typing import List, Optional

from app.services import audit_service

def submit_survey(db: Session, survey_data: SurveySubmitRequest, institution_id: int, user_id: int):
    # Validate student belongs to institution
    student = db.query(Student).filter(
        Student.id == survey_data.student_id,
        Student.institution_id == institution_id
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found in your institution"
        )
        
    # Prevent duplicate survey for same month + type
    existing = db.query(SurveyResponse).filter(
        SurveyResponse.student_id == survey_data.student_id,
        SurveyResponse.month == survey_data.month,
        SurveyResponse.year == survey_data.year,
        SurveyResponse.survey_type == survey_data.survey_type
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Survey already submitted for this student in {survey_data.month}/{survey_data.year}"
        )
        
    # Validate 8 answers
    if len(survey_data.answers) != 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Exactly 8 answers are required"
        )
        
    total_score = 0
    for answer in survey_data.answers:
        if not (1 <= answer.score <= 5):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Score for {answer.question_key} must be between 1 and 5"
            )
        total_score += answer.score
        
    percentage = (total_score / 40) * 100
    
    # Assign risk level
    if percentage >= 75:
        risk_level = "STABLE"
    elif percentage >= 60:
        risk_level = "MONITOR"
    else:
        risk_level = "HIGH_RISK"
        
    # Create survey response
    db_response = SurveyResponse(
        student_id=survey_data.student_id,
        institution_id=institution_id,
        month=survey_data.month,
        year=survey_data.year,
        survey_type=survey_data.survey_type,
        total_score=total_score,
        percentage=percentage,
        risk_level=risk_level,
        submitted_by=user_id
    )
    
    db.add(db_response)
    
    # Audit logging
    audit_service.log_action(db, user_id, "CREATE", "Survey")
    
    db.commit()
    db.refresh(db_response)
    
    # Create survey answers
    for answer in survey_data.answers:
        db_answer = SurveyAnswer(
            survey_response_id=db_response.id,
            question_key=answer.question_key,
            score=answer.score
        )
        db.add(db_answer)
        
    db.commit()
    db.refresh(db_response)
    return db_response

def get_student_surveys(db: Session, student_id: int, institution_id: Optional[int] = None, month: Optional[int] = None, year: Optional[int] = None, skip: int = 0, limit: int = 20):
    limit = min(limit, 100)
    # Security: Validate student belongs to institution
    student_query = db.query(Student).filter(Student.id == student_id, Student.is_active == True)
    if institution_id:
        student_query = student_query.filter(Student.institution_id == institution_id)
    student = student_query.first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found or access denied"
        )
        
    query = db.query(SurveyResponse).filter(SurveyResponse.student_id == student_id)
    
    if month:
        query = query.filter(SurveyResponse.month == month)
    if year:
        query = query.filter(SurveyResponse.year == year)
        
    return query.order_by(SurveyResponse.created_at.desc()).offset(skip).limit(limit).all()
