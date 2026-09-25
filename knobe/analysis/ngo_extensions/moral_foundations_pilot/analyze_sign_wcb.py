"""Primary analysis for the moral-foundations pilot (design doc section 6):
does the sign effect (bad > good foreseen-side-effect intentionality) hold
for non-harm-structured moral violations, or is it harm-specific?

Fits, per subject family (gemma/llama/mistral) x tuning status
(pretrained/finetuned), one question type at a time (`--question`, default
q_intentionality -- the only question until the 2026-09-25 blame/praise
extension):

- PRIMARY: `ev_rating ~ sign_c` split-sample within the harm-control arm
  and within the four non-harm foundations pooled, plus the direct
  difference test `ev_rating ~ sign_c * arm_c` (term `sign_c:arm_c`) on
  both arms together.
- SECONDARY (exploratory): the same sign_c fit within each foundation
  alone, reported with its own honest cluster count and no claim of equal
  power across foundations (purity G=6 is the smallest -- design doc
  section 2's explicit tradeoff).

Inference machinery is REUSED, not reimplemented: wild cluster bootstrap
and the spec-section-4.4 logit-EV score are imported from
`analysis/rq1_v1_1_robustness/lib.py` (same B=1999 CGM bootstrap-t used
throughout the v1.1 robustness re-analysis). Clustering is on `pair_id`
(the storyline scaffold): foundations share scaffolds with each other and
with the harm-controls, so pooled/interaction fits cluster the shared
storyline together across arms -- the conservative choice.
Companion mixedlm fit per cell for comparability with the v1.1 tables.

Seeding: one fixed seed (24) consumed per-call across all contrasts, same
convention as the rq1_v1_1_robustness scripts (config.yaml `seeds` note).

`--score` selects the response variable. `ev` (default) is the
spec-section-4.4 logit-fallback EV score every committed table here uses.
`parsed` substitutes the model's own numeric answer on parse_ok rows only --
the check `35_rq1_base_sign_pretrained_parsed_rating_wcb.py` used to overturn
the main run's pretrained "reversal", generalized from that one cell to every
cell here. `measurement_selection_audit.py` (commit 395a9ed) is why it's run
across finetuned cells too and not just pretrained ones: this pilot's
ev/parsed agreement is r=.523/.130/.530 for gemma/llama/mistral finetuned,
and .059-.094 for all three pretrained. The two scores are on different
scales -- EV is a logprob-weighted mean over 0-10, parsed is the raw integer
-- so compare significance patterns across `--score` runs, not coefficient
magnitudes, exactly as item 11 did.

Run from the knobe repo root:
    .venv/bin/python analysis/ngo_extensions/moral_foundations_pilot/analyze_sign_wcb.py
    .venv/bin/python analysis/ngo_extensions/moral_foundations_pilot/analyze_sign_wcb.py --score parsed
    .venv/bin/python analysis/ngo_extensions/moral_foundations_pilot/analyze_sign_wcb.py --question q_blame --score parsed

Reads outputs/elicit_results.jsonl + outputs/mf_pilot_dataset_selected.csv
(both local-only); writes outputs/sign_wcb.csv (small summary table,
committed), or outputs/sign_wcb_parsed.csv under --score parsed.
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

SEED = 24
# Untestable-cell guards, only ever triggered under --score parsed (the full
# frame is balanced by construction). G=5 generalizes the G=2 prudential
# exclusion in 32_nonmoral_subdomain_sign_wcb.py: Rademacher weights admit
# only 2^G distinct bootstrap draws, so p_wcb is granular to 1/2^G at small G.
MIN_ROWS = 30
MIN_CLUSTERS = 5
SIGN_C = {"bad": 0.5, "good": -0.5}   # config.yaml effect_coding, frozen
FOUNDATIONS = ["loyalty", "authority", "fairness", "purity"]
ARMS = [
    ("harm_control", "primary", lambda d: d["condition"] == "harm_control"),
    ("nonharm_pooled", "primary", lambda d: d["condition"] != "harm_control"),
] + [(f, "exploratory", (lambda f: lambda d: d["condition"] == f)(f)) for f in FOUNDATIONS]
MODEL_KEYS = [
    "gemma-2-9b-pretrained", "gemma-2-9b-instruct",
    "llama-3.1-8b-pretrained", "llama-3.1-8b-instruct",
    "mistral-7b-v0.1-pretrained", "mistral-7b-v0.1-instruct",
]


def load_frame(question: str | None = "q_intentionality") -> pd.DataFrame:
    """Rows for ONE question type by default. Until 2026-09-25 this pilot's
    results held q_intentionality only and this function did no question
    filtering; once the blame/praise extension is merged into the same
    elicit_results.jsonl, an unfiltered frame would silently pool three
    questions (praise with the opposite sign) into every caller --
    foundation_gradient_wcb.py and ../tuning_contrast_wcb.py included. The
    default keeps every existing caller's frame identical. question=None
    returns all questions, with a `question` column to split on."""
    df = pd.read_json(HERE / "outputs" / "elicit_results.jsonl", lines=True)
    sel = pd.read_csv(HERE / "outputs" / "mf_pilot_dataset_selected.csv")
    df["variant_id"] = df["prompt_id"].str.split("::").str[0]
    df["question"] = df["prompt_id"].str.split("::").str[1]
    if question is not None:
        df = df[df["question"] == question].reset_index(drop=True)
    df["ev_rating"] = df["logprobs_0_10"].apply(_logit_ev_rating)
    d = df.merge(sel[["variant_id", "pair_id", "condition", "sign"]], on="variant_id")
    assert len(d) == len(df), "elicit rows dropped in join -- selected CSV out of sync"
    d["sign_c"] = d["sign"].map(SIGN_C)
    d["family"] = d["model_key"].str.split("-").str[0]
    d["tuning_status"] = d["model_key"].str.contains("instruct").map(
        {True: "finetuned", False: "pretrained"})
    return d


def fit_or_skip(s: pd.DataFrame, formula: str, term: str, **meta) -> dict:
    """One cell's mixedlm + WCB, or a counts-only row when the cell can't
    support the test. Under `--score parsed` the parse_ok filter drops rows
    unevenly across arms, so a cell that was fine on the full frame can lose
    a sign level or most of its clusters -- record that as an untestable cell
    rather than crashing or, worse, reporting a WCB over 2^G weight vectors.
    Matters more here than in the sibling pilot: purity is authored at G=7."""
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
    d = load_frame(args.question)
    if args.score == "parsed":
        d = d[d["parse_ok"] & d["parsed_rating"].notna()]

    rows = []
    for mk in MODEL_KEYS:
        cell = d[d["model_key"] == mk]
        fam, tuning = cell["family"].iloc[0], cell["tuning_status"].iloc[0]
        for arm, status, mask in ARMS:
            rows.append(fit_or_skip(cell[mask(cell)], f"{resp} ~ sign_c", "sign_c",
                                    arm=arm, status=status, family=fam, tuning=tuning))
        # direct harm-vs-pooled-non-harm difference test
        s = cell.assign(arm_c=(cell["condition"] == "harm_control").map({True: 0.5, False: -0.5}))
        rows.append(fit_or_skip(s, f"{resp} ~ sign_c * arm_c", "sign_c:arm_c",
                                arm="harm_vs_nonharm_pooled", status="primary",
                                family=fam, tuning=tuning))

    out = pd.DataFrame(rows)
    print(out.to_string(index=False))
    q_suffix = "" if args.question == "q_intentionality" else f"_{args.question.removeprefix('q_')}"
    score_suffix = "" if args.score == "ev" else "_parsed"
    out_path = HERE / "outputs" / f"sign_wcb{q_suffix}{score_suffix}.csv"
    out.to_csv(out_path, index=False)
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
