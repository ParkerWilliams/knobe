"""S7b: RQ3 patch decomposition + RQ4 probe alignment + report emission
(master spec §5.3-5.4; WO-7).

Consumes the WO-6 patch results and the WO-7a probes and answers:

  * **RQ3 (decomposition).** When a critical layer is patched, is the drop in
    the whole-layer intentionality gap driven by suppressing ONE construct
    component (moral / nonmoral / typicality / evocativeness / neutral
    offset) -- selective suppression -- or all of them uniformly? A
    per-scaffold component-gap table feeds a statsmodels ``MixedLM`` with a
    scaffold random intercept: ``gap ~ C(config) * C(component)``. A
    significant ``config × component`` interaction (LRT vs the no-interaction
    model) ⇒ selective; none ⇒ uniform.

  * **RQ4 (probe alignment).** For a patched config, Δh = patched − unpatched
    final-token residual per item at every downstream layer (sourced by
    recomputing via the backend's ``run_patched_with_cache`` −
    ``run_with_cache`` -- chosen over persisting a second patched-acts cache
    so patch.py's on-disk contract is untouched). cos(mean Δh, probe
    direction_c) per construct c per layer is tested against TWO nulls: (a)
    random unit vectors matched in d_model (analytic null cos ~ N(0, 1/d),
    also simulated), and (b) permuted-label probe directions (same pipeline,
    labels shuffled). The evocativeness probe is flagged exploratory
    (DR §6.1) in the output metadata + figure caption.

  * **Gemma Scope (config-gated).** ``--sae gemma-scope`` encodes residuals
    with the pretrained SAE and reports top-k features by |Δ activation|;
    real loading is gpu-marked, the Fake path uses a small random sparse
    dictionary so the report plumbing is testable. Neuronpedia labels are a
    documented stub.

GPU-free by default (numpy/pandas/statsmodels over cached artifacts); the
only backend touched is via the ResidualAccess interface (spec §5.1).
"""
from __future__ import annotations

import sys
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd

from knobe.mech._data import scaffold_key
from knobe.schemas import PatchRecord, VignetteRow

NEUTRAL_MIDPOINT = 5.0
COMPONENTS = ("moral", "nonmoral", "typ", "evoc", "neu_offset")


# ---------------------------------------------------------------------------
# RQ3: per-scaffold component gaps from PatchRecords.
# ---------------------------------------------------------------------------


def _within_sign_gap(df: pd.DataFrame, col: str, hi: str, lo: str) -> float:
    gaps = []
    for sign in ("bad", "good"):
        s = df[df["sign"] == sign]
        hi_m = s.loc[s[col] == hi, "ev"].mean()
        lo_m = s.loc[s[col] == lo, "ev"].mean()
        if not (np.isnan(hi_m) or np.isnan(lo_m)):
            gaps.append(hi_m - lo_m)
    return float(np.mean(gaps)) if gaps else float("nan")


def _component_gaps(df: pd.DataFrame) -> dict[str, float]:
    """The five §5.3 component gaps for one (scaffold, config) slice."""
    def mean_where(mask):
        v = df.loc[mask, "ev"]
        return float(v.mean()) if len(v) else float("nan")

    return {
        "moral": mean_where(df["valence"] == "MB") - mean_where(df["valence"] == "MG"),
        "nonmoral": mean_where(df["valence"] == "NMB") - mean_where(df["valence"] == "NMG"),
        "typ": _within_sign_gap(df, "typicality", "uncommon", "common"),
        "evoc": _within_sign_gap(df, "evocativeness", "high", "low"),
        "neu_offset": mean_where(df["valence"] == "NEU") - NEUTRAL_MIDPOINT,
    }


