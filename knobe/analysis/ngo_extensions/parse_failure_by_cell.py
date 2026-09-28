"""Is answer loss (parse failure) lopsided by outcome sign or by arm?

Parsed scoring drops unparsed rows, so every parsed-rating contrast is
estimated on the rows that parsed. If failure rates differ between bad and
good items, or differ in sign between arms, the dropped rows can bias the
sign effect (and the sign x arm interaction) that the claims rest on.

Two outputs:

1. Descriptive (always): failure rate per pilot x model x question x arm x
   sign, and the bad-minus-good gap in percentage points.
2. Inferential (--wcb): a linear probability model on `failed` (0/1) per
   cell, clustered by storyline, using the SAME machinery as the sign
   effect fits -- each pilot's own `load_frame()` and
   `rq1_v1_1_robustness/lib.wild_cluster_bootstrap` (B=1999), unchanged:
     - `failed ~ sign_c` within each arm (is loss lopsided by sign?)
     - `failed ~ sign_c * arm_c` for each pilot's primary contrast
       (moral vs nonmoral pooled; harm vs non-harm pooled), term
       `sign_c:arm_c` (is the lopsidedness different between arms, which
       is what would bias the domain interactions?)
   Seed fixed at SEED below; deterministic given the data.

Cells: finetuned x all three questions (nonmoral) / intentionality (MF),
plus pretrained intentionality in both pilots, since claim 2's tuning
contrast uses pretrained parsed intentionality. Pretrained blame/praise is
excluded (no claim uses it).

3. Selection check (--selection-check): see selection_check()'s docstring.
   Writes parse_failure_selection_check.csv.

Reads each pilot's local outputs/elicit_results.jsonl + selected CSV (via
load_frame). Writes parse_failure_by_cell.csv (descriptive) and, with
--wcb, parse_failure_wcb.csv.

Run from the knobe repo root:
    .venv/bin/python analysis/ngo_extensions/parse_failure_by_cell.py
    .venv/bin/python analysis/ngo_extensions/parse_failure_by_cell.py --wcb [--limit 1]
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
import time
import warnings
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[0] / "rq1_v1_1_robustness"))
from lib import wild_cluster_bootstrap  # noqa: E402

warnings.filterwarnings("ignore")
SEED = 26
SIGN_C = {"bad": 0.5, "good": -0.5}


def _load(pilot: str) -> pd.DataFrame:
    """The pilot's own load_frame, imported under a unique module name."""
    pdir = HERE / pilot
    sys.path.insert(0, str(pdir))
    spec = importlib.util.spec_from_file_location(f"{pilot}_analyze", pdir / "analyze_sign_wcb.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sys.path.remove(str(pdir))
    if pilot == "moral_foundations_pilot":
        d = mod.load_frame(question=None)
        d["arm"] = d["condition"]
        d["primary_arm"] = d["condition"].map(lambda c: "harm" if c == "harm_control" else "nonharm")
    else:
        d = mod.load_frame()
        d["arm"] = d["category"]
        d["primary_arm"] = d["category"].map(lambda c: "moral" if c == "moral" else "nonmoral")
    d["pilot"] = pilot.replace("_pilot", "")
    d["failed"] = (~d["parse_ok"].astype(bool)).astype(float)
    d["sign_c"] = d["sign"].map(SIGN_C)
    tuning_col = "tuning_status" if "tuning_status" in d.columns else "tuning"
    d["tuning"] = d[tuning_col]
    return d[["pilot", "family", "tuning", "question", "arm", "primary_arm", "sign",
              "sign_c", "pair_id", "failed", "ev_rating"]]


def in_scope(d: pd.DataFrame) -> pd.DataFrame:
    keep = (d["tuning"] == "finetuned") | (d["question"] == "q_intentionality")
    return d[keep]


def descriptive(d: pd.DataFrame) -> pd.DataFrame:
    g = (d.groupby(["pilot", "family", "tuning", "question", "arm", "sign"])["failed"]
           .agg(["mean", "size"]).unstack("sign"))
    out = pd.DataFrame({
        "n_bad": g[("size", "bad")], "n_good": g[("size", "good")],
        "fail_bad_pct": (100 * g[("mean", "bad")]).round(1),
        "fail_good_pct": (100 * g[("mean", "good")]).round(1),
    })
    out["gap_bad_minus_good_pp"] = (out["fail_bad_pct"] - out["fail_good_pct"]).round(1)
    return out.reset_index()


def wcb_cells(d: pd.DataFrame):
    for key, s in d.groupby(["pilot", "family", "tuning", "question"]):
        for arm, a in s.groupby("arm"):
            yield (*key, arm, "sign_c"), a, "failed ~ sign_c", "sign_c"
        s = s.assign(arm_c=s["primary_arm"].map(
            {"moral": 0.5, "harm": 0.5, "nonmoral": -0.5, "nonharm": -0.5}))
        yield (*key, "primary: " + "_vs_".join(sorted(s["primary_arm"].unique(), reverse=True)),
               "sign_c:arm_c"), s, "failed ~ sign_c * arm_c", "sign_c:arm_c"


def selection_check(d: pd.DataFrame) -> pd.DataFrame:
    """Does dropping unparsed rows move the sign effect? Holds the SCORE fixed
    (logit-EV, defined for every row) and varies only the ROWS: all rows vs
    parse_ok rows. Any difference is the selection effect of the drop, not
    a scoring effect. Only informative where EV tracks the model's answer
    (blame/praise, r=.56-.82 finetuned; not intentionality, r=.15-.42), so
    the intentionality rows are reported but flagged. Same WCB, B=1999."""
    rows = []
    for (pilot, fam, q), s in d[d["tuning"] == "finetuned"].groupby(["pilot", "family", "question"]):
        specs = [(arm, a, "ev_rating ~ sign_c", "sign_c") for arm, a in s.groupby("arm")]
        s = s.assign(arm_c=s["primary_arm"].map(
            {"moral": 0.5, "harm": 0.5, "nonmoral": -0.5, "nonharm": -0.5}))
        specs.append(("primary interaction", s, "ev_rating ~ sign_c * arm_c", "sign_c:arm_c"))
        for arm, a, formula, term in specs:
            full = wild_cluster_bootstrap(a, formula, term, "pair_id", seed=SEED)
            kept = wild_cluster_bootstrap(a[a["failed"] == 0], formula, term, "pair_id", seed=SEED)
            rows.append(dict(pilot=pilot, family=fam, question=q, arm=arm, term=term,
                             ev_reliable=q != "q_intentionality",
                             beta_all_rows=round(full["beta_obs"], 3), p_all=round(full["p_wcb"], 4),
                             beta_parsed_rows=round(kept["beta_obs"], 3), p_parsed=round(kept["p_wcb"], 4),
                             shift=round(kept["beta_obs"] - full["beta_obs"], 3)))
    return pd.DataFrame(rows)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--wcb", action="store_true")
    p.add_argument("--selection-check", action="store_true")
    p.add_argument("--limit", type=int, default=None, help="run only the first N WCB cells (timing)")
    args = p.parse_args()

    d = in_scope(pd.concat([_load("nonmoral_pilot"), _load("moral_foundations_pilot")],
                           ignore_index=True))
    desc = descriptive(d)
    desc.to_csv(HERE / "parse_failure_by_cell.csv", index=False)
    pd.set_option("display.width", 200)
    print(desc.to_string(index=False))

    if args.selection_check:
        sc = selection_check(d)
        sc.to_csv(HERE / "parse_failure_selection_check.csv", index=False)
        print(sc.to_string(index=False))
    if not args.wcb:
        return
    rows = []
    cells = list(wcb_cells(d))
    if args.limit:
        cells = cells[:args.limit]
    t0 = time.time()
    for (pilot, fam, tun, q, arm, term), s, formula, t in cells:
        if s["failed"].nunique() < 2:
            rows.append(dict(pilot=pilot, family=fam, tuning=tun, question=q, arm=arm, term=term,
                             n=len(s), untestable=True))
            continue
        w = wild_cluster_bootstrap(s, formula, t, "pair_id", seed=SEED)
        rows.append(dict(pilot=pilot, family=fam, tuning=tun, question=q, arm=arm, term=term,
                         n=len(s), untestable=False, **w))
    print(f"\n{len(cells)} WCB cells in {time.time() - t0:.1f}s")
    out = pd.DataFrame(rows)
    if not args.limit:
        out.to_csv(HERE / "parse_failure_wcb.csv", index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
