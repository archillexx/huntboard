"""Reading job pages: structured data first, then the AI on a selection or the whole page."""
import pytest

import extraction
from conftest import login_as
from extraction import ExtractionFailed
from jobposting import ExtractedPosting, html_to_text, job_from_json_ld, read_job_page


# ---------- a fake AI client (same idea as test_extraction.py) ----------

class FakeResult:
    def __init__(self, posting):
        self.output_parsed = posting


class FakeResponses:
    """Plays back a script: a dict becomes a posting, "fail" raises a ValidationError. Records each input."""
    def __init__(self, outcomes):
        self.outcomes = outcomes
        self.inputs = []

    def parse(self, **kwargs):
        self.inputs.append(kwargs["input"])
        outcome = self.outcomes.pop(0)
        if outcome == "fail":
            ExtractedPosting.model_validate({"company": 123})   # wrong shape -> ValidationError
        return FakeResult(ExtractedPosting(**outcome))


class FakeClient:
    def __init__(self, outcomes):
        self.responses = FakeResponses(outcomes)


POSTING = {"company": "Riverside Bakery", "role": "Head Pastry Chef", "location": "Hobart, TAS",
           "description": "Lead our pastry kitchen."}


# ---------- 1. structured data ----------

def test_json_ld_job_posting_becomes_fields_without_ai():
    blocks = [{
        "@type": "JobPosting", "title": "Software Developer",
        "hiringOrganization": {"@type": "Organization", "name": "Lightbulb School"},
        "jobLocation": {"@type": "Place", "address": {"addressLocality": "Brisbane", "addressRegion": "QLD"}},
        "description": "<p>React &amp; PHP</p><ul><li>AWS</li></ul>",
    }]
    job = job_from_json_ld(blocks)
    assert job["company"] == "Lightbulb School"
    assert job["role"] == "Software Developer"
    assert job["location"] == "Brisbane, QLD"
    assert "React & PHP" in job["description"] and "- AWS" in job["description"]


def test_job_posting_inside_graph_is_found():
    blocks = [{"@graph": [{"@type": "WebSite"}, {"@type": "JobPosting", "title": "Chef", "hiringOrganization": "Cafe"}]}]
    assert job_from_json_ld(blocks)["company"] == "Cafe"


def test_only_a_website_block_means_no_job():   # what SEEK gives
    assert job_from_json_ld([{"@graph": [{"@type": "WebSite", "url": "https://au.seek.com"}]}]) is None


def test_html_to_text_keeps_lists_readable():
    assert html_to_text("<p>Skills</p><ul><li>React</li><li>SQL</li></ul>") == "Skills\n\n- React\n- SQL"


# ---------- 2. choosing the path ----------

def test_structured_data_wins_and_skips_the_ai():
    fake = FakeClient([])   # an empty script: any AI call would crash the test
    blocks = [{"@type": "JobPosting", "title": "Chef", "hiringOrganization": {"name": "Cafe"}}]
    job = read_job_page(blocks, selection="x" * 500, page_text="page", llm_client=fake)
    assert job["source"] == "json_ld"
    assert fake.responses.inputs == []


def test_a_real_selection_is_read_instead_of_the_page():
    fake = FakeClient([POSTING])
    job = read_job_page(None, selection="the job text " * 30, page_text="whole noisy page", llm_client=fake)
    assert job["source"] == "selection"
    assert "whole noisy page" not in fake.responses.inputs[0]


def test_a_tiny_selection_is_ignored_and_the_page_is_read():
    fake = FakeClient([POSTING])
    job = read_job_page(None, selection="oops", page_text="whole page", llm_client=fake)
    assert job["source"] == "page"
    assert fake.responses.inputs == ["whole page"]


def test_page_text_is_trimmed_before_the_ai_sees_it():
    fake = FakeClient([POSTING])
    read_job_page(None, page_text="x" * 50_000, llm_client=fake)
    assert len(fake.responses.inputs[0]) == 20_000


def test_one_failure_is_retried():
    fake = FakeClient(["fail", POSTING])
    assert read_job_page(None, page_text="page", llm_client=fake)["company"] == "Riverside Bakery"


def test_two_failures_raise_extraction_failed():
    with pytest.raises(ExtractionFailed):
        read_job_page(None, page_text="page", llm_client=FakeClient(["fail", "fail"]))


def test_nothing_to_read_is_an_error():
    with pytest.raises(ValueError):
        read_job_page(None, selection="", page_text="   ", llm_client=FakeClient([]))


# ---------- 3. the route ----------

def test_parse_page_returns_fields_without_saving(client, monkeypatch):
    monkeypatch.setattr(extraction, "client", FakeClient([POSTING]))
    headers = login_as(client, "hal@example.com")
    body = client.post("/jobs/parse-page", headers=headers,
                       json={"url": "https://www.seek.com.au/job/111?ref=x", "pageText": "noisy page"}).json()
    assert body["companyName"] == "Riverside Bakery"
    assert body["jobUrl"] == "https://www.seek.com.au/job/111"
    assert body["source"] == "page"
    assert client.get("/jobs", headers=headers).json() == []   # nothing saved yet


def test_parse_page_spots_an_already_saved_job_before_any_ai_call(client, monkeypatch):
    monkeypatch.setattr(extraction, "client", FakeClient([]))   # any AI call would crash
    headers = login_as(client, "hal@example.com")
    saved = client.post("/jobs", headers=headers, json={
        "companyName": "Cafe", "jobRole": "Chef", "jobUrl": "https://www.seek.com.au/job/111"}).json()
    body = client.post("/jobs/parse-page", headers=headers,
                       json={"url": "https://www.seek.com.au/job/111?ref=y", "pageText": "page"}).json()
    assert body["alreadySavedJobId"] == saved["jobId"]


def test_parse_page_needs_a_login(client):
    assert client.post("/jobs/parse-page", json={"url": "https://x.com", "pageText": "p"}).status_code == 401
