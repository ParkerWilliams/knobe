"""Direct dose-response test: does the bad-good intentionality gap widen
CONTINUOUSLY with severity, fit at the exact same clustering level and
subset as rq1c_typicality_x_sign / rq1c_evocativeness_x_sign (family_id,
G=84, finetuned, moral+nonmoral pooled) -- a term type the pipeline already
knows how to fit, just substituting severity_c for typ_c/evoc_c:

    ev_rating ~ severity_c * sign_c, groups=family_id

This is a genuinely different test from 17_severity_vs_label.py's
"B_severity_alone" model, which fit the same nominal interaction at SET_ID
clustering (G=21) to match RQ1a's own convention -- set-clustering and
family-clustering behave very differently for RQ1a-style variables (that's
the entire reason set-clustering was introduced), so this family_id version
is a real robustness comparison, not a repeat.

Checked for the OLS-vs-GLS divergence first (the recurring bug from
06/13/17): none here -- family_id clustering matches severity_c's level
exactly, same reason 16 and 18 needed no fix.

If severity is the real engine (docs/SEVERITY_MORALIZATION_BACKGROUND.md's
"constitutive, not just correlated" reading), this interaction should be
sizeable and reliable -- the gap should widen continuously with severity,
not just jump at the moral/nonmoral category boundary.
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
            & (d["vt"].isin(["moral", "nonmoral"]))].dropna(subset=["sign_c", "severity_c"])

    rows = []
    for fam in FAMS:
        s = sub[sub["family"] == fam]
        m = smf.mixedlm("ev_rating ~ severity_c * sign_c", s, groups=s["family_id"]).fit(reml=False, method="lbfgs")
        wcb = wild_cluster_bootstrap(s, "ev_rating ~ severity_c * sign_c", "severity_c:sign_c", "family_id", seed=19)
        rows.append(dict(contrast="severity_dose_response", family=fam, term="severity_c:sign_c",
                          lmm_estimate=m.params["severity_c:sign_c"], lmm_p=m.pvalues["severity_c:sign_c"], **wcb))

    out = pd.DataFrame(rows)
    print(out.to_string(index=False))
    save(out, "19_severity_dose_response.csv")

    print()
    print("For comparison, rq1c's structurally identical terms (same clustering/subset, from 01_rq1_base_and_rq1c_wcb.csv):")
    rq1c = pd.read_csv("outputs/01_rq1_base_and_rq1c_wcb.csv")
    print(rq1c[rq1c["contrast"].str.startswith("rq1c")][["contrast", "family", "lmm_estimate", "p_wcb"]].to_string(index=False))


if __name__ == "__main__":
    main()
