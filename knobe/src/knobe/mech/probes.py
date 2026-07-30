"""S7a: per-layer linear probes on cached residuals + RQ2 localization
(master spec §3.9; WO-7).

Trains, for each construct (§3.9) at each residual-stream layer, a linear
probe on the final-token residual cache, under two hard controls the
science depends on (PLAN §8):

  * **Leakage control (split by scaffold).** The 5 valence families of a set
    share agent/goal/actions, so they must never straddle a train/test
    split. ``build_family_split`` assigns WHOLE scaffolds (see
    ``_data.scaffold_key``), stratified by domain, and hard-errors if the
    vignettes' scaffold grouping is internally inconsistent (a shuffled
    dataset where storylines span set numbers -- the leakage acceptance
    test).
  * **Confound control (residualization).** Constructs correlate across
    items, so every probe is ALSO fit in a residualized form: the target is
    residualized on the OTHER constructs' item-level values (OLS, fit on
    train, applied to test), and the probe is trained to predict that
    residual. RQ2 dissociation claims are made on the residualized probes;
    the raw curves are descriptive only. The recipe string is recorded in
    each ProbeRecord.

Everything here is GPU-free (numpy + sklearn over the cached residuals) and
never imports transformer_lens/nnsight (spec §5.1).
"""
from __future__ import annotations

import json
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd

from knobe.mech._data import (
    ConstructSpec,
    ProbeDataset,
    all_specs,
    confound_frame,
    load_probe_dataset,
    recipe_string,
    subset_mask,
    target_vector,
)
from knobe.schemas import FamilySplit, ProbeRecord

# Fixed-template anchor separating the agent from the rest of sentence 2
# (constants.SCENARIO_TEMPLATE: "... {agent} did not care ... {agent} knew
# ..."). Used to recover the shared agent from an assembled scenario.
_CARE_ANCHOR = "did not care"


class ScaffoldLeakageError(ValueError):
    """Raised by ``build_family_split`` when the vignettes' scaffold grouping
    is internally inconsistent -- families claiming the same (domain, set)
    scaffold do not actually share a storyline stem (WO-7 leakage rule). A
    split built over such data could leak agent/goal/action structure across
    train/test, so it is a hard error, never a silent mis-split."""


# ---------------------------------------------------------------------------
# Split builder (leakage control).
# ---------------------------------------------------------------------------


def _sentence1(scenario: str) -> str:
    """The scenario's first sentence = ``{agent} {action} to {goal}.`` (the
    scaffold-defining slots), everything before the first ``". "``."""
    return scenario.split(". ", 1)[0].strip()


def _agent_of(scenario: str) -> str | None:
    """The shared agent recovered from sentence 2 (``{agent} did not care
    ...``); None if the fixed-template anchor is absent (then the agent-level
    cross-check is skipped for that scaffold)."""
    parts = scenario.split(". ", 1)
    if len(parts) < 2 or _CARE_ANCHOR not in parts[1]:
        return None
    return parts[1].split(_CARE_ANCHOR, 1)[0].strip()


def validate_scaffold_consistency(items: pd.DataFrame) -> None:
    """Structural hard-check of the scaffold grouping before splitting (WO-7
    leakage rule). A scaffold's 5 valence families share agent/goal/actions
    (GS: one storyline per set), so from the assembled ``scenario`` alone:

      1. **Within each same-typicality subgroup** of a scaffold, sentence 1
         (``{agent} {action} to {goal}.``) must be IDENTICAL across the
         families -- ``action`` differs by typicality but is shared within a
         typicality, and agent+goal are shared outright. Affected-entity /
         outcome differences (legitimate valence-driven variation) live in
         later sentences and are deliberately not checked.
      2. **Across the whole scaffold**, the agent must be identical (recovered
         via the fixed "did not care" template anchor).
      3. **Across scaffolds**, no two (domain, set) keys may carry the same
         storyline (identical sentence-1 set) -- one storyline split across
         set numbers.

    Any violation is a hard ``ScaffoldLeakageError`` -- the fingerprint of
    family ids shuffled across sets. Requires ``items`` to carry
    ``scaffold``, ``typicality``, ``scenario``."""
    for scaffold, grp in items.groupby("scaffold"):
        for typ, tg in grp.groupby("typicality"):
            s1 = {_sentence1(s) for s in tg["scenario"]}
            if len(s1) > 1:
                raise ScaffoldLeakageError(
                    f"scaffold {scaffold!r}, typicality {typ!r}: families disagree on the "
                    f"shared scaffold slots (sentence 1 = agent/action/goal): {sorted(s1)!r}. "
                    f"Families sharing a scaffold must share agent/goal/actions -- this looks "
                    f"like family ids shuffled across sets (WO-7 leakage control)."
                )
        agents = {a for a in (_agent_of(s) for s in grp["scenario"]) if a is not None}
        if len(agents) > 1:
            raise ScaffoldLeakageError(
                f"scaffold {scaffold!r}: families disagree on the shared agent {sorted(agents)!r} "
                f"(WO-7 leakage control -- a scaffold is one storyline with one agent)."
            )

    seen: dict[frozenset, str] = {}
    for scaffold, grp in items.groupby("scaffold"):
        sig = frozenset(_sentence1(s) for s in grp["scenario"])
        if sig in seen and seen[sig] != scaffold:
            raise ScaffoldLeakageError(
                f"scaffolds {seen[sig]!r} and {scaffold!r} carry the same storyline "
                f"(identical agent/action/goal) -- one storyline appears under two "
                f"(domain, set) keys (WO-7 leakage control)."
            )
        seen[sig] = scaffold


