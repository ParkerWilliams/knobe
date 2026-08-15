"""Wild-cluster-bootstrap the RQ1_base `sign_c` MAIN EFFECT (bad vs. good,
moral+nonmoral pooled, finetuned models only) -- the literal "classic Knobe
effect" contrast (`rq1_base_sign_finetuned` in
docs/RQ1_STATISTICAL_METHODS_v1.1.md section 6's table), which script 01
never bootstrapped: 01 only tests the `sign_c:tuning_c` interaction, never
the bare `sign_c` term. That contrast has so far only been reported as an
asymptotic Wald p-value (gemma p=.091, llama p=.095, mistral p=.495) -- this
closes that gap with the same WCB machinery used everywhere else in this
directory (cluster=family_id, G=84).
"""
from __future__ import annotations

import warnings

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
    base = d[
        (d["question"] == "intentionality")
        & (d["tuning_status"] == "finetuned")
        & (d["vt"].isin(["moral", "nonmoral"]))
    ].dropna(subset=["sign_c"])

    rows = []
    for fam in FAMS:
        s = base[base["family"] == fam]
        b_lmm, p_lmm = lmm(s, "ev_rating ~ sign_c", "sign_c")
        wcb = wild_cluster_bootstrap(s, "ev_rating ~ sign_c", "sign_c", "family_id", seed=20)
        rows.append(dict(contrast="rq1_base_sign_finetuned", family=fam, term="sign_c",
                          lmm_estimate=b_lmm, lmm_p=p_lmm, **wcb))

    out = pd.DataFrame(rows)
    print(out.to_string(index=False))
    save(out, "31_rq1_base_sign_main_effect_wcb.csv")


if __name__ == "__main__":
    main()
