"""Two pre-writeup audits over both Ngo-extension pilots, neither of which
needs a refit -- they check whether the *inputs* to the existing sign_wcb
fits are sound, not whether the fits were computed correctly.

**Audit 1 -- measurement.** Per (model_key, question): parse rate, and the
correlation between `ev_rating` (the spec-section-4.4 logit-fallback EV
score every pilot fit actually uses) and the model's own `parsed_rating`,
on parse_ok rows only. This is the same diagnostic
`analysis/rq1_v1_1_robustness/26_ev_scoring_validation.py` (review item 11)
ran for the v1.1 main run and `35_rq1_base_sign_pretrained_parsed_rating_wcb.py`
used to overturn the pretrained "reversal" -- applied here per *question
type*, which the main run never needed since it only ever framed the
artifact as a pretrained/finetuned split. The pilots collect three question
types on identical items, so the question axis is newly checkable.

**Audit 2 -- selection.** Authored vs. post-curation item counts per
(category/condition x sign) cell, and the survival rate per cell. Both
pilots authored balanced designs; the question is whether curation kept
them balanced. The MF pilot switched to pair-level gating mid-curation
(2026-08-19 log) specifically to avoid deleting its good arm; the nonmoral
pilot kept per-item selection. This quantifies what that difference cost.

The post-curation set is derived the same documented way the 2026-08-22
session reconstructed it -- the distinct `variant_id`s actually present in
`elicit_results.jsonl` -- rather than reading `*_selected.csv`, which is
gitignored and was never part of the collaborator's upload. That makes this
script reproducible from the published `results_dist/` archives plus the
committed base dataset CSVs, with no local-only input.

Machinery is REUSED, not reimplemented: `_logit_ev_rating` is imported from
`analysis/rq1_v1_1_robustness/lib.py`, the same import both pilots'
`analyze_sign_wcb.py` use, so the `ev_rating` audited here is byte-for-byte
the score those fits consume. No bootstrap, no seeding -- both audits are
deterministic descriptive passes over the elicitation dump.

Run from the knobe repo root (needs both pilots' elicit_results.jsonl
unpacked per knobe/README.md "Study results (compressed)"):
    .venv/bin/python analysis/ngo_extensions/measurement_selection_audit.py

Writes, per pilot, two small committed summary tables:
    <pilot>/outputs/measurement_audit.csv
    <pilot>/outputs/selection_attrition.csv
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "rq1_v1_1_robustness"))
from lib import _logit_ev_rating  # noqa: E402

# (pilot dir, base dataset CSV, the column holding the arm/condition label)
PILOTS = [
    ("nonmoral_pilot", "ngo_prudential_dataset.csv", "category"),
    ("moral_foundations_pilot", "mf_pilot_dataset.csv", "condition"),
]


def load_results(path: Path) -> pd.DataFrame:
    """Streams the elicitation dump into the few columns both audits need.

    Deliberately not pd.read_json(lines=True): the nonmoral pilot's dump is
    ~62 MB and carries an 11-float logprob vector per row, which is the only
    field needed for ev_rating and is cheaper to reduce in the loop than to
    materialize as a DataFrame column first.
    """
    rows = []
    with path.open() as fh:
        for line in fh:
            r = json.loads(line)
            variant_id, question = r["prompt_id"].split("::")[:2]
            rows.append(
                {
                    "model_key": r["model_key"],
                    "question": question,
                    "variant_id": variant_id,
                    "parse_ok": bool(r["parse_ok"]),
                    "parsed_rating": r["parsed_rating"],
                    "ev_rating": _logit_ev_rating(r["logprobs_0_10"]),
                }
            )
    return pd.DataFrame(rows)


def measurement_audit(res: pd.DataFrame) -> pd.DataFrame:
    """Parse rate + ev_rating/parsed_rating agreement per (model_key, question)."""
    out = []
    for (model_key, question), g in res.groupby(["model_key", "question"], sort=True):
        ok = g[g["parse_ok"]]
        # Degenerate-variance guard: a cell where every parsed answer is the
        # same number has no correlation to report, and np.corrcoef would
        # return nan with a RuntimeWarning rather than saying so.
        if len(ok) > 2 and ok["parsed_rating"].std() > 0 and ok["ev_rating"].std() > 0:
            r = float(np.corrcoef(ok["ev_rating"], ok["parsed_rating"])[0, 1])
        else:
            r = float("nan")
        out.append(
            {
                "model_key": model_key,
                "question": question,
                "n_rows": len(g),
                "n_parse_ok": len(ok),
                "parse_rate": round(len(ok) / len(g), 4),
                "r_ev_vs_parsed": round(r, 4) if r == r else "",
            }
        )
    return pd.DataFrame(out)


def selection_audit(base: pd.DataFrame, res: pd.DataFrame, arm_col: str) -> pd.DataFrame:
    """Authored vs. surviving item counts per (arm x sign) cell."""
    kept = set(res["variant_id"].unique())
    base = base.copy()
    base["kept"] = base["variant_id"].isin(kept)
    g = base.groupby([arm_col, "sign"], sort=True)
    out = g.agg(n_authored=("kept", "size"), n_selected=("kept", "sum")).reset_index()
    out["survival_rate"] = (out["n_selected"] / out["n_authored"]).round(4)
    return out.rename(columns={arm_col: "arm"})


def main() -> int:
    for pilot, base_csv, arm_col in PILOTS:
        outputs = HERE / pilot / "outputs"
        results_path = outputs / "elicit_results.jsonl"
        if not results_path.exists():
            print(
                f"{results_path} not found -- unpack it first (knobe/README.md "
                f"'Study results (compressed)').",
                file=sys.stderr,
            )
            return 1

        res = load_results(results_path)
        base = pd.read_csv(outputs / base_csv)

        meas = measurement_audit(res)
        sel = selection_audit(base, res, arm_col)
        meas.to_csv(outputs / "measurement_audit.csv", index=False)
        sel.to_csv(outputs / "selection_attrition.csv", index=False)

        print(f"\n===== {pilot} =====")
        print(meas.to_string(index=False))
        print()
        print(sel.to_string(index=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
