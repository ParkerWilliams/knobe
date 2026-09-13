"""Omnibus test: does the size of the Knobe sign_c effect vary across the
five foundations (harm_control, loyalty, authority, fairness, purity), per
subject family x tuning status -- one p-value per model cell, instead of
`analyze_sign_wcb.py`'s five separate pairwise/single-foundation tests.

Fits `ev_rating ~ sign_c * C(condition, Treatment(reference="harm_control"))`
and jointly tests the four `sign_c:condition[T.X]` interaction terms against
zero -- the question "does the effect differ across foundations," answered
once, rather than five separate "is the effect present in foundation X"
questions answered separately (which is what the primary/exploratory arms
in `analyze_sign_wcb.py` already give you).

Inference: a wild cluster bootstrap-F, generalizing
`analysis/rq1_v1_1_robustness/lib.py`'s single-term wild_cluster_bootstrap
(Cameron-Gelbach-Miller 2008 restricted-DGP, Rademacher weights,
cluster-robust refit) to a joint multi-parameter restriction via a
cluster-robust Wald F-statistic (Cameron & Miller 2015 sec. VI). NEW code,
not a `lib.py` addition: `wild_cluster_bootstrap` only supports testing one
coefficient, and this pilot's small clusters (purity G=6, authority/fairness
G=8-9) are exactly the regime where this project's own prior work
(rq1_v1_1_robustness script 24) found classical Wald/LRT overconfident, so
a joint test here needs the same bootstrap correction as every single-term
test in this project, not a naive multi-df F-test. The classical
cluster-robust F/p (no bootstrap) is reported alongside as a companion, the
same role `analyze_sign_wcb.py`'s mixedlm fit plays for the single-term
tests.

Reuses `load_frame()` from `analyze_sign_wcb.py` in this directory (same
merge/coding logic) rather than reimplementing the join.

Run from the knobe repo root:
    .venv/bin/python analysis/ngo_extensions/moral_foundations_pilot/foundation_gradient_wcb.py

Reads outputs/elicit_results.jsonl + outputs/mf_pilot_dataset_selected.csv
(both local-only, same as analyze_sign_wcb.py); writes
outputs/foundation_gradient_wcb.csv (small summary table, committed).
"""
from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "rq1_v1_1_robustness"))
from analyze_sign_wcb import MODEL_KEYS, load_frame  # noqa: E402

warnings.filterwarnings("ignore")

SEED = 25  # next unused seed in this pilot's sequence (24 = analyze_sign_wcb.py)
CONDITION = 'C(condition, Treatment(reference="harm_control"))'
FULL_FORMULA = f"{{resp}} ~ sign_c * {CONDITION}"
RESTRICTED_FORMULA = f"{{resp}} ~ sign_c + {CONDITION}"


def wild_cluster_bootstrap_joint(
    data: pd.DataFrame, full_formula: str, restricted_formula: str,
    interaction_prefix: str, groups_col: str, *, B: int = 1999, seed: int = 0,
) -> dict:
    """Joint (multi-df) wild cluster bootstrap-F for the null that every
    term starting with `interaction_prefix` is zero. See module docstring."""
    full = smf.ols(full_formula, data=data)
    y = np.asarray(full.endog)
    X = np.asarray(full.exog)
    names = list(full.exog_names)
    term_idx = [i for i, n in enumerate(names) if n.startswith(interaction_prefix)]
    assert term_idx, f"no terms matched prefix {interaction_prefix!r} in {names}"

    restricted_res = smf.ols(restricted_formula, data=data).fit()
    fitted_r = restricted_res.fittedvalues.values
    resid_r = restricted_res.resid.values

    groups = data[groups_col].values
    R = np.zeros((len(term_idx), len(names)))
    for i, idx in enumerate(term_idx):
        R[i, idx] = 1.0

    full_res = sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": groups})
    wald_obs = full_res.wald_test(R, use_f=True, scalar=True)
    f_obs = float(wald_obs.statistic)

    unique_groups = np.unique(groups)
    rng = np.random.default_rng(seed)
    g_index = {g: i for i, g in enumerate(unique_groups)}
    group_codes = np.array([g_index[g] for g in groups])

    f_boot = np.empty(B)
    for b in range(B):
        w = rng.choice(np.array([-1.0, 1.0]), size=len(unique_groups))
        y_star = fitted_r + w[group_codes] * resid_r
        boot_res = sm.OLS(y_star, X).fit(cov_type="cluster", cov_kwds={"groups": groups})
        f_boot[b] = float(boot_res.wald_test(R, use_f=True, scalar=True).statistic)

    p_wcb = float(np.mean(f_boot >= f_obs))
    return dict(f_obs=f_obs, df_num=len(term_idx), p_classical=float(wald_obs.pvalue),
                p_wcb=p_wcb, n_groups=len(unique_groups), B=B)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--score", default="ev", choices=["ev", "parsed"],
                    help="ev (default) = the spec section-4.4 logit-fallback EV score. "
                         "parsed = the model's own numeric answer, parse_ok rows only. "
                         "Matches analyze_sign_wcb.py --score; this joint F-test is the "
                         "one fit the 6c73ab6 substitution did not cover.")
    args = p.parse_args()
    resp = "ev_rating" if args.score == "ev" else "parsed_rating"
    full, restricted = FULL_FORMULA.format(resp=resp), RESTRICTED_FORMULA.format(resp=resp)

    d = load_frame()
    if args.score == "parsed":
        d = d[d["parse_ok"] & d["parsed_rating"].notna()]
    rows = []
    for mk in MODEL_KEYS:
        cell = d[d["model_key"] == mk]
        fam, tuning = cell["family"].iloc[0], cell["tuning_status"].iloc[0]
        res = wild_cluster_bootstrap_joint(
            cell, full, restricted,
            interaction_prefix="sign_c:C(condition", groups_col="pair_id", seed=SEED,
        )
        rows.append(dict(family=fam, tuning=tuning, n=len(cell), **res))

    out = pd.DataFrame(rows)
    print(out.to_string(index=False))
    suffix = "" if args.score == "ev" else "_parsed"
    out_path = HERE / "outputs" / f"foundation_gradient_wcb{suffix}.csv"
    out.to_csv(out_path, index=False)
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
