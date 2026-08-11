"""Descriptive bad-good intentionality gap, split by typicality condition and
separately by evocativeness condition (finetuned/instruct checkpoints only).

This is the source of docs/RQ1_MECHANISM_ANALYSIS_v1.1.md section 3's "gap,
common/typical" vs "gap, uncommon/atypical" table -- the descriptive
companion to the rq1c_typicality_x_sign / rq1c_evocativeness_x_sign LMM
interaction coefficients (01_rq1_base_and_rq1c_wcb.py). The evocativeness
split was also computed in the same original exploratory pass but did not
end up quoted in the final doc revision -- included here anyway for
completeness (every number actually run this session should be
reproducible, not just the ones that made the final prose).
"""
from __future__ import annotations

import warnings

import pandas as pd

from lib import load_frame, save

warnings.filterwarnings("ignore")


def main() -> None:
    d = load_frame()
    sub = d[(d["question"] == "intentionality") & (d["tuning_status"] == "finetuned")
            & d["sign"].isin(["bad", "good"])]

    typ = sub.groupby(["family", "typicality", "sign"])["ev_rating"].mean().unstack("sign")
    typ["gap"] = typ["bad"] - typ["good"]
    typ_out = typ["gap"].unstack("typicality").reset_index()
    typ_out.columns.name = None
    print("=== Bad-good intentionality gap by TYPICALITY ===")
    print(typ_out.to_string(index=False))
    save(typ_out, "10_typicality_gap.csv")

    evoc = sub.groupby(["family", "evocativeness", "sign"])["ev_rating"].mean().unstack("sign")
    evoc["gap"] = evoc["bad"] - evoc["good"]
    evoc_out = evoc["gap"].unstack("evocativeness").reset_index()
    evoc_out.columns.name = None
    print("\n=== Bad-good intentionality gap by EVOCATIVENESS (explored, not quoted in the final doc) ===")
    print(evoc_out.to_string(index=False))
    save(evoc_out, "10_evocativeness_gap.csv")


if __name__ == "__main__":
    main()
