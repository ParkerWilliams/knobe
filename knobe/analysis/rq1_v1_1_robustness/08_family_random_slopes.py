"""Family random-SLOPE sensitivity check: refits each focal term that varies
WITHIN family (tuning_c for RQ1_base; typ_c, evoc_c for RQ1c; pred_c for
RQ1b) with a random intercept AND slope per family_id
(re_formula="~<term>"), comparing the focal interaction's SE to the
random-intercept-only primary model. sign_c and vt_c do not vary within
family (RQ1a has no equivalent check -- see docs/RQ1_STATISTICAL_METHODS_v1.1.md
section 11).

This independently reproduces the wild-cluster-bootstrap p-values in
01/02_*_wcb.csv via completely different machinery (a parametric
random-effects model vs. a resampling test) -- see the README for the
cross-check.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from lib import load_frame, build_1b_frame, save, CONFIG

warnings.filterwarnings("ignore")

FAMS = ["gemma", "llama", "mistral"]


def fit_ri(sub, formula, term, groups_col="family_id"):
    m = smf.mixedlm(formula, sub, groups=sub[groups_col]).fit(reml=False, method="lbfgs")
    return m.params[term], m.bse[term], m.pvalues[term], bool(m.converged)


def fit_rs(sub, formula, term, groups_col, re_formula):
    try:
        m = smf.mixedlm(formula, sub, groups=sub[groups_col], re_formula=re_formula).fit(reml=False, method="lbfgs")
        return m.params[term], m.bse[term], m.pvalues[term], bool(m.converged)
    except Exception as e:
        return None, None, None, f"FAILED: {e}"


def main() -> None:
    d = load_frame()
    rows = []

    base = d[(d["question"] == "intentionality") & (d["vt"].isin(["moral", "nonmoral"]))].dropna(subset=["sign_c"])
    base = base.assign(tuning_c=np.where(base["tuning_status"] == "finetuned", 0.5, -0.5))
    for fam in FAMS:
        s = base[base["family"] == fam]
        b0, se0, p0, c0 = fit_ri(s, "ev_rating ~ sign_c * tuning_c", "sign_c:tuning_c")
        b1, se1, p1, c1 = fit_rs(s, "ev_rating ~ sign_c * tuning_c", "sign_c:tuning_c", "family_id", "~tuning_c")
        rows.append(dict(contrast="rq1_base_sign_x_tuning", family=fam,
                          ri_estimate=b0, ri_se=se0, ri_p=p0,
                          slope_estimate=b1, slope_se=se1, slope_p=p1, slope_converged=c1))

    c = d[(d["question"] == "intentionality") & (d["tuning_status"] == "finetuned")
          & (d["vt"].isin(["moral", "nonmoral"]))].dropna(subset=["sign_c", "typ_c", "evoc_c"])
    for fam in FAMS:
        s = c[c["family"] == fam]
        b0, se0, p0, c0 = fit_ri(s, "ev_rating ~ typ_c * sign_c", "typ_c:sign_c")
        b1, se1, p1, c1 = fit_rs(s, "ev_rating ~ typ_c * sign_c", "typ_c:sign_c", "family_id", "~typ_c")
        rows.append(dict(contrast="rq1c_typicality_x_sign", family=fam,
                          ri_estimate=b0, ri_se=se0, ri_p=p0,
                          slope_estimate=b1, slope_se=se1, slope_p=p1, slope_converged=c1))

        b0, se0, p0, c0 = fit_ri(s, "ev_rating ~ evoc_c * sign_c", "evoc_c:sign_c")
        b1, se1, p1, c1 = fit_rs(s, "ev_rating ~ evoc_c * sign_c", "evoc_c:sign_c", "family_id", "~evoc_c")
        rows.append(dict(contrast="rq1c_evocativeness_x_sign", family=fam,
                          ri_estimate=b0, ri_se=se0, ri_p=p0,
                          slope_estimate=b1, slope_se=se1, slope_p=p1, slope_converged=c1))

    model_keys = CONFIG["family_model_keys"]
    for fam in FAMS:
        mk = model_keys[fam]["instruct"]
        for vt in ["moral", "nonmoral"]:
            frame = build_1b_frame(d, mk, vt)
            b0, se0, p0, c0 = fit_ri(frame, "ev_rating ~ pred_c * sg_c", "pred_c:sg_c")
            b1, se1, p1, c1 = fit_rs(frame, "ev_rating ~ pred_c * sg_c", "pred_c:sg_c", "family_id", "~pred_c")
            rows.append(dict(contrast=f"rq1b_{vt}", family=fam,
                              ri_estimate=b0, ri_se=se0, ri_p=p0,
                              slope_estimate=b1, slope_se=se1, slope_p=p1, slope_converged=c1,
                              note="RQ1b's pred_c is family-correlated (see 06_rq1b_hausman_diagnostic.py) "
                                   "-- a random slope on it is vulnerable to the same endogeneity a fixed "
                                   "effect avoids; treat these rows as a disagreement to resolve, not a clean result."))

    out = pd.DataFrame(rows)
    print(out.to_string(index=False))
    save(out, "08_family_random_slopes.csv")


if __name__ == "__main__":
    main()
