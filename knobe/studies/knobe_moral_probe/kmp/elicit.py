"""Elicitation (DESIGN.md section 6): every model, every experiment, one script.

Reuses knobe's engine (vLLM on the cluster, FakeEngine for tests), model
registry, seed derivation (sha256 of RELEASE, prompt_id, model_key,
sample_idx) and ResultRecord. The readout is the written number only
(parse_rating); logprobs are not requested, which also skips vLLM's 11
forced-scoring passes per prompt.

main() appends to --out and resumes by job_id. A sidecar run manifest
(<out>.manifest.json: release, runner_version, max_tokens, engine,
model_keys, examples, prompt_id -> text_sha256) is written before generating; a
resume whose run fields or already-run prompt texts differ is refused
(exit 2), as is a resume with rows but no manifest. A manifest written
before the examples field existed counts as examples=true (every earlier
run had the worked examples). Jobs the engine
returns no response for make the run exit 1; re-running resumes them.

--no-examples (DESIGN.md section 8, example check) renders the prompts
without the worked examples. Job IDs match a normal run, so it needs its
own --out; the manifest's examples field refuses a resume across the two.

Throughput (DESIGN.md section 8, gate 5): just before a model's first batch
in each invocation, one line {"model_key", "start"} (time.time()) is
appended to <out>.starts.jsonl. Append-only and written under the lock, so
resumes add lines; read_model_starts keeps each model's earliest start.

Concurrency: the whole run holds an exclusive non-blocking fcntl.flock on
<out>.lock; a second run on the same --out exits 2. Use one --out per
model set. flock on NFS/Lustre depends on mount options (e.g. Lustre
needs -o flock; some NFS setups only lock locally), so on a cluster
filesystem check that locks are actually shared across nodes.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from knobe.elicit_vllm import (
    EngineRequest,
    EngineResponse,
    build_engine,
    default_registry_path,
    read_results_tolerating_torn_tail,
    resolve_model_id,
)
from knobe.jobs import derive_temperature_and_seed
from knobe.parsing import parse_rating
from knobe.registry import load_registry, model_key_for
from knobe.schemas import ResultRecord, append_jsonl

from kmp import prompts, protocol
from kmp.items import design_problems, load_items
from kmp.prompts import PromptSpec

FAMILIES = ("llama-3.1-8b", "mistral-7b-v0.1", "gemma-2-9b")
MODEL_KEYS = tuple(model_key_for(f, t) for f in FAMILIES for t in ("pretrained", "finetuned"))


@dataclass(frozen=True)
class Job:
    prompt_id: str
    model_key: str
    sample_idx: int
    text: str
    fmt: Literal["raw", "chat"]
    # sha256 of the exact prompt text, carried from PromptSpec so a resume
    # (Task 6) can detect that a done job was produced from different text.
    text_sha256: str

    @property
    def job_id(self) -> str:
        return f"{self.prompt_id}::{self.model_key}::{self.sample_idx}"


def build_jobs(specs: list[PromptSpec], model_keys: list[str]) -> list[Job]:
    jobs = []
    for spec in specs:
        for model_key in model_keys:
            fmt = prompts.format_for_model(model_key)
            pid = prompts.prompt_id(spec.stem, fmt)
            jobs += [Job(pid, model_key, s, spec.text, fmt, spec.text_sha256) for s in range(spec.n_samples)]
    return jobs


def to_request(job: Job, max_tokens: int) -> EngineRequest:
    temperature, seed = derive_temperature_and_seed(protocol.RELEASE, job.prompt_id, job.model_key, job.sample_idx)
    if job.fmt == "raw":
        wrapper = {"text": job.text}
    elif job.fmt == "chat":
        wrapper = {"messages": [{"role": "user", "content": job.text}]}
    else:
        raise ValueError(f"unknown fmt {job.fmt!r} for job {job.job_id}")
    return EngineRequest(job_id=job.job_id, prompt_id=job.prompt_id, temperature=temperature, seed=seed,
                         max_tokens=max_tokens, want_first_token_logprobs=False, **wrapper)


def to_result(job: Job, request: EngineRequest, response: EngineResponse, model_revision: str) -> ResultRecord:
    if response.job_id != job.job_id:
        raise ValueError(f"response job_id {response.job_id!r} does not match job_id {job.job_id!r}")
    value, ok, raw = parse_rating(response.raw_response)
    return ResultRecord(
        job_id=job.job_id, prompt_id=job.prompt_id, model_key=job.model_key, sample_idx=job.sample_idx,
        temperature=request.temperature, seed=request.seed, raw_response=raw,
        parsed_rating=value, parse_ok=ok, parse_method="regex", logprobs_0_10=None,
        model_revision=model_revision, runner_version=protocol.RUNNER_VERSION, timestamp=time.time(),
    )


# ---------------------------------------------------------------------------
# Run manifest. ResultRecord (extra="forbid") has no slot for provenance and
# resume matches on job_id only, so a sidecar records what the rows in --out
# were produced under; a resume that would mix versions is refused.
# ---------------------------------------------------------------------------

RUN_FIELDS = ("release", "runner_version", "max_tokens", "engine", "model_keys", "examples")
# Values for run fields a manifest predates: every run before --no-examples had the examples.
RUN_FIELD_DEFAULTS = {"examples": True}


def run_field(manifest: dict, key: str):
    """A manifest's run field, falling back to RUN_FIELD_DEFAULTS for older manifests."""
    return manifest.get(key, RUN_FIELD_DEFAULTS.get(key))


