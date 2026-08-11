"""Shared data loading and the wild-cluster-bootstrap implementation for the
v1.1 RQ1 small-cluster-robustness re-analysis (see config.yaml, README.md,
and docs/RQ1_STATISTICAL_METHODS_v1.1.md sections 8-11).

Not part of the `knobe` package -- these are one-off research scripts, run
from the repo root with the project's own .venv:

    .venv/bin/python analysis/rq1_v1_1_robustness/01_rq1_base_and_rq1c_wcb.py

Each numbered script loads results/v1.1/results_all.jsonl (see config.yaml
for the unpack step) + data/release/v1.1/vignettes.csv (+ curated_v1.1.csv
for severity) via `load_frame()`, runs its specific check, and writes a
small CSV to outputs/.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG = yaml.safe_load((Path(__file__).parent / "config.yaml").read_text())
OUTPUT_DIR = Path(__file__).parent / "outputs"

_SET_ID_VALENCE_RE = re.compile(r"-(MB|MG|NMB|NMG|NEU)-")


def _derive_set_id(family_id: str) -> str:
    """Mirrors src/knobe/analysis/models.py::_derive_set_id exactly."""
    return _SET_ID_VALENCE_RE.sub("-", family_id)


def _logit_ev_rating(logprobs_0_10) -> float:
    """Mirrors src/knobe/analysis/ingest.py::logit_ev_rating exactly (the
    spec §4.4 logit-fallback score used uniformly for all v1.1 checkpoints)."""
    lp = np.asarray(logprobs_0_10, dtype=float)
    w = np.exp(lp - lp.max())
    return float((w * np.arange(len(lp))).sum() / w.sum())


def load_frame() -> pd.DataFrame:
    """Builds the merged, effect-coded response-level frame every script in
    this directory starts from: one row per (model_key, variant_id,
    question_type, sample_idx), joined against vignette metadata (sign,
    typicality, evocativeness, valence, family_id, set_id) and family-level
    curation severity."""
    results_path = REPO_ROOT / CONFIG["data"]["results_jsonl"]
    vign_path = REPO_ROOT / CONFIG["data"]["vignettes_csv"]
    curated_path = REPO_ROOT / CONFIG["data"]["curated_csv"]
    if not results_path.exists():
        raise FileNotFoundError(
            f"{results_path} not found -- unpack it first (knobe/README.md "
            "'Study results (compressed)': gunzip -c results_dist/results_v1.1_all.jsonl.gz "
            "> results/v1.1/results_all.jsonl)."
        )

    df = pd.read_json(results_path, lines=True)
    vign = pd.read_csv(vign_path)
    curated = pd.read_csv(curated_path)

    df["ev_rating"] = df["logprobs_0_10"].apply(_logit_ev_rating)
    df["variant_id"] = df["prompt_id"].str.split("::").str[0]
    df["question"] = df["prompt_id"].str.split("::").str[1]
    df["family"] = df["model_key"].str.split("-").str[0]
    df["tuning_status"] = np.where(df["model_key"].str.contains("instruct"), "finetuned", "pretrained")

    vign = vign.copy()
    vign["set_id"] = vign["family_id"].map(_derive_set_id)
    vign["vt"] = np.where(
        vign["valence"].isin(["MB", "MG"]), "moral",
        np.where(vign["valence"].isin(["NMB", "NMG"]), "nonmoral", "neu"),
    )

    d = df.merge(
        vign[["variant_id", "family_id", "set_id", "sign", "typicality", "evocativeness", "valence", "vt"]],
        on="variant_id",
    )

    coding = CONFIG["effect_coding"]
    d["sign_c"] = d["sign"].map(coding["sign_c"])
    d["vt_c"] = d["vt"].map(coding["vt_c"])
    d["typ_c"] = d["typicality"].map(coding["typ_c"])
    d["evoc_c"] = d["evocativeness"].map(coding["evoc_c"])

    fam_sev = curated.groupby("family_id")["severity"].mean().rename("severity_fam")
    d = d.merge(fam_sev, on="family_id", how="left")
    d["severity_c"] = d["severity_fam"] - fam_sev.mean()

    return d


def build_1b_frame(prepared: pd.DataFrame, model_key: str, valence_type: str) -> pd.DataFrame:
    """Mirrors src/knobe/analysis/models.py::prepare_1b_frame's logic against
    this script directory's own frame shape (ev_rating/question columns
    rather than the pipeline's rating/question_type)."""
    sub = prepared[(prepared["model_key"] == model_key) & (prepared["vt"] == valence_type)]
    channel = np.where(sub["sign"] == "bad", "blame", "praise")
    resp = sub.assign(_channel=channel)
    resp = resp[resp["question"] == resp["_channel"]]
    item_pred = resp.groupby("variant_id")["ev_rating"].mean()

    intent = sub[sub["question"] == "intentionality"].copy()
    intent["pred_raw"] = intent["variant_id"].map(item_pred)
    intent = intent.dropna(subset=["pred_raw"])
    mean_, sd_ = intent["pred_raw"].mean(), intent["pred_raw"].std(ddof=0)
    intent["pred_c"] = (intent["pred_raw"] - mean_) / sd_ if sd_ > 0 else 0.0
    intent["sg_c"] = intent["sign_c"]
    return intent


def wild_cluster_bootstrap(
    data: pd.DataFrame, formula: str, term: str, groups_col: str, *, B: int = 1999, seed: int = 0,
) -> dict:
    """Cameron-Gelbach-Miller (2008) wild cluster bootstrap-t: Rademacher
    weights, restricted (null-imposed) residual DGP, OLS + cluster-robust SE
    as the refit estimator. Returns beta_obs (full-model OLS), t_obs
    (cluster-robust), p_wcb (two-sided fraction of |t*| >= |t_obs|), and
    n_groups. See docs/RQ1_STATISTICAL_METHODS_v1.1.md section 8."""
    full = smf.ols(formula, data=data)
    y = np.asarray(full.endog)
    X = np.asarray(full.exog)
    names = list(full.exog_names)
    idx = names.index(term)

    X_r = np.delete(X, idx, axis=1)
    if X_r.shape[1] == 0:
        fitted_r = np.zeros_like(y)
        resid_r = y - fitted_r
    else:
        restricted = sm.OLS(y, X_r).fit()
        fitted_r = restricted.fittedvalues
        resid_r = restricted.resid

    groups = data[groups_col].values
    full_res = sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": groups})
    beta_obs = float(full_res.params[idx])
    se_obs = float(full_res.bse[idx])
    t_obs = float(full_res.tvalues[idx])

    unique_groups = np.unique(groups)
    rng = np.random.default_rng(seed)
    g_index = {g: i for i, g in enumerate(unique_groups)}
    group_codes = np.array([g_index[g] for g in groups])

    t_boot = np.empty(B)
    for b in range(B):
        w = rng.choice(np.array([-1.0, 1.0]), size=len(unique_groups))
        y_star = fitted_r + w[group_codes] * resid_r
        boot_res = sm.OLS(y_star, X).fit(cov_type="cluster", cov_kwds={"groups": groups})
        t_boot[b] = boot_res.tvalues[idx]

    p_wcb = float(np.mean(np.abs(t_boot) >= abs(t_obs)))
    return dict(beta_obs=beta_obs, se_obs=se_obs, t_obs=t_obs, p_wcb=p_wcb, n_groups=len(unique_groups), B=B)


def save(df: pd.DataFrame, name: str) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / name
    df.to_csv(path, index=False)
    print(f"wrote {path}")
    return path
