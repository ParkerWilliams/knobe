# Severity question wording check (Phase 0 of the severity pilot)

See `docs/SEVERITY_PILOT_PLAN.md` Phase 0 for the full rationale and
decision tree. Short version: the curation severity question asks *"How
severe or **significant** is this outcome?"* — "significant" may be
leaking moral/social importance into what's supposed to be a magnitude
measure, which would mean part of the r=.885 severity/moral-sign
correlation (`docs/SEVERITY_MORALIZATION_BACKGROUND.md`) is a measurement
artifact, not a fact about the stimuli.

## Status: scripts ready, not yet run

This environment has no `ANTHROPIC_API_KEY`. Whoever has the same curation-
reviewer access already used for `knobe curate run` needs to run:

```
.venv/bin/python analysis/severity_wording_check/run_reworded_severity.py \
    --reviewer-model claude-sonnet-5
```

(~420 calls against the existing v1.1 vignette scenarios, one new question,
no new authoring — cheap, matches the existing curation cost profile). Then:

```
.venv/bin/python analysis/severity_wording_check/analyze_reworded_severity.py
```

## Why this isn't just editing `constants.py`

`CURATION_QUESTIONS` is a frozen instrument (master spec §7). The reworded
question lives only in `run_reworded_severity.py`; results go to their own
`outputs/severity_reworded_raw.jsonl`, never `curated_v1.1.csv`. If this
experiment finds the reworded question is meaningfully better, adopting it
for real goes through the project's established reword-validation track
(`docs/V1_1_WORKFLOW.md`'s "Type-1 curation-question reword"), as a new
versioned question — not a silent in-place edit.

## What "success" looks like

See `docs/SEVERITY_PILOT_PLAN.md` Phase 0's three-outcome decision tree.
The one-line version: if `corr(reworded_severity, sign)` within moral items
drops well below .885 and the RQ1a severity-adjusted interaction's SE
shrinks meaningfully, the current severity measure was partly a wording
artifact — worth knowing before spending a day on Phase 1's vignette
escalation.
