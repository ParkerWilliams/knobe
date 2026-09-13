"""Is C3's good-outcome effect about moral domain, or just about stakes?

C3 (CLAIMS.md) is that the moral-vs-nonmoral difference lives almost entirely
in the good-outcome cell: an agent who produces a GOOD outcome while
professing indifference is blamed ~7/10 when the domain is moral and ~2-4/10
when it isn't. The obvious rival reading is that this tracks how much was at
stake rather than whether the domain was moral -- being indifferent about
babies is being indifferent about something that matters, being indifferent
about a report's font is not.

The main run met a version of this as a severity confound, but that was an
authoring accident specific to its own taxonomy (MB items written around
"genuine harm", NMB items written to be low-stakes, nothing enforcing
parity -- RQ1_MECHANISM_ANALYSIS_v1.1.md section 1). The pilots don't inherit
it, because they don't inherit that taxonomy. What they do have is a rival
INTERPRETATION, and unlike the main run they already contain the comparison
that discriminates it.

The nonmoral arm is split by design into:
  - `nonmoral_prudential` -- consequences that matter to the agent
    ("...did not care at all about the effect on her own job security")
  - `nonmoral_procedural`  -- consequences that are trivial
    ("...formatted his quarterly report in an unconventional font")

Both are nonmoral; they differ in stakes. So within the good-outcome cell:

  * a STAKES account predicts a monotone gradient, procedural < prudential <
    moral, with moral continuing the same trend
  * a MORAL-DOMAIN account predicts prudential ~= procedural, and a jump to
    moral that the prudential-procedural step does not anticipate

This fits `{resp} ~ stakes_c` within good-sign nonmoral items (prudential
+0.5 / procedural -0.5, matching the project's effect-coding convention) and
wild-cluster-bootstraps it, then reports that step next to the moral jump it
would have to explain.

Machinery REUSED: `load_frame` from the pilot and `wild_cluster_bootstrap`
from `rq1_v1_1_robustness/lib.py`, so frames, coding and bootstrap match
every other fit here. parsed scoring only, per CLAIMS.md's convention;
finetuned only, since C3 is a finetuned claim.

Run from the knobe repo root:
    .venv/bin/python analysis/ngo_extensions/stakes_gradient_check.py

Writes one committed summary table:
    analysis/ngo_extensions/stakes_gradient_check.csv
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "rq1_v1_1_robustness"))
sys.path.insert(0, str(HERE / "nonmoral_pilot"))
from analyze_sign_wcb import load_frame  # noqa: E402
from lib import wild_cluster_bootstrap  # noqa: E402

warnings.filterwarnings("ignore")

SEED = 27  # next unused in this directory's sequence
STAKES_C = {"nonmoral_prudential": 0.5, "nonmoral_procedural": -0.5}
FAMILIES = ["gemma", "llama", "mistral"]


def main() -> None:
    d = load_frame()
    d = d[d["parse_ok"] & d["parsed_rating"].notna()
          & (d["tuning_status"] == "finetuned") & (d["sign"] == "good")]

    rows = []
    for question in ["q_blame", "q_praise"]:
        q = d[d["question"] == question]
        for fam in FAMILIES:
            cell = q[q["family"] == fam]
            nonmoral = cell[cell["category"].isin(STAKES_C)].copy()
            nonmoral["stakes_c"] = nonmoral["category"].map(STAKES_C)
            wcb = wild_cluster_bootstrap(
                nonmoral, "parsed_rating ~ stakes_c", "stakes_c", "pair_id", seed=SEED)

            mean = lambda c: cell[cell["category"] == c]["parsed_rating"].mean()
            moral, prud, proc = mean("moral"), mean("nonmoral_prudential"), mean("nonmoral_procedural")
            stakes_step = wcb["beta_obs"]
            moral_jump = moral - prud
            rows.append(dict(
                question=question, family=fam,
                procedural=round(proc, 3), prudential=round(prud, 3), moral=round(moral, 3),
                stakes_step=round(stakes_step, 3), stakes_p_wcb=wcb["p_wcb"],
                moral_jump_over_prudential=round(moral_jump, 3),
                # How many prudential-vs-procedural steps would it take to walk
                # from prudential up to moral? A stakes account has to make that
                # number plausible as a stakes distance; a large value means the
                # moral jump is not on the same gradient.
                jump_in_stakes_steps=(round(moral_jump / stakes_step, 1)
                                      if abs(stakes_step) > 1e-9 else float("inf")),
                n=len(cell), n_groups=wcb["n_groups"]))

    out = pd.DataFrame(rows)
    print(out.to_string(index=False))
    print("\nstakes_step = prudential - procedural among GOOD-outcome nonmoral items.")
    print("A stakes account of C3 needs this step to be large and to extrapolate")
    print("to the moral jump. A moral-domain account needs it small or absent.")
    path = HERE / "stakes_gradient_check.csv"
    out.to_csv(path, index=False)
    print(f"\nwrote {path}")


if __name__ == "__main__":
    main()
