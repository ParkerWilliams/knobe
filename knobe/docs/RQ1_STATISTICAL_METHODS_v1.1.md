# RQ1 Statistical Methods and Diagnostics — Release v1.1 (revised 2026-08-10)

**Status:** technical companion to `docs/RQ1_MECHANISM_ANALYSIS_v1.1.md` (the
research-interpretation writeup) and `docs/MAIN_RUN_WRITEUP_v1.1.md` (the
headline results). **This is a full revision, not an addendum.** The first
pass (§1–§7 below) documented the pipeline's own model specification and
diagnostics and, on that basis, provisionally trusted RQ1a's set-cluster
significance and RQ1b's primary-model point estimates. A follow-up
small-cluster-robust re-analysis (§8–§11) — wild cluster bootstrap, a
severity-covariate refit, an RE/pooled-OLS/fixed-effects diagnostic, and a
family-random-slope check — overturned several of those provisional
conclusions, not just qualified them, and led to an actual code fix in
`src/knobe/analysis/models.py` (§10.3). §12 replaces the old "what to trust"
table; treat it as authoritative over §7's more optimistic reading. §13 is
the current next-steps list.

Numbers trace to `results/v1.1/paper/contrast_table.csv` (regenerated after
the §10.3 code fix), `set_sensitivity.csv`, `ordinal_sensitivity.csv`, and
`exclusions.json`. The wild-cluster-bootstrap, severity-covariate, RE/OLS/FE,
and random-slope numbers in §8–§11 are exploratory analyses run directly
against `results/v1.1/results_all.jsonl` + `data/release/v1.1/vignettes.csv`
+ `data/curation/curated_v1.1.csv` (for severity), not yet pipeline artifacts.

## 1. Data and exclusions

`exclusions.json`: of 378,000 result rows read, 378,000 included, 0 excluded
(no curation-flag exclusion applied — `--exclude-flagged` was not passed, per
the release decision to accept flagged variants into the frozen release
rather than curate them out; see `docs/RQ1_MECHANISM_ANALYSIS_v1.1.md` and
`data/curation/FLAGGED_VARIABLES_README.md`). All six checkpoints were scored
via `--logit-fallback` (softmax expected value over `logprobs_0_10`) rather
than the regex-parsed rating, per the v1.1 decision to score uniformly across
checkpoints (spec §4.4) regardless of measured parse rate.

Response-level ratings are the unit of analysis throughout — never
item-aggregated for inference (master spec §6.3; item means are for
descriptive figures only, none of which were generated for this exploratory
run, `--no-figures`).

## 2. Effect coding

All categorical predictors are coded ±0.5 (not 0/1), so that a main-effect
coefficient is read at the other factor's mean and an interaction is a pure
product contrast (no need to hold a reference category fixed at 0):

| column | source | +0.5 | −0.5 |
|---|---|---|---|
| `sign_c` | `sign` | bad | good |
| `tuning_c` | `tuning_status` | finetuned | pretrained |
| `vt_c` | `valence_type` | moral | nonmoral |
| `typ_c` | `typicality` | uncommon | common |
| `evoc_c` | `evocativeness` | high | low |

`rating_centered = rating − 5.0` (scale midpoint), used only by the `lmm_offset`
kind (RQ1d's NEU-offset contrast, so the fitted Intercept directly tests the
deviation from the neutral point rather than from 0).

Unmapped categories (`sign == "na"` for NEU rows feeding `sign_c`) become
`NaN` and are dropped only by whichever contrast's formula actually
references that column (`_formula_columns`, token-matched against the
formula string) — a contrast that doesn't use `sign_c` keeps NEU rows.

### 1b's predictor is a standardized item-level mean, not a raw rating

`prepare_1b_frame` (models.py:302–328) builds a separate frame per
valence_type × finetuned-only subset:

1. For each `variant_id`, compute the item's mean rating on its
   *responsibility channel* — `blame` if `sign == "bad"`, `praise` if
   `sign == "good"` — across all samples of that item/model/question.
2. Join that value onto the same item's `intentionality` response rows as
   `pred_raw`.
3. Standardize: `pred_c = (pred_raw − mean(pred_raw)) / sd(pred_raw)` (z-score
   over the finetuned-checkpoint, valence-type subset; if `sd == 0`, `pred_c`
   is set to a constant 0 rather than dividing by zero).
4. `sg_c` is the ordinary `sign_c` effect code (bad/good).

**Consequence for interpretation:** the `pred_c:sg_c` coefficient in
`rq1b_moral`/`rq1b_nonmoral` is *not* "rating points per point of blame" — it
is the **difference, in rating points, between (a) the slope of intentionality
on 1 SD of standardized item-mean blame among bad items and (b) the
equivalent slope on standardized item-mean praise among good items.** The
main effect `pred_c` (not itself a declared contrast, but present in every
1b fit) is the average of those two slopes. Because the standardization
happens on the responsibility channel, not on intentionality, and channels
differ by sign, `pred_c` values are not on a shared scale across bad and good
items except in SD units — treat the reported magnitudes as effect sizes in
per-SD terms, not as calibrated 0–10 rating slopes.

**This predictor is also strongly correlated with family identity** — a fact
that turned out to matter a great deal (§10). Measured on the real data:
`corr(pred_c, its own family's mean pred_c)` is 0.77–0.96 across all six
family × valence_type cells.

## 3. Primary model: family-random-intercept LMM

