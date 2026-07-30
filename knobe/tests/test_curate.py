"""Tests for src/knobe/curate.py + the `knobe curate` CLI (WO-3).

Acceptance criteria under test (WO3_curation.md / task-4-brief.md), all
with MockClient / no real network:
  - Resume skips completed keys: a real kill/restart simulation (run half
    via --limit in one OS subprocess, restart in a SEPARATE subprocess
    without --limit) shows total calls across both runs = exactly the
    unique job count, and the final raw file is complete. A second,
    in-process version pins the same "reads only from disk, no in-memory
    cache" property at the function level.
  - A reviewer matching a subject family fails at startup: exact full HF
    id match ("meta-llama/Llama-3.1-8B") and family-key substring match
    ("llama-3.1-8b-instruct"-style key), both against the real
    configs/models.yaml.
  - Pair / typicality-manipulation / category-manipulation checks fire on
    constructed fixtures.
  - Unparseable curation responses never coerce to a number (assemble_curated).
  - --mock executes the full path with zero network calls (curate.anthropic
    stays None; MockClient never touches the network).
"""
from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path

import pytest

from knobe import constants, curate
from knobe.registry import Family, load_registry
from knobe.schemas import (
    CuratedRow,
    CurationRawResult,
    CurationRunLogEntry,
    VignetteRow,
    read_csv_validated,
    read_jsonl,
    write_csv_validated,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
MODELS_YAML = REPO_ROOT / "configs" / "models.yaml"
CURATION_YAML = REPO_ROOT / "configs" / "curation.yaml"


# ---------------------------------------------------------------------------
# Fixtures / builders
# ---------------------------------------------------------------------------


def _family(**overrides) -> Family:
    kwargs = dict(
        pretrained="org/model-base", finetuned="org/model-instruct",
        tl_name="org/model-base", d_model=4096, n_layers=32, role="extension",
    )
    kwargs.update(overrides)
    return Family(**kwargs)


def _vignette_rows(family_id: str, valence: str, *, nonmoral_subdomain: str = "") -> list[VignetteRow]:
    sign = constants.SIGN_BY_VALENCE[valence]
    rows = []
    for (typicality, evocativeness), letter in constants.VARIANT_LETTER.items():
        rows.append(
            VignetteRow(
                variant_id=f"{family_id}-{letter}", family_id=family_id, domain="Environment",
                valence=valence, nonmoral_subdomain=nonmoral_subdomain, sign=sign,
                typicality=typicality, evocativeness=evocativeness,
                scenario=f"scenario for {family_id} {typicality} {evocativeness}",
                q_intentionality="q_i", q_blame="q_b", q_praise="q_p",
            )
        )
    return rows


_LETTER_TO_TYP_EVOC = {letter: key for key, letter in constants.VARIANT_LETTER.items()}


def _curated_row(
    *,
    family_id: str = "ENV-MB-01",
    valence: str = "MB",
    nonmoral_subdomain: str = "",
    typicality: str | None = None,
    evocativeness: str | None = None,
    variant_id: str | None = None,
    sign: str | None = None,
    moral_relevance: int | None = None,
    severity: int | None = None,
    vividness: int | None = None,
    typicality_perception: int | None = None,
    individual_flags: str = "",
    pair_flag: str = "",
    reviewer_model: str = "claude-sonnet-4-6",
    curation_date: str = "2026-01-01",
    accepted: bool = False,
) -> CuratedRow:
    """Builds one self-consistent CuratedRow fixture. If ``variant_id`` is
    given explicitly, ``typicality``/``evocativeness`` are derived from its
    letter suffix (unless also given explicitly) rather than defaulted, so
    ``variant_id="...-B"`` doesn't collide with CuratedRow's own
    variant_id-vs-(typicality, evocativeness) consistency check."""
    if variant_id is not None:
        letter = variant_id.rsplit("-", 1)[-1]
        derived_typicality, derived_evocativeness = _LETTER_TO_TYP_EVOC[letter]
        typicality = typicality or derived_typicality
        evocativeness = evocativeness or derived_evocativeness
    else:
        typicality = typicality or "common"
        evocativeness = evocativeness or "low"
        letter = constants.VARIANT_LETTER[(typicality, evocativeness)]
        variant_id = f"{family_id}-{letter}"

    sign = sign or constants.SIGN_BY_VALENCE[valence]

    def _raw(v):
        return "" if v is None else str(v)

    return CuratedRow(
        variant_id=variant_id, family_id=family_id, domain="Environment", valence=valence,
        nonmoral_subdomain=nonmoral_subdomain, sign=sign, typicality=typicality,
        evocativeness=evocativeness, scenario=f"scenario for {variant_id}",
        q_intentionality="q_i", q_blame="q_b", q_praise="q_p",
        moral_relevance=moral_relevance, moral_relevance_raw=_raw(moral_relevance),
        severity=severity, severity_raw=_raw(severity),
        vividness=vividness, vividness_raw=_raw(vividness),
        typicality_perception=typicality_perception, typicality_perception_raw=_raw(typicality_perception),
        individual_flags=individual_flags, pair_flag=pair_flag, reviewer_model=reviewer_model,
        curation_date=curation_date, accepted=accepted,
    )


# ---------------------------------------------------------------------------
# Reviewer != subject (WO-3 §2)
# ---------------------------------------------------------------------------


class TestCheckReviewerNotSubject:
    def test_exact_hf_id_match_is_hard_error(self):
        registry = load_registry(MODELS_YAML)
        with pytest.raises(curate.ReviewerSubjectConflictError):
            curate.check_reviewer_not_subject("meta-llama/Llama-3.1-8B", registry)

    def test_exact_hf_id_match_case_insensitive(self):
        registry = load_registry(MODELS_YAML)
        with pytest.raises(curate.ReviewerSubjectConflictError):
            curate.check_reviewer_not_subject("META-LLAMA/LLAMA-3.1-8B", registry)

    def test_family_key_substring_match_is_hard_error(self):
        registry = load_registry(MODELS_YAML)
        with pytest.raises(curate.ReviewerSubjectConflictError):
            curate.check_reviewer_not_subject("llama-3.1-8b-instruct", registry)

    def test_reviewer_substring_of_family_key_also_matches(self):
        registry = {"llama-3.1-8b": _family()}
        with pytest.raises(curate.ReviewerSubjectConflictError):
            curate.check_reviewer_not_subject("llama-3.1-8b", registry)

    def test_unrelated_claude_reviewer_is_fine(self):
        registry = load_registry(MODELS_YAML)
        curate.check_reviewer_not_subject("claude-sonnet-4-6", registry)  # must not raise

    def test_unrelated_model_is_fine(self):
        registry = {"llama-3.1-8b": _family()}
        curate.check_reviewer_not_subject("gpt-4o", registry)  # must not raise


# ---------------------------------------------------------------------------
# MockClient determinism + AnthropicClient guard
# ---------------------------------------------------------------------------


class TestMockClient:
    def test_deterministic_across_instances(self):
        c1, c2 = curate.MockClient(), curate.MockClient()
        r1 = asyncio.run(c1.complete("hello", 10))
        r2 = asyncio.run(c2.complete("hello", 10))
        assert r1 == r2

    def test_different_prompts_can_differ(self):
        c = curate.MockClient()
        responses = {asyncio.run(c.complete(f"prompt {i}", 10)) for i in range(20)}
        assert len(responses) > 1

    def test_unparseable_rate_zero_is_always_parseable(self):
        c = curate.MockClient(unparseable_rate=0.0)
        for i in range(30):
            text = asyncio.run(c.complete(f"prompt {i}", 10))
            _, ok, _ = curate.parse_rating(text)
            assert ok

    def test_unparseable_rate_one_is_never_parseable(self):
        c = curate.MockClient(unparseable_rate=1.0)
        for i in range(30):
            text = asyncio.run(c.complete(f"prompt {i}", 10))
            _, ok, _ = curate.parse_rating(text)
            assert not ok

    def test_invalid_rate_rejected(self):
        with pytest.raises(ValueError):
            curate.MockClient(unparseable_rate=1.5)

    def test_no_network_module_needed(self):
        """--mock never touches anthropic -- confirmed by the guarded
        import staying None even though this test suite imports and
        exercises curate.py fully."""
        assert curate.anthropic is None


class TestAnthropicClientGuard:
    def test_raises_at_construction_not_import_when_package_missing(self):
        assert curate.anthropic is None  # precondition: extra not installed
        with pytest.raises(RuntimeError, match="anthropic"):
            curate.AnthropicClient(model="claude-sonnet-4-6")


# ---------------------------------------------------------------------------
# Retry logic (transient vs non-transient)
# ---------------------------------------------------------------------------


class _FlakyClient:
    def __init__(self, fail_times: int, final_text: str = "7"):
        self.fail_times = fail_times
        self.final_text = final_text
        self.attempts = 0

    async def complete(self, prompt: str, max_tokens: int) -> str:
        self.attempts += 1
        if self.attempts <= self.fail_times:
            raise curate.TransientCallError("simulated rate limit")
        return self.final_text


class _AlwaysNonTransientClient:
    def __init__(self):
        self.attempts = 0

    async def complete(self, prompt: str, max_tokens: int) -> str:
        self.attempts += 1
        raise ValueError("boom -- not retryable")


async def _fast_sleep(_seconds: float) -> None:
    return None


class TestCompleteWithRetry:
    def test_succeeds_after_transient_failures(self):
        client = _FlakyClient(fail_times=2)
        text, retries = asyncio.run(
            curate._complete_with_retry(client, "p", 10, max_retries=3, sleep=_fast_sleep)
        )
        assert text == "7"
        assert retries == 2
        assert client.attempts == 3

    def test_exhausts_retries_and_raises(self):
        client = _FlakyClient(fail_times=5)
        with pytest.raises(curate.TransientCallError):
            asyncio.run(curate._complete_with_retry(client, "p", 10, max_retries=3, sleep=_fast_sleep))
        assert client.attempts == 3

    def test_exhausted_retries_exception_carries_retries_used(self):
        """Regression: an exhausted-retry TransientCallError must carry how
        many retries were actually spent, so a caller that only sees the
        exception (run_curation_jobs's per-job error path) can still fold
        that cost into telemetry instead of silently recording 0 retries
        for a job that in fact retried all the way to its budget."""
        client = _FlakyClient(fail_times=5)
        with pytest.raises(curate.TransientCallError) as exc_info:
            asyncio.run(curate._complete_with_retry(client, "p", 10, max_retries=3, sleep=_fast_sleep))
        assert exc_info.value.retries_used == 2  # max_retries=3 -> 2 retries before giving up

    def test_non_transient_error_not_retried(self):
        client = _AlwaysNonTransientClient()
        with pytest.raises(ValueError):
            asyncio.run(curate._complete_with_retry(client, "p", 10, max_retries=3, sleep=_fast_sleep))
        assert client.attempts == 1  # no retry budget spent on a non-transient error


# ---------------------------------------------------------------------------
# build_job_keys
# ---------------------------------------------------------------------------


class TestBuildJobKeys:
    def test_variant_major_field_order(self):
        keys = curate.build_job_keys(["A", "B"])
        fields = list(constants.CURATION_QUESTIONS)
        assert keys == [(vid, f) for vid in ["A", "B"] for f in fields]

    def test_limit_truncates(self):
        keys = curate.build_job_keys(["A", "B"], limit=3)
        assert len(keys) == 3

    def test_shard_partitions_without_overlap(self):
        variant_ids = [f"V{i}" for i in range(10)]
        all_keys = curate.build_job_keys(variant_ids)
        shards = [curate.build_job_keys(variant_ids, shard=(i, 4)) for i in range(4)]
        recombined = sorted(k for shard in shards for k in shard)
        assert recombined == sorted(all_keys)
        seen = set()
        for shard in shards:
            for k in shard:
                assert k not in seen
                seen.add(k)

    def test_shard_out_of_range_rejected(self):
        with pytest.raises(ValueError):
            curate.build_job_keys(["A"], shard=(4, 4))


# ---------------------------------------------------------------------------
# The async engine: independent completions, concurrency, resume, errors
# ---------------------------------------------------------------------------


class _RecordingClient:
    """Logs every prompt it was asked to complete -- used to verify
    INDEPENDENT COMPLETIONS (each call gets a bare prompt with no history)."""

    def __init__(self):
        self.prompts: list[str] = []

    async def complete(self, prompt: str, max_tokens: int) -> str:
        self.prompts.append(prompt)
        return "5"


class _ConcurrencyTrackingClient:
    def __init__(self):
        self.current = 0
        self.max_seen = 0
        self._lock = asyncio.Lock()

    async def complete(self, prompt: str, max_tokens: int) -> str:
        async with self._lock:
            self.current += 1
            self.max_seen = max(self.max_seen, self.current)
        await asyncio.sleep(0.02)
        async with self._lock:
            self.current -= 1
        return "5"


class _FailsForOnePromptClient:
    """Fails (non-transient) for exactly one prompt's text, succeeds for
    everything else -- used to check that a failed job is left off the
    output file (so a later run can retry it) rather than silently
    dropped or corrupting the file."""

    def __init__(self, fail_prompt: str):
        self.fail_prompt = fail_prompt
        self.calls = 0

    async def complete(self, prompt: str, max_tokens: int) -> str:
        self.calls += 1
        if prompt == self.fail_prompt:
            raise ValueError("simulated permanent failure")
        return "5"


class _AlwaysTransientClient:
    """Always raises TransientCallError -- every job exhausts its full
    retry budget and ends as an error."""

    async def complete(self, prompt: str, max_tokens: int) -> str:
        raise curate.TransientCallError("simulated persistent rate limit")


class TestRunCurationJobsEngine:
    def test_independent_completions_no_shared_history(self, tmp_path):
        rows = _vignette_rows("ENV-MB-01", "MB")[:1]
        client = _RecordingClient()
        out_path = tmp_path / "raw.jsonl"
        asyncio.run(
            curate.run_curation_jobs(rows, client=client, reviewer_model="rev", out_path=out_path)
        )
        assert len(client.prompts) == len(constants.CURATION_QUESTIONS)
        for field, question in constants.CURATION_QUESTIONS.items():
            expected = constants.CURATION_PROMPT_TEMPLATE.format(scenario=rows[0].scenario, question=question)
            assert expected in client.prompts
        # No prompt contains another question's wording -- proof nothing
        # was chained/accumulated across the 4 independent calls.
        for p in client.prompts:
            this_field_questions = [q for q in constants.CURATION_QUESTIONS.values() if q in p]
            assert len(this_field_questions) == 1

    def test_concurrency_semaphore_limits_in_flight_calls(self, tmp_path):
        rows = _vignette_rows("ENV-MB-01", "MB") + _vignette_rows("ENV-MG-01", "MG")
        client = _ConcurrencyTrackingClient()
        out_path = tmp_path / "raw.jsonl"
        asyncio.run(
            curate.run_curation_jobs(
                rows, client=client, reviewer_model="rev", out_path=out_path, concurrency=3,
            )
        )
        assert client.max_seen <= 3
        assert client.max_seen >= 2  # evidence real overlap happened, not accidental seriality

    def test_resume_in_process_second_call_only_does_remaining(self, tmp_path):
        """Calling run_curation_jobs a second time is a faithful resume
        because it reads its checkpoint state (completed job keys) ONLY
        from out_path on disk -- never from anything held in memory by the
        first call. Using a brand-new client instance for the second call
        rules out any accidental in-memory cache on the client too."""
        rows = _vignette_rows("ENV-MB-01", "MB")
        out_path = tmp_path / "raw.jsonl"
        total_jobs = len(rows) * len(constants.CURATION_QUESTIONS)

        client1 = curate.MockClient()
        telemetry1 = asyncio.run(
            curate.run_curation_jobs(
                rows, client=client1, reviewer_model="rev", out_path=out_path, limit=5,
            )
        )
        assert telemetry1.n_jobs_run == 5
        assert telemetry1.n_jobs_skipped == 0
        assert len(out_path.read_text().splitlines()) == 5

        client2 = curate.MockClient()  # fresh instance -- no shared state with client1
        telemetry2 = asyncio.run(
            curate.run_curation_jobs(rows, client=client2, reviewer_model="rev", out_path=out_path)
        )
        assert telemetry2.n_jobs_skipped == 5
        assert telemetry2.n_jobs_run == total_jobs - 5
        assert len(client2.calls) == total_jobs - 5  # only the remaining jobs were called

        final_keys = {(r.variant_id, r.field) for r in read_jsonl(out_path, CurationRawResult)}
        assert final_keys == set(curate.build_job_keys([r.variant_id for r in rows]))

    def test_failed_job_left_unresolved_for_retry(self, tmp_path):
        rows = _vignette_rows("ENV-MB-01", "MB")[:1]
        out_path = tmp_path / "raw.jsonl"
        fail_prompt = constants.CURATION_PROMPT_TEMPLATE.format(
            scenario=rows[0].scenario, question=constants.CURATION_QUESTIONS["severity"],
        )
        client = _FailsForOnePromptClient(fail_prompt)

        telemetry = asyncio.run(
            curate.run_curation_jobs(rows, client=client, reviewer_model="rev", out_path=out_path)
        )
        assert telemetry.n_errors == 1
        assert telemetry.n_jobs_run == len(constants.CURATION_QUESTIONS) - 1

        keys_on_disk = {(r.variant_id, r.field) for r in read_jsonl(out_path, CurationRawResult)}
        assert ("ENV-MB-01-A", "severity") not in keys_on_disk  # left off, not corrupted-in

        # A subsequent run with a working client picks the failed job back up.
        client2 = curate.MockClient()
        telemetry2 = asyncio.run(
            curate.run_curation_jobs(rows, client=client2, reviewer_model="rev", out_path=out_path)
        )
        assert telemetry2.n_jobs_run == 1
        keys_on_disk_2 = {(r.variant_id, r.field) for r in read_jsonl(out_path, CurationRawResult)}
        assert ("ENV-MB-01-A", "severity") in keys_on_disk_2

    def test_exhausted_retries_counted_in_telemetry(self, tmp_path):
        """Regression: a job that fails ALL its retry attempts (not just
        one that eventually succeeds) must still have those retries show
        up in RunTelemetry.n_retries -- previously only the success path
        incremented n_retries, so an exhausted-retry job silently
        contributed 0 retries to the run's cost telemetry even though it
        spent its full retry budget."""
        rows = _vignette_rows("ENV-MB-01", "MB")[:1]
        out_path = tmp_path / "raw.jsonl"
        client = _AlwaysTransientClient()

        telemetry = asyncio.run(
            curate.run_curation_jobs(
                rows, client=client, reviewer_model="rev", out_path=out_path,
                max_retries=3, sleep=_fast_sleep,
            )
        )
        assert telemetry.n_errors == len(constants.CURATION_QUESTIONS)
        # Each of the 4 jobs exhausted 3 attempts -> 2 retries each.
        assert telemetry.n_retries == 2 * len(constants.CURATION_QUESTIONS)


# ---------------------------------------------------------------------------
# assemble_curated: never coerce unparseable
# ---------------------------------------------------------------------------


class TestAssembleCurated:
    def test_unparseable_never_coerces(self):
        rows = _vignette_rows("ENV-MB-01", "MB")[:1]
        raw = [
            CurationRawResult(
                variant_id="ENV-MB-01-A", field="severity", value=None, ok=False,
                raw="not a number at all", reviewer_model="rev", timestamp=0.0,
            )
        ]
        curated = curate.assemble_curated(rows, raw, reviewer_model="rev", curation_date="2026-01-01")
        row = curated[0]
        assert row.severity is None
        assert row.severity_raw == "not a number at all"
        assert "severity" in row.individual_flags
        assert "unparseable" in row.individual_flags

    def test_parseable_populates_field_and_raw(self):
        rows = _vignette_rows("ENV-MB-01", "MB")[:1]
        raw = [
            CurationRawResult(
                variant_id="ENV-MB-01-A", field=field, value=7, ok=True,
                raw="7", reviewer_model="rev", timestamp=0.0,
            )
            for field in constants.CURATION_QUESTIONS
        ]
        curated = curate.assemble_curated(rows, raw, reviewer_model="rev", curation_date="2026-01-01")
        row = curated[0]
        assert row.severity == 7
        assert row.severity_raw == "7"
        assert row.individual_flags == ""  # all 4 fields present + parseable -> no flags

    def test_missing_result_flagged_and_empty(self):
        rows = _vignette_rows("ENV-MB-01", "MB")[:1]
        curated = curate.assemble_curated(rows, [], reviewer_model="rev", curation_date="2026-01-01")
        row = curated[0]
        assert row.severity is None
        assert row.severity_raw == ""
        assert "missing curation result" in row.individual_flags

    def test_accepted_starts_false(self):
        rows = _vignette_rows("ENV-MB-01", "MB")[:1]
        curated = curate.assemble_curated(rows, [], reviewer_model="rev", curation_date="2026-01-01")
        assert curated[0].accepted is False


# ---------------------------------------------------------------------------
# merge_prior_acceptance -- CRITICAL regression: re-running `curate run`
# against an existing --out file must not silently wipe recorded
# `accepted` decisions (reviewer found this destroys the documented
# reject -> revise -> re-ingest -> re-run revision workflow, since that
# workflow necessarily re-invokes `curate run` on the whole vignette set).
# ---------------------------------------------------------------------------


class TestMergePriorAcceptance:
    def test_no_prior_file_is_a_no_op(self, tmp_path):
        rows = [_curated_row(family_id="F-MB-01")]
        n, reset = curate.merge_prior_acceptance(rows, tmp_path / "does_not_exist.csv")
        assert n == 0
        assert reset == []
        assert rows[0].accepted is False

    def test_preserves_accepted_true_across_rerun_when_ratings_unchanged(self, tmp_path):
        out_path = tmp_path / "curated.csv"
        prior = _curated_row(family_id="F-MB-01", severity=5, accepted=True)
        write_csv_validated([prior], out_path, CuratedRow)

        fresh = _curated_row(family_id="F-MB-01", severity=5, accepted=False)
        n, reset = curate.merge_prior_acceptance([fresh], out_path)
        assert n == 1
        assert reset == []
        assert fresh.accepted is True

    def test_does_not_touch_already_unaccepted_rows(self, tmp_path):
        out_path = tmp_path / "curated.csv"
        prior = _curated_row(family_id="F-MB-01", accepted=False)
        write_csv_validated([prior], out_path, CuratedRow)

        fresh = _curated_row(family_id="F-MB-01", accepted=False)
        n, reset = curate.merge_prior_acceptance([fresh], out_path)
        assert n == 0
        assert reset == []
        assert fresh.accepted is False

    def test_previously_accepted_row_with_changed_ratings_resets_to_unaccepted(self, tmp_path):
        """Important regression (re-review finding): a previously-accepted
        row whose curation ratings changed this run (e.g. a job that
        failed last time got a real value this time, possibly tripping a
        brand-new flag) must NOT silently keep accepted=True -- nobody has
        reviewed the item in its current form. It must reset to False and
        be reported back to the caller so a human notices."""
        out_path = tmp_path / "curated.csv"
        prior = _curated_row(family_id="F-MB-01", severity=5, accepted=True)
        write_csv_validated([prior], out_path, CuratedRow)

        fresh = _curated_row(family_id="F-MB-01", severity=9, accepted=False)  # rating changed
        n, reset = curate.merge_prior_acceptance([fresh], out_path)
        assert n == 0
        assert reset == [fresh.variant_id]
        assert fresh.accepted is False

    def test_previously_accepted_row_with_unchanged_ratings_stays_accepted(self, tmp_path):
        """Companion case to the reset regression above: when the ratings
        genuinely did NOT change (the common resume-skipped case),
        accepted=True must still survive -- this is the original Critical
        fix's behavior and must not regress alongside the reset fix."""
        out_path = tmp_path / "curated.csv"
        prior = _curated_row(family_id="F-MB-01", severity=5, vividness=3, accepted=True)
        write_csv_validated([prior], out_path, CuratedRow)

        fresh = _curated_row(family_id="F-MB-01", severity=5, vividness=3, accepted=False)
        n, reset = curate.merge_prior_acceptance([fresh], out_path)
        assert n == 1
        assert reset == []
        assert fresh.accepted is True

    def test_carries_forward_reviewer_model_and_date_when_ratings_unchanged(self, tmp_path):
        out_path = tmp_path / "curated.csv"
        prior = _curated_row(
            family_id="F-MB-01", severity=5, reviewer_model="old-model", curation_date="2020-01-01",
        )
        write_csv_validated([prior], out_path, CuratedRow)

        fresh = _curated_row(
            family_id="F-MB-01", severity=5, reviewer_model="new-model", curation_date="2026-01-01",
        )
        curate.merge_prior_acceptance([fresh], out_path)
        assert fresh.reviewer_model == "old-model"
        assert fresh.curation_date == "2020-01-01"

    def test_does_not_carry_forward_model_date_when_ratings_changed(self, tmp_path):
        out_path = tmp_path / "curated.csv"
        prior = _curated_row(
            family_id="F-MB-01", severity=5, reviewer_model="old-model", curation_date="2020-01-01",
        )
        write_csv_validated([prior], out_path, CuratedRow)

        fresh = _curated_row(
            family_id="F-MB-01", severity=9, reviewer_model="new-model", curation_date="2026-01-01",
        )
        curate.merge_prior_acceptance([fresh], out_path)
        assert fresh.reviewer_model == "new-model"
        assert fresh.curation_date == "2026-01-01"

    def test_new_variant_not_in_prior_file_is_untouched(self, tmp_path):
        out_path = tmp_path / "curated.csv"
        prior = _curated_row(family_id="F-MB-01", variant_id="F-MB-01-A", accepted=True)
        write_csv_validated([prior], out_path, CuratedRow)

        new_row = _curated_row(family_id="F-MB-02", variant_id="F-MB-02-A", accepted=False)
        n, reset = curate.merge_prior_acceptance([new_row], out_path)
        assert n == 0
        assert reset == []
        assert new_row.accepted is False

    def test_unreadable_prior_file_tolerated(self, tmp_path):
        out_path = tmp_path / "curated.csv"
        out_path.write_text("not,a,valid,curated,csv\n1,2,3,4,5\n", encoding="utf-8")
        rows = [_curated_row(family_id="F-MB-01")]
        n, reset = curate.merge_prior_acceptance(rows, out_path)  # must not raise
        assert n == 0
        assert reset == []
        assert rows[0].accepted is False


# ---------------------------------------------------------------------------
# check_pairs (severity match + vividness gap)
# ---------------------------------------------------------------------------


class TestCheckPairs:
    def test_matched_pair_no_flag(self):
        config = curate.CurationConfig()
        low = _curated_row(family_id="F-MB-01", typicality="common", evocativeness="low", severity=5, vividness=2)
        high = _curated_row(family_id="F-MB-01", typicality="common", evocativeness="high", severity=6, vividness=6)
        curate.check_pairs([low, high], config)
        assert low.pair_flag == ""
        assert high.pair_flag == ""

    def test_severity_mismatch_flagged(self):
        config = curate.CurationConfig()
        low = _curated_row(family_id="F-MB-01", typicality="common", evocativeness="low", severity=1, vividness=1)
        high = _curated_row(family_id="F-MB-01", typicality="common", evocativeness="high", severity=9, vividness=8)
        curate.check_pairs([low, high], config)
        assert "severity mismatch" in low.pair_flag
        assert "severity mismatch" in high.pair_flag

    def test_vividness_gap_too_small_flagged(self):
        config = curate.CurationConfig()
        low = _curated_row(family_id="F-MB-01", typicality="common", evocativeness="low", severity=5, vividness=5)
        high = _curated_row(family_id="F-MB-01", typicality="common", evocativeness="high", severity=6, vividness=5)
        curate.check_pairs([low, high], config)
        assert "vividness gap too small" in low.pair_flag
        assert "vividness gap too small" in high.pair_flag

    def test_unpaired_or_unparseable_rows_skipped(self):
        config = curate.CurationConfig()
        lonely = _curated_row(family_id="F-MB-02", typicality="common", evocativeness="low", severity=5, vividness=5)
        curate.check_pairs([lonely], config)  # no high counterpart -- must not raise
        assert lonely.pair_flag == ""

        low = _curated_row(family_id="F-MB-03", typicality="common", evocativeness="low", severity=None, vividness=5)
        high = _curated_row(family_id="F-MB-03", typicality="common", evocativeness="high", severity=9, vividness=1)
        curate.check_pairs([low, high], config)  # unparseable severity -- skipped, not raised
        assert low.pair_flag == ""
        assert high.pair_flag == ""


# ---------------------------------------------------------------------------
# check_typicality_manipulation (DR §5.1)
# ---------------------------------------------------------------------------


class TestCheckTypicalityManipulation:
    def test_common_exceeds_uncommon_no_flag(self):
        rows = [
            _curated_row(family_id="F-MB-01", typicality="common", evocativeness="low", typicality_perception=8),
            _curated_row(family_id="F-MB-01", typicality="common", evocativeness="high", typicality_perception=9),
            _curated_row(family_id="F-MB-01", typicality="uncommon", evocativeness="low", typicality_perception=2),
            _curated_row(family_id="F-MB-01", typicality="uncommon", evocativeness="high", typicality_perception=3),
        ]
        curate.check_typicality_manipulation(rows)
        assert all(r.pair_flag == "" for r in rows)

    def test_violation_flagged_with_prefix_on_every_row(self):
        rows = [
            _curated_row(family_id="F-MB-02", typicality="common", evocativeness="low", typicality_perception=2),
            _curated_row(family_id="F-MB-02", typicality="common", evocativeness="high", typicality_perception=3),
            _curated_row(family_id="F-MB-02", typicality="uncommon", evocativeness="low", typicality_perception=8),
            _curated_row(family_id="F-MB-02", typicality="uncommon", evocativeness="high", typicality_perception=9),
        ]
        curate.check_typicality_manipulation(rows)
        for r in rows:
            assert r.pair_flag.startswith("typicality_manipulation:") or "typicality_manipulation:" in r.pair_flag

    def test_composes_with_existing_pair_flag(self):
        rows = [
            _curated_row(family_id="F-MB-03", typicality="common", evocativeness="low", typicality_perception=2, pair_flag="existing flag"),
            _curated_row(family_id="F-MB-03", typicality="common", evocativeness="high", typicality_perception=3),
            _curated_row(family_id="F-MB-03", typicality="uncommon", evocativeness="low", typicality_perception=8),
            _curated_row(family_id="F-MB-03", typicality="uncommon", evocativeness="high", typicality_perception=9),
        ]
        curate.check_typicality_manipulation(rows)
        assert "existing flag" in rows[0].pair_flag
        assert "typicality_manipulation:" in rows[0].pair_flag

    def test_missing_side_skipped_without_error(self):
        rows = [
            _curated_row(family_id="F-MB-04", typicality="common", evocativeness="low", typicality_perception=None),
            _curated_row(family_id="F-MB-04", typicality="uncommon", evocativeness="low", typicality_perception=None),
        ]
        curate.check_typicality_manipulation(rows)  # must not raise
        assert all(r.pair_flag == "" for r in rows)


# ---------------------------------------------------------------------------
# check_category_manipulation (DR §13)
# ---------------------------------------------------------------------------


class TestCheckCategoryManipulation:
    def test_mb_below_moral_min_flagged(self):
        config = curate.CurationConfig()
        row = _curated_row(valence="MB", moral_relevance=3)
        curate.check_category_manipulation([row], config)
        assert "category_manipulation" in row.individual_flags
        assert "moral_min" in row.individual_flags

    def test_mb_at_or_above_moral_min_not_flagged(self):
        config = curate.CurationConfig()
        row = _curated_row(valence="MB", moral_relevance=6)
        curate.check_category_manipulation([row], config)
        assert row.individual_flags == ""

    def test_nmb_above_nonmoral_max_flagged(self):
        config = curate.CurationConfig()
        row = _curated_row(valence="NMB", nonmoral_subdomain="etiquette", moral_relevance=7)
        curate.check_category_manipulation([row], config)
        assert "category_manipulation" in row.individual_flags
        assert "nonmoral_max" in row.individual_flags

    def test_neu_above_nonmoral_max_flagged(self):
        config = curate.CurationConfig()
        row = _curated_row(valence="NEU", sign="na", moral_relevance=8)
        curate.check_category_manipulation([row], config)
        assert "category_manipulation" in row.individual_flags

    def test_nmb_at_or_below_nonmoral_max_not_flagged(self):
        config = curate.CurationConfig()
        row = _curated_row(valence="NMB", nonmoral_subdomain="etiquette", moral_relevance=4)
        curate.check_category_manipulation([row], config)
        assert row.individual_flags == ""

    def test_unparseable_moral_relevance_skipped(self):
        config = curate.CurationConfig()
        row = _curated_row(valence="MB", moral_relevance=None)
        curate.check_category_manipulation([row], config)  # must not raise
        assert row.individual_flags == ""

    def test_composes_with_existing_individual_flags(self):
        config = curate.CurationConfig()
        row = _curated_row(valence="MB", moral_relevance=2, individual_flags="some earlier flag")
        curate.check_category_manipulation([row], config)
        assert "some earlier flag" in row.individual_flags
        assert "category_manipulation" in row.individual_flags


# ---------------------------------------------------------------------------
# CurationConfig loading
# ---------------------------------------------------------------------------


class TestLoadCurationConfig:
    def test_loads_real_config(self):
        config = curate.load_curation_config(CURATION_YAML)
        assert config.severity_match_max_diff == 2
        assert config.vividness_min_gap == 2
        assert config.moral_min == 6
        assert config.nonmoral_max == 4


# ---------------------------------------------------------------------------
# report_distributions (text + PNGs, matplotlib Agg backend)
# ---------------------------------------------------------------------------


class TestReportDistributions:
    def test_writes_text_and_pngs(self, tmp_path):
        config = curate.CurationConfig()
        rows = [
            _curated_row(family_id="F-MB-01", valence="MB", typicality="common", evocativeness="low", severity=5, vividness=2, moral_relevance=8),
            _curated_row(family_id="F-MB-01", valence="MB", typicality="common", evocativeness="high", severity=6, vividness=6, moral_relevance=9),
            _curated_row(family_id="F-NMB-01", valence="NMB", nonmoral_subdomain="etiquette", typicality="common", evocativeness="low", severity=3, vividness=1, moral_relevance=2),
            _curated_row(family_id="F-NMB-01", valence="NMB", nonmoral_subdomain="etiquette", typicality="common", evocativeness="high", severity=4, vividness=4, moral_relevance=3),
        ]
        report_dir = tmp_path / "reports"
        text = curate.report_distributions(rows, config, report_dir)

        assert "severity" in text.lower()
        assert (report_dir / "curation_distribution_report.txt").exists()
        assert (report_dir / "severity_delta_hist.png").exists()
        assert (report_dir / "vividness_gap_hist.png").exists()
        assert (report_dir / "moral_relevance_by_group.png").exists()
        for png in report_dir.glob("*.png"):
            assert png.stat().st_size > 0

    def test_handles_no_matched_pairs_gracefully(self, tmp_path):
        config = curate.CurationConfig()
        rows = [_curated_row(family_id="F-MB-01", moral_relevance=8)]  # unpaired, no severity/vividness
        report_dir = tmp_path / "reports"
        text = curate.report_distributions(rows, config, report_dir)
        assert "No matched pairs" in text
        assert (report_dir / "curation_distribution_report.txt").exists()


# ---------------------------------------------------------------------------
# review_curated (acceptance workflow)
# ---------------------------------------------------------------------------


class TestReviewCurated:
    def _write_curated(self, tmp_path: Path, rows: list[CuratedRow]) -> Path:
        path = tmp_path / "curated.csv"
        write_csv_validated(rows, path, CuratedRow)
        return path

    def test_accept_unflagged_batch_mode(self, tmp_path):
        flagged = _curated_row(family_id="F-MB-01", pair_flag="some issue")
        clean = _curated_row(family_id="F-MB-02", variant_id="F-MB-02-A")
        path = self._write_curated(tmp_path, [flagged, clean])

        rc = curate.review_curated(path, accept_unflagged=True, print_fn=lambda *a: None)
        assert rc == 0

        result_rows = read_csv_validated(path, CuratedRow)
        by_variant = {r.variant_id: r for r in result_rows}
        assert by_variant[flagged.variant_id].accepted is False
        assert by_variant[clean.variant_id].accepted is True

    def test_interactive_accept_all(self, tmp_path):
        rows = [_curated_row(family_id="F-MB-01", pair_flag="issue")]
        path = self._write_curated(tmp_path, rows)

        rc = curate.review_curated(
            path, input_fn=lambda _prompt: "a", print_fn=lambda *a: None,
        )
        assert rc == 0
        result_rows = read_csv_validated(path, CuratedRow)
        assert result_rows[0].accepted is True

    def test_interactive_reject_flagged_keeps_unflagged(self, tmp_path):
        flagged = _curated_row(family_id="F-MB-01", variant_id="F-MB-01-A", pair_flag="issue")
        clean = _curated_row(family_id="F-MB-01", variant_id="F-MB-01-B")
        path = self._write_curated(tmp_path, [flagged, clean])

        printed = []
        rc = curate.review_curated(
            path, input_fn=lambda _prompt: "r", print_fn=lambda *a: printed.append(" ".join(str(x) for x in a)),
        )
        assert rc == 0
        result_rows = {r.variant_id: r for r in read_csv_validated(path, CuratedRow)}
        assert result_rows["F-MB-01-A"].accepted is False  # stays rejected
        assert result_rows["F-MB-01-B"].accepted is True  # unflagged row accepted
        assert any("re-enter" in line or "generate ingest" in line for line in printed)

    def test_interactive_skip_leaves_unchanged(self, tmp_path):
        rows = [_curated_row(family_id="F-MB-01", pair_flag="issue", accepted=False)]
        path = self._write_curated(tmp_path, rows)

        rc = curate.review_curated(path, input_fn=lambda _prompt: "s", print_fn=lambda *a: None)
        assert rc == 0
        result_rows = read_csv_validated(path, CuratedRow)
        assert result_rows[0].accepted is False

    def test_unflagged_family_not_prompted(self, tmp_path):
        rows = [_curated_row(family_id="F-MB-01")]  # no flags at all
        path = self._write_curated(tmp_path, rows)

        def _fail_if_called(_prompt):
            raise AssertionError("should not prompt for a family with no flagged rows")

        rc = curate.review_curated(path, input_fn=_fail_if_called, print_fn=lambda *a: None)
        assert rc == 0

    def test_atomic_rewrite_leaves_valid_csv_even_if_interrupted_conceptually(self, tmp_path):
        # Not a true crash-injection test, but pins that writes go through a
        # temp file + os.replace (curate._atomic_write_csv), so a reader
        # never observes a partially-written curated.csv.
        rows = [_curated_row(family_id="F-MB-01")]
        path = self._write_curated(tmp_path, rows)
        curate.review_curated(path, accept_unflagged=True, print_fn=lambda *a: None)
        assert not path.with_suffix(".csv.tmp").exists()
        # Must still be fully valid per-schema after the rewrite.
        read_csv_validated(path, CuratedRow)


# ---------------------------------------------------------------------------
# CLI integration (subprocess -- genuine separate-process runs)
# ---------------------------------------------------------------------------


def _write_vignettes_csv(path: Path, families: list[tuple[str, str, str]]) -> list[VignetteRow]:
    """families: list of (family_id, valence, nonmoral_subdomain)."""
    rows: list[VignetteRow] = []
    for family_id, valence, subdomain in families:
        rows.extend(_vignette_rows(family_id, valence, nonmoral_subdomain=subdomain))
    write_csv_validated(rows, path, VignetteRow)
    return rows


def _run_curate(tmp_path: Path, vignettes_csv: Path, *, curation_date: str) -> int:
    return curate.run(
        vignettes_csv,
        reviewer_model="claude-sonnet-4-6",
        mock=True,
        out=tmp_path / "curated.csv",
        raw_out=tmp_path / "curated_raw.jsonl",
        report_dir=tmp_path / "reports",
        runlog_path=tmp_path / "curation_runlog.jsonl",
        curation_date=curation_date,
    )


class TestRunPreservesAcceptedAcrossReruns:
    """CRITICAL regression (reviewer-reported): `curate run` was silently
    reverting every previously-recorded `accepted` decision on each rerun,
    which breaks the documented reject -> revise -> re-ingest -> re-run
    revision workflow (that workflow necessarily re-invokes `curate run`
    on the whole vignette set, which would wipe every OTHER family's
    already-reviewed decisions along with the one being revised)."""

    def test_accept_via_review_then_rerun_survives(self, tmp_path, capsys):
        vignettes_csv = tmp_path / "vignettes.csv"
        _write_vignettes_csv(vignettes_csv, [("ENV-MB-01", "MB", "")])
        out_path = tmp_path / "curated.csv"

        assert _run_curate(tmp_path, vignettes_csv, curation_date="2026-01-01") == 0
        capsys.readouterr()  # discard first run's output

        # A human reviews and accepts the whole family.
        curate.review_curated(out_path, input_fn=lambda _p: "a", print_fn=lambda *a: None)
        accepted_before = {r.variant_id: r.accepted for r in read_csv_validated(out_path, CuratedRow)}
        assert accepted_before and all(accepted_before.values())
        dates_before = {r.variant_id: r.curation_date for r in read_csv_validated(out_path, CuratedRow)}

        # Re-run `curate run` against the SAME vignettes + SAME raw
        # checkpoint (every job is resume-skipped) -- exactly the
        # "re-run curation" step of the revision workflow, and exactly
        # what the reviewer reproduced.
        assert _run_curate(tmp_path, vignettes_csv, curation_date="2026-01-02") == 0
        stdout = capsys.readouterr().out
        assert "Preserved 4 prior acceptance decision" in stdout

        result_rows = read_csv_validated(out_path, CuratedRow)
        accepted_after = {r.variant_id: r.accepted for r in result_rows}
        assert accepted_after == accepted_before
        assert all(accepted_after.values())  # not silently reverted to False

        # These items weren't actually recurated (jobs were all skipped via
        # resume, identical raw results) -- curation_date should still
        # reflect the ORIGINAL curation, not today's incidental rerun.
        dates_after = {r.variant_id: r.curation_date for r in result_rows}
        assert dates_after == dates_before
        assert all(d == "2026-01-01" for d in dates_after.values())

    def test_new_variants_added_default_unaccepted_existing_preserved(self, tmp_path):
        vignettes_csv = tmp_path / "vignettes.csv"
        existing_rows = _write_vignettes_csv(vignettes_csv, [("ENV-MB-01", "MB", "")])
        out_path = tmp_path / "curated.csv"

        assert _run_curate(tmp_path, vignettes_csv, curation_date="2026-01-01") == 0
        curate.review_curated(out_path, input_fn=lambda _p: "a", print_fn=lambda *a: None)
        assert all(r.accepted for r in read_csv_validated(out_path, CuratedRow))

        # New items are added to vignettes.csv between curation runs (e.g.
        # a fresh family, or -- per the revision workflow -- a revised
        # family re-ingested under a new "rN" family_id).
        new_rows = _vignette_rows("ENV-MG-01", "MG")
        write_csv_validated(existing_rows + new_rows, vignettes_csv, VignetteRow)

        assert _run_curate(tmp_path, vignettes_csv, curation_date="2026-01-02") == 0

        result_rows = {r.variant_id: r for r in read_csv_validated(out_path, CuratedRow)}
        assert len(result_rows) == 8
        for row in existing_rows:
            assert result_rows[row.variant_id].accepted is True  # preserved
            assert result_rows[row.variant_id].curation_date == "2026-01-01"  # unchanged ratings
        for row in new_rows:
            assert result_rows[row.variant_id].accepted is False  # new item, default
            assert result_rows[row.variant_id].curation_date == "2026-01-02"  # freshly curated

    def test_ratings_change_resets_prior_acceptance_with_notice(self, tmp_path, capsys):
        """Important regression (re-review finding): merge_prior_acceptance
        was carrying accepted=True forward UNCONDITIONALLY, even when a
        row's curation ratings changed between runs (e.g. a job that
        failed last time -- leaving a field empty -- succeeds this time,
        possibly tripping a brand-new flag). A human accepted the item as
        it looked before; nobody has reviewed its current form, so it must
        reset to unaccepted with a printed notice, not silently stay
        accepted."""
        vignettes_csv = tmp_path / "vignettes.csv"
        rows = _write_vignettes_csv(vignettes_csv, [("ENV-MB-01", "MB", "")])
        out_path = tmp_path / "curated.csv"
        raw_path = tmp_path / "curated_raw.jsonl"

        # "Run 1": ENV-MB-01-A's severity job fails outright (simulating a
        # job that never completed) -- everything else succeeds normally.
        fail_prompt = constants.CURATION_PROMPT_TEMPLATE.format(
            scenario=rows[0].scenario, question=constants.CURATION_QUESTIONS["severity"],
        )
        client1 = _FailsForOnePromptClient(fail_prompt)
        asyncio.run(
            curate.run_curation_jobs(
                rows, client=client1, reviewer_model="claude-sonnet-4-6", out_path=raw_path,
            )
        )
        raw_results = curate._read_raw_results_tolerant(raw_path)
        curated_rows = curate.assemble_curated(
            rows, raw_results, reviewer_model="claude-sonnet-4-6", curation_date="2026-01-01",
        )
        write_csv_validated(curated_rows, out_path, CuratedRow)

        # A human reviews and accepts the whole family anyway (despite the
        # missing severity field on ENV-MB-01-A).
        curate.review_curated(out_path, input_fn=lambda _p: "a", print_fn=lambda *a: None)
        prior = {r.variant_id: r for r in read_csv_validated(out_path, CuratedRow)}
        assert prior["ENV-MB-01-A"].accepted is True
        assert prior["ENV-MB-01-A"].severity is None
        for vid in ("ENV-MB-01-B", "ENV-MB-01-C", "ENV-MB-01-D"):
            assert prior[vid].accepted is True

        # "Run 2": a real `curate run` (normal MockClient) -- the
        # previously-failed severity job now succeeds, so ENV-MB-01-A's
        # ratings genuinely change; the other 3 rows are untouched
        # (resume-skipped, identical ratings).
        capsys.readouterr()
        rc = _run_curate(tmp_path, vignettes_csv, curation_date="2026-01-02")
        assert rc == 0
        stdout = capsys.readouterr().out
        assert "1 previously-accepted row(s) had ratings change" in stdout
        assert "ENV-MB-01-A" in stdout

        result = {r.variant_id: r for r in read_csv_validated(out_path, CuratedRow)}
        assert result["ENV-MB-01-A"].severity is not None  # genuinely recurated
        assert result["ENV-MB-01-A"].accepted is False  # reset -- needs re-review
        for vid in ("ENV-MB-01-B", "ENV-MB-01-C", "ENV-MB-01-D"):
            assert result[vid].accepted is True  # unaffected rows keep their prior accept


class TestCLIRunMock:
    def test_full_mock_path_zero_network(self, tmp_path):
        vignettes_csv = tmp_path / "vignettes.csv"
        _write_vignettes_csv(vignettes_csv, [("ENV-MB-01", "MB", "")])

        result = subprocess.run(
            [
                sys.executable, "-m", "knobe.cli", "curate", "run", str(vignettes_csv),
                "--reviewer-model", "claude-sonnet-4-6", "--mock",
                "--out", str(tmp_path / "curated.csv"),
                "--raw", str(tmp_path / "curated_raw.jsonl"),
                "--report-dir", str(tmp_path / "reports"),
                "--curation-date", "2026-01-01",
            ],
            capture_output=True, text=True, timeout=60, cwd=tmp_path,
        )
        assert result.returncode == 0, result.stderr
        assert (tmp_path / "curated.csv").exists()
        assert (tmp_path / "curated_raw.jsonl").exists()
        assert (tmp_path / "reports" / "curation_distribution_report.txt").exists()

        curated_rows = read_csv_validated(tmp_path / "curated.csv", CuratedRow)
        assert len(curated_rows) == 4  # one family, 4 variants

        raw_lines = [json.loads(line) for line in (tmp_path / "curated_raw.jsonl").read_text().splitlines()]
        assert len(raw_lines) == 4 * len(constants.CURATION_QUESTIONS)

    def test_reviewer_conflict_fails_fast_no_jobs_run(self, tmp_path):
        vignettes_csv = tmp_path / "vignettes.csv"
        _write_vignettes_csv(vignettes_csv, [("ENV-MB-01", "MB", "")])
        raw_path = tmp_path / "curated_raw.jsonl"

        result = subprocess.run(
            [
                sys.executable, "-m", "knobe.cli", "curate", "run", str(vignettes_csv),
                "--reviewer-model", "meta-llama/Llama-3.1-8B", "--mock",
                "--out", str(tmp_path / "curated.csv"), "--raw", str(raw_path),
            ],
            capture_output=True, text=True, timeout=60, cwd=tmp_path,
        )
        assert result.returncode != 0
        assert "reviewer" in result.stderr.lower() or "subject" in result.stderr.lower()
        assert not raw_path.exists()  # no jobs were ever run


class TestCLIResumeAcrossProcesses:
    """The definitive resume test: two SEPARATE OS processes (real
    kill/restart, not a warm in-memory cache), sharing only the on-disk
    curated_raw.jsonl checkpoint file."""

    def test_kill_restart_total_calls_equal_remaining_and_file_complete(self, tmp_path):
        vignettes_csv = tmp_path / "vignettes.csv"
        rows = _write_vignettes_csv(vignettes_csv, [("ENV-MB-01", "MB", ""), ("ENV-MG-01", "MG", "")])
        total_jobs = len(rows) * len(constants.CURATION_QUESTIONS)
        raw_path = tmp_path / "curated_raw.jsonl"
        runlog_path = tmp_path / "curation_runlog.jsonl"

        base_cmd = [
            sys.executable, "-m", "knobe.cli", "curate", "run", str(vignettes_csv),
            "--reviewer-model", "claude-sonnet-4-6", "--mock",
            "--out", str(tmp_path / "curated.csv"), "--raw", str(raw_path),
            "--runlog", str(runlog_path), "--report-dir", str(tmp_path / "reports"),
            "--curation-date", "2026-01-01",
        ]

        # "Run half, kill": first process only does the first half of the jobs.
        half = total_jobs // 2
        first = subprocess.run(base_cmd + ["--limit", str(half)], capture_output=True, text=True, timeout=60, cwd=tmp_path)
        assert first.returncode == 0, first.stderr
        assert len(raw_path.read_text().splitlines()) == half

        # "Restart": a brand-new process, no --limit, same output paths.
        second = subprocess.run(base_cmd, capture_output=True, text=True, timeout=60, cwd=tmp_path)
        assert second.returncode == 0, second.stderr

        raw_lines = raw_path.read_text().splitlines()
        assert len(raw_lines) == total_jobs  # complete, no duplicates, no losses

        final_keys = [json.loads(line) for line in raw_lines]
        unique_keys = {(r["variant_id"], r["field"]) for r in final_keys}
        assert len(unique_keys) == total_jobs  # every job exactly once

        runlog_entries = [
            CurationRunLogEntry.model_validate_json(line)
            for line in runlog_path.read_text().splitlines()
        ]
        assert len(runlog_entries) == 2
        assert runlog_entries[0].n_jobs_run == half
        assert runlog_entries[0].n_jobs_skipped == 0
        assert runlog_entries[1].n_jobs_run == total_jobs - half
        assert runlog_entries[1].n_jobs_skipped == half


class TestCLIReview:
    def test_cli_review_accept_unflagged(self, tmp_path):
        curated_path = tmp_path / "curated.csv"
        rows = [
            _curated_row(family_id="F-MB-01", variant_id="F-MB-01-A"),
            _curated_row(family_id="F-MB-01", variant_id="F-MB-01-B", pair_flag="issue"),
        ]
        write_csv_validated(rows, curated_path, CuratedRow)

        result = subprocess.run(
            [sys.executable, "-m", "knobe.cli", "curate", "review", "--curated", str(curated_path), "--accept-unflagged"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, result.stderr
        result_rows = {r.variant_id: r for r in read_csv_validated(curated_path, CuratedRow)}
        assert result_rows["F-MB-01-A"].accepted is True
        assert result_rows["F-MB-01-B"].accepted is False


class TestCLIHelp:
    def test_curate_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "knobe.cli", "curate", "--help"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0
        assert "run" in result.stdout
        assert "review" in result.stdout

    def test_curate_run_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "knobe.cli", "curate", "run", "--help"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0
        assert "--reviewer-model" in result.stdout
        assert "--mock" in result.stdout
