"""S6a: activation caching + per-layer δ_l contrasts (master spec §3.7, §5.3;
WO-6 Part B).

Orchestration only -- this module never imports transformer_lens/nnsight
(spec §5.1); it drives whatever ``ResidualAccess`` backend it is handed
(``mech/backend.py``), so the whole thing runs GPU-free under FakeBackend.

For every raw-format intentionality prompt in a release, it caches the
final-token residual stream at all layers (pre-block-0 … post-final-block)
→ ``results/<release>/acts/<model_key>/final_token_resid.safetensors`` (fp16,
tensor "resid") + ``index.json`` (row → prompt_id), then computes Raimondi's
δ_l (per-layer mean-activation contrast, bad vs good) plus the construct-
level extensions (moral vs nonmoral, typicality, evocativeness, NEU vs
valenced) → ``delta_l.parquet`` + a matplotlib line plot per model.

Item metadata (sign/valence/typicality/evocativeness) is joined in from
``vignettes.csv`` via prompt_id → variant_id, never stored in the cache.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd

from knobe.elicit_vllm import default_registry_path, resolve_model_id, shard_jobs
from knobe.mech.backend import BACKENDS, FakeBackend, ResidualAccess
from knobe.registry import Family, load_registry
from knobe.schemas import PromptRecord, VignetteRow, read_csv_validated, read_jsonl

try:
    from safetensors.numpy import load_file as _st_load
    from safetensors.numpy import save_file as _st_save
except ImportError:  # pragma: no cover -- exercised only without the safetensors dep
    _st_load = None
    _st_save = None

RESID_TENSOR_NAME = "resid"
CACHE_FILENAME = "final_token_resid.safetensors"
INDEX_FILENAME = "index.json"


# ---------------------------------------------------------------------------
# δ_l contrasts (spec §5.3 / WO-6 Part B.2). δ_l is the per-layer
# mean-difference-vector norm ‖mean(pos) − mean(neg)‖₂ (Raimondi). Contrasts
# fall in two families:
#
#   POOLED — the contrast IS the design factor, so a simple pooled
#   mean-difference is unconfounded by construction (the balanced factorial
#   makes the other factors cancel across the two pooled groups):
#     * bad_vs_good        (sign, pooled over moral+nonmoral: MB+NMB vs MG+NMG)
#     * moral_vs_nonmoral  (MB+MG vs NMB+NMG)
#     * neu_vs_valenced    (NEU vs the four valenced categories)
#
#   CONTROLLED — the contrast is a WITHIN-item factor that is NOT balanced
#   against sign in an arbitrary release subset, so a pooled mean-difference
#   would leak the sign (Knobe) signal whenever the two conditions have
#   different sign proportions. The factorial design licenses these only on
#   controlled subsets (spec §5.3), so they are computed that way:
#     * typicality (uncommon vs common) — WITHIN each sign, then averaged
#       over signs (mirrors patch.py's _within_sign_gap, but vector-valued
#       per layer). This removes the sign confound: if there is no true
#       within-sign typicality signal, δ ≈ 0 even under heavy sign imbalance.
#     * evocativeness (high vs low) — WITHIN each matched (family_id,
#       typicality) pair (the two variants that differ ONLY in evocativeness:
#       A/B and C/D), a per-pair high−low difference vector averaged over
#       complete pairs. Falls back to the within-sign estimator if no
#       complete pair exists (documented).
# ---------------------------------------------------------------------------


def _is_moral(valence: str) -> bool:
    return valence in ("MB", "MG")


def _is_nonmoral(valence: str) -> bool:
    return valence in ("NMB", "NMG")


# name -> (pos_predicate, neg_predicate) over a metadata dict row. POOLED
# contrasts only -- the controlled ones (typicality/evocativeness) are NOT
# simple pooled masks and are computed separately (see compute_delta_l).
POOLED_CONTRASTS = {
    "bad_vs_good": (lambda r: r["sign"] == "bad", lambda r: r["sign"] == "good"),
    "moral_vs_nonmoral": (lambda r: _is_moral(r["valence"]), lambda r: _is_nonmoral(r["valence"])),
    "neu_vs_valenced": (lambda r: r["valence"] == "NEU", lambda r: r["valence"] in ("MB", "MG", "NMB", "NMG")),
}

# Every contrast name compute_delta_l can emit (POOLED + the two controlled).
CONTRAST_NAMES = (*POOLED_CONTRASTS, "typicality", "evocativeness")


# ---------------------------------------------------------------------------
# Prompt selection (raw-format intentionality only) + shard/limit.
# ---------------------------------------------------------------------------


def select_prompts(
    records: Sequence[PromptRecord],
    limit: int | None = None,
    shard: tuple[int, int] | None = None,
) -> list[PromptRecord]:
    """The raw-format intentionality prompts of a release (spec §3.7's cache
    input), in file order, after ``--shard i/n`` (``idx % n == i``, disjoint
    + exhaustive, like elicit_vllm.shard_jobs) then ``--limit``."""
    selected = [r for r in records if r.question_type == "intentionality" and r.format == "raw"]
    selected = shard_jobs(selected, shard)  # idx % n == i partition (elicit_vllm)
    if limit is not None:
        selected = selected[:limit]
    return selected


# ---------------------------------------------------------------------------
# Cache read/write (safetensors round-trip + index integrity).
# ---------------------------------------------------------------------------


def write_cache(acts_resid: np.ndarray, prompt_ids: Sequence[str], out_dir: Path, meta: dict) -> None:
    """Writes ``final_token_resid.safetensors`` (fp16, tensor "resid") +
    ``index.json``. ``meta`` carries model_key/layers/positions/dims so the
    cache is self-describing on reload."""
    if _st_save is None:  # pragma: no cover
        raise RuntimeError("safetensors is required to write activation caches (install the 'mech'/'dev' extra).")
    out_dir.mkdir(parents=True, exist_ok=True)
    resid = np.ascontiguousarray(acts_resid.astype(np.float16))
    _st_save({RESID_TENSOR_NAME: resid}, str(out_dir / CACHE_FILENAME))
    index = {"prompt_ids": list(prompt_ids), **meta}
    (out_dir / INDEX_FILENAME).write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")


def read_cache(out_dir: Path) -> tuple[np.ndarray, dict]:
    """Inverse of ``write_cache``: returns (resid ``[n, n_slices, d_model]``
    fp16, index dict). Raises if the two files disagree on row count
    (integrity check)."""
    if _st_load is None:  # pragma: no cover
        raise RuntimeError("safetensors is required to read activation caches (install the 'mech'/'dev' extra).")
    resid = _st_load(str(out_dir / CACHE_FILENAME))[RESID_TENSOR_NAME]
    index = json.loads((out_dir / INDEX_FILENAME).read_text(encoding="utf-8"))
    if len(index["prompt_ids"]) != resid.shape[0]:
        raise ValueError(
            f"cache integrity: index.json has {len(index['prompt_ids'])} prompt_ids but "
            f"{CACHE_FILENAME} has {resid.shape[0]} rows in {out_dir}"
        )
    return resid, index


def cache_is_complete(out_dir: Path, expected_n: int) -> bool:
    """True iff both cache files exist and hold exactly ``expected_n`` rows
    -- the resume-skip predicate (spec §1 scheduler-agnostic rule)."""
    if not (out_dir / CACHE_FILENAME).exists() or not (out_dir / INDEX_FILENAME).exists():
        return False
    try:
        resid, index = read_cache(out_dir)
    except Exception:
        return False
    return resid.shape[0] == expected_n == len(index["prompt_ids"])


def cache_activations(
    backend: ResidualAccess,
    prompts: Sequence[PromptRecord],
    out_dir: Path,
    *,
    force: bool = False,
) -> np.ndarray:
    """Runs ``backend.run_with_cache`` over ``prompts`` (final token, all
    layers) and writes the cache. Resumes (skips the backend run) if a
    complete cache already exists and ``force`` is False; returns the
    residual array either way."""
    out_dir = Path(out_dir)
    if not force and cache_is_complete(out_dir, len(prompts)):
        print(f"[mech cache] {out_dir} already complete ({len(prompts)} rows) -- skipping.", file=sys.stderr)
        return read_cache(out_dir)[0]
    texts = [p.text for p in prompts]
    acts = backend.run_with_cache(texts, layers=None, positions="final")
    meta = {
        "model_key": backend.model_key,
        "layers": acts.layers,
        "positions": acts.positions,
        "n_layers": backend.n_layers,
        "d_model": backend.d_model,
    }
    write_cache(acts.resid, [p.prompt_id for p in prompts], out_dir, meta)
    return acts.resid


# ---------------------------------------------------------------------------
# Item-metadata join (prompt_id → variant_id → vignettes.csv).
# ---------------------------------------------------------------------------


def build_meta(prompt_ids: Sequence[str], vignettes: Sequence[VignetteRow]) -> list[dict]:
    """One metadata dict per prompt_id (row-aligned to the cache), joined
    from ``vignettes.csv`` on variant_id (prompt_id = ``variant::q::fmt``)."""
    by_variant = {v.variant_id: v for v in vignettes}
    meta = []
    for pid in prompt_ids:
        variant_id = pid.split("::", 1)[0]
        v = by_variant.get(variant_id)
        if v is None:
            raise ValueError(f"prompt_id {pid!r} → variant_id {variant_id!r} not found in vignettes.csv")
        meta.append(
            {
                "prompt_id": pid,
                "variant_id": variant_id,
                "family_id": v.family_id,  # matched-pair key for evocativeness δ_l
                "valence": v.valence,
                "sign": v.sign,
                "typicality": v.typicality,
                "evocativeness": v.evocativeness,
                "domain": v.domain,
                "nonmoral_subdomain": v.nonmoral_subdomain,
            }
        )
    return meta


# ---------------------------------------------------------------------------
# δ_l computation.
# ---------------------------------------------------------------------------


def compute_delta_l(resid: np.ndarray, meta: Sequence[dict], model_key: str, layers: Sequence[int]) -> pd.DataFrame:
    """δ_l per contrast per layer. ``resid`` is ``[n, n_slices, d_model]``;
    the contrast is taken over the PROMPT axis (mean of positive rows minus
    mean of negative rows, per slice), so ``delta`` is a per-layer scalar --
    computing it over any other axis would collapse the layer structure the
    δ_l analysis exists to expose.

    Columns: [model_key, contrast, layer, delta, delta_cos, n_pos, n_neg].
    ``delta`` = ‖diff‖₂ for the contrast's (possibly control-averaged)
    per-layer difference vector; ``delta_cos`` = cosine similarity of the
    pooled positive/negative group means (a cheap, scale-free companion
    effect size -- lower ⇒ more separated).

    POOLED contrasts use a plain group mean-difference. CONTROLLED contrasts
    (typicality, evocativeness) use the confound-removing estimators
    documented above POOLED_CONTRASTS -- so e.g. typicality δ_l does NOT
    collapse onto bad_vs_good when the release subset has sign-imbalanced
    typicality conditions.
    """
    resid = resid.astype(np.float64)
    rows: list[dict] = []

    for name, (pos_pred, neg_pred) in POOLED_CONTRASTS.items():
        pos_idx = [i for i, m in enumerate(meta) if pos_pred(m)]
        neg_idx = [i for i, m in enumerate(meta) if neg_pred(m)]
        if not pos_idx or not neg_idx:
            continue
        pos_mean, neg_mean = resid[pos_idx].mean(axis=0), resid[neg_idx].mean(axis=0)
        rows += _delta_rows(model_key, name, pos_mean - neg_mean, pos_mean, neg_mean,
                            len(pos_idx), len(neg_idx), layers)

    typ = _within_sign_delta(resid, meta, "typicality", "uncommon", "common")
    if typ is not None:
        rows += _delta_rows(model_key, "typicality", *typ, layers)

    evoc = _matched_pair_delta(resid, meta) or _within_sign_delta(
        resid, meta, "evocativeness", "high", "low"
    )
    if evoc is not None:
        rows += _delta_rows(model_key, "evocativeness", *evoc, layers)

    return pd.DataFrame(rows, columns=["model_key", "contrast", "layer", "delta", "delta_cos", "n_pos", "n_neg"])


def _delta_rows(model_key, name, diff, pos_mean, neg_mean, n_pos, n_neg, layers) -> list[dict]:
    """Per-layer rows for one contrast: ``delta`` = ‖diff[layer]‖₂, and
    ``delta_cos`` = cos(pos_mean[layer], neg_mean[layer]) (companion effect
    size; for a control-averaged contrast pos_mean/neg_mean are the pooled
    condition means, used for the cosine only -- ``diff`` is the controlled
    estimate)."""
    out = []
    for col, layer in enumerate(layers):
        p, q = pos_mean[col], neg_mean[col]
        denom = np.linalg.norm(p) * np.linalg.norm(q)
        cos = float(np.dot(p, q) / denom) if denom > 0 else 0.0
        out.append(
            {
                "model_key": model_key,
                "contrast": name,
                "layer": int(layer),
                "delta": float(np.linalg.norm(diff[col])),
                "delta_cos": cos,
                "n_pos": int(n_pos),
                "n_neg": int(n_neg),
            }
        )
    return out


def _within_sign_delta(resid, meta, col, hi, lo):
    """Controlled δ for a within-item factor: the per-layer (hi − lo)
    difference vector computed WITHIN each sign, then averaged over the signs
    that have both conditions. Returns (diff, pooled_hi_mean, pooled_lo_mean,
    n_hi, n_lo) or None if no sign has both conditions. Averaging the
    per-sign differences cancels the sign (Knobe) signal, so a pure sign
    confound cannot leak into this contrast."""
    per_sign_diffs = []
    hi_all: list[int] = []
    lo_all: list[int] = []
    for sign in ("bad", "good"):
        hi_idx = [i for i, m in enumerate(meta) if m["sign"] == sign and m[col] == hi]
        lo_idx = [i for i, m in enumerate(meta) if m["sign"] == sign and m[col] == lo]
        if not hi_idx or not lo_idx:
            continue
        per_sign_diffs.append(resid[hi_idx].mean(axis=0) - resid[lo_idx].mean(axis=0))
        hi_all += hi_idx
        lo_all += lo_idx
    if not per_sign_diffs:
        return None
    diff = np.mean(per_sign_diffs, axis=0)
    return diff, resid[hi_all].mean(axis=0), resid[lo_all].mean(axis=0), len(hi_all), len(lo_all)


def _matched_pair_delta(resid, meta):
    """Controlled δ for evocativeness: the per-layer (high − low) difference
    vector within each matched (family_id, typicality) pair -- the two
    variants that differ ONLY in evocativeness -- averaged over complete
    pairs. Returns (diff, pooled_high_mean, pooled_low_mean, n_high, n_low)
    or None if no complete pair exists (caller falls back to within-sign)."""
    from collections import defaultdict

    groups: dict[tuple, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    for i, m in enumerate(meta):
        groups[(m["family_id"], m["typicality"])][m["evocativeness"]].append(i)

    pair_diffs = []
    hi_all: list[int] = []
    lo_all: list[int] = []
    for conds in groups.values():
        if "high" not in conds or "low" not in conds:
            continue  # incomplete matched pair -- skip
        pair_diffs.append(resid[conds["high"]].mean(axis=0) - resid[conds["low"]].mean(axis=0))
        hi_all += conds["high"]
        lo_all += conds["low"]
    if not pair_diffs:
        return None
    diff = np.mean(pair_diffs, axis=0)
    return diff, resid[hi_all].mean(axis=0), resid[lo_all].mean(axis=0), len(hi_all), len(lo_all)


def plot_delta_l(df: pd.DataFrame, out_path: Path) -> None:
    """One line per contrast: δ vs layer (Raimondi's mid-to-late-layer
    concentration is the qualitative check, WO-6 G3 gate input)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 5))
    for name, sub in df.groupby("contrast"):
        sub = sub.sort_values("layer")
        ax.plot(sub["layer"], sub["delta"], marker="o", label=name)
    model_key = df["model_key"].iloc[0] if len(df) else "?"
    ax.set_xlabel("layer (residual-stream slice: 0=embed, s=resid_post.(s-1))")
    ax.set_ylabel("δ_l = ‖mean(pos) − mean(neg)‖₂")
    ax.set_title(f"Per-layer activation contrast δ_l — {model_key}")
    ax.legend()
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Backend construction from the registry.
# ---------------------------------------------------------------------------