`_fit_lmm` (models.py:355–413) fits `statsmodels.formula.api.mixedlm(formula,
data=df, groups=df["family_id"])`, maximum likelihood (`reml=False`), L-BFGS
optimizer (`method="lbfgs"`). All warnings are captured locally (not
converted to hard errors) so a benign `ConvergenceWarning` doesn't crash the
pipeline; a fit only counts as `converged=True` if statsmodels reports
convergence **and** no `ConvergenceWarning` was raised during fitting. If the
mixed model raises, fails to converge, or its target term is absent from the
parameter vector, `_fit_lmm` falls back to OLS with family-cluster-robust
standard errors (`cov_type="cluster"`) and records `fallback_used=True`,
`method="ols-familyRI"` — **this never happened for any of the 27 contrast
rows fit here**: every row shows `converged=True, fallback_used=False,
method=lmm-familyRI` (Table 1). The primary LMM is a random-intercept-only
model (no random slopes) — **§11 shows this is a materially wrong
simplification wherever the focal effect varies by family**, which is most
of RQ1. Domain is not modeled in the primary fit at all — domain is constant
within a family, so a `vc_formula` on domain nested in family-groups is
mathematically inert (identical SEs to plain family-RI, a documented finding
in the code, not a design choice made fresh here). Domain is instead
addressed by the separate, config-gated domain-cluster and domain-random-slope
sensitivity fits — neither was run for this pass (`--domain-sensitivity` /
`--domain-slope-sensitivity` omitted); see §13.

## 4. Confidence intervals: family-cluster percentile bootstrap, not the Wald interval

The `se` and `p_value` columns in Table 1 come from the mixedlm Wald test.
The `ci_low`/`ci_high` columns come from a **separate** procedure
(`_bootstrap_ci`, models.py): 200 resamples (`n_boot=200`, the CLI default),
each resampling whole families with replacement (a duplicated family is
relabeled `"{fid}__b{j}"` so it counts as an independent cluster in that
resample), refit via OLS, taking the 2.5/97.5 percentiles of the `n_boot`
point estimates. Every resample's RNG seed is
`sha256(base_seed, contrast, model_family, boot_idx)`, so the interval is a
pure, byte-reproducible function of its inputs (`base_seed=0` here, the CLI
default).

**As of this revision, the OLS refit formula is no longer always the raw
contrast formula.** `fit_contrast` now calls a new helper, `_bootstrap_formula`
(§10.3), which passes `spec.formula` through unchanged for every `kind`
except `lmm_1b`, where it rewrites the refit to include family fixed effects.
This was a real bug fix, not a robustness nicety: **before the fix, the RQ1b
bootstrap CI failed to bracket its own reported point estimate in 3 of 6
cells** (Table 1's original version, reproduced here for the record):

| contrast | family | LMM estimate | pre-fix bootstrap 95% CI | bracketed? |
|---|---|---|---|---|
| `rq1b_moral` | llama | 2.683 | [0.608, 2.344] | **No** |
| `rq1b_nonmoral` | mistral | −0.164 | [0.248, 0.895] | **No** |
| `rq1b_moral` | gemma | 0.222 | [−1.354, 0.041] | technically yes, but the interval is absurdly wide and its own upper bound sits below the point estimate |

The root cause (fully diagnosed in §10) is that `pred_c` correlates strongly
with family identity, so a plain pooled-OLS refit is a biased estimator for
this specific contrast shape — biased in a way that varies resample to
resample, producing a CI that isn't even centered on the right quantity. The
fix (family fixed effects in the 1b bootstrap refit only) resolves this: see
§10.3 for the diagnosis and §12/Table 1 for the corrected numbers, which now
bracket their point estimates in all 6 RQ1b cells. The RQ1a/RQ1c/RQ1d/RQ1_base
bootstrap CIs were never affected by this bug (their designs are balanced
categorical factorials, where plain OLS ≈ GLS — confirmed in §10.1) and are
unchanged by the fix.

## 5. Multiple comparisons: Holm within (model_family, RQ)

`_holm_correct` (models.py, `multipletests(..., method="holm")`) is applied
**within each (model_family, rq) group independently** — i.e., gemma's two
`RQ1_base` p-values are Holm-corrected against each other, separately from
gemma's one `RQ1a` p-value (uncorrected, `p_holm == p_value`, since there is
only one contrast in that family), separately from gemma's two `RQ1b`
p-values, and so on.

- `RQ1a` has exactly one contrast per family → `p_holm == p_value` for every
  RQ1a row.
- `RQ1_base` has two contrasts per family → e.g. mistral's
  `rq1_base_sign_x_tuning`: raw p=.2037, Holm p=.4074 — exactly double, the
  expected Holm penalty for the *larger* of two p-values when the smaller one
  is already significant.
- `RQ1b` has two contrasts per family (moral, nonmoral); all six raw
  Wald p-values are ≤1e-4 (§12 explains why the Wald p-values are themselves
  not trustworthy at face value), so Holm correction leaves them at their
  (rounded) floor.

**Consequence, more pointed after §8–§11 than it looked in the first pass:**
none of this Holm machinery corrects for the small-cluster-count overconfidence
diagnosed below. Holm correction adjusts for testing multiple hypotheses; it
does nothing about a single hypothesis's p-value being wrong because the
model understates uncertainty. A term can have a tiny, "Holm-survives"
p-value under the primary LMM and still fail a properly-sized test.

## 6. Table 1 — Primary contrast fits (family-RI LMM, post-§10.3-fix)

