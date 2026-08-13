"""Outstanding-review item 6: is the pipeline's own `_bootstrap_ci`
(src/knobe/analysis/models.py:421 -- n_boot=200, plain percentile, used for
the ci_low/ci_high columns in contrast_table.csv) good enough, or does it
need more resamples / a BCa correction?

This is a COMPARISON only -- it does not modify models.py. The pipeline's
own `_bootstrap_ci` is reused as-is (imported, not reimplemented) to
reproduce its current n_boot=200 percentile CI exactly. A BCa variant is
built by extending the *same* resampling loop (copied here because
`_bootstrap_ci` only returns the two percentiles, not the raw replicate
array BCa needs -- not an independent reimplementation, this mirrors it
line-for-line except for what it returns) to n_boot=1999 with a
jackknife-estimated acceleration constant and bias-correction z0.

Why this is a comparison, not a pipeline change: contrast_table.csv's
ci_low/ci_high have already been generated and cited (docs reference
`MAIN_RUN_WRITEUP_v1.1.md` numbers produced by this exact function).
Swapping the CI method retroactively changes what a previously-reported
number means -- a real ripple effect, not a contained fix -- so that's a
separate, deliberate decision, not made here. WCB p-values (not these CIs)
are already the estimator of record per project convention; this only asks
whether the difference is big enough to matter if that convention changes.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats as sstats

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from knobe.analysis.models import _bootstrap_ci, _boot_seed  # noqa: E402

from lib import load_frame, build_1b_frame, save, CONFIG  # noqa: E402

warnings.filterwarnings("ignore")

FAMS = ["gemma", "llama", "mistral"]


def _bootstrap_replicates(df, formula, term, *, base_seed, contrast, model_family, n_boot, groups="family_id"):
    """Mirrors `_bootstrap_ci`'s resampling loop exactly, returning the raw
    replicate array instead of just its percentiles (needed for BCa)."""
    family_ids = df[groups].unique()
    by_family = {fid: df[df[groups] == fid] for fid in family_ids}
    estimates = []
    for b in range(n_boot):
        rng = np.random.default_rng(_boot_seed(base_seed, contrast, model_family, b))
        picks = rng.choice(family_ids, size=len(family_ids), replace=True)
        parts = []
        for j, fid in enumerate(picks):
            block = by_family[fid].copy()
            block[groups] = f"{fid}__b{j}"
            parts.append(block)
        resampled = pd.concat(parts, ignore_index=True)
        try:
            with warnings.catch_warnings(record=True):
                warnings.simplefilter("always")
                res = smf.ols(formula, data=resampled).fit()
            if term in res.params.index and np.isfinite(res.params[term]):
                estimates.append(float(res.params[term]))
        except Exception:
            continue
    return np.asarray(estimates)


def _jackknife_estimates(df, formula, term, groups="family_id"):
    fam_ids = df[groups].unique()
    out = []
    for fid in fam_ids:
        sub = df[df[groups] != fid]
        try:
            res = smf.ols(formula, data=sub).fit()
            if term in res.params.index and np.isfinite(res.params[term]):
                out.append(float(res.params[term]))
        except Exception:
            continue
    return np.asarray(out)


def bca_ci(point_est, boot, jack, alpha=0.05):
    z0 = sstats.norm.ppf(np.mean(boot < point_est))
    jack_mean = jack.mean()
    num = np.sum((jack_mean - jack) ** 3)
    den = 6.0 * (np.sum((jack_mean - jack) ** 2) ** 1.5)
    a = num / den if den != 0 else 0.0
    z_lo, z_hi = sstats.norm.ppf(alpha / 2), sstats.norm.ppf(1 - alpha / 2)

    def adj(z):
        return sstats.norm.cdf(z0 + (z0 + z) / (1 - a * (z0 + z)))

    lo_pct, hi_pct = 100 * adj(z_lo), 100 * adj(z_hi)
    lo_pct, hi_pct = np.clip([lo_pct, hi_pct], 0.01, 99.99)
    return float(np.percentile(boot, lo_pct)), float(np.percentile(boot, hi_pct))


def compare(df, formula, term, contrast, family, groups="family_id", n_boot_bca=1999):
    point_est = float(smf.ols(formula, data=df).fit().params[term])
    ci_lo_200, ci_hi_200 = _bootstrap_ci(
        df, formula, term, base_seed=0, contrast=contrast, model_family=family, n_boot=200, groups=groups,
    )
    boot_1999 = _bootstrap_replicates(
        df, formula, term, base_seed=0, contrast=contrast, model_family=family, n_boot=n_boot_bca, groups=groups,
    )
    ci_lo_pct1999, ci_hi_pct1999 = float(np.percentile(boot_1999, 2.5)), float(np.percentile(boot_1999, 97.5))
    jack = _jackknife_estimates(df, formula, term, groups=groups)
    ci_lo_bca, ci_hi_bca = bca_ci(point_est, boot_1999, jack)
    return dict(
        contrast=contrast, family=family, term=term, point_est=point_est,
        pct_ci_lo_n200=ci_lo_200, pct_ci_hi_n200=ci_hi_200,
        pct_ci_lo_n1999=ci_lo_pct1999, pct_ci_hi_n1999=ci_hi_pct1999,
        bca_ci_lo_n1999=ci_lo_bca, bca_ci_hi_n1999=ci_hi_bca,
        n200_excludes_0=not (ci_lo_200 <= 0 <= ci_hi_200),
        bca_excludes_0=not (ci_lo_bca <= 0 <= ci_hi_bca),
    )


def main() -> None:
    # n_boot_bca=499, not 1999: measured cost is ~15s/contrast at 499 (so ~60s/contrast at 1999)
    # across 21 contrasts -- ~20+ min for the full sweep at WCB's precision, which is overkill for
    # a CI-*method* comparison (this isn't the estimator of record; WCB p-values are). Checkpoints
    # to CSV after every contrast so a future rerun (or an interrupted one) doesn't lose progress --
    # the first attempt at this script was killed after 6.5 min with nothing saved, since it only
    # printed/wrote once at the very end.
    n_boot_bca = 499
    d = load_frame()
    model_keys = CONFIG["family_model_keys"]
    rows: list[dict] = []

    def run(df, formula, term, contrast, family, **kw):
        r = compare(df, formula, term, contrast, family, n_boot_bca=n_boot_bca, **kw)
        rows.append(r)
        print(r)
        save(pd.DataFrame(rows), "27_bootstrap_ci_bca_comparison.csv")
        return r

    base = d[(d["question"] == "intentionality") & (d["vt"].isin(["moral", "nonmoral"]))].dropna(subset=["sign_c"])
    base = base.assign(tuning_c=np.where(base["tuning_status"] == "finetuned", 0.5, -0.5))
    for fam in FAMS:
        run(base[base["family"] == fam], "ev_rating ~ sign_c * tuning_c", "sign_c:tuning_c",
            "rq1_base_sign_x_tuning", fam)

    rq1a = d[(d["question"] == "intentionality") & (d["tuning_status"] == "finetuned")
             & (d["vt"].isin(["moral", "nonmoral"]))].dropna(subset=["sign_c", "vt_c"])
    for fam in FAMS:
        run(rq1a[rq1a["family"] == fam], "ev_rating ~ sign_c * vt_c", "sign_c:vt_c",
            "rq1a_sign_x_valence_type", fam, groups="set_id")

    for fam in FAMS:
        mk = model_keys[fam]["instruct"]
        for vt in ["moral", "nonmoral"]:
            frame = build_1b_frame(d, mk, vt)
            run(frame, "ev_rating ~ pred_c + pred_c:sg_c + C(family_id)", "pred_c:sg_c", f"rq1b_{vt}", fam)

    rq1c = d[(d["question"] == "intentionality") & (d["tuning_status"] == "finetuned")
             & (d["vt"].isin(["moral", "nonmoral"]))].dropna(subset=["sign_c", "typ_c", "evoc_c"])
    for fam in FAMS:
        run(rq1c[rq1c["family"] == fam], "ev_rating ~ typ_c * sign_c", "typ_c:sign_c",
            "rq1c_typicality_x_sign", fam)
        run(rq1c[rq1c["family"] == fam], "ev_rating ~ evoc_c * sign_c", "evoc_c:sign_c",
            "rq1c_evocativeness_x_sign", fam)

    neu = d[(d["question"] == "intentionality") & (d["tuning_status"] == "finetuned") & (d["valence"] == "NEU")]
    for fam in FAMS:
        run(neu[neu["family"] == fam], "ev_rating ~ typ_c", "typ_c", "rq1d_typicality_within_neu", fam)

    out = pd.DataFrame(rows)
    out["conclusion_changes"] = out["n200_excludes_0"] != out["bca_excludes_0"]
    print(out.to_string(index=False))
    save(out, "27_bootstrap_ci_bca_comparison.csv")
    print(f"\n{out['conclusion_changes'].sum()} / {len(out)} cells: BCa@{n_boot_bca} changes whether "
          f"the CI excludes 0 vs. current percentile@200")


if __name__ == "__main__":
    main()