def component_gaps_from_records(
    records_by_config: dict[str, Sequence[PatchRecord]],
    vignettes: Sequence[VignetteRow],
) -> pd.DataFrame:
    """Per-scaffold component gaps for each patch config, in LONG form
    (columns: group, config, component, gap). ``records_by_config`` maps a
    config label ("baseline", "[5]", ...) → its PatchRecords. Each record's
    EV rating is ``parsed_rating``; item metadata joins via prompt_id →
    variant_id → vignettes.csv. Gaps are computed WITHIN each scaffold group
    so the mixed model can carry a scaffold random intercept."""
    by_variant = {v.variant_id: v for v in vignettes}
    rows = []
    for config, records in records_by_config.items():
        recs = []
        for r in records:
            variant_id = r.prompt_id.split("::", 1)[0]
            v = by_variant.get(variant_id)
            if v is None:
                continue
            recs.append(
                {
                    "scaffold": scaffold_key(v.family_id),
                    "valence": v.valence,
                    "sign": v.sign,
                    "typicality": v.typicality,
                    "evocativeness": v.evocativeness,
                    "ev": float(r.parsed_rating) if r.parsed_rating is not None else np.nan,
                }
            )
        df = pd.DataFrame(recs)
        if df.empty:
            continue
        for scaffold, grp in df.groupby("scaffold"):
            gaps = _component_gaps(grp)
            for component, gap in gaps.items():
                rows.append({"group": scaffold, "config": config, "component": component, "gap": gap})
    return pd.DataFrame(rows).dropna(subset=["gap"]).reset_index(drop=True)


def normalize_gaps(
    long_df: pd.DataFrame, *, baseline_config: str = "baseline", eps: float = 0.25
) -> pd.DataFrame:
    """Baseline-normalize per-scaffold component gaps: ``norm_gap`` = gap /
    baseline_gap for that (group, component). This makes 'uniform suppression'
    mean the SAME thing (proportional) in both the interaction test and the
    RQ3 table/figure -- an additive test on raw gaps would flag proportional
    suppression of unequal-magnitude baselines as spuriously selective.

    (group, component) cells whose baseline gap is smaller than ``eps`` in
    magnitude are EXCLUDED (a proportion relative to a near-zero baseline is
    undefined; e.g. the NEU offset can sit near 0) -- documented, not silently
    imputed. Returns the long frame with an added ``norm_gap`` column."""
    base = (
        long_df[long_df["config"] == baseline_config][["group", "component", "gap"]]
        .rename(columns={"gap": "base_gap"})
    )
    merged = long_df.merge(base, on=["group", "component"], how="inner")
    merged = merged[merged["base_gap"].abs() >= eps].copy()
    merged["norm_gap"] = merged["gap"] / merged["base_gap"]
    return merged


def fit_suppression_model(
    long_df: pd.DataFrame, *, baseline_config: str = "baseline", eps: float = 0.25
) -> dict:
    """Selective- vs uniform-suppression test (RQ3), on BASELINE-NORMALIZED
    gaps (``normalize_gaps``): MixedLM ``norm_gap ~ C(config) * C(component)``
    with a scaffold (``group``) random intercept, ML-fit. The
    ``config × component`` interaction is tested by a likelihood-ratio test
    against the no-interaction model. Because the gaps are normalized to each
    family×component baseline, 'uniform' = the SAME proportional suppression
    across components (parallel → no interaction), and 'selective' = one
    component suppressed differently (interaction). Returns
    ``{interaction_p, lr_stat, df_diff, selective, converged, n_excluded, ...}``;
    a significant interaction (p<0.05) ⇒ selective suppression.

    Falls back to an OLS-based interaction F-test if the mixed model fails to
    converge (recorded in ``fallback_used`` -- never silently dropped)."""
    try:
        import statsmodels.formula.api as smf
        from scipy import stats
    except ImportError as exc:  # pragma: no cover -- exercised only without the extra
        raise RuntimeError(
            "statsmodels + scipy are required for the RQ3 patch decomposition -- install "
            "the 'mech' or 'stats' extra (`uv pip install -e '.[mech]'`)."
        ) from exc

    norm = normalize_gaps(long_df, baseline_config=baseline_config, eps=eps)
    out = {"interaction_p": float("nan"), "lr_stat": float("nan"), "df_diff": 0,
           "selective": False, "converged": False, "fallback_used": False,
           "n_groups": int(norm["group"].nunique()),
           "n_excluded": int(len(long_df) - len(norm))}

    def _ll(formula):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            md = smf.mixedlm(formula, data=norm, groups=norm["group"])
            res = md.fit(reml=False, method="lbfgs")
        return res

    try:
        full = _ll("norm_gap ~ C(config) * C(component)")
        reduced = _ll("norm_gap ~ C(config) + C(component)")
        lr = 2.0 * (full.llf - reduced.llf)
        # df = number of dropped interaction fixed-effect terms.
        df_diff = int(len(full.fe_params) - len(reduced.fe_params))
        p = float(stats.chi2.sf(lr, df_diff)) if df_diff > 0 else float("nan")
        out.update({"interaction_p": p, "lr_stat": float(lr), "df_diff": df_diff,
                    "selective": bool(p < 0.05), "converged": True})
        return out
    except Exception:
        out["fallback_used"] = True

    # OLS fallback: nested F-test on the interaction terms.
    try:
        import statsmodels.api as sm
        from statsmodels.formula.api import ols

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            full = ols("norm_gap ~ C(config) * C(component)", data=norm).fit()
            reduced = ols("norm_gap ~ C(config) + C(component)", data=norm).fit()
        anova = sm.stats.anova_lm(reduced, full)
        p = float(anova["Pr(>F)"].iloc[-1])
        out.update({"interaction_p": p, "selective": bool(p < 0.05), "converged": True})
    except Exception:
        pass
    return out


