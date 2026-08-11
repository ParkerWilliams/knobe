"""RQ1a with reviewer-rated severity as a covariate, refit at G=21 (set_id)
with wild-cluster-bootstrap p-values for both the baseline and
severity-adjusted models -- see docs/RQ1_STATISTICAL_METHODS_v1.1.md section
9. Tests whether the moral-specific sign_c:vt_c interaction survives
controlling for the MB/NMB, MG/NMG severity confound documented in
docs/RQ1_MECHANISM_ANALYSIS_v1.1.md section 1.

One family (WORK-MG-02) has no curation severity record and is dropped from
BOTH the baseline and severity-adjusted fits here, so the two are compared
on an identical sample.
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
    sub = d[(d["question"] == "intentionality") & (d["tuning_status"] == "finetuned")
            & (d["vt"].isin(["moral", "nonmoral"]))].dropna(subset=["sign_c", "vt_c", "severity_c"])

    rows = []
    for fam in FAMS:
        s = sub[sub["family"] == fam]

        m0 = smf.mixedlm("ev_rating ~ sign_c * vt_c", s, groups=s["set_id"]).fit(reml=False, method="lbfgs")
        wcb0 = wild_cluster_bootstrap(s, "ev_rating ~ sign_c * vt_c", "sign_c:vt_c", "set_id", seed=1)
        rows.append(dict(model="baseline", family=fam, term="sign_c:vt_c",
                          lmm_estimate=m0.params["sign_c:vt_c"], lmm_p=m0.pvalues["sign_c:vt_c"], **wcb0))

        m1 = smf.mixedlm("ev_rating ~ sign_c * vt_c + severity_c", s, groups=s["set_id"]).fit(reml=False, method="lbfgs")
        wcb1 = wild_cluster_bootstrap(s, "ev_rating ~ sign_c * vt_c + severity_c", "sign_c:vt_c", "set_id", seed=1)
        rows.append(dict(model="+severity_c", family=fam, term="sign_c:vt_c",
                          lmm_estimate=m1.params["sign_c:vt_c"], lmm_p=m1.pvalues["sign_c:vt_c"], **wcb1,
                          severity_coef=m1.params["severity_c"], severity_p=m1.pvalues["severity_c"]))

    out = pd.DataFrame(rows)
    print(out.to_string(index=False))
    save(out, "04_rq1a_severity_covariate.csv")


if __name__ == "__main__":
    main()
