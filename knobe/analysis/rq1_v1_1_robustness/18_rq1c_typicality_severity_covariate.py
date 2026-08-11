"""Does RQ1c's typicality x sign finding survive controlling for severity?

Motivated by a reviewer question: if severity is doing real work on the
sign asymmetry (RQ1a), does typicality itself correlate with severity in
this item set -- in which case some of "typicality dampens the asymmetry"
could be a severity story in disguise? Checked first
(`data/curation/curated_v1.1.csv`): uncommon actions read as slightly MORE
severe than common ones, consistently across every valence category (MB
6.6->7.5, MG 1.8->2.0, NMB 1.6->1.7, NMG 0.7->1.1), but the correlation is
weak (r=.07-.15) -- much smaller than RQ1a's r=.885 within moral items.
Checked for the OLS-vs-GLS divergence (the recurring pooled-OLS-with-a-
continuous-covariate bug, found 3x already this session) before trusting a
plain WCB: none here -- family_id clustering matches the level severity_c
is defined at, with balanced cluster sizes (same reason
16_valence_split_severity_covariate.py needed no fix either).
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
            & (d["vt"].isin(["moral", "nonmoral"]))].dropna(subset=["sign_c", "typ_c", "severity_c"])

    rows = []
    for fam in FAMS:
        s = sub[sub["family"] == fam]

        m0 = smf.mixedlm("ev_rating ~ typ_c * sign_c", s, groups=s["family_id"]).fit(reml=False, method="lbfgs")
        wcb0 = wild_cluster_bootstrap(s, "ev_rating ~ typ_c * sign_c", "typ_c:sign_c", "family_id", seed=3)
        rows.append(dict(model="baseline", family=fam, term="typ_c:sign_c",
                          lmm_estimate=m0.params["typ_c:sign_c"], lmm_p=m0.pvalues["typ_c:sign_c"], **wcb0))

        m1 = smf.mixedlm("ev_rating ~ typ_c * sign_c + severity_c", s, groups=s["family_id"]).fit(reml=False, method="lbfgs")
        wcb1 = wild_cluster_bootstrap(s, "ev_rating ~ typ_c * sign_c + severity_c", "typ_c:sign_c", "family_id", seed=3)
        rows.append(dict(model="+severity_c", family=fam, term="typ_c:sign_c",
                          lmm_estimate=m1.params["typ_c:sign_c"], lmm_p=m1.pvalues["typ_c:sign_c"], **wcb1,
                          severity_coef=m1.params["severity_c"], severity_p=m1.pvalues["severity_c"]))

    out = pd.DataFrame(rows)
    print(out.to_string(index=False))
    save(out, "18_rq1c_typicality_severity_covariate.csv")


if __name__ == "__main__":
    main()