def rq3_normalized_table(patch_metrics: pd.DataFrame) -> pd.DataFrame:
    """Layer × component gap normalized to the unpatched baseline (RQ3 table/
    figure). From ``patch_metrics.parquet``: the baseline row is
    ``layers == "[]"``; each patched config's component gap is reported both
    raw and as a fraction of the baseline gap (``normalized`` = gap /
    baseline_gap; ``suppression`` = 1 − normalized). Components map from the
    patch_metrics columns delta_moral/delta_nonmoral/e_typ/e_evoc/
    delta_neutral_offset."""
    col_map = {
        "moral": "delta_moral", "nonmoral": "delta_nonmoral",
        "typ": "e_typ", "evoc": "e_evoc", "neu_offset": "delta_neutral_offset",
    }
    baseline = patch_metrics[patch_metrics["layers"] == "[]"]
    if baseline.empty:
        raise ValueError("patch_metrics has no baseline row (layers == '[]').")
    base = baseline.iloc[0]
    rows = []
    for _, r in patch_metrics[patch_metrics["layers"] != "[]"].iterrows():
        for component, col in col_map.items():
            base_gap = float(base[col])
            gap = float(r[col])
            normalized = gap / base_gap if abs(base_gap) > 1e-9 else float("nan")
            rows.append(
                {
                    "model_key": r.get("model_key", base.get("model_key", "?")),
                    "family": r.get("family", ""),
                    "layers": r["layers"],
                    "component": component,
                    "gap": gap,
                    "baseline_gap": base_gap,
                    "normalized": normalized,
                    "suppression": 1.0 - normalized if normalized == normalized else float("nan"),
                }
            )
    return pd.DataFrame(rows)