def resolve_checkpoint(model_key: str, registry: dict[str, Family]) -> tuple[str, str, Family]:
    """model_key → (model_id, family_name, Family). Builds on
    elicit_vllm.resolve_model_id (the "{family}-{pretrained|instruct}"
    reverse lookup) and additionally returns the Family (dims / backend
    choice / revision)."""
    model_id, family_name, _revision = resolve_model_id(model_key, registry)
    return model_id, family_name, registry[family_name]


# The user-facing backend names (CLI ``--backend`` choices). "auto" picks
# per the registry ``mech_backend`` field; "tl"/"nnsight" map to the
# ``BACKENDS`` / registry keys below.
BACKEND_CHOICES = ("fake", "tl", "nnsight", "auto")
_BACKEND_KEY = {"tl": "transformer_lens", "nnsight": "nnsight"}


def build_backend(model_key: str, backend_name: str, registry: dict[str, Family]) -> ResidualAccess:
    """Constructs a ``ResidualAccess`` for ``model_key``. ``backend_name``
    "fake" gives a plain (no planted signal) deterministic FakeBackend for
    GPU-free plumbing rehearsal; "tl"/"nnsight" load the real model; "auto"
    honors the registry's ``mech_backend`` field."""
    model_id, _family_name, family = resolve_checkpoint(model_key, registry)
    if backend_name == "fake":
        return FakeBackend(model_key, family.n_layers, family.d_model)
    key = family.mech_backend if backend_name == "auto" else _BACKEND_KEY.get(backend_name)
    if key not in BACKENDS:
        raise ValueError(f"unknown backend {backend_name!r}; choose fake|tl|nnsight|auto")
    # The actual per-checkpoint HF id (pretrained vs finetuned) -- NOT a
    # shared tl_name, so donor and recipient really are different weights.
    # gpu tests confirm TransformerLens/nnsight recognize both names.
    return BACKENDS[key](model_key, model_id, family.n_layers, family.d_model, family.revision)


