#!/usr/bin/env python3
"""Deterministic labeled dataset for lead-scoring evals.

300 synthetic demo-form submissions with ground-truth grades. The ground
truth simulates what a careful human reviewer decides with ALL the evidence,
including the free-text message — which the rules baseline cannot read.

Case types (column `case_type`):
  clean      (~70%)  structured fields tell the whole story; rules suffice
  trap       (~15%)  the form message contradicts the structured fields —
                     hidden enterprise buyers behind personal emails, vendors
                     and students behind corporate-looking signals
  ambiguous  (~15%)  genuinely borderline; ground truth follows a documented
                     tie-break (favor the customer-facing outcome: when in
                     doubt between B and D, grade B — a wasted SDR call costs
                     less than a lost buyer)

Grades: A = priority calendar · B = standard calendar · D = thank-you page.
Everything is seeded; same CSV on every run.
"""

import csv
import os
import random

random.seed(7)
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "leads.csv")

FIRST = ["Emma", "Liam", "Sofia", "Noah", "Ava", "Lucas", "Mia", "Ethan",
         "Nina", "Oscar", "Lea", "Hugo", "Ida", "Felix", "Maja", "Jonas"]
LAST = ["Walker", "Novak", "Fischer", "Moreau", "Rossi", "Jensen", "Kaur",
        "Silva", "Berg", "Klein", "Sato", "Olsen", "Varga", "Dias"]
COMPANIES = [
    ("Northwind Retail Group", "northwindretail.example.com", "Retail", 4200),
    ("Cascade Insurance", "cascadeins.example.com", "Insurance", 2800),
    ("Beacon Financial", "beaconfin.example.com", "Financial Services", 1500),
    ("Atlas Telecom", "atlastelecom.example.com", "Telecommunications", 9000),
    ("Harborview Health", "harborviewhealth.example.com", "Healthcare", 3500),
    ("Vertex Logistics", "vertexlogistics.example.com", "Logistics", 800),
    ("Solid Manufacturing", "solidmfg.example.com", "Manufacturing", 1200),
    ("Nimbus Software", "nimbussoft.example.com", "Technology", 350),
    ("Cedar Commerce", "cedarcommerce.example.com", "Retail", 240),
    ("Orbit Analytics", "orbitanalytics.example.com", "Technology", 90),
    ("Granite Foods", "granitefoods.example.com", "Manufacturing", 600),
    ("Helix Media", "helixmedia.example.com", "Media", 150),
    ("Kite Consulting", "kiteconsult.example.com", "Consulting", 12),
    ("Falcon Energy", "falconenergy.example.com", "Energy", 2200),
    ("Prima Services", "primaservices.example.com", "Business Services", 45),
]
ICP_INDUSTRIES = {"Retail", "Insurance", "Financial Services",
                  "Telecommunications", "Healthcare"}
TITLES = {
    "c_level": ["Chief Information Officer", "CTO", "Chief Customer Officer", "CEO"],
    "vp_dir": ["VP Customer Support", "VP Operations", "Director of CX",
               "Head of Support Operations", "Director of IT"],
    "manager": ["Support Operations Manager", "IT Manager", "CX Program Manager",
                "Service Desk Manager"],
    "junior": ["Support Agent", "Business Analyst", "Operations Associate",
               "Graduate Student", "Marketing Intern"],
}
GEO = [("United States", "NA"), ("Canada", "NA"), ("Germany", "EU"),
       ("United Kingdom", "EU"), ("France", "EU"), ("Poland", "EU"),
       ("Japan", "APAC"), ("Australia", "APAC"), ("Brazil", "Other"),
       ("South Africa", "Other")]

