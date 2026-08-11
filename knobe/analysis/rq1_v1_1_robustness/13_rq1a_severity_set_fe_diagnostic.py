"""RE (MixedLM, groups=set_id) vs. pooled-OLS vs. set-fixed-effects
comparison for the SEVERITY-ADJUSTED RQ1a model
(`ev_rating ~ sign_c * vt_c + severity_c`).

Discovered while trying to finish the severity-adjusted MDE table: the LMM
estimate and 04_rq1a_severity_covariate.py's plain-pooled-OLS WCB estimate
disagree substantially (gemma even flips sign: LMM +0.28 vs. pooled-OLS
-0.98). This is the same class of problem diagnosed for RQ1b in
06_rq1b_hausman_diagnostic.py: severity_c is a continuous, family-level
covariate, not a balanced +/-0.5 design factor, so plain pooled OLS and the
GLS-based mixedlm stop agreeing once it's in the model.

Unlike RQ1b, sign_c and vt_c both vary WITHIN a set_id (a set's four non-NEU
members span MB/MG/NMB/NMG), so a set-fixed-effects specification is
well-identified here too -- no term needs to be dropped for collinearity,
unlike RQ1b's bare sg_c.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from lib import load_frame, save

warnings.filterwarnings("ignore")

FAMS = ["gemma", "llama", "mistral"]


def main() -> None:
    d = load_frame()
    sub = d[(d["question"] == "intentionality") & (d["tuning_status"] == "finetuned")
            & (d["vt"].isin(["moral", "nonmoral"]))].dropna(subset=["sign_c", "vt_c", "severity_c"])

    rows = []
    for fam in FAMS:
        s = sub[sub["family"] == fam]

        re = smf.mixedlm("ev_rating ~ sign_c * vt_c + severity_c", s, groups=s["set_id"]).fit(reml=False, method="lbfgs")
        pooled = smf.ols("ev_rating ~ sign_c * vt_c + severity_c", s).fit(cov_type="cluster", cov_kwds={"groups": s["set_id"]})
        fe = smf.ols("ev_rating ~ sign_c * vt_c + severity_c + C(set_id)", s).fit(cov_type="cluster", cov_kwds={"groups": s["set_id"]})

        fam_mean_sev = s.groupby("set_id")["severity_c"].transform("mean")
        corr = float(np.corrcoef(s["severity_c"], fam_mean_sev)[0, 1])

        rows.append(dict(
            family=fam,
            re_mixedlm=re.params["sign_c:vt_c"],
            pooled_ols=pooled.params["sign_c:vt_c"],
            set_fe=fe.params["sign_c:vt_c"],
            corr_severity_set_mean=corr,
        ))

    out = pd.DataFrame(rows)
    print(out.to_string(index=False))
    save(out, "13_rq1a_severity_set_fe_diagnostic.csv")


if __name__ == "__main__":
    main()
