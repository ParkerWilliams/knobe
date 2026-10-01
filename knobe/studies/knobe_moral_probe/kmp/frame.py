"""Results -> one analysis DataFrame (DESIGN.md section 10).

`rating` is the written number, recoded 10 - x for reversed-anchor
wordings so every rating points the same way; NaN where the model gave no
number. The existing sign-effect fits consume this frame.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from knobe.schemas import ResultRecord, read_jsonl

from kmp import protocol
from kmp.prompts import parse_prompt_id
from kmp.items import Item

SIGN_C = {"bad": 0.5, "good": -0.5}


def load_frame(results_path: str | Path, items: list[Item]) -> pd.DataFrame:
    df = pd.DataFrame([r.model_dump() for r in read_jsonl(results_path, ResultRecord)])
    parts = pd.DataFrame([parse_prompt_id(p) for p in df["prompt_id"]],
                         columns=["item_id", "qkey", "wording_key", "fmt"], index=df.index)
    df = pd.concat([df, parts], axis=1)
    meta = pd.DataFrame([i.model_dump() for i in items])[["item_id", "experiment", "storyline_id", "arm", "sign"]]
    # Rows for items no longer in the items file (removed after a partial run) are dropped.
    known = df["item_id"].isin(meta["item_id"])
    n_dropped = int((~known).sum())
    if n_dropped:
        print(f"frame: dropped {n_dropped} result row(s) for items not in the items file", file=sys.stderr)
    df = df[known]
    d = df.merge(meta, on="item_id", how="left", validate="many_to_one")
    d["reversed"] = [protocol.is_reversed(q, w) for q, w in zip(d["qkey"], d["wording_key"])]
    raw = pd.to_numeric(d["parsed_rating"], errors="coerce").where(d["parse_ok"].astype(bool))
    d["rating"] = np.where(d["reversed"], 10 - raw, raw)
    d["tuning"] = np.where(d["model_key"].str.endswith("-instruct"), "instruct", "pretrained")
    d["family"] = d["model_key"].str.split("-").str[0]
    d["sign_c"] = d["sign"].map(SIGN_C)
    d.attrs["n_dropped_unknown_items"] = n_dropped
    return d
