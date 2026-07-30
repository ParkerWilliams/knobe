"""Tests for src/knobe/mech/ (WO-6): backend.py (ResidualAccess protocol +
FakeBackend with real patching semantics), cache_acts.py (activation cache +
δ_l), patch.py (layer sweep + metrics + capability hook).

Every test here is GPU-free: FakeBackend is the vehicle, torch/transformer_
lens/nnsight are never imported (their guarded imports only surface when the
real backends are constructed, which the @pytest.mark.gpu tests in
tests/test_mech_gpu.py do on the H200).

Acceptance criteria under test (task-7-brief.md):
  - Identity: self-patch (donor == recipient) leaves logits_0_10 unchanged
    (EXACT here, since FakeBackend patches at full compute precision).
  - Planted-signal: a FakeBackend with an injected layer-5 bad/good contrast
    → δ_l peaks at layer 5, and patching layer 5 (donor lacks the signal)
    shrinks Δ_knobe MORE than patching any other layer. Driven end-to-end
    through cache → δ_l and through the real sweep → metrics loop.
  - safetensors round-trip + index integrity; resume skip; shard partition.
  - Tokenizer/seq-alignment mismatch → hard error.
  - Capability-check hook returns canned deltas (report plumbing testable).
  - CLI: `knobe mech cache` / `knobe mech patch` smoke with --backend fake.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from knobe import constants
from knobe.mech import cache_acts, patch as patch_mod
from knobe.mech.backend import (
    Acts,
    FakeBackend,
    PlantedSignal,
    ResidualAccess,
    TokenizerMismatchError,
)
from knobe.parsing import expected_rating_from_logprobs
from knobe.schemas import (
    PatchRecord,
    PromptRecord,
    VignetteRow,
    read_csv_validated,
    read_jsonl,
    sha256_for_text,
    write_csv_validated,
    write_jsonl,
)

N_LAYERS = 8
D_MODEL = 16
SIGNAL_LAYER = 5

_SIGN_OF_VALENCE = {"MB": 1, "NMB": 1, "MG": -1, "NMG": -1, "NEU": 0}


# ---------------------------------------------------------------------------
# Fixture: content-matched bad/good families so the planted-signal contrast
# is exactly zero pre-injection (the base residuals cancel in bad − good).
# ---------------------------------------------------------------------------


def _build_fixture(tmp_path: Path, n_pairs: int = 4):
    """Writes vignettes.csv + prompts.jsonl and returns (prompts_path,
    vignettes_path, label_fn). Matched families share a content_key: MB-i
    with MG-i ("pair{i}"), NMB-j with NMG-j ("nm{j}"); NEU stands alone."""
    vignette_rows: list[VignetteRow] = []
    prompt_records: list[PromptRecord] = []
    text_to_label: dict[str, tuple[str, int]] = {}

    def add_family(family_id: str, valence: str, subdomain: str, content_key: str):
        sign = constants.SIGN_BY_VALENCE[valence]
        for (typicality, evocativeness), letter in constants.VARIANT_LETTER.items():
            variant_id = f"{family_id}-{letter}"
            vignette_rows.append(
                VignetteRow(
                    variant_id=variant_id, family_id=family_id, domain="Environment",
                    valence=valence, nonmoral_subdomain=subdomain, sign=sign,
                    typicality=typicality, evocativeness=evocativeness,
                    scenario=f"scenario {variant_id}",
                    q_intentionality="Did they intentionally do it, 0 to 10?",
                    q_blame="How blameworthy, 0 to 10?", q_praise="How praiseworthy, 0 to 10?",
                )
            )
            text = f"PROMPT for {variant_id}"
            prompt_id = f"{variant_id}::intentionality::raw"
            prompt_records.append(
                PromptRecord(
                    prompt_id=prompt_id, variant_id=variant_id, question_type="intentionality",
                    format="raw", text=text, messages=None, sha256=sha256_for_text(text),
                )
            )
            text_to_label[text] = (content_key, _SIGN_OF_VALENCE[valence])

    for i in range(n_pairs):
        add_family(f"ENV-MB-{i:02d}", "MB", "", f"pair{i}")
        add_family(f"ENV-MG-{i:02d}", "MG", "", f"pair{i}")
    for j in range(2):
        add_family(f"ENV-NMB-{j:02d}", "NMB", "prudential", f"nm{j}")
        add_family(f"ENV-NMG-{j:02d}", "NMG", "prudential", f"nm{j}")
    for k in range(2):
        add_family(f"ENV-NEU-{k:02d}", "NEU", "", f"neu{k}")

    prompts_path = tmp_path / "prompts.jsonl"
    vignettes_path = tmp_path / "vignettes.csv"
    write_jsonl(prompt_records, prompts_path)
    write_csv_validated(vignette_rows, vignettes_path, VignetteRow)

    def label_fn(text: str) -> tuple[str, int]:
        return text_to_label.get(text, (text, 0))

    return prompts_path, vignettes_path, label_fn


def _planted_pair(label_fn, magnitude: float = 1.0):
    recipient = FakeBackend(
        "fam-instruct", N_LAYERS, D_MODEL, label_fn=label_fn,
        planted=PlantedSignal(layer=SIGNAL_LAYER, magnitude=magnitude),
    )
    donor = FakeBackend("fam-pretrained", N_LAYERS, D_MODEL, label_fn=label_fn)
    return recipient, donor


# ---------------------------------------------------------------------------
# Protocol conformance.
# ---------------------------------------------------------------------------


def test_fakebackend_satisfies_protocol():
    fb = FakeBackend("m", N_LAYERS, D_MODEL)
    assert isinstance(fb, ResidualAccess)
    assert fb.n_layers == N_LAYERS and fb.d_model == D_MODEL and fb.model_key == "m"


def test_run_with_cache_shape_and_dtype():
    fb = FakeBackend("m", N_LAYERS, D_MODEL)
    acts = fb.run_with_cache(["a b c", "d e"], layers=None, positions="final")
    assert isinstance(acts, Acts)
    assert acts.resid.shape == (2, N_LAYERS + 1, D_MODEL)
    assert acts.resid.dtype == np.float16
    assert acts.layers == list(range(N_LAYERS + 1))


def test_logits_0_10_are_normalised_logprobs():
    fb = FakeBackend("m", N_LAYERS, D_MODEL)
    lp = fb.logits_0_10(["x y", "z"])
    assert lp.shape == (2, 11)
    # log-softmax over the 11 tokens → each row's probabilities sum to 1.
    np.testing.assert_allclose(np.exp(lp).sum(axis=1), 1.0, atol=1e-9)


def test_determinism_across_instances():
    a = FakeBackend("m", N_LAYERS, D_MODEL).logits_0_10(["hello world"])
    b = FakeBackend("m", N_LAYERS, D_MODEL).logits_0_10(["hello world"])
    np.testing.assert_array_equal(a, b)


# ---------------------------------------------------------------------------
# Acceptance: self-patch identity (EXACT).
# ---------------------------------------------------------------------------


def test_self_patch_identity_exact():
    fb = FakeBackend("fam-instruct", N_LAYERS, D_MODEL)
    prompts = ["a b", "c d", "e f"]
    baseline = fb.logits_0_10(prompts)
    for layers in ([SIGNAL_LAYER], [0], list(range(N_LAYERS + 1)), [2, 4, 6]):
        patched = fb.run_patched(prompts, fb, layers)
        np.testing.assert_array_equal(patched, baseline)


def test_self_patch_identity_with_planted_signal():
    # Even a model that DOES carry a planted signal is unchanged by patching
    # it with ITSELF -- the identity must hold regardless of content.
    label_fn = lambda t: (t.split("|")[0], {"bad": 1, "good": -1}.get(t.split("|")[-1], 0))
    fb = FakeBackend("fam-instruct", N_LAYERS, D_MODEL, label_fn=label_fn, planted=PlantedSignal(SIGNAL_LAYER, 1.0))
    prompts = ["i0|bad", "i0|good", "i1|bad"]
    np.testing.assert_array_equal(fb.run_patched(prompts, fb, [SIGNAL_LAYER]), fb.logits_0_10(prompts))


# ---------------------------------------------------------------------------
# Acceptance: planted signal → δ_l peaks at layer 5.
# ---------------------------------------------------------------------------


def test_planted_signal_delta_l_peaks_at_layer_5(tmp_path):
    prompts_path, vignettes_path, label_fn = _build_fixture(tmp_path)
    recipient, _ = _planted_pair(label_fn)

    prompt_records = read_jsonl(prompts_path, PromptRecord)
    selected = cache_acts.select_prompts(prompt_records)
    acts = recipient.run_with_cache([p.text for p in selected], layers=None, positions="final")
    vignettes = read_csv_validated(vignettes_path, VignetteRow)
    meta = cache_acts.build_meta([p.prompt_id for p in selected], vignettes)

    delta = cache_acts.compute_delta_l(acts.resid, meta, recipient.model_key, acts.layers)
    bad_good = delta[delta["contrast"] == "bad_vs_good"].sort_values("layer")
    peak_layer = int(bad_good.loc[bad_good["delta"].idxmax(), "layer"])
    assert peak_layer == SIGNAL_LAYER
    # Discriminating: the peak is strictly above its neighbours (a δ computed
    # on the wrong axis, or a signal at the wrong layer, would not do this).
    deltas = bad_good.set_index("layer")["delta"]
    assert deltas[SIGNAL_LAYER] > deltas[SIGNAL_LAYER - 1] + 1e-6
    assert deltas[SIGNAL_LAYER] > deltas[SIGNAL_LAYER + 1] + 1e-6
    # Pre-injection layers carry no bad/good contrast at all (matched bases).
    assert deltas[SIGNAL_LAYER - 1] == pytest.approx(0.0, abs=1e-6)


# ---------------------------------------------------------------------------
# δ_l factorial controls (spec §5.3): typicality WITHIN sign, evocativeness
# WITHIN matched pairs -- must NOT leak the sign (Knobe) signal. Driven
# directly on compute_delta_l with hand-built resid + metadata so the
# confound is exactly constructible.
# ---------------------------------------------------------------------------

_DELTA_LAYER = 1
_N_SLICES = 3
_DELTA_D = 2


def _meta_row(sign, valence, typicality, evocativeness, family_id):
    return {
        "prompt_id": "p", "variant_id": "v", "family_id": family_id, "valence": valence,
        "sign": sign, "typicality": typicality, "evocativeness": evocativeness,
        "domain": "D", "nonmoral_subdomain": "",
    }


def _resid_from_signals(signal_vecs):
    """Build a [n, _N_SLICES, _DELTA_D] resid with each item's signal vector
    placed at layer _DELTA_LAYER (all other slices zero)."""
    resid = np.zeros((len(signal_vecs), _N_SLICES, _DELTA_D), dtype=np.float64)
    for i, v in enumerate(signal_vecs):
        resid[i, _DELTA_LAYER] = v
    return resid


def _pooled_delta(resid, meta, pos_pred, neg_pred, layer):
    """The NAIVE pooled mean-difference norm (the pre-fix implementation) --
    used in tests only, to prove the controlled estimator differs from it."""
    r = resid.astype(np.float64)
    pos = [i for i, m in enumerate(meta) if pos_pred(m)]
    neg = [i for i, m in enumerate(meta) if neg_pred(m)]
    diff = r[pos].mean(axis=0) - r[neg].mean(axis=0)
    return float(np.linalg.norm(diff[layer]))


def _delta_at(df, contrast, layer=_DELTA_LAYER):
    sub = df[(df["contrast"] == contrast) & (df["layer"] == layer)]
    return float(sub["delta"].iloc[0]) if len(sub) else None


def test_typicality_delta_l_removes_sign_confound():
    # PURE sign signal (bad = +v, good = -v), no true typicality signal, with
    # typicality sign-imbalanced: uncommon is mostly bad, common mostly good.
    v = np.array([1.0, 0.0])
    meta, sigs = [], []
    # uncommon: 6 bad, 2 good ; common: 2 bad, 6 good
    for sign, typ, count in [("bad", "uncommon", 6), ("good", "uncommon", 2),
                             ("bad", "common", 2), ("good", "common", 6)]:
        for k in range(count):
            meta.append(_meta_row(sign, "MB" if sign == "bad" else "MG", typ, "low", f"F{len(meta)}"))
            sigs.append(v if sign == "bad" else -v)
    resid = _resid_from_signals(sigs)
    df = cache_acts.compute_delta_l(resid, meta, "m", list(range(_N_SLICES)))

    bad_good = _delta_at(df, "bad_vs_good")
    typicality = _delta_at(df, "typicality")
    # The NAIVE pooled typicality would leak the sign signal -- demonstrably
    # nonzero here (this is exactly the reviewer's confound).
    pooled_typ = _pooled_delta(resid, meta, lambda r: r["typicality"] == "uncommon",
                               lambda r: r["typicality"] == "common", _DELTA_LAYER)
    assert bad_good == pytest.approx(2.0, abs=1e-6)
    assert pooled_typ > 0.5  # confounded implementation leaks the Knobe signal
    # The CONTROLLED (within-sign) estimator removes it: ~0 despite imbalance.
    assert typicality == pytest.approx(0.0, abs=1e-9)


def test_typicality_delta_l_recovers_within_sign_signal():
    # PURE typicality signal (uncommon = +w, common = -w), balanced across
    # sign, no sign signal.
    w = np.array([0.0, 1.0])
    meta, sigs = [], []
    for sign in ("bad", "good"):
        for typ in ("uncommon", "common"):
            for k in range(2):
                meta.append(_meta_row(sign, "MB" if sign == "bad" else "MG", typ, "low", f"F{len(meta)}"))
                sigs.append(w if typ == "uncommon" else -w)
    resid = _resid_from_signals(sigs)
    df = cache_acts.compute_delta_l(resid, meta, "m", list(range(_N_SLICES)))
    # A genuine within-sign typicality signal is recovered...
    assert _delta_at(df, "typicality") == pytest.approx(2.0, abs=1e-9)
    # ...while bad_vs_good stays ~0 (the signal is orthogonal to sign).
    assert _delta_at(df, "bad_vs_good") == pytest.approx(0.0, abs=1e-9)


def test_evocativeness_delta_l_matched_pairs_recover_and_control():
    # Two families (F0 bad, F1 good). Within each matched (family, typicality)
    # pair, plant a high−low evocativeness signal (high = +u, low = -u) AND a
    # per-family sign offset (bad = +s, good = -s). The matched-pair estimator
    # must recover the evocativeness signal and cancel the sign offset.
    u = np.array([0.0, 1.0])
    s = np.array([1.0, 0.0])
    meta, sigs = [], []
    for fam, sign in [("F0", "bad"), ("F1", "good")]:
        sign_off = s if sign == "bad" else -s
        for typ in ("common", "uncommon"):
            for evoc in ("low", "high"):
                meta.append(_meta_row(sign, "MB" if sign == "bad" else "MG", typ, evoc, fam))
                sigs.append(sign_off + (u if evoc == "high" else -u))
    resid = _resid_from_signals(sigs)
    df = cache_acts.compute_delta_l(resid, meta, "m", list(range(_N_SLICES)))
    # high−low = 2u within every pair; sign offset cancels within a pair.
    assert _delta_at(df, "evocativeness") == pytest.approx(2.0, abs=1e-9)


def test_evocativeness_delta_l_falls_back_to_within_sign_when_no_matched_pair():
    # No complete (family, typicality) pair exists (every family has only ONE
    # evocativeness level) -> matched-pair estimator returns nothing, so the
    # documented within-sign fallback is used. Plant a within-sign high−low
    # signal so the fallback has something to recover.
    u = np.array([0.0, 1.0])
    meta, sigs = [], []
    # Each family contributes exactly one variant (so no low/high pair), but
    # across families both evocativeness levels appear within each sign.
    for sign in ("bad", "good"):
        for evoc, count in [("high", 2), ("low", 2)]:
            for k in range(count):
                meta.append(_meta_row(sign, "MB" if sign == "bad" else "MG", "common", evoc, f"F{len(meta)}"))
                sigs.append(u if evoc == "high" else -u)
    resid = _resid_from_signals(sigs)
    df = cache_acts.compute_delta_l(resid, meta, "m", list(range(_N_SLICES)))
    # The fallback still produces an evocativeness row and recovers the signal.
    assert _delta_at(df, "evocativeness") == pytest.approx(2.0, abs=1e-9)


# ---------------------------------------------------------------------------
# Acceptance: patching layer 5 shrinks Δ_knobe most (whole sweep loop).
# ---------------------------------------------------------------------------


def test_planted_signal_patch_layer_5_shrinks_knobe_most(tmp_path):
    prompts_path, vignettes_path, label_fn = _build_fixture(tmp_path)
    recipient, donor = _planted_pair(label_fn)

    prompt_records = read_jsonl(prompts_path, PromptRecord)
    vignettes = read_csv_validated(vignettes_path, VignetteRow)
    prompts = cache_acts.select_prompts(prompt_records)

    configs = [[l] for l in range(N_LAYERS + 1)]
    out_dir = tmp_path / "patch" / "fam"
    metrics = patch_mod.run_sweep(recipient, donor, prompts, vignettes, configs, "fam", out_dir)

    base_knobe = float(metrics.loc[metrics["layers"] == "[]", "delta_knobe"].iloc[0])
    assert base_knobe > 3.0  # the planted signal produces a big baseline gap
    reductions = {}
    for l in range(N_LAYERS + 1):
        knobe_l = float(metrics.loc[metrics["layers"] == f"[{l}]", "delta_knobe"].iloc[0])
        reductions[l] = base_knobe - knobe_l
    best = max(reductions, key=reductions.get)
    assert best == SIGNAL_LAYER
    # Strictly greater than every other layer (unique argmax).
    for l, red in reductions.items():
        if l != SIGNAL_LAYER:
            assert reductions[SIGNAL_LAYER] > red + 1e-6
    # Patching layers strictly BEFORE the injection barely moves Δ_knobe --
    # the recipient block re-adds the signal downstream, so no signal is
    # removed; the only residual is a tiny read-out nonlinearity (the donor's
    # base shifts the absolute rating centre), orders of magnitude below the
    # layer-5 effect.
    for l in range(SIGNAL_LAYER):
        assert reductions[l] < 0.02 * reductions[SIGNAL_LAYER]


def test_sweep_writes_patchrecords_and_baseline(tmp_path):
    prompts_path, vignettes_path, label_fn = _build_fixture(tmp_path)
    recipient, donor = _planted_pair(label_fn)
    vignettes = read_csv_validated(vignettes_path, VignetteRow)
    prompts = cache_acts.select_prompts(read_jsonl(prompts_path, PromptRecord))

    out_dir = tmp_path / "patch" / "fam"
    patch_mod.run_sweep(recipient, donor, prompts, vignettes, [[5]], "fam", out_dir)

    baseline = read_jsonl(out_dir / "layer_baseline.jsonl", PatchRecord)
    patched = read_jsonl(out_dir / "layer_5.jsonl", PatchRecord)
    assert len(baseline) == len(prompts) == len(patched)
    assert baseline[0].patch.layers == [] and baseline[0].scoring == "logits_0_10"
    # The unpatched baseline carries donor="none"; a patched config, "pretrained".
    assert baseline[0].patch.donor == "none"
    assert patched[0].patch.layers == [5] and patched[0].patch.donor == "pretrained"
    assert patched[0].parse_method == "logit_fallback"
    # EV round-trips: parsed_rating equals the EV of the stored logprobs.
    assert patched[0].parsed_rating == pytest.approx(
        expected_rating_from_logprobs(patched[0].logprobs_0_10), abs=1e-9
    )


# ---------------------------------------------------------------------------
# safetensors round-trip + index integrity + resume skip.
# ---------------------------------------------------------------------------


def test_cache_roundtrip_and_index_integrity(tmp_path):
    prompts_path, vignettes_path, label_fn = _build_fixture(tmp_path)
    recipient, _ = _planted_pair(label_fn)
    prompts = cache_acts.select_prompts(read_jsonl(prompts_path, PromptRecord))
    out_dir = tmp_path / "acts"

    resid = cache_acts.cache_activations(recipient, prompts, out_dir)
    reloaded, index = cache_acts.read_cache(out_dir)
    np.testing.assert_array_equal(resid, reloaded)
    assert index["prompt_ids"] == [p.prompt_id for p in prompts]
    assert index["model_key"] == recipient.model_key
    assert reloaded.dtype == np.float16
    assert reloaded.shape == (len(prompts), N_LAYERS + 1, D_MODEL)


def test_cache_index_integrity_detects_mismatch(tmp_path):
    prompts_path, _, label_fn = _build_fixture(tmp_path)
    recipient, _ = _planted_pair(label_fn)
    prompts = cache_acts.select_prompts(read_jsonl(prompts_path, PromptRecord))
    out_dir = tmp_path / "acts"
    cache_acts.cache_activations(recipient, prompts, out_dir)
    # Corrupt index.json to disagree on row count.
    idx_path = out_dir / cache_acts.INDEX_FILENAME
    idx = json.loads(idx_path.read_text())
    idx["prompt_ids"] = idx["prompt_ids"][:-1]
    idx_path.write_text(json.dumps(idx))
    with pytest.raises(ValueError, match="integrity"):
        cache_acts.read_cache(out_dir)


def test_cache_resume_skips_completed(tmp_path):
    prompts_path, _, label_fn = _build_fixture(tmp_path)
    recipient, _ = _planted_pair(label_fn)
    prompts = cache_acts.select_prompts(read_jsonl(prompts_path, PromptRecord))
    out_dir = tmp_path / "acts"
    cache_acts.cache_activations(recipient, prompts, out_dir)
    assert cache_acts.cache_is_complete(out_dir, len(prompts))

    # A recipient that would raise if run again -- proves the run is skipped.
    class Exploding(FakeBackend):
        def run_with_cache(self, *a, **k):  # noqa: D401
            raise AssertionError("should have been skipped")

    exploding = Exploding("fam-instruct", N_LAYERS, D_MODEL, label_fn=label_fn)
    cache_acts.cache_activations(exploding, prompts, out_dir)  # no raise → skipped
    # ...but --force reruns.
    with pytest.raises(AssertionError):
        cache_acts.cache_activations(exploding, prompts, out_dir, force=True)


# ---------------------------------------------------------------------------
# Shard partition (disjoint + exhaustive).
# ---------------------------------------------------------------------------


def test_shard_partition_is_disjoint_and_exhaustive(tmp_path):
    prompts_path, _, _ = _build_fixture(tmp_path)
    records = read_jsonl(prompts_path, PromptRecord)
    full = cache_acts.select_prompts(records)
    n = 3
    shards = [cache_acts.select_prompts(records, shard=(i, n)) for i in range(n)]
    recombined = [p.prompt_id for shard in shards for p in shard]
    assert sorted(recombined) == sorted(p.prompt_id for p in full)
    assert len(recombined) == len(set(recombined))  # disjoint


def test_select_prompts_filters_to_raw_intentionality(tmp_path):
    prompts_path, _, _ = _build_fixture(tmp_path)
    records = read_jsonl(prompts_path, PromptRecord)
    selected = cache_acts.select_prompts(records)
    assert selected  # non-empty
    assert all(p.question_type == "intentionality" and p.format == "raw" for p in selected)


# ---------------------------------------------------------------------------
# Tokenizer / seq-alignment mismatch → hard error.
# ---------------------------------------------------------------------------


def test_tokenizer_mismatch_hard_error():
    recipient = FakeBackend("fam-instruct", N_LAYERS, D_MODEL)
    # Donor tokenizes one prompt to a different length → misalignment.
    donor = FakeBackend(
        "fam-pretrained", N_LAYERS, D_MODEL,
        tokens_fn=lambda p: len(p.split()) + (1 if p == "a b" else 0),
    )
    with pytest.raises(TokenizerMismatchError, match="tokenization mismatch"):
        recipient.run_patched(["a b"], donor, [SIGNAL_LAYER])
    # Aligned prompt still works.
    out = recipient.run_patched(["x y z"], donor, [SIGNAL_LAYER])
    assert out.shape == (1, 11)


# ---------------------------------------------------------------------------
# Capability-check hook (canned deltas).
# ---------------------------------------------------------------------------


def test_capability_check_fake_returns_canned_deltas():
    fb = FakeBackend("fam-instruct", N_LAYERS, D_MODEL)
    result = patch_mod.run_capability_check("fam-instruct", [5], backend=fb)
    assert set(("arc_easy", "hellaswag", "mmlu", "truthfulqa")).issubset(result)
    for task in ("arc_easy", "hellaswag", "mmlu", "truthfulqa"):
        entry = result[task]
        assert entry["delta"] == pytest.approx(entry["patched"] - entry["unpatched"], abs=1e-9)
    assert result["_meta"]["canned"] is True


# ---------------------------------------------------------------------------
# Layers-spec parsing (sweep / explicit / top-k).
# ---------------------------------------------------------------------------


def test_parse_layers_spec_sweep_and_explicit():
    assert patch_mod.parse_layers_spec("sweep", 4) == [[0], [1], [2], [3], [4]]
    assert patch_mod.parse_layers_spec("3,7,11", 12) == [[3, 7, 11]]


def test_parse_layers_spec_top_k(tmp_path):
    # A metrics parquet where layer 5 reduced Δ_knobe most, then 6, then 4.
    rows = [
        {"layers": "[]", "delta_knobe": 5.0},
        {"layers": "[4]", "delta_knobe": 5.0},
        {"layers": "[5]", "delta_knobe": 0.0},
        {"layers": "[6]", "delta_knobe": 2.0},
        {"layers": "[7]", "delta_knobe": 4.0},
    ]
    mp = tmp_path / "patch_metrics.parquet"
    pd.DataFrame(rows).to_parquet(mp)
    assert patch_mod.parse_layers_spec("top-k:2", N_LAYERS, mp) == [[5, 6]]


# ---------------------------------------------------------------------------
# CLI smoke: `knobe mech cache` / `knobe mech patch` with --backend fake.
# ---------------------------------------------------------------------------


def _small_registry(tmp_path: Path) -> Path:
    import yaml

    data = {
        "families": {
            "toy": {
                "pretrained": "toy/base", "finetuned": "toy/it", "tl_name": "toy/base",
                "d_model": D_MODEL, "n_layers": N_LAYERS, "role": "debug",
            }
        }
    }
    path = tmp_path / "models.yaml"
    path.write_text(yaml.safe_dump(data))
    return path


def test_cli_mech_cache_fake(tmp_path):
    from knobe.cli import main

    prompts_path, vignettes_path, _ = _build_fixture(tmp_path)
    registry = _small_registry(tmp_path)
    out_root = tmp_path / "results"
    rc = main([
        "mech", "cache", "--release", "v0.1", "--model-key", "toy-instruct",
        "--backend", "fake", "--prompts", str(prompts_path), "--vignettes", str(vignettes_path),
        "--out-root", str(out_root), "--registry", str(registry),
    ])
    assert rc == 0
    out_dir = out_root / "v0.1" / "acts" / "toy-instruct"
    assert (out_dir / cache_acts.CACHE_FILENAME).exists()
    assert (out_dir / "index.json").exists()
    assert (out_dir / "delta_l.parquet").exists()
    assert (out_dir / "delta_l.png").exists()
    df = pd.read_parquet(out_dir / "delta_l.parquet")
    assert set(df.columns) == {"model_key", "contrast", "layer", "delta", "delta_cos", "n_pos", "n_neg"}
    # Every emitted contrast is one of the declared names (incl. the
    # controlled typicality/evocativeness estimators).
    assert set(df["contrast"]).issubset(set(cache_acts.CONTRAST_NAMES))
    assert {"bad_vs_good", "typicality", "evocativeness"}.issubset(set(df["contrast"]))


def test_cli_mech_patch_fake(tmp_path):
    from knobe.cli import main

    prompts_path, vignettes_path, _ = _build_fixture(tmp_path)
    registry = _small_registry(tmp_path)
    out_root = tmp_path / "results"
    rc = main([
        "mech", "patch", "--release", "v0.1", "--family", "toy",
        "--backend", "fake", "--prompts", str(prompts_path), "--vignettes", str(vignettes_path),
        "--layers", "3,5", "--out-root", str(out_root), "--registry", str(registry),
    ])
    assert rc == 0
    out_dir = out_root / "v0.1" / "patch" / "toy"
    assert (out_dir / "patch_metrics.parquet").exists()
    assert (out_dir / "layer_baseline.jsonl").exists()
    assert (out_dir / "layer_3_5.jsonl").exists()
    metrics = pd.read_parquet(out_dir / "patch_metrics.parquet")
    assert set(metrics["layers"]) == {"[]", "[3,5]"}
    assert set(patch_mod.METRIC_COLUMNS).issubset(metrics.columns)


def test_cache_pushes_to_storage_when_configured(tmp_path):
    import yaml

    prompts_path, vignettes_path, _ = _build_fixture(tmp_path)
    registry = _small_registry(tmp_path)
    bucket = tmp_path / "bucket"
    storage_cfg = tmp_path / "storage.yaml"
    storage_cfg.write_text(yaml.safe_dump({"backend": "local", "root": str(bucket)}))

    cache_acts.run_cache(
        release="v0.1", model_key="toy-instruct", backend_name="fake",
        prompts_path=prompts_path, vignettes_path=vignettes_path,
        out_root=tmp_path / "results", registry_path=registry,
        storage_config_path=storage_cfg,
    )
    base = bucket / "acts" / "v0.1" / "toy-instruct"
    assert (base / cache_acts.CACHE_FILENAME).exists()
    assert (base / "index.json").exists()
    assert (base / "delta_l.parquet").exists()


def test_cli_mech_patch_missing_family(tmp_path):
    from knobe.cli import main

    prompts_path, vignettes_path, _ = _build_fixture(tmp_path)
    registry = _small_registry(tmp_path)
    rc = main([
        "mech", "patch", "--release", "v0.1", "--family", "nope",
        "--backend", "fake", "--prompts", str(prompts_path), "--vignettes", str(vignettes_path),
        "--registry", str(registry),
    ])
    assert rc == 1


# ---------------------------------------------------------------------------
# Registry: mech_backend field is additive + defaults.
# ---------------------------------------------------------------------------


def test_registry_mech_backend_default_and_override(tmp_path):
    import yaml

    from knobe.registry import load_registry

    data = {
        "families": {
            "a": {"pretrained": "a/b", "finetuned": "a/it", "d_model": 8, "n_layers": 4, "role": "debug"},
            "b": {"pretrained": "b/b", "finetuned": "b/it", "d_model": 8, "n_layers": 4,
                  "role": "debug", "mech_backend": "nnsight"},
        }
    }
    path = tmp_path / "models.yaml"
    path.write_text(yaml.safe_dump(data))
    reg = load_registry(path)
    assert reg["a"].mech_backend == "transformer_lens"  # default
    assert reg["b"].mech_backend == "nnsight"


def test_real_configs_models_yaml_still_valid():
    # The shipped registry (no mech_backend fields) still loads: additive.
    from knobe.registry import load_registry

    root = Path(__file__).resolve().parents[1]
    reg = load_registry(root / "configs" / "models.yaml")
    assert all(f.mech_backend == "transformer_lens" for f in reg.values())


# ---------------------------------------------------------------------------
# T10: CLI/module backend-choice parity (guards against drift between the two
# hand-maintained copies of the four backend names).
# ---------------------------------------------------------------------------


def test_cli_mech_backend_choices_match_cache_acts():
    from knobe import cli

    assert cli._MECH_BACKEND_CHOICES == cache_acts.BACKEND_CHOICES


# ---------------------------------------------------------------------------
# T10: sharded cache remote keys are per-shard distinct (no bucket clobber).
# ---------------------------------------------------------------------------


def _shard_storage_cfg(tmp_path: Path, bucket: Path, tag: str) -> Path:
    import yaml

    cfg = tmp_path / f"storage_{tag}.yaml"
    cfg.write_text(yaml.safe_dump({"backend": "local", "root": str(bucket)}))
    return cfg


def test_sharded_cache_remote_keys_are_distinct(tmp_path):
    prompts_path, vignettes_path, _ = _build_fixture(tmp_path)
    registry = _small_registry(tmp_path)
    bucket = tmp_path / "bucket"
    out_root = tmp_path / "results"
    n = 2
    for i in range(n):
        cache_acts.run_cache(
            release="v0.1", model_key="toy-instruct", backend_name="fake",
            prompts_path=prompts_path, vignettes_path=vignettes_path,
            out_root=out_root, registry_path=registry, shard=(i, n),
            storage_config_path=_shard_storage_cfg(tmp_path, bucket, str(i)),
        )
    keys = [p.relative_to(bucket).as_posix() for p in bucket.rglob("*") if p.is_file()]
    # Each shard's safetensors landed under its own shard_i_of_n segment --
    # two distinct remote keys, so concurrent shards do not clobber.
    st_keys = sorted(k for k in keys if k.endswith(cache_acts.CACHE_FILENAME))
    assert st_keys == [
        f"acts/v0.1/toy-instruct/shard_0_of_2/{cache_acts.CACHE_FILENAME}",
        f"acts/v0.1/toy-instruct/shard_1_of_2/{cache_acts.CACHE_FILENAME}",
    ]


# ---------------------------------------------------------------------------
# T10: merge_shards -- combine shard sub-caches into the top-level cache the
# probes loader consumes; validate completeness + disjointness.
# ---------------------------------------------------------------------------


def test_merge_shards_combines_and_is_probe_loadable(tmp_path):
    from knobe.mech._data import load_probe_dataset

    prompts_path, vignettes_path, _ = _build_fixture(tmp_path)
    registry = _small_registry(tmp_path)
    out_root = tmp_path / "results"
    n = 2
    for i in range(n):
        cache_acts.run_cache(
            release="v0.1", model_key="toy-instruct", backend_name="fake",
            prompts_path=prompts_path, vignettes_path=vignettes_path,
            out_root=out_root, registry_path=registry, shard=(i, n),
        )
    acts_model_dir = cache_acts.acts_dir(out_root, "v0.1", "toy-instruct")
    full = cache_acts.select_prompts(read_jsonl(prompts_path, PromptRecord))

    cache_acts.merge_shards(acts_model_dir)
    resid, index = cache_acts.read_cache(acts_model_dir)
    assert resid.shape[0] == len(full)
    assert sorted(index["prompt_ids"]) == sorted(p.prompt_id for p in full)

    # Byte/row consistency: every merged row equals the exact shard row for
    # that prompt_id.
    merged_by_pid = {pid: resid[i] for i, pid in enumerate(index["prompt_ids"])}
    for i in range(n):
        sresid, sindex = cache_acts.read_cache(acts_model_dir / f"shard_{i}_of_{n}")
        for j, pid in enumerate(sindex["prompt_ids"]):
            np.testing.assert_array_equal(merged_by_pid[pid], sresid[j])

    # Consumable by the probes loader.
    ds = load_probe_dataset(acts_model_dir, vignettes_path)
    assert ds.n_items == len(full)


def test_unsharded_delta_l_after_merge_matches_direct(tmp_path):
    # δ_l from the unsharded cache path run against a merged (shard-concatenated)
    # cache must equal the direct unsharded computation -- i.e. the skip path
    # aligns metadata to the cache's on-disk row order, not the selection order.
    prompts_path, vignettes_path, _ = _build_fixture(tmp_path)
    registry = _small_registry(tmp_path)

    ref_root = tmp_path / "ref"
    cache_acts.run_cache(
        release="v0.1", model_key="toy-instruct", backend_name="fake",
        prompts_path=prompts_path, vignettes_path=vignettes_path,
        out_root=ref_root, registry_path=registry,
    )
    ref = pd.read_parquet(cache_acts.acts_dir(ref_root, "v0.1", "toy-instruct") / "delta_l.parquet")

    m_root = tmp_path / "merged"
    n = 2
    for i in range(n):
        cache_acts.run_cache(
            release="v0.1", model_key="toy-instruct", backend_name="fake",
            prompts_path=prompts_path, vignettes_path=vignettes_path,
            out_root=m_root, registry_path=registry, shard=(i, n),
        )
    acts_model_dir = cache_acts.acts_dir(m_root, "v0.1", "toy-instruct")
    cache_acts.merge_shards(acts_model_dir)
    # Unsharded run reuses the merged cache (skip path).
    cache_acts.run_cache(
        release="v0.1", model_key="toy-instruct", backend_name="fake",
        prompts_path=prompts_path, vignettes_path=vignettes_path,
        out_root=m_root, registry_path=registry,
    )
    got = pd.read_parquet(acts_model_dir / "delta_l.parquet")

    pd.testing.assert_frame_equal(
        ref.sort_values(["contrast", "layer"]).reset_index(drop=True),
        got.sort_values(["contrast", "layer"]).reset_index(drop=True),
    )


def test_unsharded_cache_rejects_mismatched_prompt_set(tmp_path):
    # A complete-by-row-count cache whose prompt_id SET differs from the current
    # selection is a hard error on the skip path (not a scrambled δ_l).
    prompts_path, vignettes_path, _ = _build_fixture(tmp_path)
    registry = _small_registry(tmp_path)
    out_root = tmp_path / "results"
    cache_acts.run_cache(
        release="v0.1", model_key="toy-instruct", backend_name="fake",
        prompts_path=prompts_path, vignettes_path=vignettes_path,
        out_root=out_root, registry_path=registry,
    )
    # Corrupt one prompt_id in index.json (row count preserved -> still
    # "complete", so the skip path fires) so the cached set no longer matches.
    acts_model_dir = cache_acts.acts_dir(out_root, "v0.1", "toy-instruct")
    idx_path = acts_model_dir / cache_acts.INDEX_FILENAME
    idx = json.loads(idx_path.read_text())
    idx["prompt_ids"][0] = "BOGUS::intentionality::raw"
    idx_path.write_text(json.dumps(idx))
    with pytest.raises(ValueError, match="different prompt_id set"):
        cache_acts.run_cache(
            release="v0.1", model_key="toy-instruct", backend_name="fake",
            prompts_path=prompts_path, vignettes_path=vignettes_path,
            out_root=out_root, registry_path=registry,
        )


def test_merge_shards_errors_on_missing_shard(tmp_path):
    prompts_path, vignettes_path, _ = _build_fixture(tmp_path)
    registry = _small_registry(tmp_path)
    out_root = tmp_path / "results"
    # Only shard 0 of 2 written.
    cache_acts.run_cache(
        release="v0.1", model_key="toy-instruct", backend_name="fake",
        prompts_path=prompts_path, vignettes_path=vignettes_path,
        out_root=out_root, registry_path=registry, shard=(0, 2),
    )
    acts_model_dir = cache_acts.acts_dir(out_root, "v0.1", "toy-instruct")
    with pytest.raises(ValueError, match="missing shard"):
        cache_acts.merge_shards(acts_model_dir)


def test_merge_shards_errors_on_duplicate_rows(tmp_path):
    d = tmp_path / "acts" / "m"
    meta = {"model_key": "m", "layers": [0, 1], "positions": ["final"], "n_layers": 1, "d_model": D_MODEL}
    a = np.zeros((2, 2, D_MODEL), dtype=np.float16)
    cache_acts.write_cache(a, ["p1::intentionality::raw", "p2::intentionality::raw"], d / "shard_0_of_2", meta)
    cache_acts.write_cache(a, ["p2::intentionality::raw", "p3::intentionality::raw"], d / "shard_1_of_2", meta)
    with pytest.raises(ValueError, match="duplicate prompt_id"):
        cache_acts.merge_shards(d)


def test_cli_mech_cache_merge_shards(tmp_path):
    from knobe.cli import main

    prompts_path, vignettes_path, _ = _build_fixture(tmp_path)
    registry = _small_registry(tmp_path)
    out_root = tmp_path / "results"
    n = 2
    for i in range(n):
        cache_acts.run_cache(
            release="v0.1", model_key="toy-instruct", backend_name="fake",
            prompts_path=prompts_path, vignettes_path=vignettes_path,
            out_root=out_root, registry_path=registry, shard=(i, n),
        )
    rc = main([
        "mech", "cache", "--release", "v0.1", "--model-key", "toy-instruct",
        "--backend", "fake", "--prompts", str(prompts_path), "--vignettes", str(vignettes_path),
        "--out-root", str(out_root), "--registry", str(registry), "--merge-shards",
    ])
    assert rc == 0
    acts_model_dir = cache_acts.acts_dir(out_root, "v0.1", "toy-instruct")
    assert (acts_model_dir / cache_acts.CACHE_FILENAME).exists()
    assert (acts_model_dir / cache_acts.INDEX_FILENAME).exists()


# ---------------------------------------------------------------------------
# T10: patch sweep resume + storage sync (spec §1(b)/§1.1).
# ---------------------------------------------------------------------------


class _Counting(FakeBackend):
    """FakeBackend that tallies backend forward calls, to prove resume skips."""

    def __init__(self, *a, calls=None, **k):
        super().__init__(*a, **k)
        self._calls = calls if calls is not None else {"logits": 0, "patched": 0}

    def logits_0_10(self, texts):
        self._calls["logits"] += 1
        return super().logits_0_10(texts)

    def run_patched(self, texts, donor, layers):
        self._calls["patched"] += 1
        return super().run_patched(texts, donor, layers)


def test_patch_sweep_resume_skips_completed_configs(tmp_path):
    prompts_path, vignettes_path, label_fn = _build_fixture(tmp_path)
    recipient, donor = _planted_pair(label_fn)
    vignettes = read_csv_validated(vignettes_path, VignetteRow)
    prompts = cache_acts.select_prompts(read_jsonl(prompts_path, PromptRecord))
    out_dir = tmp_path / "patch" / "fam"
    configs = [[3], [5]]

    m1 = patch_mod.run_sweep(recipient, donor, prompts, vignettes, configs, "fam", out_dir)

    calls = {"logits": 0, "patched": 0}
    recipient2 = _Counting(
        "fam-instruct", N_LAYERS, D_MODEL, label_fn=label_fn,
        planted=PlantedSignal(layer=SIGNAL_LAYER, magnitude=1.0), calls=calls,
    )
    m2 = patch_mod.run_sweep(recipient2, donor, prompts, vignettes, configs, "fam", out_dir)
    # baseline + [3] + [5] all complete on disk -> zero backend forwards.
    assert calls == {"logits": 0, "patched": 0}
    pd.testing.assert_frame_equal(m1.reset_index(drop=True), m2.reset_index(drop=True))


def test_patch_sweep_recomputes_incomplete_config(tmp_path):
    prompts_path, vignettes_path, label_fn = _build_fixture(tmp_path)
    recipient, donor = _planted_pair(label_fn)
    vignettes = read_csv_validated(vignettes_path, VignetteRow)
    prompts = cache_acts.select_prompts(read_jsonl(prompts_path, PromptRecord))
    out_dir = tmp_path / "patch" / "fam"
    configs = [[3], [5]]
    patch_mod.run_sweep(recipient, donor, prompts, vignettes, configs, "fam", out_dir)

    # Truncate one config's file to a single row -> incomplete.
    fp = out_dir / "layer_5.jsonl"
    first_line = fp.read_text().splitlines()[0]
    fp.write_text(first_line + "\n")

    calls = {"logits": 0, "patched": 0}
    recipient2 = _Counting(
        "fam-instruct", N_LAYERS, D_MODEL, label_fn=label_fn,
        planted=PlantedSignal(layer=SIGNAL_LAYER, magnitude=1.0), calls=calls,
    )
    # Donor must share the recipient's backend implementation (spec §5.5).
    donor2 = _Counting("fam-pretrained", N_LAYERS, D_MODEL, label_fn=label_fn)
    patch_mod.run_sweep(recipient2, donor2, prompts, vignettes, configs, "fam", out_dir)
    # Only layer_5 redone (one run_patched); baseline + [3] skipped.
    assert calls == {"logits": 0, "patched": 1}
    recs = read_jsonl(fp, PatchRecord)
    assert len(recs) == len(prompts)


def test_read_complete_ev_recomputes_on_null_rating(tmp_path):
    # A record with a null parsed_rating (corrupt/interrupted write) must yield
    # a clean recompute (None), not a float(None) crash.
    prompt_ids = ["a::intentionality::raw", "b::intentionality::raw"]
    lp = np.zeros((2, 11))
    ev = np.array([5.0, 6.0])
    recs = patch_mod._patch_records(prompt_ids, "m", lp, ev, [5], "rev")
    fp = tmp_path / "layer_5.jsonl"
    patch_mod.write_patch_records(recs, fp)
    assert patch_mod._read_complete_ev(fp, prompt_ids) is not None

    recs2 = list(recs)
    recs2[0] = recs2[0].model_copy(update={"parsed_rating": None})
    patch_mod.write_patch_records(recs2, fp)
    assert patch_mod._read_complete_ev(fp, prompt_ids) is None


def test_patch_sweep_pushes_to_storage(tmp_path):
    from knobe.storage import LocalDirStorage

    prompts_path, vignettes_path, label_fn = _build_fixture(tmp_path)
    recipient, donor = _planted_pair(label_fn)
    vignettes = read_csv_validated(vignettes_path, VignetteRow)
    prompts = cache_acts.select_prompts(read_jsonl(prompts_path, PromptRecord))
    out_dir = tmp_path / "patch" / "fam"
    bucket = tmp_path / "bucket"
    storage = LocalDirStorage(bucket)

    patch_mod.run_sweep(
        recipient, donor, prompts, vignettes, [[5]], "fam", out_dir,
        storage=storage, remote_base="patch/v0.1/fam",
    )
    base = bucket / "patch" / "v0.1" / "fam"
    assert (base / "layer_baseline.jsonl").exists()
    assert (base / "layer_5.jsonl").exists()
    assert (base / "patch_metrics.parquet").exists()
