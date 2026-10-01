"""Pre-analysis gate (DESIGN.md section 8). Each function takes the
kmp.frame DataFrame and returns a small table; main() writes them and
exits 1 if any model x question x wording cell falls below the
number-rate minimum.

Number rates count parse_ok over every row (an unparsed answer is a miss).
Everything computed from ratings runs on frame.analysis_rows (NaN-free).
Per-model tables are keyed by model_key and carry tuning_status and family.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from kmp import protocol
from kmp.frame import analysis_rows, load_frame
from kmp.items import load_items

MODEL_COLS = ["model_key", "tuning_status", "family"]


def _with_model_cols(table: pd.DataFrame, frame: pd.DataFrame) -> pd.DataFrame:
    """Add tuning_status and family (one value per model_key) after model_key."""
    meta = frame[MODEL_COLS].drop_duplicates()
    if meta["model_key"].duplicated().any():
        raise ValueError("a model_key has more than one tuning_status/family in the frame")
    out = table.merge(meta, on="model_key", how="left", validate="many_to_one")
    rest = [c for c in out.columns if c not in MODEL_COLS]
    return out[MODEL_COLS + rest]


def number_rates(frame: pd.DataFrame, threshold: float = protocol.NUMBER_RATE_MIN) -> pd.DataFrame:
    out = (frame["parse_ok"].astype(bool).groupby([frame["model_key"], frame["qkey"], frame["wording_key"]]).mean()
           .rename("number_rate").reset_index())
    out["passes"] = out["number_rate"] >= threshold
    return _with_model_cols(out, frame)


def _pearson(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) < 3 or a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def anchor_agreement(frame: pd.DataFrame) -> pd.DataFrame:
    """Per model x core question: item means under normal vs reversed anchors (after recoding)."""
    rated = analysis_rows(frame)
    core = rated[rated["qkey"].isin(protocol.CORE)]
    means = (core.groupby(["model_key", "qkey", "item_id", "reversed"])["rating"].mean()
             .unstack("reversed").reindex(columns=[False, True])
             .rename(columns={False: "normal", True: "reversed"}))
    rows = []
    for (model_key, qkey), d in means.dropna().groupby(level=["model_key", "qkey"]):
        normal, rev = d["normal"].to_numpy(), d["reversed"].to_numpy()
        rows.append(dict(model_key=model_key, qkey=qkey, n_items=len(d), r=_pearson(normal, rev),
                         mean_diff=float((rev - normal).mean())))
    out = pd.DataFrame(rows, columns=["model_key", "qkey", "n_items", "r", "mean_diff"])
    return _with_model_cols(out, frame)


def validity(frame: pd.DataFrame) -> pd.DataFrame:
    """Sanity directions any real judgment should show (DESIGN.md section 8, gate 2)."""
    rows = []
    for model_key, d in analysis_rows(frame).groupby("model_key"):
        def mean(qkey, **where):
            sel = d[d["qkey"] == qkey]
            for col, val in where.items():
                sel = sel[sel[col] == val]
            return sel["rating"].mean()
        checks_ = {
            "blame_bad_minus_good": mean("blame", sign="bad") - mean("blame", sign="good"),
            "praise_good_minus_bad": mean("praise", sign="good") - mean("praise", sign="bad"),
            "significance_moral_minus_procedural": mean("significance", arm="moral") - mean("significance", arm="procedural"),
        }
        for name, value in checks_.items():
            rows.append(dict(model_key=model_key, check=name,
                             value=value, passes=bool(value > 0) if pd.notna(value) else None))
    out = pd.DataFrame(rows, columns=["model_key", "check", "value", "passes"])
    return _with_model_cols(out, frame)


def example_copying(frame: pd.DataFrame) -> pd.DataFrame:
    """Share of written answers equal to a worked-example answer (before recoding).

    The written number is recovered from `rating` by undoing the 10 - x recode,
    so this reads analysis_rows' ratings, never parsed_rating_raw."""
    rated = analysis_rows(frame)
    written = rated["rating"].where(~rated["reversed"].astype(bool), 10 - rated["rating"])
    share = (written.isin(sorted(protocol.EXAMPLE_ANSWERS))
             .groupby(rated["model_key"]).mean().rename("share_example_values").reset_index())
    share["flag"] = share["share_example_values"] > protocol.COPY_SHARE_MAX
    return _with_model_cols(share, frame)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="knobe_moral_probe pre-analysis checks")
    p.add_argument("--results", required=True, type=Path)
    p.add_argument("--items", required=True, type=Path)
    p.add_argument("--out-dir", required=True, type=Path)
    args = p.parse_args(argv)

    frame = load_frame(args.results, load_items(args.items))
    args.out_dir.mkdir(parents=True, exist_ok=True)
    tables = {"number_rates": number_rates(frame), "anchor_agreement": anchor_agreement(frame),
              "validity": validity(frame), "example_copying": example_copying(frame)}
    for name, table in tables.items():
        table.to_csv(args.out_dir / f"{name}.csv", index=False)
        print(f"\n== {name}\n{table.to_string(index=False)}")
    failing = tables["number_rates"][~tables["number_rates"]["passes"]]
    if len(failing):
        print(f"\n{len(failing)} cell(s) below the {protocol.NUMBER_RATE_MIN:.0%} number-rate minimum", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
