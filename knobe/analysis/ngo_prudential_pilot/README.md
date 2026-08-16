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
`docs/RAIMONDI_REPLICATION_GAPS.md` depended on a directly comparable
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
- `build_dataset.py` — merges all three into `outputs/ngo_prudential_dataset.csv`
  (240 rows: 80 moral + 80 nonmoral_prudential + 80 nonmoral_procedural,
  already generated and committed — this part needs no API access, it's
  pure text).
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

(240 calls, one question each — a rounding error against the existing
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
  own right about the domain, per `docs/SEVERITY_MORALIZATION_BACKGROUND.md`'s
  TDM discussion).
- Also confirm the original 80 still read as clearly moral through this
  project's own reviewer pipeline — not guaranteed just because Raimondi
  used them.

Once each `pair_id` has at least one nonmoral framing that clears
`nonmoral_max`, proceed to a real elicitation pilot: does the sign effect
appear within the surviving nonmoral set, matched pairwise against the
`moral` sign effect on the same 40 storyline templates?
