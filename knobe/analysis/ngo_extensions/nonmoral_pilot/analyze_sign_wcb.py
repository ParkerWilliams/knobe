"""Primary analysis for the Ngo nonmoral-extension pilot: does the sign
effect (bad > good foreseen-side-effect rating, the classic Knobe asymmetry)
appear within the selected nonmoral items, compared against the moral sign
effect on the same storyline templates?

Fits, per subject family (gemma/llama/mistral) x tuning status
(pretrained/finetuned), for one question type at a time (`--question`,
default q_intentionality; q_blame and q_praise were collected in the same
real run and use identical machinery -- same formula, same clustering, same
seed -- just a different `question` filter and output path):

- `ev_rating ~ sign_c` split-sample within each arm -- moral (the
  benchmark), pooled nonmoral (primary), and prudential / procedural
  separately (secondary, same honesty standard as
  `analysis/rq1_v1_1_robustness/32_nonmoral_subdomain_sign_wcb.py`) --
  mirroring `05_valence_split_wcb.py`'s split-sample design.
- `ev_rating ~ sign_c * arm_c` on moral + pooled nonmoral, term
  `sign_c:arm_c` -- the direct moral-vs-nonmoral difference test.

Inference machinery is REUSED, not reimplemented: wild cluster bootstrap
and the spec-section-4.4 logit-EV score are imported from
`analysis/rq1_v1_1_robustness/lib.py` (same B=1999 CGM bootstrap-t used
throughout the v1.1 robustness re-analysis). Clustering is on `pair_id`
(the Ngo storyline -- the analogue of family_id here; nonmoral variants
share their storyline's pair_id with the moral original, so the
interaction fit's clusters span arms, which is the conservative choice).
Companion mixedlm fit per cell for comparability with the v1.1 tables.

Seeding: one fixed seed (23) consumed per-call across all contrasts, same
convention as the rq1_v1_1_robustness scripts (config.yaml `seeds` note) --
shared across question types, since each question's WCB draws operate on a
disjoint row subset and don't interact.

`--score` selects the response variable. `ev` (default) is the
spec-section-4.4 logit-fallback EV score every committed table here uses.
`parsed` substitutes the model's own numeric answer on parse_ok rows only --
the check `35_rq1_base_sign_pretrained_parsed_rating_wcb.py` used to overturn
the main run's pretrained "reversal", generalized from that one cell to every
cell here. `measurement_selection_audit.py` (commit 395a9ed) is why it's run
across finetuned cells too and not just pretrained ones: on this pilot the
ev/parsed agreement is question-shaped, strong for q_blame/q_praise
(r=.56-.82) and weak for finetuned q_intentionality (gemma .180, llama .146).
The two scores are on different scales -- EV is a logprob-weighted mean over
0-10, parsed is the raw integer -- so compare significance patterns across
`--score` runs, not coefficient magnitudes, exactly as item 11 did.

Run from the knobe repo root:
    .venv/bin/python analysis/ngo_extensions/nonmoral_pilot/analyze_sign_wcb.py
    .venv/bin/python analysis/ngo_extensions/nonmoral_pilot/analyze_sign_wcb.py --question q_blame
    .venv/bin/python analysis/ngo_extensions/nonmoral_pilot/analyze_sign_wcb.py --question q_praise
    .venv/bin/python analysis/ngo_extensions/nonmoral_pilot/analyze_sign_wcb.py --score parsed

Reads outputs/elicit_results.jsonl + outputs/ngo_prudential_dataset_selected.csv
(both local-only); writes outputs/sign_wcb.csv for q_intentionality (small
summary table, committed) or outputs/sign_wcb_{question}.csv for
q_blame/q_praise, suffix without the `q_` prefix, plus a `_parsed` suffix
under --score parsed.
"""
from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import pandas as pd
import statsmodels.formula.api as smf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "rq1_v1_1_robustness"))
from lib import _logit_ev_rating, wild_cluster_bootstrap  # noqa: E402

warnings.filterwarnings("ignore")

SEED = 23
# Untestable-cell guards, only ever triggered under --score parsed (the full
# frame is balanced by construction). G=5 generalizes the G=2 prudential
# exclusion in 32_nonmoral_subdomain_sign_wcb.py: Rademacher weights admit
# only 2^G distinct bootstrap draws, so p_wcb is granular to 1/2^G at small G.
MIN_ROWS = 30
MIN_CLUSTERS = 5
SIGN_C = {"bad": 0.5, "good": -0.5}   # config.yaml effect_coding, frozen
ARM_C = {"moral": 0.5, "nonmoral": -0.5}
ARMS = [
    ("moral", lambda d: d["category"] == "moral"),
    ("nonmoral_pooled", lambda d: d["category"] != "moral"),
    ("nonmoral_prudential", lambda d: d["category"] == "nonmoral_prudential"),
    ("nonmoral_procedural", lambda d: d["category"] == "nonmoral_procedural"),
]
MODEL_KEYS = [
    "gemma-2-9b-pretrained", "gemma-2-9b-instruct",
    "llama-3.1-8b-pretrained", "llama-3.1-8b-instruct",
    "mistral-7b-v0.1-pretrained", "mistral-7b-v0.1-instruct",
]


