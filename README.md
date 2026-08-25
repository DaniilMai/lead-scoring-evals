# Lead Scoring Evals

[![CI](https://github.com/DaniilMai/lead-scoring-evals/actions/workflows/ci.yml/badge.svg)](https://github.com/DaniilMai/lead-scoring-evals/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)

Should an LLM grade your inbound leads? Everyone has an opinion; this repo has
a harness. A rules baseline and an LLM scorer graded on the same labeled
dataset — accuracy, precision/recall, confusion matrix, the two errors that
cost real money, and dollars per 1000 leads. Measured, not vibes-checked.

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python evals/run_eval.py --scorer rules                    # free, instant
.venv/bin/python evals/run_eval.py --scorer llm --model claude-opus-5  # needs ANTHROPIC_API_KEY
```

## The experiment

**The rules baseline** is a faithful port of a production demo-form grading
model: company size (0–40) + title seniority (0–30) + industry fit (0–15) +
geography (0–15); A ≥ 75 → priority calendar, B ≥ 45 → standard calendar,
D → thank-you page. It grades structured fields only — it cannot read the
free-text message. That blindness is the experiment.

**The LLM scorer** gets the same lead plus the message, and the same playbook
a human reviewer uses (vendors and thesis requests are not buyers; a personal
email doesn't disqualify a credible message; urgency with a mandate upgrades).
Structured output, validated grade enum, measured tokens and latency.

**The dataset** ([data/leads.csv](data/leads.csv), 300 leads, deterministic
generator): three segments with ground-truth grades.

| Segment | n | What it tests |
|---|---|---|
| `clean` | 210 | Structured fields tell the whole story — the rules' home turf |
| `trap` | 45 | The message contradicts the fields: enterprise buyers behind personal emails, vendor pitches behind senior titles, students behind corporate domains, urgency that upgrades a mid-market lead |
| `ambiguous` | 45 | Genuinely borderline; ground truth follows a documented tie-break (torn between B and D → B: a wasted call costs less than a lost buyer) |

Scorers never see `case_type`, `true_grade`, or `truth_rationale` — the
harness strips them.

## Results

| Scorer | Overall (95% CI) | Clean | Trap | Ambiguous | Missed¹ | Delayed² | Wasted³ | $/1000 leads |
|---|---|---|---|---|---|---|---|---|
| Rules baseline | **80.3%** (75.5–84.4%) | 100% | 6.7% | 62.2% | 7 | 15 | 8 | $0 |
| LLM — row lands from the first [CI eval run](.github/workflows/ci.yml) | — | — | — | — | — | — | — | — |

¹ true A → predicted D: a priority buyer sent to the thank-you page.
² true A → predicted B: a priority buyer parked in the standard queue —
cheaper per case than a full miss, far more frequent.
³ true D → predicted A: junk occupying the priority calendar.

The baseline's shape is the whole story so far: **perfect on clean, 6.7% on
traps**. Of 24 hidden priority buyers, 7 bounced off the thank-you page and
15 were demoted to the standard queue — the dominant failure is a *slower*
enterprise funnel, not just a lost one. Meanwhile all 8 wasted-priority slots
went to vendor pitches wearing senior titles. If the LLM earns its cost
anywhere, it's the trap column — and whether it does is a number, not an
argument.

Full reports per scorer: [results/rules.md](results/rules.md), plus one
`results/llm-<model>.md` per model run.

## Reading the numbers honestly

- **The eval is circular by design.** Ground truth is generated from the same
  written playbook the LLM receives in its system prompt — because that is
  exactly what a production LLM grader gets. So this measures
  *policy-execution fidelity* (can the model apply a documented policy to
  messy free text?), not judgment discovery. A perfect score means "faithful
  executor", not "better policy than yours".
- **The trap share is planted.** I decided 15% of the dataset contradicts its
  structured fields. Real inbound has its own (unknown, lower) trap rate — so
  the per-segment columns are the signal, and the overall column is a
  weighted opinion. Judge scorers segment by segment.
- **A keyword rules-v2 would catch many of these traps for free.** The trap
  messages come from a handful of templates, and templated text is exactly
  where keyword matching wins ("thesis", "reseller", "partnership" → D).
  That's the honest next baseline — and the reason synthetic results cap
  out: real messages defeat keyword lists, which is where an LLM starts
  earning its fee.
- **Error bars before conclusions.** Segment n is 45, so a single-run trap
  accuracy carries a ±13pp interval — deltas between two scorers smaller
  than the CI are noise, not findings. LLM runs are additionally
  nondeterministic: repeat before concluding.
- **Cost is measured, not estimated**: once an LLM run exists, its cost per
  1000 leads comes from measured token usage × list prices, with the Batch
  API discount (50%) alongside — lead grading is rarely latency-critical, so
  batch pricing is the honest production number.

## What broke

- **`"Director"` contains `"cto"`.** The first version of the title parser
  used substring matching and quietly promoted every director to C-level —
  caught because the clean segment, which must score 100% by construction,
  scored 98.6%. Whole-word matching fixed it; the invariant (clean = 100%)
  now guards the port in CI.

## Layout

```
data/leads.csv           labeled dataset (generated, committed, deterministic)
scripts/generate_dataset.py
scoring/rules.py         the baseline — structured fields only
scoring/llm.py           the challenger — same playbook + the message
evals/run_eval.py        harness; --check mode pins results in CI
evals/metrics.py         hand-rolled metrics incl. business-weighted errors
results/                 committed reports, one per scorer/model
```

CI regenerates the dataset (byte-identical or fail), reruns the rules eval,
and compares against the committed results. The LLM eval runs as a manually
triggered job (`Actions → llm-eval`) with `ANTHROPIC_API_KEY` as a repo
secret, and commits its report back to `results/`.