def manifest_path(out: Path) -> Path:
    """``<out>.manifest.json``, e.g. ``results.jsonl.manifest.json``."""
    out = Path(out)
    return out.with_name(out.name + ".manifest.json")


def build_manifest(jobs: list[Job], engine: str, model_keys: list[str], max_tokens: int,
                   examples: bool = True) -> dict:
    return {
        "release": protocol.RELEASE,
        "runner_version": protocol.RUNNER_VERSION,
        "max_tokens": max_tokens,
        "engine": engine,
        "model_keys": sorted(model_keys),
        "examples": examples,
        "prompts": {j.prompt_id: j.text_sha256 for j in jobs},
    }


def manifest_problems(old: dict, new: dict, done_prompt_ids: set[str], limit: int = 5) -> list[str]:
    """Why ``new`` can't resume rows produced under ``old``. Empty = safe."""
    problems = [f"{k}: manifest has {run_field(old, k)!r}, this run has {new[k]!r}"
                for k in RUN_FIELDS if run_field(old, k) != new[k]]
    old_prompts = old.get("prompts", {})
    bad = sorted(pid for pid in done_prompt_ids
                 if pid in new["prompts"] and old_prompts.get(pid) != new["prompts"][pid])
    if bad:
        shown = ", ".join(bad[:limit]) + (f" (+{len(bad) - limit} more)" if len(bad) > limit else "")
        problems.append(f"text_sha256 changed for {len(bad)} prompt_id(s) that already have rows: {shown}")
    return problems


def starts_path(out: Path) -> Path:
    """``<out>.starts.jsonl``: per-model start times, one line per model per invocation."""
    out = Path(out)
    return out.with_name(out.name + ".starts.jsonl")


