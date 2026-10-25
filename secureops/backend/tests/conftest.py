import os

os.environ["JWT_SECRET"] = "test-only-secret-that-is-more-than-32-characters"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.auth import hash_password
from app.db import Base, get_db
from app.main import app
from app.models import User


@pytest.fixture
def client(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    monkeypatch.setattr("app.main.get_engine", lambda: engine)

    def override():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = override
    with Session(engine) as db:
        db.add_all([
            User(email="admin@example.com", full_name="Test Admin", role="admin", password_hash=hash_password("long-password-for-admin")),
            User(email="viewer@example.com", full_name="Test Viewer", role="viewer", password_hash=hash_password("long-password-for-viewer")),
            User(email="analyst@example.com", full_name="Test Analyst", role="analyst", password_hash=hash_password("long-password-for-analyst")),
        ])
        db.commit()

    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture
def token(client):
    def get(email="admin@example.com", password="long-password-for-admin"):
        response = client.post("/api/auth/login", json={"email": email, "password": password})
        assert response.status_code == 200, response.text
        return {"Authorization": "Bearer " + response.json()["access_token"]}
    return get
