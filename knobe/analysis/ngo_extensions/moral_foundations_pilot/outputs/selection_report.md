# Moral-foundations pilot: post-curation selection report

moral_min=6, nonmoral_max=4 (configs/curation.yaml). 126/152 items selected -> `mf_pilot_dataset_selected.csv`.

**Selection rule: PAIR-level, keyed on the bad member** (see `select_items`'s docstring for the full rationale -- the design doc's per-item rule was revised 2026-08-19 after real curation data showed the section-5 questions only measure the violation pole, which would have deleted the good arm; flagged for collaborator review). Per-item diagnostics below are unchanged and still worth reading.

**28 harm-control item(s) failed to read as harm** through this project's reviewer pipeline (freshly-templated wording, so not guaranteed by Ngo's originals): ['harm-01-good', 'harm-02-good', 'harm-04-good', 'harm-05-good', 'harm-08-good', 'harm-09-good', 'harm-10-good', 'harm-11-good', 'harm-12-good', 'harm-13-good', 'harm-15-good', 'harm-16-good', 'harm-17-good', 'harm-18-good', 'harm-19-good', 'harm-21-good', 'harm-23-good', 'harm-24-good', 'harm-25-good', 'harm-26-good', 'harm-27-good', 'harm-31-good', 'harm-32-good', 'harm-33-good', 'harm-35-good', 'harm-38-good', 'harm-39-good', 'harm-40-good']

Foundation-item failures by reason (design doc section 5 predicts harm contamination is the likelier failure mode than a weak foundation signal):

- **harm contamination** (harm_relevance > 4): 8 item(s) ['loyalty-05-good', 'authority-17-bad', 'authority-17-good', 'authority-40-bad', 'fairness-05-good', 'fairness-17-bad', 'fairness-18-bad', 'fairness-35-bad']
- **weak foundation signal** (foundation_relevance < 6, harm ok): 28 item(s) ['loyalty-01-good', 'loyalty-10-good', 'loyalty-13-good', 'loyalty-15-good', 'loyalty-16-good', 'loyalty-19-good', 'loyalty-25-good', 'loyalty-32-good', 'authority-04-good', 'authority-18-good', 'authority-21-bad', 'authority-21-good', 'authority-23-good', 'authority-38-bad', 'fairness-02-good', 'fairness-04-good', 'fairness-08-good', 'fairness-18-good', 'fairness-19-good', 'fairness-26-good', 'fairness-35-good', 'fairness-38-bad', 'fairness-38-good', 'purity-31-good', 'purity-33-good', 'purity-101-good', 'purity-102-good', 'purity-104-good']

## Surviving cluster counts (what power_check.py projects from)

| condition | items passing | distinct storylines (pair_ids) |
|---|---|---|
| harm_control | 60 | 30 |
| loyalty | 20 | 10 |
| authority | 18 | 9 |
| fairness | 16 | 8 |
| purity | 12 | 6 *(smaller by design -- reported as tentative)* |
| non-harm pooled (primary contrast) | 66 | 26 |

**8 storyline(s) with NO surviving non-harm item at all: [5, 17, 21, 30, 35, 38, 39, 40]** -- these contribute nothing to the pooled non-harm arm; flagged rather than silently dropped.
