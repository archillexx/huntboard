from extraction import extract_skills, ExtractedSkills, ExtractionFailed
import pytest


class FakeResult:
    """Looks like the real API's response: has .output_parsed.skills."""
    def __init__(self, skills):
        self.output_parsed = ExtractedSkills(skills=skills)


class FakeResponses:
    """Stands in for client.responses; follows a script of outcomes."""
    def __init__(self, outcomes):
        self.count = 0
        self.outcomes = outcomes
    def parse(self, **kwargs):
        self.count = self.count + 1
        outcome = self.outcomes.pop(0)
        if outcome == "fail":
            ExtractedSkills.model_validate({"skills": "oops"})   # raises ValidationError
        else:
            return FakeResult(outcome)


class FakeClient:
    """Stands in for the OpenAI client: has .responses.parse."""
    def __init__(self, outcomes):
        self.responses = FakeResponses(outcomes)

def test_returns_skills_on_first_try():
    description= "Javascript and C++"
    fake = FakeClient([["python", "sql"]])
    assert extract_skills(description,llm_client = fake) == ["python","sql"]
    assert fake.responses.count == 1

def test_retries_once_then_succeeds():
    description= "Javascript and C++"
    fake = FakeClient(["fail", ["python"]]) 
    assert extract_skills(description,llm_client = fake) == ["python"]
    assert fake.responses.count == 2

def test_raises_extraction_failed_after_two_failures():
    description= "Javascript and C++"
    fake = FakeClient(["fail", "fail"]) 
    with pytest.raises(ExtractionFailed):
        extract_skills(description,llm_client = fake)
    assert fake.responses.count == 2