def build_family_split(
    vignettes,
    test_frac: float = 0.25,
    seed: int = 0,
    *,
    validate: bool = True,
) -> FamilySplit:
    """Assign whole scaffolds to train/test, stratified by domain, recording
    the member family_ids in each split (spec §3.9 FamilySplit).

    ``vignettes`` may be a sequence of ``VignetteRow`` or a DataFrame with
    at least ``variant_id/family_id/domain/scenario`` columns. Grouping is by
    scaffold (``_data.scaffold_key``) so no set straddles the split;
    stratification puts ~``test_frac`` of EACH domain's scaffolds in test.
    Deterministic in ``seed``. With ``validate`` (default) the scaffold
    grouping is consistency-checked first -- a shuffled dataset raises
    ``ScaffoldLeakageError``."""
    items = _vignettes_frame(vignettes)
    if validate:
        validate_scaffold_consistency(items)

    scaffold_domain = items.drop_duplicates("scaffold").set_index("scaffold")["domain"].to_dict()
    scaffold_to_families = (
        items.groupby("scaffold")["family_id"].agg(lambda s: sorted(set(s))).to_dict()
    )
    rng = np.random.default_rng(seed)
    train_scaffolds: list[str] = []
    test_scaffolds: list[str] = []
    for domain in sorted(set(scaffold_domain.values())):
        scaffolds = sorted(s for s, d in scaffold_domain.items() if d == domain)
        rng.shuffle(scaffolds)
        n_test = int(round(test_frac * len(scaffolds)))
        # Guarantee at least one train scaffold per domain when possible.
        n_test = min(n_test, max(0, len(scaffolds) - 1)) if len(scaffolds) > 1 else 0
        test_scaffolds += scaffolds[:n_test]
        train_scaffolds += scaffolds[n_test:]

    train_families = sorted(f for s in train_scaffolds for f in scaffold_to_families[s])
    test_families = sorted(f for s in test_scaffolds for f in scaffold_to_families[s])
    return FamilySplit(train=train_families, test=test_families)


def _vignettes_frame(vignettes) -> pd.DataFrame:
    """Normalize ``vignettes`` (VignetteRow sequence or DataFrame) to a frame
    with variant_id/family_id/domain/scenario/typicality/scaffold columns."""
    from knobe.mech._data import scaffold_key

    if isinstance(vignettes, pd.DataFrame):
        df = vignettes.copy()
    else:
        df = pd.DataFrame(
            [
                {
                    "variant_id": v.variant_id,
                    "family_id": v.family_id,
                    "domain": v.domain,
                    "scenario": v.scenario,
                    "typicality": v.typicality,
                }
                for v in vignettes
            ]
        )
    if "scaffold" not in df.columns:
        df["scaffold"] = df["family_id"].map(scaffold_key)
    return df


# ---------------------------------------------------------------------------
# Probe fitting.
# ---------------------------------------------------------------------------


