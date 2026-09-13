"""Gameplan section 5 item 2b: turn both pilots' arm-vs-arm NULLS into
equivalence statements, so "no significant interaction" carries evidential
weight instead of just failing to reject.

After the parsed-rating substitution (`6c73ab6`, `70f1a34`), the gameplan's
Rank 2 ("the asymmetry isn't harm-specific") and Rank 3 ("...and isn't
moral-specific either") both rest on nulls: no family shows a significant
moral-vs-nonmoral or harm-vs-non-harm interaction. A null at G=34-40 clusters
is weak evidence for absence on its own, which is exactly the trap
`RQ1_STATISTICAL_METHODS_v1.1.md` section 9.3 flagged for the severity
dose-response test -- its CIs were wide enough to contain an effect as large
as typicality's, making the null uninformative rather than disconfirming.
This script checks whether these nulls are in that same position.

Two quantities per cell, both standard and both reported rather than one
picked:

- **MDE (Bloom 2006)**, `se * (t_{1-alpha/2,df} + t_{power,df})`: the
  smallest interaction this design had 80% power to detect. Reused via
  importlib from `15_rq1a_severity_mde_and_power_planning.py` -- imported,
  not recopied, so alpha/power/dof_adjustment stay tied to
  `rq1_v1_1_robustness/config.yaml` and can't drift. (importlib rather than a
  plain import only because the module name starts with a digit.)
- **Equivalence bound**, `|beta| + t_{1-alpha,df} * se`: the TOST-style
  upper limit: interactions larger than this in magnitude are rejected at
  alpha=.05 one-sided. This is the number that licenses "we can rule out an
  interaction bigger than X."

Neither means anything without a yardstick, so each null is scored against a
**benchmark**: the magnitude of the same cell's own pooled `sign_c` main
effect. The scientifically relevant question is not "is the interaction
exactly zero" but "is the domain difference small relative to the asymmetry
itself." A cell whose equivalence bound sits below its benchmark supports
domain-generality; one whose bound exceeds it is simply underpowered, and
must be reported that way.

Both quantities use the cluster-robust `se_obs` the wild cluster bootstrap
already returns, and the same `n_groups` it clustered on. The WCB p-value
remains the estimator of record for the significance question -- these are a
complement to it, not a replacement.

Scope: single-df interaction terms only. The MF pilot's joint 4-df
foundation-gradient F has no single beta/se, so an equivalence bound isn't
defined for it and it is deliberately absent rather than faked.

Run from the knobe repo root (needs both pilots' --score parsed tables):
    .venv/bin/python analysis/ngo_extensions/equivalence_bounds.py

Writes one committed summary table:
    analysis/ngo_extensions/equivalence_bounds.csv
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
RQ1 = HERE.parent / "rq1_v1_1_robustness"
sys.path.insert(0, str(RQ1))

_spec = importlib.util.spec_from_file_location(
    "mde_script", RQ1 / "15_rq1a_severity_mde_and_power_planning.py")
_mde_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mde_mod)
mde, ALPHA, DOF_ADJ = _mde_mod.mde, _mde_mod.ALPHA, _mde_mod.DOF_ADJ

from scipy import stats  # noqa: E402

# (label, table, interaction arm, benchmark arm) -- benchmark is the same
# cell's own pooled sign_c main effect, the yardstick the interaction is
# being called small relative to.
CASES = [
    ("Rank 3: moral vs nonmoral (intentionality)",
     "nonmoral_pilot/outputs/sign_wcb_parsed.csv",
     "moral_vs_nonmoral_pooled", "nonmoral_pooled"),
    ("Rank 1 context: moral vs nonmoral (blame)",
     "nonmoral_pilot/outputs/sign_wcb_blame_parsed.csv",
     "moral_vs_nonmoral_pooled", "nonmoral_pooled"),
    ("Rank 1 context: moral vs nonmoral (praise)",
     "nonmoral_pilot/outputs/sign_wcb_praise_parsed.csv",
     "moral_vs_nonmoral_pooled", "nonmoral_pooled"),
    ("Rank 2: harm vs non-harm (intentionality)",
     "moral_foundations_pilot/outputs/sign_wcb_parsed.csv",
     "harm_vs_nonharm_pooled", "nonharm_pooled"),
]


def equivalence_bound(beta: float, se: float, n_groups: int) -> float:
    """Largest |effect| rejected at ALPHA one-sided -- the TOST bound."""
    df = max(n_groups - DOF_ADJ, 1)
    return abs(beta) + stats.t.ppf(1 - ALPHA, df) * se


def main() -> None:
    rows = []
    for label, rel, inter_arm, bench_arm in CASES:
        t = pd.read_csv(HERE / rel)
        for _, r in t[(t.arm == inter_arm) & (t.tuning == "finetuned")].iterrows():
            bench = t[(t.arm == bench_arm) & (t.family == r.family)
                      & (t.tuning == "finetuned")].iloc[0]
            g = int(r.n_groups)
            m, eq = mde(r.se_obs, g), equivalence_bound(r.beta_obs, r.se_obs, g)
            rows.append(dict(
                claim=label, family=r.family, n_groups=g,
                beta_obs=round(r.beta_obs, 4), se_obs=round(r.se_obs, 4),
                p_wcb=round(r.p_wcb, 4),
                mde_80=round(m, 4), equivalence_bound=round(eq, 4),
                benchmark_arm=bench_arm, benchmark=round(abs(bench.beta_obs), 4),
                # The equivalence verdict only means something for a NULL cell.
                # Where the interaction is itself significant there is nothing to
                # declare equivalent, so the verdict is left blank rather than
                # reported as a spurious "informative null".
                is_null=bool(r.p_wcb >= 0.05),
                bound_below_benchmark=(bool(eq < abs(bench.beta_obs))
                                       if r.p_wcb >= 0.05 else ""),
            ))

    out = pd.DataFrame(rows)
    print(out.to_string(index=False))
    print("\nReading: bound_below_benchmark=True means this design can rule out a")
    print("domain interaction as large as the asymmetry it is interacting with --")
    print("the null is informative. False means underpowered, report it as such.")
    for claim, g in out.groupby("claim", sort=False):
        nulls = g[g.is_null]
        if nulls.empty:
            print(f"  {claim}: no null cells -- interaction significant in all "
                  f"{len(g)}, equivalence not applicable")
        else:
            n_inf = int(sum(b is True for b in nulls.bound_below_benchmark))
            print(f"  {claim}: {n_inf}/{len(nulls)} null cells informative "
                  f"({len(g) - len(nulls)} significant, not applicable)")

    path = HERE / "equivalence_bounds.csv"
    out.to_csv(path, index=False)
    print(f"\nwrote {path}")


if __name__ == "__main__":
    main()
