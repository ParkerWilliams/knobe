"""The corrected severity-adjusted RQ1a wild-cluster-bootstrap: set-fixed-
effects refit (not plain pooled OLS -- see 13_rq1a_severity_set_fe_diagnostic.py
for why that matters), at G=21 (set_id). Supersedes the "+severity_c" rows
in 04_rq1a_severity_covariate.py's output for any purpose that needs a
trustworthy point estimate/SE (the baseline, no-severity rows in that file
are unaffected -- sign_c/vt_c alone are a balanced categorical design where
pooled OLS ~= GLS, confirmed in docs/RQ1_STATISTICAL_METHODS_v1.1.md section
7.1).
"""
from __future__ import annotations

import warnings

import pandas as pd

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
        wcb = wild_cluster_bootstrap(
            s, "ev_rating ~ sign_c * vt_c + severity_c + C(set_id)", "sign_c:vt_c",
            "set_id", seed=1,
        )
        rows.append(dict(family=fam, term="sign_c:vt_c", **wcb))

    out = pd.DataFrame(rows)
    print(out.to_string(index=False))
    save(out, "14_rq1a_severity_set_fe_wcb.csv")


if __name__ == "__main__":
    main()
