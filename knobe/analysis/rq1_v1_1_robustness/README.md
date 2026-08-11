# RQ1 v1.1 small-cluster-robustness re-analysis

Exploratory research scripts behind `docs/RQ1_STATISTICAL_METHODS_v1.1.md`
§8–§11 and `docs/RQ1_MECHANISM_ANALYSIS_v1.1.md`. Not part of the `knobe`
package or the `knobe analyze` CLI — see
`docs/RQ1_STATISTICAL_METHODS_v1.1.md` §13 item 6 for why these haven't been
promoted into the pipeline yet (mainly: the bootstrap seeding here is
per-script, not per-contrast like `models.py`'s
`sha256(base_seed, contrast, model_family, boot_idx)` scheme).

## Why this exists

The preregistered pipeline's primary model (family-random-intercept LMM,
`src/knobe/analysis/models.py`) reports Wald p-values that assume standard
asymptotics hold at 21–84 clusters. They often don't. These scripts re-test
the RQ1a–1d contrasts with methods that are valid at these cluster counts —
a wild cluster bootstrap (Cameron-Gelbach-Miller 2008), a severity-covariate
control for RQ1a's moral/nonmoral intensity confound, a Hausman-style
RE/pooled-OLS/fixed-effects diagnostic for RQ1b (which found and fixed an
actual bug in `models.py`'s bootstrap CI), a family-random-slope check, and
a minimum-detectable-effect calculation. Results and their effect on both
docs' conclusions are summarized in `docs/RQ1_MECHANISM_ANALYSIS_v1.1.md`'s
"What changed from the first pass" table.

## Running

From the repo root, with the project's own `.venv` (needs `pandas`,
`statsmodels`, `scipy`, `pyyaml` — already present if you've run
`uv pip install -e ".[dev,stats]"` per `knobe/README.md`):

```
# one-time: unpack the compressed v1.1 results (knobe/README.md "Study results (compressed)")
mkdir -p results/v1.1
gunzip -c results_dist/results_v1.1_all.jsonl.gz > results/v1.1/results_all.jsonl

cd analysis/rq1_v1_1_robustness
../../.venv/bin/python 01_rq1_base_and_rq1c_wcb.py
../../.venv/bin/python 02_rq1d_wcb.py
../../.venv/bin/python 03_rq1a_baseline_wcb.py
../../.venv/bin/python 04_rq1a_severity_covariate.py
../../.venv/bin/python 05_valence_split_wcb.py
../../.venv/bin/python 06_rq1b_hausman_diagnostic.py
../../.venv/bin/python 07_rq1b_family_fe_wcb.py
../../.venv/bin/python 08_family_random_slopes.py
../../.venv/bin/python 09_minimum_detectable_effect.py   # run after 01/02/03/07 -- reads their outputs
../../.venv/bin/python 10_typicality_evocativeness_gap_tables.py
../../.venv/bin/python 11_affect_evocativeness_construct_check.py
../../.venv/bin/python 12_affect_decoupling.py
../../.venv/bin/python 13_rq1a_severity_set_fe_diagnostic.py
../../.venv/bin/python 14_rq1a_severity_set_fe_wcb.py
../../.venv/bin/python 15_rq1a_severity_mde_and_power_planning.py   # run after 03 and 14
../../.venv/bin/python 16_valence_split_severity_covariate.py
../../.venv/bin/python 17_severity_vs_label.py
../../.venv/bin/python 18_rq1c_typicality_severity_covariate.py
../../.venv/bin/python 19_severity_dose_response.py   # run after 01 for the printed rq1c comparison
../../.venv/bin/python 20_rq1a_severity_matched_pairs_check.py
```

Every script writes one small CSV to `outputs/` and prints it to stdout.
`lib.py` holds the shared data loading (`load_frame`, `build_1b_frame`) and
the wild-cluster-bootstrap implementation (`wild_cluster_bootstrap`).
`config.yaml` records every parameter used (bootstrap resamples, seeds,
α/power for the MDE calculation, which column each contrast clusters on,
the effect-coding scheme — mirrors `src/knobe/analysis/models.py`'s own
coding exactly).

## Files

