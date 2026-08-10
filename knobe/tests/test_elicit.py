"""Tests for src/knobe/elicit_vllm.py (WO-5): the behavioral elicitation
runner. Every test uses FakeEngine (deterministic, sha256-based) --
torch/vllm are never imported at test time (VllmEngine/HfEngine's guarded
imports are only exercised implicitly by their constructors raising
RuntimeError when the optional extra isn't installed).

Acceptance criteria under test (task-5-brief.md / WO5_behavioral_h200.md):
  - Manifest guard: tampered/missing manifest.json -> refusal; correct
    manifest -> passes; --skip-manifest-check bypasses with a loud warning.
  - Resume set-difference (via jobs.diff_jobs, reused directly).
  - Parsing incl. the multi-token "10" path: FakeEngine's "single" and
    "split" token_mode both exercised, at the unit level AND inside a full
    run_elicit() pipeline.
  - Storage sync: LocalDirStorage receives shards at checkpoint intervals
    (not just a single final dump) and at a simulated crash via signal.
  - Shard partition: disjoint, exhaustive.
  - Integration (FakeEngine): 20 items x 2 questions x N=3 -> 100% of jobs
    present; re-run reproduces identical raw_response strings; kill/restart
    (two separate OS subprocesses, like test_curate.py's
    TestCLIResumeAcrossProcesses) -> final results.jsonl row-set identical
    to an uninterrupted run; logprobs_0_10 populated on every row.
"""
from __future__ import annotations

import json
import os
import signal as signal_module
import subprocess
import sys
import time as time_module
from pathlib import Path

import pytest
import yaml

