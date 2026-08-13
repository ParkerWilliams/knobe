"""Outstanding-review item 3: a proper mixed cumulative-link ordinal model
(via bambi/PyMC, family="cumulative", NUTS) for the two flagged LMM-vs-
ordinal disagreements:

  - mistral's rq1_base sign_c:tuning_c (the fixed-effects-only OrderedModel
    sensitivity check disagreed with the LMM here)
  - llama's rq1c typ_c:sign_c (same kind of disagreement)

The existing `_ordinal_sensitivity` check in src/knobe/analysis/models.py is
fixed-effects only (statsmodels' OrderedModel has no random effects) -- this
adds the missing family_id random intercept, which is what the review asked
for and what the LMM already has. ev_rating is rounded to the nearest
integer (0-10) as the ordinal outcome, matching `_ordinal_sensitivity`'s own
convention exactly.

Cost-checked before this run (see ANALYSIS_LOG.md): ~35s sampling at n=2000,
draws=1000/tune=1000/chains=4 -> extrapolated to ~2.5 min (llama, n=8400) and
~5 min (mistral, n=16800) at that draws/tune. Doubled to draws=2000/tune=2000
here for a convergence-quality margin (mild rhat>1.01 warning at the smaller
setting) -- still comfortably under the 30-60 min pause threshold.
"""
from __future__ import annotations

import time
import warnings

import _bayes_compat  # noqa: F401 -- must import before bambi/pymc, see that module's docstring
import arviz as az
import bambi as bmb
import numpy as np
import pandas as pd

from lib import load_frame, CONFIG, save

warnings.filterwarnings("ignore")

SEED = CONFIG["wild_cluster_bootstrap"]["seeds"]["29_rq1_ordinal_mixed_bambi"]
DRAWS, TUNE, CHAINS = 2000, 2000, 4


def _clean_frame(sub: pd.DataFrame, formula_cols: list[str]) -> pd.DataFrame:
    cats = sorted(sub["rating_int"].unique())
    out = sub[["rating_int", *formula_cols]].copy()
    out["rating_cat"] = pd.Categorical(out["rating_int"], categories=cats, ordered=True)
    out = out.drop(columns=["rating_int"])
    out["family_id"] = out["family_id"].astype(str)
    return out


def fit_and_summarize(sub: pd.DataFrame, formula: str, formula_cols: list[str], term: str, label: str) -> dict:
    clean = _clean_frame(sub, formula_cols)
    model = bmb.Model(formula, clean, family="cumulative")
    t0 = time.time()
    idata = model.fit(draws=DRAWS, tune=TUNE, chains=CHAINS, cores=4, progressbar=False, random_seed=SEED)
    secs = time.time() - t0
    summ = az.summary(idata, var_names=[term])
    row = dict(
        label=label, term=term, n=len(clean), secs=secs,
        mean=float(summ["mean"].iloc[0]), sd=float(summ["sd"].iloc[0]),
        hdi_3=float(summ["hdi_3%"].iloc[0]), hdi_97=float(summ["hdi_97%"].iloc[0]),
        r_hat=float(summ["r_hat"].iloc[0]), ess_bulk=float(summ["ess_bulk"].iloc[0]),
        excludes_0=not (float(summ["hdi_3%"].iloc[0]) <= 0 <= float(summ["hdi_97%"].iloc[0])),
    )
    print(row)
    return row


def main() -> None:
    d = load_frame()
    rows = []

    base = d[(d["question"] == "intentionality") & (d["vt"].isin(["moral", "nonmoral"]))].dropna(subset=["sign_c"])
    base = base.assign(tuning_c=np.where(base["tuning_status"] == "finetuned", 0.5, -0.5))
    mistral = base[base["family"] == "mistral"].copy()
    mistral["rating_int"] = mistral["ev_rating"].round().clip(0, 10).astype(int)
    rows.append(fit_and_summarize(
        mistral, "rating_cat ~ sign_c*tuning_c + (1|family_id)", ["sign_c", "tuning_c", "family_id"],
        "sign_c:tuning_c", "mistral_rq1_base_sign_x_tuning",
    ))
    save(pd.DataFrame(rows), "29_rq1_ordinal_mixed_bambi.csv")

    rq1c = d[(d["question"] == "intentionality") & (d["tuning_status"] == "finetuned")
             & (d["vt"].isin(["moral", "nonmoral"]))].dropna(subset=["sign_c", "typ_c"])
    llama = rq1c[rq1c["family"] == "llama"].copy()
    llama["rating_int"] = llama["ev_rating"].round().clip(0, 10).astype(int)
    rows.append(fit_and_summarize(
        llama, "rating_cat ~ typ_c*sign_c + (1|family_id)", ["typ_c", "sign_c", "family_id"],
        "typ_c:sign_c", "llama_rq1c_typicality_x_sign",
    ))

    out = pd.DataFrame(rows)
    print(out.to_string(index=False))
    save(out, "29_rq1_ordinal_mixed_bambi.csv")


if __name__ == "__main__":
    main()
