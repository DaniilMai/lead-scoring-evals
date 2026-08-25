#!/usr/bin/env python3
"""Run a scorer over the labeled dataset and write a results report.

  python evals/run_eval.py --scorer rules
  python evals/run_eval.py --scorer llm --model claude-opus-5
  python evals/run_eval.py --scorer rules --check   # CI: compare to committed

The scorer never sees case_type, true_grade, or truth_rationale — the
harness strips them. LLM runs record measured tokens and latency; cost per
1000 leads is computed from measured usage at list prices, not estimated.
"""

import argparse
import csv
import json
import os
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from evals.metrics import GRADES, summarize          # noqa: E402
from scoring import rules as rules_scorer            # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
DATA = os.path.join(ROOT, "data", "leads.csv")
RESULTS = os.path.join(ROOT, "results")

# The no-peeking guarantee lives HERE, in the harness — scorers only ever
# receive these fields, so a scorer cannot cheat even if it wants to.
VISIBLE_FIELDS = ("first_name", "last_name", "email", "title", "company",
                  "industry", "company_size", "country", "form_message")


def visible(lead):
    return {k: lead[k] for k in VISIBLE_FIELDS}


def load_leads():
    with open(DATA) as f:
        return list(csv.DictReader(f))


def run_rules(leads):
    rows = []
    for lead in leads:
        pred = rules_scorer.score_lead(visible(lead))
        rows.append({**lead, "predicted": pred["grade"],
                     "pred_rationale": pred["rationale"]})
    return rows, {}


