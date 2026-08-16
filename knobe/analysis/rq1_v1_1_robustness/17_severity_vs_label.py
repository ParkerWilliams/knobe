"""Does continuous severity predict the sign asymmetry as well as the
moral/nonmoral categorical label -- and does the label survive once
severity's own interaction with sign is in the model?

Three models, same degrees of freedom (each is an intercept + 2 main effects
+ 1 interaction), fit via LMM (groups=set_id, ML) for point estimates/AIC
and via a SET-FIXED-EFFECTS wild cluster bootstrap for valid small-G
inference (checked first via an RE-vs-pooled-OLS comparison -- severity_c is
a continuous, set_id-correlated covariate, so, per the lesson from
06_rq1b_hausman_diagnostic.py / 13_rq1a_severity_set_fe_diagnostic.py, plain
pooled OLS is expected to diverge here too, and does: gemma's pooled-OLS
sign_c:severity_c estimate was -0.190 against the RE estimate of -0.086).

  A (label alone):    ev_rating ~ sign_c * vt_c
  B (severity alone):  ev_rating ~ sign_c * severity_c
  C (combined):        ev_rating ~ sign_c * vt_c + sign_c * severity_c

Context: docs/severity_confound/SEVERITY_MORALIZATION_BACKGROUND.md -- this project's own
taxonomy defines "moral" as harm/welfare-affecting (constants.py's
GENERATION_SYSTEM_PROMPT explicitly excludes purity/loyalty/authority
content), so severity and moral status may not be independently
manipulable even in principle here, not just in this particular sample.
"""
from __future__ import annotations

import warnings

import pandas as pd
import statsmodels.formula.api as smf

from lib import load_frame, wild_cluster_bootstrap, save

warnings.filterwarnings("ignore")

FAMS = ["gemma", "llama", "mistral"]

MODELS = {
    "A_label_alone": ("ev_rating ~ sign_c * vt_c", "sign_c:vt_c"),
    "B_severity_alone": ("ev_rating ~ sign_c * severity_c", "sign_c:severity_c"),
    "C_combined": ("ev_rating ~ sign_c * vt_c + sign_c * severity_c", None),  # two terms of interest
}


def fe_formula(formula: str) -> str:
    return f"{formula} + C(set_id)"


def main() -> None:
    d = load_frame()
    sub = d[(d["question"] == "intentionality") & (d["tuning_status"] == "finetuned")
            & (d["vt"].isin(["moral", "nonmoral"]))].dropna(subset=["sign_c", "vt_c", "severity_c"])

    rows = []
    for fam in FAMS:
        s = sub[sub["family"] == fam]

        re_a = smf.mixedlm("ev_rating ~ sign_c * vt_c", s, groups=s["set_id"]).fit(reml=False, method="lbfgs")
        wcb_a = wild_cluster_bootstrap(s, fe_formula("ev_rating ~ sign_c * vt_c"), "sign_c:vt_c", "set_id", seed=17)
        rows.append(dict(model="A_label_alone", family=fam, term="sign_c:vt_c",
                          lmm_estimate=re_a.params["sign_c:vt_c"], aic=re_a.aic, **wcb_a))

        re_b = smf.mixedlm("ev_rating ~ sign_c * severity_c", s, groups=s["set_id"]).fit(reml=False, method="lbfgs")
        wcb_b = wild_cluster_bootstrap(s, fe_formula("ev_rating ~ sign_c * severity_c"), "sign_c:severity_c", "set_id", seed=17)
        rows.append(dict(model="B_severity_alone", family=fam, term="sign_c:severity_c",
                          lmm_estimate=re_b.params["sign_c:severity_c"], aic=re_b.aic, **wcb_b))

        re_c = smf.mixedlm("ev_rating ~ sign_c * vt_c + sign_c * severity_c", s, groups=s["set_id"]).fit(reml=False, method="lbfgs")
        wcb_c1 = wild_cluster_bootstrap(s, fe_formula("ev_rating ~ sign_c * vt_c + sign_c * severity_c"), "sign_c:vt_c", "set_id", seed=17)
        wcb_c2 = wild_cluster_bootstrap(s, fe_formula("ev_rating ~ sign_c * vt_c + sign_c * severity_c"), "sign_c:severity_c", "set_id", seed=18)
        rows.append(dict(model="C_combined", family=fam, term="sign_c:vt_c",
                          lmm_estimate=re_c.params["sign_c:vt_c"], aic=re_c.aic, **wcb_c1))
        rows.append(dict(model="C_combined", family=fam, term="sign_c:severity_c",
                          lmm_estimate=re_c.params["sign_c:severity_c"], aic=re_c.aic, **wcb_c2))

    out = pd.DataFrame(rows)
    print(out.to_string(index=False))
    save(out, "17_severity_vs_label.csv")


if __name__ == "__main__":
    main()
