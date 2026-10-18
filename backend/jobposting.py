"""Turn a job page (from the browser extension) into job fields: company, role, location, description.

Three sources, cheapest and cleanest first:
  1. the page's JSON-LD JobPosting (structured data for search engines): plain code, no AI
  2. the text you selected on the page: the AI reads just that
  3. the page's whole visible text, trimmed: the AI reads it and ignores the noise
Skills are NOT extracted here: the saved description goes through extract_skills like any job.
"""

import html
import re
from html.parser import HTMLParser

from openai import APIError
from pydantic import BaseModel, ValidationError

import extraction
from extraction import ExtractionFailed

MAX_PAGE_CHARS = 20_000      # a job page's useful part fits easily; more is menus and "similar jobs"
MIN_SELECTION_CHARS = 200    # shorter than this is probably an accidental selection, not the job


# ---------- 1. Structured data (no AI) ----------

def _find_job_postings(node):
    """Yield every JobPosting object, wherever it sits: top level, in a list, or inside @graph."""
    if isinstance(node, list):
        for item in node:
            yield from _find_job_postings(item)
    elif isinstance(node, dict):
        kind = node.get("@type")
        kinds = kind if isinstance(kind, list) else [kind]
        if "JobPosting" in kinds:
            yield node
        if "@graph" in node:
            yield from _find_job_postings(node["@graph"])


def _location_from(job_location) -> str | None:
    """schema.org allows one place or a list, and an address object or a plain string."""
    place = job_location[0] if isinstance(job_location, list) and job_location else job_location
    if not isinstance(place, dict):
        return None
    address = place.get("address")
    if isinstance(address, str):
        return address.strip() or None
    if isinstance(address, dict):
        parts = [address.get("addressLocality"), address.get("addressRegion")]
        return ", ".join(p.strip() for p in parts if isinstance(p, str) and p.strip()) or None
    return None


def job_from_json_ld(blocks) -> dict | None:
    """The first JobPosting with a title and a company, as job fields; None if there isn't one."""
    for posting in _find_job_postings(blocks or []):
        org = posting.get("hiringOrganization")
        company = org.get("name") if isinstance(org, dict) else org
        role = posting.get("title")
        if isinstance(company, str) and company.strip() and isinstance(role, str) and role.strip():
            return {
                "company": company.strip(),
                "role": role.strip(),
                "location": _location_from(posting.get("jobLocation")),
                "description": html_to_text(posting.get("description") or "") or None,
            }
    return None


# ---------- 2. HTML description -> readable text ----------

class _TextCollector(HTMLParser):
    """Keeps the text, turns block tags into line breaks and list items into "- " lines."""

    BREAKS = {"p", "div", "br", "ul", "ol", "h1", "h2", "h3", "h4", "tr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)   # turns &amp; into & as it reads
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == "li":
            self.parts.append("\n- ")
        elif tag in self.BREAKS:
            self.parts.append("\n")

    def handle_data(self, data):
        self.parts.append(data)


def html_to_text(raw: str) -> str:
    collector = _TextCollector()
    collector.feed(html.unescape(raw) if "<" not in raw else raw)
    text = "".join(collector.parts)
    text = re.sub(r"[ \t]+", " ", text)          # squeeze runs of spaces
    text = re.sub(r"\n\s*\n+", "\n\n", text)     # at most one blank line in a row
    return text.strip()


# ---------- 3. The AI path ----------

class ExtractedPosting(BaseModel):
    """What the AI must return. None = the text doesn't say (never a guess)."""
    company: str | None
    role: str | None
    location: str | None
    description: str | None


POSTING_PROMPT = """You read the text of a job advertisement page and extract the ONE job being advertised.

The text may be a whole web page: navigation menus, cookie notices, "similar jobs", "people also viewed",
salary widgets, footers and other job titles. Ignore all of that. Use only the main job posting.

Return:
- company: the employer that is hiring. Not the job board (SEEK, LinkedIn, Indeed) and not a recruitment
  agency. If an agency advertises for an unnamed client ("our client", "a leading bank"), return null.
- role: the job title exactly as the advertisement writes it.
- location: city and state or region, e.g. "Sydney, NSW" or "Melbourne, VIC". Include "Remote" only if the
  job is fully remote. Null if not stated.
- description: the posting's own text — responsibilities, requirements, about the role — copied as written,
  without page clutter or other jobs.

If something is not stated in the main posting, return null. Never guess and never take it from another job
on the page.

Example input:
"Skip to content  Jobs  Companies  Sign in
 Head Pastry Chef
 Riverside Bakery · Hobart TAS · Full time
 We're looking for a Head Pastry Chef to lead our pastry kitchen. You'll need laminated dough experience.
 Similar jobs  Sous Chef  Harbour Cafe · Launceston TAS
 © 2026 JobSite"

Example output:
{"company": "Riverside Bakery", "role": "Head Pastry Chef", "location": "Hobart, TAS",
 "description": "We're looking for a Head Pastry Chef to lead our pastry kitchen. You'll need laminated dough experience."}
"""


def extract_job_posting(page_text: str, llm_client=None) -> ExtractedPosting:
    """Ask the AI for the job's fields; one retry, then ExtractionFailed (the same design as extract_skills)."""
    llm_client = llm_client or extraction.client   # looked up at call time, so tests can pass a fake

    def ask():
        response = llm_client.responses.parse(
            text_format=ExtractedPosting,
            model="gpt-5-mini",
            instructions=POSTING_PROMPT,
            input=page_text,
        )
        return response.output_parsed

    try:
        return ask()
    except (APIError, ValidationError):
        try:
            return ask()
        except (APIError, ValidationError):
            raise ExtractionFailed("Could not read the job posting after 2 attempts")


# ---------- 4. Choosing the path ----------

def read_job_page(json_ld=None, selection: str | None = None, page_text: str | None = None, llm_client=None) -> dict:
    """Job fields plus which source produced them: "json_ld", "selection" or "page"."""
    from_structured = job_from_json_ld(json_ld)
    if from_structured:
        return {**from_structured, "source": "json_ld"}

    selection = (selection or "").strip()
    if len(selection) >= MIN_SELECTION_CHARS:
        text, source = selection, "selection"
    else:
        text, source = (page_text or "").strip()[:MAX_PAGE_CHARS], "page"
    if not text:
        raise ValueError("Nothing to read: no structured data, no selection and no page text")

    posting = extract_job_posting(text, llm_client)
    return {**posting.model_dump(), "source": source}
