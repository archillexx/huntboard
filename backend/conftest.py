"""Shared pytest setup for tests that need the real API and a real (throwaway) database.

pytest loads this file automatically. The fixtures below are only used by tests that ask
for them by name, so the pure scoring/extraction tests don't touch a database at all.
"""
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from main import app, get_db

# Never the real database: the same server, a separate "job_tracker_test" database
# that every test run wipes and rebuilds.
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    os.environ["DATABASE_URL"].rsplit("/", 1)[0] + "/job_tracker_test",
)


@pytest.fixture
def client():
    """A test client whose requests use a fresh, empty test database."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.drop_all(engine)     # start from nothing, every test
    Base.metadata.create_all(engine)   # tables straight from models.py
    TestSession = sessionmaker(bind=engine)

    def get_test_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    # Every route that asks for get_db gets the test database instead.
    app.dependency_overrides[get_db] = get_test_db
    yield TestClient(app)
    app.dependency_overrides.clear()
    engine.dispose()


def login_as(client, email, password="a-long-password"):
    """Sign up a user and return the Authorization header for their token."""
    client.post("/auth/signup", json={"email": email, "password": password})
    token = client.post("/auth/login", data={"username": email, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
