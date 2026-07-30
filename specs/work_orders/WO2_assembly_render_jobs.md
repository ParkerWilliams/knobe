# WO-2 — Assembly hardening, prompt rendering, job manifests
**Stage:** S2 + local precompute for S5 (master spec §3.2, §3.4, §3.5).
**Depends on:** nothing (start immediately). **Blocks:** WO-3, WO-5, G0.

## Objective
Port `assemble_vignettes.py` into the package unchanged in behavior, then add the two
missing precompute layers: prompt rendering (`render.py`) and job-manifest
construction (`jobs.py`), so the H200 side becomes pure execution.

## Part A — port + harden assembly (`src/knobe/assemble.py`)
1. Behavior-preserving port: byte-identical `vignettes.csv` for the existing
   105-family matrix (golden-file test committed from current output).
2. Move all constants (banned lists, template, questions, variant letters) to
   `constants.py`; `curate.py` imports from there (keeps the existing single-source
   pattern).
3. Add `--release` mode: writes into `data/release/vX.Y/` and builds `manifest.json`
   (spec §3.10). Refuses if any family lacks `human_approved` or curation acceptance.

## Part B — prompt rendering (`src/knobe/render.py`)
1. For each variant × question ∈ {intentionality, blame, praise} emit a `prompts.jsonl`
   record in **raw** format using the fixed Raimondi frame (spec §3.4).
2. Additionally emit **chat** format records for the same pairs: single user message
   with identical text; store as `messages`. (Template application happens on-device
   by tokenizer at load; text is what's frozen here.) Chat records are the robustness
   pass only — flagged so WO-5 can filter.
3. Property tests: every rendered prompt contains its scenario verbatim exactly once;
   no prompt contains a banned word outside the scenario's exempt fixed clause; sha256
   stable across runs.

## Part C — job manifests (`src/knobe/jobs.py`)
1. Expand (prompt × model_key × sample_idx 0..N-1) per run config
   (`configs/run_*.yaml`: which models, which formats, N, release string).
2. Derive `temperature` and `seed` per spec §3.5 (sha256-based; unit-test exact values
   against 3 hand-computed fixtures so the derivation can never silently change).
3. `knobe jobs diff results.jsonl jobs.jsonl` → remaining-work report (the resume
   primitive WO-5 consumes).

## Acceptance criteria
- Golden-file equality on current matrix (Part A.1).
- For a 2-family toy matrix: 8 variants → 24 raw + 24 chat prompt records → with
  N=3 and 2 models, exactly 144 raw jobs; deterministic across machines.
- `manifest.json` hashes verify with `sha256sum -c` equivalents.
