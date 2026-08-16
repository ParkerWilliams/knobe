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
moral-specific at all. Full pipeline built and verified end-to-end (with
`--mock`/`--engine fake`): dataset -> curation -> selection -> power check
-> elicitation. Curation blocked on `ANTHROPIC_API_KEY`, elicitation
blocked on GPU/`vllm` access; the power check needs only curation's
output, no additional resource.
See `nonmoral_pilot/README.md`.

## `moral_foundations_pilot/`

Not yet built — design doc at `docs/moral_foundations_extension/
MORAL_FOUNDATIONS_PILOT_PLAN.md`. Adds loyalty/authority/fairness/purity
variants to (mostly) the same 40 storylines, plus a freshly-templated
harm-control. Tests whether the asymmetry generalizes beyond the
harm/welfare side-effect structure specifically, assuming
`nonmoral_pilot/` establishes the effect is moral-specific in the first
place. Will live in this directory once built.
