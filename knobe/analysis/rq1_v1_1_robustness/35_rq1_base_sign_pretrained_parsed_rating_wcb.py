"""Is the pretrained sign_c reversal (33, 34: gemma survives even moral-only,
beta=-.172 p=.000) a genuine behavioral finding, or an artifact of the
logit-fallback ev_rating score on pretrained models, which mostly don't
produce a parseable numeric answer? Reuses the exact substitution method
already established in 26_ev_scoring_validation.py (item 11: parse_ok-only
rows, parsed_rating in place of ev_rating) -- not new machinery -- applied
to this specific cell (pretrained, moral-only, sign_c) instead of RQ1c.

Descriptive check first (not committed as a script) found ev_rating/
parsed_rating correlation on pretrained rows is ~0-0.11 across all 3
families (vs .44-.50 for instruct, per item 11), and raw parsed_rating
means for gemma/mistral point the CLASSIC direction (bad > good) while
ev_rating points reversed. This runs the formal WCB test on the
parse_ok-only subset with parsed_rating as the outcome.
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
    sub = d[(d["question"] == "intentionality") & (d["tuning_status"] == "pretrained")
            & (d["vt"] == "moral") & (d["parse_ok"])].dropna(subset=["sign_c", "parsed_rating"])

    rows = []
    for fam in FAMS:
        s = sub[sub["family"] == fam]
        m = smf.mixedlm("parsed_rating ~ sign_c", s, groups=s["family_id"]).fit(reml=False, method="lbfgs")
        wcb = wild_cluster_bootstrap(s, "parsed_rating ~ sign_c", "sign_c", "family_id", seed=24)
        rows.append(dict(contrast="rq1_base_sign_pretrained_moral_parsed_rating", family=fam, term="sign_c",
                          n=len(s),
                          lmm_estimate=m.params["sign_c"], lmm_p=m.pvalues["sign_c"], **wcb))

    out = pd.DataFrame(rows)
    print(out.to_string(index=False))
    save(out, "35_rq1_base_sign_pretrained_parsed_rating_wcb.csv")


if __name__ == "__main__":
    main()
