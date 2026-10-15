"""Proves each user only sees and changes their own data (task 7.5)."""
from conftest import login_as


def test_no_token_is_rejected(client):
    assert client.get("/jobs").status_code == 401


def test_users_only_see_their_own_jobs(client):
    alice = login_as(client, "alice@gmail.com")
    bob = login_as(client, "bob@gmail.com")
    client.post("/jobs", json={"companyName": "Canva", "jobRole": "Dev"}, headers=alice)

    assert [j["companyName"] for j in client.get("/jobs", headers=alice).json()] == ["Canva"]
    assert client.get("/jobs", headers=bob).json() == []


def test_cannot_change_someone_elses_job(client):
    alice = login_as(client, "alice@gmail.com")
    bob = login_as(client, "bob@gmail.com")
    job_id = client.post("/jobs", json={"companyName": "Canva", "jobRole": "Dev"}, headers=alice).json()["jobId"]

    # Bob gets the same 404 as for a job that doesn't exist.
    assert client.patch(f"/jobs/{job_id}", json={"jobStatus": "Rejected"}, headers=bob).status_code == 404
    assert client.put(f"/jobs/{job_id}/skills", json={"skills": ["python"]}, headers=bob).status_code == 404
    assert client.post(f"/jobs/{job_id}/extract", headers=bob).status_code == 404
    # ...and Alice's job is untouched.
    assert client.get("/jobs", headers=alice).json()[0]["jobStatus"] == "Applied"


def test_profile_skills_are_per_user(client):
    alice = login_as(client, "alice@gmail.com")
    bob = login_as(client, "bob@gmail.com")
    client.put("/profile/skills", json={"skills": ["python"]}, headers=alice)
    client.put("/profile/skills", json={"skills": ["java"]}, headers=bob)

    assert client.get("/profile/skills", headers=alice).json() == {"skills": ["python"]}
    assert client.get("/profile/skills", headers=bob).json() == {"skills": ["java"]}


def test_health_needs_no_login(client):
    assert client.get("/health").json() == {"status": "ok"}
