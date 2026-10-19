"""Jobs saved with a URL (from the browser extension): the same posting can't be saved twice."""
from conftest import login_as

URL = "https://au.indeed.com/viewjob?jk=abc123"


def new_job(client, headers, url=URL):
    return client.post("/jobs", headers=headers, json={
        "companyName": "Lightbulb School", "jobRole": "Software Developer",
        "jobUrl": url, "location": "Brisbane, QLD",
    })


def test_url_and_location_are_saved_and_returned(client):
    headers = login_as(client, "fay@example.com")
    job = new_job(client, headers).json()
    assert job["jobUrl"] == URL
    assert job["location"] == "Brisbane, QLD"


def test_same_url_twice_is_refused_and_points_at_the_first(client):
    headers = login_as(client, "fay@example.com")
    first = new_job(client, headers).json()
    again = new_job(client, headers)
    assert again.status_code == 409
    assert again.json()["detail"]["jobId"] == first["jobId"]


def test_two_users_can_save_the_same_posting(client):
    fay = login_as(client, "fay@example.com")
    gus = login_as(client, "gus@example.com")
    assert new_job(client, fay).status_code == 201
    assert new_job(client, gus).status_code == 201


def test_jobs_without_a_url_never_clash(client):
    headers = login_as(client, "fay@example.com")
    for _ in range(2):
        response = client.post("/jobs", headers=headers, json={"companyName": "Acme", "jobRole": "Dev"})
        assert response.status_code == 201


def test_same_linkedin_job_with_new_tracking_is_still_a_duplicate(client):
    headers = login_as(client, "fay@example.com")
    assert new_job(client, headers, "https://www.linkedin.com/jobs/view/42/?refId=one").status_code == 201
    assert new_job(client, headers, "https://www.linkedin.com/jobs/view/42/?refId=two").status_code == 409


def test_invisible_nul_bytes_from_a_web_page_are_stripped_before_saving(client):
    # A real SEEK description carried a NUL byte (\x00) and Postgres refused the save.
    headers = login_as(client, "fay@example.com")
    response = client.post("/jobs", headers=headers, json={
        "companyName": "Compare\x00 the Market", "jobRole": "Software Engineer",
        "jobDescription": "Who We Are\x00\n\nWe help Australians\tcompare.\x07",
    })
    assert response.status_code == 201
    job = response.json()
    assert job["companyName"] == "Compare the Market"
    assert job["jobDescription"] == "Who We Are\n\nWe help Australians\tcompare."   # newline and tab kept
