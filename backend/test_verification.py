"""Email verification: sign up -> code by email -> /auth/verify. Uses the fake outbox from conftest.py."""
from datetime import timedelta

import codes
from conftest import last_code

EMAIL = "carol@example.com"
PASSWORD = "a-long-password"


def sign_up(client):
    return client.post("/auth/signup", json={"email": EMAIL, "password": PASSWORD})


def log_in(client):
    return client.post("/auth/login", data={"username": EMAIL, "password": PASSWORD})


def verify(client, code):
    return client.post("/auth/verify", json={"email": EMAIL, "code": code})


def wrong(code):
    """Some other 6-digit code: change the last digit."""
    return code[:-1] + str((int(code[-1]) + 1) % 10)


def test_signup_emails_a_code_and_login_waits_for_it(client):
    assert sign_up(client).status_code == 201
    assert len(client.outbox) == 1
    assert log_in(client).status_code == 403          # right password, but not verified yet


def test_right_code_verifies_and_logs_in(client):
    sign_up(client)
    response = verify(client, last_code(client, EMAIL))
    assert response.status_code == 200

    token = response.json()["access_token"]
    assert client.get("/jobs", headers={"Authorization": f"Bearer {token}"}).status_code == 200
    assert log_in(client).status_code == 200          # login works from now on


def test_wrong_code_is_refused(client):
    sign_up(client)
    assert verify(client, wrong(last_code(client, EMAIL))).status_code == 400
    assert log_in(client).status_code == 403


def test_five_wrong_guesses_kill_the_code(client):
    sign_up(client)
    code = last_code(client, EMAIL)
    for _ in range(codes.MAX_ATTEMPTS):
        verify(client, wrong(code))

    # Even the right code is refused now. This only passes if each failed attempt was committed.
    response = verify(client, code)
    assert response.status_code == 400
    assert "Too many" in response.json()["detail"]


def test_expired_code_is_refused(client, monkeypatch):
    monkeypatch.setattr(codes, "CODE_LIFETIME", timedelta(seconds=-1))   # every new code is born expired
    sign_up(client)
    response = verify(client, last_code(client, EMAIL))
    assert response.status_code == 400
    assert "expired" in response.json()["detail"]


def test_resend_waits_for_the_cooldown(client):
    sign_up(client)
    client.post("/auth/resend-code", json={"email": EMAIL})
    assert len(client.outbox) == 1                    # too soon: nothing new sent


def test_resend_replaces_the_old_code(client, monkeypatch):
    monkeypatch.setattr(codes, "RESEND_COOLDOWN", timedelta(0))
    sign_up(client)
    old = last_code(client, EMAIL)
    client.post("/auth/resend-code", json={"email": EMAIL})
    new = last_code(client, EMAIL)
    assert len(client.outbox) == 2

    if old != new:                                    # 1 in a million they match
        assert verify(client, old).status_code == 400
    assert verify(client, new).status_code == 200


def test_resend_says_the_same_thing_for_unknown_emails(client):
    sign_up(client)
    known = client.post("/auth/resend-code", json={"email": EMAIL})
    unknown = client.post("/auth/resend-code", json={"email": "nobody@example.com"})
    assert known.status_code == unknown.status_code == 200
    assert known.json() == unknown.json()
