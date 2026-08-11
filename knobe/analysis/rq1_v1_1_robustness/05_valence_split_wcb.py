"""Direct split-sample test: fit the sign effect (bad vs good) separately
within moral-only and nonmoral-only items, wild-cluster-bootstrapped at
G=42 (family_id) -- the surviving piece of evidence for moral-specificity in
docs/RQ1_MECHANISM_ANALYSIS_v1.1.md section 1 (distinct from, and more
robust than, the pooled sign_c:vt_c interaction in 03/04, which does not
survive severity adjustment in any family).
"""
from __future__ import annotations

import warnings

import pandas as pd
import statsmodels.formula.api as smf

from lib import load_frame, wild_cluster_bootstrap, save

warnings.filterwarnings("ignore")

FAMS = ["gemma", "llama", "mistral"]


def main() -> None:
    d = load_frame()
    sub = d[(d["question"] == "intentionality") & (d["tuning_status"] == "finetuned")].dropna(subset=["sign_c"])

    rows = []
    for fam in FAMS:
        for vt in ["moral", "nonmoral"]:
            s = sub[(sub["family"] == fam) & (sub["vt"] == vt)]
            m = smf.mixedlm("ev_rating ~ sign_c", s, groups=s["family_id"]).fit(reml=False, method="lbfgs")
            wcb = wild_cluster_bootstrap(s, "ev_rating ~ sign_c", "sign_c", "family_id", seed=11)
            rows.append(dict(family=fam, valence_type=vt, term="sign_c",
                              lmm_estimate=m.params["sign_c"], lmm_p=m.pvalues["sign_c"], **wcb))

    out = pd.DataFrame(rows)
    print(out.to_string(index=False))
    save(out, "05_valence_split_wcb.csv")


if __name__ == "__main__":
    main()
