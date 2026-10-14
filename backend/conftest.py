"""Shared pytest setup for tests that need the real API and a real (throwaway) database.

pytest loads this file automatically. The fixtures below are only used by tests that ask
for them by name, so the pure scoring/extraction tests don't touch a database at all.
"""
import os
import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
import main
from main import app, get_db

# Never the real database: the same server, a separate "job_tracker_test" database
# that every test run wipes and rebuilds.
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    os.environ["DATABASE_URL"].rsplit("/", 1)[0] + "/job_tracker_test",
)


@pytest.fixture
def client(monkeypatch):
    """A test client whose requests use a fresh, empty test database.

    Emails never really send in tests: send_email is swapped for a fake that
    records each message in client.outbox, so tests can read the codes.
    """
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

    outbox = []
    monkeypatch.setattr(main, "send_email", lambda to, subject, text: outbox.append({"to": to, "subject": subject, "text": text}))

    test_client = TestClient(app)
    test_client.outbox = outbox
    yield test_client
    app.dependency_overrides.clear()
    engine.dispose()


def last_code(client, email):
    """The 6-digit code in the newest email the fake outbox got for this address."""
    message = [m for m in client.outbox if m["to"] == email][-1]
    return re.search(r"\b(\d{6})\b", message["text"]).group(1)


def login_as(client, email, password="a-long-password"):
    """Sign up, verify with the emailed code, and return the Authorization header."""
    client.post("/auth/signup", json={"email": email, "password": password})
    token = client.post("/auth/verify", json={"email": email, "code": last_code(client, email)}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
