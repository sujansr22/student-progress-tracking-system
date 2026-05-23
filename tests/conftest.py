"""
Test configuration and shared fixtures.
Uses a separate 'spts_test' PostgreSQL database — requires the Docker DB container to be running.
Each test function gets a rolled-back transaction so tests are fully isolated.
"""
import os
os.environ["TESTING"] = "true"   # disables rate limiting before any app module imports

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from starlette.testclient import TestClient

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings
from app.core.auth import get_password_hash
from app.models.models import Institution, User, UserRole, Subscription
from datetime import date, timedelta

# ── Test database URL ──────────────────────────────────────────────────────────
TEST_DB_URL = settings.DATABASE_URL.rsplit("/", 1)[0] + "/spts_test"


@pytest.fixture(scope="session")
def test_engine():
    # Create the test database (drop first for a clean slate)
    admin_url = settings.DATABASE_URL.rsplit("/", 1)[0] + "/postgres"
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        conn.execute(text("DROP DATABASE IF EXISTS spts_test"))
        conn.execute(text("CREATE DATABASE spts_test"))
    admin_engine.dispose()

    engine = create_engine(TEST_DB_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()

    # Clean up test database
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        conn.execute(text("DROP DATABASE IF EXISTS spts_test"))
    admin_engine.dispose()


@pytest.fixture(scope="function")
def db(test_engine):
    """Each test gets its own transaction that is rolled back on teardown."""
    connection = test_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Reusable data helpers ──────────────────────────────────────────────────────

def make_institution(db, name="Test School"):
    inst = Institution(name=name)
    db.add(inst)
    db.flush()
    return inst


def make_user(db, email, role, institution_id=None, password="Password123"):
    user = User(
        email=email,
        hashed_password=get_password_hash(password),
        role=role,
        institution_id=institution_id,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def make_subscription(db, institution_id, days_from_now=365):
    sub = Subscription(
        institution_id=institution_id,
        is_active=True,
        end_date=date.today() + timedelta(days=days_from_now),
    )
    db.add(sub)
    db.flush()
    return sub


def login(client, email, password="Password123"):
    resp = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()
