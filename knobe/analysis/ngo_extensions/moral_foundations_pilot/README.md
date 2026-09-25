# Moral-foundations pilot: does the Knobe effect generalize beyond harm?

**Running this yourself? See `HANDOFF.md` for the exact command sequence.**
The rest of this file is design rationale, not a runbook.

Implements `docs/moral_foundations_extension/MORAL_FOUNDATIONS_PILOT_PLAN.md`
(design agreed 2026-08-17; built 2026-08-19). Tests whether the classic
Knobe asymmetry (bad>good intentionality for a foreseen side effect) holds
for **non-harm-structured moral violations** -- loyalty, authority,
fairness-without-harm, purity -- or is specific to the harm/welfare
structure Raimondi et al. (arXiv:2510.12229)'s paradigm (and this project's
own "moral" category) is built on. Sibling to `../nonmoral_pilot/` (same
strategy: minimal additions to Ngo's own 40 storylines; different axis --
that pilot removes the moral stake entirely, this one swaps its normative
ground).

## Design (from the plan doc, decisions locked there)

- **4-clause template everywhere, including the harm-control** (background
  fact establishing the norm/stake -> unrelated instrumental goal -> stated
  indifference -> foreseen side-effect violation). The harm-control is
  freshly written, NOT Ngo's 3-clause original, so clause count/complexity
  is not a confound between harm and non-harm conditions.
- **Primary contrast**: harm-control vs. all four non-harm foundations
  pooled. **Secondary, exploratory**: each foundation alone, with honest
  per-foundation cluster counts. **Out of scope**: a purpose-built
  equally-powered four-foundation comparison (design doc section 2).
  q_blame/q_praise were originally out of scope too; added 2026-09-25 as an
  opt-in extension (`elicit.py --questions q_blame,q_praise`, per
  SUBMISSION_GAMEPLAN.md section 5 item 6) -- see `build_dataset.py`.
- **Sourcing**: 30 of Ngo's 40 storylines as shared scaffolds (the 3
  unadaptable pairs -- bombing/terrorism/cult -- skipped as in the sibling
  pilot, plus 7 more that didn't hold up under drafting). Loyalty/
  authority/fairness each draw the 13 core storylines they bend into
  naturally; purity (the acknowledged hard case) gets 3 Ngo-derived
  storylines plus 4 purpose-written ones (food/ritual/bodily/relic
  domains), flagged via the dataset's `source` column rather than
  pretended-equivalent. Purity's smaller N is an explicit design decision;
  the pooled primary contrast is what carries the main claim.

## Files

- `harm_control_variants.py` -- 30 freshly-templated 4-clause harm pairs.
- `loyalty_variants.py` / `authority_variants.py` / `fairness_variants.py`
  -- 13 pairs each. Fairness is the delicate one: its inequities are
  strictly non-material (slots, votes, turn order, credit, process voice),
  since unequal money/food/care would trip the harm-relevance gate.
- `purity_variants.py` -- 7 pairs (3 Ngo-derived + 4 purpose-written,
  `PURPOSE_WRITTEN_PAIR_IDS`).
- `build_dataset.py` -- merges all five into `outputs/mf_pilot_dataset.csv`
  (152 rows; committed -- pure text, no API needed).
- `curate_foundation_relevance.py` -- the two-question manipulation check
  (design doc section 5): `harm_relevance` for every item, plus the
  matching foundation-relevance question ("Setting aside any harm to
  someone's welfare...") for non-harm items. `--select` builds
  `outputs/mf_pilot_dataset_selected.csv` + `outputs/selection_report.md`.
- `power_check.py` -- MDE projection at the REAL post-curation cluster
  counts (same 09/15 machinery as the sibling pilot), for the primary arms
  under both an "effect generalizes" (moral-only) and an "it behaves
  nonmorally" (subdomain) benchmark, plus each foundation alone.
- `elicit.py` -- q_intentionality x 6 subject models x N samples, reusing
  the production engine/seeding/registry/schema machinery (see its
  docstring for the exact reuse-vs-new inventory).

## Status: full pipeline built, nothing run for real yet

Same resource split as the sibling pilot: curation needs
`ANTHROPIC_API_KEY` (~244 calls); elicitation needs a GPU + the `vllm`
extra. Verified end-to-end in this environment with `--mock` (curation ->
`--check` -> `--select` -> `power_check.py`) and `--engine fake`
(elicitation incl. resume) -- those mock outputs were deleted, not
committed, since mock ratings are hash noise.

Cost estimate, not yet validated against real throughput: at full survival,
152 items x 1 question x 6 models x N=25 = 22,800 completions -- about a
fifth of the sibling pilot's job, so well under an hour on one H200 by the
same extrapolation (and the same caveat: extrapolation, not measurement).

## What "success" looks like

- Curation: harm-controls read as harm (`harm_relevance >= moral_min`);
  foundation items read as their foundation
  (`foundation_relevance >= moral_min`) WITHOUT harm contamination
  (`harm_relevance <= nonmoral_max`). The selection report splits
  foundation failures into contamination vs. weak-signal -- the design
  doc's known-gap discussion predicts contamination is the likelier
  problem, and it's the informative one (it would mean the foundation
  can't be presented harm-free on that storyline).
- Power: note from the design-target override run
  (`--g-harm 30 --g-loyalty 13 --g-authority 13 --g-fairness 13
  --g-purity 7`): even at FULL survival, only llama's moral-only benchmark
  effect (the largest of the three families) clears the projected MDE for
  the pooled non-harm arm -- gemma/mistral-sized effects would not be
  individually detectable at these cluster counts. Same marginal-power
  picture as the sibling pilot; the pooled contrast and cross-family
  consistency carry the interpretation, not any single cell.
- Analysis (not part of this directory, same handback as the sibling):
  `sign_c` main effect, harm-control vs. pooled non-harm, family-clustered
  WCB via `analysis/rq1_v1_1_robustness/lib.py::wild_cluster_bootstrap`,
  three families x tuning split; then per-foundation repeats reported as
  exploratory.
