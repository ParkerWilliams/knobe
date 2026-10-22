"""First look (go/no-go): is there a sign effect on Ngo's 80 verbatim items?
See docs/FIRST_LOOK.md for why this runs before the extension items are
authored, and for the go/no-go rule fixed before the data.

Fits, per model x question (intentionality, blame, praise, significance):
  rating ~ sign_c                       term sign_c   (bad +0.5, good -0.5)
and per family x question (intentionality, blame, praise):
  rating ~ sign_c * tuning_c            term sign_c:tuning_c   (RQ3)
Positive sign_c = higher rating for the bad side effect (for praise the
expected direction is negative).

Reuses, does not reimplement: kmp.frame.load_frame / analysis_rows (recodes
reversed anchors, parse_ok rows only) and lib.wild_cluster_bootstrap from
analysis/rq1_v1_1_robustness/lib.py (CGM bootstrap-t, Rademacher, B=1999),
the same function the Ngo pilot scripts use. Clustered by storyline
(cluster_id, one cluster per Ngo pair). p_wcb is unadjusted; this is a
screening look, not the confirmatory analysis (DESIGN.md section 10).

Seeding: per fit, int(sha256(f"{BASE_SEED}|{cell}|{qkey}|{term}")[:8], 16),
so a fit's draws don't depend on which other fits run or their order.

--results takes one or more with-examples results files (the cluster runs
Gemma as its own job); each is loaded through load_frame, then concatenated.

Run from the repo root:
    .venv/bin/python studies/knobe_moral_probe/analysis/first_look.py \\
        --results studies/knobe_moral_probe/outputs/elicit/ngo_verbatim_gemma.jsonl \\
                  studies/knobe_moral_probe/outputs/elicit/ngo_verbatim_llama_mistral.jsonl \\
        --items studies/knobe_moral_probe/stimuli/ngo_verbatim.csv \\
        --out studies/knobe_moral_probe/outputs/first_look/sign_effects.csv
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import warnings
from pathlib import Path

import pandas as pd

STUDY_DIR = Path(__file__).resolve().parents[1]
REPO = STUDY_DIR.parents[1]
sys.path.insert(0, str(STUDY_DIR))
sys.path.insert(0, str(REPO / "analysis" / "rq1_v1_1_robustness"))
from kmp.frame import REFUSAL_BOUNDS, analysis_rows, load_frame, with_refusal_bound  # noqa: E402
from kmp.items import load_items  # noqa: E402
from lib import wild_cluster_bootstrap  # noqa: E402

warnings.filterwarnings("ignore")

BASE_SEED = "knobe_moral_probe-first_look"
B = 1999
SIGN_QUESTIONS = ["intentionality", "blame", "praise", "significance"]
TUNING_QUESTIONS = ["intentionality", "blame", "praise"]
MIN_CLUSTERS = 5   # Rademacher draws are granular to 1/2^G below this


def seed_for(*parts: str) -> int:
    return int(hashlib.sha256("|".join([BASE_SEED, *parts]).encode()).hexdigest()[:8], 16)


def fit(s: pd.DataFrame, formula: str, term: str, seed: int) -> dict:
    n_clusters = s["cluster_id"].nunique()
    if n_clusters < MIN_CLUSTERS or s["sign_c"].nunique() < 2:
        return dict(n_clusters=n_clusters, untestable=True)
    r = wild_cluster_bootstrap(s, formula, term, "cluster_id", B=B, seed=seed)
    return dict(untestable=False, **r)


def sign_effects(frame: pd.DataFrame) -> pd.DataFrame:
    d = analysis_rows(frame)
    rows = []
    for (mk, q), cell in d[d["qkey"].isin(SIGN_QUESTIONS)].groupby(["model_key", "qkey"]):
        n_all = int(((frame["model_key"] == mk) & (frame["qkey"] == q)).sum())
        means = cell.groupby("sign")["rating"].mean()
        rows.append(dict(level="model", cell=mk, family=cell["family"].iloc[0],
                         tuning_status=cell["tuning_status"].iloc[0], qkey=q, term="sign_c",
                         n_rows=len(cell), number_rate=len(cell) / n_all,
                         mean_bad=means.get("bad"), mean_good=means.get("good"),
                         **fit(cell, "rating ~ sign_c", "sign_c", seed_for(mk, q, "sign_c"))))
    for (fam, q), cell in d[d["qkey"].isin(TUNING_QUESTIONS)].groupby(["family", "qkey"]):
        if cell["tuning_c"].nunique() < 2:
            continue
        rows.append(dict(level="family", cell=fam, family=fam, tuning_status="both", qkey=q,
                         term="sign_c:tuning_c", n_rows=len(cell),
                         **fit(cell, "rating ~ sign_c * tuning_c", "sign_c:tuning_c",
                               seed_for(fam, q, "sign_c:tuning_c"))))
    return pd.DataFrame(rows)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--results", required=True, type=Path, nargs="+", help="with-examples results (kmp.elicit)")
    p.add_argument("--items", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--refusals", choices=REFUSAL_BOUNDS, default="drop",
                   help="drop: refusals stay missing (primary); min / max: refusals filled to the smallest / "
                        "largest bad - good gap they allow (DESIGN.md amendment 2026-10-22, option C)")
    a = p.parse_args(argv)
    items = load_items(a.items)
    frames = [with_refusal_bound(load_frame(r, items), a.refusals) for r in a.results]
    seen = [set(f["model_key"]) for f in frames]
    if len(seen) > 1 and sum(map(len, seen)) != len(set().union(*seen)):
        raise ValueError("a model appears in more than one results file; pass each model's results once")
    frame = pd.concat(frames, ignore_index=True)
    if (frame.groupby("family")["model_family"].nunique() > 1).any():
        raise ValueError("a short family name covers several registry families across the results files")
    out = sign_effects(frame).assign(refusals=a.refusals)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(a.out, index=False)
    with pd.option_context("display.width", 200, "display.max_columns", 20):
        print(out.drop(columns=["family", "B"], errors="ignore").round(3).to_string(index=False))
    print(f"\nwrote {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