def load_frame() -> pd.DataFrame:
    df = pd.read_json(HERE / "outputs" / "elicit_results.jsonl", lines=True)
    sel = pd.read_csv(HERE / "outputs" / "ngo_prudential_dataset_selected.csv")
    df["variant_id"] = df["prompt_id"].str.split("::").str[0]
    df["question"] = df["prompt_id"].str.split("::").str[1]
    df["ev_rating"] = df["logprobs_0_10"].apply(_logit_ev_rating)
    d = df.merge(sel[["variant_id", "pair_id", "category", "sign"]], on="variant_id")
    assert len(d) == len(df), "elicit rows dropped in join -- selected CSV out of sync"
    d["sign_c"] = d["sign"].map(SIGN_C)
    d["family"] = d["model_key"].str.split("-").str[0]
    d["tuning_status"] = d["model_key"].str.contains("instruct").map(
        {True: "finetuned", False: "pretrained"})
    return d


def fit_or_skip(s: pd.DataFrame, resp: str, formula: str, term: str, **meta) -> dict:
    """One cell's mixedlm + WCB, or a counts-only row when the cell can't
    support the test. Under `--score parsed` the parse_ok filter drops rows
    unevenly across arms, so a cell that was fine on the full frame can lose
    a sign level or most of its clusters -- record that as an untestable cell
    rather than crashing or, worse, reporting a WCB over 2^G weight vectors."""
    n_groups = s["pair_id"].nunique()
    if len(s) < MIN_ROWS or n_groups < MIN_CLUSTERS or s["sign_c"].nunique() < 2:
        return dict(**meta, term=term, n=len(s), n_groups=n_groups, untestable=True)
    m = smf.mixedlm(formula, s, groups=s["pair_id"]).fit(reml=False, method="lbfgs")
    wcb = wild_cluster_bootstrap(s, formula, term, "pair_id", seed=SEED)
    return dict(**meta, term=term, n=len(s), lmm_estimate=m.params[term],
                lmm_p=m.pvalues[term], untestable=False, **wcb)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--question", default="q_intentionality",
                    choices=["q_intentionality", "q_blame", "q_praise"])
    p.add_argument("--score", default="ev", choices=["ev", "parsed"],
                    help="ev (default) = the spec section-4.4 logit-fallback EV score "
                         "the committed tables use. parsed = the model's own numeric "
                         "answer, parse_ok rows only -- the substitution "
                         "35_rq1_base_sign_pretrained_parsed_rating_wcb.py used to "
                         "overturn the main run's pretrained reversal.")
    args = p.parse_args()

    resp = "ev_rating" if args.score == "ev" else "parsed_rating"
    d = load_frame()
    sub = d[d["question"] == args.question]
    if args.score == "parsed":
        sub = sub[sub["parse_ok"] & sub["parsed_rating"].notna()]

    rows = []
    for mk in MODEL_KEYS:
        cell = sub[sub["model_key"] == mk]
        fam, tuning = cell["family"].iloc[0], cell["tuning_status"].iloc[0]
        for arm, mask in ARMS:
            rows.append(fit_or_skip(cell[mask(cell)], resp, f"{resp} ~ sign_c", "sign_c",
                                    arm=arm, family=fam, tuning=tuning))
        # direct moral-vs-pooled-nonmoral difference test
        s = cell.assign(arm_c=(cell["category"] == "moral").map({True: 0.5, False: -0.5}))
        rows.append(fit_or_skip(s, resp, f"{resp} ~ sign_c * arm_c", "sign_c:arm_c",
                                arm="moral_vs_nonmoral_pooled", family=fam, tuning=tuning))

    out = pd.DataFrame(rows)
    print(out.to_string(index=False))
    q_suffix = "" if args.question == "q_intentionality" else f"_{args.question.removeprefix('q_')}"
    score_suffix = "" if args.score == "ev" else "_parsed"
    out_path = HERE / "outputs" / f"sign_wcb{q_suffix}{score_suffix}.csv"
    out.to_csv(out_path, index=False)
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
