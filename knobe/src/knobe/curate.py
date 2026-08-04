"""S3: curation-stage elicitation for the vignette pipeline (WO-3; master
spec §3.3, §4). Port of the legacy ``curate_vignettes.py``, extended with
async concurrency, resume, and the acceptance workflow needed to curate
~1,000 variants x 4 questions before any item is accepted into the dataset
used for the main experiment.

Two design constraints survive verbatim from the legacy script's docstring,
both still non-negotiable:

1. INDEPENDENT COMPLETIONS. Each of the four curation checks is fired as
   its own fresh API call with no shared conversation history -- never
   chained, so C1's answer can't leak into C2's context, etc. This mirrors
   the between-subjects logic used for the main-experiment questions and is
   just as important here: a curation reviewer that has already rated an
   item's severity should not carry that judgment into its vividness
   rating. Structurally enforced: ``CurationClient.complete`` takes only a
   bare prompt string, never a message history, so there is no channel for
   state to leak between calls even by accident.

2. REVIEWER != SUBJECT. Curation must be run by a model that will NOT later
   serve as a test-subject model in the main experiment. ``--reviewer-model``
   is required and is checked at startup against every model id and family
   key in ``configs/models.yaml`` (``check_reviewer_not_subject`` below) --
   replacing the legacy script's manual ``--subject-models`` flag, which
   could accidentally be left empty.

Everything that talks to the network is optional at import time: the
``anthropic`` package is guarded (as in the legacy script) so this module
imports cleanly, and ``--mock``/``MockClient`` runs the full path with zero
network calls (needed so G0 can rehearse curation plumbing offline).
"""
from __future__ import annotations

import asyncio
import hashlib
import os
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence

import yaml

from knobe import constants
from knobe.parsing import parse_rating
from knobe.registry import Family, RegistryConfigError, load_registry
from knobe.schemas import (
    CuratedRow,
    CurationRawResult,
    CurationRunLogEntry,
    VignetteRow,
    append_jsonl,
    read_csv_validated,
    read_jsonl,
    write_csv_validated,
)

try:
    import anthropic
except ImportError:  # pragma: no cover -- exercised whenever the optional
    # 'anthropic' package isn't installed; --mock and every other code path
    # in this module never touches it.
    anthropic = None


def _repo_root() -> Path:
    """Repo root, derived from this source file's location -- same
    technique as ``generate._repo_root`` (an ordinary path helper, not a
    frozen scientific instrument, so a small local copy is fine per that
    module's own precedent)."""
    return Path(__file__).resolve().parents[2]


def default_registry_path() -> Path:
    return _repo_root() / "configs" / "models.yaml"


def default_curation_config_path() -> Path:
    return _repo_root() / "configs" / "curation.yaml"


# ---------------------------------------------------------------------------
# Reviewer != subject (WO-3 §2; master spec §4.3, DR §13)
# ---------------------------------------------------------------------------


class ReviewerSubjectConflictError(ValueError):
    """Raised when ``--reviewer-model`` overlaps a subject model in
    configs/models.yaml -- hard error at startup, per the REVIEWER !=
    SUBJECT invariant."""


def check_reviewer_not_subject(reviewer_model: str, registry: dict[str, Family]) -> None:
    """Hard-fails if ``reviewer_model`` matches any subject in ``registry``:

    - exact match (case-insensitive) against a family's full HF id
      (pretrained/finetuned/tl_name) -- e.g. reviewer "meta-llama/Llama-3.1-8B"
      exactly equals a subject's ``pretrained`` id.
    - substring match, either direction, case-insensitive, against the
      family KEY itself (e.g. registry key "llama-3.1-8b") -- e.g. reviewer
      "llama-3.1-8b-instruct" (a model_key-style string) contains the
      family key as a substring, even though it isn't a literal HF id.

    This replaces the legacy script's manual ``--subject-models`` flag: the
    subject list now comes from configs/models.yaml automatically, so
    there's no way to forget to list a subject.
    """
    reviewer_lower = reviewer_model.strip().lower()
    for family_name, family in registry.items():
        family_lower = family_name.lower()
        if family_lower in reviewer_lower or reviewer_lower in family_lower:
            raise ReviewerSubjectConflictError(
                f"--reviewer-model {reviewer_model!r} matches subject family "
                f"{family_name!r} in configs/models.yaml (family-key substring match) "
                f"-- curation must be run by a model that is NOT a test subject "
                f"(master spec §4.3, DR §13)."
            )
        for model_id in (family.pretrained, family.finetuned, family.tl_name):
            if model_id and model_id.strip().lower() == reviewer_lower:
                raise ReviewerSubjectConflictError(
                    f"--reviewer-model {reviewer_model!r} exactly matches subject model id "
                    f"{model_id!r} (family {family_name!r}) in configs/models.yaml -- "
                    f"curation must be run by a model that is NOT a test subject "
                    f"(master spec §4.3, DR §13)."
                )


# ---------------------------------------------------------------------------
# Client abstraction (WO-3 §1)
# ---------------------------------------------------------------------------