| contrast | RQ | family | scope | term | estimate | SE (Wald) | p | p(Holm) | 95% CI (bootstrap) | dir. expected | dir. OK | n_obs | n_groups | method |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rq1_base_sign_finetuned | RQ1_base | gemma | finetuned | sign_c | 0.322 | 0.191 | .0914 | .0914 | [−0.03, 0.77] | positive | False | 8400 | 84 | lmm-familyRI |
| rq1_base_sign_finetuned | RQ1_base | llama | finetuned | sign_c | 0.343 | 0.206 | .0953 | .0953 | [0.01, 0.78] | positive | False | 8400 | 84 | lmm-familyRI |
| rq1_base_sign_finetuned | RQ1_base | mistral | finetuned | sign_c | −0.069 | 0.102 | .4948 | .4948 | [−0.29, 0.09] | positive | False | 8400 | 84 | lmm-familyRI |
| rq1_base_sign_x_tuning | RQ1_base | gemma | both | sign_c:tuning_c | 0.452 | 0.015 | <1e-4 | <1e-4 | [0.11, 0.80] | positive | **True** | 16800 | 84 | lmm-familyRI |
| rq1_base_sign_x_tuning | RQ1_base | llama | both | sign_c:tuning_c | 0.450 | 0.023 | <1e-4 | <1e-4 | [0.10, 0.83] | positive | **True** | 16800 | 84 | lmm-familyRI |
| rq1_base_sign_x_tuning | RQ1_base | mistral | both | sign_c:tuning_c | −0.011 | 0.009 | .2037 | .4074 | [−0.22, 0.19] | positive | False | 16800 | 84 | lmm-familyRI |
| rq1a_sign_x_valence_type | RQ1a | gemma | finetuned | sign_c:vt_c | 0.092 | 0.359 | .7980 | .7980 | [−0.73, 0.85] | positive | False | 8400 | 84 | lmm-familyRI |
| rq1a_sign_x_valence_type | RQ1a | llama | finetuned | sign_c:vt_c | 0.629 | 0.368 | .0875 | .0875 | [−0.07, 1.40] | positive | False | 8400 | 84 | lmm-familyRI |
| rq1a_sign_x_valence_type | RQ1a | mistral | finetuned | sign_c:vt_c | 0.263 | 0.124 | .0344 | .0344 | [−0.03, 0.54] | positive | **True** | 8400 | 84 | lmm-familyRI |
| rq1b_moral | RQ1b | gemma | finetuned | pred_c:sg_c | 0.222 | 0.050 | <1e-4 | <1e-4 | **[−1.10, 1.05]** | positive | **True** | 4200 | 42 | lmm-familyRI |
| rq1b_moral | RQ1b | llama | finetuned | pred_c:sg_c | 2.683 | 0.165 | <1e-4 | <1e-4 | **[1.75, 3.76]** | positive | **True** | 4200 | 42 | lmm-familyRI |
| rq1b_moral | RQ1b | mistral | finetuned | pred_c:sg_c | 1.301 | 0.052 | <1e-4 | <1e-4 | **[0.92, 1.78]** | positive | **True** | 4200 | 42 | lmm-familyRI |
| rq1b_nonmoral | RQ1b | gemma | finetuned | pred_c:sg_c | 0.443 | 0.052 | <1e-4 | <1e-4 | **[−0.25, 1.22]** | positive | **True** | 4200 | 42 | lmm-familyRI |
| rq1b_nonmoral | RQ1b | llama | finetuned | pred_c:sg_c | 1.947 | 0.084 | <1e-4 | <1e-4 | **[1.11, 3.51]** | positive | **True** | 4200 | 42 | lmm-familyRI |
| rq1b_nonmoral | RQ1b | mistral | finetuned | pred_c:sg_c | −0.164 | 0.024 | <1e-4 | <1e-4 | **[−0.58, 0.05]** | positive | False | 4200 | 42 | lmm-familyRI |
| rq1c_evocativeness_x_sign | RQ1c | gemma | finetuned | evoc_c:sign_c | −0.173 | 0.015 | <1e-4 | <1e-4 | [−0.32, −0.04] | two-sided | True | 8400 | 84 | lmm-familyRI |
| rq1c_evocativeness_x_sign | RQ1c | llama | finetuned | evoc_c:sign_c | 0.102 | 0.036 | .0044 | .0044 | [−0.09, 0.35] | two-sided | True | 8400 | 84 | lmm-familyRI |
| rq1c_evocativeness_x_sign | RQ1c | mistral | finetuned | evoc_c:sign_c | 0.060 | 0.008 | <1e-4 | <1e-4 | [−0.03, 0.14] | two-sided | True | 8400 | 84 | lmm-familyRI |
| rq1c_typicality_x_sign | RQ1c | gemma | finetuned | typ_c:sign_c | −0.415 | 0.014 | <1e-4 | <1e-4 | [−0.62, −0.24] | two-sided | True | 8400 | 84 | lmm-familyRI |
| rq1c_typicality_x_sign | RQ1c | llama | finetuned | typ_c:sign_c | −0.177 | 0.025 | <1e-4 | <1e-4 | [−0.58, 0.18] | two-sided | True | 8400 | 84 | lmm-familyRI |
| rq1c_typicality_x_sign | RQ1c | mistral | finetuned | typ_c:sign_c | −0.195 | 0.006 | <1e-4 | <1e-4 | [−0.26, −0.13] | two-sided | True | 8400 | 84 | lmm-familyRI |
| rq1d_neu_offset | RQ1d | gemma | finetuned | Intercept | 1.547 | 0.065 | <1e-4 | <1e-4 | [1.43, 1.70] | two-sided | True | 2100 | 21 | lmm-familyRI |
| rq1d_neu_offset | RQ1d | llama | finetuned | Intercept | 2.645 | 0.065 | <1e-4 | <1e-4 | [2.53, 2.77] | two-sided | True | 2100 | 21 | lmm-familyRI |
| rq1d_neu_offset | RQ1d | mistral | finetuned | Intercept | 1.820 | 0.026 | <1e-4 | <1e-4 | [1.77, 1.88] | two-sided | True | 2100 | 21 | lmm-familyRI |
| rq1d_typicality_within_neu | RQ1d | gemma | finetuned | typ_c | −0.374 | 0.008 | <1e-4 | <1e-4 | [−0.44, −0.31] | two-sided | True | 2100 | 21 | lmm-familyRI |
| rq1d_typicality_within_neu | RQ1d | llama | finetuned | typ_c | 0.601 | 0.015 | <1e-4 | <1e-4 | [0.43, 0.83] | two-sided | True | 2100 | 21 | lmm-familyRI |
| rq1d_typicality_within_neu | RQ1d | mistral | finetuned | typ_c | 0.293 | 0.008 | <1e-4 | <1e-4 | [0.25, 0.33] | two-sided | True | 2100 | 21 | lmm-familyRI |

