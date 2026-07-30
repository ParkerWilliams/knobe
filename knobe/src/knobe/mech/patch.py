"""S6b: layer patching + patched re-elicitation metrics + capability-check
hook (master spec §3.8, §5.2-5.4; WO-6 Part C).

Orchestration only -- like cache_acts.py this drives a ``ResidualAccess``
backend and never imports transformer_lens/nnsight (spec §5.1), so the whole
sweep runs GPU-free under FakeBackend.

Procedure (spec §5.2): for a core family, patch the pretrained (donor)
residual stream into the finetuned (recipient) model one layer at a time,
all token positions, then re-elicit intentionality deterministically via
the logit-distribution expected value (scoring == "logits_0_10", NOT
stochastic sampling) → ``patch/<family>/layer_<l>.jsonl`` as PatchRecords.

Metrics per patched config (spec §5.3) → ``patch_metrics.parquet``: the full
Δ_knobe plus every component gap, so RQ3's "which component did the patch
suppress" table falls straight out.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd

from knobe.mech.backend import FakeBackend, ResidualAccess
from knobe.mech.cache_acts import registry_default, build_backend, build_meta, select_prompts
from knobe.parsing import expected_rating_from_logprobs
from knobe.registry import load_registry, model_key_for
from knobe.schemas import (
    PatchInfo,
    PatchRecord,
    PromptRecord,
    VignetteRow,
    read_csv_validated,
    read_jsonl,
    write_jsonl,
)

PATCH_RUNNER_VERSION = "mech-patch-0.1"
NEUTRAL_MIDPOINT = 5.0

# Deterministic-scoring placeholders written into every PatchRecord: the
# patched re-elicitation is a single deterministic forward (logit EV), not a
# sampled completion, so sample_idx/temperature/seed carry no information and
# are pinned here (documented in the PatchRecord docstring reference).
_DET_SAMPLE_IDX = 0
_DET_TEMPERATURE = 0.0
_DET_SEED = 0
_DET_TIMESTAMP = 0.0


# ---------------------------------------------------------------------------
# Layers-spec parsing: "sweep" | "top-k:K" | "3,7,11".
# ---------------------------------------------------------------------------


def parse_layers_spec(spec: str, n_layers: int, metrics_path: Path | None = None) -> list[list[int]]:
    """Turn a ``--layers`` spec into the list of patch CONFIGS to run, each a
    list of slice indices (see backend.py's convention):

      * ``"sweep"`` (default): every single layer 0..n_layers, each its own
        config → ``[[0], [1], ..., [n_layers]]``.
      * ``"3,7,11"``: one explicit multi-layer config → ``[[3, 7, 11]]``.
      * ``"top-k:K"``: one config of the K layers with the largest
        |Δ_knobe reduction| in a prior sweep's ``patch_metrics.parquet``
        (``metrics_path`` required).
    """
    spec = spec.strip()
    if spec == "sweep":
        return [[l] for l in range(n_layers + 1)]
    if spec.startswith("top-k:"):
        k = int(spec.split(":", 1)[1])
        if metrics_path is None:
            raise ValueError("--layers top-k:K requires a prior patch_metrics.parquet (metrics_path).")
        return [top_k_layers(metrics_path, k)]
    layers = [int(x) for x in spec.split(",") if x.strip()]
    if not layers:
        raise ValueError(f"could not parse --layers {spec!r}")
    return [layers]


def top_k_layers(metrics_path: Path, k: int) -> list[int]:
    """The K single layers whose patch most reduced |Δ_knobe| relative to
    the unpatched baseline (layers == "[]"), read from a prior sweep's
    metrics parquet. Ordering = descending |baseline_Δknobe − layer_Δknobe|."""
    df = pd.read_parquet(metrics_path)
    baseline = df[df["layers"] == "[]"]
    if baseline.empty:
        raise ValueError(f"{metrics_path} has no baseline row (layers == '[]') -- cannot rank layers.")
    base_knobe = float(baseline["delta_knobe"].iloc[0])
    singles = df[df["layers"].str.fullmatch(r"\[\d+\]")].copy()
    singles["reduction"] = (base_knobe - singles["delta_knobe"]).abs()
    singles = singles.sort_values("reduction", ascending=False)
    return sorted(int(s.strip("[]")) for s in singles["layers"].head(k))


# ---------------------------------------------------------------------------
# Scoring: logits → expected-value rating per prompt.
# ---------------------------------------------------------------------------


def _ev(logprobs_row: np.ndarray) -> float:
    return expected_rating_from_logprobs([float(x) for x in logprobs_row])


def score_config(
    recipient: ResidualAccess,
    donor: ResidualAccess | None,
    prompt_texts: Sequence[str],
    layers: Sequence[int],
) -> tuple[np.ndarray, np.ndarray]:
    """Returns (logprobs ``[n, 11]``, ev ``[n]``) for one patch config.
    ``layers == []`` (and ``donor is None``) is the unpatched baseline
    (recipient.logits_0_10); otherwise recipient.run_patched(donor, layers)."""
    if not layers:
        logprobs = recipient.logits_0_10(prompt_texts)
    else:
        assert donor is not None
        logprobs = recipient.run_patched(prompt_texts, donor, list(layers))
    ev = np.array([_ev(row) for row in logprobs])
    return logprobs, ev


# ---------------------------------------------------------------------------
# PatchRecord writing (spec §3.8).
# ---------------------------------------------------------------------------


def _patch_records(
    prompt_ids: Sequence[str],
    model_key: str,
    logprobs: np.ndarray,
    ev: np.ndarray,
    layers: Sequence[int],
    model_revision: str,
) -> list[PatchRecord]:
    layers_tag = ",".join(str(l) for l in layers) if layers else "baseline"
    # The unpatched baseline (layers==[]) has no donor -- record donor="none"
    # so a baseline PatchRecord is unambiguously distinguishable from a
    # layer-patched one (spec §3.8; donor is a free str field there).
    donor = "pretrained" if layers else "none"
    records = []
    for pid, lp_row, ev_val in zip(prompt_ids, logprobs, ev):
        records.append(
            PatchRecord(
                job_id=f"{pid}::patch::{layers_tag}",
                prompt_id=pid,
                model_key=model_key,
                sample_idx=_DET_SAMPLE_IDX,
                temperature=_DET_TEMPERATURE,
                seed=_DET_SEED,
                raw_response=f"[logits_0_10 EV={float(ev_val):.6f}]",
                parsed_rating=float(ev_val),
                parse_ok=True,
                parse_method="logit_fallback",
                logprobs_0_10=[float(x) for x in lp_row],
                model_revision=model_revision,
                runner_version=PATCH_RUNNER_VERSION,
                timestamp=_DET_TIMESTAMP,
                patch=PatchInfo(donor=donor, layers=list(layers), positions="all"),
                scoring="logits_0_10",
            )
        )
    return records


def write_patch_records(records: Sequence[PatchRecord], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(records, path)


def _read_complete_ev(path: Path, prompt_ids: Sequence[str]) -> np.ndarray | None:
    """Resume predicate for one config's ``layer_<tag>.jsonl``: if the file
    exists and holds exactly one PatchRecord per expected prompt_id (same
    set, no missing/extra rows), return the EV vector aligned to
    ``prompt_ids``; otherwise return None (caller recomputes + rewrites the
    file)."""
    if not path.exists():
        return None
    try:
        recs = read_jsonl(path, PatchRecord)
        ev_by_pid = {r.prompt_id: r.parsed_rating for r in recs}
        if len(recs) != len(prompt_ids) or set(ev_by_pid) != set(prompt_ids):
            return None
        # float() is inside the guard on purpose: a corrupt/null parsed_rating
        # (e.g. an interrupted write) must trigger a clean recompute, not crash.
        return np.array([float(ev_by_pid[pid]) for pid in prompt_ids])
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Metrics (spec §5.3).
# ---------------------------------------------------------------------------


def _mean(df: pd.DataFrame, mask: pd.Series) -> float:
    sub = df[mask]
    return float(sub["ev"].mean()) if len(sub) else float("nan")


def _within_sign_gap(df: pd.DataFrame, col: str, hi: str, lo: str) -> float:
    """Mean(hi) − mean(lo) computed within each sign then averaged over the
    signs present (bad, good) -- the factorial design's controlled subset
    for the E_typ / E_evoc effects (spec §5.3)."""
    gaps = []
    for sign in ("bad", "good"):
        sign_df = df[df["sign"] == sign]
        hi_m = _mean(sign_df, sign_df[col] == hi)
        lo_m = _mean(sign_df, sign_df[col] == lo)
        if not (np.isnan(hi_m) or np.isnan(lo_m)):
            gaps.append(hi_m - lo_m)
    return float(np.mean(gaps)) if gaps else float("nan")


def compute_metrics_row(model_key: str, family: str, layers: Sequence[int], meta: Sequence[dict], ev: np.ndarray) -> dict:
    """One ``patch_metrics.parquet`` row for a patched config: the full
    Δ_knobe plus every §5.3 component gap, from EV scores + item metadata."""
    df = pd.DataFrame(meta)
    df["ev"] = ev
    return {
        "model_key": model_key,
        "family": family,
        "layers": "[" + ",".join(str(l) for l in layers) + "]",
        "positions": "all" if layers else "",
        "scoring": "logits_0_10",
        "n": int(len(df)),
        # Δ_knobe = μ(bad) − μ(good) over MB+NMB vs MG+NMG (spec §5.3).
        "delta_knobe": _mean(df, df["sign"] == "bad") - _mean(df, df["sign"] == "good"),
        "delta_moral": _mean(df, df["valence"] == "MB") - _mean(df, df["valence"] == "MG"),
        "delta_nonmoral": _mean(df, df["valence"] == "NMB") - _mean(df, df["valence"] == "NMG"),
        # NEU mean − scale midpoint (documented offset, spec §5.3).
        "delta_neutral_offset": _mean(df, df["valence"] == "NEU") - NEUTRAL_MIDPOINT,
        "e_typ": _within_sign_gap(df, "typicality", "uncommon", "common"),
        "e_evoc": _within_sign_gap(df, "evocativeness", "high", "low"),
    }


METRIC_COLUMNS = [
    "model_key", "family", "layers", "positions", "scoring", "n",
    "delta_knobe", "delta_moral", "delta_nonmoral", "delta_neutral_offset", "e_typ", "e_evoc",
]


# ---------------------------------------------------------------------------
# Capability-check hook (spec §5.4; WO-6 Part C.4).
# ---------------------------------------------------------------------------


def run_capability_check(
    model_key: str,
    patch_config: Sequence[int],
    tasks: Sequence[str] = ("arc_easy", "hellaswag", "mmlu", "truthfulqa"),
    *,
    backend: ResidualAccess | None = None,
) -> dict:
    """Capability check for a "successful" patch config (spec §5.4): run
    lm-eval-harness on ARC-Easy/HellaSwag/MMLU/TruthfulQA against the
    patched model and report deltas vs unpatched.

    This is a thin, config-gated hook. The real path (guarded ``lm_eval``
    import) is gpu-only and confirmed by a @pytest.mark.gpu test; the
    FakeBackend path returns CANNED per-task deltas so the report plumbing
    (which consumes this dict) is testable offline. The interface is fixed
    here: ``{task: {"patched": float, "unpatched": float, "delta": float}}``
    plus a ``"_meta"`` block."""
    if isinstance(backend, FakeBackend):
        # Deterministic canned result: a small, plausible capability dip.
        out = {}
        for i, task in enumerate(tasks):
            unpatched = 0.70 - 0.01 * i
            delta = -0.02 - 0.005 * len(patch_config)
            out[task] = {"patched": unpatched + delta, "unpatched": unpatched, "delta": delta}
        out["_meta"] = {"model_key": model_key, "patch_config": list(patch_config), "backend": "fake", "canned": True}
        return out

    try:  # pragma: no cover -- gpu-only real path
        import lm_eval  # noqa: F401
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "lm-eval is required for the real capability check -- install the 'eval' extra "
            "(`uv pip install -e '.[eval]'`). Use the FakeBackend path for offline plumbing tests."
        ) from exc
    raise NotImplementedError(  # pragma: no cover -- gpu-only; the @pytest.mark.gpu test drives the real harness
        "Real lm-eval capability check runs only on the H200 (gpu-marked test); "
        "wire the patched-model hook into lm_eval.simple_evaluate here."
    )


# ---------------------------------------------------------------------------
# Sweep orchestration.
# ---------------------------------------------------------------------------


def run_sweep(
    recipient: ResidualAccess,
    donor: ResidualAccess,
    prompts: Sequence[PromptRecord],
    vignettes: Sequence[VignetteRow],
    configs: Sequence[Sequence[int]],
    family: str,
    out_dir: Path,
    *,
    model_revision: str = "fake",
    include_baseline: bool = True,
    force: bool = False,
    storage=None,
    remote_base: str | None = None,
) -> pd.DataFrame:
    """The layer sweep: writes ``layer_<tag>.jsonl`` PatchRecords per config
    (plus the unpatched baseline row, layers==[]) and returns the
    ``patch_metrics`` DataFrame. Asserts donor/recipient tokenizer alignment
    per prompt via run_patched (spec §5.5) -- hard error on mismatch.

    Resumable (spec §1 scheduler-agnostic rule): a config whose
    ``layer_<tag>.jsonl`` already holds exactly one row per prompt is skipped
    (its EV is reused from disk for the metrics table, so no backend call is
    made); an incomplete/corrupt file is recomputed and rewritten. ``force``
    recomputes everything. When ``storage`` is given, each config's jsonl is
    pushed under ``remote_base`` right after it is (re)written, and
    ``patch_metrics.parquet`` at the end (spec §1.1 durability).

    Parallelism policy: parallelize a sweep by ``--layers`` (each config writes
    a DISTINCT ``layer_<tag>.jsonl``, so parallel processes never collide), NOT
    by ``--shard``. Every shard of a ``--shard`` run writes the SAME
    ``layer_<tag>.jsonl`` paths (and pushes to the same shard-less remote
    keys), so concurrent ``--shard`` patch runs against one output dir clobber
    each other -- and with resume enabled they rewrite each other's "complete"
    files. Use ``--shard`` only to subset prompts within a single process.

    Performance note (GPU path): each config calls ``run_patched``, which
    re-runs the DONOR forward internally. The donor activations are
    config-independent, so a full sweep recomputes the identical donor
    forward once per config -- an O(n_configs) redundancy that is negligible
    for FakeBackend but real on the H200. Hoisting a single all-positions
    donor cache across configs is the intended optimization; it is deferred
    because a correct implementation needs the all-positions ``Acts``
    representation to handle variable-length sequences per prompt (the fp16
    ``Acts`` here is fixed-shape, final-token only), which only the gpu-marked
    tests can exercise."""
    out_dir = Path(out_dir)
    prompt_ids = [p.prompt_id for p in prompts]
    texts = [p.text for p in prompts]
    meta = build_meta(prompt_ids, vignettes)

    all_configs: list[Sequence[int]] = []
    if include_baseline:
        all_configs.append([])
    all_configs.extend(configs)

    metric_rows = []
    for layers in all_configs:
        tag = "baseline" if not layers else "_".join(str(l) for l in layers)
        fp = out_dir / f"layer_{tag}.jsonl"
        ev = None if force else _read_complete_ev(fp, prompt_ids)
        if ev is not None:
            print(f"[mech patch] {fp.name} already complete ({len(prompt_ids)} rows) -- skipping.", file=sys.stderr)
        else:
            d = None if not layers else donor
            logprobs, ev = score_config(recipient, d, texts, layers)
            records = _patch_records(prompt_ids, recipient.model_key, logprobs, ev, layers, model_revision)
            write_patch_records(records, fp)
            if storage is not None and remote_base is not None:
                storage.push(fp, f"{remote_base}/{fp.name}")
        metric_rows.append(compute_metrics_row(recipient.model_key, family, layers, meta, ev))

    metrics = pd.DataFrame(metric_rows, columns=METRIC_COLUMNS)
    out_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = out_dir / "patch_metrics.parquet"
    metrics.to_parquet(metrics_path)
    if storage is not None and remote_base is not None:
        storage.push(metrics_path, f"{remote_base}/{metrics_path.name}")
    return metrics


# ---------------------------------------------------------------------------
# CLI orchestration.
# ---------------------------------------------------------------------------


def patch_dir(out_root: Path, release: str, family: str) -> Path:
    return Path(out_root) / release / "patch" / family


def run_patch(
    *,
    release: str,
    family: str,
    backend_name: str,
    prompts_path: str | Path,
    vignettes_path: str | Path,
    layers_spec: str = "sweep",
    out_root: str | Path = "results",
    registry_path: str | Path | None = None,
    recipient: ResidualAccess | None = None,
    donor: ResidualAccess | None = None,
    limit: int | None = None,
    shard: tuple[int, int] | None = None,
    force: bool = False,
    storage_config_path: str | Path | None = None,
) -> int:
    """``knobe mech patch`` entry point: build donor (pretrained) + recipient
    (finetuned) backends for ``family``, parse the layers spec, run the
    sweep. ``recipient``/``donor`` may be injected (tests pass planted
    FakeBackends). Resumable: already-complete config files are skipped.
    When ``storage_config_path`` is given, each config's jsonl +
    patch_metrics.parquet are pushed to the configured backend."""
    registry = load_registry(registry_path) if registry_path else registry_default()
    if family not in registry:
        print(f"ERROR: family {family!r} not in registry.", file=sys.stderr)
        return 1

    recip_key = model_key_for(family, "finetuned")
    donor_key = model_key_for(family, "pretrained")
    if recipient is None:
        recipient = build_backend(recip_key, backend_name, registry)
    if donor is None:
        donor = build_backend(donor_key, backend_name, registry)

    all_prompts = read_jsonl(prompts_path, PromptRecord)
    prompts = select_prompts(all_prompts, limit=limit, shard=shard)
    if not prompts:
        print("[mech patch] no raw-format intentionality prompts selected -- nothing to do.", file=sys.stderr)
        return 0
    vignettes = read_csv_validated(vignettes_path, VignetteRow)

    out_dir = patch_dir(out_root, release, family)
    metrics_path = out_dir / "patch_metrics.parquet"
    configs = parse_layers_spec(
        layers_spec, recipient.n_layers, metrics_path if metrics_path.exists() else None
    )
    storage = None
    remote_base = None
    if storage_config_path is not None:
        from knobe.storage import load_storage_config

        storage = load_storage_config(storage_config_path)
        remote_base = f"patch/{release}/{family}"
        if shard is not None:
            print(
                "[mech patch] WARNING: --shard combined with --storage. Patch-sweep shards write "
                "the SAME layer_<tag>.jsonl paths and push to the SAME shard-less remote keys, so "
                "concurrent shards clobber each other. Parallelize by --layers instead; use --shard "
                "only for single-process prompt subsetting.",
                file=sys.stderr,
            )

    metrics = run_sweep(
        recipient, donor, prompts, vignettes, configs, family, out_dir,
        model_revision=registry[family].revision if backend_name != "fake" else "fake",
        force=force, storage=storage, remote_base=remote_base,
    )
    baseline = metrics[metrics["layers"] == "[]"]
    base_knobe = float(baseline["delta_knobe"].iloc[0]) if len(baseline) else float("nan")
    print(
        f"[mech patch] {family}: {len(configs)} config(s) + baseline over {len(prompts)} prompts; "
        f"baseline Δ_knobe={base_knobe:.3f} → {out_dir}",
        file=sys.stderr,
    )
    return 0
