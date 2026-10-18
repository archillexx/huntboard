"""Deleting jobs: only your own, and the URL is free to save again afterwards."""
from conftest import login_as


def make_job(client, headers, **extra):
    return client.post("/jobs", headers=headers, json={"companyName": "Acme", "jobRole": "Dev", **extra}).json()


def test_delete_removes_the_job(client):
    headers = login_as(client, "ivy@example.com")
    job = make_job(client, headers)
    assert client.delete(f"/jobs/{job['jobId']}", headers=headers).status_code == 204
    assert client.get("/jobs", headers=headers).json() == []


def test_deleting_a_job_also_removes_its_skills(client):
    headers = login_as(client, "ivy@example.com")
    job = make_job(client, headers)
    client.put(f"/jobs/{job['jobId']}/skills", headers=headers, json={"skills": ["react", "sql"]})
    client.delete(f"/jobs/{job['jobId']}", headers=headers)
    assert client.get("/gaps", headers=headers).json() == []   # no skills left anywhere


def test_cannot_delete_someone_elses_job(client):
    ivy = login_as(client, "ivy@example.com")
    jon = login_as(client, "jon@example.com")
    job = make_job(client, ivy)
    assert client.delete(f"/jobs/{job['jobId']}", headers=jon).status_code == 404
    assert len(client.get("/jobs", headers=ivy).json()) == 1   # still there


def test_a_deleted_postings_url_can_be_saved_again(client):
    headers = login_as(client, "ivy@example.com")
    url = "https://www.seek.com.au/job/555"
    job = make_job(client, headers, jobUrl=url)
    client.delete(f"/jobs/{job['jobId']}", headers=headers)
    assert client.post("/jobs", headers=headers, json={"companyName": "Acme", "jobRole": "Dev", "jobUrl": url}).status_code == 201


def test_delete_needs_a_login(client):
    assert client.delete("/jobs/1").status_code == 401
