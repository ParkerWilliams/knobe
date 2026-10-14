"""Sign effect per arm, and the arm contrast, for the nonmoral and foundations
experiments -- the pilots' own questions, which analysis/first_look.py pools
over.

Per model x question (intentionality, blame, praise) x arm:
    rating ~ sign_c                      term sign_c
and per model x question, the experiment's primary contrast:
    nonmoral:    rating ~ sign_c * arm_c   arm_c = moral +0.5 / prudential+procedural -0.5
    foundations: rating ~ sign_c * arm_c   arm_c = harm +0.5 / loyalty+authority+fairness+purity -0.5
    term sign_c:arm_c (positive = larger bad-vs-good gap in the moral / harm arm)
the same codings the August pilots used (analyze_sign_wcb.py).

Reuses, does not reimplement: kmp.frame.load_frame / analysis_rows, and
first_look.fit / seed_for (lib.wild_cluster_bootstrap, B=1999, clustered by
storyline, MIN_CLUSTERS guard). Seeds are first_look's rule with the arm or
contrast name added as a part. p_wcb is unadjusted (exploratory).

--registry lets the OpenRouter runs (tools/openrouter_models.yaml) through
load_frame; default is the repo registry.

From the study folder:
    ../../.venv/bin/python analysis/arm_effects.py --experiment nonmoral \\
        --items stimuli/pilot/pilot_nonmoral.csv --registry tools/openrouter_models.yaml \\
        --results outputs/elicit/or_pilot_nonmoral_*.jsonl \\
        --out outputs/first_look/or_pilot_nonmoral_arm_effects.csv
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

STUDY_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STUDY_DIR))
sys.path.insert(0, str(STUDY_DIR / "analysis"))

from knobe.registry import load_registry  # noqa: E402

from first_look import fit, seed_for  # noqa: E402
from kmp.frame import analysis_rows, load_frame  # noqa: E402
from kmp.items import load_items  # noqa: E402

QUESTIONS = ["intentionality", "blame", "praise"]
FOCAL_ARM = {"nonmoral": "moral", "foundations": "harm"}


def arm_effects(d: pd.DataFrame, experiment: str) -> pd.DataFrame:
    focal = FOCAL_ARM[experiment]
    rows = []
    for (mk, q), cell in d[d["qkey"].isin(QUESTIONS)].groupby(["model_key", "qkey"]):
        for arm, s in cell.groupby("arm"):
            means = s.groupby("sign")["rating"].mean()
            rows.append(dict(model_key=mk, qkey=q, arm=arm, term="sign_c", n_rows=len(s),
                             n_storylines=s["cluster_id"].nunique(),
                             mean_bad=means.get("bad"), mean_good=means.get("good"),
                             **fit(s, "rating ~ sign_c", "sign_c", seed_for(mk, q, arm, "sign_c"))))
        c = cell.assign(arm_c=(cell["arm"] == focal).map({True: 0.5, False: -0.5}))
        rows.append(dict(model_key=mk, qkey=q, arm=f"{focal}_vs_rest", term="sign_c:arm_c", n_rows=len(c),
                         n_storylines=c["cluster_id"].nunique(),
                         **fit(c, "rating ~ sign_c * arm_c", "sign_c:arm_c",
                               seed_for(mk, q, f"{focal}_vs_rest", "sign_c:arm_c"))))
    return pd.DataFrame(rows)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--experiment", required=True, choices=sorted(FOCAL_ARM))
    p.add_argument("--results", required=True, type=Path, nargs="+")
    p.add_argument("--items", required=True, type=Path)
    p.add_argument("--registry", type=Path)
    p.add_argument("--reparse", action="store_true", help="re-read raw_response with kmp.answer (runner 0.1 rows)")
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args(argv)
    items = load_items(a.items)
    registry = load_registry(a.registry) if a.registry else None
    frame = pd.concat([load_frame(r, items, registry, reparse=a.reparse) for r in a.results], ignore_index=True)
    out = arm_effects(analysis_rows(frame), a.experiment)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(a.out, index=False)
    cols = ["model_key", "qkey", "arm", "term", "n_rows", "n_storylines", "mean_bad", "mean_good", "beta_obs", "p_wcb"]
    with pd.option_context("display.width", 200, "display.float_format", "{:.3f}".format):
        print(out[[c for c in cols if c in out.columns]].to_string(index=False))
    print(f"\nwrote {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
