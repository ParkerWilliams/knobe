"""Does instruction tuning change the size of the Knobe asymmetry? The
formal test, which neither pilot ever ran.

ALIGNMENT_DISCUSSION point 1 ("the Knobe effect showed up in gemma, llama and
mistral -- but only once finetuned") is read off six separate split-sample
`sign_c` fits, three pretrained and three finetuned, and a 6/6 eyeball of
which ones cleared .05. That is not a test of the difference: two fits
landing on opposite sides of a significance threshold is not evidence that
they differ from each other. This is the mirror image of the gap
`31_rq1_base_sign_main_effect_wcb.py` closed for the main run, where script
01 had only ever bootstrapped `sign_c:tuning_c` and never the bare `sign_c`
main effect. Here the interaction is the missing half.

Fits `{resp} ~ sign_c * tuning_c` per (pilot, family, arm) and wild cluster
bootstraps the `sign_c:tuning_c` term -- one p-value per cell answering "is
the asymmetry bigger after finetuning," instead of two p-values that have to
be compared by eye.

Coding follows `rq1_v1_1_robustness/config.yaml` exactly: `tuning_c`
finetuned +0.5 / pretrained -0.5, `sign_c` bad +0.5 / good -0.5, so a
POSITIVE `sign_c:tuning_c` means finetuning increases the bad>good
asymmetry -- the same orientation as `configs/contrasts.yaml`'s
`rq1_base` contrast, so the pilot numbers read the same way as the main
run's.

Clustering is on `pair_id`, and clusters therefore span both tuning states
(the same storyline is rated by the pretrained and the finetuned checkpoint
of a family). That is the conservative choice and matches how the existing
arm-vs-arm interaction fits cluster across arms.

Run under both scorings. `--score parsed` is the one to read: pretrained
cells are where the logit-fallback EV artifact is worst
(`measurement_audit.csv`: r=.059-.227), and this contrast has a pretrained
cell in every row by construction.

Machinery is REUSED, not reimplemented: `wild_cluster_bootstrap` and the
per-pilot `load_frame` come from the existing scripts, so the frames, merges,
codings and bootstrap are identical to the fits this complements.

Run from the knobe repo root:
    .venv/bin/python analysis/ngo_extensions/tuning_contrast_wcb.py
    .venv/bin/python analysis/ngo_extensions/tuning_contrast_wcb.py --score parsed

Writes one committed summary table:
    analysis/ngo_extensions/tuning_contrast_wcb{,_parsed}.csv
"""
from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import pandas as pd
import statsmodels.formula.api as smf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "rq1_v1_1_robustness"))
from lib import wild_cluster_bootstrap  # noqa: E402

warnings.filterwarnings("ignore")

SEED = 26  # next unused seed across the two pilots (23, 24, 25 taken)
TUNING_C = {"finetuned": 0.5, "pretrained": -0.5}  # config.yaml, frozen
FAMILIES = ["gemma", "llama", "mistral"]

# (pilot dir, arm column, arms to test). Each pilot's own load_frame supplies
# the frame, so sign_c / family / tuning_status are already coded.
PILOTS = [
    ("nonmoral_pilot", "category",
     [("moral", lambda d: d["category"] == "moral"),
      ("nonmoral_pooled", lambda d: d["category"] != "moral")]),
    ("moral_foundations_pilot", "condition",
     [("harm_control", lambda d: d["condition"] == "harm_control"),
      ("nonharm_pooled", lambda d: d["condition"] != "harm_control")]),
]


def load(pilot: str):
    sys.path.insert(0, str(HERE / pilot))
    mod = __import__("analyze_sign_wcb")
    # Both pilots define a module named analyze_sign_wcb; drop it between
    # pilots so the second import doesn't silently reuse the first pilot's.
    frame = mod.load_frame()
    del sys.modules["analyze_sign_wcb"]
    sys.path.pop(0)
    return frame


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--score", default="ev", choices=["ev", "parsed"])
    args = p.parse_args()
    resp = "ev_rating" if args.score == "ev" else "parsed_rating"
    formula = f"{resp} ~ sign_c * tuning_c"

    rows = []
    for pilot, _, arms in PILOTS:
        d = load(pilot)
        if "question" in d.columns:                 # nonmoral pilot only
            d = d[d["question"] == "q_intentionality"]
        if args.score == "parsed":
            d = d[d["parse_ok"] & d["parsed_rating"].notna()]
        d = d.assign(tuning_c=d["tuning_status"].map(TUNING_C))

        for fam in FAMILIES:
            cell = d[d["family"] == fam]
            for arm, mask in arms:
                s = cell[mask(cell)]
                m = smf.mixedlm(formula, s, groups=s["pair_id"]).fit(
                    reml=False, method="lbfgs")
                wcb = wild_cluster_bootstrap(
                    s, formula, "sign_c:tuning_c", "pair_id", seed=SEED)
                # Report each tuning state's own simple slope alongside the
                # interaction: sign_c at tuning_c=+-0.5 is what point 1's
                # split-sample table shows, so the two are comparable.
                b_sign, b_int = m.params["sign_c"], m.params["sign_c:tuning_c"]
                rows.append(dict(
                    pilot=pilot, family=fam, arm=arm, n=len(s),
                    slope_pretrained=round(b_sign - 0.5 * b_int, 4),
                    slope_finetuned=round(b_sign + 0.5 * b_int, 4),
                    lmm_interaction=round(b_int, 4),
                    lmm_p=m.pvalues["sign_c:tuning_c"], **wcb))

    out = pd.DataFrame(rows)
    print(out.to_string(index=False))
    n_sig = (out.p_wcb < .05).sum()
    print(f"\nsign_c:tuning_c significant in {n_sig}/{len(out)} cells "
          f"(positive = finetuning increases the bad>good asymmetry)")

    suffix = "" if args.score == "ev" else "_parsed"
    path = HERE / f"tuning_contrast_wcb{suffix}.csv"
    out.to_csv(path, index=False)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