def record_model_start(out: Path, model_key: str) -> None:
    with open(starts_path(out), "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"model_key": model_key, "start": time.time()}) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def read_model_starts(out: Path) -> dict[str, float]:
    """Each model's earliest recorded start; {} if the sidecar is absent.
    Unreadable lines (a torn last write) are skipped."""
    path = starts_path(out)
    if not path.exists():
        return {}
    starts: dict[str, float] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(line)
            model_key, start = entry["model_key"], float(entry["start"])
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            continue
        starts[model_key] = min(start, starts.get(model_key, start))
    return starts


def lock_path(out: Path) -> Path:
    """``<out>.lock``, held (flock) for the whole run."""
    out = Path(out)
    return out.with_name(out.name + ".lock")


def write_manifest(manifest: dict, path: Path) -> None:
    """Atomic: unique tmp file in the same dir, fsync, then os.replace."""
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def _reconcile_manifest(out: Path, manifest: dict, done_rows: list[ResultRecord]) -> list[str]:
    """Checks ``manifest`` (this run) against the sidecar of the rows already
    in ``out``, merges in the old prompt entries, and writes it. Returns the
    reasons to refuse (nothing is written then); empty = written."""
    mpath = manifest_path(out)
    if done_rows:
        if not mpath.exists():
            return [f"{out} has {len(done_rows)} rows but no run manifest at {mpath}"]
        try:
            old = json.loads(mpath.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            return [f"run manifest {mpath} could not be read as JSON: {exc}"]
        if not isinstance(old, dict) or not isinstance(old.get("prompts", {}), dict):
            return [f"run manifest {mpath} is not a JSON object with a prompts mapping"]
        problems = manifest_problems(old, manifest, {r.prompt_id for r in done_rows})
        if problems:
            return [f"rows would mix versions (see {mpath}):", *problems]
        manifest = {**manifest, "prompts": {**old.get("prompts", {}), **manifest["prompts"]}}
    write_manifest(manifest, mpath)
    return []


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="knobe_moral_probe elicitation")
    p.add_argument("--items", required=True, type=Path, help="selected items CSV (from kmp.screen)")
    p.add_argument("--out", required=True, type=Path,
                   help="results JSONL (appended; resumable); one --out per model set; "
                        "concurrent runs on the same --out are refused")
    # Required, no default: a cluster command that forgot --engine used to get
    # the fake engine and write random answers into a real --out.
    p.add_argument("--engine", required=True, choices=["fake", "vllm", "hf"],
                   help="vllm on the cluster; fake only for tests and dry runs")
    p.add_argument("--model-keys", help=f"comma-separated subset of {', '.join(MODEL_KEYS)}")
    p.add_argument("--registry", type=Path, help="models.yaml (default: the repo's configs/models.yaml)")
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--max-tokens", type=int, default=protocol.MAX_TOKENS)
    p.add_argument("--no-examples", action="store_true",
                   help="omit the worked examples (DESIGN.md section 8 example check). "
                        "Job IDs match a normal run, so use a separate --out file.")
    args = p.parse_args(argv)

    model_keys = (sorted(dict.fromkeys(k.strip() for k in args.model_keys.split(",")))
                  if args.model_keys else list(MODEL_KEYS))
    unknown = sorted(set(model_keys) - set(MODEL_KEYS))
    if unknown:
        p.error(f"unknown model key(s) {unknown}")

    items = load_items(args.items)
    problems = design_problems(items, stage="selected") + [f"{i.item_id} is {i.review_status}, not approved"
                                         for i in items if i.review_status != "approved"]
    if problems:
        print("refusing to run:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 2

    examples = () if args.no_examples else protocol.EXAMPLES
    jobs = build_jobs(prompts.build_subject_prompts(items, examples), model_keys)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    lpath = lock_path(args.out)
    with open(lpath, "a") as lock_fh:
        try:
            fcntl.flock(lock_fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(f"refusing to run: another run holds {lpath}; use one --out per model set", file=sys.stderr)
            return 2
        return _run_locked(args, jobs, model_keys)   # lock released when lock_fh closes


def _run_locked(args: argparse.Namespace, jobs: list[Job], model_keys: list[str]) -> int:
    # Missing/empty file -> []; a torn trailing line (crash mid-write) is
    # dropped and the file repaired in place, so that job is simply re-run.
    done_rows = read_results_tolerating_torn_tail(args.out)
    manifest = build_manifest(jobs, args.engine, model_keys, args.max_tokens, examples=not args.no_examples)
    problems = _reconcile_manifest(args.out, manifest, done_rows)
    if problems:
        print(f"refusing to resume {args.out}:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 2

    # Local set difference: knobe.jobs.diff_jobs takes JobRecord, not kmp's Job (CLAUDE.md section 7).
    done_ids = {r.job_id for r in done_rows}
    remaining = [j for j in jobs if j.job_id not in done_ids]
    print(f"{len(jobs) - len(remaining)} done, {len(remaining)} remaining of {len(jobs)} jobs")
    if not remaining:
        return 0

    registry = load_registry(args.registry or default_registry_path())
    engine = build_engine(args.engine)
    by_model: dict[str, list[Job]] = {}
    for job in remaining:
        by_model.setdefault(job.model_key, []).append(job)

    n_missing = 0
    with open(args.out, "a", encoding="utf-8") as fh:
        for model_key, model_jobs in by_model.items():
            model_id, _family, pinned = resolve_model_id(model_key, registry)
            revision = engine.load(model_id, revision=pinned)
            print(f"[elicit] {model_key} ({model_id}@{revision}): {len(model_jobs)} jobs")
            record_model_start(args.out, model_key)
            for start in range(0, len(model_jobs), args.batch_size):
                batch = model_jobs[start:start + args.batch_size]
                requests = [to_request(j, args.max_tokens) for j in batch]
                responses = {r.job_id: r for r in engine.generate(requests)}
                for job, request in zip(batch, requests):
                    response = responses.get(job.job_id)
                    if response is None:
                        print(f"ERROR: no response for {job.job_id}", file=sys.stderr)
                        n_missing += 1
                        continue
                    append_jsonl(to_result(job, request, response, revision), fh)  # flushes per row
    if n_missing:
        print(f"ERROR: {n_missing} job(s) got no response; re-run the same command to resume them",
              file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
