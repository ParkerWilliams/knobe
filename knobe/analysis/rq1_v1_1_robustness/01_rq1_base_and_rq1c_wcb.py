"""Wild-cluster-bootstrap validation at G=84 (family_id) for RQ1_base
sign_x_tuning and RQ1c typ_x_sign / evoc_x_sign -- see
docs/RQ1_STATISTICAL_METHODS_v1.1.md section 8, Table (large-G comparison).
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from lib import load_frame, wild_cluster_bootstrap, save

warnings.filterwarnings("ignore")

FAMS = ["gemma", "llama", "mistral"]


def lmm(sub, formula, term, groups_col="family_id"):
    m = smf.mixedlm(formula, sub, groups=sub[groups_col]).fit(reml=False, method="lbfgs")
    return m.params[term], m.pvalues[term]


def main() -> None:
    d = load_frame()
    rows = []

    base = d[(d["question"] == "intentionality") & (d["vt"].isin(["moral", "nonmoral"]))].dropna(subset=["sign_c"])
    base = base.assign(tuning_c=np.where(base["tuning_status"] == "finetuned", 0.5, -0.5))
    for fam in FAMS:
        s = base[base["family"] == fam]
        b_lmm, p_lmm = lmm(s, "ev_rating ~ sign_c * tuning_c", "sign_c:tuning_c")
        wcb = wild_cluster_bootstrap(s, "ev_rating ~ sign_c * tuning_c", "sign_c:tuning_c", "family_id", seed=2)
        rows.append(dict(contrast="rq1_base_sign_x_tuning", family=fam, term="sign_c:tuning_c",
                          lmm_estimate=b_lmm, lmm_p=p_lmm, **wcb))

    c = d[(d["question"] == "intentionality") & (d["tuning_status"] == "finetuned")
          & (d["vt"].isin(["moral", "nonmoral"]))].dropna(subset=["sign_c", "typ_c", "evoc_c"])
    for fam in FAMS:
        s = c[c["family"] == fam]
        b1, p1 = lmm(s, "ev_rating ~ typ_c * sign_c", "typ_c:sign_c")
        wcb1 = wild_cluster_bootstrap(s, "ev_rating ~ typ_c * sign_c", "typ_c:sign_c", "family_id", seed=3)
        rows.append(dict(contrast="rq1c_typicality_x_sign", family=fam, term="typ_c:sign_c",
                          lmm_estimate=b1, lmm_p=p1, **wcb1))
        b2, p2 = lmm(s, "ev_rating ~ evoc_c * sign_c", "evoc_c:sign_c")
        wcb2 = wild_cluster_bootstrap(s, "ev_rating ~ evoc_c * sign_c", "evoc_c:sign_c", "family_id", seed=4)
        rows.append(dict(contrast="rq1c_evocativeness_x_sign", family=fam, term="evoc_c:sign_c",
                          lmm_estimate=b2, lmm_p=p2, **wcb2))

    out = pd.DataFrame(rows)
    print(out.to_string(index=False))
    save(out, "01_rq1_base_and_rq1c_wcb.csv")


if __name__ == "__main__":
    main()
