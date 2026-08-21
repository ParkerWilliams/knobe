"""Primary analysis for the moral-foundations pilot (design doc section 6):
does the sign effect (bad > good foreseen-side-effect intentionality) hold
for non-harm-structured moral violations, or is it harm-specific?

Fits, per subject family (gemma/llama/mistral) x tuning status
(pretrained/finetuned), q_intentionality (the only question elicited):

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

Run from the knobe repo root:
    .venv/bin/python analysis/ngo_extensions/moral_foundations_pilot/analyze_sign_wcb.py

Reads outputs/elicit_results.jsonl + outputs/mf_pilot_dataset_selected.csv
(both local-only); writes outputs/sign_wcb.csv (small summary table,
committed).
"""
from __future__ import annotations

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


def load_frame() -> pd.DataFrame:
    df = pd.read_json(HERE / "outputs" / "elicit_results.jsonl", lines=True)
    sel = pd.read_csv(HERE / "outputs" / "mf_pilot_dataset_selected.csv")
    df["variant_id"] = df["prompt_id"].str.split("::").str[0]
    df["ev_rating"] = df["logprobs_0_10"].apply(_logit_ev_rating)
    d = df.merge(sel[["variant_id", "pair_id", "condition", "sign"]], on="variant_id")
    assert len(d) == len(df), "elicit rows dropped in join -- selected CSV out of sync"
    d["sign_c"] = d["sign"].map(SIGN_C)
    d["family"] = d["model_key"].str.split("-").str[0]
    d["tuning_status"] = d["model_key"].str.contains("instruct").map(
        {True: "finetuned", False: "pretrained"})
    return d


def main() -> None:
    d = load_frame()

    rows = []
    for mk in MODEL_KEYS:
        cell = d[d["model_key"] == mk]
        fam, tuning = cell["family"].iloc[0], cell["tuning_status"].iloc[0]
        for arm, status, mask in ARMS:
            s = cell[mask(cell)]
            m = smf.mixedlm("ev_rating ~ sign_c", s, groups=s["pair_id"]).fit(reml=False, method="lbfgs")
            wcb = wild_cluster_bootstrap(s, "ev_rating ~ sign_c", "sign_c", "pair_id", seed=SEED)
            rows.append(dict(arm=arm, status=status, family=fam, tuning=tuning, term="sign_c",
                             n=len(s), lmm_estimate=m.params["sign_c"],
                             lmm_p=m.pvalues["sign_c"], **wcb))
        # direct harm-vs-pooled-non-harm difference test
        s = cell.assign(arm_c=(cell["condition"] == "harm_control").map({True: 0.5, False: -0.5}))
        wcb = wild_cluster_bootstrap(s, "ev_rating ~ sign_c * arm_c", "sign_c:arm_c", "pair_id", seed=SEED)
        m = smf.mixedlm("ev_rating ~ sign_c * arm_c", s, groups=s["pair_id"]).fit(reml=False, method="lbfgs")
        rows.append(dict(arm="harm_vs_nonharm_pooled", status="primary", family=fam, tuning=tuning,
                         term="sign_c:arm_c", n=len(s), lmm_estimate=m.params["sign_c:arm_c"],
                         lmm_p=m.pvalues["sign_c:arm_c"], **wcb))

    out = pd.DataFrame(rows)
    print(out.to_string(index=False))
    out_path = HERE / "outputs" / "sign_wcb.csv"
    out.to_csv(out_path, index=False)
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
