import enum
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Index, Enum, Date, UniqueConstraint, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.core.encryption import EncryptedText

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    SCHOOL_ADMIN = "SCHOOL_ADMIN"
    INSTRUCTOR = "INSTRUCTOR"
    STUDENT = "STUDENT"

class AttendanceStatus(str, enum.Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    LATE = "LATE"

class RiskLevel(str, enum.Enum):
    SAFE = "SAFE"
    LOW_ATTENDANCE = "LOW_ATTENDANCE"
    HIGH_RISK = "HIGH_RISK"

class SurveyType(str, enum.Enum):
    INSTRUCTOR = "INSTRUCTOR"
    STUDENT = "STUDENT"

class ProgressLevel(str, enum.Enum):
    THRIVING = "THRIVING"
    STABLE = "STABLE"
    NEEDS_ATTENTION = "NEEDS_ATTENTION"
    CRITICAL = "CRITICAL"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"

class Institution(Base):
    __tablename__ = "institutions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    users = relationship("User", back_populates="institution")
    students = relationship("Student", back_populates="institution")
    attendance_records = relationship("Attendance", back_populates="institution")
    survey_responses = relationship("SurveyResponse", back_populates="institution")
    academic_years = relationship("AcademicYear", back_populates="institution", cascade="all, delete-orphan")
    classes = relationship("SchoolClass", back_populates="institution", cascade="all, delete-orphan")
    class_instructor_maps = relationship("ClassInstructorMap", back_populates="institution", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="institution", cascade="all, delete-orphan")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(Enum(UserRole), nullable=False)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="RESTRICT"), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    institution = relationship("Institution", back_populates="users")
    marked_attendance = relationship("Attendance", back_populates="creator")
    submitted_surveys = relationship("SurveyResponse", back_populates="submitter")
    audit_logs = relationship("AuditLog", back_populates="user")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_user_institution_id", "institution_id"),
        Index("ix_users_institution_role", "institution_id", "role"),
    )

class Student(Base):
    __tablename__ = "students"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_unique_id = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String, nullable=False)
    enrollment_date = Column(Date, nullable=False)
    health_notes = Column(EncryptedText, nullable=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="RESTRICT"), nullable=False, index=True)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id", ondelete="RESTRICT"), nullable=False, index=True)
    class_id = Column(Integer, ForeignKey("classes.id", ondelete="RESTRICT"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, unique=True)
    is_active = Column(Boolean, default=True, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    institution = relationship("Institution", back_populates="students")
    school_class = relationship("SchoolClass", back_populates="students")
    attendance_records = relationship("Attendance", back_populates="student")
    survey_responses = relationship("SurveyResponse", back_populates="student")
    assigned_surveys = relationship("AssignedSurvey", back_populates="student", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("institution_id", "student_unique_id", name="unique_student_id_per_institution"),
        Index("ix_students_institution_academic_year", "institution_id", "academic_year_id"),
    )

class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="RESTRICT"), nullable=False, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="RESTRICT"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    status = Column(Enum(AttendanceStatus), nullable=False)
    marked_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    student = relationship("Student", back_populates="attendance_records")
    institution = relationship("Institution", back_populates="attendance_records")
    creator = relationship("User", back_populates="marked_attendance")

    __table_args__ = (
        UniqueConstraint("student_id", "date", name="unique_student_attendance_per_day"),
        Index("ix_attendance_student_date", "student_id", "date"),
    )

class SurveyResponse(Base):
    __tablename__ = "survey_responses"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="RESTRICT"), nullable=False, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="RESTRICT"), nullable=False, index=True)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    survey_type = Column(Enum(SurveyType), nullable=False)
    total_score = Column(Integer, nullable=False)
    percentage = Column(Integer, nullable=False) # Changed to Integer as per typical use, but can be float
    risk_level = Column(String, nullable=False)
    submitted_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    student = relationship("Student", back_populates="survey_responses")
    institution = relationship("Institution", back_populates="survey_responses")
    submitter = relationship("User", back_populates="submitted_surveys")
    answers = relationship("SurveyAnswer", back_populates="survey_response", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("student_id", "month", "year", "survey_type", name="unique_survey_per_period"),
        Index("ix_survey_student_month", "student_id", "month", "year"),
    )

class SurveyAnswer(Base):
    __tablename__ = "survey_answers"

    id = Column(Integer, primary_key=True, index=True)
    survey_response_id = Column(Integer, ForeignKey("survey_responses.id", ondelete="RESTRICT"), nullable=False)
    question_key = Column(String, nullable=False)
    score = Column(Integer, nullable=False)

    survey_response = relationship("SurveyResponse", back_populates="answers")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)
    entity = Column(String, nullable=False)
    ip_address = Column(String, nullable=True)
    action_type = Column(String, nullable=False)  # READ / CREATE / UPDATE / DELETE 
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="audit_logs")

class AcademicYear(Base):
    __tablename__ = "academic_years"

    id = Column(Integer, primary_key=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="RESTRICT"), nullable=False, index=True)
    year_label = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    institution = relationship("Institution", back_populates="academic_years")
    classes = relationship("SchoolClass", back_populates="academic_year", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("institution_id", "year_label", name="unique_year_label_per_institution"),
        Index(
            "ix_only_one_active_year_per_institution",
            "institution_id",
            unique=True,
            postgresql_where=(is_active == True)
        ),
    )

class SchoolClass(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="RESTRICT"), nullable=False, index=True)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id", ondelete="RESTRICT"), nullable=False, index=True)
    grade = Column(String, nullable=False)
    section = Column(String, nullable=False)
    class_label = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    institution = relationship("Institution", back_populates="classes")
    academic_year = relationship("AcademicYear", back_populates="classes")
    students = relationship("Student", back_populates="school_class")
    instructor_mappings = relationship("ClassInstructorMap", back_populates="school_class", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("institution_id", "academic_year_id", "grade", "section", name="unique_class_per_year"),
        Index("ix_classes_institution_academic_year", "institution_id", "academic_year_id"),
    )

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="RESTRICT"), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    end_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    institution = relationship("Institution", back_populates="subscriptions")

class ClassInstructorMap(Base):
    __tablename__ = "class_instructor_maps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_id = Column(Integer, ForeignKey("classes.id", ondelete="RESTRICT"), nullable=False, index=True)
    instructor_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id", ondelete="RESTRICT"), nullable=False, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="RESTRICT"), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    school_class = relationship("SchoolClass", back_populates="instructor_mappings")
    instructor = relationship("User")
    academic_year = relationship("AcademicYear")
    institution = relationship("Institution", back_populates="class_instructor_maps")

    __table_args__ = (
        UniqueConstraint("instructor_id", "class_id", "academic_year_id", name="unique_instructor_mapping_per_year"),
        Index("ix_mappings_institution_academic_year", "institution_id", "academic_year_id"),
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="refresh_tokens")

    __table_args__ = (
        Index("ix_refresh_tokens_hash", "token_hash", unique=True),
    )


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="reset_tokens")


class AssignedSurveyStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"


class AssignedSurvey(Base):
    __tablename__ = "assigned_surveys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="RESTRICT"), nullable=False, index=True)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    due_date = Column(Date, nullable=True)
    status = Column(Enum(AssignedSurveyStatus), nullable=False, default=AssignedSurveyStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    student = relationship("Student", back_populates="assigned_surveys")
    instructor = relationship("User", foreign_keys=[assigned_by])

    __table_args__ = (
        UniqueConstraint("student_id", "month", "year", name="unique_assignment_per_period"),
    )
