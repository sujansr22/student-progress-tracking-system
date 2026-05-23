from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID
from app.models.models import UserRole, AttendanceStatus, RiskLevel, SurveyType, ProgressLevel, AssignedSurveyStatus

# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[UserRole] = None
    institution_id: Optional[int] = None

class RefreshRequest(BaseModel):
    refresh_token: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)

# Institution Schemas
class InstitutionBase(BaseModel):
    name: str

class InstitutionCreate(InstitutionBase):
    pass

class InstitutionResponse(InstitutionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole
    institution_id: Optional[int] = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Student Schemas
class StudentBase(BaseModel):
    student_unique_id: str
    first_name: str
    last_name: str
    email: EmailStr
    age: int
    gender: str
    enrollment_date: date
    health_notes: Optional[str] = None
    academic_year_id: int
    class_id: int

class StudentCreate(StudentBase):
    pass

class StudentUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    health_notes: Optional[str] = None
    is_active: Optional[bool] = None

class StudentResponse(StudentBase):
    id: UUID
    institution_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Attendance Schemas
class AttendanceBase(BaseModel):
    student_id: UUID
    date: date
    status: AttendanceStatus

class AttendanceCreate(AttendanceBase):
    pass

class AttendanceResponse(AttendanceBase):
    id: int
    institution_id: int
    marked_by: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class AttendanceSummaryResponse(BaseModel):
    student_id: UUID
    full_name: str
    total_present: int
    total_absent: int
    attendance_percentage: float

class AttendancePercentageResponse(BaseModel):
    student_id: UUID
    student_name: str
    total_days: int
    present_days: int
    attendance_percentage: float
    risk_level: RiskLevel

# Survey Schemas
class SurveyAnswerBase(BaseModel):
    question_key: str
    score: int

class SurveyAnswerCreate(SurveyAnswerBase):
    pass

class SurveySubmitRequest(BaseModel):
    student_id: UUID
    month: int
    year: int
    survey_type: SurveyType
    answers: List[SurveyAnswerCreate]

class SurveyAnswerResponse(SurveyAnswerBase):
    id: int

    class Config:
        from_attributes = True

class SurveyDetailedResponse(BaseModel):
    id: int
    student_id: UUID
    month: int
    year: int
    survey_type: SurveyType
    total_score: int
    percentage: float
    risk_level: str
    submitted_by: Optional[int]
    created_at: datetime
    answers: List[SurveyAnswerResponse]

    class Config:
        from_attributes = True

class StudentExportResponse(BaseModel):
    exported_at: datetime
    student: StudentResponse
    attendance_records: List[AttendanceResponse]
    survey_responses: List[SurveyDetailedResponse]

    class Config:
        from_attributes = True


class StudentProgressResponse(BaseModel):
    student_id: UUID
    student_name: str
    month: int
    year: int
    attendance_percentage: float
    instructor_survey_percentage: float
    student_survey_percentage: float
    final_progress_score: Optional[float]
    progress_level: ProgressLevel

# Academic Year Schemas
class AcademicYearBase(BaseModel):
    year_label: str
    start_date: date
    end_date: date
    is_active: bool = False

class AcademicYearCreate(AcademicYearBase):
    pass

class AcademicYearUpdate(BaseModel):
    year_label: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None

class AcademicYearResponse(AcademicYearBase):
    id: int
    institution_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# School Class Schemas
class SchoolClassBase(BaseModel):
    grade: str
    section: str
    class_label: Optional[str] = None
    is_active: bool = True

class SchoolClassCreate(SchoolClassBase):
    academic_year_id: int

class SchoolClassResponse(SchoolClassBase):
    id: int
    institution_id: int
    academic_year_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Class Instructor Map Schemas
class ClassInstructorMapBase(BaseModel):
    class_id: int
    instructor_id: int
    academic_year_id: int
    is_active: bool = True

class ClassInstructorMapCreate(ClassInstructorMapBase):
    pass

class ClassInstructorMapResponse(ClassInstructorMapBase):
    id: UUID
    institution_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# Subscription Schemas
class SubscriptionBase(BaseModel):
    is_active: bool = True
    end_date: date

class SubscriptionCreate(SubscriptionBase):
    institution_id: int

class SubscriptionResponse(SubscriptionBase):
    id: UUID
    institution_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class SubscriptionStatusResponse(BaseModel):
    institution_id: int
    institution_name: str
    is_active: bool
    end_date: date
    days_remaining: int
    is_in_grace_period: bool


# Assigned Survey Schemas
class AssignedSurveyCreate(BaseModel):
    student_id: UUID
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=2000)
    due_date: Optional[date] = None

class AssignedSurveyResponse(BaseModel):
    id: UUID
    student_id: UUID
    assigned_by: Optional[int]
    institution_id: int
    month: int
    year: int
    due_date: Optional[date]
    status: AssignedSurveyStatus
    created_at: datetime

    class Config:
        from_attributes = True
