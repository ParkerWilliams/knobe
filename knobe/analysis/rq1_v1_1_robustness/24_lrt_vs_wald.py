"""Outstanding-review item 8: likelihood-ratio tests alongside Wald, for the
same primary contrasts already WCB-tested in scripts 01/02/03/07. ML fits
(reml=False, matching those scripts) for full vs. restricted (term dropped),
LRT = -2*(llf_restricted - llf_full), df=1, p from chi2.sf. RQ1b's primary
spec is OLS with family fixed effects (not MixedLM), so its LRT uses
statsmodels' own `compare_lr_test` on nested OLS fits instead.

This checks whether LRT ever disagrees *qualitatively* with the already-
reported Wald/WCB p-values -- new information if so, confirmation if not.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats

from lib import load_frame, build_1b_frame, wild_cluster_bootstrap, save, CONFIG

warnings.filterwarnings("ignore")

FAMS = ["gemma", "llama", "mistral"]


def lmm_lrt(sub: pd.DataFrame, full_formula: str, restricted_formula: str, term: str, groups_col: str) -> dict:
    m_full = smf.mixedlm(full_formula, sub, groups=sub[groups_col]).fit(reml=False, method="lbfgs")
    m_res = smf.mixedlm(restricted_formula, sub, groups=sub[groups_col]).fit(reml=False, method="lbfgs")
    lrt_stat = 2 * (m_full.llf - m_res.llf)
    df = len(m_full.params) - len(m_res.params)
    lrt_p = float(stats.chi2.sf(lrt_stat, df)) if lrt_stat >= 0 else float("nan")
    return dict(wald_p=float(m_full.pvalues[term]), lrt_stat=float(lrt_stat), lrt_df=df, lrt_p=lrt_p)


def ols_fe_lrt(sub: pd.DataFrame, full_formula: str, restricted_formula: str) -> dict:
    m_full = smf.ols(full_formula, sub).fit()
    m_res = smf.ols(restricted_formula, sub).fit()
    lrt_stat, lrt_p, lrt_df = m_full.compare_lr_test(m_res)
    return dict(lrt_stat=float(lrt_stat), lrt_df=int(lrt_df), lrt_p=float(lrt_p))


def main() -> None:
    d = load_frame()
    model_keys = CONFIG["family_model_keys"]
    rows = []

    base = d[(d["question"] == "intentionality") & (d["vt"].isin(["moral", "nonmoral"]))].dropna(subset=["sign_c"])
    base = base.assign(tuning_c=np.where(base["tuning_status"] == "finetuned", 0.5, -0.5))
    for fam in FAMS:
        s = base[base["family"] == fam]
        wcb = wild_cluster_bootstrap(s, "ev_rating ~ sign_c * tuning_c", "sign_c:tuning_c", "family_id", seed=2)
        r = lmm_lrt(s, "ev_rating ~ sign_c * tuning_c", "ev_rating ~ sign_c + tuning_c",
                    "sign_c:tuning_c", "family_id")
        rows.append(dict(contrast="rq1_base_sign_x_tuning", family=fam, term="sign_c:tuning_c",
                          p_wcb=wcb["p_wcb"], **r))

    rq1a = d[(d["question"] == "intentionality") & (d["tuning_status"] == "finetuned")
             & (d["vt"].isin(["moral", "nonmoral"]))].dropna(subset=["sign_c", "vt_c"])
    for fam in FAMS:
        s = rq1a[rq1a["family"] == fam]
        wcb = wild_cluster_bootstrap(s, "ev_rating ~ sign_c * vt_c", "sign_c:vt_c", "set_id", seed=1)
        r = lmm_lrt(s, "ev_rating ~ sign_c * vt_c", "ev_rating ~ sign_c + vt_c", "sign_c:vt_c", "set_id")
        rows.append(dict(contrast="rq1a_sign_x_valence_type", family=fam, term="sign_c:vt_c",
                          p_wcb=wcb["p_wcb"], **r))

    for fam in FAMS:
        mk = model_keys[fam]["instruct"]
        for vt in ["moral", "nonmoral"]:
            frame = build_1b_frame(d, mk, vt)
            wcb = wild_cluster_bootstrap(frame, "ev_rating ~ pred_c + pred_c:sg_c + C(family_id)",
                                          "pred_c:sg_c", "family_id", seed=9)
            r = ols_fe_lrt(frame, "ev_rating ~ pred_c + pred_c:sg_c + C(family_id)",
                            "ev_rating ~ pred_c + C(family_id)")
            rows.append(dict(contrast="rq1b", family=fam, valence_type=vt, term="pred_c:sg_c",
                              p_wcb=wcb["p_wcb"], wald_p=float("nan"), **r))

    rq1c = d[(d["question"] == "intentionality") & (d["tuning_status"] == "finetuned")
             & (d["vt"].isin(["moral", "nonmoral"]))].dropna(subset=["sign_c", "typ_c", "evoc_c"])
    for fam in FAMS:
        s = rq1c[rq1c["family"] == fam]
        wcb1 = wild_cluster_bootstrap(s, "ev_rating ~ typ_c * sign_c", "typ_c:sign_c", "family_id", seed=3)
        r1 = lmm_lrt(s, "ev_rating ~ typ_c * sign_c", "ev_rating ~ typ_c + sign_c", "typ_c:sign_c", "family_id")
        rows.append(dict(contrast="rq1c_typicality_x_sign", family=fam, term="typ_c:sign_c",
                          p_wcb=wcb1["p_wcb"], **r1))
        wcb2 = wild_cluster_bootstrap(s, "ev_rating ~ evoc_c * sign_c", "evoc_c:sign_c", "family_id", seed=4)
        r2 = lmm_lrt(s, "ev_rating ~ evoc_c * sign_c", "ev_rating ~ evoc_c + sign_c", "evoc_c:sign_c", "family_id")
        rows.append(dict(contrast="rq1c_evocativeness_x_sign", family=fam, term="evoc_c:sign_c",
                          p_wcb=wcb2["p_wcb"], **r2))

    neu = d[(d["question"] == "intentionality") & (d["tuning_status"] == "finetuned") & (d["valence"] == "NEU")].copy()
    for fam in FAMS:
        s = neu[neu["family"] == fam]
        wcb = wild_cluster_bootstrap(s, "ev_rating ~ typ_c", "typ_c", "family_id", seed=6)
        r = lmm_lrt(s, "ev_rating ~ typ_c", "ev_rating ~ 1", "typ_c", "family_id")
        rows.append(dict(contrast="rq1d_typicality_within_neu", family=fam, term="typ_c",
                          p_wcb=wcb["p_wcb"], **r))

    out = pd.DataFrame(rows)
    cols = ["contrast", "family", "valence_type", "term", "wald_p", "lrt_stat", "lrt_df", "lrt_p", "p_wcb"]
    out = out.reindex(columns=cols)
    out["disagrees_with_wcb"] = (out["lrt_p"] < 0.05) != (out["p_wcb"] < 0.05)
    print(out.to_string(index=False))
    save(out, "24_lrt_vs_wald.csv")


if __name__ == "__main__":
    main()
