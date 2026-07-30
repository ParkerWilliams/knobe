# WO-3 — Curation elicitation at scale
**Stage:** S3 (local, Claude API). **Depends on:** WO-2 Part A. **Blocks:** G2.

## Objective
Port `curate_vignettes.py` to `src/knobe/curate.py`, keeping its two non-negotiables
(independent completions; reviewer ≠ subject — spec §4.1/§4.3) and adding the
throughput, resume, and acceptance mechanics needed for ~1,000 variants × 4 questions.

## Requirements
1. **Resume + concurrency:** same job-key checkpointing pattern as elicitation
   (variant × curation question); concurrent requests (async, configurable, default 8)
   with per-request retry/backoff. Curation questions come from `constants.py`
   (`CURATION_QUESTIONS`, unchanged wording).
2. **Reviewer config:** `--reviewer-model` required; subject-model list read from
   `configs/models.yaml` automatically (any HF id or family key match → hard error),
   replacing the manual `--subject-models` flag.
3. **Pair checks** (existing `check_pairs` logic): severity |Δ| ≤ 2 within
   (family, typicality) low/high pairs; vividness gap ≥ 2. Keep thresholds in config,
   report the empirical distributions so thresholds can be revisited (the code's own
   caveat). Add the typicality manipulation check (DR §5.1): mean
   `typicality_perception` of common-variant rows must exceed uncommon-variant rows
   within family; flag violators.
4. **Category manipulation check (DR §13):** moral_relevance must separate MB/MG from
   NMB/NMG/NEU; emit per-item flags for MB/MG items scoring <6 or NMB/NMG >4
   (thresholds in config) and a summary distribution plot (matplotlib, saved PNG).
5. **Acceptance workflow:** `knobe curate review` prints flagged items with their
   family context for human accept/revise decisions, writing `accepted` into
   `curated.csv`. Revised families re-enter via WO-1 ingest (new family version id
   suffix, e.g. `ENV-MB-01r1`), never by in-place edit.
6. Cost/telemetry: per-run token + call counts logged.

## Acceptance criteria
- Mock-client tests for: resume skips completed keys; a reviewer matching a subject
  family fails at startup; pair/typicality/category checks fire on constructed
  fixtures; unparseable responses never coerce to a number (existing invariant).
- Dry-run mode (`--mock`) executes the full path against fake responses with zero
  network calls (needed so G0 can rehearse curation plumbing offline).
