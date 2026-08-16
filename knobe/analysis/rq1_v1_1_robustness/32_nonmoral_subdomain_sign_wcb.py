"""Does the nonmoral sign_c null (05_valence_split_wcb.py) hide a real effect
within a more homogeneous nonmoral subdomain? The pooled nonmoral arm has
~4.3x the between-family variance of the moral arm (checked directly:
between-family var 1.139 vs 0.266 for gemma), because "nonmoral" spans
disparate content (aesthetic/procedural/prudential per
`vignettes.csv::nonmoral_subdomain`) while "moral" is a narrow harm-based
construct. This re-tests `sign_c` within each nonmoral subdomain that has
enough family_id clusters to bootstrap: aesthetic (24 families) and
procedural (16 families). Prudential (2 families) is excluded -- far too
few clusters for any cluster-robust inference, flagged rather than
reported.
"""
from __future__ import annotations

import warnings

import pandas as pd
import statsmodels.formula.api as smf

from lib import load_frame, wild_cluster_bootstrap, save

warnings.filterwarnings("ignore")

REPO_ROOT_VIGN = "../../data/release/v1.1/vignettes.csv"
FAMS = ["gemma", "llama", "mistral"]
SUBDOMAINS = ["aesthetic", "procedural"]  # prudential (G=2) excluded, too few clusters


def main() -> None:
    d = load_frame()
    vign = pd.read_csv(REPO_ROOT_VIGN)[["family_id", "nonmoral_subdomain"]].drop_duplicates()
    d = d.merge(vign, on="family_id", how="left")

    sub = d[(d["question"] == "intentionality") & (d["tuning_status"] == "finetuned")
            & (d["vt"] == "nonmoral")].dropna(subset=["sign_c"])

    rows = []
    for subdomain in SUBDOMAINS:
        for fam in FAMS:
            s = sub[(sub["family"] == fam) & (sub["nonmoral_subdomain"] == subdomain)]
            n_groups = s["family_id"].nunique()
            m = smf.mixedlm("ev_rating ~ sign_c", s, groups=s["family_id"]).fit(reml=False, method="lbfgs")
            wcb = wild_cluster_bootstrap(s, "ev_rating ~ sign_c", "sign_c", "family_id", seed=21)
            rows.append(dict(subdomain=subdomain, family=fam, term="sign_c", n=len(s),
                              lmm_estimate=m.params["sign_c"], lmm_p=m.pvalues["sign_c"], **wcb))

    out = pd.DataFrame(rows)
    print(out.to_string(index=False))
    save(out, "32_nonmoral_subdomain_sign_wcb.csv")

    excluded_n = sub[sub["nonmoral_subdomain"] == "prudential"]["family_id"].nunique()
    print(f"\nExcluded: prudential (G={excluded_n} families -- too few clusters for WCB)")


if __name__ == "__main__":
    main()
