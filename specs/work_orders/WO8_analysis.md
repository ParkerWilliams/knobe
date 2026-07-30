# WO-8 — Behavioral statistical analysis (S8, local)
**Depends on:** results schema (spec §3.6) only — build against fixtures now; real
data later. **Blocks:** nothing (start anytime after WO-2).

## Objective
`src/knobe/analysis/`: the preregistration-grade analysis pipeline that turns
`results.jsonl` + release metadata + curated ratings into the RQ1 result set, so that
when the main run lands the analysis is a button-press, not an improvisation.

## Requirements
1. **Ingest:** stream-join results.jsonl with release vignette metadata (via
   variant_id) and curated ratings; validate row counts against the job manifest;
   exclusions ledger (parse failures, incomplete items) reported, never silent.
2. **Primary models** (per subject model; ordinal CLMM preferred, LMM sensitivity
   check; `family` random intercept + slopes where estimable, domain random effect):
   - RQ1 base: sign × tuning_status (the Raimondi replication, now over decomposed
     items).
   - 1a: sign × valence-type (moral/nonmoral) interaction; NEU handled per 1d.
   - 1b: intentionality~blame slope on bad items vs intentionality~praise slope on
     good items (Hindriks asymmetry), within moral and nonmoral separately.
   - 1c: typicality effect concentrated on positive items; evocativeness effect on
     negative items (Ngo dissociation), tested at item-rating level with curation
     vividness/typicality_perception as continuous predictors in secondary models.
   - 1d: NEU intentionality vs stakeless-baseline expectations; typicality within NEU.
3. **Multiple comparisons:** Holm within each RQ family; all planned contrasts
   declared in a `contrasts.yaml` the code reads (this file IS the prereg of record —
   human-approved before G2, frozen into the release).
4. **Descriptives + figures:** per-cell distributions (not just means), item-level
   caterpillar plots, model-family comparison panels; all figures from one styling
   module.
5. **Robustness stubs** (config-gated, off by default): chat-format condition
   comparison; Lindauer–Southwood cancelling-statement follow-up (DR "two further
   ambiguities") — schema reserved now (`format: "cancel"` prompt variant) so the
   later study reuses the whole pipeline.
6. Everything runs from fixtures in CI; a `make paper` target regenerates every
   number and figure from raw artifacts.

## Acceptance criteria
- Simulation test: pipeline applied to data generated with known effects recovers
  them (signs + approximate magnitudes) and its Type-I rate on null-generated data is
  nominal across 200 sims for the primary contrasts.
- Round-trip determinism: same inputs → identical numbers (seeded bootstraps).
- Runs against the G0 dry-run output without modification.
