"""Is the pretrained sign_c reversal (33_rq1_base_sign_by_tuning_wcb.py: all 3
families significant, good rated more intentional than bad) an artifact of
pooling moral+nonmoral together in the pretrained arm -- content Raimondi
et al. (arXiv:2510.12229) never had, since their 80 scenarios are all
moral-valence? Raimondi's own reported pretrained deltas are small and
POSITIVE (classic direction): llama +0.24, mistral +0.06, gemma +0.51. This
restricts our pretrained sign_c test to moral-only content -- the actual
apples-to-apples scope against their design -- to see whether the
reversal survives or was a pooling artifact.
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
            & (d["vt"] == "moral")].dropna(subset=["sign_c"])

    rows = []
    for fam in FAMS:
        s = sub[sub["family"] == fam]
        m = smf.mixedlm("ev_rating ~ sign_c", s, groups=s["family_id"]).fit(reml=False, method="lbfgs")
        wcb = wild_cluster_bootstrap(s, "ev_rating ~ sign_c", "sign_c", "family_id", seed=23)
        rows.append(dict(contrast="rq1_base_sign_pretrained_moral_only", family=fam, term="sign_c",
                          lmm_estimate=m.params["sign_c"], lmm_p=m.pvalues["sign_c"], **wcb))

    out = pd.DataFrame(rows)
    print(out.to_string(index=False))
    save(out, "34_rq1_base_sign_pretrained_moral_only_wcb.csv")


if __name__ == "__main__":
    main()
