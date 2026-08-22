"""Holm-corrects the two Ngo-extension pilots' existing sign_c WCB p-values,
per this project's own convention for the main run (`models.holm_correct`:
Holm within each (model_family, rq) group, via
`statsmodels.stats.multitest.multipletests`). Not a new analysis -- no
refits, just a correction pass over already-committed `sign_wcb*.csv`
tables, applied because neither pilot's `analyze_sign_wcb.py` currently
applies any multiple-comparisons correction (unlike the main run), and the
two pilots together produce ~130 individually-interpreted p_wcb values.

Reuses `statsmodels.stats.multitest.multipletests` directly rather than
`models.holm_correct` itself: that wrapper operates on
`ContrastResultRecord` (requires `rq`, `direction_expected` fields the
pilots' plain CSV output doesn't have), so re-deriving the group-then-correct
loop here is the appropriate amount of reuse rather than force-fitting the
pilot tables into the main run's schema.

Correction groups (the pilot analogue of "within family, within one
research question"):
- nonmoral pilot: per (question, family, tuning) -- the 4 sign_c arms +
  1 interaction term tested together in one results block.
- moral-foundations pilot: per (family, tuning, status) -- primary
  (harm_control, nonharm_pooled, interaction) and exploratory (loyalty,
  authority, fairness, purity) corrected separately, respecting the
  pilot's own primary/exploratory split rather than pooling them.

Run from the knobe repo root:
    .venv/bin/python analysis/ngo_extensions/holm_correct_pilots.py

Reads each pilot's already-committed outputs/sign_wcb*.csv; writes
outputs/sign_wcb_holm_summary.csv per pilot (small, committed) with a
p_holm column and a `flips` flag for any cell where the p<.05 verdict
changes between p_wcb and p_holm.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from statsmodels.stats.multitest import multipletests

HERE = Path(__file__).resolve().parent
ALPHA = 0.05


def holm_within_groups(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    out = []
    for _key, g in df.groupby(group_cols, sort=False):
        g = g.copy()
        _, p_holm, _, _ = multipletests(g["p_wcb"], alpha=ALPHA, method="holm")
        g["p_holm"] = p_holm
        out.append(g)
    result = pd.concat(out, ignore_index=True)
    result["sig_wcb"] = result["p_wcb"] < ALPHA
    result["sig_holm"] = result["p_holm"] < ALPHA
    result["flips"] = result["sig_wcb"] != result["sig_holm"]
    return result


def process_nonmoral() -> pd.DataFrame:
    base = HERE / "nonmoral_pilot" / "outputs"
    frames = []
    for question, fname in [
        ("q_intentionality", "sign_wcb.csv"),
        ("q_blame", "sign_wcb_blame.csv"),
        ("q_praise", "sign_wcb_praise.csv"),
    ]:
        d = pd.read_csv(base / fname)
        d["question"] = question
        frames.append(d)
    d = pd.concat(frames, ignore_index=True)
    d["pilot"] = "nonmoral"
    return holm_within_groups(d, ["question", "family", "tuning"])


def process_moral_foundations() -> pd.DataFrame:
    base = HERE / "moral_foundations_pilot" / "outputs"
    d = pd.read_csv(base / "sign_wcb.csv")
    d["question"] = "q_intentionality"
    d["pilot"] = "moral_foundations"
    return holm_within_groups(d, ["family", "tuning", "status"])


def main() -> None:
    nonmoral = process_nonmoral()
    mf = process_moral_foundations()
    mf["status"] = mf.get("status", pd.Series(dtype=str))

    cols = ["pilot", "question", "arm", "family", "tuning", "term",
            "p_wcb", "p_holm", "sig_wcb", "sig_holm", "flips", "n_groups"]
    combined = pd.concat([
        nonmoral.assign(status=nonmoral.get("status", "n/a"))[cols[:3] + ["status"] + cols[3:]],
        mf[cols[:3] + ["status"] + cols[3:]],
    ], ignore_index=True)

    flipped = combined[combined["flips"]]
    print(f"total rows: {len(combined)}")
    print(f"flips (p<.05 under raw WCB, not under Holm): {len(flipped)}")
    if len(flipped):
        print(flipped.to_string(index=False))
    print()
    print("still significant under Holm, by pilot x question:")
    print(combined[combined["sig_holm"]].groupby(["pilot", "question"]).size())

    for pilot, sub in combined.groupby("pilot"):
        out_dir = HERE / ("nonmoral_pilot" if pilot == "nonmoral" else "moral_foundations_pilot") / "outputs"
        out_path = out_dir / "sign_wcb_holm_summary.csv"
        sub.drop(columns=["pilot"]).to_csv(out_path, index=False)
        print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