CLEAN_MESSAGES = [
    "Interested in a demo for our support team.",
    "We'd like to see how the platform handles our ticket volume.",
    "Looking to modernize our knowledge base. Please reach out.",
    "Saw your webinar, want to learn more.",
    "Evaluating options for customer-service automation.",
    "Can you show us the reporting capabilities?",
    "",
    "",
]
HIDDEN_ENTERPRISE_MESSAGES = [
    "I run support operations at {company} ({size}+ agents). Using my personal "
    "email because our filters eat vendor mail. We're evaluating platforms for Q4.",
    "Writing from my personal address — I'm the {title} at {company}. We have "
    "budget approved for a knowledge-management overhaul this quarter.",
    "This is for {company} (I'm on the leadership team, ~{size} employees). "
    "Corporate email is tied up in an IT migration, please reply here.",
]
VENDOR_MESSAGES = [
    "We provide offshore staffing for support teams and would love to explore "
    "a partnership. Who handles vendor relationships?",
    "I run an agency helping SaaS companies with SEO. This is about a "
    "collaboration, not a purchase.",
    "We'd like to feature your product in our paid newsletter. Media-kit rates attached.",
    "Reseller inquiry: we distribute software in our region and want margin terms.",
]
STUDENT_MESSAGES = [
    "I'm writing my master's thesis on AI in customer service. Could I get "
    "access for research purposes?",
    "Preparing a university case study about your category. No purchase intent, "
    "just a few questions.",
]
URGENT_MIDMARKET_MESSAGES = [
    "Our current vendor's contract expires in six weeks and we're not renewing. "
    "Need a decision path fast — {size} agents to migrate.",
    "Board signed off on replacing our support stack this quarter. Shortlisting "
    "two vendors, you're one of them.",
]
AMBIGUOUS_MESSAGES = [
    "Just exploring what's out there for now.",
    "Comparing a few tools for a project later this year.",
    "A colleague recommended you — not sure yet if this fits our roadmap.",
    "Curious about pricing.",
]

rows = []
lead_id = 0


def add_row(case_type, first, last, email, title, company, industry, size,
            country, message, true_grade, rationale):
    global lead_id
    lead_id += 1
    rows.append({
        "lead_id": f"L{lead_id:04d}",
        "case_type": case_type,
        "first_name": first,
        "last_name": last,
        "email": email,
        "title": title,
        "company": company,
        "industry": industry,
        "company_size": size,
        "country": country,
        "form_message": message.strip(),
        "true_grade": true_grade,
        "truth_rationale": rationale,
    })


def rules_grade(seniority, size, industry, region, personal_email):
    """The same scoring the rules baseline uses — used here only to label
    the clean cases, where the reviewer and the rules agree by design."""
    if personal_email:
        size_known, industry_known = 0, "Unknown"
    else:
        size_known, industry_known = size, industry
    pts = 0
    pts += 40 if size_known >= 500 else 30 if size_known >= 200 else \
           20 if size_known >= 50 else 5 if size_known >= 10 else 0
    pts += {"c_level": 30, "vp_dir": 25, "manager": 15, "junior": 0}[seniority]
    pts += 15 if industry_known in ICP_INDUSTRIES else 5
    pts += {"NA": 15, "EU": 12, "APAC": 8, "Other": 3}[region]
    return "A" if pts >= 75 else "B" if pts >= 45 else "D"


# ------------------------------------------------------------------ clean 210
for _ in range(210):
    first, last = random.choice(FIRST), random.choice(LAST)
    name, domain, industry, size = random.choice(COMPANIES)
    seniority = random.choice(list(TITLES))
    title = random.choice(TITLES[seniority])
    country, region = random.choice(GEO)
    personal = random.random() < 0.10
    email = (f"{first}.{last}{lead_id}@personalmail.example.org".lower()
             if personal else f"{first}.{last}{lead_id}@{domain}".lower())
    grade = rules_grade(seniority, size, industry, region, personal)
    add_row("clean", first, last, email, title, name, industry, size, country,
            random.choice(CLEAN_MESSAGES), grade,
            "Structured fields are the whole story; message adds nothing.")