def plot_rq3(normalized: pd.DataFrame, out_path: Path) -> None:
    """Grouped-bar figure: per patched config, each component's baseline-
    normalized gap (RQ3). Selective suppression shows one bar near zero while
    others stay near one; uniform suppression lowers all bars together."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    configs = list(dict.fromkeys(normalized["layers"]))
    components = [c for c in COMPONENTS if c in set(normalized["component"])]
    fig, ax = plt.subplots(figsize=(9, 5))
    width = 0.8 / max(len(components), 1)
    x = np.arange(len(configs))
    for i, comp in enumerate(components):
        sub = normalized[normalized["component"] == comp].set_index("layers")
        vals = [float(sub.loc[c, "normalized"]) if c in sub.index else np.nan for c in configs]
        ax.bar(x + i * width, vals, width, label=comp)
    ax.axhline(1.0, color="k", lw=0.7, ls="--")
    ax.set_xticks(x + 0.4 - width / 2)
    ax.set_xticklabels(configs, rotation=45, ha="right", fontsize=7)
    ax.set_ylabel("gap normalized to unpatched baseline")
    ax.set_title("RQ3 patch decomposition (per-component suppression)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)


# ---------------------------------------------------------------------------
# RQ4: probe-alignment of patch-induced activation shifts.
# ---------------------------------------------------------------------------


def mean_delta_h(recipient, donor, prompt_texts: Sequence[str], config_layers: Sequence[int]) -> dict[int, np.ndarray]:
    """Δh̄ per downstream layer: mean over items of (patched − unpatched)
    final-token residual, sourced by recomputing via the backend
    (``run_patched_with_cache`` − ``run_with_cache``; WO-7 sourcing choice).
    Returns {layer: mean Δh vector}."""
    unpatched = recipient.run_with_cache(prompt_texts, layers=None, positions="final")
    patched = recipient.run_patched_with_cache(prompt_texts, donor, list(config_layers), positions="final")
    delta = patched.resid.astype(np.float64) - unpatched.resid.astype(np.float64)  # [n, L+1, d]
    mean = delta.mean(axis=0)  # [L+1, d]
    return {int(l): mean[i] for i, l in enumerate(unpatched.layers)}


def _cos(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return float(np.dot(a, b) / (na * nb)) if na > 1e-12 and nb > 1e-12 else 0.0


def random_unit_null(delta_h_vec: np.ndarray, *, n: int = 1000, seed: int = 0) -> dict:
    """Null (a): |cos(Δh̄, random unit vector)| distribution matched in
    d_model. Analytic: cos ~ N(0, 1/d), so sd ≈ 1/√d -- reported alongside
    the simulated band (95% two-sided)."""
    d = delta_h_vec.shape[0]
    rng = np.random.default_rng(seed)
    dirs = rng.standard_normal((n, d))
    dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
    dh = delta_h_vec / (np.linalg.norm(delta_h_vec) + 1e-12)
    cosines = dirs @ dh
    lo, hi = np.percentile(cosines, [2.5, 97.5])
    return {"null_sd": float(np.std(cosines)), "analytic_sd": float(1.0 / np.sqrt(d)),
            "null_lo": float(lo), "null_hi": float(hi), "abs_hi": float(np.percentile(np.abs(cosines), 95))}


def permuted_label_null(
    dataset,
    spec,
    split,
    layer: int,
    delta_h_vec: np.ndarray,
    *,
    n_perm: int = 50,
    seed: int = 0,
    residualized: bool = True,
) -> dict:
    """Null (b): probe directions trained on LABEL-PERMUTED data through the
    SAME pipeline as the observed statistic, cos(Δh̄, permuted direction). A
    stronger null than random vectors -- it preserves the residual-stream
    feature geometry a real probe exploits, only breaking the label
    correspondence.

    Crucially it mirrors the observed probe's pipeline: when the observed
    direction is the RESIDUALIZED probe (``residualized=True``, the RQ2/RQ4
    default), each permutation permutes the target, RE-RESIDUALIZES the
    permuted target on the (unpermuted, train-imputed) confounds, and refits
    the ridge probe -- so the null carries the residualization step it is
    meant to be a null for. ``residualized=False`` fits the raw probe (kind
    per the construct). Returns the |cos| band over ``n_perm`` permutations."""
    from knobe.mech._data import confound_frame, subset_mask, target_vector
    from knobe.mech.probes import fit_probe, fit_residualizer

    items = dataset.items
    mask = subset_mask(items, spec)
    sub = items.loc[mask].reset_index(drop=True)
    row_idx = np.where(mask)[0]
    is_train = sub["family_id"].isin(set(split.train)).to_numpy()
    X = dataset.X(layer)[row_idx][is_train]
    y_full = target_vector(sub, spec)
    if residualized:
        confounds, cols = confound_frame(sub, spec, train_mask=is_train)
        confounds_tr = confounds[is_train]
        recipe = f"{spec.target_col} ~ " + (" + ".join(cols) if cols else "1")
    y = y_full[is_train]

    rng = np.random.default_rng(seed)
    cosines = []
    for _ in range(n_perm):
        yp = rng.permutation(y)
        if residualized:
            # Re-residualize the PERMUTED target on the (unpermuted) confounds,
            # exactly as the observed residualized probe was built, then refit
            # the ridge probe on the residual.
            rzr = fit_residualizer(yp, confounds_tr, recipe)
            yp_resid = rzr.transform(yp, confounds_tr)
            probe = fit_probe(X, yp_resid, "ridge", spec.construct, layer)
        else:
            probe = fit_probe(X, yp, spec.kind, spec.construct, layer)
        if probe is None:
            continue
        cosines.append(abs(_cos(delta_h_vec, probe.direction())))
    if not cosines:
        return {"null_abs_hi": float("nan"), "null_abs_med": float("nan")}
    return {"null_abs_hi": float(np.percentile(cosines, 95)), "null_abs_med": float(np.median(cosines))}


def rq4_alignment(
    delta_h_by_layer: dict[int, np.ndarray],
    directions_by_construct: dict[str, dict[int, np.ndarray]],
    *,
    exploratory: Sequence[str] = ("vividness_evocativeness",),
    random_null_n: int = 1000,
    seed: int = 0,
    dataset=None,
    specs_by_construct: dict | None = None,
    split=None,
    permuted_null_n: int = 0,
    residualized: bool = True,
) -> pd.DataFrame:
    """cos(Δh̄, probe direction) per construct per layer, against the two
    nulls (WO-7 RQ4). ``directions_by_construct`` maps a construct tag →
    {layer: unit direction}. The random-vector null is always computed; the
    permuted-label null is computed when a ``dataset``/``specs``/``split`` are
    supplied and ``permuted_null_n > 0`` -- and it MIRRORS the observed
    pipeline via ``residualized`` (default True, matching residualized probe
    directions). ``exploratory`` construct tags are flagged in the output."""
    rows = []
    for tag, dirs in directions_by_construct.items():
        base_construct = tag.split("::", 1)[0]
        is_expl = base_construct in set(exploratory)
        for layer, direction in dirs.items():
            if layer not in delta_h_by_layer:
                continue
            dh = delta_h_by_layer[layer]
            cos = _cos(dh, direction)
            rnull = random_unit_null(dh, n=random_null_n, seed=seed)
            row = {
                "construct": tag, "layer": int(layer), "cos": cos, "abs_cos": abs(cos),
                "random_null_abs_hi": rnull["abs_hi"], "random_null_sd": rnull["null_sd"],
                "analytic_sd": rnull["analytic_sd"],
                "aligned_vs_random": bool(abs(cos) > rnull["abs_hi"]),
                "exploratory": is_expl,
            }
            if permuted_null_n and dataset is not None and specs_by_construct and split is not None:
                spec = specs_by_construct.get(base_construct)
                if spec is not None:
                    pnull = permuted_label_null(
                        dataset, spec, split, layer, dh,
                        n_perm=permuted_null_n, seed=seed, residualized=residualized,
                    )
                    row["permuted_null_abs_hi"] = pnull.get("null_abs_hi", float("nan"))
                    row["aligned_vs_permuted"] = bool(abs(cos) > pnull.get("null_abs_hi", np.inf))
            rows.append(row)
    return pd.DataFrame(rows)


def plot_rq4(alignment: pd.DataFrame, out_path: Path) -> None:
    """|cos(Δh̄, probe direction)| vs layer per construct, with the random-
    vector null band shaded. Evocativeness is drawn dashed + labelled
    exploratory (DR §6.1)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(9, 5))
    for tag, sub in alignment.groupby("construct"):
        sub = sub.sort_values("layer")
        expl = bool(sub["exploratory"].iloc[0])
        ax.plot(sub["layer"], sub["abs_cos"], marker="o", ls="--" if expl else "-",
                label=f"{tag}{' [exploratory]' if expl else ''}")
    if len(alignment):
        band = alignment.groupby("layer")["random_null_abs_hi"].mean().sort_index()
        ax.fill_between(band.index, 0, band.values, color="grey", alpha=0.2, label="random-vector null (95%)")
    ax.set_xlabel("layer (residual-stream slice)")
    ax.set_ylabel("|cos(Δh̄, probe direction)|")
    ax.set_title("RQ4 patch-shift ↔ probe-direction alignment\n(evocativeness probe exploratory, DR §6.1)")
    ax.legend(fontsize=7, ncol=2)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Gemma Scope option (config-gated stub).
