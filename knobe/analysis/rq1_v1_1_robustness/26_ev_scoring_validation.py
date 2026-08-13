"""Outstanding-review item 11: validate the uniform logit-fallback EV-scoring
decision. `ev_rating` (lib.py::_logit_ev_rating, mirroring
src/knobe/analysis/ingest.py::logit_ev_rating) is applied to every row
regardless of parse success. For high-parse-rate checkpoints, check whether
it agrees with `parsed_rating` on the rows where parsing actually succeeded,
and whether swapping to parsed_rating on that subset would change any
qualitative WCB conclusion for RQ1_base / RQ1c (the two contrasts already
WCB-tested per family in script 01).
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from lib import load_frame, wild_cluster_bootstrap, save

warnings.filterwarnings("ignore")

FAMS = ["gemma", "llama", "mistral"]


def main() -> None:
    d = load_frame()
    intent = d[d["question"] == "intentionality"].copy()

    parse_rates = intent.groupby("model_key")["parse_ok"].mean().sort_values(ascending=False)
    print("parse rate by checkpoint:\n", parse_rates.to_string(), "\n")

    agree_rows = []
    for mk, sub in intent.groupby("model_key"):
        ok = sub[sub["parse_ok"] & sub["parsed_rating"].notna()]
        if len(ok) < 30:
            continue
        corr = ok["ev_rating"].corr(ok["parsed_rating"])
        mad = float((ok["ev_rating"] - ok["parsed_rating"]).abs().mean())
        agree_rows.append(dict(model_key=mk, parse_rate=parse_rates[mk], n_parsed=len(ok),
                                corr_ev_vs_parsed=corr, mean_abs_diff=mad))
    agree = pd.DataFrame(agree_rows).sort_values("parse_rate", ascending=False)
    print(agree.to_string(index=False))
    save(agree, "26_ev_vs_parsed_agreement.csv")

    # rq1_base (sign x tuning) can't isolate to high-parse-rate checkpoints: it always needs the
    # low-parse-rate pretrained side too. Use RQ1c typ_c:sign_c instead -- it's already
    # finetuned-only (script 01), and the finetuned/instruct checkpoints are the best-parsed of
    # the six (gemma 60.5%, llama 84.5%, mistral 98.2%) -- this is also the release's strongest
    # surviving result, so it's the one most worth stress-testing against the scoring method.
    print("\nre-testing RQ1c typ_c:sign_c (finetuned only) with parse_ok-only rows + parsed_rating "
          "substituted for ev_rating")
    rq1c = d[(d["question"] == "intentionality") & (d["tuning_status"] == "finetuned")
             & (d["vt"].isin(["moral", "nonmoral"]))].dropna(subset=["sign_c", "typ_c", "parsed_rating"]).copy()
    rq1c = rq1c[rq1c["parse_ok"]]
    rq1c["rating_for_test"] = rq1c["parsed_rating"]

    swap_rows = []
    for fam in FAMS:
        s = rq1c[rq1c["family"] == fam]
        n_parsed = len(s)
        wcb_orig = wild_cluster_bootstrap(
            d[(d["question"] == "intentionality") & (d["tuning_status"] == "finetuned")
              & (d["vt"].isin(["moral", "nonmoral"])) & (d["family"] == fam)].dropna(subset=["sign_c", "typ_c"]),
            "ev_rating ~ typ_c * sign_c", "typ_c:sign_c", "family_id", seed=3,
        )
        wcb_swap = wild_cluster_bootstrap(
            s, "rating_for_test ~ typ_c * sign_c", "typ_c:sign_c", "family_id", seed=3,
        )
        swap_rows.append(dict(family=fam, n_parsed_only=n_parsed,
                               p_wcb_ev_rating_all_rows=wcb_orig["p_wcb"], p_wcb_parsed_only=wcb_swap["p_wcb"],
                               beta_ev=wcb_orig["beta_obs"], beta_parsed=wcb_swap["beta_obs"]))
    swap_out = pd.DataFrame(swap_rows)
    swap_out["disagrees"] = (swap_out["p_wcb_ev_rating_all_rows"] < 0.05) != (swap_out["p_wcb_parsed_only"] < 0.05)
    print(swap_out.to_string(index=False))
    save(swap_out, "26_rq1c_parsed_only_wcb.csv")


if __name__ == "__main__":
    main()