def run_llm(leads, model, workers):
    from scoring import llm as llm_scorer
    client = llm_scorer.make_client()

    def one(lead):
        pred = llm_scorer.score_lead(client, visible(lead), model=model)
        return {**lead, "predicted": pred.get("grade"),
                "pred_rationale": pred.get("rationale", pred.get("error", "")),
                "input_tokens": pred.get("input_tokens"),
                "output_tokens": pred.get("output_tokens"),
                "latency_s": pred.get("latency_s")}

    with ThreadPoolExecutor(max_workers=workers) as pool:
        rows = list(pool.map(one, leads))

    ok = [r for r in rows if r.get("latency_s") is not None]
    in_price, out_price = llm_scorer.PRICES.get(model, (None, None))
    extras = {}
    if ok:
        mean_in = statistics.mean(r["input_tokens"] for r in ok)
        mean_out = statistics.mean(r["output_tokens"] for r in ok)
        lat = sorted(r["latency_s"] for r in ok)
        extras = {
            "model": model,
            "mean_input_tokens": round(mean_in, 1),
            "mean_output_tokens": round(mean_out, 1),
            "latency_p50_s": round(lat[len(lat) // 2], 2),
            "latency_p95_s": round(lat[int(len(lat) * 0.95) - 1], 2),
        }
        if in_price is not None:
            # computed over successful calls only — failed calls are counted
            # as wrong in accuracy and reported separately
            extras["cost_per_1000_leads_usd"] = round(
                (mean_in * in_price + mean_out * out_price) / 1e6 * 1000, 2)
            extras["cost_per_1000_leads_batch_usd"] = round(
                extras["cost_per_1000_leads_usd"] / 2, 2)  # Batch API: 50% off
    return rows, extras


def render_markdown(name, summary, extras, worst):
    lines = [f"# Eval results — {name}", ""]
    if extras:
        lines += [f"Model: `{extras['model']}` · "
                  f"mean tokens {extras['mean_input_tokens']:.0f} in / "
                  f"{extras['mean_output_tokens']:.0f} out · "
                  f"latency p50 {extras['latency_p50_s']}s, "
                  f"p95 {extras['latency_p95_s']}s · "
                  f"**${extras.get('cost_per_1000_leads_usd', '?')} per 1000 "
                  f"leads** (${extras.get('cost_per_1000_leads_batch_usd', '?')} "
                  f"via Batch API)", ""]
    ci = summary["accuracy_ci95"]
    lines += [f"**Accuracy: {summary['accuracy']:.1%}** "
              f"(95% CI {ci[0]:.1%}–{ci[1]:.1%}) on {summary['n']} leads", ""]
    if summary["failed_calls"]:
        lines += [f"⚠️ Failed calls: {summary['failed_calls']} "
                  "(counted as wrong; excluded from token/cost averages)", ""]
    lines += ["| Case type | n | Accuracy | 95% CI |", "|---|---|---|---|"]
    for case, s in summary["accuracy_by_case"].items():
        lines.append(f"| {case} | {s['n']} | {s['accuracy']:.1%} "
                     f"| {s['ci95'][0]:.1%}–{s['ci95'][1]:.1%} |")
    lines += ["", "| Grade | Precision | Recall | F1 | Support |",
              "|---|---|---|---|---|"]
    for g, s in summary["per_grade"].items():
        lines.append(f"| {g} | {s['precision']:.2f} | {s['recall']:.2f} "
                     f"| {s['f1']:.2f} | {s['support']} |")
    lines += ["", "Confusion (rows = truth, columns = predicted):", "",
              "| | A | B | D |", "|---|---|---|---|"]
    for t in GRADES:
        c = summary["confusion"][t]
        lines.append(f"| **{t}** | {c['A']} | {c['B']} | {c['D']} |")
    lines += ["",
              f"**Missed enterprise** (true A → predicted D): "
              f"{summary['missed_enterprise']}",
              f"**Delayed enterprise** (true A → predicted B): "
              f"{summary['delayed_enterprise']}",
              f"**Wasted priority** (true D → predicted A): "
              f"{summary['wasted_priority']}", ""]
    if worst:
        lines += ["## Sample misses", ""]
        for r in worst[:8]:
            lines.append(f"- `{r['lead_id']}` [{r['case_type']}] "
                         f"true **{r['true_grade']}** → predicted "
                         f"**{r['predicted']}** — {r['form_message'][:90]!r}")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scorer", choices=["rules", "llm"], required=True)
    ap.add_argument("--model", default="claude-opus-5")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--check", action="store_true",
                    help="compare against committed results (CI)")
    args = ap.parse_args()

    leads = load_leads()
    if args.scorer == "rules":
        rows, extras = run_rules(leads)
        name = "rules"
    else:
        if not (os.environ.get("ANTHROPIC_API_KEY")
                or os.environ.get("ANTHROPIC_AUTH_TOKEN")
                or os.path.exists(os.path.expanduser("~/.config/anthropic"))):
            sys.exit("error: no Anthropic credentials found — export "
                     "ANTHROPIC_API_KEY (or run `ant auth login`) before "
                     "running the LLM scorer. The rules scorer needs no key.")
        rows, extras = run_llm(leads, args.model, args.workers)
        name = f"llm-{args.model}"

    summary = summarize(rows)
    worst = [r for r in rows if r["predicted"] != r["true_grade"]]
    payload = {"scorer": name, **extras, "summary": summary}

    os.makedirs(RESULTS, exist_ok=True)
    json_path = os.path.join(RESULTS, f"{name}.json")

    if args.check:
        # invariant, not just equality: the clean segment is 100% by
        # construction — anything less means the port drifted from the
        # generator's semantics, even if someone committed matching results
        if summary["accuracy_by_case"]["clean"]["accuracy"] != 1.0:
            print("INVARIANT BROKEN: clean segment must score 100% by "
                  "construction — the rules port no longer matches the "
                  "dataset generator's semantics")
            sys.exit(1)
        with open(json_path) as f:
            committed = json.load(f)
        if committed["summary"] != summary:
            print(f"MISMATCH: computed summary differs from {json_path}")
            sys.exit(1)
        print(f"OK: results match {json_path} and invariants hold")
        return

    with open(json_path, "w") as f:
        json.dump(payload, f, indent=2)
    md_path = os.path.join(RESULTS, f"{name}.md")
    with open(md_path, "w") as f:
        f.write(render_markdown(name, summary, extras, worst))
    print(f"{name}: accuracy {summary['accuracy']:.1%} "
          f"(clean {summary['accuracy_by_case']['clean']['accuracy']:.1%}, "
          f"trap {summary['accuracy_by_case']['trap']['accuracy']:.1%}, "
          f"ambiguous {summary['accuracy_by_case']['ambiguous']['accuracy']:.1%})"
          + (f" · ${extras.get('cost_per_1000_leads_usd')}/1000 leads"
             if extras.get("cost_per_1000_leads_usd") else ""))
    print(f"wrote {json_path} and {md_path}")


if __name__ == "__main__":
    main()
