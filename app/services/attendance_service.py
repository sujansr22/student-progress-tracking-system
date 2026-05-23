from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from app.models.models import Attendance, Student, User, AttendanceStatus, RiskLevel
from app.schemas.schemas import AttendanceCreate, AttendanceSummaryResponse, AttendancePercentageResponse
from fastapi import HTTPException, status
from typing import List, Optional

def _calculate_risk_level(attendance_percentage: float, total_days: int) -> RiskLevel:
    if total_days == 0:
        return RiskLevel.HIGH_RISK
    if attendance_percentage >= 75:
        return RiskLevel.SAFE
    if attendance_percentage >= 60:
        return RiskLevel.LOW_ATTENDANCE
    return RiskLevel.HIGH_RISK

def _get_attendance_stats_query(db: Session, institution_id: Optional[int] = None, month: Optional[int] = None, year: Optional[int] = None):
    query = db.query(
        Student.id.label("student_id"),
        (Student.first_name + " " + Student.last_name).label("student_name"),
        func.count(Attendance.id).label("total_days"),
        func.count(Attendance.id).filter(Attendance.status == AttendanceStatus.PRESENT).label("present_days")
    ).join(Attendance, Student.id == Attendance.student_id, isouter=True)

    if institution_id:
        query = query.filter(Student.institution_id == institution_id)
    
    if month:
        query = query.filter(extract('month', Attendance.date) == month)
    if year:
        query = query.filter(extract('year', Attendance.date) == year)
        
    return query.group_by(Student.id)

from app.services import audit_service

def mark_attendance(db: Session, attendance_data: AttendanceCreate, institution_id: int, user_id: int):
    # ... existing code ...
    db_attendance = Attendance(
        student_id=attendance_data.student_id,
        institution_id=institution_id,
        date=attendance_data.date,
        status=attendance_data.status,
        marked_by=user_id
    )
    
    db.add(db_attendance)
    
    # Audit logging
    audit_service.log_action(db, user_id, "CREATE", "Attendance")
    
    db.commit()
    db.refresh(db_attendance)
    return db_attendance

def get_student_attendance(db: Session, student_id: int, institution_id: int, skip: int = 0, limit: int = 100):
    # Verify student belongs to the institution
    student = db.query(Student).filter(
        Student.id == student_id,
        Student.institution_id == institution_id
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found in your institution"
        )
    
    return db.query(Attendance).filter(
        Attendance.student_id == student_id,
        Attendance.institution_id == institution_id
    ).offset(skip).limit(limit).all()

def get_institution_attendance_summary(db: Session, institution_id: Optional[int] = None, skip: int = 0, limit: int = 20):
    limit = min(limit, 100)
    results = _get_attendance_stats_query(db, institution_id).offset(skip).limit(limit).all()
    
    summary = []
    for row in results:
        total = row.total_days
        present = row.present_days
        percentage = round((present / total * 100), 2) if total > 0 else 0.0
        summary.append(AttendanceSummaryResponse(
            student_id=row.student_id,
            full_name=row.student_name,
            total_present=present,
            total_absent=total - present,
            attendance_percentage=percentage
        ))
        
    return summary

def get_student_attendance_risk(db: Session, student_id: int, institution_id: Optional[int] = None, month: Optional[int] = None, year: Optional[int] = None):
    # Base validation for student existence and multi-tenancy
    student_query = db.query(Student).filter(Student.id == student_id)
    if institution_id:
        student_query = student_query.filter(Student.institution_id == institution_id)
    student = student_query.first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found or access denied"
        )

    # Use centralized aggregation logic
    stats = _get_attendance_stats_query(db, institution_id, month, year).filter(Student.id == student_id).first()
    
    total_days = stats.total_days if stats else 0
    present_days = stats.present_days if stats else 0
    percentage = round((present_days / total_days * 100), 2) if total_days > 0 else 0.0
    
    return AttendancePercentageResponse(
        student_id=student.id,
        student_name=f"{student.first_name} {student.last_name}",
        total_days=total_days,
        present_days=present_days,
        attendance_percentage=percentage,
        risk_level=_calculate_risk_level(percentage, total_days)
    )

def get_high_risk_students(db: Session, institution_id: Optional[int] = None, month: Optional[int] = None, year: Optional[int] = None, skip: int = 0, limit: int = 100):
    # Get stats for all students in the institution
    results = _get_attendance_stats_query(db, institution_id, month, year).all()
    
    high_risk_students = []
    for row in results:
        total = row.total_days
        present = row.present_days
        percentage = round((present / total * 100), 2) if total > 0 else 0.0
        risk_level = _calculate_risk_level(percentage, total)
        
        if risk_level != RiskLevel.SAFE:
            high_risk_students.append(AttendancePercentageResponse(
                student_id=row.student_id,
                student_name=row.student_name,
                total_days=total,
                present_days=present,
                attendance_percentage=percentage,
                risk_level=risk_level
            ))
            
    # Apply pagination in Python since filtering by calculated risk level is easier here 
    # (unless we move risk logic into a SQL CASE statement, which we could do for better scaling)
    return high_risk_students[skip : skip + limit]
