"""Change password while logged in: other sessions are logged out, this one keeps going."""
import time

from conftest import login_as

EMAIL = "dave@example.com"
OLD = "a-long-password"
NEW = "a-brand-new-password"


def change(client, headers, current, new):
    return client.post("/auth/change-password", headers=headers,
                       json={"current_password": current, "new_password": new})


def log_in(client, password):
    return client.post("/auth/login", data={"username": EMAIL, "password": password})


def test_change_password_swaps_which_password_works(client):
    headers = login_as(client, EMAIL, OLD)
    assert change(client, headers, OLD, NEW).status_code == 200
    assert log_in(client, OLD).status_code == 401
    assert log_in(client, NEW).status_code == 200


def test_wrong_current_password_changes_nothing(client):
    headers = login_as(client, EMAIL, OLD)
    assert change(client, headers, "not-my-password", NEW).status_code == 400
    assert log_in(client, OLD).status_code == 200


def test_other_sessions_are_logged_out_but_this_one_continues(client):
    other_device = login_as(client, EMAIL, OLD)
    time.sleep(1.1)   # tokens record whole seconds; make sure the change is clearly later
    this_device = {"Authorization": f"Bearer {log_in(client, OLD).json()['access_token']}"}

    time.sleep(1.1)
    response = change(client, this_device, OLD, NEW)
    fresh = {"Authorization": f"Bearer {response.json()['access_token']}"}

    assert client.get("/jobs", headers=other_device).status_code == 401
    assert client.get("/jobs", headers=this_device).status_code == 401   # its old token too
    assert client.get("/jobs", headers=fresh).status_code == 200          # the new one works


def test_change_password_needs_a_login(client):
    assert client.post("/auth/change-password", json={"current_password": OLD, "new_password": NEW}).status_code == 401
