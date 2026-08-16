"""Minimum-detectable-effect (MDE) planning check for the nonmoral pilot,
run AFTER curation's ``--select`` step and BEFORE ``elicit.py`` -- the
thing worth checking before committing to an elicitation run isn't cost
(elicitation is cheap regardless of item count), it's whether the number
of storylines that survive curation is even large enough for the
resulting test to be interpretable at all, the same failure mode as
prudential's untestable G=2 in the existing v1.1 release
(`docs/rq1_findings/OUTSTANDING_STATISTICAL_ANALYSIS.md`).

Reuses this project's existing MDE machinery directly, not a new
formula: the Bloom (2006)-style cluster-design MDE
(``MDE = SE * (t_(1-alpha/2, df) + t_(power, df))``) and the
``se ~ sqrt(G_current / G_new)`` scaling approximation are both already
established in `analysis/rq1_v1_1_robustness/09_minimum_detectable_effect.py`
and `15_rq1a_severity_mde_and_power_planning.py` respectively. Not
literally imported from there (those scripts assume `lib.py`'s
directory-relative CONFIG loading and a cwd of their own directory,
making a cross-directory import fragile for what is otherwise a five-line
pure function) -- the formula and its config values (alpha=.05,
power=.80, dof_adjustment=2, from
`analysis/rq1_v1_1_robustness/config.yaml`) are reproduced verbatim
here, cited rather than silently reimplemented.

**Benchmarks are borrowed from this project's own closest analogous
results, read directly from their committed output CSVs (not
hand-copied):**
  - `05_valence_split_wcb.csv` (moral-only sign_c, G=42) -- the closest
    analog to this pilot's harm-control arm: a plain sign_c effect on
    harm-structured content, family-clustered.
  - `32_nonmoral_subdomain_sign_wcb.csv` (aesthetic/procedural sign_c,
    G=24/G=16) -- the closest analog to this pilot's nonmoral arm: a
    plain sign_c effect on nonmoral content at a similarly modest
    cluster count.
These are read as illustrative reference points for "if this pilot's
variance structure resembles that cell, would an effect of that size be
detectable at the REAL cluster count curation actually produced" -- not a
guarantee, exactly the caveat 15's own docstring already states for this
same scaling approximation.

Usage (after `curate_moral_relevance.py --select` has produced
outputs/ngo_prudential_dataset_selected.csv):
    .venv/bin/python analysis/ngo_extensions/nonmoral_pilot/power_check.py

Or to test the mechanics before real curation data exists (this
environment's own situation right now):
    .venv/bin/python analysis/ngo_extensions/nonmoral_pilot/power_check.py \
        --g-moral 20 --g-nonmoral 15
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
from scipy import stats

HERE = Path(__file__).parent
REPO_ROOT = HERE.resolve().parents[2]
SELECTED_PATH = HERE / "outputs" / "ngo_prudential_dataset_selected.csv"
RQ1_OUTPUTS = REPO_ROOT / "analysis" / "rq1_v1_1_robustness" / "outputs"

# Verbatim from analysis/rq1_v1_1_robustness/config.yaml's
# minimum_detectable_effect block -- see module docstring for why this
# is reproduced rather than imported.
ALPHA = 0.05
POWER = 0.80
DOF_ADJUSTMENT = 2


def mde(se: float, n_groups: int) -> float:
    """Bloom (2006)-style cluster-design MDE -- identical formula to
    `09_minimum_detectable_effect.py::mde`."""
    df = max(n_groups - DOF_ADJUSTMENT, 1)
    return se * (stats.t.ppf(1 - ALPHA / 2, df) + stats.t.ppf(POWER, df))


def project_se(se_current: float, g_current: int, g_new: int) -> float:
    """se ~ sqrt(g_current / g_new) -- identical approximation to
    `15_rq1a_severity_mde_and_power_planning.py::required_sets`, applied
    in the opposite direction (given a new G, project the SE) rather than
    solving for the G a target MDE would need."""
    return se_current * (g_current / g_new) ** 0.5


def load_benchmarks() -> pd.DataFrame:
    moral = pd.read_csv(RQ1_OUTPUTS / "05_valence_split_wcb.csv")
    moral = moral[moral["valence_type"] == "moral"].assign(source="05_valence_split_wcb (moral-only)")

    nonmoral = pd.read_csv(RQ1_OUTPUTS / "32_nonmoral_subdomain_sign_wcb.csv")
    nonmoral = nonmoral.assign(source="32_nonmoral_subdomain_sign_wcb (" + nonmoral["subdomain"] + ")")

    cols = ["source", "family", "beta_obs", "se_obs", "n_groups"]
    return pd.concat([moral[cols], nonmoral[cols]], ignore_index=True)


def real_cluster_counts() -> tuple[int, int]:
    if not SELECTED_PATH.exists():
        print(f"{SELECTED_PATH} doesn't exist yet -- run "
              f"`curate_moral_relevance.py --select` first, or pass --g-moral/--g-nonmoral "
              f"to test this script's mechanics before real curation data exists.", file=sys.stderr)
        sys.exit(1)
    df = pd.read_csv(SELECTED_PATH)
    g_moral = df[df["category"] == "moral"]["pair_id"].nunique()
    g_nonmoral = df[df["category"].isin(["nonmoral_prudential", "nonmoral_procedural"])]["pair_id"].nunique()
    return g_moral, g_nonmoral


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--g-moral", type=int, help="override the real post-curation moral-arm cluster count")
    p.add_argument("--g-nonmoral", type=int, help="override the real post-curation nonmoral-arm cluster count")
    args = p.parse_args()

    if args.g_moral is not None and args.g_nonmoral is not None:
        g_moral, g_nonmoral = args.g_moral, args.g_nonmoral
        print(f"Using overridden cluster counts (not read from {SELECTED_PATH.name}): "
              f"G_moral={g_moral}, G_nonmoral={g_nonmoral}\n")
    else:
        g_moral, g_nonmoral = real_cluster_counts()
        print(f"Real post-curation cluster counts from {SELECTED_PATH.name}: "
              f"G_moral={g_moral} distinct pair_ids, G_nonmoral={g_nonmoral} distinct pair_ids\n")

    benchmarks = load_benchmarks()
    rows = []
    for _, r in benchmarks.iterrows():
        is_moral_benchmark = "moral-only" in r["source"]
        g_new = g_moral if is_moral_benchmark else g_nonmoral
        arm = "moral (harm-control)" if is_moral_benchmark else "nonmoral (pooled)"
        se_projected = project_se(r["se_obs"], int(r["n_groups"]), g_new)
        mde_projected = mde(se_projected, g_new)
        rows.append(dict(
            arm=arm, benchmark_source=r["source"], benchmark_family=r["family"],
            benchmark_beta=r["beta_obs"], benchmark_se=r["se_obs"], benchmark_g=int(r["n_groups"]),
            projected_g=g_new, projected_se=se_projected, projected_mde=mde_projected,
            benchmark_effect_detectable_at_projected_g=abs(r["beta_obs"]) >= mde_projected,
        ))

    out = pd.DataFrame(rows)
    pd.set_option("display.width", 160)
    print(out.to_string(index=False))

    out_path = HERE / "outputs" / "power_check.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False)
    print(f"\nwrote {out_path}")
    print(
        "\nReading this: for each existing benchmark cell, 'projected_se'/'projected_mde' answer "
        "\"if this pilot's variance structure resembles that cell, what effect size could the REAL "
        "post-curation cluster count detect at 80% power\" -- compared against that benchmark's own "
        "observed effect. This is a planning approximation (se ~ sqrt(G_current/G_new)), not a "
        "guarantee -- same caveat as 15_rq1a_severity_mde_and_power_planning.py's use of the same "
        "scaling. Not a blocking gate on elicitation; a report for judging whether the survived "
        "cluster count looks sufficient before committing to the run."
    )


if __name__ == "__main__":
    main()
