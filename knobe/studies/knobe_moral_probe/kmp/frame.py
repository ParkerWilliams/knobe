"""Results -> one analysis DataFrame (DESIGN.md section 10).

One row per result record (model x prompt x sample), joined to its item.
The coding matches the existing fits this frame feeds
(analysis/rq1_v1_1_robustness/lib.py and config.yaml, the ngo_extensions
pilot scripts, src/knobe/analysis/ingest.py), so their formulas and
lib.wild_cluster_bootstrap run on it unchanged.

Column contract:
  item_id, qkey, wording_key, fmt   parsed from prompt_id (kmp.prompts)
  experiment, storyline_id, arm, sign   from the items file
  cluster_id        f"{experiment}-{storyline_id:03d}". Use this, not
                    storyline_id, as the cluster for any pooled fit:
                    ngo_verbatim shares nonmoral's storyline numbering by
                    design (so verbatim and adapted pairs can be matched on
                    storyline_id), and cluster_id keeps them separate clusters.
  reversed          protocol.is_reversed(qkey, wording_key)
  rating            the written number, recoded 10 - x for reversed-anchor
                    wordings; NaN where parse_ok is False or no number was
                    recorded. Fit on this.
  parsed_rating_raw the number as written, NOT recoded. Never fit on it.
  parse_ok, raw_response  kept from the result record
  model_family, tuning_status   from the registry via
                    knobe.analysis.ingest.build_model_key_index
                    (tuning_status is "finetuned" / "pretrained")
  family            short family name (model_family up to its first "-":
                    gemma, llama, mistral), the pilot scripts' `family`
  sign_c            bad +0.5, good -0.5 (config.yaml effect_coding)
  tuning_c          finetuned +0.5, pretrained -0.5 (config.yaml effect_coding)

Pass analysis_rows(frame) to a fit: lib.wild_cluster_bootstrap takes its
cluster groups from the unfiltered frame, so NaN ratings must be dropped first.

Pilot-script names -> frame names:
  question (q_intentionality, q_blame, q_praise)  -> qkey (intentionality, blame, praise)
  category (nonmoral pilot) / condition (MF pilot) -> arm
  variant_id                                       -> item_id
  pair_id (pilots) / family_id (main study)        -> cluster_id
  parsed_rating                                    -> rating (recoded); un-recoded: parsed_rating_raw
  family, tuning_status, sign_c, tuning_c          -> same names, same values

Fails loudly: an empty results file, duplicate job_ids, a model_key not in
the registry, or two registry families sharing one short `family` name
raise ValueError. Rows for items no longer in the items file are dropped and
reported (stderr, plus attrs n_dropped_unknown_items / dropped_unknown_item_ids).
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from knobe.analysis.ingest import build_model_key_index
from knobe.elicit_vllm import default_registry_path
from knobe.registry import load_registry
from knobe.schemas import ResultRecord, read_jsonl

from kmp import protocol
from kmp.items import Item
from kmp.prompts import parse_prompt_id

# analysis/rq1_v1_1_robustness/config.yaml effect_coding (frozen there).
SIGN_C = {"bad": 0.5, "good": -0.5}
TUNING_C = {"finetuned": 0.5, "pretrained": -0.5}


def load_frame(results_path: str | Path, items: list[Item], registry: dict | None = None) -> pd.DataFrame:
    """registry: a loaded model registry (default: the repo's configs/models.yaml)."""
    records = list(read_jsonl(results_path, ResultRecord))
    if not records:
        raise ValueError(f"{results_path}: no result records")
    dup_counts = Counter(r.job_id for r in records)
    dups = sorted(j for j, n in dup_counts.items() if n > 1)
    if dups:
        raise ValueError(f"{results_path}: {len(dups)} duplicate job_id(s), e.g. {dups[:5]}")

    df = pd.DataFrame([r.model_dump() for r in records]).rename(columns={"parsed_rating": "parsed_rating_raw"})

    index = build_model_key_index(registry if registry is not None else load_registry(default_registry_path()))
    unknown = sorted(set(df["model_key"]) - set(index))
    if unknown:
        raise ValueError(f"{results_path}: model_key(s) not in the registry: {unknown}")
    df["model_family"] = [index[k][0] for k in df["model_key"]]
    df["tuning_status"] = [index[k][1] for k in df["model_key"]]
    df["family"] = df["model_family"].str.split("-").str[0]
    per_short = df.groupby("family")["model_family"].unique()
    clashes = {f: sorted(m) for f, m in per_short.items() if len(m) > 1}
    if clashes:
        raise ValueError(f"{results_path}: short family name shared by several registry families: {clashes}")

    parts = pd.DataFrame([parse_prompt_id(p) for p in df["prompt_id"]],
                         columns=["item_id", "qkey", "wording_key", "fmt"], index=df.index)
    df = pd.concat([df, parts], axis=1)
    meta = pd.DataFrame([i.model_dump() for i in items])[["item_id", "experiment", "storyline_id", "arm", "sign"]]
    # Rows for items no longer in the items file (removed after a partial run) are dropped.
    known = df["item_id"].isin(meta["item_id"])
    dropped_ids = sorted(set(df.loc[~known, "item_id"]))
    n_dropped = int((~known).sum())
    if n_dropped:
        print(f"frame: dropped {n_dropped} result row(s) for {len(dropped_ids)} item(s) not in the items file: "
              f"{dropped_ids[:5]}", file=sys.stderr)
    df = df[known]
    d = df.merge(meta, on="item_id", how="left", validate="many_to_one")
    d["cluster_id"] = [f"{e}-{s:03d}" for e, s in zip(d["experiment"], d["storyline_id"])]
    d["reversed"] = [protocol.is_reversed(q, w) for q, w in zip(d["qkey"], d["wording_key"])]
    raw = pd.to_numeric(d["parsed_rating_raw"], errors="coerce").astype(float).where(d["parse_ok"].astype(bool))
    d["rating"] = np.where(d["reversed"], 10 - raw, raw)
    d["sign_c"] = d["sign"].map(SIGN_C)
    d["tuning_c"] = d["tuning_status"].map(TUNING_C)
    d.attrs["n_dropped_unknown_items"] = n_dropped
    d.attrs["dropped_unknown_item_ids"] = dropped_ids
    return d


def analysis_rows(frame: pd.DataFrame) -> pd.DataFrame:
    """Only rows with a rating: what lib.wild_cluster_bootstrap and the other fits need."""
    return frame[frame["rating"].notna()].reset_index(drop=True)
