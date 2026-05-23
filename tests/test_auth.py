"""Tests: authentication, token refresh, password reset."""
import pytest
from tests.conftest import make_institution, make_user, login
from app.models.models import UserRole


def test_register_success(client):
    resp = client.post("/api/v1/auth/register", json={"email": "new@test.com", "password": "Password123"})
    assert resp.status_code == 201
    assert resp.json()["email"] == "new@test.com"


def test_register_duplicate_email(client):
    client.post("/api/v1/auth/register", json={"email": "dup@test.com", "password": "Password123"})
    resp = client.post("/api/v1/auth/register", json={"email": "dup@test.com", "password": "Password123"})
    assert resp.status_code == 400


def test_register_short_password(client):
    resp = client.post("/api/v1/auth/register", json={"email": "short@test.com", "password": "abc"})
    assert resp.status_code == 422


def test_login_success(client, db):
    make_user(db, "admin@test.com", UserRole.SUPER_ADMIN)
    tokens = login(client, "admin@test.com")
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"


def test_login_wrong_password(client, db):
    make_user(db, "user@test.com", UserRole.INSTRUCTOR)
    resp = client.post("/api/v1/auth/login", data={"username": "user@test.com", "password": "WRONG"})
    assert resp.status_code == 401


def test_login_unknown_email(client):
    resp = client.post("/api/v1/auth/login", data={"username": "ghost@test.com", "password": "anything"})
    assert resp.status_code == 401


def test_refresh_token_works(client, db):
    make_user(db, "refresh@test.com", UserRole.SUPER_ADMIN)
    tokens = login(client, "refresh@test.com")

    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 200
    new_tokens = resp.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens
    # Refresh token must always rotate to a new value
    assert new_tokens["refresh_token"] != tokens["refresh_token"]


def test_refresh_token_rotation(client, db):
    """Once a refresh token is used, it cannot be used again."""
    make_user(db, "rotate@test.com", UserRole.SUPER_ADMIN)
    tokens = login(client, "rotate@test.com")
    old_refresh = tokens["refresh_token"]

    # Use it once — valid
    client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})

    # Use same token again — must fail
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert resp.status_code == 401


def test_invalid_refresh_token(client):
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": "completely-fake-token"})
    assert resp.status_code == 401


def test_logout_invalidates_token(client, db):
    make_user(db, "logout@test.com", UserRole.SUPER_ADMIN)
    tokens = login(client, "logout@test.com")

    client.post("/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]})

    # Token should no longer work
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 401


def test_forgot_password_always_200(client):
    """Never reveals whether the email exists."""
    resp = client.post("/api/v1/auth/forgot-password", json={"email": "ghost@test.com"})
    assert resp.status_code == 200


def test_reset_password_invalid_token(client):
    resp = client.post("/api/v1/auth/reset-password", json={"token": "fake", "new_password": "NewPass123"})
    assert resp.status_code == 400


def test_reset_password_full_flow(client, db):
    from app.core.auth import create_password_reset_token
    user = make_user(db, "reset@test.com", UserRole.INSTRUCTOR)
    plain_token = create_password_reset_token(db, user.id)

    resp = client.post("/api/v1/auth/reset-password", json={"token": plain_token, "new_password": "NewPassword123"})
    assert resp.status_code == 200

    # Old password no longer works
    resp = client.post("/api/v1/auth/login", data={"username": "reset@test.com", "password": "Password123"})
    assert resp.status_code == 401

    # New password works
    resp = client.post("/api/v1/auth/login", data={"username": "reset@test.com", "password": "NewPassword123"})
    assert resp.status_code == 200


def test_reset_token_single_use(client, db):
    from app.core.auth import create_password_reset_token
    user = make_user(db, "once@test.com", UserRole.INSTRUCTOR)
    plain_token = create_password_reset_token(db, user.id)

    client.post("/api/v1/auth/reset-password", json={"token": plain_token, "new_password": "NewPassword123"})

    # Second use must fail
    resp = client.post("/api/v1/auth/reset-password", json={"token": plain_token, "new_password": "AnotherPass123"})
    assert resp.status_code == 400