from knobe import elicit_vllm, jobs as jobs_mod, storage
from knobe.parsing import expected_rating_from_logprobs
from knobe.registry import Family, load_registry
from knobe.schemas import (
    FileManifestEntry,
    JobRecord,
    PromptRecord,
    ReleaseCounts,
    ReleaseManifest,
    ResultRecord,
    read_jsonl,
    sha256_for_text,
    write_jsonl,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
MODELS_YAML = REPO_ROOT / "configs" / "models.yaml"


# ---------------------------------------------------------------------------
# Fixture builders
# ---------------------------------------------------------------------------


def _prompt(prompt_id: str, variant_id: str, question_type: str, fmt: str, text: str) -> PromptRecord:
    if fmt == "chat":
        messages = [{"role": "user", "content": text}]
        from knobe.schemas import sha256_for_messages

        return PromptRecord(
            prompt_id=prompt_id, variant_id=variant_id, question_type=question_type,
            format=fmt, text=text, messages=messages, sha256=sha256_for_messages(messages),
        )
    return PromptRecord(
        prompt_id=prompt_id, variant_id=variant_id, question_type=question_type,
        format=fmt, text=text, messages=None, sha256=sha256_for_text(text),
    )


def _toy_prompts(n_items: int, questions: list[str], fmt: str = "raw") -> list[PromptRecord]:
    prompts = []
    for i in range(n_items):
        variant_id = f"TST-MB-{i:02d}-A"
        for q in questions:
            prompt_id = f"{variant_id}::{q}::{fmt}"
            text = f"Read carefully the following scenario... item {i} question {q}\nAnswer:"
            prompts.append(_prompt(prompt_id, variant_id, q, fmt, text))
    return prompts


def _write_run_config(path: Path, *, release: str, models: list[str], formats: list[str],
                       n_samples: int, questions: list[str],
                       logit_fallback_checkpoints: list[str] | None = None) -> None:
    data = {
        "release": release, "models": models, "formats": formats,
        "n_samples": n_samples, "questions": questions,
    }
    if logit_fallback_checkpoints is not None:
        data["logit_fallback_checkpoints"] = logit_fallback_checkpoints
    path.write_text(yaml.safe_dump(data))


def _write_release(release_root: Path, release: str, files: dict[str, bytes]) -> Path:
    """Writes a minimal, self-consistent data/release/<release>/ directory
    (manifest.json + arbitrary named files), for manifest-guard tests."""
    release_dir = release_root / release
    release_dir.mkdir(parents=True)
    import hashlib

    entries = {}
    for name, content in files.items():
        (release_dir / name).write_bytes(content)
        entries[name] = FileManifestEntry(sha256=hashlib.sha256(content).hexdigest(), rows=1)
    manifest = ReleaseManifest(
        release=release, created="2026-01-01T00:00:00Z", git_commit="deadbeef",
        files=entries, counts=ReleaseCounts(families=1, variants=1, by_valence={}, by_domain={}),
        gates_passed=[], changelog="",
    )
    (release_dir / "manifest.json").write_text(manifest.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return release_dir


# ---------------------------------------------------------------------------
# EngineRequest validation
# ---------------------------------------------------------------------------


class TestEngineRequest:
    def test_requires_exactly_one_of_text_messages(self):
        with pytest.raises(ValueError):
            elicit_vllm.EngineRequest(job_id="j", prompt_id="p", temperature=1.0, seed=1)  # neither
        with pytest.raises(ValueError):
            elicit_vllm.EngineRequest(
                job_id="j", prompt_id="p", temperature=1.0, seed=1,
                text="x", messages=[{"role": "user", "content": "x"}],  # both
            )

    def test_text_only_ok(self):
        req = elicit_vllm.EngineRequest(job_id="j", prompt_id="p", temperature=1.0, seed=1, text="x")
        assert req.text == "x"

    def test_messages_only_ok(self):
        req = elicit_vllm.EngineRequest(
            job_id="j", prompt_id="p", temperature=1.0, seed=1,
            messages=[{"role": "user", "content": "x"}],
        )
        assert req.messages is not None


# ---------------------------------------------------------------------------
# FakeEngine: determinism + the two token-mode logprob code paths
# ---------------------------------------------------------------------------


class TestFakeEngineDeterminism:
    def test_same_prompt_and_seed_same_response_across_instances(self):
        req = elicit_vllm.EngineRequest(job_id="j", prompt_id="p", temperature=0.9, seed=42, text="hello")
        r1 = elicit_vllm.FakeEngine().generate([req])[0]
        r2 = elicit_vllm.FakeEngine().generate([req])[0]
        assert r1.raw_response == r2.raw_response
        assert r1.logprobs_0_10 == r2.logprobs_0_10

    def test_different_seed_can_differ(self):
        engine = elicit_vllm.FakeEngine()
        texts = {
            engine.generate([elicit_vllm.EngineRequest(job_id=str(s), prompt_id="p", temperature=1.0, seed=s, text="x")])[0].raw_response
            for s in range(30)
        }
        assert len(texts) > 1

    def test_temperature_does_not_affect_determinism(self):
        """FakeEngine is a pure test vehicle -- it deliberately ignores
        temperature (unlike a real stochastic engine) so tests stay
        reproducible regardless of the manifest's per-job temperature."""
        req_a = elicit_vllm.EngineRequest(job_id="j", prompt_id="p", temperature=0.85, seed=7, text="x")
        req_b = elicit_vllm.EngineRequest(job_id="j", prompt_id="p", temperature=1.15, seed=7, text="x")
        ra = elicit_vllm.FakeEngine().generate([req_a])[0]
        rb = elicit_vllm.FakeEngine().generate([req_b])[0]
        assert ra.raw_response == rb.raw_response

    def test_want_first_token_logprobs_false_gives_none(self):
        req = elicit_vllm.EngineRequest(
            job_id="j", prompt_id="p", temperature=1.0, seed=1, text="x", want_first_token_logprobs=False,
        )
        resp = elicit_vllm.FakeEngine().generate([req])[0]
        assert resp.logprobs_0_10 is None

    def test_load_returns_fake_revision_and_records_call(self):
        engine = elicit_vllm.FakeEngine()
        revision = engine.load("org/model", revision="v2")
        assert revision == "fake"
        assert engine.load_calls == [("org/model", "v2")]


class TestFakeEngineLogprobsSingleToken:
    def test_every_response_has_11_logprobs(self):
        engine = elicit_vllm.FakeEngine(token_mode="single")
        for seed in range(20):
            req = elicit_vllm.EngineRequest(job_id="j", prompt_id="p", temperature=1.0, seed=seed, text="x")
            resp = engine.generate([req])[0]
            assert len(resp.logprobs_0_10) == 11

    def test_argmax_matches_raw_response_digit(self):
        engine = elicit_vllm.FakeEngine(token_mode="single")
        for seed in range(20):
            req = elicit_vllm.EngineRequest(job_id="j", prompt_id="p", temperature=1.0, seed=seed, text="x")
            resp = engine.generate([req])[0]
            argmax_idx = max(range(11), key=lambda i: resp.logprobs_0_10[i])
            assert argmax_idx == int(resp.raw_response)

    def test_expected_value_close_to_generated_rating(self):
        """Sanity-check the renormalized-EV of the fake distribution lands
        near the token it actually generated -- proves the fake logprobs
        aren't just noise unrelated to raw_response."""
        engine = elicit_vllm.FakeEngine(token_mode="single")
        req = elicit_vllm.EngineRequest(job_id="j", prompt_id="p", temperature=1.0, seed=3, text="x")
        resp = engine.generate([req])[0]
        ev = expected_rating_from_logprobs(resp.logprobs_0_10)
        assert abs(ev - int(resp.raw_response)) < 0.5


class TestFakeEngineLogprobsSplitToken:
    """WO-5 requirement 3's multi-token "10" handling -- the split
    token_mode BOTH exercises ratings 0-9 (single-token, straight off
    position 0) and rating 10 (the joint two-call computation) in the same
    test sweep, per the self-review requirement that both code paths be
    hit by FakeEngine."""

    def _find_seed_for_rating(self, target_rating: int, *, limit: int = 500) -> int:
        for seed in range(limit):
            req = elicit_vllm.EngineRequest(job_id="j", prompt_id="p", temperature=1.0, seed=seed, text="x")
            rating = elicit_vllm._rating_from_material(elicit_vllm._request_material(req))
            if rating == target_rating:
                return seed
        raise AssertionError(f"no seed in range({limit}) produced rating {target_rating}")

    def test_every_response_has_11_finite_logprobs(self):
        engine = elicit_vllm.FakeEngine(token_mode="split")
        for seed in range(20):
            req = elicit_vllm.EngineRequest(job_id="j", prompt_id="p", temperature=1.0, seed=seed, text="x")
            resp = engine.generate([req])[0]
            assert len(resp.logprobs_0_10) == 11
            assert all(lp > float("-inf") for lp in resp.logprobs_0_10)

    def test_single_digit_ratings_read_straight_off_position_0(self):
        engine = elicit_vllm.FakeEngine(token_mode="split")
        seed = self._find_seed_for_rating(4)
        req = elicit_vllm.EngineRequest(job_id="j", prompt_id="p", temperature=1.0, seed=seed, text="x")
        resp = engine.generate([req])[0]
        assert resp.raw_response == "4"
        argmax_idx = max(range(11), key=lambda i: resp.logprobs_0_10[i])
        assert argmax_idx == 4

    def test_rating_10_uses_joint_two_call_computation(self):
        engine = elicit_vllm.FakeEngine(token_mode="split")
        seed = self._find_seed_for_rating(10)
        req = elicit_vllm.EngineRequest(job_id="j", prompt_id="p", temperature=1.0, seed=seed, text="x")
        resp = engine.generate([req])[0]
        assert resp.raw_response == "10"

        # log P("10") = log P(t0="1") * P(t1="0"|t0="1"), i.e. in log-space
        # index10 = index1 + (a second, independently-derived logprob that
        # is always <= 0) -- a joint can never exceed one of its own
        # factors, so index 10 must be <= index 1 (both are boosted near
        # certainty here), while still being clearly the runner-up: well
        # above every OTHER (unboosted) digit's background logprob. This
        # is exactly what the two-call joint computation should produce.
        assert resp.logprobs_0_10[10] <= resp.logprobs_0_10[1]
        background = [resp.logprobs_0_10[i] for i in range(10) if i != 1]
        assert resp.logprobs_0_10[10] > max(background)

        # The joint really is a SUM in log-space of two independently-
        # derived logprobs (not just a copy of index 1's value) -- pin
        # that it differs from the raw index-1 (rating "1") logprob.
        assert resp.logprobs_0_10[10] != resp.logprobs_0_10[1]

    def test_split_mode_never_puts_a_single_token_at_index_10_directly(self):
        """Regression guard: in split mode, index 10 must come from the
        two-call joint, not from a (nonexistent, for this fake tokenizer)
        single "10" token lookup -- pinned by checking the joint value
        equals logprobs0[1] + logprobs1[0] exactly, recomputed independently
        here."""
        engine = elicit_vllm.FakeEngine(token_mode="split")
        seed = self._find_seed_for_rating(10)
        req = elicit_vllm.EngineRequest(job_id="j", prompt_id="p", temperature=1.0, seed=seed, text="x")
        material = elicit_vllm._request_material(req)
        rating = elicit_vllm._rating_from_material(material)
        assert rating == 10
        expected = engine._split_token_logprobs(material, rating)
        resp = engine.generate([req])[0]
        assert resp.logprobs_0_10 == expected


# ---------------------------------------------------------------------------
# resolve_model_id
# ---------------------------------------------------------------------------


class TestResolveModelId:
    def test_pretrained_and_finetuned_resolve(self):
        registry = load_registry(MODELS_YAML)
        model_id, family_name, revision = elicit_vllm.resolve_model_id("gemma-2-2b-pretrained", registry)
        assert model_id == "google/gemma-2-2b"
        assert family_name == "gemma-2-2b"
        assert revision == "main"

        model_id2, _, _ = elicit_vllm.resolve_model_id("gemma-2-2b-instruct", registry)
        assert model_id2 == "google/gemma-2-2b-it"

    def test_unknown_model_key_raises(self):
        registry = load_registry(MODELS_YAML)
        with pytest.raises(ValueError, match="does not match any family"):
            elicit_vllm.resolve_model_id("totally-bogus-model-key", registry)

    def test_family_missing_checkpoint_raises(self):
        registry = {
            "foo": Family(
                pretrained=None, finetuned="org/foo-instruct", tl_name=None,
                d_model=10, n_layers=1, role="debug",
            )
        }
        with pytest.raises(ValueError, match="no pretrained checkpoint"):
            elicit_vllm.resolve_model_id("foo-pretrained", registry)


# ---------------------------------------------------------------------------
# Manifest guard (spec §3.10)
# ---------------------------------------------------------------------------


class TestManifestGuard:
    def test_matching_manifest_passes(self, tmp_path):
        release_root = tmp_path / "release"
        _write_release(release_root, "v9.9", {"vignettes.csv": b"a,b\n1,2\n"})
        elicit_vllm.verify_release_manifest("v9.9", release_root)  # must not raise

    def test_tampered_file_refused(self, tmp_path):
        release_root = tmp_path / "release"
        release_dir = _write_release(release_root, "v9.9", {"vignettes.csv": b"a,b\n1,2\n"})
        (release_dir / "vignettes.csv").write_bytes(b"TAMPERED")
        with pytest.raises(elicit_vllm.ManifestGuardError, match="sha256 mismatch"):
            elicit_vllm.verify_release_manifest("v9.9", release_root)

    def test_missing_manifest_refused(self, tmp_path):
        release_root = tmp_path / "release"
        release_root.mkdir()
        with pytest.raises(elicit_vllm.ManifestGuardError, match="does not exist"):
            elicit_vllm.verify_release_manifest("v9.9", release_root)

    def test_missing_listed_file_refused(self, tmp_path):
        release_root = tmp_path / "release"
        release_dir = _write_release(release_root, "v9.9", {"vignettes.csv": b"a,b\n1,2\n"})
        (release_dir / "vignettes.csv").unlink()
        with pytest.raises(elicit_vllm.ManifestGuardError, match="missing"):
            elicit_vllm.verify_release_manifest("v9.9", release_root)

    def test_wrong_release_name_in_manifest_refused(self, tmp_path):
        release_root = tmp_path / "release"
        _write_release(release_root, "v9.9", {"vignettes.csv": b"x"})
        # Rename the directory so verify looks for "v9.10" but the
        # manifest inside still declares "v9.9".
        (release_root / "v9.9").rename(release_root / "v9.10")
        with pytest.raises(elicit_vllm.ManifestGuardError, match="declares release"):
            elicit_vllm.verify_release_manifest("v9.10", release_root)

    def test_run_honors_custom_release_root(self, tmp_path):
        """The CLI wrapper (run) must forward release_root to run_elicit so a
        wheel-installed knobe can verify a release dir shipped alongside the
        job data (the on-cluster main-run layout) -- with the guard ON."""
        prompts = _toy_prompts(2, ["intentionality"])
        prompts_path = tmp_path / "prompts.jsonl"
        write_jsonl(prompts, prompts_path)
        built_jobs = jobs_mod.build_jobs(
            prompts, release="v9.9", models=["gemma-2-2b-pretrained"], formats=["raw"],
            questions=["intentionality"], n_samples=1,
        )
        jobs_path = tmp_path / "jobs.jsonl"
        jobs_mod.write_jobs_jsonl(built_jobs, jobs_path)
        run_config_path = tmp_path / "run.yaml"
        _write_run_config(
            run_config_path, release="v9.9", models=["gemma-2-2b-pretrained"], formats=["raw"],
            n_samples=1, questions=["intentionality"],
        )
        release_root = tmp_path / "release"
        _write_release(release_root, "v9.9", {"vignettes.csv": b"a,b\n1,2\n"})

        # Without release_root the guard must refuse (v9.9 is not in the
        # repo's own data/release/); with it, the run must succeed.
        rc_missing = elicit_vllm.run(
            jobs_path=jobs_path, prompts_path=prompts_path, run_config_path=run_config_path,
            out_path=tmp_path / "r1.jsonl", engine_name="fake", registry_path=MODELS_YAML,
        )
        assert rc_missing == 1
        rc = elicit_vllm.run(
            jobs_path=jobs_path, prompts_path=prompts_path, run_config_path=run_config_path,
            out_path=tmp_path / "r2.jsonl", engine_name="fake", registry_path=MODELS_YAML,
            release_root=release_root,
        )
        assert rc == 0
        assert len(read_jsonl(tmp_path / "r2.jsonl", ResultRecord)) == len(built_jobs)


# ---------------------------------------------------------------------------
# Sharding
# ---------------------------------------------------------------------------


def _job(job_id: str, prompt_id: str = "p", model_key: str = "m", sample_idx: int = 0) -> JobRecord:
    return JobRecord(job_id=job_id, prompt_id=prompt_id, model_key=model_key, sample_idx=sample_idx, temperature=1.0, seed=1)


class TestShardJobs:
    def test_no_shard_returns_everything(self):
        jobs_list = [_job(f"j{i}") for i in range(5)]
        assert elicit_vllm.shard_jobs(jobs_list, None) == jobs_list

    def test_disjoint_and_exhaustive(self):
        jobs_list = [_job(f"j{i}") for i in range(23)]
        shards = [elicit_vllm.shard_jobs(jobs_list, (i, 4)) for i in range(4)]
        recombined = sorted((j.job_id for shard in shards for j in shard))
        assert recombined == sorted(j.job_id for j in jobs_list)
        seen = set()
        for shard in shards:
            for j in shard:
                assert j.job_id not in seen
                seen.add(j.job_id)

    def test_deterministic_job_index_assignment(self):
        jobs_list = [_job(f"j{i}") for i in range(6)]
        shard0 = elicit_vllm.shard_jobs(jobs_list, (0, 3))
        assert [j.job_id for j in shard0] == ["j0", "j3"]

    def test_out_of_range_shard_rejected(self):
        with pytest.raises(ValueError):
            elicit_vllm.shard_jobs([_job("j0")], (4, 4))


# ---------------------------------------------------------------------------
# Storage restore-fresher-of-local-or-remote
# ---------------------------------------------------------------------------


class TestRestoreCompletedResults:
    def test_local_ahead_of_remote_stays_local(self, tmp_path):
        out_path = tmp_path / "results.jsonl"
        out_path.write_text('{"a":1}\n{"a":2}\n{"a":3}\n{"a":4}\n{"a":5}\n')
        store = storage.LocalDirStorage(tmp_path / "bucket")
        remote = tmp_path / "remote_src.jsonl"
        remote.write_text('{"a":1}\n{"a":2}\n')
        store.push(remote, "k")

        elicit_vllm.restore_completed_results(out_path, store, "k")
        assert len(out_path.read_text().splitlines()) == 5

    def test_remote_ahead_of_local_replaces_local(self, tmp_path):
        out_path = tmp_path / "results.jsonl"
        out_path.write_text('{"a":1}\n')
        store = storage.LocalDirStorage(tmp_path / "bucket")
        remote = tmp_path / "remote_src.jsonl"
        remote.write_text('{"a":1}\n{"a":2}\n{"a":3}\n')
        store.push(remote, "k")

        elicit_vllm.restore_completed_results(out_path, store, "k")
        assert len(out_path.read_text().splitlines()) == 3

    def test_no_local_file_restores_entirely_from_remote(self, tmp_path):
        out_path = tmp_path / "results.jsonl"  # never created
        store = storage.LocalDirStorage(tmp_path / "bucket")
        remote = tmp_path / "remote_src.jsonl"
        remote.write_text('{"a":1}\n{"a":2}\n')
        store.push(remote, "k")

        elicit_vllm.restore_completed_results(out_path, store, "k")
        assert len(out_path.read_text().splitlines()) == 2

    def test_no_remote_object_leaves_local_untouched(self, tmp_path):
        out_path = tmp_path / "results.jsonl"
        out_path.write_text('{"a":1}\n')
        store = storage.LocalDirStorage(tmp_path / "bucket")

        elicit_vllm.restore_completed_results(out_path, store, "does-not-exist")
        assert out_path.read_text() == '{"a":1}\n'

    def test_no_remote_no_local_is_a_noop(self, tmp_path):
        out_path = tmp_path / "results.jsonl"
        store = storage.LocalDirStorage(tmp_path / "bucket")
        elicit_vllm.restore_completed_results(out_path, store, "k")  # must not raise
        assert not out_path.exists()


# ---------------------------------------------------------------------------
# read_results_tolerating_torn_tail -- Important reviewer fix: a real
# SIGKILL can leave a partial/invalid trailing line on disk; resume must
# tolerate (and repair) that without treating it as real corruption.
# ---------------------------------------------------------------------------


def _valid_result_line(**overrides) -> str:
    kwargs = dict(
        job_id="j1", prompt_id="p1", model_key="m", sample_idx=0,
        temperature=1.0, seed=1, raw_response="7", parsed_rating=7,
        parse_ok=True, parse_method="regex", logprobs_0_10=None,
        model_revision="fake", runner_version="v", timestamp=1.0,
    )
    kwargs.update(overrides)
    return ResultRecord(**kwargs).model_dump_json()


class TestReadResultsTolerantOfTornTail:
    def test_torn_trailing_line_dropped_and_file_repaired(self, tmp_path):
        path = tmp_path / "results.jsonl"
        good = _valid_result_line(job_id="j1")
        torn = '{"job_id": "j2", "raw_respo'  # deliberately truncated, no closing brace/newline
        path.write_text(good + "\n" + torn)

        results = elicit_vllm.read_results_tolerating_torn_tail(path)
        assert [r.job_id for r in results] == ["j1"]

        # File is REPAIRED (torn bytes don't linger to corrupt a later append).
        lines = path.read_text().splitlines()
        assert len(lines) == 1
        assert "j2" not in path.read_text()

        # Idempotent: reading the now-clean file again gives the same result.
        results2 = elicit_vllm.read_results_tolerating_torn_tail(path)
        assert [r.job_id for r in results2] == ["j1"]

    def test_torn_line_in_the_middle_is_a_hard_error_not_silently_dropped(self, tmp_path):
        path = tmp_path / "results.jsonl"
        broken_mid_file = '{"totally broken, not the last line'
        path.write_text(broken_mid_file + "\n" + _valid_result_line(job_id="j2") + "\n")
        with pytest.raises(ValueError, match="NOT the trailing line"):
            elicit_vllm.read_results_tolerating_torn_tail(path)

    def test_fully_valid_file_is_unaffected_and_not_rewritten(self, tmp_path):
        path = tmp_path / "results.jsonl"
        content = _valid_result_line(job_id="j1") + "\n" + _valid_result_line(job_id="j2") + "\n"
        path.write_text(content)

        results = elicit_vllm.read_results_tolerating_torn_tail(path)
        assert {r.job_id for r in results} == {"j1", "j2"}
        assert path.read_text() == content  # untouched -- nothing torn, no repair needed

    def test_missing_file_returns_empty(self, tmp_path):
        assert elicit_vllm.read_results_tolerating_torn_tail(tmp_path / "does_not_exist.jsonl") == []

    def test_candidate_tail_ids_survives_sentencepiece_boundary(self):
        """Regression (Mistral flat-logprobs bug, main runs v1.0/v1.1,
        found 2026-08-09): SentencePiece-family tokenizers encode a bare
        candidate ("7") as a word-boundary piece with a DIFFERENT id than
        the same digit realized in-context after "Answer:". Candidate ids
        must therefore come from the in-context diff of encode(forced) vs
        encode(prompt), never from a standalone encode(candidate)."""

        class SentencePieceLike:
            BOUNDARY_SEVEN = 901   # id of "_7" (standalone, word-initial)
            PLAIN_SEVEN = 55       # id of "7" realized mid-word after ":"

            def encode(self, text, add_special_tokens=True):
                ids = [1] if add_special_tokens else []  # BOS
                if text == "7":
                    return ids + [self.BOUNDARY_SEVEN]
                if text.endswith("Answer:7"):
                    return ids + [10, 11, self.PLAIN_SEVEN]
                if text.endswith("Answer:"):
                    return ids + [10, 11]
                raise AssertionError(f"unexpected: {text!r}")

        tok = SentencePieceLike()
        prompt = "Scenario...\nAnswer:"
        tail = elicit_vllm.candidate_tail_ids(tok, prompt, prompt + "7")
        assert tail == [SentencePieceLike.PLAIN_SEVEN]
        # The old (buggy) approach would have produced the boundary id:
        assert tok.encode("7", add_special_tokens=False) == [SentencePieceLike.BOUNDARY_SEVEN]

    def test_unicode_line_separator_in_raw_response_is_not_misread_as_corruption(self, tmp_path):
        """Regression (main-run job 42, 2026-08-05): pydantic serializes
        non-ASCII raw, so a completion containing U+2028/U+0085 puts a
        literal unicode line separator INSIDE a legal-JSON string. A
        splitlines()-based loader shreds that record into two invalid
        fragments and raises the mid-file-corruption error on a file the
        line-oriented repair pass (correctly) considers clean. The loader
        must split on \\n only and hand the record back intact."""
        from knobe.schemas import ResultRecord

        weird = ResultRecord(
            job_id="ENV-MB-00-A::intentionality::raw::llama-3.1-8b-instruct::0",
            prompt_id="ENV-MB-00-A::intentionality::raw", model_key="llama-3.1-8b-instruct",
            sample_idx=0, temperature=1.0, seed=1,
            raw_response="7 because the managerknew",
            parsed_rating=7, parse_ok=True, parse_method="regex",
            model_revision="x", runner_version="t", timestamp=0.0,
        )
        path = tmp_path / "results.jsonl"
        path.write_text(
            weird.model_dump_json() + "\n" + _valid_result_line(job_id="j2") + "\n",
            encoding="utf-8",
        )
        # Precondition making the regression real: the serialized record
        # must actually contain the raw separator (not an escape sequence).
        assert " " in path.read_text(encoding="utf-8")

        results = elicit_vllm.read_results_tolerating_torn_tail(path)
        assert [r.job_id for r in results] == [weird.job_id, "j2"]
        assert results[0].raw_response == "7 because the managerknew"

    def test_empty_file_returns_empty(self, tmp_path):
        path = tmp_path / "results.jsonl"
        path.write_text("")
        assert elicit_vllm.read_results_tolerating_torn_tail(path) == []

    def test_lone_torn_line_repairs_to_an_empty_file(self, tmp_path):
        path = tmp_path / "results.jsonl"
        path.write_text('{"job_id": "only", "broken')
        results = elicit_vllm.read_results_tolerating_torn_tail(path)
        assert results == []
        assert path.read_text() == ""

    def test_run_elicit_resumes_cleanly_after_a_torn_trailing_line(self, tmp_path):
        """End-to-end: run_elicit itself (not just the loader function in
        isolation) must resume correctly when out_path has a torn tail --
        the torn job gets redone, nothing else is lost or duplicated."""
        prompts = _toy_prompts(4, ["intentionality"])
        prompts_path = tmp_path / "prompts.jsonl"
        write_jsonl(prompts, prompts_path)
        built_jobs = jobs_mod.build_jobs(
            prompts, release="v1.0", models=["gemma-2-2b-pretrained"], formats=["raw"],
            questions=["intentionality"], n_samples=1,
        )
        jobs_path = tmp_path / "jobs.jsonl"
        jobs_mod.write_jobs_jsonl(built_jobs, jobs_path)
        run_config_path = tmp_path / "run.yaml"
        _write_run_config(
            run_config_path, release="v1.0", models=["gemma-2-2b-pretrained"], formats=["raw"],
            n_samples=1, questions=["intentionality"],
        )
        out_path = tmp_path / "results.jsonl"

        # Simulate a crash: 2 clean rows, then a torn one.
        good_lines = [
            _valid_result_line(job_id=built_jobs[0].job_id, prompt_id=built_jobs[0].prompt_id,
                                model_key=built_jobs[0].model_key, sample_idx=built_jobs[0].sample_idx,
                                temperature=built_jobs[0].temperature, seed=built_jobs[0].seed),
            _valid_result_line(job_id=built_jobs[1].job_id, prompt_id=built_jobs[1].prompt_id,
                                model_key=built_jobs[1].model_key, sample_idx=built_jobs[1].sample_idx,
                                temperature=built_jobs[1].temperature, seed=built_jobs[1].seed),
        ]
        torn = f'{{"job_id": "{built_jobs[2].job_id}", "raw_respo'
        out_path.write_text("\n".join(good_lines) + "\n" + torn)

        rc = elicit_vllm.run_elicit(
            jobs_path=jobs_path, prompts_path=prompts_path, run_config_path=run_config_path,
            out_path=out_path, engine_name="fake", skip_manifest_check=True,
            registry_path=MODELS_YAML, install_signal_handlers=False,
        )
        assert rc == 0
        results = read_jsonl(out_path, ResultRecord)
        assert len(results) == len(built_jobs)  # all 4 present, no duplicates, torn job redone
        assert {r.job_id for r in results} == {j.job_id for j in built_jobs}


# ---------------------------------------------------------------------------
# Durability: simulated crash via signal (acceptance criterion, literal)
# ---------------------------------------------------------------------------


class TestDurabilitySignalHandler:
    def test_sigterm_pushes_current_contents_before_exit(self, tmp_path):
        out_path = tmp_path / "results.jsonl"
        out_path.write_text('{"a":1}\n{"a":2}\n')
        store = storage.LocalDirStorage(tmp_path / "bucket")
        remote_key = "results/v1.0/results.jsonl"

        old_term = signal_module.getsignal(signal_module.SIGTERM)
        uninstall = elicit_vllm.install_durability_handlers(out_path, store, remote_key)
        try:
            handler = signal_module.getsignal(signal_module.SIGTERM)
            assert handler not in (signal_module.SIG_DFL, old_term)
            with pytest.raises(SystemExit):
                handler(signal_module.SIGTERM, None)
            assert store.exists(remote_key)
            pulled = tmp_path / "pulled.jsonl"
            store.pull(remote_key, pulled)
            assert pulled.read_text() == out_path.read_text()
        finally:
            uninstall()

    def test_sigint_also_installed(self, tmp_path):
        out_path = tmp_path / "results.jsonl"
        out_path.write_text('{"a":1}\n')
        store = storage.LocalDirStorage(tmp_path / "bucket")

        uninstall = elicit_vllm.install_durability_handlers(out_path, store, "k")
        try:
            handler = signal_module.getsignal(signal_module.SIGINT)
            with pytest.raises(SystemExit):
                handler(signal_module.SIGINT, None)
            assert store.exists("k")
        finally:
            uninstall()

    def test_uninstall_restores_previous_handlers(self, tmp_path):
        out_path = tmp_path / "results.jsonl"
        out_path.write_text('{"a":1}\n')
        store = storage.LocalDirStorage(tmp_path / "bucket")

        old_term = signal_module.getsignal(signal_module.SIGTERM)
        old_int = signal_module.getsignal(signal_module.SIGINT)
        uninstall = elicit_vllm.install_durability_handlers(out_path, store, "k")
        assert signal_module.getsignal(signal_module.SIGTERM) is not old_term
        uninstall()
        assert signal_module.getsignal(signal_module.SIGTERM) is old_term
        assert signal_module.getsignal(signal_module.SIGINT) is old_int

    def test_repeated_install_replaces_not_accumulates_atexit_callback(self, tmp_path):
        """Minor reviewer fix: calling install_durability_handlers many
        times within one process (as this whole test module does) must not
        pile up one atexit callback per call -- each new install replaces
        the module's single tracked callback, unregistering the previous
        one, rather than leaving it to fire (referencing a since-deleted
        tmp_path) at interpreter exit."""
        out_path = tmp_path / "results.jsonl"
        out_path.write_text('{"a":1}\n')
        store = storage.LocalDirStorage(tmp_path / "bucket")

        uninstall1 = elicit_vllm.install_durability_handlers(out_path, store, "k1")
        first_push = elicit_vllm._installed_atexit_push
        assert first_push is not None
        try:
            uninstall2 = elicit_vllm.install_durability_handlers(out_path, store, "k2")
            second_push = elicit_vllm._installed_atexit_push
            assert second_push is not None
            assert second_push is not first_push  # replaced, not appended alongside

            uninstall2()
            assert elicit_vllm._installed_atexit_push is None
        finally:
            # Best-effort cleanup in case an assertion above failed before
            # uninstall2() ran -- avoid leaking a handler into later tests.
            if elicit_vllm._installed_atexit_push is not None:
                elicit_vllm._installed_atexit_push = None
            uninstall1()


# ---------------------------------------------------------------------------
# Full run_elicit integration, FakeEngine, in-process
# ---------------------------------------------------------------------------


class TestRunElicitIntegration:
    def _build_fixture(self, tmp_path, *, n_items=20, questions=("intentionality", "blame"),
                        n_samples=3, models=("gemma-2-2b-pretrained",), release="v1.0"):
        prompts = _toy_prompts(n_items, list(questions))
        prompts_path = tmp_path / "prompts.jsonl"
        write_jsonl(prompts, prompts_path)

        built_jobs = jobs_mod.build_jobs(
            prompts, release=release, models=list(models), formats=["raw"],
            questions=list(questions), n_samples=n_samples,
        )
        jobs_path = tmp_path / "jobs.jsonl"
        jobs_mod.write_jobs_jsonl(built_jobs, jobs_path)

        run_config_path = tmp_path / "run.yaml"
        _write_run_config(
            run_config_path, release=release, models=list(models), formats=["raw"],
            n_samples=n_samples, questions=list(questions),
        )
        return prompts_path, jobs_path, run_config_path, built_jobs

    def test_100_percent_jobs_present(self, tmp_path):
        prompts_path, jobs_path, run_config_path, built_jobs = self._build_fixture(tmp_path)
        out_path = tmp_path / "results.jsonl"

        rc = elicit_vllm.run_elicit(
            jobs_path=jobs_path, prompts_path=prompts_path, run_config_path=run_config_path,
            out_path=out_path, engine_name="fake", skip_manifest_check=True,
            registry_path=MODELS_YAML, install_signal_handlers=False,
        )
        assert rc == 0

        results = read_jsonl(out_path, ResultRecord)
        assert len(results) == 20 * 2 * 3  # n_items x questions x n_samples
        assert {r.job_id for r in results} == {j.job_id for j in built_jobs}

    def test_logprobs_populated_on_every_row(self, tmp_path):
        prompts_path, jobs_path, run_config_path, _ = self._build_fixture(tmp_path, n_items=5, n_samples=2)
        out_path = tmp_path / "results.jsonl"
        elicit_vllm.run_elicit(
            jobs_path=jobs_path, prompts_path=prompts_path, run_config_path=run_config_path,
            out_path=out_path, engine_name="fake", skip_manifest_check=True,
            registry_path=MODELS_YAML, install_signal_handlers=False,
        )
        results = read_jsonl(out_path, ResultRecord)
        assert results  # sanity
        for r in results:
            assert r.logprobs_0_10 is not None
            assert len(r.logprobs_0_10) == 11
            assert r.model_revision == "fake"
            assert r.runner_version == elicit_vllm.RUNNER_VERSION

    def test_rerun_reproduces_identical_raw_responses(self, tmp_path):
        prompts_path, jobs_path, run_config_path, _ = self._build_fixture(tmp_path, n_items=5, n_samples=2)

        out1 = tmp_path / "results_1.jsonl"
        out2 = tmp_path / "results_2.jsonl"
        for out in (out1, out2):
            elicit_vllm.run_elicit(
                jobs_path=jobs_path, prompts_path=prompts_path, run_config_path=run_config_path,
                out_path=out, engine_name="fake", skip_manifest_check=True,
                registry_path=MODELS_YAML, install_signal_handlers=False,
            )

        by_id_1 = {r.job_id: r.raw_response for r in read_jsonl(out1, ResultRecord)}
        by_id_2 = {r.job_id: r.raw_response for r in read_jsonl(out2, ResultRecord)}
        assert by_id_1 == by_id_2
        assert by_id_1  # sanity: nonempty

    def test_split_token_mode_populates_a_real_rating_10_row(self, tmp_path):
        """Runs the full pipeline (not just the FakeEngine unit test) with
        token_mode="split" and enough jobs that at least one lands on
        rating 10 (~9% chance per job; with 5*3*3=45 jobs the chance of
        zero hits is (10/11)**45 ~= 1.4% -- use enough items to make this
        robust)."""
        prompts_path, jobs_path, run_config_path, _ = self._build_fixture(
            tmp_path, n_items=15, questions=("intentionality", "blame", "praise"), n_samples=3,
        )
        out_path = tmp_path / "results.jsonl"
        elicit_vllm.run_elicit(
            jobs_path=jobs_path, prompts_path=prompts_path, run_config_path=run_config_path,
            out_path=out_path, engine_name="fake", engine=elicit_vllm.FakeEngine(token_mode="split"),
            skip_manifest_check=True, registry_path=MODELS_YAML, install_signal_handlers=False,
        )
        results = read_jsonl(out_path, ResultRecord)
        tens = [r for r in results if r.raw_response == "10"]
        assert tens, "expected at least one job to land on rating 10 across 135 jobs"
        for r in tens:
            assert len(r.logprobs_0_10) == 11
            assert r.logprobs_0_10[10] > float("-inf")  # the joint computation produced a real value
            assert r.parse_ok is True
            assert r.parsed_rating == 10

    def test_grouping_loads_each_model_exactly_once(self, tmp_path):
        prompts_path, jobs_path, run_config_path, _ = self._build_fixture(
            tmp_path, n_items=3, models=("gemma-2-2b-pretrained", "gemma-2-2b-instruct"),
        )
        out_path = tmp_path / "results.jsonl"
        fake = elicit_vllm.FakeEngine()
        elicit_vllm.run_elicit(
            jobs_path=jobs_path, prompts_path=prompts_path, run_config_path=run_config_path,
            out_path=out_path, engine_name="fake", engine=fake, skip_manifest_check=True,
            registry_path=MODELS_YAML, install_signal_handlers=False,
        )
        assert len(fake.load_calls) == 2  # one model resident at a time -- loaded exactly once each
        assert {mid for mid, _rev in fake.load_calls} == {"google/gemma-2-2b", "google/gemma-2-2b-it"}

    def test_manifest_guard_refuses_and_writes_nothing(self, tmp_path):
        prompts_path, jobs_path, run_config_path, _ = self._build_fixture(tmp_path, n_items=2, n_samples=1)
        release_root = tmp_path / "release"
        _write_release(release_root, "v1.0", {"vignettes.csv": b"x"})
        (release_root / "v1.0" / "vignettes.csv").write_bytes(b"TAMPERED")
        out_path = tmp_path / "results.jsonl"

        rc = elicit_vllm.run_elicit(
            jobs_path=jobs_path, prompts_path=prompts_path, run_config_path=run_config_path,
            out_path=out_path, engine_name="fake", release_root=release_root,
            registry_path=MODELS_YAML, install_signal_handlers=False,
        )
        assert rc == 1
        assert not out_path.exists()

    def test_skip_manifest_check_warns_and_proceeds(self, tmp_path, capsys):
        prompts_path, jobs_path, run_config_path, _ = self._build_fixture(tmp_path, n_items=2, n_samples=1)
        out_path = tmp_path / "results.jsonl"

        rc = elicit_vllm.run_elicit(
            jobs_path=jobs_path, prompts_path=prompts_path, run_config_path=run_config_path,
            out_path=out_path, engine_name="fake", skip_manifest_check=True,
            registry_path=MODELS_YAML, install_signal_handlers=False,
        )
        assert rc == 0
        stderr = capsys.readouterr().err
        assert "SKIPPING" in stderr
        assert out_path.exists()

    def test_limit_truncates_remaining_jobs(self, tmp_path):
        prompts_path, jobs_path, run_config_path, _ = self._build_fixture(tmp_path, n_items=5, n_samples=2)
        out_path = tmp_path / "results.jsonl"
        elicit_vllm.run_elicit(
            jobs_path=jobs_path, prompts_path=prompts_path, run_config_path=run_config_path,
            out_path=out_path, engine_name="fake", skip_manifest_check=True, limit=3,
            registry_path=MODELS_YAML, install_signal_handlers=False,
        )
        assert len(read_jsonl(out_path, ResultRecord)) == 3

    def test_shard_restricts_to_this_process_share(self, tmp_path):
        prompts_path, jobs_path, run_config_path, built_jobs = self._build_fixture(
            tmp_path, n_items=6, n_samples=2,
        )
        results_by_shard: list[set[str]] = []
        for i in range(3):
            out_path = tmp_path / f"results_shard{i}.jsonl"
            elicit_vllm.run_elicit(
                jobs_path=jobs_path, prompts_path=prompts_path, run_config_path=run_config_path,
                out_path=out_path, engine_name="fake", skip_manifest_check=True, shard=(i, 3),
                registry_path=MODELS_YAML, install_signal_handlers=False,
            )
            results_by_shard.append({r.job_id for r in read_jsonl(out_path, ResultRecord)})

        all_ids = set().union(*results_by_shard)
        assert all_ids == {j.job_id for j in built_jobs}
        for a in range(3):
            for b in range(a + 1, 3):
                assert results_by_shard[a].isdisjoint(results_by_shard[b])

    def test_resume_skips_already_completed_rows(self, tmp_path):
        prompts_path, jobs_path, run_config_path, built_jobs = self._build_fixture(
            tmp_path, n_items=4, n_samples=2,
        )
        out_path = tmp_path / "results.jsonl"

        elicit_vllm.run_elicit(
            jobs_path=jobs_path, prompts_path=prompts_path, run_config_path=run_config_path,
            out_path=out_path, engine_name="fake", skip_manifest_check=True, limit=3,
            registry_path=MODELS_YAML, install_signal_handlers=False,
        )
        assert len(read_jsonl(out_path, ResultRecord)) == 3

        fake = elicit_vllm.FakeEngine()
        elicit_vllm.run_elicit(
            jobs_path=jobs_path, prompts_path=prompts_path, run_config_path=run_config_path,
            out_path=out_path, engine_name="fake", engine=fake, skip_manifest_check=True,
            registry_path=MODELS_YAML, install_signal_handlers=False,
        )
        total = len(built_jobs)
        results = read_jsonl(out_path, ResultRecord)
        assert len(results) == total
        assert {r.job_id for r in results} == {j.job_id for j in built_jobs}
        n_requested_second_run = sum(len(batch) for batch in fake.generate_calls)
        assert n_requested_second_run == total - 3  # only the remaining jobs were (re-)requested


# ---------------------------------------------------------------------------
# Checkpoint-interval storage sync (LocalDirStorage: shards appear at
# checkpoint intervals, not just a single final dump)
# ---------------------------------------------------------------------------


class _SnapshottingStorage:
    """Wraps a real StorageBackend, recording the row-count of the local
    file AT THE MOMENT each push() happens -- proves genuine periodic
    checkpointing (a monotonically-growing sequence of row counts, not one
    final push)."""

    def __init__(self, inner):
        self.inner = inner
        self.push_row_counts: list[int] = []

    def push(self, local_path, remote_key) -> None:
        with open(local_path, encoding="utf-8") as f:
            n = sum(1 for line in f if line.strip())
        self.push_row_counts.append(n)
        self.inner.push(local_path, remote_key)

    def pull(self, remote_key, local_path):
        return self.inner.pull(remote_key, local_path)

    def exists(self, remote_key):
        return self.inner.exists(remote_key)

    def list(self, prefix):
        return self.inner.list(prefix)


class TestCheckpointIntervalSync:
    def test_pushes_happen_at_intervals_not_just_once(self, tmp_path):
        prompts = _toy_prompts(10, ["intentionality"])
        prompts_path = tmp_path / "prompts.jsonl"
        write_jsonl(prompts, prompts_path)
        built_jobs = jobs_mod.build_jobs(
            prompts, release="v1.0", models=["gemma-2-2b-pretrained"], formats=["raw"],
            questions=["intentionality"], n_samples=1,
        )
        jobs_path = tmp_path / "jobs.jsonl"
        jobs_mod.write_jobs_jsonl(built_jobs, jobs_path)
        run_config_path = tmp_path / "run.yaml"
        _write_run_config(
            run_config_path, release="v1.0", models=["gemma-2-2b-pretrained"], formats=["raw"],
            n_samples=1, questions=["intentionality"],
        )
        out_path = tmp_path / "results.jsonl"

        spy = _SnapshottingStorage(storage.LocalDirStorage(tmp_path / "bucket"))
        rc = elicit_vllm.run_elicit(
            jobs_path=jobs_path, prompts_path=prompts_path, run_config_path=run_config_path,
            out_path=out_path, engine_name="fake", skip_manifest_check=True,
            registry_path=MODELS_YAML, install_signal_handlers=False,
            storage=spy, checkpoint_every=3, batch_size=1,
        )
        assert rc == 0
        # 10 jobs, checkpoint_every=3 -> periodic pushes at 3, 6, 9 rows,
        # plus a final push at 10 -- at least 2 DISTINCT row counts proves
        # genuine intermediate checkpointing, not a single final dump.
        assert len(spy.push_row_counts) >= 2
        assert len(set(spy.push_row_counts)) > 1
        assert spy.push_row_counts == sorted(spy.push_row_counts)  # monotonically nondecreasing
        assert spy.push_row_counts[-1] == 10


# ---------------------------------------------------------------------------
# Throughput report / parse-rate warning (WO-5 requirement 7)
# ---------------------------------------------------------------------------


class _EveryThirdUnparseableEngine:
    """Wraps FakeEngine but returns deliberately-unparseable text for every
    third response, pushing the checkpoint's regex parse rate below the
    95% warning threshold on purpose."""

    def __init__(self):
        self._inner = elicit_vllm.FakeEngine()
        self._counter = 0

    def load(self, *args, **kwargs):
        return self._inner.load(*args, **kwargs)

    def generate(self, batch):
        responses = self._inner.generate(batch)
        out = []
        for r in responses:
            self._counter += 1
            if self._counter % 3 == 0:
                out.append(elicit_vllm.EngineResponse(
                    job_id=r.job_id, raw_response="no number here", logprobs_0_10=r.logprobs_0_10,
                ))
            else:
                out.append(r)
        return out


class TestParseRateReporting:
    def _fixture(self, tmp_path):
        prompts = _toy_prompts(10, ["intentionality"])
        prompts_path = tmp_path / "prompts.jsonl"
        write_jsonl(prompts, prompts_path)
        built_jobs = jobs_mod.build_jobs(
            prompts, release="v1.0", models=["gemma-2-2b-pretrained"], formats=["raw"],
            questions=["intentionality"], n_samples=1,
        )
        jobs_path = tmp_path / "jobs.jsonl"
        jobs_mod.write_jobs_jsonl(built_jobs, jobs_path)
        run_config_path = tmp_path / "run.yaml"
        _write_run_config(
            run_config_path, release="v1.0", models=["gemma-2-2b-pretrained"], formats=["raw"],
            n_samples=1, questions=["intentionality"],
        )
        return prompts_path, jobs_path, run_config_path

    def test_low_parse_rate_prints_logit_fallback_instruction(self, tmp_path, capsys):
        prompts_path, jobs_path, run_config_path = self._fixture(tmp_path)
        out_path = tmp_path / "results.jsonl"
        elicit_vllm.run_elicit(
            jobs_path=jobs_path, prompts_path=prompts_path, run_config_path=run_config_path,
            out_path=out_path, engine_name="fake", engine=_EveryThirdUnparseableEngine(),
            skip_manifest_check=True, registry_path=MODELS_YAML, install_signal_handlers=False,
        )
        stderr = capsys.readouterr().err
        assert "WARNING" in stderr
        assert "gemma-2-2b-pretrained" in stderr
        assert "--logit-fallback" in stderr
        assert "95%" in stderr

        results = read_jsonl(out_path, ResultRecord)
        n_unparsed = sum(1 for r in results if not r.parse_ok)
        assert n_unparsed > 0  # sanity: the deliberately-bad responses really did fail regex

    def test_high_parse_rate_no_warning(self, tmp_path, capsys):
        prompts_path, jobs_path, run_config_path = self._fixture(tmp_path)
        out_path = tmp_path / "results.jsonl"
        elicit_vllm.run_elicit(
            jobs_path=jobs_path, prompts_path=prompts_path, run_config_path=run_config_path,
            out_path=out_path, engine_name="fake", skip_manifest_check=True,
            registry_path=MODELS_YAML, install_signal_handlers=False,
        )
        stderr = capsys.readouterr().err
        assert "--logit-fallback" not in stderr  # no low-parse-rate warning fired
        assert "rows/sec" in stderr  # the (non-warning) throughput report still printed

    def test_logit_fallback_flag_recovers_unparseable_rows(self, tmp_path):
        prompts_path, jobs_path, run_config_path = self._fixture(tmp_path)
        out_path = tmp_path / "results.jsonl"
        elicit_vllm.run_elicit(
            jobs_path=jobs_path, prompts_path=prompts_path, run_config_path=run_config_path,
            out_path=out_path, engine_name="fake", engine=_EveryThirdUnparseableEngine(),
            skip_manifest_check=True, registry_path=MODELS_YAML, install_signal_handlers=False,
            logit_fallback_checkpoints=["gemma-2-2b-pretrained"],
        )
        results = read_jsonl(out_path, ResultRecord)
        fallback_rows = [r for r in results if r.parse_method == "logit_fallback"]
        assert fallback_rows
        for r in fallback_rows:
            assert r.parse_ok is True
            assert isinstance(r.parsed_rating, float)

    def test_logit_fallback_from_run_config_alone_also_works(self, tmp_path):
        """The run config's own `logit_fallback_checkpoints` list must work
        even with no --logit-fallback CLI flag at all -- this is what makes
        the decision durable across restarts (WO-5 requirement 7's "the
        config key to set")."""
        prompts = _toy_prompts(10, ["intentionality"])
        prompts_path = tmp_path / "prompts.jsonl"
        write_jsonl(prompts, prompts_path)
        built_jobs = jobs_mod.build_jobs(
            prompts, release="v1.0", models=["gemma-2-2b-pretrained"], formats=["raw"],
            questions=["intentionality"], n_samples=1,
        )
        jobs_path = tmp_path / "jobs.jsonl"
        jobs_mod.write_jobs_jsonl(built_jobs, jobs_path)
        run_config_path = tmp_path / "run.yaml"
        _write_run_config(
            run_config_path, release="v1.0", models=["gemma-2-2b-pretrained"], formats=["raw"],
            n_samples=1, questions=["intentionality"],
            logit_fallback_checkpoints=["gemma-2-2b-pretrained"],
        )
        out_path = tmp_path / "results.jsonl"

        elicit_vllm.run_elicit(
            jobs_path=jobs_path, prompts_path=prompts_path, run_config_path=run_config_path,
            out_path=out_path, engine_name="fake", engine=_EveryThirdUnparseableEngine(),
            skip_manifest_check=True, registry_path=MODELS_YAML, install_signal_handlers=False,
            # deliberately no logit_fallback_checkpoints kwarg here
        )
        results = read_jsonl(out_path, ResultRecord)
        fallback_rows = [r for r in results if r.parse_method == "logit_fallback"]
        assert fallback_rows


# ---------------------------------------------------------------------------
# _safe_parse_with_fallback -- Critical reviewer fix: a degenerate (all
# -inf) logprobs_0_10 distribution must never crash the write loop.
# ---------------------------------------------------------------------------


class TestSafeParseWithFallbackGuard:
    def test_all_neg_inf_logprobs_degrades_to_parse_ok_false(self):
        result = elicit_vllm._safe_parse_with_fallback("garbage", [float("-inf")] * 11, threshold_ok=False)
        assert result.parse_ok is False
        assert result.parsed_rating is None
        assert result.parse_method == "regex"
        assert result.raw == "garbage"

    def test_regression_bare_parse_with_fallback_actually_raises(self):
        """Pins the underlying bug this wrapper guards against -- without
        the wrapper, this exact input crashes."""
        from knobe.parsing import parse_with_fallback

        with pytest.raises(ValueError):
            parse_with_fallback("garbage", [float("-inf")] * 11, False)

    def test_normal_regex_path_unaffected(self):
        result = elicit_vllm._safe_parse_with_fallback("7", None, threshold_ok=True)
        assert result.parse_ok is True
        assert result.parsed_rating == 7
        assert result.parse_method == "regex"

    def test_normal_fallback_path_unaffected(self):
        # A non-degenerate distribution still gets a real expected value.
        logprobs = [-10.0] * 11
        logprobs[6] = -0.01
        result = elicit_vllm._safe_parse_with_fallback("garbage", logprobs, threshold_ok=False)
        assert result.parse_ok is True
        assert result.parse_method == "logit_fallback"
        assert result.parsed_rating is not None


class TestSanitizeLogprobsForStorage:
    """Related bug found while testing the guard above: pydantic silently
    serializes -inf/+inf/NaN as JSON `null`, and ResultRecord.logprobs_0_10
    is `list[float] | None` (not `list[float | None]`) -- a `null` entry
    fails re-validation on the very next read, corrupting resume against a
    file containing a genuinely degenerate row."""

    def test_none_passes_through(self):
        assert elicit_vllm._sanitize_logprobs_for_storage(None) is None

    def test_neg_inf_clamped_to_finite_sentinel(self):
        out = elicit_vllm._sanitize_logprobs_for_storage([float("-inf")] * 11)
        assert out == [elicit_vllm._LOGPROB_NEG_INF_SENTINEL] * 11
        assert all(v == v and v != float("-inf") for v in out)  # finite, not NaN

    def test_nan_clamped_to_finite_sentinel(self):
        out = elicit_vllm._sanitize_logprobs_for_storage([float("nan")] * 11)
        assert out == [elicit_vllm._LOGPROB_NEG_INF_SENTINEL] * 11

    def test_ordinary_finite_values_untouched(self):
        logprobs = [-0.5, -1.2, -3.0, -5.0, -6.0, -7.0, -8.0, -9.0, -10.0, -11.0, -12.0]
        assert elicit_vllm._sanitize_logprobs_for_storage(logprobs) == logprobs

    def test_mixed_finite_and_degenerate_entries(self):
        logprobs = [-0.01] + [float("-inf")] * 10
        out = elicit_vllm._sanitize_logprobs_for_storage(logprobs)
        assert out[0] == -0.01
        assert out[1:] == [elicit_vllm._LOGPROB_NEG_INF_SENTINEL] * 10

    def test_sanitized_value_round_trips_through_json(self):
        """The actual bug: a ResultRecord built with a RAW -inf entry
        fails re-validation immediately after being written+re-read; one
        built with the sanitized value round-trips cleanly."""
        raw = ResultRecord(
            job_id="j", prompt_id="p", model_key="m", sample_idx=0, temperature=1.0, seed=1,
            raw_response="x", parsed_rating=None, parse_ok=False, parse_method="regex",
            logprobs_0_10=[float("-inf")] * 11, model_revision="fake", runner_version="v", timestamp=1.0,
        )
        with pytest.raises(Exception):
            ResultRecord.model_validate_json(raw.model_dump_json())  # the unsanitized bug, pinned

        sanitized = ResultRecord(
            job_id="j", prompt_id="p", model_key="m", sample_idx=0, temperature=1.0, seed=1,
            raw_response="x", parsed_rating=None, parse_ok=False, parse_method="regex",
            logprobs_0_10=elicit_vllm._sanitize_logprobs_for_storage([float("-inf")] * 11),
            model_revision="fake", runner_version="v", timestamp=1.0,
        )
        round_tripped = ResultRecord.model_validate_json(sanitized.model_dump_json())
        assert round_tripped == sanitized


class _AllNegInfLogprobsEngine:
    """Wraps FakeEngine but forces a totally degenerate logprobs_0_10 (all
    -inf) and unparseable raw text for exactly the FIRST job it's asked
    about, deterministically -- without the ``_safe_parse_with_fallback``
    guard, this response raises ``ValueError`` inside ``run_elicit``'s
    write loop and aborts the whole run."""

    def __init__(self):
        self._inner = elicit_vllm.FakeEngine()
        self._forced = False

    def load(self, *args, **kwargs):
        return self._inner.load(*args, **kwargs)

    def generate(self, batch):
        responses = self._inner.generate(batch)
        out = []
        for r in responses:
            if not self._forced:
                self._forced = True
                out.append(elicit_vllm.EngineResponse(
                    job_id=r.job_id, raw_response="not parseable at all",
                    logprobs_0_10=[float("-inf")] * 11,
                ))
            else:
                out.append(r)
        return out


class TestDegenerateLogprobsDoesNotCrashRun:
    def test_run_completes_and_degenerate_row_is_parse_ok_false(self, tmp_path):
        prompts = _toy_prompts(6, ["intentionality"])
        prompts_path = tmp_path / "prompts.jsonl"
        write_jsonl(prompts, prompts_path)
        built_jobs = jobs_mod.build_jobs(
            prompts, release="v1.0", models=["gemma-2-2b-pretrained"], formats=["raw"],
            questions=["intentionality"], n_samples=1,
        )
        jobs_path = tmp_path / "jobs.jsonl"
        jobs_mod.write_jobs_jsonl(built_jobs, jobs_path)
        run_config_path = tmp_path / "run.yaml"
        _write_run_config(
            run_config_path, release="v1.0", models=["gemma-2-2b-pretrained"], formats=["raw"],
            n_samples=1, questions=["intentionality"],
        )
        out_path = tmp_path / "results.jsonl"

        # threshold_ok=False (via --logit-fallback) is what makes
        # run_elicit actually ATTEMPT the EV computation for the
        # unparseable row -- that's the branch that used to raise.
        rc = elicit_vllm.run_elicit(
            jobs_path=jobs_path, prompts_path=prompts_path, run_config_path=run_config_path,
            out_path=out_path, engine_name="fake", engine=_AllNegInfLogprobsEngine(),
            skip_manifest_check=True, registry_path=MODELS_YAML, install_signal_handlers=False,
            logit_fallback_checkpoints=["gemma-2-2b-pretrained"],
        )
        assert rc == 0  # the run COMPLETED -- did not crash mid-write

        # This read alone (via schemas.read_jsonl, plain per-line
        # validation, NOT the torn-tail-tolerant loader) is itself proof
        # the degenerate row round-trips cleanly on disk -- before the
        # sanitization fix, writing a literal -inf entry silently
        # serialized to JSON `null`, which then failed re-validation on
        # this exact read (ResultRecord.logprobs_0_10 is `list[float]`,
        # not `list[float | None]`), corrupting resume on the very next
        # attempt against this file.
        results = read_jsonl(out_path, ResultRecord)
        assert len(results) == len(built_jobs)  # every job still got a row written

        degenerate = [r for r in results if r.raw_response == "not parseable at all"]
        assert len(degenerate) == 1
        assert degenerate[0].parse_ok is False
        assert degenerate[0].parsed_rating is None
        assert degenerate[0].parse_method == "regex"
        assert degenerate[0].logprobs_0_10 == [elicit_vllm._LOGPROB_NEG_INF_SENTINEL] * 11
        assert all(lp == lp and lp != float("-inf") for lp in degenerate[0].logprobs_0_10)  # finite, not NaN


# ---------------------------------------------------------------------------
# ElicitRunLogEntry
# ---------------------------------------------------------------------------


class TestRunlog:
    def test_runlog_entry_written(self, tmp_path):
        prompts = _toy_prompts(3, ["intentionality"])
        prompts_path = tmp_path / "prompts.jsonl"
        write_jsonl(prompts, prompts_path)
        built_jobs = jobs_mod.build_jobs(
            prompts, release="v1.0", models=["gemma-2-2b-pretrained"], formats=["raw"],
            questions=["intentionality"], n_samples=1,
        )
        jobs_path = tmp_path / "jobs.jsonl"
        jobs_mod.write_jobs_jsonl(built_jobs, jobs_path)
        run_config_path = tmp_path / "run.yaml"
        _write_run_config(
            run_config_path, release="v1.0", models=["gemma-2-2b-pretrained"], formats=["raw"],
            n_samples=1, questions=["intentionality"],
        )
        out_path = tmp_path / "results.jsonl"
        runlog_path = tmp_path / "elicit_runlog.jsonl"

        elicit_vllm.run_elicit(
            jobs_path=jobs_path, prompts_path=prompts_path, run_config_path=run_config_path,
            out_path=out_path, engine_name="fake", skip_manifest_check=True,
            registry_path=MODELS_YAML, install_signal_handlers=False, runlog_path=runlog_path,
        )
        from knobe.schemas import ElicitRunLogEntry

        entries = read_jsonl(runlog_path, ElicitRunLogEntry)
        assert len(entries) == 1
        assert entries[0].n_jobs_run == 3
        assert entries[0].release == "v1.0"
        assert entries[0].engine == "fake"
        assert "gemma-2-2b-pretrained" in entries[0].parse_rate_by_model_key


# ---------------------------------------------------------------------------
# CLI: --help, the G0 gate (kill/restart across real subprocesses)
# ---------------------------------------------------------------------------


class TestCLIHelp:
    def test_elicit_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "knobe.cli", "elicit", "--help"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0
        assert "--jobs" in result.stdout
        assert "--engine" in result.stdout
        assert "--shard" in result.stdout


def _run_cli_elicit(tmp_path: Path, *, jobs_path, prompts_path, run_config_path, out_path,
                     extra_args: list[str] | None = None) -> subprocess.CompletedProcess:
    cmd = [
        sys.executable, "-m", "knobe.cli", "elicit",
        "--jobs", str(jobs_path), "--prompts", str(prompts_path),
        "--run-config", str(run_config_path), "--out", str(out_path),
        "--engine", "fake", "--skip-manifest-check",
    ]
    cmd.extend(extra_args or [])
    return subprocess.run(cmd, capture_output=True, text=True, timeout=60, cwd=tmp_path)


class TestCLIResumeAcrossProcesses:
    """A cheap, fully-deterministic two-phase resume check: two SEPARATE
    OS processes sharing only the on-disk results.jsonl checkpoint file,
    the second cooperatively stopped via --limit rather than killed -- same
    pattern as test_curate.py's TestCLIResumeAcrossProcesses. Final
    row-set must be identical (up to ordering) to a single uninterrupted
    run's row-set. This is clean two-phase resume, NOT a genuine kill -9 --
    see TestCLIRealSigkillResume below for the literal G0 gate (a real
    SIGKILL sent to a still-running subprocess); this class is kept
    alongside it as the cheaper, non-timing-dependent case."""

    def _build_fixture(self, tmp_path):
        prompts = _toy_prompts(8, ["intentionality", "blame"])
        prompts_path = tmp_path / "prompts.jsonl"
        write_jsonl(prompts, prompts_path)
        built_jobs = jobs_mod.build_jobs(
            prompts, release="v1.0", models=["gemma-2-2b-pretrained"], formats=["raw"],
            questions=["intentionality", "blame"], n_samples=2,
        )
        jobs_path = tmp_path / "jobs.jsonl"
        jobs_mod.write_jobs_jsonl(built_jobs, jobs_path)
        run_config_path = tmp_path / "run.yaml"
        _write_run_config(
            run_config_path, release="v1.0", models=["gemma-2-2b-pretrained"], formats=["raw"],
            n_samples=2, questions=["intentionality", "blame"],
        )
        return prompts_path, jobs_path, run_config_path, built_jobs

    def test_kill_restart_row_set_identical_to_uninterrupted_run(self, tmp_path):
        prompts_path, jobs_path, run_config_path, built_jobs = self._build_fixture(tmp_path)
        total = len(built_jobs)  # 8 items x 2 questions x 2 samples = 32
        assert total == 32

        # A single uninterrupted run, for comparison.
        uninterrupted_out = tmp_path / "results_uninterrupted.jsonl"
        r0 = _run_cli_elicit(
            tmp_path, jobs_path=jobs_path, prompts_path=prompts_path,
            run_config_path=run_config_path, out_path=uninterrupted_out,
        )
        assert r0.returncode == 0, r0.stderr
        uninterrupted_ids = {json.loads(line)["job_id"] for line in uninterrupted_out.read_text().splitlines()}
        assert uninterrupted_ids == {j.job_id for j in built_jobs}

        # "Run half, kill": first process only does the first half (--limit).
        out_path = tmp_path / "results.jsonl"
        half = total // 2
        first = _run_cli_elicit(
            tmp_path, jobs_path=jobs_path, prompts_path=prompts_path,
            run_config_path=run_config_path, out_path=out_path,
            extra_args=["--limit", str(half)],
        )
        assert first.returncode == 0, first.stderr
        assert len(out_path.read_text().splitlines()) == half

        # "Restart": a brand-new process, no --limit, same output path.
        second = _run_cli_elicit(
            tmp_path, jobs_path=jobs_path, prompts_path=prompts_path,
            run_config_path=run_config_path, out_path=out_path,
        )
        assert second.returncode == 0, second.stderr

        raw_lines = out_path.read_text().splitlines()
        assert len(raw_lines) == total  # complete, no duplicates, no losses
        final_ids = {json.loads(line)["job_id"] for line in raw_lines}
        assert len(final_ids) == total  # every job exactly once
        assert final_ids == uninterrupted_ids  # row-set identical to the uninterrupted run

        # Determinism bonus: since FakeEngine is deterministic, the actual
        # raw_response content matches too, not just the id set.
        by_id_restart = {json.loads(line)["job_id"]: json.loads(line)["raw_response"] for line in raw_lines}
        by_id_uninterrupted = {
            json.loads(line)["job_id"]: json.loads(line)["raw_response"]
            for line in uninterrupted_out.read_text().splitlines()
        }
        assert by_id_restart == by_id_uninterrupted


class TestCLIRealSigkillResume:
    """The literal G0 gate (Important reviewer fix): launches a real
    subprocess, polls the output file on disk until several rows genuinely
    exist, sends a real ``SIGKILL`` (uncatchable -- not a cooperative
    ``--limit`` stop), then restarts without ``--limit`` and asserts the
    final row-set matches an uninterrupted control run. Uses FakeEngine's
    ``KNOBE_FAKE_ENGINE_SLEEP_MS`` test-only hook (see its docstring in
    elicit_vllm.py) so the subprocess is reliably still running when the
    kill is sent, rather than racing a near-instant FakeEngine run against
    OS process-spawn timing."""

    def _build_fixture(self, tmp_path, n_items=100):
        prompts = _toy_prompts(n_items, ["intentionality"])
        prompts_path = tmp_path / "prompts.jsonl"
        write_jsonl(prompts, prompts_path)
        built_jobs = jobs_mod.build_jobs(
            prompts, release="v1.0", models=["gemma-2-2b-pretrained"], formats=["raw"],
            questions=["intentionality"], n_samples=1,
        )
        jobs_path = tmp_path / "jobs.jsonl"
        jobs_mod.write_jobs_jsonl(built_jobs, jobs_path)
        run_config_path = tmp_path / "run.yaml"
        _write_run_config(
            run_config_path, release="v1.0", models=["gemma-2-2b-pretrained"], formats=["raw"],
            n_samples=1, questions=["intentionality"],
        )
        return prompts_path, jobs_path, run_config_path, built_jobs

    def test_sigkill_mid_run_then_restart_matches_uninterrupted(self, tmp_path):
        prompts_path, jobs_path, run_config_path, built_jobs = self._build_fixture(tmp_path)
        total = len(built_jobs)
        assert total == 100

        # Uninterrupted control run -- no artificial delay, runs to completion.
        uninterrupted_out = tmp_path / "results_uninterrupted.jsonl"
        r0 = _run_cli_elicit(
            tmp_path, jobs_path=jobs_path, prompts_path=prompts_path,
            run_config_path=run_config_path, out_path=uninterrupted_out,
        )
        assert r0.returncode == 0, r0.stderr
        uninterrupted_ids = {json.loads(line)["job_id"] for line in uninterrupted_out.read_text().splitlines()}
        assert uninterrupted_ids == {j.job_id for j in built_jobs}

        # Real kill: --batch-size 1 + the sleep hook means each row takes
        # >= 25ms, so a 100-job run takes >= 2.5s -- comfortably long
        # enough to reliably observe partial progress and send SIGKILL
        # well before it would finish on its own.
        out_path = tmp_path / "results.jsonl"
        cmd = [
            sys.executable, "-m", "knobe.cli", "elicit",
            "--jobs", str(jobs_path), "--prompts", str(prompts_path),
            "--run-config", str(run_config_path), "--out", str(out_path),
            "--engine", "fake", "--skip-manifest-check", "--batch-size", "1",
        ]
        env = dict(os.environ, KNOBE_FAKE_ENGINE_SLEEP_MS="25")
        proc = subprocess.Popen(
            cmd, cwd=tmp_path, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        try:
            deadline = time_module.time() + 30
            observed_progress = False
            while time_module.time() < deadline:
                if out_path.exists():
                    n = out_path.read_text(encoding="utf-8", errors="ignore").count("\n")
                    if n >= 5:
                        observed_progress = True
                        break
                if proc.poll() is not None:
                    break  # finished (or died) before we ever saw 5 rows
                time_module.sleep(0.01)

            assert proc.poll() is None, (
                "the elicit subprocess finished (or died) before SIGKILL could be sent -- "
                "increase n_items/KNOBE_FAKE_ENGINE_SLEEP_MS in this test if it gets flaky"
            )
            assert observed_progress, "never observed >= 5 written rows before the poll deadline"

            os.kill(proc.pid, signal_module.SIGKILL)
            proc.wait(timeout=10)
        finally:
            if proc.poll() is None:  # pragma: no cover -- safety net only
                proc.kill()
                proc.wait()
            # Popen's PIPE fds are never read here (we only poll the
            # output FILE, not the process's stdout/stderr) -- close them
            # explicitly so CPython doesn't finalize them via __del__ at
            # some later, unpredictable point, which pytest's
            # filterwarnings=["error"] turns into a hard test failure
            # (ResourceWarning: unclosed file).
            if proc.stdout is not None:
                proc.stdout.close()
            if proc.stderr is not None:
                proc.stderr.close()

        assert proc.returncode == -signal_module.SIGKILL  # genuinely killed, not a clean/cooperative exit

        n_before_restart = out_path.read_text(encoding="utf-8", errors="ignore").count("\n")
        assert 0 < n_before_restart < total  # truly interrupted mid-run (not before-start, not after-finish)

        # Restart: a brand-new process, no --limit, no artificial delay,
        # same output path -- must tolerate whatever state the SIGKILL
        # left behind (including a possibly-torn trailing line, per
        # read_results_tolerating_torn_tail).
        second = _run_cli_elicit(
            tmp_path, jobs_path=jobs_path, prompts_path=prompts_path,
            run_config_path=run_config_path, out_path=out_path,
        )
        assert second.returncode == 0, second.stderr

        raw_lines = out_path.read_text().splitlines()
        final_ids = {json.loads(line)["job_id"] for line in raw_lines}
        assert len(final_ids) == total  # every job exactly once, none lost, none duplicated
        assert final_ids == uninterrupted_ids  # row-set identical (up to ordering) to the control run
