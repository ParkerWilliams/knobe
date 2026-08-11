# Analysis log

Append-only provenance log per `CLAUDE.md` section 5: one line per completed
analysis run, so any number in a writeup can be traced back to exactly how
it was produced. Format:

    YYYY-MM-DD | script/command | key params | one-line outcome | commit hash

Backfilled entries below are reconstructed from the 2026-08-10 session
history rather than logged live as each run happened — going forward, add
the line at the time of the run, not after the fact.

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
