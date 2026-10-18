from urls import canonical_job_url


def test_linkedin_tracking_is_dropped():
    a = canonical_job_url("https://www.linkedin.com/jobs/view/123456/?refId=x7Gq&trackingId=abc")
    b = canonical_job_url("https://linkedin.com/jobs/view/123456")
    assert a == b == "https://www.linkedin.com/jobs/view/123456"


def test_linkedin_search_page_with_a_job_open_is_that_job():
    url = "https://www.linkedin.com/jobs/search/?currentJobId=123456&keywords=react"
    assert canonical_job_url(url) == "https://www.linkedin.com/jobs/view/123456"


def test_seek_keeps_only_the_job_id():
    url = "https://www.seek.com.au/job/87654321?type=standard&ref=search-standalone#sol=abc"
    assert canonical_job_url(url) == "https://www.seek.com.au/job/87654321"


def test_indeed_keeps_the_job_key_but_drops_tracking():
    a = canonical_job_url("https://au.indeed.com/viewjob?jk=abc123&from=serp&vjs=3")
    b = canonical_job_url("https://au.indeed.com/viewjob?jk=abc123")
    assert a == b


def test_parameter_order_and_utm_tags_dont_matter():
    a = canonical_job_url("https://jobs.example.com/apply?id=9&lang=en&utm_source=x")
    b = canonical_job_url("https://jobs.example.com/apply?lang=en&id=9")
    assert a == b
