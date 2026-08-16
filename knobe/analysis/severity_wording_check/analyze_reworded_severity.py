"""Phase 0 analysis, run after run_reworded_severity.py has produced
outputs/severity_reworded_raw.jsonl (needs the reviewer-model API access
this environment doesn't have -- see that script's docstring).

Compares the reworded magnitude-only severity score against the original
curation severity score:
  1. corr(new_score, sign) within moral and nonmoral items, vs. the
     original r=.885 / r=.473 (docs/severity_confound/SEVERITY_MORALIZATION_BACKGROUND.md).
  2. corr(new_score, original_score) -- convergent validity.
  3. Refits the RQ1a severity-adjusted interaction
     (analysis/rq1_v1_1_robustness/14_rq1a_severity_set_fe_wcb.py's spec)
     substituting the new score for severity_c, via the same set-FE wild
     cluster bootstrap (reused from analysis/rq1_v1_1_robustness/lib.py --
     not reimplemented) to see whether the SE shrinks / the interaction
     becomes resolvable at G=21.

See docs/severity_confound/SEVERITY_PILOT_PLAN.md Phase 0 for the three possible outcomes and
what each implies for whether Phase 1 (the vignette-escalation pilot) is
still needed.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "analysis" / "rq1_v1_1_robustness"))
from lib import load_frame, wild_cluster_bootstrap  # noqa: E402

REWORDED_PATH = Path(__file__).parent / "outputs" / "severity_reworded_raw.jsonl"
FAMS = ["gemma", "llama", "mistral"]


def main() -> None:
    if not REWORDED_PATH.exists():
        raise FileNotFoundError(
            f"{REWORDED_PATH} not found -- run run_reworded_severity.py first "
            "(needs ANTHROPIC_API_KEY access this environment doesn't have)."
        )
    reworded = pd.read_json(REWORDED_PATH, lines=True)
    reworded = reworded.rename(columns={"severity_reworded": "severity_reworded_raw"})

    d = load_frame()  # has original severity_c, sign_c, vt_c, set_id, family_id, etc.
    d = d.merge(reworded[["variant_id", "severity_reworded_raw"]], on="variant_id", how="left")

    # family-level mean of the new score, grand-mean centered -- mirrors
    # lib.load_frame()'s treatment of the original severity_c exactly.
    fam_new_sev = d.groupby("family_id")["severity_reworded_raw"].mean()
    d["severity_reworded_c"] = d["family_id"].map(fam_new_sev) - fam_new_sev.mean()

    print("=== Convergent validity: corr(reworded, original severity), by sign-within-valence-type ===")
    cur = pd.read_csv(REPO_ROOT / "data" / "curation" / "curated_v1.1.csv")
    cur["vt"] = cur["valence"].map({"MB": "moral", "MG": "moral", "NMB": "nonmoral", "NMG": "nonmoral"})
    cur["sign_c"] = cur["sign"].map({"bad": 0.5, "good": -0.5})
    merged = cur.merge(reworded[["variant_id", "severity_reworded_raw"]], on="variant_id", how="inner")
    print("overall corr(new, original):", round(merged["severity"].corr(merged["severity_reworded_raw"]), 3))
    for vt in ["moral", "nonmoral"]:
        sub = merged[merged["vt"] == vt].dropna(subset=["severity_reworded_raw", "sign_c"])
        print(f"{vt:8s} corr(new_severity, sign)      = {round(sub['severity_reworded_raw'].corr(sub['sign_c']), 3)}"
              f"   (original was moral=.885 / nonmoral=.473)")

    print()
    print("=== RQ1a severity-adjusted interaction, reworded severity vs. original (set-FE WCB, G=21) ===")
    sub = d[(d["question"] == "intentionality") & (d["tuning_status"] == "finetuned")
            & (d["vt"].isin(["moral", "nonmoral"]))].dropna(
        subset=["sign_c", "vt_c", "severity_c", "severity_reworded_c"]
    )
    for fam in FAMS:
        s = sub[sub["family"] == fam]
        re_new = smf.mixedlm("ev_rating ~ sign_c * vt_c + severity_reworded_c", s, groups=s["set_id"]).fit(reml=False, method="lbfgs")
        wcb_new = wild_cluster_bootstrap(
            s, "ev_rating ~ sign_c * vt_c + severity_reworded_c + C(set_id)", "sign_c:vt_c", "set_id", seed=1,
        )
        print(f"{fam:8s} reworded-severity: sign_c:vt_c={re_new.params['sign_c:vt_c']:+.4f}  "
              f"WCB se={wcb_new['se_obs']:.4f}  p_wcb={wcb_new['p_wcb']:.4f}  "
              f"(compare to original severity_c's se/p in outputs/14_rq1a_severity_set_fe_wcb.csv)")


if __name__ == "__main__":
    main()
