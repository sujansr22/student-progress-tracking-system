"""Tests: subscription enforcement with 7-day grace period."""
import pytest
from datetime import date, timedelta
from tests.conftest import make_institution, make_user, make_subscription, login
from app.models.models import UserRole, Subscription, AcademicYear, SchoolClass
import uuid


def _make_school_with_instructor(db, name="Acme School", sub_days=365):
    inst = make_institution(db, name)
    if sub_days is not None:
        make_subscription(db, inst.id, days_from_now=sub_days)
    instr = make_user(db, f"instr@{name.lower().replace(' ', '')}.com", UserRole.INSTRUCTOR, inst.id)
    return inst, instr


def _mark_attendance_request(client, headers, student_id):
    return client.post("/api/v1/attendance/mark", json={
        "student_id": str(student_id),
        "date": str(date.today()),
        "status": "PRESENT",
    }, headers=headers)


def test_active_subscription_allows_write(client, db):
    inst, instr = _make_school_with_instructor(db, "Active School", sub_days=365)
    tokens = login(client, instr.email)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # Create a student (write operation) — should be allowed
    # We expect 400 (missing academic year) not 402 (subscription block)
    resp = client.post("/api/v1/students/", json={
        "student_unique_id": "S001", "first_name": "Test", "last_name": "User",
        "email": "s001@active.com", "age": 10, "gender": "Male",
        "enrollment_date": str(date.today()), "academic_year_id": 999, "class_id": 999,
    }, headers=headers)
    assert resp.status_code != 402, "Active subscription should not return 402"


def test_no_subscription_blocks_write(client, db):
    inst, instr = _make_school_with_instructor(db, "No Sub School", sub_days=None)
    tokens = login(client, instr.email)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = client.post("/api/v1/students/", json={
        "student_unique_id": "S001", "first_name": "Test", "last_name": "User",
        "email": "s001@nosub.com", "age": 10, "gender": "Male",
        "enrollment_date": str(date.today()), "academic_year_id": 1, "class_id": 1,
    }, headers=headers)
    assert resp.status_code == 402


def test_expired_beyond_grace_blocks_write(client, db):
    """Subscription expired 10 days ago (beyond 7-day grace) — must block."""
    inst, instr = _make_school_with_instructor(db, "Expired School", sub_days=None)

    sub = Subscription(
        institution_id=inst.id,
        is_active=True,
        end_date=date.today() - timedelta(days=10),
    )
    db.add(sub)
    db.flush()

    tokens = login(client, instr.email)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = client.post("/api/v1/students/", json={
        "student_unique_id": "S001", "first_name": "Test", "last_name": "User",
        "email": "s001@expired.com", "age": 10, "gender": "Male",
        "enrollment_date": str(date.today()), "academic_year_id": 1, "class_id": 1,
    }, headers=headers)
    assert resp.status_code == 402


def test_within_grace_period_allows_write(client, db):
    """Subscription expired 3 days ago — still within 7-day grace, must allow."""
    inst, instr = _make_school_with_instructor(db, "Grace School", sub_days=None)

    sub = Subscription(
        institution_id=inst.id,
        is_active=True,
        end_date=date.today() - timedelta(days=3),
    )
    db.add(sub)
    db.flush()

    tokens = login(client, instr.email)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = client.post("/api/v1/students/", json={
        "student_unique_id": "S001", "first_name": "Test", "last_name": "User",
        "email": "s001@grace.com", "age": 10, "gender": "Male",
        "enrollment_date": str(date.today()), "academic_year_id": 999, "class_id": 999,
    }, headers=headers)
    # Should NOT be 402 — subscription check passes (even if 400 for missing class/year)
    assert resp.status_code != 402, "Grace period should allow write access"


def test_read_always_allowed_after_expiry(client, db):
    """Expired subscription must never block GET (read) endpoints."""
    inst, instr = _make_school_with_instructor(db, "Read School", sub_days=None)

    sub = Subscription(
        institution_id=inst.id, is_active=True,
        end_date=date.today() - timedelta(days=30),
    )
    db.add(sub)
    db.flush()

    tokens = login(client, instr.email)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = client.get("/api/v1/students/", headers=headers)
    assert resp.status_code == 200, "Expired subscription must not block read access"


def test_super_admin_never_blocked(client, db):
    super_admin = make_user(db, "superadmin@spts.com", UserRole.SUPER_ADMIN)
    tokens = login(client, "superadmin@spts.com")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # SUPER_ADMIN creates institution (write op) — no subscription needed
    resp = client.post("/api/v1/institutions/", json={"name": "New School"}, headers=headers)
    assert resp.status_code == 201
