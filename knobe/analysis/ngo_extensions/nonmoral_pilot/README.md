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
- `power_check.py` — projects whether the real post-curation cluster
  count is large enough to detect an effect at all, before spending an
  elicitation run on it. Reuses this project's existing MDE formula and
  SE-scaling approximation (`analysis/rq1_v1_1_robustness/09` and `15`),
  benchmarked against real numbers read from `05_valence_split_wcb.csv`
  and `32_nonmoral_subdomain_sign_wcb.csv`, not hand-copied.
- `elicit.py` — runs the actual intentionality/blame/praise questions
  against the 6 subject models (gemma/llama/mistral, pretrained +
  instruct), reusing this project's real inference machinery
  (`knobe.elicit_vllm`'s engine abstraction, `knobe.jobs`' frozen seeding
  rule, `knobe.registry`'s model resolution, `knobe.schemas.ResultRecord`
  for output) rather than a one-off reimplementation — see the script's
  own docstring for exactly what's reused vs. deliberately new.

## Status: full pipeline built (dataset, curation, selection, power check, elicitation), nothing run for real yet

This environment has no `ANTHROPIC_API_KEY` and no GPU/`vllm` — two
different resources, possibly two different people on your end. Curation
first, then elicitation:

**1. Curation** (needs `ANTHROPIC_API_KEY`):
```
.venv/bin/python analysis/ngo_extensions/nonmoral_pilot/curate_moral_relevance.py \
    --reviewer-model claude-sonnet-5
```
(240 calls, one question each — a rounding error against the existing
curation cost profile). Then build the filtered dataset elicitation
actually reads:
```
.venv/bin/python analysis/ngo_extensions/nonmoral_pilot/curate_moral_relevance.py --select
```
Selection rule: every item that independently clears its own threshold is
kept (moral items need `moral_relevance >= moral_min`; either nonmoral
framing needs `<= nonmoral_max`) — no preference between
`nonmoral_prudential`/`nonmoral_procedural` when both pass for the same
`pair_id` (an earlier draft of this rule wrongly picked one; see the
script's docstring). Writes `outputs/ngo_prudential_dataset_selected.csv`
(what `elicit.py` reads) and `outputs/selection_report.md` (a by-`pair_id`
breakdown, including which storylines end up with no usable nonmoral
framing at all). This isn't a blocking checkpoint — `elicit.py` doesn't
wait on anyone reviewing the report — but it's there to look at, before or
after running elicitation, given the full run is estimated under an hour
(below) and cheap to redo if the report shows something worth fixing.
`--check` (no filtering, just prints the same pass/fail numbers) still
works if you just want a quick look without building the selected file.

**2. Power check** (no GPU/API needed, just curation's output), before
committing to elicitation:
```
.venv/bin/python analysis/ngo_extensions/nonmoral_pilot/power_check.py
```
The thing worth checking before an elicitation run isn't cost (cheap
regardless of item count) -- it's whether the number of storylines that
survived curation is even large enough to make the result interpretable,
the same failure mode as prudential's untestable G=2 in the existing v1.1
release. Projects the minimum detectable effect at the REAL post-curation
cluster count, benchmarked against this project's own closest analogous
results (`05_valence_split_wcb.csv`'s moral-only sign_c fits,
`32_nonmoral_subdomain_sign_wcb.csv`'s aesthetic/procedural fits) — not a
blocking gate, just a report to weigh before spending the run.

**3. Elicitation** (needs a GPU + `uv pip install -e '.[vllm]'`), once
`--select` has produced `outputs/ngo_prudential_dataset_selected.csv`
(`elicit.py` exits with an error if that file doesn't exist yet):
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
vignettes already have to pass.

**Selection is per-item, not per-`pair_id`, and there's no preference
between nonmoral framings** (see `curate_moral_relevance.py --select`'s
docstring for why an earlier draft of this rule was wrong): every item
that independently clears its own threshold is included, whether that
means a `pair_id` contributes zero, one, or both nonmoral framings. Using
both when both pass makes the pooled nonmoral result more generalizable,
not redundant — the same reasoning
`docs/moral_foundations_extension/MORAL_FOUNDATIONS_PILOT_PLAN.md` uses
for pooling multiple foundations rather than picking one.

`selection_report.md` (written by `--select`) still surfaces the things
worth knowing about even though nothing is gated on them:
- Which `pair_id`s end up with **no usable nonmoral framing at all** —
  that storyline's domain doesn't have a clean nonmoral analogue in
  either framing, worth reporting rather than silently dropping (a
  finding in its own right about the domain, per
  `docs/severity_confound/SEVERITY_MORALIZATION_BACKGROUND.md`'s TDM
  discussion).
- Which of Ngo's original 80 items failed to read as moral through this
  project's own reviewer pipeline — not guaranteed just because Raimondi
  used them.
- The `category` column survives into the selected CSV, so a
  prudential-vs-procedural breakdown is still possible later as a
  secondary check, the same way aesthetic/procedural/prudential got
  broken out in `analysis/rq1_v1_1_robustness/32_nonmoral_subdomain_sign_wcb.py`.

Once `--select` has run, `elicit.py` (above) answers the actual question:
does the sign effect appear within the selected nonmoral set, compared
against the `moral` sign effect on the same 40 storyline templates?
