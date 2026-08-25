"""LLM scorer — grades a lead the way a careful human reviewer would,
given the same playbook and ALL the evidence, including the free-text
message the rules baseline cannot read.

Uses structured outputs (`client.messages.parse`) so the grade is a
validated enum, never a string to regex out of prose. Credentials resolve
from the environment (ANTHROPIC_API_KEY or an `ant auth login` profile).
"""

import time
from typing import Literal

import anthropic
from pydantic import BaseModel

# USD per 1M tokens (Claude API list prices, cached 2026-08).
PRICES = {
    "claude-opus-5": (5.00, 25.00),
    "claude-opus-4-8": (5.00, 25.00),
    "claude-sonnet-5": (3.00, 15.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-haiku-4-5": (1.00, 5.00),
}

SYSTEM = """You grade inbound demo-form leads for a B2B SaaS company selling
knowledge-management and support automation to mid-size and enterprise teams.

Ideal customer profile: companies in industries like Retail, Insurance,
Financial Services, Telecommunications, or Healthcare; the bigger the support
organization, the better. Primary buyers: support/CX/IT leadership.

Grades:
- A: priority — a plausible buyer at a strong-fit company with real intent
  or urgency. Gets the priority booking calendar.
- B: standard — a plausible buyer, fit or intent not yet strong. Standard
  booking calendar.
- D: not sales-ready — poor fit, no purchase intent, or not a buyer at all.
  Thank-you page.

Judgment rules, in the order a careful reviewer applies them:
1. Read the message first. Vendors pitching services, partnership/reseller
   inquiries, media offers, and research/thesis requests are D regardless of
   title or company — they are not buyers.
2. A personal email does not disqualify a lead. If the message credibly
   identifies a real company, role, and buying intent, grade on that
   evidence.
3. Explicit urgency with a mandate (contract expiring, approved budget,
   active vendor shortlist) upgrades an otherwise-B lead to A.
4. Absent message signal, grade on firmographics: company size matters most,
   then seniority, then industry fit, then region (NA/EU strongest).
5. When genuinely torn between B and D, choose B — a wasted call costs less
   than a lost buyer. When torn between A and B with no urgency evidence,
   choose B."""

PROMPT = """Grade this lead:

Name: {first_name} {last_name}
Email: {email}
Title: {title}
Company: {company}
Industry: {industry}
Company size: {company_size} employees
Country: {country}
Form message: {form_message!r}"""


class LeadGrade(BaseModel):
    grade: Literal["A", "B", "D"]
    rationale: str


def make_client() -> anthropic.Anthropic:
    return anthropic.Anthropic()


def score_lead(client: anthropic.Anthropic, lead: dict,
               model: str = "claude-opus-5") -> dict:
    """Return {'grade', 'rationale', 'input_tokens', 'output_tokens',
    'latency_s'} — or {'grade': None, 'error': ...} on hard failure.

    `lead` arrives pre-stripped by the harness (VISIBLE_FIELDS in
    run_eval.py) — the scorer never has label columns to leak."""
    t0 = time.perf_counter()
    try:
        response = client.messages.parse(
            model=model,
            max_tokens=2000,
            system=SYSTEM,
            messages=[{"role": "user", "content": PROMPT.format(**lead)}],
            output_format=LeadGrade,
        )
    except anthropic.RateLimitError as exc:
        return {"grade": None, "error": f"rate_limit: {exc}"}
    except anthropic.APIStatusError as exc:
        return {"grade": None, "error": f"api_{exc.status_code}: {exc}"}
    except anthropic.APIConnectionError as exc:
        return {"grade": None, "error": f"connection: {exc}"}
    latency = time.perf_counter() - t0

    if response.stop_reason == "refusal":
        return {"grade": None, "error": "refusal"}
    parsed = response.parsed_output
    return {
        "grade": parsed.grade,
        "rationale": parsed.rationale,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "latency_s": round(latency, 3),
    }