# ---------------------------------------------------------------------------
# CLI orchestration.
# ---------------------------------------------------------------------------


def acts_dir(out_root: Path, release: str, model_key: str) -> Path:
    return Path(out_root) / release / "acts" / model_key


def run_cache(
    *,
    release: str,
    model_key: str,
    backend_name: str,
    prompts_path: str | Path,
    vignettes_path: str | Path,
    out_root: str | Path = "results",
    registry_path: str | Path | None = None,
    backend: ResidualAccess | None = None,
    limit: int | None = None,
    shard: tuple[int, int] | None = None,
    force: bool = False,
    storage_config_path: str | Path | None = None,
) -> int:
    """cache → δ_l → parquet + plot for one checkpoint. ``backend`` may be
    injected (tests pass a planted FakeBackend); otherwise it is built from
    the registry. When ``storage_config_path`` is given, the cache +
    summary artifacts are pushed to the configured backend (spec §1.1
    durability rule)."""
    registry = load_registry(registry_path) if registry_path else registry_default()
    if backend is None:
        backend = build_backend(model_key, backend_name, registry)

    all_prompts = read_jsonl(prompts_path, PromptRecord)
    prompts = select_prompts(all_prompts, limit=limit, shard=shard)
    if not prompts:
        print("[mech cache] no raw-format intentionality prompts selected -- nothing to do.", file=sys.stderr)
        return 0
    vignettes = read_csv_validated(vignettes_path, VignetteRow)

    out_dir = acts_dir(out_root, release, model_key)
    if shard is not None:
        out_dir = out_dir / f"shard_{shard[0]}_of_{shard[1]}"
    resid = cache_activations(backend, prompts, out_dir, force=force)

    # δ_l metadata MUST be aligned to the cache's ACTUAL on-disk row order, not
    # the current selection order. A resumed/merged cache can be in a different
    # order than `prompts` (a merged cache is shard-concatenated:
    # idx%n==0 rows, then idx%n==1, ...), so building meta from `prompts` here
    # would attribute residual rows to the wrong prompt_ids and silently
    # compute δ_l on a scrambled join. Read index.json (cheap -- not the whole
    # tensor) for the authoritative row→prompt_id mapping and hard-error if its
    # prompt_id set disagrees with the current selection (e.g. running the
    # unsharded path against a cache that only holds one shard's rows).
    index = json.loads((out_dir / INDEX_FILENAME).read_text(encoding="utf-8"))
    prompt_ids = index["prompt_ids"]
    if set(prompt_ids) != {p.prompt_id for p in prompts}:
        raise ValueError(
            f"cache in {out_dir} holds a different prompt_id set than the current selection "
            f"({len(prompt_ids)} cached vs {len(prompts)} selected) -- refusing to compute δ_l "
            f"on a mismatched cache. Re-run with --force, or --merge-shards a complete shard set."
        )
    layers = list(range(backend.n_layers + 1))
    meta = build_meta(prompt_ids, vignettes)
    delta = compute_delta_l(resid, meta, model_key, layers)
    delta.to_parquet(out_dir / "delta_l.parquet")
    if len(delta):
        plot_delta_l(delta, out_dir / "delta_l.png")

    if storage_config_path is not None:
        from knobe.storage import load_storage_config

        storage = load_storage_config(storage_config_path)
        # The remote key MUST carry the shard segment when sharded -- otherwise
        # every concurrent shard would push to the same acts/<release>/<model_key>/
        # keys and clobber each other in the bucket (they hold different rows).
        remote_base = f"acts/{release}/{model_key}"
        if shard is not None:
            remote_base = f"{remote_base}/shard_{shard[0]}_of_{shard[1]}"
        for name in (CACHE_FILENAME, INDEX_FILENAME, "delta_l.parquet", "delta_l.png"):
            fp = out_dir / name
            if fp.exists():
                storage.push(fp, f"{remote_base}/{name}")

    print(
        f"[mech cache] {model_key}: cached {resid.shape[0]} prompts x {resid.shape[1]} slices, "
        f"δ_l over {delta['contrast'].nunique() if len(delta) else 0} contrasts → {out_dir}",
        file=sys.stderr,
    )
    return 0


