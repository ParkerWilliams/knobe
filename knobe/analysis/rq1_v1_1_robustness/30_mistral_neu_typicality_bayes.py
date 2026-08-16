"""Outstanding-review item 4: Bayesian-regularized ordinal fit for mistral's
NEU-typicality quasi-separation cell (fixed-effects OrderedModel MLE
diverges to a degenerate estimate=13.3, docs/rq1_findings/RQ1_STATISTICAL_METHODS_v1.1.md
section 7.2 -- small N=2100/G=21 subset where typ_c likely near-perfectly
predicts category membership).

Bayesian estimation with bambi's default weakly-informative slope priors
(N(0, sd scaled to the data) rather than a flat/MLE objective) is the
standard regularization fix for quasi/complete separation -- no custom prior
tuning needed, this is exactly what a proper prior buys over MLE here.
family="cumulative" (mixed: family_id random intercept), same rounding
convention as script 29 and models.py::_ordinal_sensitivity.

Cost: N=2100/G=21 is far smaller than script 29's cells (8400-16800) -- a
quick subsample cost-check first, but this is expected to be fast.
"""
from __future__ import annotations

import time
import warnings

import _bayes_compat  # noqa: F401
import arviz as az
import bambi as bmb
import pandas as pd

from lib import load_frame, CONFIG, save

warnings.filterwarnings("ignore")

SEED = CONFIG["wild_cluster_bootstrap"]["seeds"]["30_mistral_neu_typicality_bayes"]
DRAWS, TUNE, CHAINS = 2000, 2000, 4


def main() -> None:
    d = load_frame()
    neu = d[(d["question"] == "intentionality") & (d["tuning_status"] == "finetuned")
            & (d["valence"] == "NEU") & (d["family"] == "mistral")].dropna(subset=["typ_c"]).copy()
    neu["rating_int"] = neu["ev_rating"].round().clip(0, 10).astype(int)
    cats = sorted(neu["rating_int"].unique())
    clean = neu[["rating_int", "typ_c", "family_id"]].copy()
    clean["rating_cat"] = pd.Categorical(clean["rating_int"], categories=cats, ordered=True)
    clean = clean.drop(columns=["rating_int"])
    clean["family_id"] = clean["family_id"].astype(str)
    print(f"n={len(clean)}, n_families={clean['family_id'].nunique()}, n_categories={len(cats)}")

    model = bmb.Model("rating_cat ~ typ_c + (1|family_id)", clean, family="cumulative")
    t0 = time.time()
    idata = model.fit(draws=DRAWS, tune=TUNE, chains=CHAINS, cores=4, progressbar=False, random_seed=SEED)
    secs = time.time() - t0
    summ = az.summary(idata, var_names=["typ_c"])
    row = dict(
        label="mistral_rq1d_typicality_within_neu", term="typ_c", n=len(clean), secs=secs,
        mean=float(summ["mean"].iloc[0]), sd=float(summ["sd"].iloc[0]),
        hdi_3=float(summ["hdi_3%"].iloc[0]), hdi_97=float(summ["hdi_97%"].iloc[0]),
        r_hat=float(summ["r_hat"].iloc[0]), ess_bulk=float(summ["ess_bulk"].iloc[0]),
        excludes_0=not (float(summ["hdi_3%"].iloc[0]) <= 0 <= float(summ["hdi_97%"].iloc[0])),
    )
    print(row)
    save(pd.DataFrame([row]), "30_mistral_neu_typicality_bayes.csv")


if __name__ == "__main__":
    main()
