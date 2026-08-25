# Eval results — llm-claude-sonnet-5

Model: `claude-sonnet-5` · mean tokens 941 in / 340 out · latency p50 5.24s, p95 8.11s · **$7.91 per 1000 leads** ($3.96 via Batch API)

**Accuracy: 48.7%** (95% CI 43.1%–54.3%) on 300 leads

| Case type | n | Accuracy | 95% CI |
|---|---|---|---|
| clean | 210 | 36.7% | 30.4%–43.4% |
| trap | 45 | 71.1% | 56.6%–82.3% |
| ambiguous | 45 | 82.2% | 68.7%–90.7% |

| Grade | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| A | 1.00 | 0.11 | 0.20 | 107 |
| B | 0.44 | 0.80 | 0.57 | 128 |
| D | 0.55 | 0.49 | 0.52 | 65 |

Confusion (rows = truth, columns = predicted):

| | A | B | D |
|---|---|---|---|
| **A** | 12 | 95 | 0 |
| **B** | 0 | 102 | 26 |
| **D** | 0 | 33 | 32 |

**Missed enterprise** (true A → predicted D): 0
**Delayed enterprise** (true A → predicted B): 95
**Wasted priority** (true D → predicted A): 0

## Sample misses

- `L0177` [clean] true **D** → predicted **B** — 'Saw your webinar, want to learn more.'
- `L0141` [clean] true **A** → predicted **B** — ''
- `L0187` [clean] true **A** → predicted **B** — 'Saw your webinar, want to learn more.'
- `L0101` [clean] true **A** → predicted **B** — 'Interested in a demo for our support team.'
- `L0161` [clean] true **A** → predicted **B** — 'Interested in a demo for our support team.'
- `L0261` [ambiguous] true **B** → predicted **D** — 'Curious about pricing.'
- `L0173` [clean] true **B** → predicted **D** — ''
- `L0077` [clean] true **D** → predicted **B** — 'Evaluating options for customer-service automation.'
