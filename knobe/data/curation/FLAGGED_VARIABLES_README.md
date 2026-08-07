# Curation manipulation-check flags — how these CSVs were built, and what to do with them

Companion files: `moral_relevance_flagged.csv`, `vividness_gap_flagged.csv`,
`severity_mismatch_flagged.csv`, `typicality_manipulation_flagged.csv`.

## Why these exist

Every vignette gets four independent 0-10 ratings from a reviewer model at
curation time (`CURATION_QUESTIONS` in `src/knobe/constants.py`):
`moral_relevance`, `severity`, `vividness`, `typicality_perception`. These
exist to check that each design manipulation (valence category, evocativeness,
typicality) actually reads the way it was intended to read to an independent
judge, and that manipulations that are supposed to hold something constant
(severity, across the evocativeness swap) actually do. `src/knobe/curate.py`
runs four checks against these ratings and writes the result into
`individual_flags` / `pair_flag` columns in `data/curation/curated.csv`:

| check | function | scope | threshold (`configs/curation.yaml`) |
|---|---|---|---|
| category manipulation | `check_category_manipulation` | per-variant | MB/MG must score `moral_relevance >= 6`; NMB/NMG/NEU must score `<= 4` |
| vividness gap | `check_pairs` | per (family, typicality) pair | high-evoc vividness − low-evoc vividness must be `>= 2` |
| severity match | `check_pairs` | per (family, typicality) pair | \|high-evoc severity − low-evoc severity\| must be `<= 2` |
| typicality manipulation | `check_typicality_manipulation` | per family | mean `typicality_perception` of common variants must exceed mean of uncommon variants |

The four CSVs here pull each of those checks out into its own file, joined
against `data/authoring/ALL_DOMAINS_master_matrix.csv` for the actual
goal/action/outcome text, so the flagged cases can be reviewed and rewritten
directly rather than reverse-engineered from `curated.csv`'s packed flag
strings.

## One thing the CSVs surface that the pipeline's own count doesn't

`check_pairs` requires **all four** of (low-severity, high-severity,
low-vividness, high-vividness) to be parseable before it will run *either*
the severity or the vividness comparison for a pair — if either side's
severity rating was unparseable, the pair is skipped entirely, even if both
vividness ratings are fine (`curate.py:587-589`). That coupling means some
real vividness-gap failures never got an official flag. `vividness_gap_flagged.csv`
computes the gap directly from the raw ratings regardless of severity
parseability, and marks those extra cases `SKIPPED_BY_PIPELINE (gap<2: True)`
in `official_flag` so they're visible instead of silently absent. Worth a
small fix in `curate.py` to decouple the two checks; not touched here since
that's a pipeline change, not a data one.

## What was found, and what to do about each

### `moral_relevance_flagged.csv` — 57/420 variants (13.6%) miscategorized
**Pattern:** concentrated, not uniform. Zero MB items misfire (mean 8.9,
stdev 0.59); MG is much noisier (mean 6.47, stdev 2.31, some as low as 2).
Nonmoral misfires cluster in `procedural`/`aesthetic` subdomains (36/39) and
in domains with inherent real-world stakes (Healthcare, Finance, Environment,
Data Privacy, Product Safety — 20-26% flag rate vs. 2.6% for Animal Welfare).
It clusters by **family**, not by random variant noise: 31 distinct families
account for all 57 flags, because the shared goal/context for a family set
(e.g. "restructure nurse staffing ratios to reduce labor costs") often
carries real moral weight on its own, independent of whatever nominally-
nonmoral outcome_verb (decor, cover design, odor) was picked for that
family's NMB/NMG sibling.

**Next steps:**
1. Rewrite the ~31 flagged families, prioritized by domain
   (Healthcare/Finance/Environment/Data Privacy/Product Safety) and
   subdomain (procedural/aesthetic first) — either soften the shared goal so
   it isn't itself stakes-laden, or pick an outcome_verb that's a cleaner
   side-channel.
2. Generalize the existing "document-readability trap" guardrail in
   `GENERATION_SYSTEM_PROMPT` (`constants.py`) — currently scoped to
   documents only — into a general rule that NMB/NMG outcomes must be as
   dimensionally independent from the domain's real stakes as NEU already is
   required to be.
3. Separately: MG's much looser spread than MB's suggests the reviewer
   *instrument* itself may weight harms as more legibly "moral" than
   equivalent benefits. Worth a small calibration check (rate a few matched
   harm/benefit pairs of equal magnitude) before assuming every low-MG score
   is a stimulus bug rather than a judge bias.

### `vividness_gap_flagged.csv` — 173/210 pairs (82%) fail, 36 reversed
**Pattern:** uniform, not concentrated — spread evenly across every domain
(13-26 each) and every valence (36-42 each, MB slightly better at 17), and
roughly even across typicality (89 common / 84 uncommon). This is **not** a
fixable list of bad vignettes; it's a construct mismatch baked into the
generation instructions. `high_evocative_outcome` was written to be more
*concrete/specific*; the curation question asks about *emotional vividness*.
Those aren't the same axis, so most pairs don't show a gap on the axis being
measured even when they do differ on the axis being manipulated.

**"36 reversed" counting convention:** that figure (and the 173/210 above)
counts at the **pair level** — 210 total `(family_id, typicality)` pairs,
the exact unit `check_pairs` operates on. A family-level count (mean gap
across a family's up-to-two typicality-conditioned pairs) gives a different
number — 27 families with a strictly negative mean gap, 51 including
exact-zero-mean ties — which is not a data discrepancy, just a different
unit of analysis. State which one you're using when citing either number.

**Next steps:** this needs a v1.1 redesign, not per-item patching. See
`docs/V1_1_REVISION_PLAN.md` Workstream B §3 for the current thinking:
external-lexicon scoring was considered and rejected (it encodes what human
lexicographers tagged as emotionally loaded, not what's salient to the
subject models being tested); personal-report wording framing ("residents
said..." vs. "a survey found...") was tested directly against this data and
does *not* meaningfully move the vividness gap (0.51 vs. 0.45 mean gap with
vs. without that framing — no real difference), so don't rely on it as a
fix. Current candidates are subject-model self-report of affect salience or
a surprisal-based signal — both grounded in the models being tested rather
than an external judge. Don't spend review time rewriting individual pairs
until the construct itself is decided; you'd be re-fighting the same
failure 173 times.

### `severity_mismatch_flagged.csv` — 6/187 pairs (3.2%)
Small and not patterned (mild MG concentration, 5/6). Spot-fixable — review
these six pairs directly and adjust wording so the evocativeness swap
doesn't also change perceived severity.

### `typicality_manipulation_flagged.csv` — 4/105 families (3.8%)
Small, isolated, no domain/subdomain pattern (2 Product Safety, 1
Environment, 1 Workplace). Spot-fixable.

## Bottom line

Two of these four checks are basically clean (severity, typicality) — don't
over-invest there. `moral_relevance` has a real but *targeted* problem with
a clear fix list. `vividness`/evocativeness has a *systemic* problem that
needs a construct redesign before any amount of vignette-level editing will
help.