class TransientCallError(Exception):
    """Raised by a ``CurationClient`` implementation to signal a retryable
    failure (rate limit, timeout, 5xx). ``_complete_with_retry`` retries
    ONLY this exception type, with exponential backoff, up to a fixed
    number of total attempts. Any other exception is treated as
    non-transient (e.g. an auth or bad-request error that retrying can't
    fix) and propagates immediately, uncounted against the retry budget --
    "per-request retry... transient errors only" (WO-3 §1)."""


class CurationClient(Protocol):
    async def complete(self, prompt: str, max_tokens: int) -> str:
        """Fires ONE independent completion for ``prompt`` and returns the
        raw response text. Implementations must not retain or replay any
        state from prior calls (INDEPENDENT COMPLETIONS)."""
        ...


class MockClient:
    """Deterministic fake ``CurationClient`` -- no real randomness. The
    response for a given prompt is derived entirely from
    ``sha256(prompt)``, so identical prompts always produce identical
    responses, across runs and across process restarts (required for the
    --mock resume tests, and for common-context.md constraint 4: no bare /
    time-seeded randomness anywhere).

    ``unparseable_rate`` controls what (hash-determined, not random)
    fraction of prompts get a deliberately unparseable response, so the
    never-coerce path is exercised even in --mock runs.
    """

    def __init__(self, unparseable_rate: float = 0.1):
        if not (0.0 <= unparseable_rate <= 1.0):
            raise ValueError("unparseable_rate must be in [0, 1]")
        self.unparseable_rate = unparseable_rate
        self.calls: list[str] = []

    async def complete(self, prompt: str, max_tokens: int) -> str:
        self.calls.append(prompt)
        digest = hashlib.sha256(prompt.encode("utf-8")).digest()
        n = int.from_bytes(digest[:8], "big")
        if (n % 1000) / 1000 < self.unparseable_rate:
            return "unclear"
        return str(n % 11)


_TRANSIENT_ANTHROPIC_ERRORS: tuple[type, ...] = ()
if anthropic is not None:  # pragma: no cover -- only when the extra is installed
    _TRANSIENT_ANTHROPIC_ERRORS = (
        anthropic.RateLimitError,
        anthropic.APIConnectionError,
        anthropic.APITimeoutError,
        anthropic.InternalServerError,
    )


class AnthropicClient:
    """``CurationClient`` backed by the real Anthropic API
    (``AsyncAnthropic``). Every call is a brand-new
    ``client.messages.create`` with exactly one user message built from
    ``prompt`` and nothing else -- fresh context every time (INDEPENDENT
    COMPLETIONS, master spec §4.1). Requires the optional ``anthropic``
    package; raises at CONSTRUCTION time, not at import time, if it's
    missing, so --mock runs (and every other function in this module)
    never need it installed."""

    def __init__(self, model: str, api_key: str | None = None):
        if anthropic is None:
            raise RuntimeError(
                "the 'anthropic' package is required for non-mock curation runs -- "
                "install it (e.g. `uv pip install anthropic`) or pass --mock."
            )
        self.model = model
        self._client = anthropic.AsyncAnthropic(api_key=api_key) if api_key else anthropic.AsyncAnthropic()
        self.input_tokens_used = 0
        self.output_tokens_used = 0

    async def complete(self, prompt: str, max_tokens: int) -> str:
        try:
            resp = await self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                # Claude 5-generation models run adaptive thinking by default,
                # and max_tokens caps thinking + text TOGETHER -- at curation's
                # small max_tokens the whole budget goes to thinking and the
                # text comes back empty. Rating elicitation needs no thinking.
                thinking={"type": "disabled"},
                messages=[{"role": "user", "content": prompt}],
            )
        except _TRANSIENT_ANTHROPIC_ERRORS as exc:
            raise TransientCallError(str(exc)) from exc

        usage = getattr(resp, "usage", None)
        if usage is not None:
            self.input_tokens_used += getattr(usage, "input_tokens", 0) or 0
            self.output_tokens_used += getattr(usage, "output_tokens", 0) or 0
        return "".join(b.text for b in resp.content if b.type == "text").strip()


async def _complete_with_retry(
    client: CurationClient,
    prompt: str,
    max_tokens: int,
    max_retries: int,
    *,
    sleep=asyncio.sleep,
) -> tuple[str, int]:
    """Fires one completion via ``client.complete``, retrying only
    ``TransientCallError`` with exponential backoff (``sleep(2**attempt)``
    seconds), up to ``max_retries`` total attempts. Any other exception
    propagates immediately, unretried. Returns ``(response_text,
    n_retries_used)`` on success. ``sleep`` is injectable so tests can
    avoid real delays.

    On exhausting all retries, the final ``TransientCallError`` is
    re-raised with a ``retries_used`` attribute set (== the number of
    retries spent before giving up) so a caller that only sees the
    exception -- e.g. ``run_curation_jobs``'s per-job error handler, which
    counts a job as an error rather than swallowing the return value --
    can still fold those retries into its own telemetry instead of
    silently under-counting every exhausted-retry job as zero retries."""
    if max_retries < 1:
        raise ValueError("max_retries must be >= 1")
    for attempt in range(max_retries):
        try:
            text = await client.complete(prompt, max_tokens)
            return text, attempt
        except TransientCallError as exc:
            if attempt == max_retries - 1:
                exc.retries_used = attempt
                raise
            await sleep(2**attempt)
    raise AssertionError("unreachable")  # max_retries >= 1 guaranteed above


