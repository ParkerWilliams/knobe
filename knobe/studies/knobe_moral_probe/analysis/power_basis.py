"""Design-stage power basis for DESIGN.md section 9: storylines per
foundation needed for 80% power to detect each finetuned per-foundation
sign effect seen in the MF pilot (parsed scoring).

Reuses required_sets() and mde() from
analysis/rq1_v1_1_robustness/15_rq1a_severity_mde_and_power_planning.py,
unchanged (se ~ sqrt(G_current / G_new) scaling). Reads the pilot's
committed sign_wcb_parsed.csv; this is the one place the study reads
earlier outputs (README exception). Deterministic, no seeding.

Run from the repo root:
    .venv/bin/python studies/knobe_moral_probe/analysis/power_basis.py
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd

STUDY_DIR = Path(__file__).resolve().parents[1]
REPO = STUDY_DIR.parents[1]
PILOT_TABLE = REPO / "analysis/ngo_extensions/moral_foundations_pilot/outputs/sign_wcb_parsed.csv"
S15 = REPO / "analysis/rq1_v1_1_robustness/15_rq1a_severity_mde_and_power_planning.py"
OUT = STUDY_DIR / "outputs" / "power_basis.csv"
MIN_EFFECT = 0.2          # below this there is no effect to power; reported as None


def _load_s15():
    sys.path.insert(0, str(S15.parent))
    spec = importlib.util.spec_from_file_location("s15_power", S15)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    s15 = _load_s15()
    d = pd.read_csv(PILOT_TABLE)
    d = d[(d["tuning"] == "finetuned") & (d["term"] == "sign_c")].copy()
    d["already_powered"] = [s15.mde(se, int(g)) <= abs(b) for b, se, g in zip(d["beta_obs"], d["se_obs"], d["n_groups"])]
    d["storylines_for_80pct"] = [s15.required_sets(b, se, int(g)) if abs(b) > MIN_EFFECT else None
                                 for b, se, g in zip(d["beta_obs"], d["se_obs"], d["n_groups"])]
    out = d[["family", "arm", "n_groups", "beta_obs", "se_obs", "already_powered", "storylines_for_80pct"]].round(3)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    print(out.to_string(index=False))
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
