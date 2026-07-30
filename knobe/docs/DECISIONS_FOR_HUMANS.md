# Decisions for humans

This codebase implements a fully specified design, but a handful of scientific
and modeling choices were made *by following the spec's letter* where the spec
itself may deserve a second look, or where two design documents disagree. None
of these blocks the pipeline from running end-to-end; each should be confirmed
by the researchers **before pre-registration freeze and before any RQ claim**
is drawn from the affected output.

This file is committed (unlike the working notes under `.superpowers/`, which
is gitignored) so the list travels with the repo.

---

## (a) T8 — RQ2 probe confound sets include behavioral means — RESOLVED (2026-07-28)

**Where:** `src/knobe/mech/probes.py` / `src/knobe/mech/_data.py` (the
`confound_frame` / construct-spec residualization for the `sign` and
`valence_moral` probes).

The spec instructs, for the moral-valence and sign construct probes, to
"residualize on the other constructs." Implemented literally, the confound set
for those probes included the downstream behavioral means `blame_mean` and
`intentionality_mean`. But those means are plausibly **mediators** of the very
localization RQ2 is trying to measure: residualizing a design factor on a
downstream behavioral response conditions on a mediator, which can erase
genuine localization signal rather than control nuisance variance.

**RESOLVED (2026-07-28, researcher directive):** behavioral means are
**excluded** from the residualization confound sets of the `sign` and
`valence_moral` probes (they are downstream consequences of those design
factors — conditioning on them conditions on mediators). Implemented via the
`_BEHAVIORAL_MEDIATORS` addition to those two specs' `exclude` tuples in
`mech/_data.py`; the `residualization_recipe` strings for both probes no longer
list `blame_mean`/`intentionality_mean`. The curation-rating confounds
(`severity`, `vividness`, `typicality_perception`) and the other design factors
are retained.

**Sub-question RESOLVED (2026-07-28, researcher directive):** the same mediator
logic applies to `typicality_condition` and `vividness_evocativeness` — the
behavioral means are excluded from those confound sets too. Rationale
confirmed with the researcher: the component of a design factor's
representation that co-varies with the model's blame/intentionality outputs is
the causally efficacious signal, not a confound; residualizing it away would
leave only the behaviorally inert remainder. Curation-rating probes are
unchanged (their cross-item correlation is a stimulus-construction confound,
which residualization is for).

## (b) T9 — LMM-primary / OrderedModel-sensitivity inversion, and domain clustering

**Where:** `src/knobe/analysis/models.py` (primary RQ1 fits + the
config-gated `--domain-sensitivity` fit).

Two coupled choices:

1. WO-8 originally called an ordinal cumulative-link mixed model (CLMM) the
   *preferred* primary model. `statsmodels` has no CLMM with random effects
   (`OrderedModel` is fixed-effects only), so this implementation **inverts**
   that: a linear mixed model (LMM) with a family random intercept is the
   primary fit, and `OrderedModel` is run only as a no-random-effects
   *sensitivity* check. This is an honest engineering constraint, not a
   silent downgrade, but it reverses the spec's stated preference.
2. The primary LMM models **family** clustering only. Master spec §6's intent
   ("domain = random effect") is served by a separate, config-gated
   `--domain-sensitivity` fit (`groups=domain`) rather than the primary model,
   because the two random-effect groupings are not simultaneously fittable in
   the primary specification.

**RESOLVED (2026-07-28, researcher directive):** LMM accepted as the primary
model; `OrderedModel` remains the distributional sensitivity check. Domain
clustering stays out of the primary fit and is assessed via the config-gated
`--domain-sensitivity` (`groups=domain`) fit. Note for the record: the real
pipeline reads all 10 domains from `ALL_DOMAINS_master_matrix.csv` end to end
(verified: 105 families → 420 variants, 10 domains); small domain counts appear
only in synthetic pytest fixtures.

