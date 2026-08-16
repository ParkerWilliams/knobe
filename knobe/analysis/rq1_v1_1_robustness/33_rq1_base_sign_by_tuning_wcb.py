"""What actually drives the significant sign_c:tuning_c interaction
(01_rq1_base_and_rq1c_wcb.py, gemma/llama survive WCB)? 31 established the
finetuned-only sign_c main effect is marginal-to-null (gemma p=.106, llama
p=.102, mistral p=.533). This fills the missing complement -- the
pretrained-only sign_c main effect -- to see whether the interaction is
driven by a strong finetuned effect (it isn't, per 31) or something else
entirely on the pretrained side.
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
    base = d[(d["question"] == "intentionality") & (d["vt"].isin(["moral", "nonmoral"]))].dropna(subset=["sign_c"])

    rows = []
    for fam in FAMS:
        for tuning in ["pretrained", "finetuned"]:
            s = base[(base["family"] == fam) & (base["tuning_status"] == tuning)]
            m = smf.mixedlm("ev_rating ~ sign_c", s, groups=s["family_id"]).fit(reml=False, method="lbfgs")
            wcb = wild_cluster_bootstrap(s, "ev_rating ~ sign_c", "sign_c", "family_id", seed=22)
            rows.append(dict(contrast="rq1_base_sign_by_tuning", family=fam, tuning_status=tuning, term="sign_c",
                              lmm_estimate=m.params["sign_c"], lmm_p=m.pvalues["sign_c"], **wcb))

    out = pd.DataFrame(rows)
    print(out.to_string(index=False))
    save(out, "33_rq1_base_sign_by_tuning_wcb.csv")


if __name__ == "__main__":
    main()
