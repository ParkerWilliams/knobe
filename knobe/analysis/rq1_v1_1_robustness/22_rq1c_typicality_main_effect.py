"""Does typicality have a reliable MAIN effect on intentionality, independent
of sign -- not just the typ_c:sign_c interaction everything so far has
tested?

Motivated by 21_rq1c_typicality_reversal_cellmeans.py: the raw cell means
show choosing an uncommon *method* raises intentionality ratings overall in
all three families (not just for bad items), and does so unevenly enough
between bad/good in gemma and mistral to produce their significant
typ_c:sign_c interaction -- while llama's typicality effect is the LARGEST
of the three in absolute terms but lands almost symmetrically on both signs,
which is why its interaction is null (p=.403) despite typicality clearly
doing *something* in that family.

This fits the same model rq1c_typicality_x_sign already uses
(`ev_rating ~ typ_c * sign_c`, family_id clustering, G=84) and WCB-tests the
typ_c MAIN EFFECT term specifically, alongside the already-known
typ_c:sign_c interaction term, so both numbers are visible side by side.
"""
from __future__ import annotations

import warnings

import pandas as pd

from lib import load_frame, wild_cluster_bootstrap, save

warnings.filterwarnings("ignore")

FAMS = ["gemma", "llama", "mistral"]
SEED = 13  # fresh seed, not reused by any other script (see config.yaml)


def main() -> None:
    d = load_frame()
    sub = d[(d["question"] == "intentionality") & (d["tuning_status"] == "finetuned")
            & d["sign"].isin(["bad", "good"])].dropna(subset=["sign_c", "typ_c"])

    rows = []
    for fam in FAMS:
        s = sub[sub["family"] == fam]
        for term in ["typ_c", "typ_c:sign_c"]:
            wcb = wild_cluster_bootstrap(s, "ev_rating ~ typ_c * sign_c", term, "family_id", seed=SEED)
            rows.append(dict(family=fam, term=term, **wcb))

    out = pd.DataFrame(rows)
    print(out.to_string(index=False))
    save(out, "22_rq1c_typicality_main_effect.csv")


if __name__ == "__main__":
    main()
