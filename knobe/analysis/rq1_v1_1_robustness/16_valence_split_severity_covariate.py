"""Severity-adjusted version of the direct moral-only/nonmoral-only sign
split (05_valence_split_wcb.py), per docs/RQ1_MECHANISM_ANALYSIS_v1.1.md's
open follow-up: does the surviving moral-specific sign effect (gemma/llama)
hold up once severity is controlled for WITHIN each valence type?

Expectation going in, stated before running (per this project's
cost-check/prediction discipline): severity correlates with sign at r=.885
within moral items (MB items were authored around "genuine harm," which is
inherently high-severity, with no matched-severity requirement against MG)
vs. r=.473 within nonmoral items -- so the moral-only severity-adjusted test
is expected to lose most of its identifying variance (severity ~= sign
there) and likely fail to reach significance for that reason specifically,
not because the underlying effect is smaller. The nonmoral-only test has
more separable variance (r=.473) and is a cleaner check of whether its
already-null result stays null once severity is controlled for.
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
    sub = d[(d["question"] == "intentionality") & (d["tuning_status"] == "finetuned")].dropna(
        subset=["sign_c", "severity_c"]
    )

    rows = []
    for fam in FAMS:
        for vt in ["moral", "nonmoral"]:
            s = sub[(sub["family"] == fam) & (sub["vt"] == vt)]

            m0 = smf.mixedlm("ev_rating ~ sign_c", s, groups=s["family_id"]).fit(reml=False, method="lbfgs")
            wcb0 = wild_cluster_bootstrap(s, "ev_rating ~ sign_c", "sign_c", "family_id", seed=11)
            rows.append(dict(model="baseline", family=fam, valence_type=vt,
                              lmm_estimate=m0.params["sign_c"], lmm_p=m0.pvalues["sign_c"], **wcb0))

            m1 = smf.mixedlm("ev_rating ~ sign_c + severity_c", s, groups=s["family_id"]).fit(reml=False, method="lbfgs")
            wcb1 = wild_cluster_bootstrap(s, "ev_rating ~ sign_c + severity_c", "sign_c", "family_id", seed=11)
            rows.append(dict(model="+severity_c", family=fam, valence_type=vt,
                              lmm_estimate=m1.params["sign_c"], lmm_p=m1.pvalues["sign_c"], **wcb1,
                              severity_coef=m1.params["severity_c"], severity_p=m1.pvalues["severity_c"]))

    out = pd.DataFrame(rows)
    print(out.to_string(index=False))
    save(out, "16_valence_split_severity_covariate.csv")


if __name__ == "__main__":
    main()
