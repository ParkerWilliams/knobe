# Ngo/Raimondi nonmoral-extension pilot

Extends Raimondi et al. (arXiv:2510.12229)'s own 80-scenario design (Ngo
et al. 2015, *Scientific Reports* 5:17390 — the local copy is
`ngo_2015_original_80.txt`) with **two independent** nonmoral third
variants for each of the 40 harm/help pairs, rather than folding a new
axis into this project's own decomposed factorial dataset
(`data/release/v1.1/`):

- **Prudential** (`prudential_variants.py`): redirects the affected party
  to the agent's own self-interest (health, finances, reputation, safety).
  A self-regarding outcome engages no other party's welfare or rights at
  all, making it the sharpest available test of whether the classic Knobe
  asymmetry is genuinely moral-specific or just tracks badness/severity in
  general.
- **Procedural** (`procedural_variants.py`): redirects the affected outcome
  to an arbitrary office/social convention (dress code, seating chart,
  naming convention) — Turiel's conventional pole, the polar opposite of a
  harm/welfare stake. Added as a fallback in case prudential's
  self-regarding-*harm* framing still reads as too morally loaded for some
  pairs (a self-inflicted injury or financial loss can still register as
  "significant" even with no other party involved) — procedural has no
  stakes for anyone at all, moral or otherwise.

Both stay inside Raimondi's original template (rather than this project's
own typicality/evocativeness/domain-crossed design) to keep the comparison
to their reported numbers clean, the same way
`docs/rq1_findings/RAIMONDI_REPLICATION_GAPS.md` depended on a directly comparable
slice to diagnose the pretrained scoring artifact.

Each new item keeps the original template exactly — *"[Agent] [did X] to
[goal]. [Agent] did not care at all about the effect this would have on
[affected]. [Agent] knew [X] would help/harm: [outcome]."* — but redirects
the affected party from another person/group to the agent's own
self-interest (health, finances, reputation, standing, safety). A few
source pairs (13-14, 67-68, 73-74: wartime bombing, terrorism, mass
suicide) have no plausible self-regarding analogue at comparable stakes;
those use a fresh mundane domain instead of forcing the original topic —
noted in `prudential_variants.py`'s docstring.

## Files

- `ngo_2015_original_80.txt` — the source Ngo/Raimondi stimuli (80 items).
- `prudential_variants.py` — the 40 new self-regarding pairs (hand-authored).
- `procedural_variants.py` — the 40 new convention/etiquette pairs (hand-authored).

Each of the 240 dataset rows carries three questions, not just one:
`q_intentionality` (targets the foreseen SIDE EFFECT only — e.g. "Did Bill
intentionally cause the death of babies?", never the main action, which is
never in question), `q_blame`, and `q_praise` (`constants.QUESTIONS`'
frozen wording, same agent phrase, rendered for every item regardless of
sign — matching `render.py`'s production convention that every variant
gets all three question types, with the *analysis* stage picking
blame-for-bad/praise-for-good later, not elicitation). As with everything
else here, each question type would be sent to the model as its own
independent, single-turn completion (this project's existing
"INDEPENDENT COMPLETIONS" convention, `curate.py`'s docstring, master spec
§4.1) — never concatenated into one multi-question prompt, so adding
blame/praise doesn't change what the model sees for `q_intentionality`.
- `build_dataset.py` — merges all three into `outputs/ngo_prudential_dataset.csv`
  (240 rows: 80 moral + 80 nonmoral_prudential + 80 nonmoral_procedural,
  already generated and committed — this part needs no API access, it's
  pure text).
- `curate_moral_relevance.py` — the curation-only manipulation check.
- `elicit.py` — runs the actual intentionality/blame/praise questions
  against the 6 subject models (gemma/llama/mistral, pretrained +
  instruct), reusing this project's real inference machinery
  (`knobe.elicit_vllm`'s engine abstraction, `knobe.jobs`' frozen seeding
  rule, `knobe.registry`'s model resolution, `knobe.schemas.ResultRecord`
  for output) rather than a one-off reimplementation — see the script's
  own docstring for exactly what's reused vs. deliberately new.