**FINAL RESOLUTION (2026-07-28, researcher decision — middle course adopted):**
the **family-RI LMM stays primary**, and a **DECLARED domain-random-slope
sensitivity analysis** is added to the prereg (`configs/contrasts.yaml`,
`sensitivity_analyses.domain_random_slope`) for the four headline
cross-domain-generalization contrasts (`rq1_base_sign_x_tuning`,
`rq1a_sign_x_valence_type`, both `rq1c_*`). For each, `mixedlm` is fit with
`groups=domain` and a random **slope** for the focal term
(`re_formula="~<term>"`), same fixed effects as the primary; non-convergence is
recorded honestly (no OLS fallback — there is no random slope to recover under
OLS). The declared, machine-readable interpretation rule
(`models.CI_WIDTH_RATIO_THRESHOLD = 1.5`, `models.SLOPE_VAR_THRESHOLD`): if the
domain-random-slope CI is materially wider than the primary CI (ratio > 1.5) or
the between-domain slope variance is non-negligible, that contrast's
cross-domain generalization claim is reported **QUALIFIED**. The
domain-**intercept** cluster fit (`--domain-sensitivity`, `groups=domain`) is
**retained as the secondary check**. Run both via `knobe analyze
--domain-slope-sensitivity` / `--domain-sensitivity`; results land in
`domain_slope_sensitivity.csv` / `domain_sensitivity.csv` and their own
`summary.md` sections. This section (b) is now fully resolved.

## (c) T0 — `ResultRecord.parsed_rating` is `int | float | None`

**Where:** `src/knobe/schemas.py` (`ResultRecord.parsed_rating`).

Spec §3.6 types this field as `int | null`. It is implemented as
`int | float | None`, because the logit-fallback scoring path (spec §4.4,
`parse_method="logit_fallback"`) produces a non-integer **expected value** over
the 0–10 distribution, which cannot round-trip through an `int`-only field
without discarding information. The `float` widening is deliberate and
localized; confirm it is acceptable relative to the §3.6 contract.

**RESOLVED (2026-07-28, researcher directive):** `int | float | None` widening
accepted as fine and expected.

## (d) Freeze-time confirmations

**Where:** `src/knobe/assemble.py`, `src/knobe/curate.py`,
`src/knobe/constants.py`.

A cluster of smaller choices that are resolved in code but should be eyeballed
once at freeze:

- **NEU 4-variant decision** — spec §3.2 says NEU families produce all 4
  variants; DR §7 says 2. The spec was followed (4 variants). This is the
  already-flagged, resolved conflict from `common-context.md`; re-confirm it is
  still the intended end state.
- **Manifest `by_valence` / `by_domain` counts** are tallied at the **variant**
  level (not the family level) in the release manifest. Confirm that is the
  count the researchers expect to read there.
- **T4 NEU inclusion in the curation category check** — the nonmoral-threshold
  category check in curation includes NEU items in its denominator; confirm NEU
  belongs on that side of the nonmoral threshold.

**RESOLVED (2026-07-28, researcher directives):** d1 NEU 4-variant confirmed as
intended end state; d2 manifest reports both variant-level and family-level
counts, labeled (implemented in this commit); d3 NEU confirmed in the
nonmoral-threshold denominator of the curation category check. Item (e) remains
the only open item (awaits pilot blame/praise data).

## (e) T6 — 1b power-curve placeholder calibration

**Where:** `src/knobe/power.py` / `src/knobe/power_sim.py` (also surfaced in
the printed power report artifact).

The power curve for the 1b contrast uses a placeholder effect-size calibration
until a real pilot is available. This is annotated in the generated
`power_report/` artifact, but the placeholder must be replaced with a
pilot-derived effect size before the power analysis is used to justify sample
sizes.

**Plan of record (2026-07-28, researcher directive):** recalibrate 1b from the
G1 pilot (observed slope difference, empirical spread of item-level
blame/praise means, and the within- vs between-item variance ratio — the pilot
elicits blame and praise of every item anyway), then re-run
`knobe power simulate`. **If the recalibrated curves indicate that N (response-
level and/or item-level) must be much larger than the pilot defaults, we grow N
in response** — sample size follows the power analysis, not the other way
around. Three a-priori-unknowable quantities drive 1b's demands: the slope-
difference magnitude (a difference-of-slopes compounds noise like any
interaction, DR §16), the predictor's empirical spread (restricted range of
item blame/praise means inflates slope SEs), and errors-in-variables
attenuation (item means are estimates; response-level N shrinks the
predictor's measurement error, so 1b uniquely benefits from more samples per
item). If even generous N leaves 1b underpowered, that finding is reported and
1b is de-emphasized rather than preregistered as a headline claim. This item
stays open until the pilot lands.
