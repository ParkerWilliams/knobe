"""Elicitation (DESIGN.md section 6): every model, both experiments, one script.

Reuses knobe's engine (vLLM on the cluster, FakeEngine for tests), model
registry, seed derivation (sha256 of RELEASE, prompt_id, model_key,
sample_idx) and ResultRecord. The readout is the written number only
(parse_rating); logprobs are not requested, which also skips vLLM's 11
forced-scoring passes per prompt.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from knobe.elicit_vllm import EngineRequest, EngineResponse
from knobe.jobs import derive_temperature_and_seed
from knobe.parsing import parse_rating
from knobe.registry import model_key_for
from knobe.schemas import ResultRecord

from kmp import prompts, protocol
from kmp.prompts import PromptSpec

FAMILIES = ("llama-3.1-8b", "mistral-7b-v0.1", "gemma-2-9b")
MODEL_KEYS = tuple(model_key_for(f, t) for f in FAMILIES for t in ("pretrained", "finetuned"))


@dataclass(frozen=True)
class Job:
    prompt_id: str
    model_key: str
    sample_idx: int
    text: str
    fmt: str
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
    wrapper = {"text": job.text} if job.fmt == "raw" else {"messages": [{"role": "user", "content": job.text}]}
    return EngineRequest(job_id=job.job_id, prompt_id=job.prompt_id, temperature=temperature, seed=seed,
                         max_tokens=max_tokens, want_first_token_logprobs=False, **wrapper)


def to_result(job: Job, request: EngineRequest, response: EngineResponse, model_revision: str) -> ResultRecord:
    value, ok, raw = parse_rating(response.raw_response)
    return ResultRecord(
        job_id=job.job_id, prompt_id=job.prompt_id, model_key=job.model_key, sample_idx=job.sample_idx,
        temperature=request.temperature, seed=request.seed, raw_response=raw,
        parsed_rating=value, parse_ok=ok, parse_method="regex", logprobs_0_10=None,
        model_revision=model_revision, runner_version=protocol.RUNNER_VERSION, timestamp=time.time(),
    )