Bolded RQ1b CIs are the post-fix values (all 6 now bracket their point
estimate). All 27 rows: `converged=True`, `fallback_used=False`. **Do not
read the Wald p-values in this table as calibrated** — §8 and §11 show most
of them are dramatically overconfident; this table records the primary
model's own output faithfully, not a final verdict.

`n_obs`/`n_groups` reflect the subset each contrast fits on: RQ1_base's
`sign_x_tuning` term pools pretrained+finetuned (16,800 = 84 families ×
200 obs/family, both tuning states); RQ1b subsets to one valence_type (42
families = 21 MB+MG or 21 NMB+NMG); RQ1d subsets to NEU only (21 families).

## 7. Sensitivity analyses (as originally run)

### 7.1 Set-cluster (`--set-sensitivity`)

`set_id` is derived by stripping the valence token out of `family_id` — the
five valence-siblings (MB/MG/NMB/NMG/NEU) of one authored storyline share a
`set_id`. `RQ1_base`/`RQ1a` are, under the primary family-RI model, **fully
between-family** variance (`sign` and `valence_type` are both constant within
a family), so family-RI clustering absorbs the entire signal as noise on
those two RQs specifically. Refitting with `groups=set_id` recovers the
five-way matched structure.

**This check "passes" (point-estimate-stable) for `RQ1_base`, `RQ1a`, `RQ1c`,
`RQ1d`** — every point estimate in `set_sensitivity.csv` is identical to its
`contrast_table.csv` counterpart to at least 6 decimal places, with only the
SE and p-value changing (e.g. RQ1a gemma's SE drops from 0.359 to 0.029, a
>12x reduction, flipping the family-RI p=.798 to p=.0014 under set-clustering).
**This point-estimate stability is necessary but not sufficient for trusting
the resulting p-value** — §8 shows the set-cluster p-values themselves don't
survive a properly-sized small-G test (G=21 sets), because the *asymptotic*
theory behind the set-cluster Wald SE is exactly as unreliable at G=21 as the
family-RI Wald SE is unreliable elsewhere. Point-estimate stability rules out
one failure mode (the clustering variable absorbing the effect); it does not
rule out the other (the asymptotic SE being wrong at small G).

**This check fails point-estimate-stability outright for `RQ1b`** — every
point estimate changes materially under set-clustering, two flip sign
entirely (gemma nonmoral 0.443→−0.266; mistral nonmoral −0.164→+0.129). §10
diagnoses the mechanism: `set_id` groups a MUCH coarser unit (2 families per
set within one valence_type) than `family_id`, and since `pred_c` correlates
strongly with family identity, changing the clustering granularity changes
which variance the GLS weighting attributes to "cluster" vs. "the covariate
of interest." **The RQ1b set-cluster numbers in `set_sensitivity.csv` remain
not usable for anything.**

### 7.2 Ordinal distributional sensitivity (always run)

`OrderedModel` (statsmodels, logit link, BFGS, fixed effects only — no random
intercept) is the documented inversion of WO-8's stated CLMM-primary
preference. Full table and two flagged disagreements (mistral's
`sign_x_tuning`, llama's `typ_x_sign`, mistral's degenerate NEU-typicality
fit) are unchanged from the first pass — **and §8/§11 now independently
corroborate both flagged disagreements** using completely different methods
(wild cluster bootstrap and family-random-slope LMMs), which is reassuring
that they're real rather than artifacts of the ordinal model's lack of
random effects. See §12 for the reconciled picture.

## 8. Wild cluster bootstrap (Cameron–Gelbach–Miller 2008)

**Motivation.** RQ1 clusters on 21–84 families depending on the contrast.
That is well below the ~40–50-cluster rule of thumb where asymptotic
cluster-robust standard errors (the mixedlm Wald SE, and the plain
percentile bootstrap in §4) are known to under-cover (Cameron, Gelbach &
Miller 2008; Cameron & Miller 2015, *A Practitioner's Guide to Cluster-Robust
Inference*). RQ1b/RQ1d bottom out at G=21–42. A **wild cluster bootstrap**
gives a finite-sample-valid test that doesn't rely on the number of clusters
being asymptotically large.

**Procedure**, implemented from scratch (not yet in the pipeline):

1. Fit the *restricted* model (the focal term's coefficient constrained to
   zero, by dropping that column from the design matrix) via OLS, recording
   its fitted values and residuals.
2. For `B=1999` iterations: draw one Rademacher weight (±1, uniform) per
   cluster; construct `y* = fitted_restricted + w_cluster · resid_restricted`
   — the null-imposed synthetic outcome. Refit the *full* model (OLS,
   cluster-robust SE) on `y*` against the unperturbed design matrix; record
   the cluster-robust t-statistic for the focal term.
3. p-value = the fraction of bootstrap |t*| at least as extreme as the
   observed cluster-robust |t| on the real data.

Clustering unit matches each contrast's actual experimental unit: `set_id`
(G=21) for RQ1a, `family_id` (G=84) for RQ1_base/RQ1c, `family_id` (G=21) for
RQ1d, `family_id` (G=42) for RQ1b (using the §10.3 family-fixed-effects
specification, not plain pooled OLS — see §10).

**Validation: large-G contrasts agree with the primary model; small-G
contrasts often don't.**