# ------------------------------------------------------------------ traps 45
for _ in range(18):   # hidden enterprise buyer behind a personal email
    first, last = random.choice(FIRST), random.choice(LAST)
    name, domain, industry, size = random.choice(
        [c for c in COMPANIES if c[3] >= 800])
    seniority = random.choice(["c_level", "vp_dir"])
    title = random.choice(TITLES[seniority])
    country, region = random.choice(GEO[:8])
    email = f"{first}.{last}{lead_id}@personalmail.example.org".lower()
    msg = random.choice(HIDDEN_ENTERPRISE_MESSAGES).format(
        company=name, size=size, title=title)
    add_row("trap", first, last, email, title, name, industry, size, country,
            msg, "A",
            "Personal email hides an enterprise buyer; the message names the "
            "company, scale, and buying intent.")

for _ in range(15):   # vendor/partner pitch behind a corporate-looking lead
    first, last = random.choice(FIRST), random.choice(LAST)
    name, domain, industry, size = random.choice(COMPANIES)
    seniority = random.choice(["c_level", "vp_dir", "manager"])
    title = random.choice(TITLES[seniority])
    country, region = random.choice(GEO)
    email = f"{first}.{last}{lead_id}@{domain}".lower()
    add_row("trap", first, last, email, title, name, industry, size, country,
            random.choice(VENDOR_MESSAGES), "D",
            "Not a buyer: a vendor/partner pitch wearing a senior title.")

for _ in range(6):    # student research behind a plausible profile
    first, last = random.choice(FIRST), random.choice(LAST)
    name, domain, industry, size = random.choice(COMPANIES)
    title = random.choice(["Business Analyst", "Graduate Student"])
    country, region = random.choice(GEO)
    email = f"{first}.{last}{lead_id}@{domain}".lower()
    add_row("trap", first, last, email, title, name, industry, size, country,
            random.choice(STUDENT_MESSAGES), "D",
            "Research request, no purchase intent.")

for _ in range(6):    # urgent mid-market: message upgrades B to A
    first, last = random.choice(FIRST), random.choice(LAST)
    name, domain, industry, size = random.choice(
        [c for c in COMPANIES if 200 <= c[3] < 800])
    seniority = random.choice(["vp_dir", "manager"])
    title = random.choice(TITLES[seniority])
    country, region = random.choice(GEO[:6])
    email = f"{first}.{last}{lead_id}@{domain}".lower()
    msg = random.choice(URGENT_MIDMARKET_MESSAGES).format(size=size)
    add_row("trap", first, last, email, title, name, industry, size, country,
            msg, "A",
            "Mid-market on paper, but explicit timeline and mandate make it "
            "priority.")

# -------------------------------------------------------------- ambiguous 45
for _ in range(45):
    first, last = random.choice(FIRST), random.choice(LAST)
    name, domain, industry, size = random.choice(COMPANIES)
    seniority = random.choice(["vp_dir", "manager", "junior"])
    title = random.choice(TITLES[seniority])
    country, region = random.choice(GEO)
    email = f"{first}.{last}{lead_id}@{domain}".lower()
    base = rules_grade(seniority, size, industry, region, False)
    # tie-break rule: low-intent message downgrades A to B; between B and D
    # favor B (wasted call < lost buyer)
    truth = "B" if base == "A" else base
    add_row("ambiguous", first, last, email, title, name, industry, size,
            country, random.choice(AMBIGUOUS_MESSAGES), truth,
            "Borderline; tie-break favors the customer-facing outcome.")

random.shuffle(rows)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print(f"leads.csv: {len(rows)} rows "
      f"({sum(1 for r in rows if r['case_type'] == 'clean')} clean, "
      f"{sum(1 for r in rows if r['case_type'] == 'trap')} trap, "
      f"{sum(1 for r in rows if r['case_type'] == 'ambiguous')} ambiguous)")
