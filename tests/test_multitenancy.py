"""Tests: institution isolation — School A cannot access School B's data."""
import pytest
from tests.conftest import make_institution, make_user, make_subscription, login
from app.models.models import UserRole, AcademicYear, SchoolClass, Student
from datetime import date
import uuid


def _setup_two_schools(db):
    school_a = make_institution(db, "School Alpha")
    school_b = make_institution(db, "School Beta")
    make_subscription(db, school_a.id)
    make_subscription(db, school_b.id)

    admin_a = make_user(db, "admin_a@alpha.com", UserRole.SCHOOL_ADMIN, school_a.id)
    admin_b = make_user(db, "admin_b@beta.com",  UserRole.SCHOOL_ADMIN, school_b.id)
    instr_a = make_user(db, "instr_a@alpha.com", UserRole.INSTRUCTOR,   school_a.id)
    instr_b = make_user(db, "instr_b@beta.com",  UserRole.INSTRUCTOR,   school_b.id)

    # Academic year + class for school A
    year_a = AcademicYear(institution_id=school_a.id, year_label="2025-26",
                          start_date=date(2025, 4, 1), end_date=date(2026, 3, 31), is_active=True)
    db.add(year_a)
    db.flush()

    cls_a = SchoolClass(institution_id=school_a.id, academic_year_id=year_a.id,
                        grade="6", section="A", class_label="6-A", is_active=True)
    db.add(cls_a)
    db.flush()

    # Student in school A
    student_a = Student(
        id=uuid.uuid4(),
        student_unique_id="A001",
        first_name="Alice", last_name="Smith",
        email="alice@alpha.com", age=12, gender="Female",
        enrollment_date=date(2025, 4, 1),
        institution_id=school_a.id,
        academic_year_id=year_a.id,
        class_id=cls_a.id,
    )
    db.add(student_a)
    db.flush()

    return school_a, school_b, instr_a, instr_b, admin_a, admin_b, student_a


def test_instructor_cannot_see_other_school_students(client, db):
    _, _, instr_a, instr_b, _, _, student_a = _setup_two_schools(db)

    # instr_b (School B) tries to access School A's student
    tokens_b = login(client, "instr_b@beta.com")
    headers = {"Authorization": f"Bearer {tokens_b['access_token']}"}

    resp = client.get(f"/api/v1/students/{student_a.id}", headers=headers)
    assert resp.status_code == 404, "School B instructor should not see School A's student"


def test_instructor_can_see_own_school_student(client, db):
    _, _, instr_a, _, _, _, student_a = _setup_two_schools(db)

    tokens_a = login(client, "instr_a@alpha.com")
    headers = {"Authorization": f"Bearer {tokens_a['access_token']}"}

    resp = client.get(f"/api/v1/students/{student_a.id}", headers=headers)
    assert resp.status_code == 200


def test_school_admin_cannot_see_other_school_students(client, db):
    _, _, _, _, admin_a, admin_b, student_a = _setup_two_schools(db)

    tokens_b = login(client, "admin_b@beta.com")
    headers = {"Authorization": f"Bearer {tokens_b['access_token']}"}

    resp = client.get(f"/api/v1/students/{student_a.id}", headers=headers)
    # SCHOOL_ADMIN uses INSTRUCTOR role on this endpoint — will be 403 or 404
    assert resp.status_code in (403, 404)


def test_super_admin_can_see_any_school(client, db):
    _, _, _, _, _, _, student_a = _setup_two_schools(db)
    super_admin = make_user(db, "super@spts.com", UserRole.SUPER_ADMIN)

    tokens = login(client, "super@spts.com")
    # SUPER_ADMIN hits analytics (no institution filter)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp = client.get(
        f"/api/v1/analytics/student/{student_a.id}/progress",
        params={"month": 5, "year": 2025},
        headers=headers,
    )
    # Should be 200 (or INSUFFICIENT_DATA response, not 404)
    assert resp.status_code == 200


def test_analytics_institution_isolation(client, db):
    """School B instructor gets INSUFFICIENT_DATA or 404, never School A's data."""
    _, _, _, instr_b, _, _, student_a = _setup_two_schools(db)

    tokens_b = login(client, "instr_b@beta.com")
    headers = {"Authorization": f"Bearer {tokens_b['access_token']}"}

    resp = client.get(
        f"/api/v1/analytics/student/{student_a.id}/progress",
        params={"month": 5, "year": 2025},
        headers=headers,
    )
    # Institution filter in analytics → student not found for this institution
    assert resp.status_code in (404, 200)
    if resp.status_code == 200:
        assert resp.json().get("progress_level") == "INSUFFICIENT_DATA"
