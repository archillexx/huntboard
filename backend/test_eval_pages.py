"""The evaluation's scoring maths (no AI calls)."""
from eval_pages import same_text, skill_scores


def test_text_match_ignores_case_and_spacing_but_not_content():
    assert same_text("Sydney, NSW", "sydney,  nsw")
    assert not same_text("Sydney, NSW", "Sydney NSW")
    assert same_text(None, None)
    assert not same_text(None, "Acme")


def test_skill_precision_and_recall():
    scores = skill_scores(expected=["react", "sql", "aws", "git"], extracted=["react", "sql", "jira"])
    assert scores["precision"] == 2 / 3      # 2 of the 3 it returned were right
    assert scores["recall"] == 2 / 4         # it found 2 of the 4 it should have
    assert scores["invented"] == ["jira"]
    assert scores["missed"] == ["aws", "git"]


def test_skills_are_compared_after_normalising():
    assert skill_scores(["node.js"], ["NodeJS"])["precision"] == 1.0


def test_empty_cases_are_not_divisions_by_zero():
    assert skill_scores([], [])["precision"] == 1.0
    assert skill_scores(["react"], [])["recall"] == 0.0