# ---------------------------------------------------------------------------


@dataclass
class FakeSAE:
    """A tiny random SPARSE dictionary standing in for a real Gemma Scope SAE
    (WO-7 §4). Encodes a residual vector to ``n_features`` activations via a
    fixed random decoder, keeping only the top ``k_active`` per item (the
    sparsity a real SAE enforces). Deterministic in ``seed`` -- so the
    report plumbing (top-k features by |Δact|) is testable offline without
    downloading a 16k-feature SAE."""

    d_model: int
    n_features: int = 64
    k_active: int = 8
    seed: int = 0

    def __post_init__(self):
        rng = np.random.default_rng(self.seed)
        W = rng.standard_normal((self.n_features, self.d_model))
        self.W_enc = W / np.linalg.norm(W, axis=1, keepdims=True)

    def encode(self, resid: np.ndarray) -> np.ndarray:
        """``[n, d]`` → sparse ``[n, n_features]`` (ReLU + top-k per row)."""
        resid = np.atleast_2d(resid).astype(np.float64)
        acts = np.maximum(resid @ self.W_enc.T, 0.0)
        if self.k_active < self.n_features:
            for i in range(acts.shape[0]):
                thresh_idx = np.argsort(acts[i])[: -self.k_active]
                acts[i, thresh_idx] = 0.0
        return acts


