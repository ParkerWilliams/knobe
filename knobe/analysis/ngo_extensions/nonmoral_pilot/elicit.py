"""Elicitation for the Ngo nonmoral pilot: reads
outputs/ngo_prudential_dataset_selected.csv (built by
``curate_moral_relevance.py --select``, NOT the full unfiltered
outputs/ngo_prudential_dataset.csv) x 3 questions (q_intentionality,
q_blame, q_praise) x 6 subject models x N samples. Run
``curate_moral_relevance.py --select`` first -- this script exits with an
error if the selected file doesn't exist yet, rather than silently
falling back to the unfiltered 240-item set.

Reuses this project's core inference machinery directly, not a
reimplementation:
  - ``knobe.elicit_vllm``: ``GenerationEngine``/``FakeEngine``/``VllmEngine``/
    ``build_engine`` (the actual model-calling abstraction -- includes the
    exact-forced-continuation logprob scoring that fixed the 2026-08-09
    Mistral tokenizer bug; re-deriving this would risk repeating it),
    ``EngineRequest``/``EngineResponse``, ``resolve_model_id``,
    ``_safe_parse_with_fallback``, ``_sanitize_logprobs_for_storage``.
  - ``knobe.jobs.derive_temperature_and_seed`` -- the frozen seeding rule
    (spec section 3.5): sha256(release, prompt_id, model_key, sample_idx).
    Same formula used everywhere else in this project; a pilot-specific
    ``release`` string (below) is the only new input to it.
  - ``knobe.registry.load_registry`` / ``elicit_vllm.default_registry_path``
    -- resolves real HF checkpoint ids from ``configs/models.yaml``, the
    same path that already caught the Mistral tokenizer bug once. Do not
    hand-roll model ids here.
  - ``knobe.constants.RAIMONDI_PROMPT_TEMPLATE`` -- the project's existing
    "Raimondi-comparable" prompt frame (spec section 3.4), not a new one.
  - ``knobe.schemas.ResultRecord``/``append_jsonl``/``read_jsonl`` -- the
    production result schema, so this pilot's output is directly
    loadable with the same tools as any other results.jsonl (join
    against ``outputs/ngo_prudential_dataset.csv`` via ``prompt_id``'s
    ``variant_id`` prefix, the same "no denormalized item fields" design
    the schema already uses).

**NOT reused**: ``elicit_vllm.run_elicit``'s full orchestration
(jobs.jsonl/prompts.jsonl file pipeline, release-manifest hash guard,
remote-storage durability handlers, sharding). That machinery assumes the
full production data contract -- a frozen release registered in a
manifest under ``data/release/`` -- which this pilot's flat 240-row CSV
doesn't have and doesn't need. Same reasoning
``curate_moral_relevance.py`` already gave for not reusing
``curate.run()``.

**Format: raw completion only, for BOTH pretrained and instruct models.**
Not a simplification specific to this pilot -- ``specs/00_PLAN.md``
section 5 states the PRIMARY condition is raw completion for both tuning
statuses (matching how Raimondi themselves queried their models); chat
templating is only ever a secondary robustness pass in this project. A
chat-formatted pass could be added later the same way production does;
out of scope here.

**Fallback scoring: captured, not applied, at elicitation time.** Unlike
production's ``run_elicit`` (which needs a pre-declared
``logit_fallback_checkpoints`` list, since it follows the spec's 95%-
parse-rate gate strictly), this script always requests logprobs
(``want_first_token_logprobs=True``) and always parses with
``threshold_ok=True`` (regex-only, no auto-fallback) -- deliberately, so
``parsed_rating``/``parse_ok`` reflect the literal parsed answer, and
whether to apply ``parsing.expected_rating_from_logprobs`` on top is an
analysis-time decision made per cell with real data in hand. This is a
direct lesson from this session's own investigation
(`docs/rq1_findings/RAIMONDI_REPLICATION_GAPS.md` section 3): baking in a
fallback decision before any real parse-rate data exists is exactly what
produced a spurious reversal there.

**NOT YET RUN.** Needs a GPU + the ``vllm`` extra
(``uv pip install -e '.[vllm]'``) -- this environment has neither.
Verified end-to-end with ``--engine fake`` (deterministic, no GPU, no real
model).

Usage:
    # 1. Verify clean with zero GPU/model access:
    .venv/bin/python analysis/ngo_extensions/nonmoral_pilot/elicit.py \
        --engine fake --n-samples 2

    # 2. Real run, once handed to whoever has H200/vllm access:
    .venv/bin/python analysis/ngo_extensions/nonmoral_pilot/elicit.py \
        --engine vllm --n-samples 25

Writes outputs/elicit_results.jsonl, one line per (prompt_id, model_key,
sample_idx). Checkpoint/resume: job_ids already present in that file are
skipped on a rerun, same pattern as
``analysis/severity_wording_check/run_reworded_severity.py`` and
``curate_moral_relevance.py`` in this directory.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pandas as pd

REPO_SRC = Path(__file__).resolve().parents[3] / "src"
sys.path.insert(0, str(REPO_SRC))

from knobe import constants  # noqa: E402
from knobe.elicit_vllm import (  # noqa: E402
    EngineRequest,
    _safe_parse_with_fallback,
    _sanitize_logprobs_for_storage,
    build_engine,
    default_registry_path,
    resolve_model_id,
)
from knobe.jobs import derive_temperature_and_seed  # noqa: E402
from knobe.registry import load_registry, model_key_for  # noqa: E402
from knobe.schemas import ResultRecord, append_jsonl, read_jsonl  # noqa: E402

HERE = Path(__file__).parent
DATASET_PATH = HERE / "outputs" / "ngo_prudential_dataset_selected.csv"
OUT_PATH = HERE / "outputs" / "elicit_results.jsonl"

RUNNER_VERSION = "ngo_extensions_nonmoral_pilot_elicit-0.1"
RELEASE = "ngo_extensions_nonmoral_pilot_v1"

FAMILIES = ["llama-3.1-8b", "mistral-7b-v0.1", "gemma-2-9b"]
MODEL_KEYS = [
    model_key_for(fam, tuning) for fam in FAMILIES for tuning in ("pretrained", "finetuned")
]
QUESTION_TYPES = ["q_intentionality", "q_blame", "q_praise"]
MAX_TOKENS = 10


def build_prompts(df: pd.DataFrame) -> dict[str, str]:
    """{prompt_id: prompt_text} for every (variant_id, question_type),
    prompt_id = "{variant_id}::{question_type}" (production's convention
    minus "::{format}", since this pilot only ever emits one format --
    see module docstring)."""
    prompts: dict[str, str] = {}
    for _, row in df.iterrows():
        for qtype in QUESTION_TYPES:
            prompt_id = f"{row['variant_id']}::{qtype}"
            prompts[prompt_id] = constants.RAIMONDI_PROMPT_TEMPLATE.format(
                scenario=row["scenario"], question=row[qtype],
            )
    return prompts


def build_job_list(prompt_ids: list[str], model_keys: list[str], n_samples: int) -> list[tuple[str, str, int]]:
    """(prompt_id, model_key, sample_idx) triples, in the same
    prompt-then-model-then-sample order convention as
    ``jobs.build_jobs`` (byte-stable given the same inputs)."""
    return [
        (pid, model_key, sample_idx)
        for pid in prompt_ids
        for model_key in model_keys
        for sample_idx in range(n_samples)
    ]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--engine", default="fake", choices=["fake", "vllm", "hf"])
    p.add_argument("--n-samples", type=int, default=25, help="matches this project's production N (v1.1 main run)")
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--model-keys",
                    help="comma-separated subset of the six model keys to run (default: all). "
                         "Lets the cluster runner split gemma (Triton attention backend) from "
                         "llama/mistral into separate jobs and run one subprocess per model, "
                         "per the main run's per-model-subprocess lesson.")
    p.add_argument("--registry", type=Path, default=None,
                    help="path to models.yaml (default: the repo's configs/models.yaml). "
                         "Needed on-cluster, where the bundle ships its own copy and the "
                         "repo root doesn't exist.")
    args = p.parse_args()

    if args.model_keys:
        model_keys = [k.strip() for k in args.model_keys.split(",") if k.strip()]
        unknown = sorted(set(model_keys) - set(MODEL_KEYS))
        if unknown:
            print(f"unknown model key(s) {unknown}; valid: {MODEL_KEYS}", file=sys.stderr)
            sys.exit(2)
    else:
        model_keys = MODEL_KEYS

    if not DATASET_PATH.exists():
        print(f"{DATASET_PATH} doesn't exist yet -- run "
              f"`curate_moral_relevance.py --select` first (needs curation results).", file=sys.stderr)
        sys.exit(1)
    df = pd.read_csv(DATASET_PATH)
    prompts = build_prompts(df)
    prompt_ids = sorted(prompts)
    jobs = build_job_list(prompt_ids, model_keys, args.n_samples)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = {r.job_id for r in read_jsonl(OUT_PATH, ResultRecord)} if OUT_PATH.exists() else set()
    remaining = [j for j in jobs if f"{j[0]}::{j[1]}::{j[2]}" not in existing]
    print(f"{len(existing)} already done, {len(remaining)} remaining of {len(jobs)} total "
          f"({len(prompt_ids)} prompts x {len(model_keys)} models x {args.n_samples} samples)")

    registry = load_registry(args.registry if args.registry else default_registry_path())
    engine = build_engine(args.engine)

    by_model: dict[str, list[tuple[str, str, int]]] = {}
    for job in remaining:
        by_model.setdefault(job[1], []).append(job)

    with open(OUT_PATH, "a", encoding="utf-8") as fh:
        for model_key, model_jobs in by_model.items():
            model_id, _family_name, pinned_revision = resolve_model_id(model_key, registry)
            resolved_revision = engine.load(model_id, revision=pinned_revision)
            print(f"[elicit] {model_key} ({model_id}@{resolved_revision}): {len(model_jobs)} jobs")

            for start in range(0, len(model_jobs), args.batch_size):
                batch_jobs = model_jobs[start:start + args.batch_size]
                requests = []
                for prompt_id, mk, sample_idx in batch_jobs:
                    temperature, seed = derive_temperature_and_seed(RELEASE, prompt_id, mk, sample_idx)
                    requests.append(EngineRequest(
                        job_id=f"{prompt_id}::{mk}::{sample_idx}",
                        prompt_id=prompt_id,
                        temperature=temperature,
                        seed=seed,
                        max_tokens=MAX_TOKENS,
                        text=prompts[prompt_id],
                        want_first_token_logprobs=True,
                    ))
                responses = {r.job_id: r for r in engine.generate(requests)}

                for prompt_id, mk, sample_idx in batch_jobs:
                    job_id = f"{prompt_id}::{mk}::{sample_idx}"
                    resp = responses.get(job_id)
                    if resp is None:
                        print(f"ERROR: no response for {job_id}", file=sys.stderr)
                        continue
                    temperature, seed = derive_temperature_and_seed(RELEASE, prompt_id, mk, sample_idx)
                    logprobs = _sanitize_logprobs_for_storage(resp.logprobs_0_10)
                    parsed = _safe_parse_with_fallback(resp.raw_response, logprobs, threshold_ok=True)
                    result = ResultRecord(
                        job_id=job_id, prompt_id=prompt_id, model_key=mk, sample_idx=sample_idx,
                        temperature=temperature, seed=seed,
                        raw_response=resp.raw_response,
                        parsed_rating=parsed.parsed_rating, parse_ok=parsed.parse_ok,
                        parse_method=parsed.parse_method, logprobs_0_10=logprobs,
                        model_revision=resolved_revision, runner_version=RUNNER_VERSION,
                        timestamp=time.time(),
                    )
                    append_jsonl(result, fh)
                fh.flush()

    print("done")


if __name__ == "__main__":
    main()
