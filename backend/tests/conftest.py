"""Points the app at an isolated, throwaway SQLite DB and Chroma directory
before any app module is imported, and sets DEMO_MODE so tests never call
the real Gemini API."""

import os
import tempfile

_TEST_DIR = tempfile.mkdtemp(prefix="customerops_test_")
os.environ.setdefault("DEMO_MODE", "true")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_TEST_DIR}/test.db")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-do-not-use-in-production")
os.environ.setdefault("CHROMA_PERSIST_DIR", os.path.join(_TEST_DIR, "chroma"))

import pytest
from fastapi.testclient import TestClient

from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.main import app
from app.models.agent import SupportAgent


@pytest.fixture(autouse=True)
def _clean_database():
    """Recreates the schema fresh before every test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def support_agent(db):
    agent = SupportAgent(
        full_name="Test Agent",
        email="test.agent@example.com",
        password_hash=hash_password("password123"),
        role="support_agent",
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


@pytest.fixture
def team_lead(db):
    agent = SupportAgent(
        full_name="Test Lead",
        email="test.lead@example.com",
        password_hash=hash_password("password123"),
        role="team_lead",
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


@pytest.fixture
def agent_headers(client, support_agent):
    r = client.post(
        "/api/v1/auth/login", json={"email": support_agent.email, "password": "password123"}
    )
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def lead_headers(client, team_lead):
    r = client.post(
        "/api/v1/auth/login", json={"email": team_lead.email, "password": "password123"}
    )
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
