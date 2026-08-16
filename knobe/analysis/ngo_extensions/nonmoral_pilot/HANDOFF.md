# Handoff: run the Ngo nonmoral pilot

One person, one environment (same `ANTHROPIC_API_KEY` + GPU/HF access
already used for this project's main runs). Run these in order.

## One-time setup

1. `git pull` on `main` — this pilot lives at
   `analysis/ngo_extensions/nonmoral_pilot/`.
2. `uv pip install -e ".[dev,stats,vllm]"` (adds the `vllm` extra on top
   of the base install; skip if already installed).
3. `export ANTHROPIC_API_KEY=...` — same reviewer-model access already
   used for `knobe curate run`.
4. Confirm HuggingFace access to the gated checkpoints
   (`google/gemma-2-9b`/`-it`, `meta-llama/Llama-3.1-8B`/`-Instruct`) —
   should already be in place if this is the same environment/account
   that ran the main v1.1 elicitation.
5. If this project's GPU stages normally go through the cluster
   job-submission wrapper (`scripts/cluster_connect.sh`, per the top-level
   README's "H200 arrival checklist") rather than direct execution on the
   box, adapt step 4 below to that convention — `elicit.py` has only been
   verified via direct invocation (`--engine fake`), not through that
   wrapper.

## Run, in order

```
cd analysis/ngo_extensions/nonmoral_pilot

# 1. Curation (~240 calls, cheap and fast)
.venv/bin/python curate_moral_relevance.py --reviewer-model claude-sonnet-5

# 2. Build the filtered dataset + a by-storyline report
.venv/bin/python curate_moral_relevance.py --select
cat outputs/selection_report.md   # worth a look; doesn't block the next step

# 3. Power check (instant — no GPU/API needed, just curation's own output)
.venv/bin/python power_check.py

# 4. Elicitation. Recommend one small timing run first:
.venv/bin/python elicit.py --engine vllm --n-samples 1
# ...then the real run (~108,000 completions at N=25, estimated well under
# an hour on one H200 -- not a measurement, just an extrapolation from the
# v1.1 main run's own throughput):
.venv/bin/python elicit.py --engine vllm --n-samples 25
```

Step 4 resumes automatically if interrupted — rerunning the same command
skips whatever's already in `outputs/elicit_results.jsonl`.

## What you'll have afterward

`outputs/elicit_results.jsonl` — one row per (prompt_id, model_key,
sample_idx), same schema as any other `results.jsonl` in this project.
Analysis (joining against `outputs/ngo_prudential_dataset_selected.csv`,
fitting the WCB contrasts) isn't part of this handoff — send the file back
and it gets picked up from there.

## If something looks off

- `selection_report.md` (step 2) flags any `pair_id` with no usable
  nonmoral framing, and any of Ngo's original 80 items that unexpectedly
  failed the moral check.
- `power_check.py` (step 3) reports whether the surviving cluster count
  looks large enough to detect an effect at all, benchmarked against this
  project's own comparable results.

Neither of these blocks the run — they're there to look at before or
after, not a required approval step.
