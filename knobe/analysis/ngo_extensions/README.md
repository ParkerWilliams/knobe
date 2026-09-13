# Ngo extensions: targeted, minimal additions to Raimondi's own stimulus set

Two independent pilots that share one strategy: instead of growing this
project's own decomposed factorial dataset further, or fixing the RQ1a
severity confound within this project's own taxonomy (`docs/
severity_confound/`, currently set aside), **step back to Raimondi et
al.'s (arXiv:2510.12229) original 80 Ngo-derived scenarios and add the
smallest content change needed to test one specific question directly on
their own materials.** Keeping additions minimal and structurally close
to the original is what keeps results comparable to Raimondi's own
reported numbers — the same property that let
`docs/rq1_findings/RAIMONDI_REPLICATION_GAPS.md` catch a real pretrained
scoring artifact that a comparison against this project's larger, more
decomposed dataset wouldn't have surfaced.

The two pilots are independent of each other (different question,
different content, run and analyzed separately) — grouped here only
because they're the same kind of move against the same base material.

## `nonmoral_pilot/`

Adds a nonmoral third variant (prudential, with a procedural fallback) to
each of Ngo's 40 harm/help pairs. Tests whether the classic asymmetry is
moral-specific at all. **Run end to end**: real curation 2026-08-19, real
elicitation published 2026-08-22 (`results_dist/results_pilot_nonmoral_all.jsonl.gz`,
88,200 responses across three question types).

**Answer, as of 2026-09-13: no.** Under `parsed_rating` scoring no family
shows a significant moral-vs-nonmoral interaction. The earlier
moral-specific result was a logit-fallback scoring artifact -- see
`docs/rq1_findings/ALIGNMENT_DISCUSSION_ngo_pilots.md`'s correction note.
See `nonmoral_pilot/README.md`.

## `moral_foundations_pilot/`

Built 2026-08-19 from the design doc at `docs/moral_foundations_extension/
MORAL_FOUNDATIONS_PILOT_PLAN.md`. Adds loyalty/authority/fairness/purity
variants to a 30-storyline core of the same 40 storylines, plus a
freshly-templated 4-clause harm-control. Tests whether the asymmetry
generalizes beyond the harm/welfare side-effect structure specifically.
(The original framing made this conditional on the sibling pilot
establishing moral-specificity first. That premise did not survive -- the
question stands on its own.) **Run end to end**: real curation 2026-08-19,
real elicitation published 2026-08-22
(`results_dist/results_pilot_moral_foundations_all.jsonl.gz`, 18,900
responses, intentionality only).
See `moral_foundations_pilot/README.md` and its `HANDOFF.md`.

## Cross-pilot scripts

Run against both pilots' committed tables; all reuse
`rq1_v1_1_robustness/lib.py` rather than reimplementing inference.

| script | what it does |
|---|---|
| `measurement_selection_audit.py` | Parse rate and `ev_rating`/`parsed_rating` agreement per (model, question); authored-vs-surviving item counts per cell. The audit that showed the scoring artifact is question-shaped |
| `holm_correct_pilots.py` | Holm correction within (family, tuning, question). `--score {ev,parsed}` |
| `tuning_contrast_wcb.py` | Formal `sign_c x tuning_c` interaction -- whether instruction tuning changes the asymmetry |
| `blame_praise_swing.py` | Blame-vs-praise swing on a common scale, raw cell means, and the moral-vs-nonmoral gap split by sign |
| `stakes_gradient_check.py` | Whether the good-cell domain effect tracks stakes or moral domain, using the prudential/procedural split |
| `equivalence_bounds.py` | MDE and TOST-style bounds, so arm-vs-arm nulls carry evidential weight |

Claim-to-table mapping for all of these is in
`docs/submission_plan/CLAIMS.md`.
