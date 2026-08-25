"""Rules baseline — a faithful port of a production demo-form grading model.

Four weighted dimensions, graded from structured fields only. It cannot read
the free-text message; that blindness is the experiment. Deterministic, free,
and instant — the bar any LLM scorer has to beat by enough to justify its
cost.
"""

import re

ICP_INDUSTRIES = {"Retail", "Insurance", "Financial Services",
                  "Telecommunications", "Healthcare"}

# Acronyms must match whole words: "Director" contains "cto", and the first
# version of this port quietly promoted every director to C-level because of
# it. Substring matching on titles is a bug generator, not a parser.
C_LEVEL = {"chief", "cto", "cio", "ceo", "cfo", "coo", "cmo"}
VP_DIR = {"vp", "vice", "director", "head"}
MANAGER = {"manager", "lead"}

PERSONAL_DOMAINS = {"personalmail.example.org", "gmail.example.org"}

REGION = {
    "United States": "NA", "Canada": "NA",
    "Germany": "EU", "United Kingdom": "EU", "France": "EU", "Poland": "EU",
    "Japan": "APAC", "Australia": "APAC",
}


def title_seniority(title: str) -> str:
    words = set(re.split(r"[^a-z]+", title.lower()))
    if words & C_LEVEL:
        return "c_level"
    if words & VP_DIR:
        return "vp_dir"
    if words & MANAGER:
        return "manager"
    return "junior"


def score_lead(lead: dict) -> dict:
    """Return {'grade': 'A'|'B'|'D', 'score': int, 'rationale': str}."""
    personal = lead["email"].split("@")[-1] in PERSONAL_DOMAINS

    # A personal email severs the link to the company: firmographics unknown.
    size = 0 if personal else int(lead["company_size"])
    industry = "Unknown" if personal else lead["industry"]

    size_pts = 40 if size >= 500 else 30 if size >= 200 else \
               20 if size >= 50 else 5 if size >= 10 else 0
    title_pts = {"c_level": 30, "vp_dir": 25,
                 "manager": 15, "junior": 0}[title_seniority(lead["title"])]
    industry_pts = 15 if industry in ICP_INDUSTRIES else 5
    geo_pts = {"NA": 15, "EU": 12, "APAC": 8}.get(
        REGION.get(lead["country"], "Other"), 3)

    total = size_pts + title_pts + industry_pts + geo_pts
    grade = "A" if total >= 75 else "B" if total >= 45 else "D"
    return {
        "grade": grade,
        "score": total,
        "rationale": f"size={size_pts} title={title_pts} "
                     f"industry={industry_pts} geo={geo_pts}"
                     + (" (personal email: firmographics zeroed)" if personal else ""),
    }
