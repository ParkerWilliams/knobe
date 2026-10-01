"""Results -> one analysis DataFrame (DESIGN.md section 10).

`rating` is the written number, recoded 10 - x for reversed-anchor
wordings so every rating points the same way; NaN where the model gave no
number. The existing sign-effect fits consume this frame.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from knobe.schemas import ResultRecord, read_jsonl

from kmp import protocol
from kmp.items import Item

SIGN_C = {"bad": 0.5, "good": -0.5}


def load_frame(results_path: str | Path, items: list[Item]) -> pd.DataFrame:
    df = pd.DataFrame([r.model_dump() for r in read_jsonl(results_path, ResultRecord)])
    df[["item_id", "qkey", "wording_key", "fmt"]] = df["prompt_id"].str.split("::", expand=True)
    meta = pd.DataFrame([i.model_dump() for i in items])[["item_id", "experiment", "storyline_id", "arm", "sign"]]
    unknown = sorted(set(df["item_id"]) - set(meta["item_id"]))
    if unknown:
        raise ValueError(f"{len(unknown)} result item_id(s) not in the items file, e.g. {unknown[:3]}")
    d = df.merge(meta, on="item_id", how="left", validate="many_to_one")
    d["reversed"] = [protocol.is_reversed(q, w) for q, w in zip(d["qkey"], d["wording_key"])]
    raw = pd.to_numeric(d["parsed_rating"], errors="coerce").where(d["parse_ok"].astype(bool))
    d["rating"] = np.where(d["reversed"], 10 - raw, raw)
    d["tuning"] = np.where(d["model_key"].str.endswith("-instruct"), "instruct", "pretrained")
    d["family"] = d["model_key"].str.split("-").str[0]
    d["sign_c"] = d["sign"].map(SIGN_C)
    return d
