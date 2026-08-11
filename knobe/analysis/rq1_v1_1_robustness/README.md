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