@dataclass
class FittedProbe:
    """A fit linear probe + its standardizer, kept in a form where the
    read-out DIRECTION in the ORIGINAL residual space (``direction``) is
    recoverable for RQ4 alignment (cos with Δh, which lives in that space)."""

    construct: str
    layer: int
    kind: str
    coef: np.ndarray  # in standardized feature space
    intercept: float
    mean: np.ndarray
    scale: np.ndarray

    def direction(self) -> np.ndarray:
        d = self.coef / self.scale
        n = np.linalg.norm(d)
        return d / n if n > 0 else d

    def decision(self, X: np.ndarray) -> np.ndarray:
        Xs = (X - self.mean) / self.scale
        return Xs @ self.coef + self.intercept


def _standardize(X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mean = X.mean(axis=0)
    scale = X.std(axis=0)
    scale = np.where(scale > 1e-8, scale, 1.0)
    return mean, scale


def fit_probe(X: np.ndarray, y: np.ndarray, kind: str, construct: str, layer: int) -> FittedProbe | None:
    """Fit one probe. classification → logistic, ridge → linear ridge, both
    on standardized features. Returns None when the target is degenerate
    (one class, or zero variance) -- the caller skips that (construct, layer)."""
    try:
        from sklearn.linear_model import LogisticRegression, Ridge
    except ImportError as exc:  # pragma: no cover -- exercised only without the extra
        raise RuntimeError(
            "scikit-learn is required for mech probes -- install the 'mech' or 'stats' "
            "extra (`uv pip install -e '.[mech]'`)."
        ) from exc

    mean, scale = _standardize(X)
    Xs = (X - mean) / scale
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # sklearn ConvergenceWarning on tiny data
        if kind == "classification":
            if len(np.unique(y)) < 2:
                return None
            clf = LogisticRegression(max_iter=2000, C=1.0)
            clf.fit(Xs, y)
            coef, intercept = clf.coef_[0].astype(float), float(clf.intercept_[0])
        else:
            if np.std(y) < 1e-9:
                return None
            reg = Ridge(alpha=1.0)
            reg.fit(Xs, y)
            coef, intercept = reg.coef_.astype(float), float(reg.intercept_)
    return FittedProbe(construct, layer, kind, coef, intercept, mean, scale)


def score_probe(probe: FittedProbe, X: np.ndarray, y: np.ndarray) -> float:
    """Test score: accuracy for classification, R² for ridge."""
    pred = probe.decision(X)
    if probe.kind == "classification":
        return float(np.mean((pred > 0).astype(int) == y))
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot > 1e-12 else 0.0


# ---------------------------------------------------------------------------
# Residualization (confound control).
# ---------------------------------------------------------------------------


@dataclass
class Residualizer:
    """OLS residualizer fit on TRAIN (target ~ 1 + confounds), applied to any
    split -- so the residualized target on test never sees test confounds
    (no leakage)."""

    beta: np.ndarray  # [1 + k]
    recipe: str

    def transform(self, target: np.ndarray, confounds: np.ndarray) -> np.ndarray:
        A = np.column_stack([np.ones(len(target)), confounds]) if confounds.shape[1] else np.ones((len(target), 1))
        return target - A @ self.beta


def fit_residualizer(target: np.ndarray, confounds: np.ndarray, recipe: str) -> Residualizer:
    A = np.column_stack([np.ones(len(target)), confounds]) if confounds.shape[1] else np.ones((len(target), 1))
    beta, *_ = np.linalg.lstsq(A, target, rcond=None)
    return Residualizer(beta=beta, recipe=recipe)


def _partial_corr(pred: np.ndarray, resid_target: np.ndarray) -> float:
    """Partial correlation of probe prediction and target given the confounds
    = plain corr of the probe prediction with the residualized target (the
    prediction is already a function of the residual-stream, the confound
    linear part having been removed from the target)."""
    if np.std(pred) < 1e-12 or np.std(resid_target) < 1e-12:
        return 0.0
    return float(np.corrcoef(pred, resid_target)[0, 1])


# ---------------------------------------------------------------------------
# Per-construct localization curve (raw + residualized), the RQ2 core.
# ---------------------------------------------------------------------------


@dataclass
class ConstructResult:
    spec: ConstructSpec
    target_kind: str
    curve: pd.DataFrame  # per-layer scores
    raw_probes: dict[int, FittedProbe]
    resid_probes: dict[int, FittedProbe]
    recipe: str
    split: FamilySplit
    n_train: int
    n_test: int


def _group_kfold_score(X, y, groups, kind, construct, n_splits) -> float:
    """Mean GroupKFold score over scaffold groups on the TRAIN set (cv_score
    for the ProbeRecord). Falls back to the train score if there are too few
    groups to fold."""
    try:
        from sklearn.model_selection import GroupKFold
    except ImportError as exc:  # pragma: no cover -- exercised only without the extra
        raise RuntimeError(
            "scikit-learn is required for mech probes -- install the 'mech' or 'stats' "
            "extra (`uv pip install -e '.[mech]'`)."
        ) from exc

    uniq = np.unique(groups)
    if len(uniq) < 2:
        probe = fit_probe(X, y, kind, construct, -1)
        return score_probe(probe, X, y) if probe else float("nan")
    k = int(min(n_splits, len(uniq)))
    scores = []
    for tr, te in GroupKFold(n_splits=k).split(X, y, groups):
        probe = fit_probe(X[tr], y[tr], kind, construct, -1)
        if probe is None:
            continue
        scores.append(score_probe(probe, X[te], y[te]))
    return float(np.mean(scores)) if scores else float("nan")


def construct_curve(
    dataset: ProbeDataset,
    spec: ConstructSpec,
    split: FamilySplit,
    *,
    cv_splits: int = 5,
    domain_generalization: bool = True,
) -> ConstructResult | None:
    """Fit raw + residualized probes for one construct at every layer and
    return the per-layer score curve. None if the construct has no usable
    labels (e.g. a behavioral construct with no results.jsonl)."""
    items = dataset.items
    mask = subset_mask(items, spec)
    if mask.sum() < 4:
        return None
    sub = items.loc[mask].reset_index(drop=True)
    row_idx = np.where(mask)[0]

    train_fams = set(split.train)
    test_fams = set(split.test)
    is_train = sub["family_id"].isin(train_fams).to_numpy()
    is_test = sub["family_id"].isin(test_fams).to_numpy()
    if is_train.sum() < 2 or is_test.sum() < 1:
        return None

    y = target_vector(sub, spec)
    confounds, confound_cols = confound_frame(sub, spec, train_mask=is_train)
    recipe = recipe_string(spec, confound_cols)
    groups_train = sub.loc[is_train, "scaffold"].to_numpy()

    # Residualizer fit on train only.
    resid_izer = fit_residualizer(y[is_train], confounds[is_train], recipe)
    y_resid = resid_izer.transform(y, confounds)

    rows = []
    raw_probes: dict[int, FittedProbe] = {}
    resid_probes: dict[int, FittedProbe] = {}
    for layer in dataset.layers:
        Xall = dataset.X(layer)[row_idx]
        Xtr, Xte = Xall[is_train], Xall[is_test]

        raw = fit_probe(Xtr, y[is_train], spec.kind, spec.construct, layer)
        raw_score = score_probe(raw, Xte, y[is_test]) if raw else float("nan")
        cv = (
            _group_kfold_score(Xtr, y[is_train], groups_train, spec.kind, spec.construct, cv_splits)
            if raw
            else float("nan")
        )
        if raw:
            raw_probes[layer] = raw

        resid = fit_probe(Xtr, y_resid[is_train], "ridge", spec.construct, layer)
        if resid:
            resid_probes[layer] = resid
            pred_te = resid.decision(Xte)
            resid_score = score_probe(resid, Xte, y_resid[is_test])
            pcorr = _partial_corr(pred_te, y_resid[is_test])
            resid_cv = _group_kfold_score(
                Xtr, y_resid[is_train], groups_train, "ridge", spec.construct, cv_splits
            )
        else:
            resid_score, pcorr, resid_cv = float("nan"), float("nan"), float("nan")

        loo = (
            _loo_domain_score(dataset, spec, row_idx, Xall, y, layer)
            if domain_generalization
            else float("nan")
        )

        rows.append(
            {
                "model_key": dataset.model_key,
                "construct": spec.construct,
                "target_kind": spec.target_kind,
                "kind": spec.kind,
                "layer": int(layer),
                "raw_score": raw_score,
                "cv_score": cv,
                "resid_cv_score": resid_cv,
                "resid_score": resid_score,
                "partial_corr": pcorr,
                "loo_domain_score": loo,
                "n_train": int(is_train.sum()),
                "n_test": int(is_test.sum()),
                "exploratory": spec.exploratory,
            }
        )

    curve = pd.DataFrame(rows)
    return ConstructResult(
        spec=spec,
        target_kind=spec.target_kind,
        curve=curve,
        raw_probes=raw_probes,
        resid_probes=resid_probes,
        recipe=recipe,
        split=split,
        n_train=int(is_train.sum()),
        n_test=int(is_test.sum()),
    )


def _loo_domain_score(dataset, spec, row_idx, Xall, y, layer) -> float:
    """Leave-one-domain-out generalization (secondary metric, WO-7 §2): mean
    test score training on all-but-one domain, over domains. NaN with <2
    domains."""
    domains = dataset.items.loc[row_idx, "domain"].to_numpy()
    uniq = np.unique(domains)
    if len(uniq) < 2:
        return float("nan")
    scores = []
    for held in uniq:
        tr = domains != held
        te = domains == held
        if spec.kind == "classification" and len(np.unique(y[tr])) < 2:
            continue
        probe = fit_probe(Xall[tr], y[tr], spec.kind, spec.construct, layer)
        if probe is None or te.sum() == 0:
            continue
        scores.append(score_probe(probe, Xall[te], y[te]))
    return float(np.mean(scores)) if scores else float("nan")


# ---------------------------------------------------------------------------
# RQ2: bootstrap CIs, peak-layer dissociation, subspace overlap.
# ---------------------------------------------------------------------------


def bootstrap_curve_ci(
    dataset: ProbeDataset,
    result: ConstructResult,
    *,
    n_boot: int = 200,
    seed: int = 0,
    metric: str = "resid_score",
) -> pd.DataFrame:
    """Per-layer bootstrap CI over TEST scaffold groups. We resample the test
    scaffolds (with replacement) and RE-EVALUATE the already-fit probes on
    the resampled test items -- fast, and it is the split-group uncertainty
    RQ2 curves report (documented choice; does not refit the probe). Uses the
    raw probe for classification/ridge raw metrics, the residualized probe
    for ``resid_score``/``partial_corr``."""
    items = dataset.items
    mask = subset_mask(items, result.spec)
    sub = items.loc[mask].reset_index(drop=True)
    row_idx = np.where(mask)[0]
    is_train = sub["family_id"].isin(set(result.split.train)).to_numpy()
    is_test = sub["family_id"].isin(set(result.split.test)).to_numpy()
    test_scaffolds = sub.loc[is_test, "scaffold"].to_numpy()
    uniq_scaffolds = np.unique(test_scaffolds)

    y = target_vector(sub, result.spec)
    confounds, confound_cols = confound_frame(sub, result.spec, train_mask=is_train)
    resid_izer = fit_residualizer(y[is_train], confounds[is_train], result.recipe)
    y_resid = resid_izer.transform(y, confounds)

    rng = np.random.default_rng(seed)
    use_resid = metric in ("resid_score", "partial_corr")
    probes = result.resid_probes if use_resid else result.raw_probes
    target = y_resid if use_resid else y

    rows = []
    for layer in dataset.layers:
        probe = probes.get(layer)
        Xall = dataset.X(layer)[row_idx]
        boot_scores = []
        if probe is not None and len(uniq_scaffolds) > 0:
            for _ in range(n_boot):
                picked = rng.choice(uniq_scaffolds, size=len(uniq_scaffolds), replace=True)
                sel = np.concatenate([np.where(test_scaffolds == s)[0] for s in picked])
                test_rows = np.where(is_test)[0][sel]
                Xb, yb = Xall[test_rows], target[test_rows]
                if metric == "partial_corr":
                    boot_scores.append(_partial_corr(probe.decision(Xb), yb))
                else:
                    boot_scores.append(score_probe(probe, Xb, yb))
        if boot_scores:
            lo, mid, hi = np.percentile(boot_scores, [2.5, 50, 97.5])
        else:
            lo = mid = hi = float("nan")
        rows.append(
            {"construct": result.spec.construct, "target_kind": result.target_kind,
             "layer": int(layer), "metric": metric, "ci_lo": lo, "ci_med": mid, "ci_hi": hi}
        )
    return pd.DataFrame(rows)


def peak_layer(curve: pd.DataFrame, metric: str = "resid_score") -> int:
    """Layer of maximum ``metric`` on a construct curve (the localization
    peak). NaNs ignored."""
    sub = curve.dropna(subset=[metric])
    if sub.empty:
        return -1
    return int(sub.loc[sub[metric].idxmax(), "layer"])


def peak_layer_dissociation(
    dataset: ProbeDataset,
    results: Sequence[ConstructResult],
    *,
    metric: str = "resid_score",
    n_boot: int = 200,
    seed: int = 0,
) -> pd.DataFrame:
    """Bootstrap distribution of the peak-layer DIFFERENCE for every construct
    pair (RQ2 dissociation stat (a)). For each bootstrap resample of the test
    scaffolds we recompute each construct's per-layer score and its peak
    layer, then the signed peak-layer difference per pair. Reports the
    observed difference plus the bootstrap 95% interval and the fraction of
    resamples with a non-zero (dissociated) difference."""
    # Precompute per-construct bootstrap peak-layer draws.
    per_construct_peaks: dict[str, np.ndarray] = {}
    observed_peak: dict[str, int] = {}
    key = lambda r: f"{r.spec.construct}::{r.target_kind}"
    for r in results:
        observed_peak[key(r)] = peak_layer(r.curve, metric)
        per_construct_peaks[key(r)] = _bootstrap_peak_layers(
            dataset, r, metric=metric, n_boot=n_boot, seed=seed
        )

    rows = []
    keys = list(per_construct_peaks)
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            a, b = keys[i], keys[j]
            diff = per_construct_peaks[a] - per_construct_peaks[b]
            valid = diff[~np.isnan(diff)]
            if valid.size == 0:
                lo = hi = frac = float("nan")
            else:
                lo, hi = np.percentile(valid, [2.5, 97.5])
                frac = float(np.mean(valid != 0))
            rows.append(
                {
                    "construct_a": a, "construct_b": b, "metric": metric,
                    "observed_peak_a": observed_peak[a], "observed_peak_b": observed_peak[b],
                    "observed_diff": observed_peak[a] - observed_peak[b],
                    "boot_diff_lo": lo, "boot_diff_hi": hi, "frac_dissociated": frac,
                }
            )
    return pd.DataFrame(rows)


def _bootstrap_peak_layers(dataset, result, *, metric, n_boot, seed) -> np.ndarray:
    """Bootstrap draws of a construct's peak layer (resample test scaffolds,
    re-evaluate the fit probes per layer, take argmax)."""
    items = dataset.items
    mask = subset_mask(items, result.spec)
    sub = items.loc[mask].reset_index(drop=True)
    row_idx = np.where(mask)[0]
    is_test = sub["family_id"].isin(set(result.split.test)).to_numpy()
    test_scaffolds = sub.loc[is_test, "scaffold"].to_numpy()
    uniq = np.unique(test_scaffolds)
    y = target_vector(sub, result.spec)
    is_train = sub["family_id"].isin(set(result.split.train)).to_numpy()
    confounds, _ = confound_frame(sub, result.spec, train_mask=is_train)
    resid_izer = fit_residualizer(y[is_train], confounds[is_train], result.recipe)
    y_resid = resid_izer.transform(y, confounds)
    use_resid = metric in ("resid_score", "partial_corr")
    probes = result.resid_probes if use_resid else result.raw_probes
    target = y_resid if use_resid else y

    layers = dataset.layers
    Xlayers = {l: dataset.X(l)[row_idx] for l in layers}
    rng = np.random.default_rng(seed + 1)
    peaks = np.full(n_boot, np.nan)
    test_pos = np.where(is_test)[0]
    for b in range(n_boot):
        if uniq.size == 0:
            break
        picked = rng.choice(uniq, size=uniq.size, replace=True)
        sel = np.concatenate([np.where(test_scaffolds == s)[0] for s in picked])
        rows_sel = test_pos[sel]
        scores = []
        for l in layers:
            probe = probes.get(l)
            if probe is None:
                scores.append(np.nan)
                continue
            Xb, yb = Xlayers[l][rows_sel], target[rows_sel]
            if metric == "partial_corr":
                scores.append(_partial_corr(probe.decision(Xb), yb))
            else:
                scores.append(score_probe(probe, Xb, yb))
        scores = np.array(scores)
        if np.all(np.isnan(scores)):
            continue
        peaks[b] = layers[int(np.nanargmax(scores))]
    return peaks


def subspace_overlap(
    results: Sequence[ConstructResult],
    *,
    top_k: int = 3,
    residualized: bool = True,
) -> pd.DataFrame:
    """Principal angles between construct probe-weight SPANS across layers
    (RQ2 dissociation stat (b)). For each construct we stack its probe
    DIRECTIONS at its top-k layers (by the residualized score) into a
    subspace, then report, per construct pair, the principal angles between
    the two subspaces (``min_cos`` = cos of the smallest angle = max
    alignment; low ⇒ well-separated subspaces)."""
    from scipy.linalg import subspace_angles

    bases: dict[str, np.ndarray] = {}
    key = lambda r: f"{r.spec.construct}::{r.target_kind}"
    for r in results:
        metric = "resid_score" if residualized else "raw_score"
        probes = r.resid_probes if residualized else r.raw_probes
        ranked = r.curve.dropna(subset=[metric]).sort_values(metric, ascending=False)
        layers = [int(l) for l in ranked["layer"].tolist() if int(l) in probes][:top_k]
        if not layers:
            continue
        mat = np.stack([probes[l].direction() for l in layers], axis=0)  # [k, d]
        bases[key(r)] = mat

    rows = []
    keys = list(bases)
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            a, b = keys[i], keys[j]
            angles = subspace_angles(bases[a].T, bases[b].T)  # columns = basis vectors
            cosines = np.cos(angles)
            rows.append(
                {
                    "construct_a": a, "construct_b": b,
                    "min_angle_rad": float(np.min(angles)),
                    "max_angle_rad": float(np.max(angles)),
                    # top_cos = cos of the SMALLEST principal angle = strongest
                    # alignment between the two probe subspaces (low ⇒ well
                    # separated / dissociated).
                    "top_cos": float(np.max(cosines)),
                    "mean_cos": float(np.mean(cosines)),
                }
            )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Probe artifact persistence (spec §3.9).
# ---------------------------------------------------------------------------


def probes_dir(out_root: Path, release: str, model_key: str) -> Path:
    return Path(out_root) / release / "probes" / model_key


def save_construct_probes(result: ConstructResult, out_dir: Path) -> list[ProbeRecord]:
    """Write ``<construct>__layer<l>.json`` (ProbeRecord) + a sibling
    ``.npz`` of the raw + residualized weights for every layer (spec §3.9).
    The json stays light (cv_score, split, recipe, target_kind); the npz
    carries coef/intercept/mean/scale + both read-out directions (RQ4 reads
    the residualized direction)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    records: list[ProbeRecord] = []
    curve = result.curve.set_index("layer")
    tag = f"{result.spec.construct}__{result.target_kind}"
    for layer, raw in result.raw_probes.items():
        resid = result.resid_probes.get(layer)
        npz_name = f"{tag}__layer{layer}.npz"
        payload = {
            "raw_coef": raw.coef, "raw_intercept": np.array([raw.intercept]),
            "mean": raw.mean, "scale": raw.scale, "raw_direction": raw.direction(),
        }
        if resid is not None:
            payload.update(
                {
                    "resid_coef": resid.coef, "resid_intercept": np.array([resid.intercept]),
                    "resid_direction": resid.direction(),
                }
            )
        np.savez(out_dir / npz_name, **payload)
        cv = float(curve.loc[layer, "cv_score"]) if layer in curve.index else float("nan")
        rcv = float(curve.loc[layer, "resid_cv_score"]) if layer in curve.index else float("nan")
        record = ProbeRecord(
            model_key=str(result.curve["model_key"].iloc[0]),
            construct=result.spec.construct,
            layer=int(layer),
            weights_ref=npz_name,
            split=result.split,
            cv_score=cv if not np.isnan(cv) else 0.0,
            resid_cv_score=rcv if not np.isnan(rcv) else 0.0,
            residualization_recipe=result.recipe,
            target_kind=result.target_kind,
            residualized=False,
        )
        (out_dir / f"{tag}__layer{layer}.json").write_text(
            record.model_dump_json(indent=2) + "\n", encoding="utf-8"
        )
        records.append(record)
    return records


def load_probe_directions(out_dir: Path, construct: str, target_kind: str, *, residualized: bool = True) -> dict[int, np.ndarray]:
    """Read back the per-layer probe directions for a construct (RQ4). Returns
    {layer: unit direction in residual space}."""
    out_dir = Path(out_dir)
    tag = f"{construct}__{target_kind}"
    key = "resid_direction" if residualized else "raw_direction"
    directions: dict[int, np.ndarray] = {}
    for npz in sorted(out_dir.glob(f"{tag}__layer*.npz")):
        layer = int(npz.stem.split("layer")[-1])
        data = np.load(npz)
        if key in data:
            directions[layer] = data[key]
    return directions


# ---------------------------------------------------------------------------
# Figures.
# ---------------------------------------------------------------------------


def plot_localization_curves(curves: pd.DataFrame, out_path: Path, *, metric: str = "resid_score") -> None:
    """One line per construct: ``metric`` vs layer (RQ2 localization figure)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(9, 5))
    for (construct, tk), sub in curves.groupby(["construct", "target_kind"]):
        sub = sub.sort_values("layer")
        label = f"{construct} ({tk})"
        expl = sub["exploratory"].iloc[0] if "exploratory" in sub else False
        if expl:
            label += " [exploratory]"
        ax.plot(sub["layer"], sub[metric], marker="o", label=label)
    ax.set_xlabel("layer (residual-stream slice)")
    ax.set_ylabel(f"{metric} (residualized probe = RQ2 dissociation basis)")
    ax.set_title("RQ2 per-construct localization curves")
    ax.legend(fontsize=7, ncol=2)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Orchestration (CLI entry point).
