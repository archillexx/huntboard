"""Score the page reader against the golden pages in tests/fixtures/pages/.

Each page folder holds page.txt (the visible text), jsonld.json (only if the page had structured data)
and expected.json (the answer, written by hand before any AI saw the page).

Run by hand — it makes real AI calls (a few cents):
    python eval_pages.py
Not part of pytest/CI on purpose; the scoring maths below IS tested (test_eval_pages.py).
"""

import json
from pathlib import Path

from extraction import extract_skills
from jobposting import read_job_page
from scoring import normalise_skills

PAGES = Path(__file__).parent / "tests" / "fixtures" / "pages"
FIELDS = ["company", "role", "location"]


def same_text(expected, actual) -> bool:
    """Exact match after ignoring case and extra spaces. null only matches null."""
    if expected is None or actual is None:
        return expected is None and actual is None
    clean = lambda s: " ".join(s.lower().split())
    return clean(expected) == clean(actual)


def skill_scores(expected: list[str], extracted: list[str]) -> dict:
    """Precision: of the skills it returned, how many were right. Recall: of the right ones, how many it found."""
    want, got = set(normalise_skills(expected)), set(normalise_skills(extracted))
    right = want & got
    precision = len(right) / len(got) if got else (1.0 if not want else 0.0)
    recall = len(right) / len(want) if want else 1.0
    return {"precision": precision, "recall": recall,
            "invented": sorted(got - want), "missed": sorted(want - got)}


def evaluate_page(folder: Path) -> dict:
    expected = json.loads((folder / "expected.json").read_text())
    jsonld_file = folder / "jsonld.json"
    jsonld = json.loads(jsonld_file.read_text()) if jsonld_file.exists() else None

    # The same call the extension triggers, minus a selection: the hardest realistic case.
    job = read_job_page(jsonld, None, (folder / "page.txt").read_text())
    skills = extract_skills(job["description"]) if job["description"] else []

    return {
        "page": folder.name,
        "source": job["source"],
        "fields": {f: {"ok": same_text(expected[f], job[f]), "expected": expected[f], "got": job[f]} for f in FIELDS},
        "skills": skill_scores(expected["skills"], skills),
    }


def main():
    results = [evaluate_page(folder) for folder in sorted(p for p in PAGES.iterdir() if p.is_dir())]

    print(f"\n{'page':38} {'source':9} " + " ".join(f"{f:9}" for f in FIELDS) + " skills P   skills R")
    for r in results:
        marks = " ".join(f"{'✓' if r['fields'][f]['ok'] else '✗':9}" for f in FIELDS)
        print(f"{r['page']:38} {r['source']:9} {marks} {r['skills']['precision']:8.2f}   {r['skills']['recall']:.2f}")

    n = len(results)
    print("\nField accuracy: " + ", ".join(f"{f} {sum(r['fields'][f]['ok'] for r in results)}/{n}" for f in FIELDS))
    print(f"Skills: mean precision {sum(r['skills']['precision'] for r in results) / n:.2f}, "
          f"mean recall {sum(r['skills']['recall'] for r in results) / n:.2f}")

    print("\nWhat went wrong (the part to read):")
    for r in results:
        for f in FIELDS:
            if not r["fields"][f]["ok"]:
                print(f"  {r['page']}: {f} expected {r['fields'][f]['expected']!r}, got {r['fields'][f]['got']!r}")
        if r["skills"]["invented"]:
            print(f"  {r['page']}: invented skills {r['skills']['invented']}")
        if r["skills"]["missed"]:
            print(f"  {r['page']}: missed skills {r['skills']['missed']}")


if __name__ == "__main__":
    main()