# ---------------------------------------------------------------------------
# Shard merge: combine shard_i_of_n/ caches into the top-level cache the
# probes loader expects (final_token_resid.safetensors + index.json).
# ---------------------------------------------------------------------------

_SHARD_DIR_RE = re.compile(r"^shard_(\d+)_of_(\d+)$")


def merge_shards(acts_model_dir: str | Path, *, force: bool = False) -> Path:
    """Combine the ``shard_i_of_n/`` sub-caches under ``acts_model_dir`` into
    a single top-level ``final_token_resid.safetensors`` + ``index.json`` (the
    layout ``probes``/``read_cache`` consume).

    Validates the shard set is complete and disjoint: every shard directory
    must agree on ``n``, all indices ``0..n-1`` must be present (missing shard
    → error), and no prompt_id may appear in two shards (duplicate row →
    error). Shard metadata (model_key / layers / d_model) must be consistent.
    Rows are concatenated in ascending shard-index order (deterministic).
    Returns the ``acts_model_dir`` the merged cache was written into."""
    acts_model_dir = Path(acts_model_dir)
    shard_dirs: dict[int, Path] = {}
    n_total: int | None = None
    for child in sorted(acts_model_dir.iterdir()) if acts_model_dir.exists() else []:
        if not child.is_dir():
            continue
        m = _SHARD_DIR_RE.match(child.name)
        if not m:
            continue
        i, n = int(m.group(1)), int(m.group(2))
        if n_total is None:
            n_total = n
        elif n != n_total:
            raise ValueError(
                f"inconsistent shard counts under {acts_model_dir}: found n={n_total} and n={n}"
            )
        if i in shard_dirs:
            raise ValueError(f"duplicate shard index {i} under {acts_model_dir}")
        shard_dirs[i] = child

    if n_total is None:
        raise ValueError(f"no shard_i_of_n directories found under {acts_model_dir} to merge.")
    missing = sorted(set(range(n_total)) - set(shard_dirs))
    if missing:
        raise ValueError(
            f"missing shard(s) {missing} of {n_total} under {acts_model_dir} -- cannot merge an "
            f"incomplete shard set (run the remaining shards first)."
        )

    if not force and cache_is_complete_any(acts_model_dir):
        # A top-level cache already exists; re-merging would be a no-op unless
        # the shards changed. Respect --force for an explicit rebuild.
        print(f"[mech cache] merged cache already present in {acts_model_dir} -- pass force to rebuild.", file=sys.stderr)
        return acts_model_dir

    resid_parts: list[np.ndarray] = []
    prompt_ids: list[str] = []
    base_meta: dict | None = None
    for i in range(n_total):
        resid, index = read_cache(shard_dirs[i])
        meta = {k: index[k] for k in ("model_key", "layers", "positions", "n_layers", "d_model") if k in index}
        if base_meta is None:
            base_meta = meta
        elif meta != base_meta:
            raise ValueError(
                f"shard {i} metadata {meta} disagrees with earlier shards {base_meta} under {acts_model_dir}"
            )
        resid_parts.append(resid)
        prompt_ids.extend(index["prompt_ids"])

    dupes = sorted(pid for pid, c in Counter(prompt_ids).items() if c > 1)
    if dupes:
        raise ValueError(f"duplicate prompt_id(s) across shards under {acts_model_dir}: {dupes}")

    combined = np.concatenate(resid_parts, axis=0)
    meta = dict(base_meta or {})
    meta["merged_from_shards"] = n_total
    write_cache(combined, prompt_ids, acts_model_dir, meta)
    print(
        f"[mech cache] merged {n_total} shards → {len(prompt_ids)} rows in {acts_model_dir}",
        file=sys.stderr,
    )
    return acts_model_dir


