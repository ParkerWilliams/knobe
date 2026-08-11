"""The manipulation check RQ1a's item set should have gotten at norming
time and didn't: are moral and nonmoral items actually matched on severity,
within the same storyline (set_id)?

The curation severity-match check (check_pairs, curate.py) only ever
compares WITHIN a family across the low/high-evocativeness swap -- it was
never checked ACROSS valence categories. This pulls the within-storyline
(same set_id) MB-vs-NMB and MG-vs-NMG pairs directly, which is the correct
matched-pair comparison (same underlying goal/actions, only the valence
category differs).

This is the decisive finding behind docs/RQ1_MECHANISM_ANALYSIS_v1.1.md
section 1 and docs/SEVERITY_PILOT_PLAN.md's scoping to nonmoral-BAD content
specifically: bad pairs are catastrophically unmatched (every single one of
21 storylines), good pairs are reasonably close. No amount of statistical
modeling of the existing data can substitute for this -- it's a stimulus-
design fact, checkable directly without any regression.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    cur = pd.read_csv(REPO_ROOT / "data" / "curation" / "curated_v1.1.csv")
    cur["set_id"] = cur["family_id"].str.replace(r"-(MB|MG|NMB|NMG|NEU)-", "-", regex=True)
    fam_sev = cur.groupby(["set_id", "valence"])["severity"].mean().unstack()

    bad_pairs = fam_sev[["MB", "NMB"]].dropna().copy()
    bad_pairs["diff"] = bad_pairs["MB"] - bad_pairs["NMB"]
    good_pairs = fam_sev[["MG", "NMG"]].dropna().copy()
    good_pairs["diff"] = good_pairs["MG"] - good_pairs["NMG"]

    print("=== Bad pairs: MB vs. NMB, matched by storyline ===")
    print(bad_pairs.round(2).to_string())
    print(f"\nmean diff={bad_pairs['diff'].mean():.2f}  min={bad_pairs['diff'].min():.2f}  "
          f"max={bad_pairs['diff'].max():.2f}  matched (within 1.0): "
          f"{(bad_pairs['diff'].abs() <= 1.0).sum()}/{len(bad_pairs)}")

    print("\n=== Good pairs: MG vs. NMG, matched by storyline ===")
    print(good_pairs.round(2).to_string())
    print(f"\nmean diff={good_pairs['diff'].mean():.2f}  min={good_pairs['diff'].min():.2f}  "
          f"max={good_pairs['diff'].max():.2f}  matched (within 1.0): "
          f"{(good_pairs['diff'].abs() <= 1.0).sum()}/{len(good_pairs)}")

    bad_pairs.to_csv(Path(__file__).parent / "outputs" / "20_severity_matched_pairs_bad.csv")
    good_pairs.to_csv(Path(__file__).parent / "outputs" / "20_severity_matched_pairs_good.csv")
    print("\nwrote outputs/20_severity_matched_pairs_bad.csv, outputs/20_severity_matched_pairs_good.csv")


if __name__ == "__main__":
    main()