# ---------------------------------------------------------------------------
# Job assembly + the async engine (WO-3 §1)
# ---------------------------------------------------------------------------


def build_job_keys(
    variant_ids: Sequence[str],
    *,
    shard: tuple[int, int] | None = None,
    limit: int | None = None,
) -> list[tuple[str, str]]:
    """Deterministic ``(variant_id, curation_field)`` job-key list: every
    variant x every field in ``constants.CURATION_QUESTIONS``, variant-major
    order (matches the input ``variant_ids`` order), field order =
    ``CURATION_QUESTIONS``'s own key order.

    ``--shard i/n`` stripes by index (``idx % n == i``) so a shard stays
    balanced across variants rather than being one contiguous block.
    ``--limit`` truncates the (post-shard) list to its first N keys.
    """
    keys = [(vid, field) for vid in variant_ids for field in constants.CURATION_QUESTIONS]
    if shard is not None:
        i, n = shard
        if not (0 <= i < n):
            raise ValueError(f"--shard index must satisfy 0 <= i < n; got {shard}")
        keys = [k for idx, k in enumerate(keys) if idx % n == i]
    if limit is not None:
        keys = keys[:limit]
    return keys


def _read_raw_results_tolerant(path: str | Path) -> list[CurationRawResult]:
    """Reads curated_raw.jsonl, tolerating a missing or empty file (nothing
    completed yet -- everything is remaining), matching jobs.py's
    ``read_results_tolerant`` resume-semantics precedent."""
    path = Path(path)
    if not path.exists() or path.stat().st_size == 0:
        return []
    return read_jsonl(path, CurationRawResult)


@dataclass(frozen=True)
class RunTelemetry:
    n_jobs_total: int
    n_jobs_run: int
    n_jobs_skipped: int
    n_retries: int
    n_errors: int
    input_tokens: int | None
    output_tokens: int | None
    wall_time_sec: float