| script | produces | doc section |
|---|---|---|
| `01_rq1_base_and_rq1c_wcb.py` | `outputs/01_rq1_base_and_rq1c_wcb.csv` | STATISTICAL_METHODS §8 (large-G validation table) |
| `02_rq1d_wcb.py` | `outputs/02_rq1d_wcb.csv` | STATISTICAL_METHODS §8 (RQ1d rows) |
| `03_rq1a_baseline_wcb.py` | `outputs/03_rq1a_baseline_wcb.csv` | STATISTICAL_METHODS §8 (RQ1a baseline row, full 84-family sample) |
| `04_rq1a_severity_covariate.py` | `outputs/04_rq1a_severity_covariate.csv` | STATISTICAL_METHODS §9; MECHANISM_ANALYSIS §1 |
| `05_valence_split_wcb.py` | `outputs/05_valence_split_wcb.csv` | STATISTICAL_METHODS §9 (direct split table); MECHANISM_ANALYSIS §1 |
| `06_rq1b_hausman_diagnostic.py` | `outputs/06_rq1b_hausman_diagnostic.csv` | STATISTICAL_METHODS §10.1 |
| `07_rq1b_family_fe_wcb.py` | `outputs/07_rq1b_family_fe_wcb.csv` | STATISTICAL_METHODS §8, §10.3; MECHANISM_ANALYSIS §2 |
| `08_family_random_slopes.py` | `outputs/08_family_random_slopes.csv` | STATISTICAL_METHODS §11 |
| `09_minimum_detectable_effect.py` | `outputs/09_minimum_detectable_effect.csv` | STATISTICAL_METHODS §11.1 |
| `10_typicality_evocativeness_gap_tables.py` | `outputs/10_typicality_gap.csv`, `outputs/10_evocativeness_gap.csv` | MECHANISM_ANALYSIS §3 (typicality gap quoted; evocativeness gap explored, not quoted) |
| `11_affect_evocativeness_construct_check.py` | `outputs/11_affect_evocativeness_construct_check.csv` | MECHANISM_ANALYSIS §4 (first table) |
| `12_affect_decoupling.py` | `outputs/12_affect_decoupling.csv` | MECHANISM_ANALYSIS §4 (second table) — flagged there as a lead, not yet WCB/random-slope tested |
| `13_rq1a_severity_set_fe_diagnostic.py` | `outputs/13_rq1a_severity_set_fe_diagnostic.csv` | STATISTICAL_METHODS §9 (diagnostic note) |
| `14_rq1a_severity_set_fe_wcb.py` | `outputs/14_rq1a_severity_set_fe_wcb.csv` | STATISTICAL_METHODS §9 (corrected +severity WCB p-values); MECHANISM_ANALYSIS §1 |
| `15_rq1a_severity_mde_and_power_planning.py` | `outputs/15_rq1a_severity_mde_and_power_planning.csv` | STATISTICAL_METHODS §11.2; MECHANISM_ANALYSIS §1 |
| `16_valence_split_severity_covariate.py` | `outputs/16_valence_split_severity_covariate.csv` | MECHANISM_ANALYSIS §1 (severity-adjusted direct split; no OLS-vs-GLS divergence here, checked and confirmed clean) |
| `17_severity_vs_label.py` | `outputs/17_severity_vs_label.csv` | MECHANISM_ANALYSIS §1; SEVERITY_MORALIZATION_BACKGROUND.md; SEVERITY_PILOT_PLAN.md |
| `18_rq1c_typicality_severity_covariate.py` | `outputs/18_rq1c_typicality_severity_covariate.csv` | MECHANISM_ANALYSIS §3 — does typicality's effect ride on severity? No: coefficients unchanged to 6 decimal places in all 3 families |
| `19_severity_dose_response.py` | `outputs/19_severity_dose_response.csv` | MECHANISM_ANALYSIS §1 — direct severity_c:sign_c dose-response test at rq1c's own clustering/power; not significant in any family, weaker than typicality or evocativeness, but its own CI is too wide to be disconfirming (see script 20 for the decisive check) |
| `20_rq1a_severity_matched_pairs_check.py` | `outputs/20_severity_matched_pairs_{bad,good}.csv` | MECHANISM_ANALYSIS §1 — **the decisive finding**: within-storyline manipulation check shows MB/NMB (bad pairs) catastrophically severity-unmatched (0/21 sets within 1.0 point); MG/NMG (good pairs) reasonably matched (11/20). Stimulus-design confound, not a statistical-power problem |

## A second instance of the pooled-OLS bias, found while finishing the MDE table

Same root cause as the RQ1b bug (see `06_rq1b_hausman_diagnostic.py` /
`docs/RQ1_STATISTICAL_METHODS_v1.1.md` §10.1), different contrast: RQ1a's
severity-adjusted model (`04_rq1a_severity_covariate.py`'s `+severity_c`
rows) also used a plain-pooled-OLS WCB refit, and `severity_c` — a
continuous, family-level covariate — broke it the same way `pred_c` broke
RQ1b's (gemma's pooled-OLS point estimate was −0.976 against an LMM estimate
of +0.280 — a sign flip). `13`/`14` diagnose and fix it with a
**set**-fixed-effects refit (not family-FE — unlike RQ1b, `sign_c`/`vt_c`
vary within a `set_id`, so this is the correctly-scoped fix here). **Only
two of these have been caught, both by hand.** Audited every other
`wild_cluster_bootstrap(...)` call in `01`-`12` (`grep -n
"wild_cluster_bootstrap(" 0*.py`) to check: every other formula uses only
the balanced ±0.5 effect-coded factors (`sign_c`, `tuning_c`, `typ_c`,
`evoc_c`) or a bare intercept — `pred_c` (RQ1b) and `severity_c` (RQ1a) were
the only two continuous, cluster-correlated covariates in this directory,
and both are now fixed. No other instance of this bug exists here as of
this audit; recheck this if a future script adds another continuous
covariate to a WCB call.

## Known loose end

`03_rq1a_baseline_wcb.py` (full 84-family sample) and
`04_rq1a_severity_covariate.py`'s "baseline" column (83-family,
severity-complete subsample, for an apples-to-apples comparison against the
severity-adjusted model) report *slightly* different numbers for the same
nominal contrast, because one family (`WORK-MG-02`) has no curation severity
record. The qualitative pattern is identical either way (llama and mistral
survive the baseline WCB, gemma doesn't); both docs cite each number from
its own script and note the discrepancy explicitly rather than silently
picking one. See `docs/RQ1_STATISTICAL_METHODS_v1.1.md` §9's footnote.
