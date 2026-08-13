"""Outstanding-review item 2: SIMEX (Cook & Stefanski 1994) correction for
RQ1b's pred_c measurement error. pred_c (an item's blame/praise mean rating,
standardized) is built from repeated sample_idx draws per item
(lib.py::build_1b_frame) -- the per-item measurement-error variance of that
mean is directly estimable as Var(ev_rating within item) / n_samples, no new
data or tooling needed.

Procedure: for lambda in {0, .5, 1, 1.5, 2}, add N(0, lambda * item-specific
measurement-error variance) noise to pred_c (drawn once per item, broadcast
across that item's rows -- pred_c is an item-level constant), refit
`ev_rating ~ pred_c_sim + pred_c_sim:sg_c + C(family_id)` (the same
family-FE spec 07_rq1b_family_fe_wcb.py already established as the
corrected refit engine), average the pred_c_sim:sg_c coefficient over B
reps, then extrapolate the lambda-vs-coefficient curve (quadratic) back to
lambda=-1 (the "no measurement error" point) for the SIMEX-corrected
estimate.

Run on all 6 rq1b cells for the headline attenuation-correction numbers.
For mistral-nonmoral specifically -- the cell with the named disagreement
between the family-FE WCB (p=.255) and family-random-slope model (p=.0021,
docs/RQ1_STATISTICAL_METHODS_v1.1.md section 10.2) -- additionally runs a
family-cluster bootstrap of the whole SIMEX procedure (resample families,
redo naive+extrapolation each draw) to get a percentile CI/p-value on the
corrected estimate, since that's the one place the report needs an answer
to "does this resolve the disagreement," not just a corrected point estimate.

Seeds: config.yaml `28_rq1b_simex` (main curve) and `28_rq1b_simex_bootstrap`
(mistral-nonmoral cluster bootstrap only), one RNG per script instantiated
once and consumed sequentially, matching this directory's existing
convention (see config.yaml's wild_cluster_bootstrap.seeds comment).
"""
from __future__ import annotations

import time
import warnings

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from lib import load_frame, build_1b_frame, save, CONFIG

warnings.filterwarnings("ignore")

FAMS = ["gemma", "llama", "mistral"]
LAMBDAS = np.array([0.0, 0.5, 1.0, 1.5, 2.0])
TERM = "pred_c_sim:sg_c"
FORMULA = "ev_rating ~ pred_c_sim + pred_c_sim:sg_c + C(family_id)"


def item_measurement_error(prepared: pd.DataFrame, model_key: str, valence_type: str) -> pd.Series:
    """Mirrors build_1b_frame's blame/praise item-mean selection exactly
    (that intermediate frame isn't exposed there), returning each item's
    measurement-error variance of pred_raw (= within-item response variance
    / n samples), rescaled to the pred_c (standardized) scale."""
    sub = prepared[(prepared["model_key"] == model_key) & (prepared["vt"] == valence_type)]
    channel = np.where(sub["sign"] == "bad", "blame", "praise")
    resp = sub.assign(_channel=channel)
    resp = resp[resp["question"] == resp["_channel"]]
    stats = resp.groupby("variant_id")["ev_rating"].agg(["mean", "var", "count"])
    mev_raw = stats["var"] / stats["count"]

    item_pred = stats["mean"]
    sd_ = item_pred.std(ddof=0)
    mev_c = mev_raw / (sd_**2) if sd_ > 0 else mev_raw * 0.0
    return mev_c


def simex_curve(frame: pd.DataFrame, mev_c: pd.Series, rng: np.random.Generator, n_boot: int) -> np.ndarray:
    """Returns the mean pred_c_sim:sg_c coefficient at each lambda in LAMBDAS."""
    item_ids = frame["variant_id"].unique()
    mev_arr = mev_c.reindex(item_ids).fillna(mev_c.mean()).values
    betas = np.empty(len(LAMBDAS))
    for li, lam in enumerate(LAMBDAS):
        draws = np.empty(n_boot)
        for b in range(n_boot):
            z = rng.standard_normal(len(item_ids))
            noise = pd.Series(np.sqrt(lam * mev_arr) * z, index=item_ids)
            sim = frame.copy()
            sim["pred_c_sim"] = sim["pred_c"] + sim["variant_id"].map(noise)
            res = smf.ols(FORMULA, data=sim).fit()
            draws[b] = res.params.get(TERM, np.nan)
        betas[li] = np.nanmean(draws)
    return betas


