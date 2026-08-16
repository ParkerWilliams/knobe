"""Minimum detectable effect (MDE) per contrast x family, using the
PROPERLY-SIZED cluster-robust SE from the wild-cluster-bootstrap outputs
(01-03, 07) rather than the primary model's own (understated) Wald SE.

Standard cluster-design MDE formula (Bloom 2006-style): for a given
cluster-robust SE and G clusters,

    MDE = SE * (t_(1-alpha/2, df) + t_(power, df)),   df = G - dof_adjustment

i.e. "how large would the true effect need to be for this design to detect
it 80% of the time at alpha=.05, given the SE and cluster count it actually
has." Reading this alongside the observed effect size tells you whether a
non-significant result is a genuine null or just an underpowered design at
this cluster count -- see docs/rq1_findings/RQ1_STATISTICAL_METHODS_v1.1.md section 13
item on formal power/precision analysis.

Depends on 01_rq1_base_and_rq1c_wcb.py, 02_rq1d_wcb.py,
03_rq1a_baseline_wcb.py, and 07_rq1b_family_fe_wcb.py having been run first
(reads their output CSVs rather than re-fitting).
"""
from __future__ import annotations

import pandas as pd
from scipy import stats

from lib import CONFIG, OUTPUT_DIR, save

ALPHA = CONFIG["minimum_detectable_effect"]["alpha"]
POWER = CONFIG["minimum_detectable_effect"]["power"]
DOF_ADJ = CONFIG["minimum_detectable_effect"]["dof_adjustment"]


def mde(se: float, n_groups: int) -> float:
    df = max(n_groups - DOF_ADJ, 1)
    t_alpha = stats.t.ppf(1 - ALPHA / 2, df)
    t_power = stats.t.ppf(POWER, df)
    return se * (t_alpha + t_power)


def main() -> None:
    sources = {
        "01_rq1_base_and_rq1c_wcb.csv": "contrast",
        "02_rq1d_wcb.csv": "contrast",
        "03_rq1a_baseline_wcb.csv": "contrast",
        "07_rq1b_family_fe_wcb.csv": None,  # no "contrast" column; label manually below
    }
    frames = []
    for fname, _ in sources.items():
        path = OUTPUT_DIR / fname
        if not path.exists():
            raise FileNotFoundError(f"{path} missing -- run {fname.replace('.csv', '.py')} first.")
        df = pd.read_csv(path)
        if "contrast" not in df.columns:
            df = df.assign(contrast="rq1b_" + df["valence_type"])
        frames.append(df[["contrast", "family", "beta_obs", "se_obs", "n_groups"]])

    combined = pd.concat(frames, ignore_index=True)
    combined["mde"] = combined.apply(lambda r: mde(r["se_obs"], int(r["n_groups"])), axis=1)
    combined["observed_effect_ge_mde"] = combined["beta_obs"].abs() >= combined["mde"]

    print(combined.to_string(index=False))
    save(combined, "09_minimum_detectable_effect.csv")


if __name__ == "__main__":
    main()
