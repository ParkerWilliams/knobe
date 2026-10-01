"""Elicitation (DESIGN.md section 6): every model, both experiments, one script.

Reuses knobe's engine (vLLM on the cluster, FakeEngine for tests), model
registry, seed derivation (sha256 of RELEASE, prompt_id, model_key,
sample_idx) and ResultRecord. The readout is the written number only
(parse_rating); logprobs are not requested, which also skips vLLM's 11
forced-scoring passes per prompt.
"""
from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from knobe.elicit_vllm import (
    EngineRequest,
    EngineResponse,
    build_engine,
    default_registry_path,
    resolve_model_id,
)
from knobe.jobs import derive_temperature_and_seed
from knobe.parsing import parse_rating
from knobe.registry import load_registry, model_key_for
from knobe.schemas import ResultRecord, append_jsonl, read_jsonl

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


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="knobe_moral_probe elicitation")
    p.add_argument("--items", required=True, type=Path, help="selected items CSV (from kmp.screen)")
    p.add_argument("--out", required=True, type=Path, help="results JSONL (appended; resumable)")
    p.add_argument("--engine", default="fake", choices=["fake", "vllm", "hf"])
    p.add_argument("--model-keys", help=f"comma-separated subset of {', '.join(MODEL_KEYS)}")
    p.add_argument("--registry", type=Path, help="models.yaml (default: the repo's configs/models.yaml)")
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--max-tokens", type=int, default=protocol.MAX_TOKENS)
    args = p.parse_args(argv)

    model_keys = [k.strip() for k in args.model_keys.split(",")] if args.model_keys else list(MODEL_KEYS)
    unknown = sorted(set(model_keys) - set(MODEL_KEYS))
    if unknown:
        p.error(f"unknown model key(s) {unknown}")

    items = load_items(args.items)
    problems = design_problems(items) + [f"{i.item_id} is {i.review_status}, not approved"
                                         for i in items if i.review_status != "approved"]
    if problems:
        print("refusing to run:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 2

    jobs = build_jobs(prompts.build_subject_prompts(items), model_keys)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    done = ({r.job_id for r in read_jsonl(args.out, ResultRecord)}
            if args.out.exists() and args.out.stat().st_size else set())

    remaining = [j for j in jobs if j.job_id not in done]
    print(f"{len(done)} done, {len(remaining)} remaining of {len(jobs)} jobs")
    if not remaining:
        return 0

    registry = load_registry(args.registry or default_registry_path())
    engine = build_engine(args.engine)
    by_model: dict[str, list[Job]] = {}
    for job in remaining:
        by_model.setdefault(job.model_key, []).append(job)

    with open(args.out, "a", encoding="utf-8") as fh:
        for model_key, model_jobs in by_model.items():
            model_id, _family, pinned = resolve_model_id(model_key, registry)
            revision = engine.load(model_id, revision=pinned)
            print(f"[elicit] {model_key} ({model_id}@{revision}): {len(model_jobs)} jobs")
            for start in range(0, len(model_jobs), args.batch_size):
                batch = model_jobs[start:start + args.batch_size]
                requests = [to_request(j, args.max_tokens) for j in batch]
                responses = {r.job_id: r for r in engine.generate(requests)}
                for job, request in zip(batch, requests):
                    response = responses.get(job.job_id)
                    if response is None:
                        print(f"ERROR: no response for {job.job_id}", file=sys.stderr)
                        continue
                    append_jsonl(to_result(job, request, response, revision), fh)
                fh.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