def extrapolate(betas: np.ndarray) -> float:
    coeffs = np.polyfit(LAMBDAS, betas, 2)
    return float(np.polyval(coeffs, -1.0))


def naive_estimate(frame: pd.DataFrame) -> tuple[float, float]:
    res = smf.ols("ev_rating ~ pred_c + pred_c:sg_c + C(family_id)", data=frame).fit()
    return float(res.params["pred_c:sg_c"]), float(res.pvalues["pred_c:sg_c"])


def main() -> None:
    d = load_frame()
    model_keys = CONFIG["family_model_keys"]
    seed_main = CONFIG["wild_cluster_bootstrap"]["seeds"]["28_rq1b_simex"]
    seed_boot = CONFIG["wild_cluster_bootstrap"]["seeds"]["28_rq1b_simex_bootstrap"]
    rng = np.random.default_rng(seed_main)

    rows = []
    for fam in FAMS:
        mk = model_keys[fam]["instruct"]
        for vt in ["moral", "nonmoral"]:
            t0 = time.time()
            frame = build_1b_frame(d, mk, vt)
            mev_c = item_measurement_error(d, mk, vt)
            naive_beta, naive_p = naive_estimate(frame)
            betas = simex_curve(frame, mev_c, rng, n_boot=200)
            simex_beta = extrapolate(betas)
            attenuation_pct = 100 * (simex_beta - naive_beta) / naive_beta if naive_beta != 0 else float("nan")
            rows.append(dict(
                family=fam, valence_type=vt, naive_beta=naive_beta, naive_p=naive_p,
                mean_mev_c=float(mev_c.mean()), beta_lambda0=betas[0], beta_lambda2=betas[-1],
                simex_beta=simex_beta, attenuation_pct=attenuation_pct, secs=time.time() - t0,
            ))
            print(rows[-1])
            save(pd.DataFrame(rows), "28_rq1b_simex.csv")

    out = pd.DataFrame(rows)
    print(out.to_string(index=False))
    save(out, "28_rq1b_simex.csv")

    # Mistral-nonmoral: family-cluster bootstrap of the whole SIMEX procedure.
    print("\n--- mistral-nonmoral: family-cluster bootstrap of the SIMEX procedure ---")
    mk = model_keys["mistral"]["instruct"]
    frame = build_1b_frame(d, mk, "nonmoral")
    mev_c = item_measurement_error(d, mk, "nonmoral")
    fam_ids = frame["family_id"].unique()

    t0 = time.time()
    rng_boot = np.random.default_rng(seed_boot)
    n_boot_outer = 200
    n_boot_inner = 20
    boot_betas = np.empty(n_boot_outer)
    for b in range(n_boot_outer):
        picks = rng_boot.choice(fam_ids, size=len(fam_ids), replace=True)
        parts = []
        for j, fid in enumerate(picks):
            block = frame[frame["family_id"] == fid].copy()
            block["family_id"] = f"{fid}__b{j}"
            parts.append(block)
        resampled = pd.concat(parts, ignore_index=True)
        try:
            betas_b = simex_curve(resampled, mev_c, rng_boot, n_boot=n_boot_inner)
            boot_betas[b] = extrapolate(betas_b)
        except Exception:
            boot_betas[b] = np.nan
        if b == 0:
            per_rep = time.time() - t0
            print(f"(first bootstrap rep took {per_rep:.1f}s, extrapolating to ~{per_rep * n_boot_outer / 60:.1f} min total)")

    boot_betas = boot_betas[np.isfinite(boot_betas)]
    ci_lo, ci_hi = np.percentile(boot_betas, [2.5, 97.5])
    p_boot = float(2 * min(np.mean(boot_betas <= 0), np.mean(boot_betas >= 0)))
    point_simex = extrapolate(simex_curve(frame, mev_c, np.random.default_rng(seed_main + 1000), n_boot=200))
    result = dict(
        family="mistral", valence_type="nonmoral", simex_beta=point_simex,
        boot_ci_lo=float(ci_lo), boot_ci_hi=float(ci_hi), boot_p_approx=p_boot,
        n_boot_outer=n_boot_outer, n_boot_inner=n_boot_inner, n_valid_draws=len(boot_betas),
        secs=time.time() - t0,
    )
    print(result)
    save(pd.DataFrame([result]), "28_rq1b_simex_mistral_nonmoral_bootstrap.csv")


if __name__ == "__main__":
    main()
