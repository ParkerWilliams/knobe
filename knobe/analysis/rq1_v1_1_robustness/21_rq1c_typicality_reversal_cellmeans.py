"""Raw cell means (not just the bad-good gap) for the RQ1c typicality x sign
reversal (docs/RQ1_MECHANISM_ANALYSIS_v1.1.md section 3).

10_typicality_evocativeness_gap_tables.py only ever reported the bad-good
GAP by typicality. That table can't distinguish two very different stories:

  (a) a genuine reversal of the asymmetry itself (bad ratings drop / good
      ratings rise specifically for uncommon items), vs.
  (b) a ceiling/floor compression artifact -- uncommon items of BOTH signs
      already sit close to the same (high or low) intentionality rating,
      so the gap between them mechanically shrinks, without the
      underlying "bad reads as more intentional" mechanism actually
      reversing.

This script reports the four cell means (typicality x sign) directly, per
family, finetuned checkpoint only, intentionality question only -- same
subset as script 10, just not collapsed to the gap.
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

    cell = sub.groupby(["family", "typicality", "sign"])["ev_rating"].agg(["mean", "std", "count"])
    cell = cell.reset_index()
    print("=== Cell means: intentionality rating by family x typicality x sign ===")
    print(cell.to_string(index=False))
    save(cell, "21_typicality_reversal_cellmeans.csv")

    wide = sub.groupby(["family", "typicality", "sign"])["ev_rating"].mean().unstack(["typicality", "sign"])
    print("\n=== Same, wide format (rows=family, cols=typicality/sign) ===")
    print(wide.to_string())


if __name__ == "__main__":
    main()
