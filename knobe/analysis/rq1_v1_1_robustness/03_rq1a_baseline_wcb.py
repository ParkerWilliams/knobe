"""Wild-cluster-bootstrap validation at G=21 (set_id) for RQ1a
sign_x_valence_type, no severity covariate -- see
docs/rq1_findings/RQ1_STATISTICAL_METHODS_v1.1.md section 8. Companion:
04_rq1a_severity_covariate.py adds the severity control and re-runs WCB.
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
            & (d["vt"].isin(["moral", "nonmoral"]))].dropna(subset=["sign_c", "vt_c"])

    rows = []
    for fam in FAMS:
        s = sub[sub["family"] == fam]
        m = smf.mixedlm("ev_rating ~ sign_c * vt_c", s, groups=s["set_id"]).fit(reml=False, method="lbfgs")
        wcb = wild_cluster_bootstrap(s, "ev_rating ~ sign_c * vt_c", "sign_c:vt_c", "set_id", seed=1)
        rows.append(dict(contrast="rq1a_sign_x_valence_type", family=fam, term="sign_c:vt_c",
                          lmm_estimate=m.params["sign_c:vt_c"], lmm_p=m.pvalues["sign_c:vt_c"], **wcb))

    out = pd.DataFrame(rows)
    print(out.to_string(index=False))
    save(out, "03_rq1a_baseline_wcb.csv")


if __name__ == "__main__":
    main()
