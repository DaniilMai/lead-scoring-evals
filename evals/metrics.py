"""Hand-rolled metrics — no sklearn dependency for arithmetic we can read.

Beyond the standard trio (accuracy, per-grade precision/recall/F1, confusion
matrix), the report tracks the two errors that actually cost money:

  missed_enterprise   true A predicted D — a priority buyer sent to the
                      thank-you page. The most expensive single mistake.
  delayed_enterprise  true A predicted B — a priority buyer parked in the
                      standard queue. Cheaper per case than a full miss,
                      but far more frequent: slower first touch at exactly
                      the accounts where speed matters.
  wasted_priority     true D predicted A — junk occupying the priority
                      calendar and an AE's morning.
"""

GRADES = ["A", "B", "D"]


def wilson_ci(k, n, z=1.96):
    """95% Wilson interval — segment n is small (45), so every accuracy
    needs error bars before anyone compares two scorers with it."""
    if n == 0:
        return [0.0, 0.0]
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / denom
    # list, not tuple: the summary round-trips through JSON in --check mode
    return [round(max(0.0, center - half), 3), round(min(1.0, center + half), 3)]


def confusion(rows):
    m = {t: {p: 0 for p in GRADES + ["none"]} for t in GRADES}
    for r in rows:
        m[r["true_grade"]][r["predicted"] or "none"] += 1
    return m


def per_grade(rows):
    out = {}
    for g in GRADES:
        tp = sum(1 for r in rows if r["true_grade"] == g and r["predicted"] == g)
        fp = sum(1 for r in rows if r["true_grade"] != g and r["predicted"] == g)
        fn = sum(1 for r in rows if r["true_grade"] == g and r["predicted"] != g)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = (2 * precision * recall / (precision + recall)
              if precision + recall else 0.0)
        out[g] = {"precision": round(precision, 3),
                  "recall": round(recall, 3),
                  "f1": round(f1, 3),
                  "support": tp + fn}
    return out


def summarize(rows):
    n = len(rows)
    correct = sum(1 for r in rows if r["predicted"] == r["true_grade"])
    by_case = {}
    for case in ("clean", "trap", "ambiguous"):
        sub = [r for r in rows if r["case_type"] == case]
        if sub:
            k = sum(1 for r in sub if r["predicted"] == r["true_grade"])
            by_case[case] = {
                "n": len(sub),
                "accuracy": round(k / len(sub), 3),
                "ci95": wilson_ci(k, len(sub)),
            }
    return {
        "n": n,
        "accuracy": round(correct / n, 3),
        "accuracy_ci95": wilson_ci(correct, n),
        "accuracy_by_case": by_case,
        "per_grade": per_grade(rows),
        "confusion": confusion(rows),
        "missed_enterprise": sum(1 for r in rows
                                 if r["true_grade"] == "A"
                                 and r["predicted"] == "D"),
        "delayed_enterprise": sum(1 for r in rows
                                  if r["true_grade"] == "A"
                                  and r["predicted"] == "B"),
        "wasted_priority": sum(1 for r in rows
                               if r["true_grade"] == "D"
                               and r["predicted"] == "A"),
        "failed_calls": sum(1 for r in rows if r["predicted"] is None),
    }
