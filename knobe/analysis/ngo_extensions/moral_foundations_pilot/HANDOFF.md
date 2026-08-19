# Handoff: run the moral-foundations pilot

One person, one environment (same `ANTHROPIC_API_KEY` + GPU/HF access
already used for this project's main runs). Same shape as
`../nonmoral_pilot/HANDOFF.md`; run these in order.

## One-time setup

Identical to `../nonmoral_pilot/HANDOFF.md`'s setup (same env, same gated
checkpoints, same cluster-wrapper caveat) -- if that pilot's setup is done,
nothing new is needed here.

## Run, in order

```
cd analysis/ngo_extensions/moral_foundations_pilot

# 1. Curation (~244 calls: 152 harm-relevance + 92 foundation-relevance)
.venv/bin/python curate_foundation_relevance.py --reviewer-model claude-sonnet-5

# 2. Build the filtered dataset + selection report
.venv/bin/python curate_foundation_relevance.py --select
cat outputs/selection_report.md   # worth a look; doesn't block the next step

# 3. Power check (instant -- no GPU/API needed, just curation's own output)
.venv/bin/python power_check.py

# 4. Elicitation. Recommend one small timing run first:
.venv/bin/python elicit.py --engine vllm --n-samples 1
# ...then the real run (~22,800 completions at N=25 if everything survives
# curation -- about a fifth of the nonmoral pilot's job, same
# extrapolation-not-measurement caveat):
.venv/bin/python elicit.py --engine vllm --n-samples 25
```

Steps 1 and 4 both resume automatically if interrupted -- rerunning the
same command skips whatever is already in the output file.

## What you'll have afterward

`outputs/elicit_results.jsonl` -- one row per (prompt_id, model_key,
sample_idx), production `ResultRecord` schema. Analysis (joining against
`outputs/mf_pilot_dataset.csv` via the `variant_id` prefix of `prompt_id`,
fitting the harm-vs-pooled-non-harm WCB contrast) isn't part of this
handoff -- send the file back and it gets picked up from there.

## If something looks off

- `outputs/selection_report.md` (step 2) flags harm-controls that failed
  to read as harm, foundation items lost to harm contamination vs. weak
  foundation signal, per-condition surviving cluster counts, and any
  storyline left with no non-harm item at all.
- `power_check.py` (step 3) reports whether surviving cluster counts make
  the tests interpretable, benchmarked against this project's own
  comparable results; arms with G<3 are marked untestable (the v1.1
  prudential G=2 failure mode).

Neither blocks the run -- they're there to look at before or after, not a
required approval step.
