"""Verifies both pilots' selected-item sets against the actual curation
checkpoints, closing SUBMISSION_GAMEPLAN.md section 5 item 2 / section 7.

Until 2026-09-25 the selected sets (196/240 nonmoral, 126/152 MF) were
reconstructed by inference -- the distinct `variant_id`s present in the
published `results_dist/` archives, the method
`measurement_selection_audit.py` documents -- because the curation
checkpoints (`*_relevance_raw.jsonl`) and `selection_report.md` files were
local to whoever ran curation. They are now committed. This script checks
three sets per pilot against each other:

  A  actual  -- the local `*_selected.csv` elicitation actually consumed
                (gitignored; skipped with a note if absent)
  B  mer     -- distinct variant_ids in the published results_dist archive
  C  rerun   -- the pilot's own curation `select_items()` re-run on the
                committed raw checkpoint, outputs redirected to a tempdir

C is the check anyone can reproduce from the public repo alone. B == C
means the reconstruction used throughout the 2026-08-22 and 2026-09-13
analyses is exactly the set the selection rule produces from the actual
reviewer scores.

Machinery is REUSED, not reimplemented: each pilot's curation module is
imported and its own `select_items()` / `_load_curated_and_thresholds()`
run unchanged, with only SELECTED_PATH/REPORT_PATH redirected. No
bootstrap, no seeding -- deterministic.

Also reports two things the reconstruction could not see: items excluded
because the reviewer's answer failed to parse (not because of their score),
and the moral_relevance scores of the nonmoral pilot's kept vs. dropped
moral-good items (CLAIMS.md claim 9, reading (c)).

Run from the knobe repo root:
    .venv/bin/python analysis/ngo_extensions/verify_curation_provenance.py
"""
from __future__ import annotations

import gzip
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]

PILOTS = [
    dict(name="nonmoral_pilot", module="curate_moral_relevance.py",
         base="ngo_prudential_dataset.csv", selected="ngo_prudential_dataset_selected.csv",
         dist="results_pilot_nonmoral_all.jsonl.gz"),
    dict(name="moral_foundations_pilot", module="curate_foundation_relevance.py",
         base="mf_pilot_dataset.csv", selected="mf_pilot_dataset_selected.csv",
         dist="results_pilot_moral_foundations_all.jsonl.gz"),
]


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _dist_variant_ids(path: Path) -> set[str]:
    ids = set()
    with gzip.open(path, "rt") as fh:
        for line in fh:
            ids.add(json.loads(line)["prompt_id"].split("::")[0])
    return ids


def _compare(label: str, left: set[str], right: set[str]) -> bool:
    same = left == right
    detail = "" if same else f"  only-left={sorted(left - right)} only-right={sorted(right - left)}"
    print(f"  {label}: {'IDENTICAL' if same else 'DIFFER'}{detail}")
    return same


def main() -> int:
    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        for p in PILOTS:
            outputs = HERE / p["name"] / "outputs"
            print(f"\n===== {p['name']} =====")
            base = pd.read_csv(outputs / p["base"])

            curate = _load_module(HERE / p["name"] / p["module"], f"{p['name']}_curate")
            curate.SELECTED_PATH = Path(tmp) / f"{p['name']}_selected.csv"
            curate.REPORT_PATH = Path(tmp) / f"{p['name']}_selection_report.md"
            curate.select_items()
            rerun = pd.read_csv(curate.SELECTED_PATH)
            C = set(rerun["variant_id"])

            B = _dist_variant_ids(REPO / "results_dist" / p["dist"])
            print(f"authored={len(base)}  B(published results)={len(B)}  C(rerun from raw)={len(C)}")
            ok &= _compare("B vs C (reconstruction vs. selection rule on actual scores)", B, C)

            actual_path = outputs / p["selected"]
            if actual_path.exists():
                actual = pd.read_csv(actual_path)
                ok &= _compare("A vs C (local selected CSV vs. rerun)", set(actual["variant_id"]), C)
                a = actual.sort_values("variant_id").reset_index(drop=True)
                c = rerun.sort_values("variant_id").reset_index(drop=True)
                same = list(a.columns) == list(c.columns) and a.equals(c)
                ok &= same
                print(f"  A == C on every column and cell: {same}")
            else:
                print(f"  A skipped: {actual_path.name} not present (gitignored, local to curation)")

            raw = pd.read_json(curate.OUT_PATH, lines=True)
            unparsed = raw[~raw["parse_ok"]]
            print(f"  raw checkpoint: {len(raw)} rows, {raw['variant_id'].nunique()} variant_ids, "
                  f"{len(unparsed)} unparsed")
            for vid in unparsed["variant_id"].unique():
                row = base[base["variant_id"] == vid].iloc[0]
                arm = row["category"] if "category" in base.columns else row["condition"]
                qk = unparsed.loc[unparsed["variant_id"] == vid, "question_key"].tolist() \
                    if "question_key" in unparsed.columns else ["moral_relevance"]
                print(f"    {vid:20s} ({arm}, pair {row['pair_id']}) unparsed={qk} selected={vid in C}")

            if p["name"] == "nonmoral_pilot":
                mg = raw[raw["variant_id"].str.match(r"moral-\d+-good")].copy()
                mg["kept"] = mg["variant_id"].isin(C)
                print("  moral-good moral_relevance by fate (moral_min=6):")
                for kept, g in mg.groupby("kept"):
                    scores = sorted(g.loc[g["parse_ok"], "moral_relevance"].astype(int))
                    print(f"    kept={kept}: n={len(g)}, scored={len(scores)}, scores={scores}")

    print("\nALL CHECKS PASS" if ok else "\nSOME CHECKS FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
