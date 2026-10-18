"""One standard form per job posting URL, so the duplicate check isn't fooled by tracking junk.

Same posting, different visits:
    https://www.linkedin.com/jobs/view/123456/?refId=x7Gq&trackingId=abc
    https://www.linkedin.com/jobs/view/123456/
both become  https://www.linkedin.com/jobs/view/123456
"""

import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

# Query parameters that only track how you arrived, never which job it is.
TRACKING_PARAMS = {"refid", "trackingid", "trk", "trkinfo", "lipi", "ref", "from", "source", "src",
                   "gclid", "fbclid", "msclkid", "sol_id", "origin", "searchid", "tk", "vjs", "advn"}


def canonical_job_url(url: str) -> str:
    parts = urlsplit(url.strip())
    host = parts.netloc.lower()
    path = parts.path.rstrip("/")

    # LinkedIn: the job id is in the path, so the query can go entirely.
    # A search page with a job open (?currentJobId=123) is the same job as /jobs/view/123.
    if host.endswith("linkedin.com"):
        params = dict(parse_qsl(parts.query))
        job_id = params.get("currentJobId") or (re.search(r"/jobs/view/(\d+)", path) or [None, None])[1]
        if job_id:
            return f"https://www.linkedin.com/jobs/view/{job_id}"

    # SEEK: /job/12345678 is the job; everything after ? is tracking.
    if host.endswith("seek.com.au") or host.endswith("seek.com"):
        match = re.search(r"/job/(\d+)", path)
        if match:
            return f"https://{host}/job/{match.group(1)}"

    # Everyone else (Indeed's ?jk=, careers pages): keep meaningful parameters, drop tracking ones,
    # sort what's left so the order doesn't matter, and drop the #fragment.
    kept = sorted((k, v) for k, v in parse_qsl(parts.query)
                  if k.lower() not in TRACKING_PARAMS and not k.lower().startswith("utm_"))
    return urlunsplit(("https", host, path, urlencode(kept), ""))
