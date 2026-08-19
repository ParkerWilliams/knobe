"""Minimum-detectable-effect (MDE) planning check for the moral-foundations
pilot, run AFTER curation's ``--select`` step and BEFORE ``elicit.py`` --
same rationale as the sibling `../nonmoral_pilot/power_check.py`: the thing
worth checking before an elicitation run isn't cost, it's whether the
cluster counts that survive curation make the tests interpretable at all.

Reuses this project's established MDE machinery, cited rather than
silently reimplemented (same provenance note as the sibling script): the
Bloom (2006)-style cluster-design MDE and the ``se ~ sqrt(G_current /
G_new)`` scaling approximation from
`analysis/rq1_v1_1_robustness/09_minimum_detectable_effect.py` and
`15_rq1a_severity_mde_and_power_planning.py`, with alpha=.05, power=.80,
dof_adjustment=2 from `analysis/rq1_v1_1_robustness/config.yaml`.

Arms projected (design doc section 6):
  - harm-control arm, and the pooled non-harm arm (the primary contrast's
    two sides), each benchmarked against `05_valence_split_wcb.csv`'s
    moral-only sign_c fits -- if the Knobe asymmetry generalizes to
    non-harm moral content, that's the variance structure the non-harm arm
    should resemble.
  - the pooled non-harm arm again, benchmarked against
    `32_nonmoral_subdomain_sign_wcb.csv`'s aesthetic/procedural cells --
    the pessimistic analog: if the effect does NOT generalize, the
    non-harm foundations behave like nonmoral content, and those cells
    show what a similarly modest cluster count could still detect.
  - each foundation individually (secondary, exploratory), against the
    moral-only benchmark, reported with its own cluster count and no
    claim of equal power -- purity's smaller G by design (doc section 4).

Usage (after `curate_foundation_relevance.py --select`):
    .venv/bin/python analysis/ngo_extensions/moral_foundations_pilot/power_check.py

Or to test the mechanics before real curation data exists:
    .venv/bin/python analysis/ngo_extensions/moral_foundations_pilot/power_check.py \
        --g-harm 28 --g-loyalty 12 --g-authority 12 --g-fairness 12 --g-purity 6
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
from scipy import stats

HERE = Path(__file__).parent
REPO_ROOT = HERE.resolve().parents[2]
SELECTED_PATH = HERE / "outputs" / "mf_pilot_dataset_selected.csv"
RQ1_OUTPUTS = REPO_ROOT / "analysis" / "rq1_v1_1_robustness" / "outputs"

FOUNDATIONS = ["loyalty", "authority", "fairness", "purity"]

# Verbatim from analysis/rq1_v1_1_robustness/config.yaml's
# minimum_detectable_effect block -- see module docstring.
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
    `15_rq1a_severity_mde_and_power_planning.py::required_sets`."""
    return se_current * (g_current / g_new) ** 0.5


def load_benchmarks() -> tuple[pd.DataFrame, pd.DataFrame]:
    moral = pd.read_csv(RQ1_OUTPUTS / "05_valence_split_wcb.csv")
    moral = moral[moral["valence_type"] == "moral"].assign(source="05_valence_split_wcb (moral-only)")

    nonmoral = pd.read_csv(RQ1_OUTPUTS / "32_nonmoral_subdomain_sign_wcb.csv")
    nonmoral = nonmoral.assign(source="32_nonmoral_subdomain_sign_wcb (" + nonmoral["subdomain"] + ")")

    cols = ["source", "family", "beta_obs", "se_obs", "n_groups"]
    return moral[cols], nonmoral[cols]


