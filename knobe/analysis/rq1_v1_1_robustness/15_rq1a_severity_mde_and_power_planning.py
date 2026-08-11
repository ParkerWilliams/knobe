"""Severity-adjusted RQ1a MDE (using the corrected set-FE SE from
14_rq1a_severity_set_fe_wcb.py, not the biased pooled-OLS SE) plus a
sample-size-planning extension: how many MORE sets (beyond the 21 the v1.1
release has) would be needed to detect the OBSERVED severity-adjusted effect
size at 80% power, if that effect and the per-set variance structure held in
a larger release.

Power-planning approximation, stated explicitly: SE scales as
sqrt(G_current / G_new) (the standard 1/G cluster-variance scaling used for
back-of-envelope power planning), holding the per-set variance components
and the observed effect size fixed. This is NOT a guarantee -- it assumes a
future release's added sets would be drawn from the same population as the
current 21, and that the true effect equals what was observed here (not
its own draw from a larger, more precise study). Read the "sets needed"
number as "how big would a follow-up need to be to have a chance," not as
a promise of what a follow-up would find.
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
    return se * (stats.t.ppf(1 - ALPHA / 2, df) + stats.t.ppf(POWER, df))


def required_sets(effect: float, se_current: float, g_current: int, g_max: int = 5000) -> int | None:
    """Smallest G_new > g_current such that MDE(G_new) <= |effect|, under the
    se ~ sqrt(g_current / g_new) scaling approximation."""
    for g_new in range(g_current + 1, g_max):
        se_new = se_current * (g_current / g_new) ** 0.5
        if mde(se_new, g_new) <= abs(effect):
            return g_new
    return None


def main() -> None:
    baseline = pd.read_csv(OUTPUT_DIR / "03_rq1a_baseline_wcb.csv")
    severity = pd.read_csv(OUTPUT_DIR / "14_rq1a_severity_set_fe_wcb.csv")

    rows = []
    for _, r in baseline.iterrows():
        rows.append(dict(model="baseline", family=r["family"], beta_obs=r["beta_obs"],
                          se_obs=r["se_obs"], n_groups=int(r["n_groups"])))
    for _, r in severity.iterrows():
        rows.append(dict(model="+severity_c (set-FE corrected)", family=r["family"],
                          beta_obs=r["beta_obs"], se_obs=r["se_obs"], n_groups=int(r["n_groups"])))

    out = pd.DataFrame(rows)
    out["mde"] = out.apply(lambda r: mde(r["se_obs"], r["n_groups"]), axis=1)
    out["observed_ge_mde"] = out["beta_obs"].abs() >= out["mde"]
    out["sets_needed_for_80pct_power"] = out.apply(
        lambda r: required_sets(r["beta_obs"], r["se_obs"], r["n_groups"]), axis=1
    )
    out["additional_sets_needed"] = out["sets_needed_for_80pct_power"] - out["n_groups"]

    print(out.to_string(index=False))
    save(out, "15_rq1a_severity_mde_and_power_planning.csv")


if __name__ == "__main__":
    main()
