"""Numeric-answer rate by sign: is answer loss lopsided between bad and good items?

Per set x model x question (intentionality, blame, praise): the share of
replies with a rating (parse_ok) on bad items and on good items, and
bad minus good. A large gap means the rated rows are a sign-dependent
subset, so the sign effect on them may carry selection bias.

Descriptive only (no fits, no seeds). Reuses kmp.frame.load_frame for the
item join and, with --reparse, kmp.answer for re-reading runner-0.1 rows.
Replaces the inline pandas behind outputs/first_look/or_parse_rate_by_sign.csv
(2026-10-13); same columns.

From the study folder (one --set per vignette set: name, items, results):
    ../../.venv/bin/python analysis/parse_rate_by_sign.py --registry tools/openrouter_models.yaml \\
        --set ngo_verbatim stimuli/ngo_verbatim.csv outputs/elicit/or_v2_ngo_verbatim_<mk>.jsonl ... \\
        --set pilot_nonmoral stimuli/pilot/pilot_nonmoral.csv outputs/elicit/or_v2_pilot_nonmoral_<mk>.jsonl ... \\
        --out outputs/first_look/or_v2_parse_rate_by_sign.csv
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

STUDY_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STUDY_DIR))

from knobe.registry import load_registry  # noqa: E402

from kmp.frame import load_frame  # noqa: E402
from kmp.items import load_items  # noqa: E402

QUESTIONS = ["intentionality", "blame", "praise"]


def rates(frame: pd.DataFrame, run: str) -> pd.DataFrame:
    d = frame[frame["qkey"].isin(QUESTIONS)]
    t = d.groupby(["model_key", "qkey", "sign"])["parse_ok"].mean().unstack("sign").reset_index()
    t.columns.name = None
    return t.assign(run=run, bad_minus_good=t["bad"] - t["good"])[
        ["run", "model_key", "qkey", "bad", "good", "bad_minus_good"]]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--set", dest="sets", action="append", nargs="+", required=True,
                   metavar="NAME ITEMS RESULTS", help="set name, items CSV, then its results files")
    p.add_argument("--registry", type=Path)
    p.add_argument("--reparse", action="store_true", help="re-read raw_response with kmp.answer (runner 0.1 rows)")
    p.add_argument("--reader", choices=("regex", "jev", "jev_ev"), default="regex",
                   help="whose reading of each reply: kmp.answer (regex, the reader of record) or Jev's "
                        "sidecar (kmp/jev.py; tools/jev_read.py)")
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args(argv)
    registry = load_registry(a.registry) if a.registry else None
    parts = []
    for name, items_path, *results in a.sets:
        if not results:
            p.error(f"--set {name}: no results files")
        items = load_items(Path(items_path))
        frame = pd.concat([load_frame(r, items, registry, reparse=a.reparse, reader=a.reader) for r in results], ignore_index=True)
        parts.append(rates(frame, name))
    out = pd.concat(parts, ignore_index=True)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(a.out, index=False)
    with pd.option_context("display.width", 200, "display.float_format", "{:.3f}".format):
        print(out.to_string(index=False))
    print(f"\nwrote {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
