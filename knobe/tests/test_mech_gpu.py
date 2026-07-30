"""GPU-only tests for src/knobe/mech/ (WO-6), all @pytest.mark.gpu so they
are DESELECTED by default (pyproject addopts ``-m 'not gpu'``) and never run
on a laptop without torch/transformer_lens/nnsight/lm-eval. The H200 runs
them with ``pytest -m gpu`` (a command-line ``-m`` overrides the addopts
default).

These pin down the parts of backend.py that cannot be verified locally --
the exact TransformerLens/nnsight APIs, the real debug-model cache→δ_l→sweep
smoke path, and the lm-eval capability check -- per WO-6's acceptance
criteria and the task-7-brief note ("For TL/nnsight API details you cannot
verify locally, write careful, conventional code ... do not silently
guess"). They are written so a maintainer on the H200 can run and, if an API
detail differs, fix in one place.

Debug model: gemma-2-2b (registry ``role: debug``); WO-6 budgets the whole
end-to-end at < 30 min on one small GPU over ~40 items.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

pytestmark = pytest.mark.gpu

DEBUG_FAMILY = "gemma-2-2b"


def _registry():
    from knobe.registry import load_registry

    root = Path(__file__).resolve().parents[1]
    return load_registry(root / "configs" / "models.yaml")


def _build_backends():
    from knobe.mech.cache_acts import build_backend

    reg = _registry()
    recip = build_backend(f"{DEBUG_FAMILY}-instruct", "tl", reg)
    donor = build_backend(f"{DEBUG_FAMILY}-pretrained", "tl", reg)
    return recip, donor


# ---------------------------------------------------------------------------
# Part A.3: TL vs nnsight equivalence on the debug model.
# ---------------------------------------------------------------------------


def test_tl_vs_nnsight_cached_residuals_agree():
    """Cached final-token residuals from TLBackend and NnsightBackend agree
    within fp16 tolerance (WO-6 Part A equivalence check)."""
    from knobe.mech.cache_acts import build_backend

    reg = _registry()
    prompts = ["Read the scenario and answer 0-10.\nScenario: x.\nQuestion: y?\nAnswer:"]
    tl = build_backend(f"{DEBUG_FAMILY}-instruct", "tl", reg)
    nn = build_backend(f"{DEBUG_FAMILY}-instruct", "nnsight", reg)
    tl_acts = tl.run_with_cache(prompts, layers=None, positions="final")
    nn_acts = nn.run_with_cache(prompts, layers=None, positions="final")
    assert tl_acts.resid.shape == nn_acts.resid.shape
    np.testing.assert_allclose(
        tl_acts.resid.astype(np.float32), nn_acts.resid.astype(np.float32), atol=1e-2, rtol=1e-2
    )


def test_tl_vs_nnsight_patched_scores_agree():
    """Patched logits_0_10 agree between the two backends within tolerance."""
    from knobe.mech.cache_acts import build_backend

    reg = _registry()
    prompts = ["Scenario: x.\nQuestion: y?\nAnswer:"]
    layers = [10]
    tl_r = build_backend(f"{DEBUG_FAMILY}-instruct", "tl", reg)
    tl_d = build_backend(f"{DEBUG_FAMILY}-pretrained", "tl", reg)
    nn_r = build_backend(f"{DEBUG_FAMILY}-instruct", "nnsight", reg)
    nn_d = build_backend(f"{DEBUG_FAMILY}-pretrained", "nnsight", reg)
    tl_scores = tl_r.run_patched(prompts, tl_d, layers)
    nn_scores = nn_r.run_patched(prompts, nn_d, layers)
    np.testing.assert_allclose(tl_scores, nn_scores, atol=5e-2)


# ---------------------------------------------------------------------------
# Identity + tokenizer alignment on a real model.
# ---------------------------------------------------------------------------


def test_real_self_patch_identity_within_tolerance():
    recip, _ = _build_backends()
    prompts = ["Scenario: a.\nQuestion: b?\nAnswer:"]
    baseline = recip.logits_0_10(prompts)
    patched = recip.run_patched(prompts, recip, [12])
    np.testing.assert_allclose(patched, baseline, atol=1e-2)


# ---------------------------------------------------------------------------
# Part B/C: real debug-model cache → δ_l → single-layer sweep → metrics.
# ---------------------------------------------------------------------------


def test_real_debug_model_end_to_end(tmp_path):
    """cache → δ_l plot → single-layer sweep → metrics on the debug model,
    ~40 items, < 30 min (WO-6 acceptance). Requires a released prompts.jsonl
    + vignettes.csv; skips cleanly if not present in the test environment."""
    from knobe.mech.cache_acts import run_cache
    from knobe.mech.patch import run_patch

    release_root = Path(__file__).resolve().parents[1] / "data" / "release"
    releases = sorted(p.name for p in release_root.glob("v*")) if release_root.exists() else []
    if not releases:
        pytest.skip("no release on disk to run the real end-to-end smoke against")
    release = releases[-1]
    vignettes = release_root / release / "vignettes.csv"
    prompts = release_root / release / "prompts.jsonl"
    if not prompts.exists():
        pytest.skip(f"release {release} has no prompts.jsonl")

    rc = run_cache(
        release=release, model_key=f"{DEBUG_FAMILY}-instruct", backend_name="tl",
        prompts_path=prompts, vignettes_path=vignettes, out_root=tmp_path, limit=40,
    )
    assert rc == 0
    rc = run_patch(
        release=release, family=DEBUG_FAMILY, backend_name="tl",
        prompts_path=prompts, vignettes_path=vignettes, layers_spec="sweep",
        out_root=tmp_path, limit=40,
    )
    assert rc == 0
    assert (Path(tmp_path) / release / "patch" / DEBUG_FAMILY / "patch_metrics.parquet").exists()


# ---------------------------------------------------------------------------
# Capability check (real lm-eval-harness).
# ---------------------------------------------------------------------------


@pytest.mark.xfail(
    reason="lm-eval wiring deferred; run_capability_check's real (non-fake) path is a "
    "documented stub that raises NotImplementedError until lm_eval.simple_evaluate is "
    "wired behind the guarded import (WO-6 Part C.4).",
    raises=(NotImplementedError, RuntimeError),
    strict=True,
)
def test_real_capability_check_runs():
    from knobe.mech.patch import run_capability_check

    recip, _ = _build_backends()
    result = run_capability_check(f"{DEBUG_FAMILY}-instruct", [12], backend=recip)
    for task in ("arc_easy", "hellaswag", "mmlu", "truthfulqa"):
        assert "delta" in result[task]
