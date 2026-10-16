"""Pytest configuration: in-memory SQLite test DB and dependency overrides."""
import os
import sys

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_soc.db")
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("CORTEX_DEMO_MODE", "true")
os.environ.setdefault("AI_DEMO_MODE", "true")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import engine as app_engine, SessionLocal as app_session
from app.models.base import Base
from app.main import app
from app.api.deps import get_db
from app.core.security import hash_password
from app.models.user import User

TEST_DB_URL = "sqlite:///./test_soc.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    # Remove any leftover test DB from a previous interrupted run.
    try:
        os.remove(TEST_DB_URL.replace("sqlite:///", ""))
    except OSError:
        pass
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    if not db.query(User).first():
        db.add(User(username="analyst", email="analyst@test.local", password_hash=hash_password("password123"), role="analyst", is_active=True))
        db.add(User(username="admin", email="admin@test.local", password_hash=hash_password("admin123"), role="admin", is_active=True))
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)
    try:
        os.remove(TEST_DB_URL.replace("sqlite:///", ""))
    except OSError:
        pass


@pytest.fixture
def db():
    app.dependency_overrides[get_db] = override_get_db
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
    app.dependency_overrides.clear()


@pytest.fixture
def client(db):
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    r = client.post("/api/auth/login", json={"username": "analyst", "password": "password123"})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}