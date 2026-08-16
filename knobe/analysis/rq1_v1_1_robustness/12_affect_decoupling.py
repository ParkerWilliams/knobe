"""Within-family self-reported-affect-to-intentionality coupling, and
whether instruction-tuning changes it.

Source of docs/rq1_findings/RQ1_MECHANISM_ANALYSIS_v1.1.md section 4's second table
(the "affect decoupling" finding): for each subject family x sign, demean
both self-reported affect_salience and intentionality within
(model_key, family_id, sign) -- stripping the family-level confound (more
severe/high-stakes scenarios rate higher on both regardless of the
typicality/evocativeness manipulation) -- then fit
`intentionality_demeaned ~ affect_demeaned * instruct` and read off the
pretrained-checkpoint slope and the instruct-checkpoint shift.

NOTE (per docs/rq1_findings/RQ1_MECHANISM_ANALYSIS_v1.1.md section 4): this result has
NOT been put through the same wild-cluster-bootstrap / family-random-slope
rigor as everything else in this directory (it's a plain OLS Wald p-value on
a small within-family sample, 4 variants x ~21 families per sign). Given how
many Wald-significant findings elsewhere did not survive that treatment,
read this as a lead, not a confirmed result, until it does.
"""
from __future__ import annotations

import warnings

import pandas as pd
import statsmodels.formula.api as smf

from lib import load_frame, save

warnings.filterwarnings("ignore")

FAMS = ["gemma", "llama", "mistral"]


def main() -> None:
    d = load_frame()

    agg = (
        d[d["question"].isin(["intentionality", "affect_salience"])]
        .groupby(["model_key", "family", "tuning_status", "family_id", "variant_id", "question"])["ev_rating"]
        .mean()
        .unstack("question")
        .reset_index()
    )
    agg = agg.merge(
        d[["variant_id", "sign"]].drop_duplicates("variant_id"),
        on="variant_id",
    )
    agg["aff_dm"] = agg.groupby(["model_key", "family_id", "sign"])["affect_salience"].transform(lambda x: x - x.mean())
    agg["int_dm"] = agg.groupby(["model_key", "family_id", "sign"])["intentionality"].transform(lambda x: x - x.mean())
    agg["instruct"] = (agg["tuning_status"] == "finetuned").astype(int)

    rows = []
    for fam in FAMS:
        for sign in ["bad", "good"]:
            sub = agg[(agg["family"] == fam) & (agg["sign"] == sign)]
            m = smf.ols("int_dm ~ aff_dm * instruct", data=sub).fit()
            rows.append(dict(
                family=fam, sign=sign,
                slope_pretrained=m.params["aff_dm"],
                shift_under_instruct=m.params["aff_dm:instruct"],
                shift_p=m.pvalues["aff_dm:instruct"],
                n_obs=len(sub),
            ))

    out = pd.DataFrame(rows)
    print(out.to_string(index=False))
    save(out, "12_affect_decoupling.csv")


if __name__ == "__main__":
    main()