def cache_is_complete_any(out_dir: Path) -> bool:
    """True iff a self-consistent top-level cache (files present, index row
    count matches the tensor) already exists in ``out_dir`` -- the merge-skip
    predicate (row count unknown ahead of time, unlike cache_is_complete)."""
    out_dir = Path(out_dir)
    if not (out_dir / CACHE_FILENAME).exists() or not (out_dir / INDEX_FILENAME).exists():
        return False
    try:
        read_cache(out_dir)
    except Exception:
        return False
    return True


def run_merge_shards(
    *,
    release: str,
    model_key: str,
    out_root: str | Path = "results",
    force: bool = False,
    storage_config_path: str | Path | None = None,
) -> int:
    """``knobe mech cache --merge-shards`` entry point: merge the shard
    sub-caches under ``results/<release>/acts/<model_key>/`` into the
    top-level cache, then optionally push it to configured storage."""
    acts_model_dir = acts_dir(out_root, release, model_key)
    merge_shards(acts_model_dir, force=force)

    if storage_config_path is not None:
        from knobe.storage import load_storage_config

        storage = load_storage_config(storage_config_path)
        remote_base = f"acts/{release}/{model_key}"
        for name in (CACHE_FILENAME, INDEX_FILENAME):
            fp = acts_model_dir / name
            if fp.exists():
                storage.push(fp, f"{remote_base}/{name}")
    return 0


def registry_default() -> dict[str, Family]:
    return load_registry(default_registry_path())