| contrast | family | LMM p (asymptotic) | WCB p (G shown) |
|---|---|---|---|
| rq1_base_sign_x_tuning | gemma | 5×10⁻²⁰³ | .009 (G=84) |
| rq1_base_sign_x_tuning | llama | 4×10⁻⁸⁴ | .023 (G=84) |
| rq1_base_sign_x_tuning | mistral | .204 | .919 (G=84) |
| rq1c_typicality_x_sign | gemma | 3×10⁻¹⁹³ | **<.001** (G=84) |
| rq1c_typicality_x_sign | llama | 1×10⁻¹² | **.403** (G=84) |
| rq1c_typicality_x_sign | mistral | 8×10⁻²³¹ | **<.001** (G=84) |
| rq1c_evocativeness_x_sign | gemma | 5×10⁻³² | **.030** (G=84) |
| rq1c_evocativeness_x_sign | llama | .0044 | **.374** (G=84) |
| rq1c_evocativeness_x_sign | mistral | 3×10⁻¹⁵ | **.170** (G=84) |
| rq1d_neu_offset | all 3 | <1e-4 | **.000** (G=21, 0/1999 draws exceeded observed) |
| rq1d_typicality_within_neu | all 3 | <1e-4 | **.000** (G=21) |
| rq1a_sign_x_valence_type (baseline, no severity, full 84-family sample) | gemma | .798 (family-RI) / .0014 (set-cluster asymptotic) | **.512** (G=21, set-clustered) |
| rq1a_sign_x_valence_type (baseline) | llama | .088 / <.0001 | **.003** (G=21) |
| rq1a_sign_x_valence_type (baseline) | mistral | .034 / <.0001 | **<.0001** (G=21) |
| rq1b_moral (family-FE refit, §10.3) | gemma | <1e-4 | **.698** (G=42) |
| rq1b_moral | llama | <1e-4 | **<.0001** (G=42) |
| rq1b_moral | mistral | <1e-4 | **<.0001** (G=42) |
| rq1b_nonmoral | gemma | <1e-4 | **.337** (G=42) |
| rq1b_nonmoral | llama | <1e-4 | **.0005** (G=42) |
| rq1b_nonmoral | mistral | <1e-4 | **.255** (G=42) |

