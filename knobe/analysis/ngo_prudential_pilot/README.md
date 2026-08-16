# Ngo/Raimondi prudential-nonmoral extension pilot

Extends Raimondi et al. (arXiv:2510.12229)'s own 80-scenario design (Ngo
et al. 2015, *Scientific Reports* 5:17390 — the local copy is
`ngo_2015_original_80.txt`) with a matched nonmoral-prudential third
variant for each of the 40 harm/help pairs, rather than folding a new
axis into this project's own decomposed factorial dataset
(`data/release/v1.1/`). Rationale: a self-regarding (prudential) outcome
engages no other party's welfare or rights at all, so it's the sharpest
available test of whether the classic Knobe asymmetry is genuinely
moral-specific or just tracks badness/severity in general — and staying
inside Raimondi's original template (rather than this project's own
typicality/evocativeness/domain-crossed design) keeps the comparison to
their reported numbers clean, the same way `docs/RAIMONDI_REPLICATION_GAPS.md`
depended on a directly comparable slice to diagnose the pretrained scoring
artifact.

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
- `build_dataset.py` — merges both into `outputs/ngo_prudential_dataset.csv`
  (160 rows: 80 moral + 80 nonmoral_prudential, already generated and
  committed — this part needs no API access, it's pure text).
- `curate_moral_relevance.py` — the curation-only manipulation check.

## Status: dataset built, curation not yet run

This environment has no `ANTHROPIC_API_KEY`. Verified clean with `--mock`
(zero API calls, deterministic fake responses) — no import or logic
errors. Whoever has the same curation-reviewer access already used for
`knobe curate run` needs to run:

```
.venv/bin/python analysis/ngo_prudential_pilot/curate_moral_relevance.py \
    --reviewer-model claude-sonnet-5
```

(160 calls, one question each — a rounding error against the existing
curation cost profile). Then:

```
.venv/bin/python analysis/ngo_prudential_pilot/curate_moral_relevance.py --check
```

## What this reuses vs. what's new

Reuses directly: `constants.CURATION_QUESTIONS["moral_relevance"]` and
`constants.CURATION_PROMPT_TEMPLATE` (the exact frozen question/format,
not reworded), `curate.AnthropicClient`/`MockClient`/`_complete_with_retry`
(the actual API-calling/retry machinery), `parsing.parse_rating`, and
`configs/curation.yaml`'s `moral_min`/`nonmoral_max` thresholds (the same
numbers `check_category_manipulation` uses in production). **Does not**
reuse `curate.run()`'s full orchestration — that expects a `Family`
registry and the production `CuratedRow` schema (typicality/evocativeness/
severity/domain), which this pilot's plain 160-item, single-question check
doesn't have and doesn't need.

## What "success" looks like

`moral` items should score at or above `moral_min=6`; `nonmoral_prudential`
items at or below `nonmoral_max=4` — the same category-manipulation check
production vignettes already have to pass. Two outcomes:

- **Both pass**: the prudential variants read as crisply nonmoral,
  and the original 80 still read as clearly moral through this project's
  own reviewer pipeline (not guaranteed just because Raimondi used them —
  worth confirming). Proceed to a real elicitation pilot (does the sign
  effect appear within `nonmoral_prudential`, matched pairwise against the
  `moral` sign effect on the same 40 storyline templates?).
- **`nonmoral_prudential` items don't clear `nonmoral_max`**: the
  self-regarding redirect wasn't enough to escape moral registration for
  some pairs — report which `pair_id`s failed and by how much (a finding
  in its own right, per `docs/SEVERITY_MORALIZATION_BACKGROUND.md`'s TDM
  discussion) rather than silently dropping them.