def real_cluster_counts() -> dict[str, int]:
    if not SELECTED_PATH.exists():
        print(f"{SELECTED_PATH} doesn't exist yet -- run "
              f"`curate_foundation_relevance.py --select` first, or pass the --g-* overrides "
              f"to test this script's mechanics before real curation data exists.", file=sys.stderr)
        sys.exit(1)
    df = pd.read_csv(SELECTED_PATH)
    counts = {"harm_control": df[df["condition"] == "harm_control"]["pair_id"].nunique(),
              "nonharm_pooled": df[df["condition"] != "harm_control"]["pair_id"].nunique()}
    for f in FOUNDATIONS:
        counts[f] = df[df["condition"] == f]["pair_id"].nunique()
    return counts


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--g-harm", type=int)
    for f in FOUNDATIONS:
        p.add_argument(f"--g-{f}", type=int)
    args = p.parse_args()

    overrides = dict(harm_control=args.g_harm,
                     **{f: getattr(args, f"g_{f}") for f in FOUNDATIONS})
    if all(v is not None for v in overrides.values()):
        counts = dict(overrides)
        counts["nonharm_pooled"] = sum(overrides[f] for f in FOUNDATIONS)
        print("Using overridden cluster counts (not read from "
              f"{SELECTED_PATH.name}; nonharm_pooled = sum of the four = "
              f"{counts['nonharm_pooled']}, an upper bound that ignores storyline overlap "
              "between foundations)\n")
    elif any(v is not None for v in overrides.values()):
        p.error("pass either all of --g-harm/--g-loyalty/--g-authority/--g-fairness/--g-purity, or none")
    else:
        counts = real_cluster_counts()
        print(f"Real post-curation cluster counts from {SELECTED_PATH.name}: "
              + ", ".join(f"G_{k}={v}" for k, v in counts.items()) + "\n")

    moral_bench, nonmoral_bench = load_benchmarks()

    # (arm label, cluster count, benchmark frame, why that benchmark)
    arms = [
        ("harm-control", counts["harm_control"], moral_bench, "primary"),
        ("non-harm pooled (if effect generalizes)", counts["nonharm_pooled"], moral_bench, "primary"),
        ("non-harm pooled (if it behaves nonmorally)", counts["nonharm_pooled"], nonmoral_bench, "primary"),
    ] + [
        (f"{f} alone", counts[f], moral_bench, "secondary/exploratory") for f in FOUNDATIONS
    ]

    rows = []
    for arm, g_new, bench, role in arms:
        for _, r in bench.iterrows():
            if g_new < 3:
                # fewer than 3 clusters is the v1.1 prudential G=2 failure
                # mode -- untestable, not just underpowered
                se_projected = mde_projected = float("nan")
                detectable = False
            else:
                se_projected = project_se(r["se_obs"], int(r["n_groups"]), g_new)
                mde_projected = mde(se_projected, g_new)
                detectable = abs(r["beta_obs"]) >= mde_projected
            rows.append(dict(
                arm=arm, role=role, benchmark_source=r["source"], benchmark_family=r["family"],
                benchmark_beta=r["beta_obs"], benchmark_se=r["se_obs"], benchmark_g=int(r["n_groups"]),
                projected_g=g_new, projected_se=se_projected, projected_mde=mde_projected,
                benchmark_effect_detectable_at_projected_g=detectable,
            ))

    out = pd.DataFrame(rows)
    pd.set_option("display.width", 200)
    print(out.to_string(index=False))

    out_path = HERE / "outputs" / "power_check.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False)
    print(f"\nwrote {out_path}")
    print(
        "\nReading this: for each benchmark cell, 'projected_mde' answers \"if this pilot's "
        "variance structure resembles that cell, what effect size could the REAL post-curation "
        "cluster count detect at 80% power\", compared against that benchmark's own observed "
        "effect. Planning approximation (se ~ sqrt(G_current/G_new)), not a guarantee -- same "
        "caveat as 15_rq1a_severity_mde_and_power_planning.py. Foundations are reported "
        "individually as exploratory only; purity's G is smaller by design. Not a blocking gate "
        "on elicitation."
    )


if __name__ == "__main__":
    main()
