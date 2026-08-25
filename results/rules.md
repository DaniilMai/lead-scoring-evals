# Eval results — rules

**Accuracy: 80.3%** (95% CI 75.5%–84.4%) on 300 leads

| Case type | n | Accuracy | 95% CI |
|---|---|---|---|
| clean | 210 | 100.0% | 98.2%–100.0% |
| trap | 45 | 6.7% | 2.3%–17.9% |
| ambiguous | 45 | 62.2% | 47.6%–74.9% |

| Grade | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| A | 0.77 | 0.79 | 0.78 | 107 |
| B | 0.80 | 0.87 | 0.83 | 128 |
| D | 0.86 | 0.69 | 0.77 | 65 |

Confusion (rows = truth, columns = predicted):

| | A | B | D |
|---|---|---|---|
| **A** | 85 | 15 | 7 |
| **B** | 17 | 111 | 0 |
| **D** | 8 | 12 | 45 |

**Missed enterprise** (true A → predicted D): 7
**Delayed enterprise** (true A → predicted B): 15
**Wasted priority** (true D → predicted A): 8

## Sample misses

- `L0248` [trap] true **D** → predicted **B** — "I'm writing my master's thesis on AI in customer service. Could I get access for research "
- `L0224` [trap] true **A** → predicted **B** — "Writing from my personal address — I'm the Head of Support Operations at Beacon Financial."
- `L0286` [ambiguous] true **B** → predicted **A** — 'Comparing a few tools for a project later this year.'
- `L0288` [ambiguous] true **B** → predicted **A** — 'Comparing a few tools for a project later this year.'
- `L0296` [ambiguous] true **B** → predicted **A** — 'A colleague recommended you — not sure yet if this fits our roadmap.'
- `L0233` [trap] true **D** → predicted **B** — "We'd like to feature your product in our paid newsletter. Media-kit rates attached."
- `L0234` [trap] true **D** → predicted **A** — 'I run an agency helping SaaS companies with SEO. This is about a collaboration, not a purc'
- `L0241` [trap] true **D** → predicted **B** — 'Reseller inquiry: we distribute software in our region and want margin terms.'
