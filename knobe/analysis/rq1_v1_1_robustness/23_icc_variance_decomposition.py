"""Outstanding-review item 10: effect sizes / variance decomposition (ICC).

For each primary RQ1a-d analysis subsample, fits a random-intercept-only
variance-components model (REML, not ML -- unbiased variance estimates are
the point here, unlike the LRT script which needs ML) at the same grouping
column and subsample the corresponding WCB script uses (see
config.yaml:clustering), and reports:

  icc = re_var / (re_var + resid_var)          -- how much of response-level
                                                    variance is between-cluster
  design_effect = 1 + (avg_cluster_n - 1) * icc -- how much replicate sampling
                                                    within a cluster is worth
                                                    vs. adding new clusters

This is the input for right-sizing the next data-collection increment: a
high ICC means more *families*, not more *samples per family*, buys power;
a low ICC means the opposite. Not a re-run of the RQ1a MDE calc in
09_minimum_detectable_effect.py / 15_rq1a_severity_mde_and_power_planning.py
-- this is the general-purpose decomposition the original review asked for,
which those two MDE scripts don't produce as a general table.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from lib import load_frame, build_1b_frame, save, CONFIG

warnings.filterwarnings("ignore")

FAMS = ["gemma", "llama", "mistral"]


def icc_row(sub: pd.DataFrame, outcome: str, group_col: str, contrast: str, family: str, extra: dict) -> dict:
    m = smf.mixedlm(f"{outcome} ~ 1", sub, groups=sub[group_col]).fit(reml=True, method="lbfgs")
    re_var = float(m.cov_re.iloc[0, 0])
    resid_var = float(m.scale)
    icc = re_var / (re_var + resid_var) if (re_var + resid_var) > 0 else float("nan")
    n_groups = sub[group_col].nunique()
    n_obs = len(sub)
    avg_cluster_n = n_obs / n_groups
    design_effect = 1 + (avg_cluster_n - 1) * icc
    return dict(contrast=contrast, family=family, group_col=group_col, n_groups=n_groups, n_obs=n_obs,
                avg_cluster_n=avg_cluster_n, re_var=re_var, resid_var=resid_var, icc=icc,
                design_effect=design_effect, **extra)


def main() -> None:
    d = load_frame()
    model_keys = CONFIG["family_model_keys"]
    rows = []

    base = d[(d["question"] == "intentionality") & (d["vt"].isin(["moral", "nonmoral"]))].dropna(subset=["sign_c"])
    for fam in FAMS:
        rows.append(icc_row(base[base["family"] == fam], "ev_rating", "family_id",
                             "rq1_base_sign_x_tuning", fam, {}))

    rq1a = d[(d["question"] == "intentionality") & (d["tuning_status"] == "finetuned")
             & (d["vt"].isin(["moral", "nonmoral"]))].dropna(subset=["sign_c", "vt_c"])
    for fam in FAMS:
        rows.append(icc_row(rq1a[rq1a["family"] == fam], "ev_rating", "set_id",
                             "rq1a_sign_x_valence_type", fam, {}))

    for fam in FAMS:
        mk = model_keys[fam]["instruct"]
        for vt in ["moral", "nonmoral"]:
            frame = build_1b_frame(d, mk, vt)
            rows.append(icc_row(frame, "ev_rating", "family_id", "rq1b", fam, {"valence_type": vt}))

    rq1c = d[(d["question"] == "intentionality") & (d["tuning_status"] == "finetuned")
             & (d["vt"].isin(["moral", "nonmoral"]))].dropna(subset=["sign_c", "typ_c", "evoc_c"])
    for fam in FAMS:
        rows.append(icc_row(rq1c[rq1c["family"] == fam], "ev_rating", "family_id",
                             "rq1c_typ_and_evoc", fam, {}))

    neu = d[(d["question"] == "intentionality") & (d["tuning_status"] == "finetuned") & (d["valence"] == "NEU")]
    for fam in FAMS:
        rows.append(icc_row(neu[neu["family"] == fam], "ev_rating", "family_id",
                             "rq1d_neu", fam, {}))

    out = pd.DataFrame(rows)
    cols = ["contrast", "family", "valence_type", "group_col", "n_groups", "n_obs", "avg_cluster_n",
            "re_var", "resid_var", "icc", "design_effect"]
    out = out.reindex(columns=cols)
    print(out.to_string(index=False))
    save(out, "23_icc_variance_decomposition.csv")


if __name__ == "__main__":
    main()
