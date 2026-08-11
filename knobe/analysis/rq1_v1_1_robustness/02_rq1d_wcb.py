"""Wild-cluster-bootstrap validation at G=21 (family_id, NEU only) for RQ1d
neu_offset and typicality_within_neu -- see
docs/RQ1_STATISTICAL_METHODS_v1.1.md section 8. This is the RQ that survives
overwhelmingly (p_wcb=.000 in every cell) -- the strongest result in the
release.
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
    neu = d[(d["question"] == "intentionality") & (d["tuning_status"] == "finetuned") & (d["valence"] == "NEU")].copy()
    neu["rating_centered"] = neu["ev_rating"] - 5.0

    rows = []
    for fam in FAMS:
        s = neu[neu["family"] == fam]

        m = smf.mixedlm("rating_centered ~ 1", s, groups=s["family_id"]).fit(reml=False, method="lbfgs")
        wcb = wild_cluster_bootstrap(s, "rating_centered ~ 1", "Intercept", "family_id", seed=5)
        rows.append(dict(contrast="rq1d_neu_offset", family=fam, term="Intercept",
                          lmm_estimate=m.params["Intercept"], lmm_p=m.pvalues["Intercept"], **wcb))

        m2 = smf.mixedlm("ev_rating ~ typ_c", s, groups=s["family_id"]).fit(reml=False, method="lbfgs")
        wcb2 = wild_cluster_bootstrap(s, "ev_rating ~ typ_c", "typ_c", "family_id", seed=6)
        rows.append(dict(contrast="rq1d_typicality_within_neu", family=fam, term="typ_c",
                          lmm_estimate=m2.params["typ_c"], lmm_p=m2.pvalues["typ_c"], **wcb2))

    out = pd.DataFrame(rows)
    print(out.to_string(index=False))
    save(out, "02_rq1d_wcb.csv")


if __name__ == "__main__":
    main()
