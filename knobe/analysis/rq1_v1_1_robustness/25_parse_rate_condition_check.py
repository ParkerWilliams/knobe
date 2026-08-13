"""Outstanding-review item 12: does parse failure correlate with condition?

Per model_key, logistic regression of parse_ok on typicality/sign/valence-
type (+domain as a control), on the intentionality question rows (the
question every RQ1a-d contrast actually uses). If parse failure is
systematically higher for e.g. atypical or NEU items, that's a selection
bias sitting under exactly the contrasts (RQ1c/RQ1d typicality) that are
this release's strongest surviving findings.

Special attention: llama-3.1-8b-pretrained has the lowest overall parse
rate (24.4%) and anchors several tuning contrasts.
"""
from __future__ import annotations

import warnings

import pandas as pd
import statsmodels.formula.api as smf

from lib import load_frame, REPO_ROOT, CONFIG, save

warnings.filterwarnings("ignore")


def main() -> None:
    d = load_frame()
    vign = pd.read_csv(REPO_ROOT / CONFIG["data"]["vignettes_csv"])
    d = d.merge(vign[["variant_id", "domain"]], on="variant_id", how="left")

    intent = d[d["question"] == "intentionality"].dropna(subset=["sign_c", "typ_c", "vt_c"]).copy()

    rows = []
    overall = intent.groupby("model_key")["parse_ok"].mean().rename("parse_rate")
    for mk, sub in intent.groupby("model_key"):
        rate = overall[mk]
        n = len(sub)
        row = dict(model_key=mk, n=n, parse_rate=rate)
        try:
            m = smf.logit(
                "parse_ok ~ typ_c + sign_c + vt_c + C(domain)", sub.assign(parse_ok=sub["parse_ok"].astype(int)),
            ).fit(disp=False)
            for term in ["typ_c", "sign_c", "vt_c"]:
                row[f"{term}_coef"] = float(m.params.get(term, float("nan")))
                row[f"{term}_p"] = float(m.pvalues.get(term, float("nan")))
            row["converged"] = bool(m.mle_retvals.get("converged", True))
        except Exception as e:  # perfect separation / singular design on some low-rate checkpoints
            row["fit_error"] = str(e)
        rows.append(row)

    out = pd.DataFrame(rows).sort_values("parse_rate")
    print(out.to_string(index=False))
    save(out, "25_parse_rate_condition_check.csv")

    print("\n--- raw parse rate by typicality, sign, valence-type (all rows, no model fit) ---")
    for factor in ["typicality", "sign", "vt"]:
        print(f"\nby {factor}:")
        print(intent.groupby(["model_key", factor])["parse_ok"].mean().unstack().to_string())


if __name__ == "__main__":
    main()
