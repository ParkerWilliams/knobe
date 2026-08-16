# Analysis log

Append-only provenance log per `CLAUDE.md` section 5: one line per completed
analysis run, so any number in a writeup can be traced back to exactly how
it was produced. Format:

    YYYY-MM-DD | script/command | key params | one-line outcome | commit hash

Backfilled entries below are reconstructed from the 2026-08-10 session
history rather than logged live as each run happened — going forward, add
the line at the time of the run, not after the fact.

## Session summary — 2026-08-10

Per `CLAUDE.md` section 6 (end-of-session file-change summary). 27 commits,
`ed6e031..a087185`, all pushed to `origin/main`.

**Modified** (3 files): `src/knobe/analysis/models.py` (the `_bootstrap_formula`
fix — RQ1b's bootstrap CI used a biased pooled-OLS refit), `tests/test_analysis.py`
(regression tests for that fix), `.gitignore` (excepted `results/ANALYSIS_LOG.md`
from the blanket `results/*` rule).

**Created** (55 files): `CLAUDE.md` (moved from the outer repo root into
`knobe/`); 5 docs (`RQ1_MECHANISM_ANALYSIS_v1.1.md` and
`RQ1_STATISTICAL_METHODS_v1.1.md` — both full revisions, not first drafts;
`SEVERITY_MORALIZATION_BACKGROUND.md`; `SEVERITY_PILOT_PLAN.md`;
`OUTSTANDING_STATISTICAL_ANALYSIS.md`); this log itself; and 48 files under
`analysis/` — 20 numbered scripts plus `lib.py`/`config.yaml`/`README.md` in
`analysis/rq1_v1_1_robustness/`, and 3 files (2 scripts + README, not yet
run — needs API access this environment doesn't have) in
`analysis/severity_wording_check/`.

**Narrative arc**: started from a full v1.1 pull and RQ1a-1d analysis, then
a small-cluster-robustness re-analysis (wild cluster bootstrap, family
random slopes, minimum-detectable-effect/power planning) that overturned
several first-pass headline claims and caught the same pooled-OLS bootstrap
bias independently twice (RQ1b's `pred_c`, RQ1a's `severity_c`). The
session's last thread — severity vs. moral category for RQ1a — initially
proceeded through several statistical routes (severity-covariate refit, a
label-vs-severity AIC comparison, a direct dose-response test) that each
produced ambiguous or overstated results; review caught two real
overclaims (an equivalence-test problem dressed as a null, and an
uninformative internal ranking from a family with no effect on any
predictor) before the actual resolution arrived from a direct manipulation
check, not a model: moral-bad and nonmoral-bad items were never
severity-matched at norming (0 of 21 storylines within 1 severity point of
each other), while moral-good/nonmoral-good pairs are fine. That reframes
RQ1a as a stimulus-design confound specific to the bad-valence pairs, not a
statistically-resolvable question on the existing data — motivating the
two-phase severity pilot (`SEVERITY_PILOT_PLAN.md`) scoped for the next
session.

**Known gaps carried forward**: see "Known gaps" and "Planned, scripted,
blocked on external resource" below, and `OUTSTANDING_STATISTICAL_ANALYSIS.md`
for the fuller status check against the original 12-item statistical review.

2026-08-10 | `knobe analyze` (RQ1a-1d contrast set) | `--contrast-names rq1_base_sign_finetuned,rq1_base_sign_x_tuning,rq1a_sign_x_valence_type,rq1b_moral,rq1b_nonmoral,rq1c_typicality_x_sign,rq1c_evocativeness_x_sign,rq1d_neu_offset,rq1d_typicality_within_neu --logit-fallback <all 6 model_keys> --no-figures` | primary family-RI LMM fits for RQ1a-1d, reproduced the `MAIN_RUN_WRITEUP_v1.1.md` numbers | ed6e031 (pre-existing pipeline, no local changes yet)
2026-08-10 | `knobe analyze` (same, + `--set-sensitivity`) | adds `set_id`-clustered refit | RQ1a "significant in all 3 families under set-clustering" headline reproduced from the asymptotic Wald p-values (later found in the WCB re-analysis not to survive a properly-sized test) | ed6e031
2026-08-10 | `knobe analyze` (regenerated, same flags) | rerun after the `_bootstrap_formula` fix | RQ1b bootstrap CIs now bracket their point estimate in all 6 cells (previously 3 of 6 failed to) | 8338f92
2026-08-10 | `analysis/rq1_v1_1_robustness/01_rq1_base_and_rq1c_wcb.py` | B=1999, cluster=family_id (G=84) | gemma/llama `sign_x_tuning` survive (p=.009/.023); mistral null confirmed; llama's `typ_x_sign` and `evoc_x_sign` fail WCB despite p≈0 under the asymptotic Wald test | e58f9bd
2026-08-10 | `analysis/rq1_v1_1_robustness/02_rq1d_wcb.py` | B=1999, cluster=family_id (G=21) | all 6 RQ1d cells survive overwhelmingly (p_wcb=.000, 0/1999 draws exceeded the observed statistic) | e58f9bd
2026-08-10 | `analysis/rq1_v1_1_robustness/03_rq1a_baseline_wcb.py` | B=1999, cluster=set_id (G=21), full 84-family sample | gemma fails (p=.512); llama/mistral survive (p=.003/<.0001) | e58f9bd
2026-08-10 | `analysis/rq1_v1_1_robustness/04_rq1a_severity_covariate.py` | + `severity_c` covariate, severity-complete 83-family subsample | none of the 3 families survive WCB once severity is controlled for; mistral's coefficient flips sign | e58f9bd
2026-08-10 | `analysis/rq1_v1_1_robustness/05_valence_split_wcb.py` | B=1999, cluster=family_id (G=42) | direct moral-only sign effect survives for gemma/llama (p=.021/.0005); nonmoral-only is null in all 3 families | e58f9bd
2026-08-10 | `analysis/rq1_v1_1_robustness/06_rq1b_hausman_diagnostic.py` | RE (MixedLM) vs. pooled-OLS vs. family-FE comparison | pooled OLS diverges from RE/FE in all 6 cells (sign flips in 3); `pred_c` correlates .77-.96 with its own family mean — diagnosed the root cause of the bootstrap-CI bug fixed in commit 8338f92 | e58f9bd
2026-08-10 | `analysis/rq1_v1_1_robustness/07_rq1b_family_fe_wcb.py` | B=1999, cluster=family_id (G=42), family-FE refit | gemma fails both domains; llama survives both; mistral survives moral only (nonmoral unresolved, p=.255) | e58f9bd
2026-08-10 | `analysis/rq1_v1_1_robustness/08_family_random_slopes.py` | `re_formula="~<term>"` per family_id | 3-12x SE inflation vs. random-intercept-only in every cell tested; independently reproduces the WCB p-values to within ~.02 via completely different machinery | e58f9bd
2026-08-10 | `analysis/rq1_v1_1_robustness/09_minimum_detectable_effect.py` | α=.05, power=.80, df=G-2, SEs from scripts 01/02/03/07 | llama's `typ_x_sign`/`evoc_x_sign` and every `evoc_x_sign` cell are consistent with this design being underpowered at its cluster count, not necessarily a true null | e58f9bd
2026-08-10 | `analysis/rq1_v1_1_robustness/10_typicality_evocativeness_gap_tables.py` | descriptive means, finetuned checkpoints | bad-good intentionality gap is largest for TYPICAL actions in gemma/mistral — opposite of the human exacerbation pattern | b7b2d8f
2026-08-10 | `analysis/rq1_v1_1_robustness/11_affect_evocativeness_construct_check.py` | descriptive means, pooled across tuning states | the evocativeness manipulation does not raise self-reported affect in any family (gap is slightly negative in all 3) | b7b2d8f
2026-08-10 | `analysis/rq1_v1_1_robustness/12_affect_decoupling.py` | family-demeaned OLS, `aff_dm * instruct` | pretrained checkpoints show a real within-family affect-to-intentionality coupling; instruction-tuning collapses it toward zero, sharpest for bad-sign items (not yet WCB/random-slope tested — a lead, not a confirmed result) | b7b2d8f
2026-08-10 | `analysis/rq1_v1_1_robustness/13_rq1a_severity_set_fe_diagnostic.py` | RE (MixedLM, set_id) vs. pooled-OLS vs. set-FE comparison | found a second instance of the pooled-OLS bootstrap bias (same root cause as RQ1b's, fixed in 8338f92): `severity_c` broke the plain-pooled-OLS WCB refit for the severity-adjusted RQ1a model; set-FE agrees closely with the LMM in all 3 families | f0e50a9
2026-08-10 | `analysis/rq1_v1_1_robustness/14_rq1a_severity_set_fe_wcb.py` | B=1999, cluster=set_id (G=21), set-FE refit | corrected +severity_c WCB p-values: gemma .655, llama .222, mistral .564 (previous, biased numbers: .316/.459/.203) — same qualitative conclusion, wider margin | f0e50a9
2026-08-10 | `analysis/rq1_v1_1_robustness/15_rq1a_severity_mde_and_power_planning.py` | α=.05, power=.80, df=G-2, SE-scaling sample-size approximation | all 3 families underpowered (not confirmed-null) post-severity-control; llama needs ~70 sets for 80% power (+49), gemma/mistral need 400+ (+397/+463) — consistent with gemma/mistral's effects being mostly noise | 74fd855

2026-08-10 | `analysis/rq1_v1_1_robustness/16_valence_split_severity_covariate.py` | B=1999, cluster=family_id (G=42), severity_c covariate | moral-only: gemma fails (p=.543), llama close but not sig (p=.134), mistral null; nonmoral-only: mistral flips to strongly significant negative (p=.000) — unanticipated, severity was suppressing it | d094283
2026-08-10 | `docs/SEVERITY_MORALIZATION_BACKGROUND.md` (theory note, no script) | Turiel/Rozin/Gray-Schein/Haidt synthesis | connects the r=.885 severity-sign correlation to this project's harm-based "moral" definition (constants.py excludes purity/loyalty/authority) — severity may be constitutive of, not just correlated with, moral status here | b7c0cb6
2026-08-10 | `analysis/rq1_v1_1_robustness/17_severity_vs_label.py` | LMM (set_id) + set-FE WCB, 3 same-DF models | AIC favors the categorical label over severity alone in all 3 families (mistral: 3232 vs 5212); neither term survives in the combined model in any family (near-collinearity signature) | 672ec17
2026-08-10 | `docs/SEVERITY_PILOT_PLAN.md` (plan doc, no script) | scoped for 2026-08-11 | curation-only pilot: 3-5 prudential families x 3 severity rungs, read moral_relevance-vs-severity slope, second-reviewer check before trusting a "flat" result | cca125a
2026-08-10 | `analysis/rq1_v1_1_robustness/18_rq1c_typicality_severity_covariate.py` | B=1999, cluster=family_id (G=84), severity_c covariate | typicality/severity correlation is weak (r=.07-.15, vs RQ1a's r=.885); typ_c:sign_c coefficient UNCHANGED to 6 decimal places with severity added, all 3 families — RQ1c's typicality finding does not ride on severity | bec34a3

2026-08-10 | `analysis/rq1_v1_1_robustness/19_severity_dose_response.py` | B=1999, cluster=family_id (G=84), severity_c*sign_c | not significant in any family (p=.54/.70/.36) — weaker than typicality (p<.0001 in 2/3) and evocativeness (p=.03 in 1/3); resolves script 17's ambiguity: severity's RQ1a power-eating effect was collinearity suppression, not an independent dose-response signal | 5c38c6a

2026-08-10 | `analysis/rq1_v1_1_robustness/20_rq1a_severity_matched_pairs_check.py` | within-storyline (set_id) matched-pair comparison, no regression | **decisive**: bad pairs (MB vs NMB) catastrophically severity-unmatched (mean gap 5.42, 0/21 sets within 1.0 point); good pairs (MG vs NMG) reasonably matched (mean gap 1.00, 11/20) — stimulus-design confound, not a power problem; supersedes the dose-response/AIC framing | d786d4e

## Planned, scripted, blocked on external resource

2026-08-10 | `analysis/severity_wording_check/run_reworded_severity.py` | reworded magnitude-only severity question, ~420 reviewer calls | **not yet run** — needs `ANTHROPIC_API_KEY` this environment doesn't have. Script verified to import/compile clean (`2a062c2`). See `docs/SEVERITY_PILOT_PLAN.md` Phase 0. | 2a062c2 (script only, no results yet)

2026-08-12 | items 2/3/4, scoped only per explicit instruction, not implemented | environment check: `statsmodels`/`scipy` present; no `rpy2`, no R/Rscript on PATH, no `pymc`/`bambi`/`numpyro`, no `semopy`, no `firthlogist` | **item 2 (RQ1b measurement-error correction):** SIMEX is feasible with zero new dependencies — the per-item measurement-error variance is directly estimable from `results_all.jsonl`'s repeated `sample_idx` draws per variant (already the basis of `build_1b_frame`'s item-level mean), so a Cook-Stefanski SIMEX refit is pure numpy/statsmodels, low effort, fast to run. A full joint/structural latent-variable model needs new tooling (`semopy`, pip-installable, no R) for the general case, but a lower-friction approximation — a bivariate mixed model with a shared item-level random effect (blame-mean and intentionality stacked long, one shared random intercept) — is buildable in `statsmodels` alone. Recommendation: try SIMEX first (addresses the literal "conservative floor" ask); reach for the bivariate-mixed-model route specifically to resolve the mistral-nonmoral disagreement if SIMEX alone doesn't settle it; treat full `semopy` SEM as a fallback pending a one-line install. **item 3 (proper mixed cumulative-link ordinal model):** no Python-native option exists (`statsmodels.miscmodels.ordinal_model.OrderedModel` is fixed-effects-only, confirmed by reading `models.py`'s own `_ordinal_sensitivity`); the literal ask (`ordinal::clmm`) needs R+rpy2, not installed and a heavier lift than a single pip install; the lower-friction path is a Bayesian ordinal random-intercept model via `pymc`/`bambi` (pip-installable, no R) — rough estimate: minutes per fit given the data size (thousands of rows, 2 flagged cells), plus one-time install/first-compile overhead. Both flagged disagreements already have independent convergent evidence (random-slope LMM agrees with WCB on both), so the marginal value here is closing a documentation gap, not expected to overturn a conclusion. **item 4 (mistral NEU-typicality quasi-separation, Firth/Bayesian-regularized ordinal):** blocked on the same missing tooling as item 3 (no Firth-for-ordinal package exists in Python either); the Bayesian route would share the same `pymc`/`bambi` investment as item 3 (a weakly-informative prior regularizes the quasi-separation directly). Recommendation: bundle with item 3's tooling decision rather than pursue separately; independently low-urgency since the underlying LMM+WCB result for this cell is already well-supported (see `RQ1_STATISTICAL_METHODS_v1.1.md` §7.2). | (scoping only, no commit)

## Known gaps (not yet scripted, numbers already in a doc)

These predate the `analysis/rq1_v1_1_robustness/` scripts and were run as
one-off Python before this log or that directory existed. Flagging per
CLAUDE.md's own traceability standard rather than silently leaving them
unaddressed:

- Reviewer-rated severity by valence category (MB 7.04, NMB 1.62, MG 1.90,
  NMG 0.86 — `docs/RQ1_MECHANISM_ANALYSIS_v1.1.md` section 1's severity
  confound table) — a simple `curated_v1.1.csv` groupby, not yet a script.
- The `data/curation/curated_v1.1.csv` `pair_flag`/`individual_flags`
  distribution check (84 clean vs. 336 vividness-flagged variants) used to
  confirm no vividness-flagged variants were excluded from the v1.1 release.
- Early EDA (parse rate by model, EV rating by model x question, affect
  tracks sign) that reproduced already-published `MAIN_RUN_WRITEUP_v1.1.md`
  numbers as a sanity check rather than producing a new cited result — lower
  priority to formalize since nothing in a writeup depends on it uniquely.
2026-08-11 | `analysis/rq1_v1_1_robustness/21_rq1c_typicality_reversal_cellmeans.py` | intentionality, finetuned, family x typicality x sign cell means | raw cell means (not just the gap) show uncommon-method items rate higher on intentionality overall in all 3 families, rising more for good than bad items | (uncommitted)
2026-08-11 | `analysis/rq1_v1_1_robustness/22_rq1c_typicality_main_effect.py` | B=1999, cluster=family_id (G=84), seed=13, WCB on typ_c and typ_c:sign_c in `ev_rating ~ typ_c * sign_c` | llama: typ_c main effect huge and survives (p<.0001), interaction null (p=.40) -- symmetric shift; gemma: typ_c main effect does NOT survive (p=.126), interaction survives (p=.0005) -- interaction-only; mistral: both survive (p<.0001 / p<.0001) | 6f9d458

## Closing out `docs/OUTSTANDING_STATISTICAL_ANALYSIS.md` (2026-08-12) — design/QA groundwork for the next (145-family) increment, not new confirmatory findings

2026-08-12 | `analysis/rq1_v1_1_robustness/23_icc_variance_decomposition.py` | item 10: REML random-intercept-only fits at each contrast's existing grouping column | ICC ranges 0.02-0.88, design effects mostly large (6-160x) — within-family replicate sampling has strongly diminishing returns vs. adding families; direct input for sizing the next increment | 6ff1149
2026-08-12 | `analysis/rq1_v1_1_robustness/24_lrt_vs_wald.py` | item 8: ML-fit LRT (df=1) vs. existing Wald/WCB p-values, same contrasts as scripts 01/02/03/07 | LRT reproduces Wald's exact overconfidence pattern in every cell WCB already flagged (rq1a-gemma, rq1b-gemma both domains, rq1b-mistral-nonmoral, rq1c-llama typ+evoc, rq1c-mistral-evoc) — confirms the small-cluster problem isn't a WCB-specific artifact | 2e4ea85
2026-08-12 | `analysis/rq1_v1_1_robustness/25_parse_rate_condition_check.py` | item 12: logistic regression of parse_ok on typ_c/sign_c/vt_c (+domain), per model_key, intentionality rows | typicality shows no effect on parse rate anywhere (all p>.13) — no threat to RQ1c/RQ1d; valence-type does predict parse rate in 3/6 checkpoints (mistral-pretrained p=2.7e-7, gemma-instruct p=4.4e-4, llama-instruct p=3.9e-3) — flagged, not yet chased further | 7b7de27
2026-08-12 | `analysis/rq1_v1_1_robustness/26_ev_scoring_validation.py` | item 11: ev_rating (logit-fallback) vs. parsed_rating agreement + RQ1c typ_c:sign_c re-tested on parse_ok-only rows with parsed_rating substituted | agreement only moderate even on best-parsed checkpoints (corr .44-.50 instruct, .05-.07 pretrained) — scores aren't interchangeable at the response level, but the RQ1c WCB significance pattern is identical under either scoring method in all 3 families (effect sizes roughly double under parsed-only) | 1eb6de4
2026-08-12 | `analysis/rq1_v1_1_robustness/27_bootstrap_ci_bca_comparison.py` | item 6: pipeline's own `_bootstrap_ci` (percentile, n_boot=200) vs. jackknife-BCa (n_boot=499) for the same 21 primary cells; comparison only, models.py not touched | BCa changes the zero-exclusion conclusion in exactly 1/21 cells — gemma's evoc_x_sign (pct@200 CI includes 0, BCa excludes it) — which is also the single most marginal cell in the release (WCB p=.030). All other 20 cells agree regardless of method. First attempt at n_boot=1999 was killed after 6.5 min with nothing saved (no checkpointing) before this cost-reduced, checkpointed version | 984d3fd
2026-08-12 | `pyproject.toml` (`bayes` extra) + `analysis/rq1_v1_1_robustness/_bayes_compat.py` | `uv pip install -e ".[bayes]"` (pymc, bambi) | added per coordinator go-ahead for items 3/4. pymc's arviz dependency broke on import against this project's matplotlib (arviz_plots bug); a matplotlib<3.10 downgrade "fixed" it but broke 26 existing tests via an unrelated pyparsing-deprecation-as-error interaction — reverted, fixed instead with a 2-line compat shim, no dependency version pinned. Verified reproducible in a from-scratch venv; full test suite reconfirmed clean (564 passed, 1 pre-existing unrelated failure) | 5c015b4
2026-08-12 | `analysis/rq1_v1_1_robustness/28_rq1b_simex.py` | item 2: SIMEX (per-item measurement-error variance from repeated sample_idx draws, quadratic extrapolation to lambda=-1), all 6 rq1b cells + family-cluster bootstrap for mistral-nonmoral (seeds 14/15) | measurement-error variance is negligible everywhere (1.5e-8 to 7.4e-8) — ev_rating is near-deterministic given the prompt across its 50 repeated samples per item, confirmed directly — so SIMEX correction does essentially nothing (attenuation -0.001% to +0.01% in all 6 cells). Mistral-nonmoral bootstrap: simex_beta=-0.176 (unchanged), 95% CI [-0.568, .054] crosses 0, p~=.14 — does NOT resolve the named disagreement (family-FE WCB p=.255 vs. random-slope p=.0021) in favor of significance; leans toward the WCB's null reading | 63a5b48
2026-08-12 | `analysis/rq1_v1_1_robustness/29_rq1_ordinal_mixed_bambi.py` | item 3: bambi/PyMC `family="cumulative"`, `(1\|family_id)` random intercept, NUTS draws=2000/tune=2000/chains=4, seed 16 | cost-checked first (n=2000 subsample ~35-45s/1000 draws), full run: mistral rq1_base n=16800 took 303s, llama rq1c n=8400 took 918s, both converged cleanly (r_hat=1.0). Both terms come back SIGNIFICANT (mistral sign_c:tuning_c mean=1.387 HDI[1.236,1.539]; llama typ_c:sign_c mean=1.302 HDI[1.037,1.561]) — disagreeing with the existing convergent-null evidence (WCB p=.918/.403, family-random-slope LMM p~=.92/.39-.40). Caveat: this model has a random INTERCEPT only, not the random SLOPE the "family-random-slope LMM" pillar actually relies on (script 08 found 3-12x SE inflation from omitting exactly that) — attempted a random-slope refit (`(1+term\|family_id)`) but killed it after a 2000-row calibration subsample alone ran >5 min (vs. 44.5s for the intercept-only version at the same n) — well past the 30-60 min threshold once extrapolated to full data, not attempted further. Open, not resolved: does the ordinal-vs-LMM disagreement survive once random slopes are added, or is this the same missing-random-slope artifact repeating in the ordinal model | 1d4e0ad
2026-08-12 | `analysis/rq1_v1_1_robustness/30_mistral_neu_typicality_bayes.py` | item 4: bambi/PyMC `family="cumulative"`, `(1\|family_id)`, NUTS draws=2000/tune=2000/chains=4, seed 17, mistral NEU/finetuned only (n=2100, G=21) | fast (28s), converged cleanly (r_hat=1.0). Diagnosed the degeneracy directly: this subset's rounded ratings collapse to only 2 categories, so the "ordinal" model is really binary logistic, and typ_c apparently near-perfectly separates them — classic MLE-to-infinity failure mode. Bayesian default weakly-informative priors regularize it to mean=6.0, 94% HDI [4.52, 7.67], excludes 0 with real (finite) uncertainty. Corroborates rather than contradicts the existing LMM+WCB result for this cell (p_wcb=.000) — resolved cleanly, no open thread | d112ede
2026-08-15 | `analysis/rq1_v1_1_robustness/31_rq1_base_sign_main_effect_wcb.py` | classic-Knobe-effect gap-fill: WCB (B=1999, cluster=family_id, G=84) on the bare `sign_c` main effect (`ev_rating ~ sign_c`), finetuned-only, moral+nonmoral pooled -- the term script 01 never bootstrapped (01 only tests `sign_c:tuning_c`), seed=20 | p_wcb: gemma .1056 (Wald .091), llama .1016 (Wald .095), mistral .5328 (Wald .495) -- none survive; the two near-Wald-misses weaken slightly rather than tighten, consistent with WCB never rescuing a Wald-marginal term elsewhere in this project. No robust pooled (valence-type-agnostic) classic Knobe main effect in any family | 61c5757
2026-08-15 | `analysis/rq1_v1_1_robustness/33_rq1_base_sign_by_tuning_wcb.py` | complement to 31: WCB (B=1999, cluster=family_id, G=84) on `sign_c` split by tuning_status instead of pooling/inferring pretrained algebraically, seed=22 | pretrained shows a robust, WCB-significant REVERSED effect (good rated more intentional than bad) in all 3 families: gemma beta=-.130 p=.000, llama beta=-.107 p=.024, mistral beta=-.058 p=.042. Finetuned remains marginal-to-null per 31 (gemma p=.105, llama p=.115, mistral p=.518). So the significant sign_c:tuning_c interaction (script 01, gemma/llama survive) is driven by a real, robust reversal in pretrained models eroding toward zero/marginal-classic-direction under finetuning -- not by finetuning installing a robust classic Knobe effect on top of a null pretrained baseline. Reframes RQ1_base: "finetuning induces the Knobe effect" undersells it; "finetuning erodes a robust anti-Knobe pretrained bias, without reliably flipping it to the classic direction" is the more accurate read for gemma/llama, and mistral just goes from a small significant reversal to a clean null | 874e8ac
