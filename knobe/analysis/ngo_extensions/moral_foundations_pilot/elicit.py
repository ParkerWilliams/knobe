"""Elicitation for the moral-foundations pilot: reads
outputs/mf_pilot_dataset_selected.csv (built by
``curate_foundation_relevance.py --select``, NOT the unfiltered
outputs/mf_pilot_dataset.csv) x the --questions subset (default
q_intentionality only, the original 2026-08-19 run) x 6 subject models x N
samples. Exits with an error if the selected file doesn't exist
yet rather than silently falling back to the unfiltered set.

q_blame/q_praise were originally out of scope (design doc section 2) and
were added 2026-09-25 per SUBMISSION_GAMEPLAN.md section 5 item 6 -- see
build_dataset.py's docstring. They are opt-in via ``--questions`` so the
default invocation still reproduces the original intentionality-only run
exactly. RELEASE is unchanged: seeds derive from (RELEASE, prompt_id,
model_key, sample_idx), so the new prompt_ids get their own seeds and the
existing q_intentionality rows' job_ids and seeds are untouched --
results from both runs merge into one file without collision.
RUNNER_VERSION is bumped so each row records which code produced it.
Everything else mirrors `../nonmoral_pilot/elicit.py`, including exactly
what it reuses from the production pipeline and why:

  - ``knobe.elicit_vllm``: the engine abstraction (incl. the
    exact-forced-continuation logprob scoring that fixed the 2026-08-09
    Mistral tokenizer bug), ``EngineRequest``, ``resolve_model_id``,
    ``_safe_parse_with_fallback``, ``_sanitize_logprobs_for_storage``.
  - ``knobe.jobs.derive_temperature_and_seed`` -- the frozen seeding rule,
    with this pilot's own ``release`` string as the only new input.
  - ``knobe.registry`` for real HF checkpoint resolution; never hand-roll
    model ids.
  - ``knobe.constants.RAIMONDI_PROMPT_TEMPLATE`` -- the existing
    Raimondi-comparable prompt frame.
  - ``knobe.schemas.ResultRecord``/``append_jsonl``/``read_jsonl`` -- the
    production result schema; join analysis-side against
    outputs/mf_pilot_dataset.csv via the ``variant_id`` prefix of
    ``prompt_id``.

NOT reused: ``elicit_vllm.run_elicit``'s full release-manifest/sharding
orchestration (this pilot's flat CSV has no frozen release manifest), for
the same reason the sibling gives. Raw-completion format for both tuning
statuses (the project's PRIMARY condition, specs/00_PLAN.md section 5);
fallback scoring captured (logprobs always requested) but not applied at
elicitation time -- an analysis-time decision, per the
RAIMONDI_REPLICATION_GAPS.md section 3 lesson.

q_intentionality run 2026-08-19 (18,900 rows, published as
results_dist/results_pilot_moral_foundations_all.jsonl.gz); q_blame/q_praise
not yet run. Needs a GPU + the ``vllm`` extra; ``--engine fake`` verifies
end-to-end with no GPU or real model.

Usage:
    # 1. Verify clean with zero GPU/model access:
    .venv/bin/python analysis/ngo_extensions/moral_foundations_pilot/elicit.py \
        --engine fake --n-samples 2

    # 2. Real run, once handed to whoever has H200/vllm access:
    .venv/bin/python analysis/ngo_extensions/moral_foundations_pilot/elicit.py \
        --engine vllm --n-samples 25

    # 3. The 2026-09-25 blame/praise extension:
    .venv/bin/python analysis/ngo_extensions/moral_foundations_pilot/elicit.py \
        --engine vllm --n-samples 25 --questions q_blame,q_praise

Writes outputs/elicit_results.jsonl, one line per (prompt_id, model_key,
sample_idx). Checkpoint/resume: job_ids already present in that file are
skipped on a rerun.
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
DATASET_PATH = HERE / "outputs" / "mf_pilot_dataset_selected.csv"
OUT_PATH = HERE / "outputs" / "elicit_results.jsonl"

RUNNER_VERSION = "ngo_extensions_moral_foundations_pilot_elicit-0.2"
RELEASE = "ngo_extensions_moral_foundations_pilot_v1"

FAMILIES = ["llama-3.1-8b", "mistral-7b-v0.1", "gemma-2-9b"]
MODEL_KEYS = [
    model_key_for(fam, tuning) for fam in FAMILIES for tuning in ("pretrained", "finetuned")
]
QUESTION_TYPES = ["q_intentionality", "q_blame", "q_praise"]
DEFAULT_QUESTIONS = ["q_intentionality"]
MAX_TOKENS = 10


def build_prompts(df: pd.DataFrame, question_types: list[str]) -> dict[str, str]:
    """{prompt_id: prompt_text}, prompt_id = "{variant_id}::{question_type}"
    (same convention as the sibling pilot, so result rows join/parse
    identically)."""
    prompts: dict[str, str] = {}
    for _, row in df.iterrows():
        for qtype in question_types:
            prompt_id = f"{row['variant_id']}::{qtype}"
            prompts[prompt_id] = constants.RAIMONDI_PROMPT_TEMPLATE.format(
                scenario=row["scenario"], question=row[qtype],
            )
    return prompts


def build_job_list(prompt_ids: list[str], model_keys: list[str], n_samples: int) -> list[tuple[str, str, int]]:
    """(prompt_id, model_key, sample_idx) triples, prompt-then-model-then-
    sample order (jobs.build_jobs' byte-stable convention)."""
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
    p.add_argument("--questions", default=",".join(DEFAULT_QUESTIONS),
                    help=f"comma-separated subset of {QUESTION_TYPES} (default: "
                         f"{','.join(DEFAULT_QUESTIONS)}, the original run).")
    args = p.parse_args()

    question_types = [q.strip() for q in args.questions.split(",") if q.strip()]
    unknown_q = sorted(set(question_types) - set(QUESTION_TYPES))
    if unknown_q or not question_types:
        print(f"unknown/empty question type(s) {unknown_q}; valid: {QUESTION_TYPES}", file=sys.stderr)
        sys.exit(2)

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
              f"`curate_foundation_relevance.py --select` first (needs curation results).", file=sys.stderr)
        sys.exit(1)
    df = pd.read_csv(DATASET_PATH)
    missing_cols = sorted(set(question_types) - set(df.columns))
    if missing_cols:
        print(f"{DATASET_PATH.name} lacks column(s) {missing_cols} -- rebuild it: "
              f"build_dataset.py, then curate_foundation_relevance.py --select.", file=sys.stderr)
        sys.exit(1)
    prompts = build_prompts(df, question_types)
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
