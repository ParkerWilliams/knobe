"""S7 probe/decomposition data assembly (WO-7): the ONE join that
``probes.py`` and ``decompose.py`` share.

Assembles the per-variant analysis table for a checkpoint from the four
inputs the mech layer already ships:

  * ``acts/<model_key>/final_token_resid.safetensors`` (+ ``index.json``):
    residual stream ``[n_prompts, n_layers+1, d_model]`` fp16, one row per
    raw-format intentionality prompt (spec §3.7). The cache rows are the
    probe items (one per variant).
  * ``vignettes.csv`` (``VignetteRow``): the design factors -- valence,
    sign, typicality, evocativeness, domain, family_id (spec §3.2).
  * ``curated.csv`` (``CuratedRow``): the curation ratings -- severity,
    vividness, typicality_perception, moral_relevance (spec §3.3).
  * optional ``results.jsonl`` (``ResultRecord``): per-item behavioral
    means (intentionality, blame) from the raw-format S5 jobs (spec §3.6).
    Absent → the two behavioral-rating constructs are skipped gracefully.

Everything joins on ``variant_id`` (``prompt_id = variant_id::q::fmt``), so
the residual cache row order defines the item order for the whole pipeline.

This module never imports transformer_lens/nnsight (spec §5.1) and never
touches sklearn/statsmodels -- it is pure pandas/numpy assembly, so probes
and decompose can each stay lean.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd

from knobe.mech.cache_acts import read_cache
from knobe.schemas import (
    CuratedRow,
    ResultRecord,
    VignetteRow,
    read_csv_validated,
    read_jsonl,
)

# ---------------------------------------------------------------------------
# Scaffold key (leakage-control grouping unit). A "scaffold" is a
# (domain, set) storyline: ALL 5 valence families of a set (MB/MG/NMB/NMG/
# NEU) share the same agent/goal/actions, so they must never straddle a
# train/test split (WO-7 hard rule). The scaffold key is the family_id with
# its valence segment removed: "ENV-MB-01" and "ENV-MG-01" both → "ENV-01".
# ---------------------------------------------------------------------------

_FAMILY_ID_PARTS = re.compile(r"([A-Z]+)-(MB|MG|NMB|NMG|NEU)-(\d{2}(?:r\d+)?)")


def scaffold_key(family_id: str) -> str:
    """``family_id`` → its scaffold (domain, set) key, dropping the valence
    segment. ``"ENV-MB-01" → "ENV-01"``. Raises on a malformed family_id."""
    m = _FAMILY_ID_PARTS.fullmatch(family_id)
    if m is None:
        raise ValueError(f"family_id {family_id!r} does not parse as DOMAIN-VALENCE-SET")
    return f"{m.group(1)}-{m.group(3)}"


# ---------------------------------------------------------------------------
# Numeric construct encodings (used as probe targets AND as residualization
# confounds). Each design factor becomes a symmetric ±1 code; ratings stay
# on their 0-10 scale. NEU has no sign / no moral-vs-nonmoral contrast, so
# those codes are 0 there (and NEU rows are excluded from the sign /
# valence_moral probes -- see CONSTRUCT_SPECS).
# ---------------------------------------------------------------------------

_SIGN_NUM = {"bad": 1.0, "good": -1.0, "na": 0.0}


def _valence_moral_num(valence: str) -> float:
    if valence in ("MB", "MG"):
        return 1.0
    if valence in ("NMB", "NMG"):
        return -1.0
    return 0.0  # NEU


# ---------------------------------------------------------------------------
# Construct target specification (§3.9's 8 constructs). ``kind`` picks the
# raw-probe estimator (classification=logistic, ridge=linear); ``target_col``
# is the column in the assembled item table; ``target_kind`` is the additive
# ProbeRecord field distinguishing a discrete *condition* label from a
# continuous *rating*; ``exclude`` names the construct's OWN numeric columns
# (removed from the confound set when residualizing); ``subset`` filters
# which item rows the construct is defined on (e.g. NEU excluded from sign).
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ConstructSpec:
    construct: str
    kind: str  # "classification" | "ridge"
    target_kind: str  # "condition" | "rating"
    target_col: str
    # Columns removed from the confound set when residualizing this construct:
    # the construct's OWN numeric column(s), PLUS any downstream behavioral
    # MEDIATORS the researcher has ruled out (see the sign / valence_moral
    # specs -- DECISIONS_FOR_HUMANS.md item (a), resolved 2026-07-28).
    exclude: tuple[str, ...]
    subset: str  # "all" | "valenced" (excludes NEU) | "rated" (target non-null)
    needs_behavioral: bool = False
    exploratory: bool = False


# The full construct numeric columns available as confounds.
CONFOUND_COLS = (
    "sign_num",
    "valence_moral_num",
    "typicality_num",
    "evoc_num",
    "severity",
    "vividness",
    "typicality_perception",
    "blame_mean",
    "intentionality_mean",
)

# Behavioral means that are DOWNSTREAM consequences of the design factors --
# excluded from the residualization confound sets of ALL design-factor
# (condition) probes so we don't condition on a mediator: the component of a
# design factor's representation that correlates with the model's own
# blame/intentionality outputs is the causally efficacious part, not a
# confound (DECISIONS_FOR_HUMANS.md item (a), resolved by researcher
# directive 2026-07-28; extended to typicality_condition and
# vividness_evocativeness by researcher directive 2026-07-28). Curation
# ratings (severity, vividness, typicality_perception) remain in the confound
# sets -- their cross-item correlation is a stimulus-construction confound,
# which residualization is for.
_BEHAVIORAL_MEDIATORS = ("blame_mean", "intentionality_mean")

CONSTRUCT_SPECS: dict[str, ConstructSpec] = {
    "valence_moral": ConstructSpec(
        "valence_moral", "classification", "condition", "valence_moral_num",
        exclude=("valence_moral_num", *_BEHAVIORAL_MEDIATORS), subset="valenced",
    ),
    "sign": ConstructSpec(
        "sign", "classification", "condition", "sign_num",
        exclude=("sign_num", *_BEHAVIORAL_MEDIATORS), subset="valenced",
    ),
    "typicality_condition": ConstructSpec(
        "typicality_condition", "classification", "condition", "typicality_num",
        exclude=("typicality_num", *_BEHAVIORAL_MEDIATORS), subset="all",
    ),
    # §3.9 names ONE construct for the evocativeness axis. Both a
    # classification probe on the low/high evocativeness *condition* and a
    # ridge probe on the curated *vividness* rating are licensed; the two
    # are emitted under this same construct, distinguished by target_kind
    # (WO-7). "condition" is the primary; the rating variant is added in
    # build_targets. Its OWN columns (evoc_num, vividness) are both excluded
    # from either variant's confound set.
    "vividness_evocativeness": ConstructSpec(
        "vividness_evocativeness", "classification", "condition", "evoc_num",
        exclude=("evoc_num", "vividness", *_BEHAVIORAL_MEDIATORS),
        subset="all", exploratory=True,
    ),
    "severity": ConstructSpec(
        "severity", "ridge", "rating", "severity",
        exclude=("severity",), subset="rated",
    ),
    "typicality_perception": ConstructSpec(
        "typicality_perception", "ridge", "rating", "typicality_perception",
        exclude=("typicality_perception", "typicality_num"), subset="rated",
    ),
    "blame_rating": ConstructSpec(
        "blame_rating", "ridge", "rating", "blame_mean",
        exclude=("blame_mean",), subset="rated", needs_behavioral=True,
    ),
    "intentionality_rating": ConstructSpec(
        "intentionality_rating", "ridge", "rating", "intentionality_mean",
        exclude=("intentionality_mean",), subset="rated", needs_behavioral=True,
    ),
}

# The evocativeness ridge-on-vividness companion (same construct, target_kind
# "rating") -- built alongside the condition probe in build_targets.
_VIVIDNESS_RATING_SPEC = ConstructSpec(
    "vividness_evocativeness", "ridge", "rating", "vividness",
    exclude=("evoc_num", "vividness"), subset="rated", exploratory=True,
)


# ---------------------------------------------------------------------------
# The assembled dataset.
# ---------------------------------------------------------------------------


@dataclass
class ProbeDataset:
    """The per-variant analysis table + the residual cache, row-aligned.

    ``resid`` is ``[n_items, n_layers+1, d_model]`` (float32 here -- promoted
    from the fp16 on-disk cache for numerically-stable probe fitting).
    ``items`` is a DataFrame with one row per cache item carrying the design
    factors, scaffold key, and every construct's numeric column. ``layers``
    lists the slice index of each ``resid`` axis-1 column."""

    resid: np.ndarray
    items: pd.DataFrame
    layers: list[int]
    model_key: str
    has_behavioral: bool = False
    _rating_present: dict[str, bool] = field(default_factory=dict)

    @property
    def n_items(self) -> int:
        return self.resid.shape[0]

    @property
    def d_model(self) -> int:
        return self.resid.shape[2]

    def X(self, layer: int) -> np.ndarray:
        """Feature matrix ``[n_items, d_model]`` at ``layer`` (slice index)."""
        col = self.layers.index(layer)
        return self.resid[:, col, :]


def _behavioral_means(results: Sequence[ResultRecord]) -> pd.DataFrame:
    """Per-variant behavioral means from a raw-format results.jsonl: mean
    parsed_rating grouped by (variant_id, question_type). Only parse_ok rows
    with a numeric rating contribute. variant_id is recovered from prompt_id
    (``variant::question::format``); only ``format == raw`` rows are used."""
    rows = []
    for r in results:
        parts = r.prompt_id.split("::")
        if len(parts) != 3:
            continue
        variant_id, question_type, fmt = parts
        if fmt != "raw" or not r.parse_ok or r.parsed_rating is None:
            continue
        rows.append({"variant_id": variant_id, "question_type": question_type, "rating": float(r.parsed_rating)})
    if not rows:
        return pd.DataFrame(columns=["variant_id", "intentionality_mean", "blame_mean"])
    df = pd.DataFrame(rows)
    wide = df.groupby(["variant_id", "question_type"])["rating"].mean().unstack("question_type")
    out = pd.DataFrame({"variant_id": wide.index})
    out["intentionality_mean"] = wide["intentionality"].to_numpy() if "intentionality" in wide else np.nan
    out["blame_mean"] = wide["blame"].to_numpy() if "blame" in wide else np.nan
    return out.reset_index(drop=True)


def assemble_items(
    prompt_ids: Sequence[str],
    vignettes: Sequence[VignetteRow],
    curated: Sequence[CuratedRow] | None = None,
    results: Sequence[ResultRecord] | None = None,
) -> tuple[pd.DataFrame, bool, dict[str, bool]]:
    """Build the row-aligned item table for ``prompt_ids`` (cache order).

    Returns (items_df, has_behavioral, rating_present). ``rating_present``
    flags which rating columns (severity/vividness/typicality_perception/
    blame_mean/intentionality_mean) have at least one non-null value, so a
    construct with no labels at all is skipped rather than fit on nothing."""
    by_variant = {v.variant_id: v for v in vignettes}
    curated_by_variant = {c.variant_id: c for c in (curated or [])}
    behav = _behavioral_means(results or [])
    behav_by_variant = {row["variant_id"]: row for _, row in behav.iterrows()}
    has_behavioral = bool(len(behav))

    records = []
    for pid in prompt_ids:
        variant_id = pid.split("::", 1)[0]
        v = by_variant.get(variant_id)
        if v is None:
            raise ValueError(f"prompt_id {pid!r} → variant_id {variant_id!r} not in vignettes.csv")
        c = curated_by_variant.get(variant_id)
        b = behav_by_variant.get(variant_id)
        records.append(
            {
                "prompt_id": pid,
                "variant_id": variant_id,
                "family_id": v.family_id,
                "scaffold": scaffold_key(v.family_id),
                "scenario": v.scenario,
                "domain": v.domain,
                "valence": v.valence,
                "sign": v.sign,
                "typicality": v.typicality,
                "evocativeness": v.evocativeness,
                # Numeric construct encodings.
                "sign_num": _SIGN_NUM[v.sign],
                "valence_moral_num": _valence_moral_num(v.valence),
                "typicality_num": 1.0 if v.typicality == "uncommon" else -1.0,
                "evoc_num": 1.0 if v.evocativeness == "high" else -1.0,
                "severity": float(c.severity) if c and c.severity is not None else np.nan,
                "vividness": float(c.vividness) if c and c.vividness is not None else np.nan,
                "typicality_perception": (
                    float(c.typicality_perception) if c and c.typicality_perception is not None else np.nan
                ),
                "intentionality_mean": float(b["intentionality_mean"]) if b is not None else np.nan,
                "blame_mean": float(b["blame_mean"]) if b is not None else np.nan,
            }
        )
    items = pd.DataFrame.from_records(records)
    rating_present = {
        col: bool(items[col].notna().any())
        for col in ("severity", "vividness", "typicality_perception", "blame_mean", "intentionality_mean")
    }
    return items, has_behavioral, rating_present


def load_probe_dataset(
    acts_dir: str | Path,
    vignettes_path: str | Path,
    curated_path: str | Path | None = None,
    results_path: str | Path | None = None,
) -> ProbeDataset:
    """Assemble a ``ProbeDataset`` from an activation cache directory + the
    release tables. ``curated_path``/``results_path`` are optional; without
    curated ratings the ridge-on-rating constructs are unavailable, without
    results the two behavioral constructs are skipped (documented)."""
    resid, index = read_cache(Path(acts_dir))
    prompt_ids = index["prompt_ids"]
    model_key = index.get("model_key", "unknown")
    vignettes = read_csv_validated(vignettes_path, VignetteRow)
    curated = read_csv_validated(curated_path, CuratedRow) if curated_path else None
    results = read_jsonl(results_path, ResultRecord) if results_path else None
    items, has_behavioral, rating_present = assemble_items(prompt_ids, vignettes, curated, results)
    layers = list(index.get("layers") or range(resid.shape[1]))
    return ProbeDataset(
        resid=resid.astype(np.float32),
        items=items,
        layers=layers,
        model_key=model_key,
        has_behavioral=has_behavioral,
        _rating_present=rating_present,
    )


# ---------------------------------------------------------------------------
# Target/subset resolution (shared by probes.py).
# ---------------------------------------------------------------------------


def all_specs(include_behavioral: bool = True) -> list[ConstructSpec]:
    """Every construct target to fit, INCLUDING the vividness-rating
    companion of the evocativeness construct. ``include_behavioral`` gates
    the two results.jsonl-dependent constructs."""
    specs = list(CONSTRUCT_SPECS.values()) + [_VIVIDNESS_RATING_SPEC]
    if not include_behavioral:
        specs = [s for s in specs if not s.needs_behavioral]
    return specs


def subset_mask(items: pd.DataFrame, spec: ConstructSpec) -> np.ndarray:
    """Boolean row mask for the items a construct is defined on."""
    if spec.subset == "valenced":
        mask = items["valence"] != "NEU"
    else:
        mask = pd.Series(True, index=items.index)
    if spec.subset == "rated" or spec.target_kind == "rating":
        mask = mask & items[spec.target_col].notna()
    return mask.to_numpy()


def target_vector(items: pd.DataFrame, spec: ConstructSpec) -> np.ndarray:
    """The raw probe target for a construct's in-subset rows. Classification
    targets are mapped to {0,1}; ridge targets stay on their native scale."""
    col = items[spec.target_col].to_numpy(dtype=float)
    if spec.kind == "classification":
        return (col > 0).astype(int)
    return col


def confound_frame(
    items: pd.DataFrame, spec: ConstructSpec, train_mask: np.ndarray | None = None
) -> tuple[np.ndarray, list[str]]:
    """The residualization design matrix: every construct numeric column
    EXCEPT the construct's own (``spec.exclude``), keeping only columns that
    have at least one non-null value in ``items``. Missing values are
    mean-imputed so a partially-rated confound still contributes; the
    imputation mean is computed from ``train_mask`` rows ONLY (test rows get
    the train mean -- no test-set leakage into the design matrix). With
    ``train_mask=None`` the mean is over all rows (used only where no split is
    in play). Returns (matrix ``[n, k]``, column-name list) -- the names feed
    the recipe string."""
    cols = [c for c in CONFOUND_COLS if c not in spec.exclude and items[c].notna().any()]
    if not cols:
        return np.zeros((len(items), 0)), []
    mat = np.array(items[cols].to_numpy(dtype=float), copy=True)
    impute_src = mat if train_mask is None else mat[train_mask]
    with np.errstate(invalid="ignore"):
        col_means = np.nanmean(impute_src, axis=0) if len(impute_src) else np.zeros(mat.shape[1])
    col_means = np.where(np.isnan(col_means), 0.0, col_means)  # a col all-NaN in train
    inds = np.where(np.isnan(mat))
    mat[inds] = np.take(col_means, inds[1])
    return mat, cols


def recipe_string(spec: ConstructSpec, confound_cols: Sequence[str]) -> str:
    """The residualization recipe recorded in the ProbeRecord, e.g.
    ``"severity ~ vividness + typicality_perception + sign_num + ..."``."""
    rhs = " + ".join(confound_cols) if confound_cols else "1"
    return f"{spec.target_col} ~ {rhs}"
