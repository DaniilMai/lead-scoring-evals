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

All four scorers, same dataset, same blindfold. LLM rows were produced by the
CI eval job — measured tokens, measured latency, list prices.

| Scorer | Overall (95% CI) | Clean | Trap | Ambiguous | Missed¹ | Delayed² | Wasted³ | $/1000⁴ | p50 |
|---|---|---|---|---|---|---|---|---|---|
| Rules baseline | **80.3%** (75.5–84.4%) | **100%** | 6.7% | 62.2% | 7 | 15 | 8 | $0 | ~0 |
| claude-haiku-4-5 | 50.7% (45.0–56.3%) | 40.5% | 73.3% | 75.6% | 8 | 74 | 1 | $1.30 | 2.2s |
| claude-sonnet-5 | 48.7% (43.1–54.3%) | 36.7% | 71.1% | 82.2% | **0** | 95 | **0** | $7.91 | 5.2s |
| claude-opus-5 | 54.7% (49.0–60.2%) | 43.3% | **75.6%** | **86.7%** | **0** | 85 | 1 | $12.13 | 5.3s |

¹ true A → predicted D: a priority buyer sent to the thank-you page.
² true A → predicted B: a priority buyer parked in the standard queue —
cheaper per case than a full miss, far more frequent.
³ true D → predicted A: junk occupying the priority calendar.
⁴ list prices, successful calls; the Batch API halves it (haiku $0.65,
sonnet $3.96, opus $6.07).

### What the numbers actually say

1. **The failure profiles are opposites.** Rules: perfect on structured
   fields, 6.7% on traps — every vendor pitch with a senior title got a
   calendar. LLMs: ~11× better on traps (71–76%) and better on ambiguous
   (up to 86.7%), with **zero missed-enterprise errors** on sonnet and opus —
   but they tank the clean segment (37–43%) by refusing to grade A on
   firmographics alone, parking 74–95 priority buyers in the standard queue.
   Neither scorer should own the whole pipeline; the honest architecture is
   the hybrid: rules for structured fields, LLM for the message.
2. **The eval caught a policy-spec bug, not just model behavior.** The
   written playbook says "torn between A and B with no urgency evidence,
   choose B" — and the models obey it *everywhere*, including cases the
   numeric formula scores as a confident 75+ A. The words and the numbers
   disagree about what "strong fit without message signal" means, and no one
   notices that gap until a harness makes both grade the same 300 leads.
3. **For message-reading, the cheap model is enough.** Haiku's trap accuracy
   (73.3%) is within the error bars of opus (75.6%) at a ninth of the cost
   and half the latency. The expensive models buy fewer catastrophic errors
   (0 missed enterprise), not better text comprehension.

Full reports per scorer: [results/rules.md](results/rules.md),
[llm-claude-haiku-4-5.md](results/llm-claude-haiku-4-5.md),
[llm-claude-sonnet-5.md](results/llm-claude-sonnet-5.md),
[llm-claude-opus-5.md](results/llm-claude-opus-5.md).

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
