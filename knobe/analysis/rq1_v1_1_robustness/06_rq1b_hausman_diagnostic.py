"""RE (MixedLM) vs. pooled-OLS vs. family-fixed-effects comparison for RQ1b's
pred_c:sg_c term -- the Hausman-style diagnostic that (a) explains why the
first-pass wild-cluster-bootstrap for RQ1b gave nonsensical, sign-flipped
results, and (b) motivated the actual pipeline fix in
src/knobe/analysis/models.py (_bootstrap_formula). See
docs/RQ1_STATISTICAL_METHODS_v1.1.md section 10.1.

FE and RE should agree closely (both correctly separate within-family
covariation from the family-level confound); pooled OLS should diverge,
because pred_c correlates strongly with family identity (also reported here,
"corr_pred_c_family_mean").
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from lib import load_frame, build_1b_frame, save, CONFIG

warnings.filterwarnings("ignore")

FAMS = ["gemma", "llama", "mistral"]


def main() -> None:
    d = load_frame()
    model_keys = CONFIG["family_model_keys"]

    rows = []
    for fam in FAMS:
        mk = model_keys[fam]["instruct"]
        for vt in ["moral", "nonmoral"]:
            frame = build_1b_frame(d, mk, vt)

            re = smf.mixedlm("ev_rating ~ pred_c * sg_c", frame, groups=frame["family_id"]).fit(reml=False, method="lbfgs")
            pooled = smf.ols("ev_rating ~ pred_c * sg_c", frame).fit(cov_type="cluster", cov_kwds={"groups": frame["family_id"]})
            fe = smf.ols("ev_rating ~ pred_c + pred_c:sg_c + C(family_id)", frame).fit(cov_type="cluster", cov_kwds={"groups": frame["family_id"]})

            fam_mean_pred = frame.groupby("family_id")["pred_c"].transform("mean")
            corr = float(np.corrcoef(frame["pred_c"], fam_mean_pred)[0, 1])

            rows.append(dict(
                family=fam, valence_type=vt,
                re_mixedlm=re.params["pred_c:sg_c"],
                pooled_ols=pooled.params["pred_c:sg_c"],
                family_fe=fe.params["pred_c:sg_c"],
                corr_pred_c_family_mean=corr,
            ))

    out = pd.DataFrame(rows)
    print(out.to_string(index=False))
    save(out, "06_rq1b_hausman_diagnostic.csv")


if __name__ == "__main__":
    main()
