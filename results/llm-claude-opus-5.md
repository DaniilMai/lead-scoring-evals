# Eval results — llm-claude-opus-5

Model: `claude-opus-5` · mean tokens 941 in / 297 out · latency p50 5.33s, p95 8.81s · **$12.13 per 1000 leads** ($6.07 via Batch API)

**Accuracy: 54.7%** (95% CI 49.0%–60.2%) on 300 leads

| Case type | n | Accuracy | 95% CI |
|---|---|---|---|
| clean | 210 | 43.3% | 36.8%–50.1% |
| trap | 45 | 75.6% | 61.3%–85.8% |
| ambiguous | 45 | 86.7% | 73.8%–93.7% |

| Grade | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| A | 0.92 | 0.21 | 0.34 | 107 |
| B | 0.48 | 0.88 | 0.62 | 128 |
| D | 0.67 | 0.46 | 0.55 | 65 |

Confusion (rows = truth, columns = predicted):

| | A | B | D |
|---|---|---|---|
| **A** | 22 | 85 | 0 |
| **B** | 1 | 112 | 15 |
| **D** | 1 | 34 | 30 |

**Missed enterprise** (true A → predicted D): 0
**Delayed enterprise** (true A → predicted B): 85
**Wasted priority** (true D → predicted A): 1

## Sample misses

- `L0177` [clean] true **D** → predicted **B** — 'Saw your webinar, want to learn more.'
- `L0141` [clean] true **A** → predicted **B** — ''
- `L0187` [clean] true **A** → predicted **B** — 'Saw your webinar, want to learn more.'
- `L0101` [clean] true **A** → predicted **B** — 'Interested in a demo for our support team.'
- `L0161` [clean] true **A** → predicted **B** — 'Interested in a demo for our support team.'
- `L0261` [ambiguous] true **B** → predicted **D** — 'Curious about pricing.'
- `L0173` [clean] true **B** → predicted **D** — ''
- `L0077` [clean] true **D** → predicted **B** — 'Evaluating options for customer-service automation.'