# ---------------------------------------------------------------------------


def run_probes(
    *,
    release: str,
    model_key: str,
    acts_dir: str | Path,
    vignettes_path: str | Path,
    curated_path: str | Path | None = None,
    results_path: str | Path | None = None,
    out_root: str | Path = "results",
    test_frac: float = 0.25,
    seed: int = 0,
    n_boot: int = 200,
) -> int:
    """Fit every construct's probes, write the §3.9 probe artifacts, and emit
    the RQ2 report tables + figure to ``results/<release>/mech_report/``."""
    dataset = load_probe_dataset(acts_dir, vignettes_path, curated_path, results_path)
    pdir = probes_dir(out_root, release, model_key)

    specs = all_specs(include_behavioral=dataset.has_behavioral)
    if not dataset.has_behavioral:
        print("[mech probes] no results.jsonl behavioral means -- skipping blame/intentionality probes.", file=sys.stderr)

    # Build the split once, from the full vignette frame (so scaffold
    # consistency is validated over all items).
    split = build_family_split(dataset.items, test_frac=test_frac, seed=seed)

    results: list[ConstructResult] = []
    all_curves = []
    for spec in specs:
        # Skip a rating construct that has no labels at all.
        if spec.target_kind == "rating" and not dataset._rating_present.get(spec.target_col, False):
            print(f"[mech probes] construct {spec.construct}/{spec.target_kind}: no labels -- skipped.", file=sys.stderr)
            continue
        res = construct_curve(dataset, spec, split)
        if res is None:
            print(f"[mech probes] construct {spec.construct}/{spec.target_kind}: insufficient data -- skipped.", file=sys.stderr)
            continue
        results.append(res)
        all_curves.append(res.curve)
        save_construct_probes(res, pdir)

    if not results:
        print("[mech probes] no constructs could be fit -- nothing emitted.", file=sys.stderr)
        return 1

    report_dir = Path(out_root) / release / "mech_report"
    report_dir.mkdir(parents=True, exist_ok=True)

    curves = pd.concat(all_curves, ignore_index=True)
    curves.to_parquet(report_dir / "rq2_curves.parquet")

    ci_frames = [bootstrap_curve_ci(dataset, r, n_boot=n_boot, seed=seed) for r in results]
    pd.concat(ci_frames, ignore_index=True).to_parquet(report_dir / "rq2_curve_cis.parquet")

    dissociation = peak_layer_dissociation(dataset, results, n_boot=n_boot, seed=seed)
    dissociation.to_parquet(report_dir / "rq2_dissociation.parquet")

    overlap = subspace_overlap(results)
    if len(overlap):
        overlap.to_parquet(report_dir / "rq2_subspace.parquet")

    plot_localization_curves(curves, report_dir / "rq2_localization.png")

    print(
        f"[mech probes] {model_key}: fit {len(results)} construct probes over "
        f"{len(dataset.layers)} layers → {pdir} ; RQ2 report → {report_dir}",
        file=sys.stderr,
    )
    return 0