## Status: dataset built, curation not yet run, elicitation built not yet run

This environment has no `ANTHROPIC_API_KEY` and no GPU/`vllm` — two
different resources, possibly two different people on your end. Curation
first, then elicitation:

**1. Curation** (needs `ANTHROPIC_API_KEY`):
```
.venv/bin/python analysis/ngo_extensions/nonmoral_pilot/curate_moral_relevance.py \
    --reviewer-model claude-sonnet-5
```
(240 calls, one question each — a rounding error against the existing
curation cost profile). Then:
```
.venv/bin/python analysis/ngo_extensions/nonmoral_pilot/curate_moral_relevance.py --check
```

**2. Elicitation** (needs a GPU + `uv pip install -e '.[vllm]'`), once
curation passes for whichever `pair_id`s/framings clear the threshold
(§"What success looks like" below):
```
.venv/bin/python analysis/ngo_extensions/nonmoral_pilot/elicit.py \
    --engine vllm --n-samples 25
```
Verified clean with `--engine fake` (deterministic, zero GPU/model
access) — correct model resolution against the real registry, correct
seeding, correct resume behavior. **Not yet run for real.**

Cost estimate, not yet validated against real throughput: 240 items x 3
questions x 6 models x N=25 samples = 108,000 completions — about 6% of
the v1.1 main run's scale (1.8M completions, "a few GPU-hours total" per
`specs/00_PLAN.md`), so likely well under an hour on one H200, but that's
an extrapolation, not a measurement. Recommend a quick timing check first
(`--n-samples 1` against one model) before committing to the full N=25
run, per this project's own cost-check-before-expensive-runs convention.

## What this reuses vs. what's new

Reuses directly: `constants.CURATION_QUESTIONS["moral_relevance"]` and
`constants.CURATION_PROMPT_TEMPLATE` (the exact frozen question/format,
not reworded), `curate.AnthropicClient`/`MockClient`/`_complete_with_retry`
(the actual API-calling/retry machinery), `parsing.parse_rating`, and
`configs/curation.yaml`'s `moral_min`/`nonmoral_max` thresholds (the same
numbers `check_category_manipulation` uses in production). **Does not**
reuse `curate.run()`'s full orchestration — that expects a `Family`
registry and the production `CuratedRow` schema (typicality/evocativeness/
severity/domain), which this pilot's plain 240-item, single-question check
doesn't have and doesn't need.

## What "success" looks like

`moral` items should score at or above `moral_min=6`; both
`nonmoral_prudential` and `nonmoral_procedural` items at or below
`nonmoral_max=4` — the same category-manipulation check production
vignettes already have to pass. Outcomes, per `pair_id` rather than in the
aggregate (a pair can pass on one nonmoral framing and not the other):

- **A pair passes on `nonmoral_prudential`**: use that framing for the
  pair — it's the more scientifically direct test (self-regarding harm vs.
  no harm to anyone), so prefer it whenever it clears the threshold.
- **A pair fails `nonmoral_prudential` but passes `nonmoral_procedural`**:
  fall back to the procedural framing for that `pair_id` — evidence the
  self-regarding-harm framing was still registering as morally loaded for
  that particular storyline, consistent with harm-to-self sometimes still
  reading as "significant" even with no other party involved.
- **A pair fails both**: that storyline's domain doesn't have a clean
  nonmoral analogue in either framing — worth reporting which `pair_id`s
  these are and why, rather than silently dropping them (a finding in its
  own right about the domain, per `docs/severity_confound/SEVERITY_MORALIZATION_BACKGROUND.md`'s
  TDM discussion).
- Also confirm the original 80 still read as clearly moral through this
  project's own reviewer pipeline — not guaranteed just because Raimondi
  used them.

Once each `pair_id` has at least one nonmoral framing that clears
`nonmoral_max`, run `elicit.py` (above): does the sign effect appear
within the surviving nonmoral set, matched pairwise against the
`moral` sign effect on the same 40 storyline templates?
