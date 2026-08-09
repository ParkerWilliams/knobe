"""WO-2 Part C: job-manifest construction + the deterministic seeding rule
(master spec §3.5), plus the ``knobe jobs diff`` resume primitive WO-5
consumes.

Three independent pieces (kept in one module since they're small and share
no state with render.py, per the task's "render.py = rendering only;
jobs.py = config, expansion, seeding, diff" split):
  1. ``RunConfig`` -- loads/validates ``configs/run_*.yaml``.
  2. ``derive_temperature_and_seed`` / ``build_jobs`` -- the (prompt x
     model_key x sample_idx) expansion and the frozen seeding derivation.
  3. ``diff_jobs`` -- set-difference on ``job_id`` against a results file,
     tolerating a missing/empty results file (nothing done yet).

The H200 runner (WO-5) must never generate randomness itself (spec §3.5) --
every job's temperature/seed is precomputed here and shipped in
jobs.jsonl; reruns are exactly reproducible and resume is a pure
set-difference on job_id.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal, Sequence

import yaml
from pydantic import Field

from knobe import constants
from knobe.schemas import (
    JobRecord,
    KnobeModel,
    PromptRecord,
    ResultRecord,
    read_jsonl,
    write_jsonl,
)

QuestionType = Literal["intentionality", "blame", "praise", "affect_salience"]
JobFormat = Literal["raw", "chat"]

# Default question set for a run config that doesn't name one explicitly
# (WO-2 Part C item 1: "questions: [...] default all three"). Reuses
# constants.MAIN_QUESTION_COLUMNS's own key order rather than re-declaring
# the three question-type names as a separate literal list.
_DEFAULT_QUESTIONS: tuple[QuestionType, ...] = tuple(constants.MAIN_QUESTION_COLUMNS.keys())


# ---------------------------------------------------------------------------
# Run config (configs/run_*.yaml)
# ---------------------------------------------------------------------------


class RunConfig(KnobeModel):
    """One ``configs/run_*.yaml`` (WO-2 Part C item 1): release string,
    which model_keys/formats/questions to expand jobs for, and how many
    samples per (prompt, model_key)."""

    release: str
    models: list[str]
    formats: list[JobFormat]
    n_samples: int
    questions: list[QuestionType] = Field(default_factory=lambda: list(_DEFAULT_QUESTIONS))
    # WO-5 §4.4/§7: model_keys whose measured regex parse rate fell below
    # the 95% threshold in a prior G0/G1 run, and should therefore use
    # logit-fallback (expected-value-from-logprobs) scoring instead.
    # Optional/additive -- defaults to empty so every pre-existing
    # configs/run_*.yaml (and every test fixture built before WO-5) keeps
    # validating unchanged. elicit_vllm.py's runner unions this with its
    # own ``--logit-fallback`` CLI flag, so the decision can live durably
    # in version control OR be set ad hoc for one invocation.
    logit_fallback_checkpoints: list[str] = Field(default_factory=list)


def load_run_config(path: str | Path) -> RunConfig:
    path = Path(path)
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return RunConfig(**(data or {}))


# ---------------------------------------------------------------------------
# Seeding rule -- master spec §3.5, EXACT. This derivation is pinned by
# hand-computed fixtures in tests/test_jobs.py; it must never change
# silently (common-context.md constraint 4, master spec §7.5).
# ---------------------------------------------------------------------------

# The joiner IS the derivation (task-2-brief.md): rng material is the UTF-8
# bytes of "{release}|{prompt_id}|{model_key}|{sample_idx}", fields joined
# by a literal "|" in exactly this order. Changing the joiner character,
# the field order, or str()-formatting of sample_idx (e.g. zero-padding)
# would silently change every seed/temperature ever derived -- do not
# "clean this up" without a version bump and re-derivation of the fixtures.
_SEED_MATERIAL_TEMPLATE = "{release}|{prompt_id}|{model_key}|{sample_idx}"


def derive_temperature_and_seed(
    release: str, prompt_id: str, model_key: str, sample_idx: int
) -> tuple[float, int]:
    """spec §3.5: rng = sha256(release, prompt_id, model_key, sample_idx).
    temperature ~ U(0.85, 1.15) from digest[0:8] (first 8 bytes, big-endian,
    as a fraction of 2**64); seed from digest[8:16] (next 8 bytes,
    big-endian, mod 2**31). Pure function of its four inputs -- no bare
    ``random``, no time-seeded RNG (common-context.md constraint 4)."""
    material = _SEED_MATERIAL_TEMPLATE.format(
        release=release, prompt_id=prompt_id, model_key=model_key, sample_idx=sample_idx
    )
    digest = hashlib.sha256(material.encode("utf-8")).digest()

    fraction = int.from_bytes(digest[0:8], "big") / 2**64
    temperature = 0.85 + 0.30 * fraction
    seed = int.from_bytes(digest[8:16], "big") % 2**31
    return temperature, seed


# ---------------------------------------------------------------------------
# Expansion: (prompt x model_key x sample_idx) -> JobRecord
# ---------------------------------------------------------------------------


def build_jobs(
    prompts: Sequence[PromptRecord],
    *,
    release: str,
    models: Sequence[str],
    formats: Sequence[str],
    questions: Sequence[str] = _DEFAULT_QUESTIONS,
    n_samples: int,
) -> list[JobRecord]:
    """Expands filtered prompts x models x sample_idx 0..N-1 into
    JobRecords. Deterministic output ordering: prompt order as given (the
    caller passes prompts already read from a byte-stable prompts.jsonl,
    so this preserves render.py's variant_id/question/format order), then
    model_key in the order listed in the run config, then sample_idx
    ascending -- so jobs.jsonl is byte-stable across runs given the same
    inputs (WO-2 acceptance criterion)."""
    formats_set = set(formats)
    questions_set = set(questions)
    filtered = [p for p in prompts if p.format in formats_set and p.question_type in questions_set]

    jobs: list[JobRecord] = []
    for prompt in filtered:
        for model_key in models:
            for sample_idx in range(n_samples):
                temperature, seed = derive_temperature_and_seed(
                    release, prompt.prompt_id, model_key, sample_idx
                )
                jobs.append(
                    JobRecord(
                        job_id=f"{prompt.prompt_id}::{model_key}::{sample_idx}",
                        prompt_id=prompt.prompt_id,
                        model_key=model_key,
                        sample_idx=sample_idx,
                        temperature=temperature,
                        seed=seed,
                    )
                )
    return jobs


def write_jobs_jsonl(jobs: list[JobRecord], path: str | Path) -> None:
    write_jsonl(jobs, path)


# ---------------------------------------------------------------------------
# Resume primitive: knobe jobs diff (set-difference on job_id)
# ---------------------------------------------------------------------------


class DiffReport(KnobeModel):
    total: int
    done: int
    remaining: int


def read_results_tolerant(path: str | Path) -> list[ResultRecord]:
    """Reads results.jsonl, tolerating a missing or empty file (means
    nothing has been done yet -- everything is remaining), per WO-2 Part C
    item 5's resume-semantics requirement."""
    path = Path(path)
    if not path.exists() or path.stat().st_size == 0:
        return []
    return read_jsonl(path, ResultRecord)


def diff_jobs(jobs: Sequence[JobRecord], results: Sequence[ResultRecord]) -> tuple[list[JobRecord], DiffReport]:
    """Set-difference on job_id: a job is "done" iff some result carries
    its job_id (extra/unknown result ids, e.g. from a stale results file,
    are simply ignored -- they don't count against ``total``). Returns
    (remaining JobRecords, in the SAME relative order as ``jobs``; a
    counts report)."""
    done_ids = {r.job_id for r in results}
    remaining = [j for j in jobs if j.job_id not in done_ids]
    report = DiffReport(total=len(jobs), done=len(jobs) - len(remaining), remaining=len(remaining))
    return remaining, report


# ---------------------------------------------------------------------------
# CLI-facing orchestration (called by knobe.cli's "jobs build"/"jobs diff")
# ---------------------------------------------------------------------------


def run_build(config_path: str | Path, prompts_path: str | Path, out_path: str | Path) -> int:
    config = load_run_config(config_path)
    prompts = read_jsonl(prompts_path, PromptRecord)
    print(f"Loaded {len(prompts)} prompt records from {prompts_path}")

    jobs = build_jobs(
        prompts,
        release=config.release,
        models=config.models,
        formats=config.formats,
        questions=config.questions,
        n_samples=config.n_samples,
    )
    write_jobs_jsonl(jobs, out_path)
    print(f"Wrote {len(jobs)} job records to {out_path}")
    return 0


def run_diff(jobs_path: str | Path, results_path: str | Path, *, out_path: str | Path | None = None) -> int:
    jobs = read_jsonl(jobs_path, JobRecord)
    results = read_results_tolerant(results_path)
    remaining, report = diff_jobs(jobs, results)

    print(f"total={report.total} done={report.done} remaining={report.remaining}")
    if out_path is not None:
        write_jobs_jsonl(remaining, out_path)
        print(f"Wrote {len(remaining)} remaining job record(s) to {out_path}")
    return 0
