import os

# Testler gerçek veritabanına ve gerçek anahtara dokunmasın.
# Bu satırlar, app modülleri içe aktarılmadan ÖNCE çalışmalı.
os.environ["SECRET_KEY"] = "test-secret-key-only-for-tests"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def make_user(client):
    def _make(email="a@example.com", password="password123"):
        client.post("/auth/register", json={"email": email, "password": password})
        r = client.post("/auth/login", data={"username": email, "password": password})
        return {"Authorization": f"Bearer {r.json()['access_token']}"}

    return _make