def load_sae(name: str, d_model: int, *, seed: int = 0):
    """Config-gated SAE loader. ``name == "fake"`` → ``FakeSAE`` (offline,
    deterministic). Any real name (e.g. "gemma-scope") requires the guarded
    ``sae_lens`` import and is gpu-marked; the wiring point is documented."""
    if name == "fake":
        return FakeSAE(d_model=d_model, seed=seed)
    try:  # pragma: no cover -- gpu-only real path
        import sae_lens  # noqa: F401
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "sae_lens is required for a real SAE -- install the 'sae' extra "
            "(`uv pip install -e '.[sae]'`). Use name='fake' for offline plumbing tests."
        ) from exc
    raise NotImplementedError(  # pragma: no cover -- gpu-only; wired by the @pytest.mark.gpu test
        f"Real SAE loading for {name!r} runs only on the H200 (gpu-marked). Load the pretrained "
        "Gemma Scope SAE at the matched layer via sae_lens.SAE.from_pretrained here."
    )


def top_k_delta_features(unpatched_resid: np.ndarray, patched_resid: np.ndarray, sae, k: int = 10) -> pd.DataFrame:
    """Top-k SAE features by mean |Δ activation| between patched and unpatched
    residuals (WO-7 §4, descriptive). Columns: feature_id, mean_delta,
    mean_abs_delta, label (Neuronpedia stub → None)."""
    fu = sae.encode(unpatched_resid).mean(axis=0)
    fp = sae.encode(patched_resid).mean(axis=0)
    delta = fp - fu
    order = np.argsort(np.abs(delta))[::-1][:k]
    labels = neuronpedia_labels([int(i) for i in order])
    return pd.DataFrame(
        {
            "feature_id": [int(i) for i in order],
            "mean_delta": [float(delta[i]) for i in order],
            "mean_abs_delta": [float(abs(delta[i])) for i in order],
            "label": [labels[int(i)] for i in order],
        }
    )


def neuronpedia_labels(feature_ids: Sequence[int]) -> dict[int, str | None]:
    """Neuronpedia feature-label interface (stub). Returns every feature id
    UNLABELED (None) -- the real integration would query Neuronpedia's API for
    the matched SAE release; documented as a secondary, descriptive upgrade
    that needs network access not assumed in this environment."""
    return {int(fid): None for fid in feature_ids}