async def run_curation_jobs(
    vignette_rows: Sequence[VignetteRow],
    *,
    client: CurationClient,
    reviewer_model: str,
    out_path: str | Path,
    concurrency: int = 8,
    max_retries: int = 3,
    max_tokens: int = 10,
    limit: int | None = None,
    shard: tuple[int, int] | None = None,
    sleep=asyncio.sleep,
) -> RunTelemetry:
    """The async curation engine: fires one independent completion per
    (variant, curation question) job, respecting a concurrency semaphore,
    appending each completed job to ``out_path`` as it finishes
    (checkpoint/resume: job keys already present in ``out_path`` are
    skipped -- same pattern as elicitation's resume, WO-3 §1). A job whose
    call fails even after retries is left OFF the output file entirely, so
    a subsequent run will retry it rather than silently losing it.

    This function is a pure function of its arguments plus whatever is
    already on disk at ``out_path`` -- it carries no other state between
    invocations, so calling it twice (in the same process or two separate
    ones) against the same ``out_path`` is a faithful resume, not a
    warm-cache shortcut.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    scenario_by_vid = {r.variant_id: r.scenario for r in vignette_rows}
    variant_ids = [r.variant_id for r in vignette_rows]

    selected = build_job_keys(variant_ids, shard=shard, limit=limit)
    completed = {(r.variant_id, r.field) for r in _read_raw_results_tolerant(out_path)}
    remaining = [k for k in selected if k not in completed]
    n_skipped = len(selected) - len(remaining)

    sem = asyncio.Semaphore(concurrency)
    n_retries = 0
    n_errors = 0

    start = time.perf_counter()
    with open(out_path, "a", encoding="utf-8") as fh:

        async def _do_job(vid: str, field: str) -> None:
            nonlocal n_retries, n_errors
            async with sem:
                prompt = constants.CURATION_PROMPT_TEMPLATE.format(
                    scenario=scenario_by_vid[vid],
                    question=constants.CURATION_QUESTIONS[field],
                )
                try:
                    text, retries = await _complete_with_retry(
                        client, prompt, max_tokens, max_retries, sleep=sleep,
                    )
                except Exception as exc:
                    n_errors += 1
                    n_retries += getattr(exc, "retries_used", 0)
                    print(f"ERROR curating {vid}::{field}: {exc}", file=sys.stderr)
                    return
                n_retries += retries
                value, ok, raw = parse_rating(text)
                result = CurationRawResult(
                    variant_id=vid, field=field, value=value, ok=ok, raw=raw,
                    reviewer_model=reviewer_model, timestamp=time.time(),
                )
                # No `await` between here and the write below, so this is
                # safe under asyncio's single-threaded cooperative
                # scheduling without an explicit lock: once a task starts
                # writing, it runs to completion (no yield point).
                append_jsonl(result, fh)

        await asyncio.gather(*(_do_job(vid, field) for vid, field in remaining))
    wall_time = time.perf_counter() - start

    return RunTelemetry(
        n_jobs_total=len(selected),
        n_jobs_run=len(remaining) - n_errors,
        n_jobs_skipped=n_skipped,
        n_retries=n_retries,
        n_errors=n_errors,
        input_tokens=getattr(client, "input_tokens_used", None),
        output_tokens=getattr(client, "output_tokens_used", None),
        wall_time_sec=wall_time,
    )


# ---------------------------------------------------------------------------
# Assembling curated.csv from vignettes.csv + curated_raw.jsonl (WO-3 §3)
# ---------------------------------------------------------------------------


def assemble_curated(
    vignette_rows: Sequence[VignetteRow],
    raw_results: Sequence[CurationRawResult],
    *,
    reviewer_model: str,
    curation_date: str,
) -> list[CuratedRow]:
    """Joins ``vignette_rows`` with ``raw_results`` (keyed by
    ``(variant_id, field)``) into ``CuratedRow`` instances, ``accepted``
    left False (WO-3 §6 owns setting it). Unparseable (``ok=False``) or
    entirely-missing (job never completed, e.g. run was interrupted) ->
    the field is left empty (None), ``<field>_raw`` holds the verbatim
    response (or "" if the job never ran at all), and an
    ``individual_flags`` entry records why -- NEVER silently coerced to a
    number (the ported legacy invariant)."""
    by_key = {(r.variant_id, r.field): r for r in raw_results}
    out: list[CuratedRow] = []
    for row in vignette_rows:
        kwargs = row.model_dump()
        flags: list[str] = []
        for field in constants.CURATION_QUESTIONS:
            result = by_key.get((row.variant_id, field))
            if result is None:
                kwargs[field] = None
                kwargs[f"{field}_raw"] = ""
                flags.append(f"{field}: missing curation result (job not completed)")
                continue
            kwargs[field] = result.value if result.ok else None
            kwargs[f"{field}_raw"] = result.raw
            if not result.ok:
                flags.append(f"{field}: unparseable response ({result.raw!r})")
        kwargs["individual_flags"] = "; ".join(flags)
        kwargs["pair_flag"] = ""
        kwargs["reviewer_model"] = reviewer_model
        kwargs["curation_date"] = curation_date
        kwargs["accepted"] = False
        out.append(CuratedRow(**kwargs))
    return out


_CURATION_RATING_FIELDNAMES: tuple[str, ...] = tuple(
    f for field in constants.CURATION_QUESTIONS for f in (field, f"{field}_raw")
)


def merge_prior_acceptance(
    curated_rows: Sequence[CuratedRow], out_path: str | Path,
) -> tuple[int, list[str]]:
    """Re-running ``knobe curate run`` against the same ``--out`` path must
    NOT silently wipe human acceptance decisions already recorded there --
    the documented revision path (reject flagged -> revise the family ->
    re-ingest under a new ``rN`` family_id -> re-run curation) necessarily
    re-invokes ``curate run`` on the WHOLE vignette set, and without this
    step it would blow away every other, unrelated family's already-
    reviewed ``accepted`` state along with it.

    If a prior ``curated.csv`` already exists at ``out_path``, this mutates
    ``curated_rows`` IN PLACE (matching ``check_pairs`` et al.'s own
    mutate-in-place convention), keyed by ``variant_id``. Whether ``accepted``
    is carried forward is gated on the SAME "ratings unchanged?" test used
    for ``reviewer_model``/``curation_date`` below (``_CURATION_RATING_FIELDNAMES``:
    value + raw text, all 4 fields, byte-identical to the prior run's):

    - Previously accepted (``prior.accepted``) AND ratings unchanged (this
      item genuinely wasn't recurated this time -- the common case: its
      jobs were skipped via resume) -> ``accepted`` stays True.
    - Previously accepted BUT ratings changed (e.g. a job that failed last
      time -- leaving the field empty -- got a real value this time,
      possibly tripping a brand-new flag) -> ``accepted`` is RESET to
      False. A human accepted the item as it looked THEN; nobody has
      reviewed it in its current form, so silently keeping that old accept
      would let a never-seen flag slip into the accepted set unreviewed.
    - Not previously accepted -> stays False (assemble_curated's default),
      regardless of whether ratings changed.

    Independently of the above, ``reviewer_model``/``curation_date`` are
    carried forward for ANY row whose ratings are unchanged (accepted or
    not), so provenance still reflects when the item was actually curated,
    not today's incidental rerun; rows with changed ratings keep the fresh
    run's stamp (already set by ``assemble_curated``).

    Returns ``(n_preserved, reset_variant_ids)``: the count of rows whose
    ``accepted=True`` survived unchanged, and the variant_ids that were
    previously accepted but got reset to False because their ratings
    changed (caller prints/logs both). Missing/unreadable ``out_path`` is
    tolerated (nothing to merge -- e.g. the first-ever run) and returns
    ``(0, [])``.
    """
    out_path = Path(out_path)
    if not out_path.exists() or out_path.stat().st_size == 0:
        return 0, []

    try:
        prior_rows = read_csv_validated(out_path, CuratedRow)
    except Exception:
        # Not a readable/valid prior curated.csv (e.g. --out points at a
        # fresh path with leftover unrelated content) -- nothing to merge,
        # and this must not turn an otherwise-successful curation run into
        # a hard failure.
        return 0, []

    prior_by_variant = {r.variant_id: r for r in prior_rows}
    n_preserved = 0
    reset_variant_ids: list[str] = []
    for row in curated_rows:
        prior = prior_by_variant.get(row.variant_id)
        if prior is None:
            continue
        ratings_unchanged = all(
            getattr(row, f) == getattr(prior, f) for f in _CURATION_RATING_FIELDNAMES
        )
        if prior.accepted:
            if ratings_unchanged:
                row.accepted = True
                n_preserved += 1
            else:
                row.accepted = False  # explicit -- assemble_curated already defaults to False
                reset_variant_ids.append(row.variant_id)
        if ratings_unchanged:
            row.reviewer_model = prior.reviewer_model
            row.curation_date = prior.curation_date
    return n_preserved, reset_variant_ids


# ---------------------------------------------------------------------------
# Pair / typicality / category manipulation checks (WO-3 §3/§4)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CurationConfig:
    severity_match_max_diff: int = 2
    vividness_min_gap: int = 2
    moral_min: int = 6
    nonmoral_max: int = 4


def load_curation_config(path: str | Path) -> CurationConfig:
    path = Path(path)
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return CurationConfig(**data)


def _iter_matched_pairs(rows: Sequence[CuratedRow]):
    """Yields ``(low, high)`` evocativeness-matched row pairs sharing a
    ``(family_id, typicality)`` key -- shared by ``check_pairs`` and
    ``report_distributions`` so the two never compute pairing differently."""
    by_key: dict[tuple[str, str], dict[str, CuratedRow]] = {}
    for r in rows:
        by_key.setdefault((r.family_id, r.typicality), {})[r.evocativeness] = r
    for pair in by_key.values():
        low, high = pair.get("low"), pair.get("high")
        if low is not None and high is not None:
            yield low, high


def check_pairs(rows: Sequence[CuratedRow], config: CurationConfig) -> None:
    """Port of the legacy ``check_pairs``: for every (family_id,
    typicality) pair, compares the low- and high-evocativeness rows'
    severity (should be matched within ``severity_match_max_diff``) and
    vividness (should differ by at least ``vividness_min_gap``). Sets
    ``pair_flag`` on both rows IN PLACE (mutates ``rows``; ``CuratedRow``
    is an ordinary, non-frozen pydantic model). Threshold caveat carried
    over from the legacy script's own docstring: these are starting
    heuristics -- inspect ``report_distributions``'s empirical output
    before treating them as hard cutoffs.

    Rows with an unparseable severity/vividness rating on either side of
    the pair are skipped (already flagged individually by
    ``assemble_curated``)."""
    for low, high in _iter_matched_pairs(rows):
        if None in (low.severity, high.severity, low.vividness, high.vividness):
            continue
        pair_flags = []
        if abs(high.severity - low.severity) > config.severity_match_max_diff:
            pair_flags.append(
                f"severity mismatch: low={low.severity} high={high.severity} "
                f"(should be matched, max diff {config.severity_match_max_diff})"
            )
        if (high.vividness - low.vividness) < config.vividness_min_gap:
            pair_flags.append(
                f"vividness gap too small: low={low.vividness} high={high.vividness} "
                f"(should differ by >= {config.vividness_min_gap})"
            )
        flag_text = "; ".join(pair_flags)
        low.pair_flag = flag_text
        high.pair_flag = flag_text


def check_typicality_manipulation(rows: Sequence[CuratedRow]) -> None:
    """DR §5.1: every item's asserted typicality is checked against an
    independent perceived-typicality rating at curation -- within a
    family, the mean ``typicality_perception`` of the common-variant rows
    must exceed that of the uncommon-variant rows. Violating families get
    a family-level flag appended (mutated in place) to every one of their
    rows' ``pair_flag``, prefixed ``"typicality_manipulation:"`` so it's
    distinguishable from the pair-level severity/vividness flag that may
    already be there (both live in ``pair_flag`` since both are
    above-the-single-row checks; ``individual_flags`` is reserved for
    single-row-only checks -- see ``check_category_manipulation``).

    Families where either side has no parseable typicality_perception
    ratings at all are skipped (can't compute a mean); this is distinct
    from a family that simply fails the check."""
    by_family: dict[str, list[CuratedRow]] = {}
    for r in rows:
        by_family.setdefault(r.family_id, []).append(r)

    for family_id, family_rows in by_family.items():
        common_vals = [
            r.typicality_perception for r in family_rows
            if r.typicality == "common" and r.typicality_perception is not None
        ]
        uncommon_vals = [
            r.typicality_perception for r in family_rows
            if r.typicality == "uncommon" and r.typicality_perception is not None
        ]
        if not common_vals or not uncommon_vals:
            continue
        mean_common = statistics.mean(common_vals)
        mean_uncommon = statistics.mean(uncommon_vals)
        if not (mean_common > mean_uncommon):
            flag = (
                f"typicality_manipulation: mean common ({mean_common:.1f}) does not "
                f"exceed mean uncommon ({mean_uncommon:.1f}) for family {family_id}"
            )
            for r in family_rows:
                r.pair_flag = f"{r.pair_flag}; {flag}" if r.pair_flag else flag


_NONMORAL_VALENCES_FOR_CATEGORY_CHECK = ("NMB", "NMG", "NEU")


def check_category_manipulation(rows: Sequence[CuratedRow], config: CurationConfig) -> None:
    """DR §13: ``moral_relevance`` must separate MB/MG from NMB/NMG/NEU.
    Flags MB/MG items scoring below ``config.moral_min``, and
    NMB/NMG/NEU items scoring above ``config.nonmoral_max``, appended
    (mutated in place) to ``individual_flags`` with a
    ``"category_manipulation:"`` prefix -- a single-row check (unlike the
    pair/family checks above), so it lives in ``individual_flags`` rather
    than ``pair_flag``."""
    for r in rows:
        if r.moral_relevance is None:
            continue
        flag = None
        if r.valence in ("MB", "MG") and r.moral_relevance < config.moral_min:
            flag = (
                f"category_manipulation: moral_relevance={r.moral_relevance} < "
                f"moral_min={config.moral_min} for {r.valence} item"
            )
        elif r.valence in _NONMORAL_VALENCES_FOR_CATEGORY_CHECK and r.moral_relevance > config.nonmoral_max:
            flag = (
                f"category_manipulation: moral_relevance={r.moral_relevance} > "
                f"nonmoral_max={config.nonmoral_max} for {r.valence} item"
            )
        if flag:
            r.individual_flags = f"{r.individual_flags}; {flag}" if r.individual_flags else flag


# ---------------------------------------------------------------------------
# Empirical distribution report + plots (WO-3 §4/§5)
# ---------------------------------------------------------------------------


def _int_hist_bins(data: Sequence[int]) -> range:
    return range(min(data), max(data) + 2)


def _plot_distributions(
    sev_deltas: Sequence[int],
    viv_gaps: Sequence[int],
    moral_relevance_by_group: dict[str, list[int]],
    report_dir: Path,
) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover -- exercised only without the 'stats' extra
        raise RuntimeError(
            "matplotlib is required for curation distribution plots -- install the "
            "'stats' extra (`uv pip install -e '.[stats]'`)."
        ) from exc

    if sev_deltas:
        fig, ax = plt.subplots()
        ax.hist(sev_deltas, bins=_int_hist_bins(sev_deltas))
        ax.set_xlabel("severity |delta| (matched low/high pairs)")
        ax.set_ylabel("count")
        ax.set_title("Severity match distribution")
        fig.savefig(report_dir / "severity_delta_hist.png")
        plt.close(fig)

    if viv_gaps:
        fig, ax = plt.subplots()
        ax.hist(viv_gaps, bins=_int_hist_bins(viv_gaps))
        ax.set_xlabel("vividness gap (high - low, matched pairs)")
        ax.set_ylabel("count")
        ax.set_title("Vividness gap distribution")
        fig.savefig(report_dir / "vividness_gap_hist.png")
        plt.close(fig)

    groups_with_data = {k: v for k, v in moral_relevance_by_group.items() if v}
    if groups_with_data:
        fig, ax = plt.subplots()
        ax.boxplot(list(groups_with_data.values()), tick_labels=list(groups_with_data.keys()))
        ax.set_ylabel("moral_relevance")
        ax.set_title("moral_relevance by valence group")
        fig.savefig(report_dir / "moral_relevance_by_group.png")
        plt.close(fig)


def report_distributions(rows: Sequence[CuratedRow], config: CurationConfig, report_dir: str | Path) -> str:
    """Text summary + matplotlib histogram/boxplot PNGs of the pair-check
    and category-check distributions, saved to ``report_dir`` (WO-3 §4/§5)
    -- so the config thresholds can be revisited against real empirical
    data rather than the initial heuristic guesses. Returns the text
    summary (also written to ``curation_distribution_report.txt``)."""
    report_dir = Path(report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)

    sev_deltas: list[int] = []
    viv_gaps: list[int] = []
    for low, high in _iter_matched_pairs(rows):
        if None in (low.severity, high.severity, low.vividness, high.vividness):
            continue
        sev_deltas.append(abs(high.severity - low.severity))
        viv_gaps.append(high.vividness - low.vividness)

    lines = ["=== Curation pair-check distributions ===", ""]
    lines.append(f"Matched pairs with parseable severity+vividness ratings: {len(sev_deltas)}")
    if sev_deltas:
        lines.append(
            f"severity |delta|: mean={statistics.mean(sev_deltas):.2f} "
            f"median={statistics.median(sev_deltas):.1f} max={max(sev_deltas)} "
            f"(threshold: <= {config.severity_match_max_diff})"
        )
        lines.append(
            f"vividness gap: mean={statistics.mean(viv_gaps):.2f} "
            f"median={statistics.median(viv_gaps):.1f} min={min(viv_gaps)} "
            f"(threshold: >= {config.vividness_min_gap})"
        )
    else:
        lines.append("No matched pairs with parseable severity/vividness ratings.")

    moral_relevance_by_group: dict[str, list[int]] = {"MB/MG": [], "NMB/NMG/NEU": []}
    for r in rows:
        if r.moral_relevance is None:
            continue
        if r.valence in ("MB", "MG"):
            moral_relevance_by_group["MB/MG"].append(r.moral_relevance)
        else:
            moral_relevance_by_group["NMB/NMG/NEU"].append(r.moral_relevance)

    lines.append("")
    lines.append(
        f"moral_relevance by group (category check: MB/MG >= {config.moral_min}, "
        f"NMB/NMG/NEU <= {config.nonmoral_max}):"
    )
    for group, vals in moral_relevance_by_group.items():
        if vals:
            lines.append(f"  {group}: n={len(vals)} mean={statistics.mean(vals):.2f}")
        else:
            lines.append(f"  {group}: n=0")

    summary_text = "\n".join(lines)
    (report_dir / "curation_distribution_report.txt").write_text(summary_text, encoding="utf-8")
    _plot_distributions(sev_deltas, viv_gaps, moral_relevance_by_group, report_dir)
    return summary_text


# ---------------------------------------------------------------------------
# Acceptance workflow -- `knobe curate review` (WO-3 §6)
# ---------------------------------------------------------------------------


def _is_flagged(row: CuratedRow) -> bool:
    return bool(row.individual_flags) or bool(row.pair_flag)


def _atomic_write_csv(rows, path: Path, model) -> None:
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    write_csv_validated(rows, tmp, model)
    os.replace(tmp, path)


def review_curated(
    curated_path: str | Path,
    *,
    accept_unflagged: bool = False,
    input_fn=input,
    print_fn=print,
) -> int:
    """The human acceptance workflow (WO-3 §6).

    Default (interactive) mode: groups rows by family, and for every family
    that has at least one flagged row, prints full context (scenario,
    ratings, flags) for every row in that family, then prompts once per
    family: accept all / reject flagged / skip.
      - "accept all": every row in the family (flagged or not) -> accepted=True.
      - "reject flagged": only the family's UNFLAGGED rows -> accepted=True;
        flagged rows stay accepted=False, and the WO-1 revision instruction
        is printed (a rejected family is never edited in place -- it must
        re-enter authoring under a new "rN" family_id suffix and be
        re-ingested via `knobe generate ingest`).
      - "skip": no change to any row in the family.
    Families with zero flagged rows are not shown in interactive mode (there
    is nothing to review) and are left as-is; use --accept-unflagged (below)
    to accept them.

    ``--accept-unflagged`` batch mode (for scripted G0 runs): skips all
    prompting and sets accepted=True for every currently-unflagged row in
    the whole file, non-interactively.

    Either mode rewrites ``curated_path`` atomically (temp file + os.replace).
    """
    rows: list[CuratedRow] = read_csv_validated(curated_path, CuratedRow)  # type: ignore[assignment]

    if accept_unflagged:
        n_newly = 0
        for r in rows:
            if not _is_flagged(r) and not r.accepted:
                r.accepted = True
                n_newly += 1
        _atomic_write_csv(rows, Path(curated_path), CuratedRow)
        n_accepted = sum(1 for r in rows if r.accepted)
        print_fn(
            f"--accept-unflagged: accepted {n_newly} previously-unaccepted unflagged row(s) "
            f"({n_accepted}/{len(rows)} accepted total) in {curated_path}."
        )
        return 0

    by_family: dict[str, list[CuratedRow]] = {}
    for r in rows:
        by_family.setdefault(r.family_id, []).append(r)

    for family_id in sorted(by_family):
        family_rows = by_family[family_id]
        flagged = [r for r in family_rows if _is_flagged(r)]
        if not flagged:
            continue

        print_fn(f"\n=== family {family_id} ({len(flagged)}/{len(family_rows)} row(s) flagged) ===")
        for r in sorted(family_rows, key=lambda r: r.variant_id):
            marker = "  FLAGGED" if _is_flagged(r) else ""
            print_fn(f"  {r.variant_id} [{r.typicality}/{r.evocativeness}]{marker}")
            print_fn(f"    scenario: {r.scenario}")
            print_fn(
                f"    moral_relevance={r.moral_relevance} severity={r.severity} "
                f"vividness={r.vividness} typicality_perception={r.typicality_perception}"
            )
            if r.individual_flags:
                print_fn(f"    individual_flags: {r.individual_flags}")
            if r.pair_flag:
                print_fn(f"    pair_flag: {r.pair_flag}")

        choice = input_fn(f"[{family_id}] accept all / reject flagged / skip? [a/r/s]: ").strip().lower()
        if choice.startswith("a"):
            for r in family_rows:
                r.accepted = True
        elif choice.startswith("r"):
            for r in family_rows:
                if not _is_flagged(r):
                    r.accepted = True
            print_fn(
                f"  Rejected the flagged rows in family {family_id}. Revision path: fix the "
                f"family in the authoring matrix under a NEW version id (e.g. {family_id}r1) "
                f"and re-enter it via `knobe generate ingest` (WO-1) -- curated.csv rows are "
                f"never edited in place."
            )
        else:
            print_fn(f"  Skipped family {family_id} (no accept/reject decision recorded).")

    _atomic_write_csv(rows, Path(curated_path), CuratedRow)
    n_accepted = sum(1 for r in rows if r.accepted)
    print_fn(f"\nDone. {n_accepted}/{len(rows)} row(s) accepted in {curated_path}.")
    return 0


# ---------------------------------------------------------------------------
# CLI-facing orchestration (called by knobe.cli's "curate run"/"curate review")
# ---------------------------------------------------------------------------


def run(
    vignettes_path: str | Path,
    *,
    reviewer_model: str,
    mock: bool = False,
    out: str | Path = "curated.csv",
    raw_out: str | Path = "curated_raw.jsonl",
    concurrency: int = 8,
    max_retries: int = 3,
    max_tokens: int = 10,
    limit: int | None = None,
    shard: tuple[int, int] | None = None,
    report_dir: str | Path = "curation_reports",
    runlog_path: str | Path | None = None,
    registry_path: str | Path | None = None,
    curation_config_path: str | Path | None = None,
    curation_date: str | None = None,
) -> int:
    """``knobe curate run``'s full orchestration: reviewer-vs-subject
    check, the async elicitation engine, curated.csv assembly, all three
    manipulation checks, merging forward any prior acceptance decisions
    from an existing ``--out`` file (``merge_prior_acceptance``), and the
    distribution report -- in that order. Returns a process exit code (0
    success, 1 a checked/expected failure)."""
    import datetime

    registry_path = registry_path or default_registry_path()
    try:
        registry = load_registry(registry_path)
    except RegistryConfigError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    try:
        check_reviewer_not_subject(reviewer_model, registry)
    except ReviewerSubjectConflictError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    vignette_rows: list[VignetteRow] = read_csv_validated(vignettes_path, VignetteRow)  # type: ignore[assignment]
    print(f"Loaded {len(vignette_rows)} vignette variant(s) from {vignettes_path}")

    client: CurationClient = MockClient() if mock else AnthropicClient(model=reviewer_model)

    telemetry = asyncio.run(
        run_curation_jobs(
            vignette_rows,
            client=client,
            reviewer_model=reviewer_model,
            out_path=raw_out,
            concurrency=concurrency,
            max_retries=max_retries,
            max_tokens=max_tokens,
            limit=limit,
            shard=shard,
        )
    )
    print(
        f"Curation calls: run={telemetry.n_jobs_run} skipped(resumed)={telemetry.n_jobs_skipped} "
        f"retries={telemetry.n_retries} errors={telemetry.n_errors} "
        f"wall_time={telemetry.wall_time_sec:.1f}s"
        + (
            f" input_tokens={telemetry.input_tokens} output_tokens={telemetry.output_tokens}"
            if telemetry.input_tokens is not None
            else ""
        )
    )

    runlog_path = Path(runlog_path) if runlog_path else Path(raw_out).parent / "curation_runlog.jsonl"
    runlog_path.parent.mkdir(parents=True, exist_ok=True)
    runlog_entry = CurationRunLogEntry(
        timestamp=time.time(),
        reviewer_model=reviewer_model,
        mock=mock,
        n_jobs_total=telemetry.n_jobs_total,
        n_jobs_run=telemetry.n_jobs_run,
        n_jobs_skipped=telemetry.n_jobs_skipped,
        n_retries=telemetry.n_retries,
        n_errors=telemetry.n_errors,
        input_tokens=telemetry.input_tokens,
        output_tokens=telemetry.output_tokens,
        wall_time_sec=telemetry.wall_time_sec,
    )
    with open(runlog_path, "a", encoding="utf-8") as fh:
        append_jsonl(runlog_entry, fh)

    raw_results = _read_raw_results_tolerant(raw_out)
    curated_rows = assemble_curated(
        vignette_rows, raw_results,
        reviewer_model=reviewer_model,
        curation_date=curation_date or datetime.date.today().isoformat(),
    )

    curation_config_path = curation_config_path or default_curation_config_path()
    config = load_curation_config(curation_config_path)
    check_pairs(curated_rows, config)
    check_typicality_manipulation(curated_rows)
    check_category_manipulation(curated_rows, config)

    # Merge forward any accepted/reviewer_model/curation_date state already
    # recorded in an existing --out file, so re-running `curate run` (e.g.
    # the reject -> revise -> re-ingest -> re-run revision workflow) never
    # silently reverts prior human acceptance decisions on unrelated rows.
    # A previously-accepted row whose ratings changed this run is reset to
    # unaccepted rather than carried forward -- nobody has reviewed it in
    # its current form (see merge_prior_acceptance's docstring).
    n_preserved, reset_variant_ids = merge_prior_acceptance(curated_rows, out)
    print(f"Preserved {n_preserved} prior acceptance decision(s) from existing {out}.")
    if reset_variant_ids:
        print(
            f"{len(reset_variant_ids)} previously-accepted row(s) had ratings change -- "
            f"reset to unaccepted, needs re-review: {reset_variant_ids}"
        )

    write_csv_validated(curated_rows, out, CuratedRow)

    n_individual_flagged = sum(1 for r in curated_rows if r.individual_flags)
    n_pair_flagged = sum(1 for r in curated_rows if r.pair_flag)
    print(f"\nCurated {len(curated_rows)} item(s).")
    print(f"{n_individual_flagged} item(s) flagged individually (unparseable / category manipulation).")
    print(f"{n_pair_flagged} item(s) flagged at the pair/family level (severity/vividness/typicality).")
    print(f"Written to {out}")

    report_distributions(curated_rows, config, report_dir)
    print(f"Distribution report + plots written to {report_dir}")
    return 0