Even at G=84 — not a "small" cluster count by the usual rule of thumb — WCB
p-values are routinely orders of magnitude larger than the asymptotic LMM
Wald p-value (e.g. gemma's `sign_x_tuning`: 5×10⁻²⁰³ vs. .009). §11 shows this
gap is explained by the primary model's random-*intercept*-only
specification, not by WCB being overly conservative. RQ1d is the one RQ that
survives WCB overwhelmingly in every cell — the strongest, most literally
undeniable result in the release.

## 9. Severity-covariate refit of RQ1a

**Motivation.** `docs/RQ1_MECHANISM_ANALYSIS_v1.1.md` documents that
reviewer-rated `severity` differs sharply between moral and nonmoral items
(MB mean 7.04 vs. NMB mean 1.62; MG 1.90 vs. NMG 0.86) — a confound baked
into the stimulus set, not a sampling artifact. This tests whether RQ1a's
`sign_c:vt_c` interaction survives controlling for it.

**Procedure.** Refit `rating ~ sign_c * vt_c + severity_c` (family-mean
severity from `curated_v1.1.csv`, grand-mean centered) under the same
set-clustered LMM RQ1a's headline number uses, then re-run WCB (G=21) on
both the baseline and severity-adjusted models for an apples-to-apples
comparison (one family, WORK-MG-02, has no curation severity record and is
dropped from *both* fits to keep the compared sample identical — 83 of 84
families, still 21 sets). **This baseline column is therefore not identical
to §8's full-84-family baseline row above** (dropping one family shifts the
point estimate and p slightly: gemma .512→.640, llama .003→.0045, mistral
<.0001→.001) — the qualitative pattern (llama/mistral survive, gemma doesn't)
is the same either way; only cite the exact decimals from the sample they
were computed on (script `04_rq1a_severity_covariate.py` vs.
`03_rq1a_baseline_wcb.py` in `analysis/rq1_v1_1_robustness/`).

| family | baseline β (LMM) | baseline WCB p (severity-complete subsample) | +severity β (LMM) | +severity WCB p |
|---|---|---|---|---|
| gemma | +0.065 | .640 | +0.280 | **.316** |
| llama | +0.650 | **.0045** | +1.640 | **.459** |
| mistral | +0.250 | **.001** | **−0.064** (sign flip) | **.203** |

**None of the three families' RQ1a interaction survives both a properly-sized
small-G test and severity adjustment simultaneously.** Llama and mistral
survive the baseline WCB alone; none survive once severity is in the model.
Mistral's coefficient actually reverses sign once severity is controlled for
(and is not significant either way at that point). This directly weakens
RQ1a's headline: what looked like "moral badness specifically, not just any
negative valence" is at least partly attributable to moral items being more
severe, and the interaction that would isolate the "purely moral" component
doesn't clear a properly-sized bar once you try to isolate it.

**This does not fully overturn the separate, direct moral-vs-nonmoral split
test** in `docs/RQ1_MECHANISM_ANALYSIS_v1.1.md` §1 (fitting the sign effect
separately within the moral-only and nonmoral-only subsets, rather than as a
pooled interaction). Re-run through WCB (`family_id` clustering, G=42, no
severity adjustment yet):

| family | moral-only sign effect, WCB p | nonmoral-only sign effect, WCB p |
|---|---|---|
| gemma | **.021** | .436 |
| llama | **.0005** | .918 |
| mistral | .408 | .060 |

This *does* survive for gemma and llama — a real, if narrower, piece of
evidence that moral badness (not nonmoral badness) drives the sign effect in
those two families. The tension between this result and the failed RQ1a
interaction test is genuine and not yet resolved: a split-sample test and a
pooled-interaction test are answering closely related but not identical
questions, and can behave differently in finite, clustered samples,
especially when (as here) they're estimated at different cluster
granularities (G=42 family-clustered vs. G=21 set-clustered) and the split
test hasn't itself been adjusted for severity. Read §12 for how these two
pieces of evidence are reconciled in the current write-up.

## 10. The RQ1b pooled-OLS bug: diagnosis and fix

### 10.1 The diagnostic: RE vs. pooled OLS vs. fixed effects

The first-pass wild cluster bootstrap for RQ1b (§8, `pred_c:sg_c`, using
plain pooled OLS as the refit engine, matching the pipeline's own `_bootstrap_ci`)
produced point estimates that disagreed wildly with the primary mixedlm
estimate, occasionally flipping sign (e.g. gemma-moral: LMM +0.222 vs. pooled
OLS **−0.589**). That is not bootstrap noise — the plain, single, non-resampled
pooled-OLS fit on the real data disagrees with the mixedlm fit by construction.
A three-way comparison (random-effects/MixedLM, pooled OLS with no family
term at all, and OLS with family fixed effects — a Hausman-style diagnostic)
resolves why:

| family | vt | RE (MixedLM) | pooled OLS (no family term) | FE (family dummies) |
|---|---|---|---|---|
| gemma | moral | 0.2223 | **−0.5890** | 0.2311 |
| gemma | nonmoral | 0.4433 | 0.5997 | 0.4262 |
| llama | moral | 2.6832 | **1.2083** | 2.7221 |
| llama | nonmoral | 1.9467 | 2.1927 | 1.9361 |
| mistral | moral | 1.3013 | **2.0978** | 1.2968 |
| mistral | nonmoral | −0.1645 | **0.6269** | −0.1758 |

**FE and RE agree closely in every cell (within ~5%). Pooled OLS diverges
substantially in every cell, and flips sign in three.** This is the textbook
signature of a regressor (`pred_c`) correlated with the random/fixed effect
(family identity) — an omitted between-family confound (plausibly the same
severity/valence-intensity driver documented for RQ1a) shifts both an item's
judged blameworthiness and its intentionality rating together, and pooled OLS
attributes that shared between-family covariation to the `pred_c:sg_c` slope
instead of to the family effect. RE (MixedLM) and FE both correctly separate
within-family covariation (the thing `pred_c:sg_c` is supposed to measure)
from this confound, which is why they agree; pooled OLS doesn't, which is why
it doesn't. **This also confirms the original LMM point estimates for RQ1b
were fine all along** — it was the bootstrap's *refit engine*, not the
reported estimate, that was broken.

### 10.2 A genuine unresolved disagreement: mistral, nonmoral

One cell doesn't reconcile cleanly even after the fix. The family-random-slope
check (§11) gives mistral-nonmoral a *significant, larger-magnitude* negative
estimate (−0.918, p=.0021) where the family-FE WCB (§8) found no significant
effect at all (p=.255). Both methods are, in principle, more defensible than
plain pooled OLS, but they make different assumptions (FE is robust to any
family-level confounding by construction; a random slope assumes the
family-level slopes are drawn independently of the family-level confound,
which is questionable in exactly the way RE's intercept assumption was
questionable here). Given the demonstrated endogeneity in this predictor, the
FE-based result is the more conservative and defensible of the two — treat
mistral's nonmoral "reversal" as genuinely unresolved, not confirmed in
either direction, until a joint/latent-variable model settles it (§13).

### 10.3 The code fix

`src/knobe/analysis/models.py` now has a `_bootstrap_formula(spec)` helper,
called from `fit_contrast` before `_bootstrap_ci`. For every contrast kind
except `lmm_1b` it returns `spec.formula` unchanged (those designs are
balanced categorical factorials where pooled OLS ≈ GLS, confirmed by the
point-estimate-identical set-cluster/family-RI comparison in §7.1 for
RQ1_base/RQ1a/RQ1c/RQ1d). For `lmm_1b` contrasts it rewrites
`"... pred_c * sg_c"` to `"... pred_c + pred_c:sg_c + C(family_id)"` — adding
family fixed effects and dropping the now-collinear bare `sg_c` main effect
(sign is constant within a family/valence, so once family dummies are in the
model, `sg_c` is perfectly explained by them; leaving it in produces a
rank-deficient design and degenerate standard errors — confirmed by trial:
including it gave nonsensical near-zero t-statistics). `pred_c:sg_c` stays
identified because each family's fixed `sg_c` value multiplies that family's
*own* within-family `pred_c` variation, and families differ in which `sg_c`
value they carry.

Regenerating `results/v1.1/paper/` with the fix gives RQ1b bootstrap CIs that
bracket their point estimates in all 6 cells (Table 1, §6) — the pathology
in §4's original table is gone. Two new tests
(`test_1b_bootstrap_ci_biased_by_pooled_ols_under_family_confound`,
`test_1b_bootstrap_ci_family_fe_fix_brackets_estimate`, plus a governance
test on `_bootstrap_formula`'s formula-shape assumption) were added to
`tests/test_analysis.py`; all 33 tests in the suite pass.

## 11. Family random slopes: quantifying the constant-slope misspecification

**Motivation.** The primary LMM assumes each focal effect (sign, typicality,
evocativeness, tuning, the 1b slope) is *constant* across families — only the
intercept varies. §8's large gap between LMM and WCB p-values at G=84 (where
cluster count alone shouldn't be the problem) suggests this assumption is
false and is producing understated SEs wherever it's false.

**Procedure.** For every term that varies *within* a family (tuning_c in
RQ1_base; typ_c and evoc_c in RQ1c; pred_c in RQ1b — sign_c and vt_c do NOT
vary within family and so cannot support a family random slope at all, which
is exactly why RQ1a has no family-level version of this check, only the
set-level check in §7.1/§9), refit with `re_formula="~<term>"` (random
intercept **and slope** for that term, per family) and compare the focal
interaction's standard error to the random-intercept-only primary.

| contrast | family | RI-only SE | +slope SE | SE inflation | RI-only p | +slope p |
|---|---|---|---|---|---|---|
| rq1_base sign×tuning | gemma | 0.015 | 0.180 | **12.1x** | 5×10⁻²⁰³ | **.012** |
| rq1_base sign×tuning | llama | 0.023 | 0.201 | **8.7x** | 4×10⁻⁸⁴ | **.025** |
| rq1_base sign×tuning | mistral | 0.009 | 0.112 | **12.5x** | .204 | .919 |
| rq1c typ×sign | gemma | 0.014 | 0.106 | **7.6x** | 3×10⁻¹⁹³ | **9×10⁻⁵** |
| rq1c typ×sign | llama | 0.025 | 0.207 | **8.3x** | 1×10⁻¹² | **.394** |
| rq1c typ×sign | mistral | 0.006 | 0.034 | **5.7x** | 8×10⁻²³¹ | **9×10⁻⁹** |
| rq1c evoc×sign | gemma | 0.015 | 0.079 | **5.4x** | 5×10⁻³² | **.029** |
| rq1c evoc×sign | llama | 0.036 | 0.112 | **3.1x** | .0044 | .361 |
| rq1c evoc×sign | mistral | 0.008 | 0.042 | **5.5x** | 3×10⁻¹⁵ | .151 |

**Every single cell inflates 3–12x, and in every case the point estimate is
numerically identical between the RI-only and +slope models** (statsmodels
keeps the fixed-effect estimate fixed when only the random-effects structure
changes here) — this is a pure uncertainty correction, not a different
estimate. It **independently reproduces the WCB p-values in §8 to within
~.02 in most cells** (llama typ×sign: WCB p=.403, random-slope p=.394; gemma
evoc×sign: WCB p=.030, random-slope p=.029) — two methods with essentially no
shared machinery (a resampling test vs. a different parametric model)
converging on the same answer is strong evidence this is a real
misspecification, not an artifact of either method.

RQ1b's version of this check is confounded by the same family-correlated-
predictor issue as §10 (a random slope on `pred_c` is itself vulnerable to
the same endogeneity a fixed effect avoids), so its numbers are reported in
§10.2 as a disagreement to resolve, not added to this table as a clean
result.

**Conclusion: the family-random-intercept-only primary model materially
understates uncertainty for essentially every RQ1 contrast where the focal
term varies within family.** This is not specific to small G — it shows up
at G=84 exactly as it does at G=21 or G=42. Promoting family random slopes
to (at least) a standard sensitivity fit, alongside the existing
domain-random-slope sensitivity analysis, is now a clear next step (§13).

### 11.1 Minimum detectable effect: how underpowered is this design?

Given each contrast's *properly-sized* cluster-robust SE (§8's WCB SE, not
the understated Wald SE) and cluster count, the standard cluster-design MDE
formula (Bloom 2006-style) gives the smallest true effect this design could
detect 80% of the time at α=.05: `MDE = SE × (t_{1−α/2,df} + t_{power,df})`,
`df = G − 2`. This reframes every non-significant WCB result as either "a
genuine null" or "underpowered at this cluster count," which a p-value alone
doesn't distinguish (`analysis/rq1_v1_1_robustness/09_minimum_detectable_effect.py`):

| contrast | family | observed \|effect\| | MDE | observed ≥ MDE? |
|---|---|---|---|---|
| rq1_base_sign_x_tuning | gemma | 0.452 | 0.514 | No (survives WCB anyway — MDE is a design property, not a guarantee) |
| rq1_base_sign_x_tuning | llama | 0.450 | 0.574 | No |
| rq1_base_sign_x_tuning | mistral | 0.011 | 0.319 | No — consistent with a genuine null, not just underpowered |
| rq1c_typicality_x_sign | gemma | 0.415 | 0.303 | **Yes** |
| rq1c_typicality_x_sign | llama | 0.177 | 0.591 | No — this design would need a ~3.3x larger effect to reliably detect one |
| rq1c_typicality_x_sign | mistral | 0.195 | 0.097 | **Yes** |
| rq1c_evocativeness_x_sign | gemma/llama/mistral | 0.173/0.102/0.060 | 0.226/0.319/0.120 | No / No / No |
| rq1d_neu_offset | all 3 | 1.55–2.65 | 0.08–0.20 | **Yes, by a wide margin** |
| rq1d_typicality_within_neu | all 3 | 0.29–0.60 | 0.06–0.30 | **Yes** |
| rq1a_sign_x_valence_type | gemma/llama/mistral | 0.092/0.629/0.263 | 0.397/0.723/0.200 | No / No / **Yes** |
| rq1b_moral | gemma/llama/mistral | 0.231/2.722/1.297 | 1.572/1.462/0.657 | No / **Yes** / **Yes** |
| rq1b_nonmoral | gemma/llama/mistral | 0.431/1.937/0.176 | 1.042/1.656/0.401 | No / **Yes** / No |

The "observed ≥ MDE" column and the WCB significance verdict (§8, §10, §12)
agree everywhere except `rq1_base_sign_x_tuning` for gemma/llama, where the
observed effect is technically just under this particular MDE estimate yet
still clears the WCB test — MDE and a single realized bootstrap p-value are
related but not the same statistic (MDE answers "what effect size would this
design reliably detect," the WCB p-value answers "is this particular observed
effect surprising under the null"), so occasional near-boundary disagreements
like this are expected, not a contradiction. The useful reading is the
*non-significant* cells: gemma's `rq1c_typicality_x_sign`... [not applicable,
gemma survives] — rather, `rq1c_typicality_x_sign` for llama (observed 0.177
vs. MDE 0.591) and every `rq1c_evocativeness_x_sign` cell are consistent with
this design simply not being powered to detect effects that size at these
cluster counts, which is a different, more actionable conclusion than "no
effect exists" — it argues for more families/sets in a future release
specifically for these contrasts, not for abandoning the underlying question.

## 12. Summary: what to trust, per contrast family (revised)

| RQ | primary LMM (Wald) | WCB / random-slope (properly sized) | net verdict |
|---|---|---|---|
| RQ1_base sign×tuning | gemma/llama "p≈0"; mistral null | gemma p=.009–.012, llama p=.023–.025 (survive, more modestly); mistral null confirmed (p=.92) by WCB, **but the ordinal check disagrees in sign** (§7.2) — unresolved | gemma/llama: real, smaller than it looked. Mistral's null: probably real, one open thread. |
| RQ1a sign×valence_type | "significant in all 3" under set-clustering (asymptotic) | **None of the 3 survive WCB + severity adjustment together**; the baseline (no severity) survives WCB for llama/mistral only | The pooled-interaction test does not support a robust, severity-independent moral-specific effect in any family. |
| RQ1a direct split (moral-only vs. nonmoral-only sign effect, mechanism doc §1) | gemma/llama moral p<.02, nonmoral n.s. | **Survives WCB** for gemma (.021) and llama (.0005); not severity-adjusted yet | The most defensible surviving evidence for "moral, not just negative" — in gemma/llama only. |
| RQ1b moral | "p≈0" all 3 | llama/mistral survive WCB (p<.0001 both); **gemma does not** (p=.698) | Only llama and mistral show a real Hindriks-style responsibility effect on moral items. |
| RQ1b nonmoral | "p≈0" all 3 | llama survives (p=.0005); gemma and mistral do not (p=.337, .255) | Only llama's nonmoral effect is robust; mistral's "reversal" is unresolved (§10.2), not confirmed. |
| RQ1c typicality×sign | "p≈0" all 3 | gemma/mistral survive (p<.001 both); **llama does not** (p=.403, confirmed by both WCB and random-slope) | The release's most-touted "most robust effect" is robust in 2 of 3 families, not 3. |
| RQ1c evocativeness×sign | "p≈0" (mistral), significant (all 3) | **only gemma survives, marginally** (p=.030); llama and mistral do not (p=.374, .170) | Evocativeness×sign is weak evidence at best, and its construct validity is independently in doubt (mechanism doc §4: the manipulation doesn't move self-reported affect). |
| RQ1d neu_offset | "p≈0" all 3 | **Survives overwhelmingly, all 3** (WCB p=.000, 0/1999 draws exceeded) | The most robust finding in the entire release. |
| RQ1d typicality_within_neu | "p≈0" all 3 | **Survives overwhelmingly, all 3** (WCB p=.000) | Equally robust; direction differs by family (already noted in the mechanism doc), which is itself informative, not a weakness. |

## 13. What would strengthen this further

1. **Resolve the mistral-nonmoral RQ1b disagreement (§10.2)** with a joint
   latent-variable / errors-in-variables model (e.g. a Bayesian multilevel
   model treating the item's blame mean and intentionality as two indicators
   of a shared latent construct) rather than choosing between FE and
   random-slope by intuition.
2. **Promote family random slopes to a standard, always-reported sensitivity
   fit** (parallel to the existing domain-random-slope sensitivity), given
   §11's finding that they matter for essentially every RQ1 contrast, not a
   special case.
3. **Resolve the RQ1_base mistral sign×tuning ordinal-vs-everything-else
   disagreement** (§7.2, §12) — the one thread WCB and random-slopes didn't
   settle, since both corroborate the LMM's null while only the (less
   trustworthy, no-random-effects) ordinal model disagrees. Worth a real
   mixed cumulative-link model (R's `ordinal::clmm` or a Bayesian ordinal fit
   in `brms`) rather than statsmodels' fixed-effects-only `OrderedModel`.
4. **Domain-cluster and domain-random-slope sensitivity fits** (still not run
   for this release, `--domain-sensitivity` / `--domain-slope-sensitivity`);
   given how much family-level heterogeneity §11 found, domain-level
   generalization claims need the same scrutiny.
5. **A severity-covariate refit of the direct moral/nonmoral split test**
   (§9's second table) — the pooled RQ1a interaction was tested with severity
   control, the split test wasn't yet; needed to know if the one surviving
   piece of moral-specificity evidence also survives.
6. **Wild-cluster-bootstrap and random-slope checks should become first-class
   pipeline sensitivity analyses** (like `--set-sensitivity` /
   `--domain-slope-sensitivity`) rather than one-off exploratory scripts —
   everything in §8–§11 was run outside `knobe analyze` and should be
   reproducible via the CLI before being cited in any future writeup.

— §1–§7 generated 2026-08-10 from `knobe analyze`
(`--contrast-names rq1_base_sign_finetuned,rq1_base_sign_x_tuning,rq1a_sign_x_valence_type,rq1b_moral,rq1b_nonmoral,rq1c_typicality_x_sign,rq1c_evocativeness_x_sign,rq1d_neu_offset,rq1d_typicality_within_neu --set-sensitivity --logit-fallback <all 6 model_keys> --no-figures`),
output in `results/v1.1/paper/`, regenerated after the §10.3 fix. §8–§11 are
exploratory analyses against the same underlying data — not yet pipeline
artifacts (per item 6 above) but fully committed, reproducible scripts under
`analysis/rq1_v1_1_robustness/` (numbered `01`–`09`, one script per table in
these two sections plus the MDE analysis in §11.1; `config.yaml` records every
parameter — seeds, α, power, clustering column per contrast; small output
CSVs live in `analysis/rq1_v1_1_robustness/outputs/`). Run
`.venv/bin/python analysis/rq1_v1_1_robustness/0N_*.py` from the repo root
(after unpacking `results/v1.1/results_all.jsonl` per `knobe/README.md`) to
regenerate any table in §8–§11.
