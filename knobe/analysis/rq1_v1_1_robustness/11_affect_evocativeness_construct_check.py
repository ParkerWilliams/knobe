"""Construct-validity check for the evocativeness manipulation: does the
subject models' own self-reported affect_salience actually differ between
the high- and low-evocative renderings of the same underlying fact?

Source of docs/RQ1_MECHANISM_ANALYSIS_v1.1.md section 4's first table
("affect, high-evocative" vs "affect, low-evocative"). Pooled across both
tuning states (six model_keys) per family, matching the original
exploratory run. Answer: no family shows a positive gap; if anything it
runs backwards -- consistent with the vividness-gap construct-mismatch
finding already documented in data/curation/FLAGGED_VARIABLES_README.md,
now extended from the external reviewer judge to the subject models
themselves.
"""
from __future__ import annotations

import warnings

from lib import load_frame, save

warnings.filterwarnings("ignore")


def main() -> None:
    d = load_frame()

    agg = (
        d[d["question"].isin(["intentionality", "affect_salience"])]
        .groupby(["model_key", "family", "tuning_status", "variant_id", "question"])["ev_rating"]
        .mean()
        .unstack("question")
        .reset_index()
    )
    agg = agg.merge(
        d[["variant_id", "sign", "typicality", "evocativeness", "valence"]].drop_duplicates("variant_id"),
        on="variant_id",
    )

    g = agg.groupby(["family", "evocativeness"])["affect_salience"].mean().unstack()
    g["gap_high_minus_low"] = g["high"] - g["low"]
    g = g.reset_index()
    print("=== Self-reported affect_salience by evocativeness label (pooled across tuning states) ===")
    print(g.to_string(index=False))
    save(g, "11_affect_evocativeness_construct_check.csv")


if __name__ == "__main__":
    main()