# ---------------------------------------------------------------------------
# Report emission (markdown summary).
# ---------------------------------------------------------------------------


def write_markdown_summary(
    out_path: Path,
    *,
    model_key: str,
    rq3: dict | None,
    rq3_table: pd.DataFrame | None,
    rq4: pd.DataFrame | None,
) -> None:
    """A human-readable ``mech_report`` summary listing the per-construct RQ3/
    RQ4 verdicts."""
    lines = [f"# Mechanistic decomposition report — {model_key}", ""]
    lines.append("## RQ3 — patch decomposition (selective vs uniform suppression)")
    if rq3 is not None:
        verdict = "SELECTIVE" if rq3.get("selective") else "uniform / not selective"
        lines.append(
            f"- config × component interaction: p = {rq3.get('interaction_p'):.4g} "
            f"(LR={rq3.get('lr_stat'):.3g}, df={rq3.get('df_diff')}, "
            f"n_groups={rq3.get('n_groups')}{', OLS fallback' if rq3.get('fallback_used') else ''}) → **{verdict}**"
        )
        if rq3_table is not None and len(rq3_table):
            lines.append("")
            lines.append("Per-component baseline-normalized gap (mean over patched configs):")
            agg = rq3_table.groupby("component")["normalized"].mean()
            for comp in COMPONENTS:
                if comp in agg.index:
                    lines.append(f"  - {comp}: {agg[comp]:.3f}")
    else:
        lines.append("- (no patch metrics supplied)")
    lines.append("")
    lines.append("## RQ4 — patch-shift ↔ probe-direction alignment")
    lines.append("_Evocativeness probe is exploratory (DR §6.1)._")
    if rq4 is not None and len(rq4):
        for tag, sub in rq4.groupby("construct"):
            best = sub.loc[sub["abs_cos"].idxmax()]
            aligned = "ALIGNED" if best.get("aligned_vs_random") else "within null band"
            expl = " [exploratory]" if bool(best.get("exploratory")) else ""
            lines.append(
                f"- {tag}{expl}: peak |cos| = {best['abs_cos']:.3f} at layer "
                f"{int(best['layer'])} (random null 95% = {best['random_null_abs_hi']:.3f}) → **{aligned}**"
            )
    else:
        lines.append("- (no alignment computed)")
    lines.append("")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Orchestration (CLI entry point).
# ---------------------------------------------------------------------------


def run_decompose(
    *,
    release: str,
    model_key: str,
    patch_metrics_path: str | Path | None = None,
    out_root: str | Path = "results",
) -> int:
    """RQ3 report from a patch_metrics.parquet: the normalized decomposition
    table + figure + (if enough scaffolds are recoverable) the suppression
    model verdict. RQ4 alignment requires a live backend + fit probes and is
    driven by ``rq4_alignment``/``mean_delta_h`` from the caller or the
    gpu-marked pipeline; this CLI entry point emits the RQ3 artifacts and a
    markdown summary so the report plumbing is exercised offline."""
    report_dir = Path(out_root) / release / "mech_report"
    report_dir.mkdir(parents=True, exist_ok=True)

    rq3_table = None
    if patch_metrics_path is not None:
        patch_metrics = pd.read_parquet(patch_metrics_path)
        rq3_table = rq3_normalized_table(patch_metrics)
        rq3_table.to_parquet(report_dir / "rq3_decomposition.parquet")
        if len(rq3_table):
            plot_rq3(rq3_table, report_dir / "rq3_decomposition.png")
        print(f"[mech decompose] RQ3 decomposition table + figure → {report_dir}", file=sys.stderr)
    else:
        print("[mech decompose] no --patch-metrics supplied; RQ3 skipped.", file=sys.stderr)

    write_markdown_summary(
        report_dir / "decompose_summary.md",
        model_key=model_key, rq3=None, rq3_table=rq3_table, rq4=None,
    )
    return 0
