# Eval results — llm-claude-haiku-4-5

Model: `claude-haiku-4-5` · mean tokens 687 in / 124 out · latency p50 2.19s, p95 2.79s · **$1.3 per 1000 leads** ($0.65 via Batch API)

**Accuracy: 50.7%** (95% CI 45.0%–56.3%) on 300 leads

| Case type | n | Accuracy | 95% CI |
|---|---|---|---|
| clean | 210 | 40.5% | 34.1%–47.2% |
| trap | 45 | 73.3% | 59.0%–84.0% |
| ambiguous | 45 | 75.6% | 61.3%–85.8% |

| Grade | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| A | 0.86 | 0.23 | 0.37 | 107 |
| B | 0.47 | 0.64 | 0.54 | 128 |
| D | 0.47 | 0.69 | 0.56 | 65 |

Confusion (rows = truth, columns = predicted):

| | A | B | D |
|---|---|---|---|
| **A** | 25 | 74 | 8 |
| **B** | 3 | 82 | 43 |
| **D** | 1 | 19 | 45 |

**Missed enterprise** (true A → predicted D): 8
**Delayed enterprise** (true A → predicted B): 74
**Wasted priority** (true D → predicted A): 1

## Sample misses

- `L0082` [clean] true **B** → predicted **D** — ''
- `L0098` [clean] true **B** → predicted **D** — ''
- `L0141` [clean] true **A** → predicted **D** — ''
- `L0187` [clean] true **A** → predicted **B** — 'Saw your webinar, want to learn more.'
- `L0101` [clean] true **A** → predicted **B** — 'Interested in a demo for our support team.'
- `L0161` [clean] true **A** → predicted **B** — 'Interested in a demo for our support team.'
- `L0261` [ambiguous] true **B** → predicted **D** — 'Curious about pricing.'
- `L0281` [ambiguous] true **B** → predicted **D** — "Just exploring what's out there for now."
