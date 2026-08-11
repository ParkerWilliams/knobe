"""The corrected RQ1b wild-cluster-bootstrap: family-fixed-effects refit
(not plain pooled OLS -- see 06_rq1b_hausman_diagnostic.py for why that
matters), at G=42 (family_id). This is the actual result cited in both
revised docs. The bare sg_c main effect is dropped from the formula because
sign is constant within a family/valence, so once family dummies are in the
model sg_c is perfectly collinear with them (confirmed empirically: leaving
it in produces degenerate near-zero t-statistics).
"""
from __future__ import annotations

import warnings

import pandas as pd

from lib import load_frame, build_1b_frame, wild_cluster_bootstrap, save, CONFIG

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
            wcb = wild_cluster_bootstrap(
                frame, "ev_rating ~ pred_c + pred_c:sg_c + C(family_id)", "pred_c:sg_c",
                "family_id", seed=9,
            )
            rows.append(dict(family=fam, valence_type=vt, term="pred_c:sg_c", **wcb))

    out = pd.DataFrame(rows)
    print(out.to_string(index=False))
    save(out, "07_rq1b_family_fe_wcb.csv")


if __name__ == "__main__":
    main()
