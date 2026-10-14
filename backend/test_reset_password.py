"""Forgot password: email -> reset code -> new password. Uses the fake outbox from conftest.py."""
import time

from conftest import last_code, login_as

EMAIL = "erin@example.com"
OLD = "a-long-password"
NEW = "a-brand-new-password"


def forgot(client, email=EMAIL):
    return client.post("/auth/forgot-password", json={"email": email})


def reset(client, code, new=NEW):
    return client.post("/auth/reset-password", json={"email": EMAIL, "code": code, "new_password": new})


def log_in(client, password):
    return client.post("/auth/login", data={"username": EMAIL, "password": password})


def wrong(code):
    return code[:-1] + str((int(code[-1]) + 1) % 10)


def test_reset_flow_swaps_the_password(client):
    login_as(client, EMAIL, OLD)
    assert forgot(client).status_code == 200
    response = reset(client, last_code(client, EMAIL))
    assert response.status_code == 200
    assert log_in(client, OLD).status_code == 401
    assert log_in(client, NEW).status_code == 200


def test_reset_logs_out_old_sessions(client):
    old_session = login_as(client, EMAIL, OLD)
    time.sleep(1.1)   # tokens record whole seconds
    forgot(client)
    reset(client, last_code(client, EMAIL))
    assert client.get("/jobs", headers=old_session).status_code == 401


def test_unknown_email_gets_the_same_reply_and_no_email(client):
    login_as(client, EMAIL, OLD)
    sent_before = len(client.outbox)
    known = forgot(client)
    unknown = forgot(client, "nobody@example.com")
    assert known.json() == unknown.json()
    assert known.status_code == unknown.status_code == 200
    assert len(client.outbox) == sent_before + 1     # only the real account got an email


def test_wrong_code_changes_nothing(client):
    login_as(client, EMAIL, OLD)
    forgot(client)
    assert reset(client, wrong(last_code(client, EMAIL))).status_code == 400
    assert log_in(client, OLD).status_code == 200


def test_a_verification_code_cannot_reset_a_password(client):
    client.post("/auth/signup", json={"email": EMAIL, "password": OLD})
    verify_code = last_code(client, EMAIL)            # emailed at signup, purpose verify_email
    assert reset(client, verify_code).status_code == 400
