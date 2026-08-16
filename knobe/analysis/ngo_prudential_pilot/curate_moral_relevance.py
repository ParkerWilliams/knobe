"""Curation-only manipulation check for the Ngo prudential pilot
(`build_dataset.py`'s outputs/ngo_prudential_dataset.csv, 160 items: 80
Ngo/Raimondi moral scenarios + 80 new nonmoral-prudential variants).

Per the pilot's scope, this asks exactly one question -- the project's own
frozen `moral_relevance` curation question (`constants.CURATION_QUESTIONS`,
`constants.CURATION_PROMPT_TEMPLATE`) -- not the full 4-question curation
battery (severity/vividness/typicality_perception don't apply here, since
this pilot doesn't cross those axes). Reuses the project's own curation
call machinery (`knobe.curate.AnthropicClient`/`MockClient`,
`_complete_with_retry`, `knobe.parsing.parse_rating`) rather than
reimplementing the API-calling/retry/parsing logic -- NOT reusing
`curate.run()`'s full orchestration, because that expects a `Family`
registry and the production `CuratedRow` schema (typicality/evocativeness/
severity/domain), which this pilot's 160 plain items don't have and don't
need. `check_category_manipulation`'s thresholds (`configs/curation.yaml`:
moral_min=6, nonmoral_max=4) are reused directly for the pass/fail check
in `--check` mode, rather than redefining new numbers.

**NOT YET RUN.** This environment has no ANTHROPIC_API_KEY -- hand this to
whoever has the same curation-reviewer access already used for `knobe
curate run` (same handoff pattern as `analysis/severity_wording_check/`).

Usage:
    # 1. Verify it imports/runs clean with zero API access:
    .venv/bin/python analysis/ngo_prudential_pilot/curate_moral_relevance.py --mock

    # 2. Real run, once handed to someone with API access:
    .venv/bin/python analysis/ngo_prudential_pilot/curate_moral_relevance.py \
        --reviewer-model claude-sonnet-5

    # 3. Check pass/fail against configs/curation.yaml's thresholds:
    .venv/bin/python analysis/ngo_prudential_pilot/curate_moral_relevance.py --check

Writes outputs/moral_relevance_raw.jsonl (checkpoint/resume: already-completed
variant_ids are skipped on rerun, same pattern as
`knobe.curate.run_curation_jobs` / `analysis/severity_wording_check`).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

REPO_SRC = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(REPO_SRC))

from knobe import constants  # noqa: E402
from knobe.curate import AnthropicClient, MockClient, TransientCallError, _complete_with_retry  # noqa: E402
from knobe.parsing import parse_rating  # noqa: E402

import pandas as pd  # noqa: E402
import yaml  # noqa: E402

HERE = Path(__file__).parent
DATASET_PATH = HERE / "outputs" / "ngo_prudential_dataset.csv"
OUT_PATH = HERE / "outputs" / "moral_relevance_raw.jsonl"
CURATION_CONFIG_PATH = REPO_SRC.parent / "configs" / "curation.yaml"


def _read_completed(path: Path) -> set[str]:
    if not path.exists():
        return set()
    completed = set()
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                completed.add(json.loads(line)["variant_id"])
    return completed


async def run_curation(client, concurrency: int, max_retries: int, max_tokens: int) -> None:
    df = pd.read_csv(DATASET_PATH)
    scenario_by_vid = dict(zip(df["variant_id"], df["scenario"]))

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    completed = _read_completed(OUT_PATH)
    remaining = [vid for vid in scenario_by_vid if vid not in completed]
    print(f"{len(completed)} already done, {len(remaining)} remaining of {len(scenario_by_vid)} total")

    sem = asyncio.Semaphore(concurrency)
    n_errors = 0

    with open(OUT_PATH, "a", encoding="utf-8") as fh:

        async def _do_one(vid: str) -> None:
            nonlocal n_errors
            async with sem:
                prompt = constants.CURATION_PROMPT_TEMPLATE.format(
                    scenario=scenario_by_vid[vid],
                    question=constants.CURATION_QUESTIONS["moral_relevance"],
                )
                try:
                    text, retries = await _complete_with_retry(client, prompt, max_tokens, max_retries)
                except (TransientCallError, Exception) as exc:
                    n_errors += 1
                    print(f"ERROR on {vid}: {exc}", file=sys.stderr)
                    return
                value, ok, raw = parse_rating(text)
                fh.write(json.dumps(dict(
                    variant_id=vid, moral_relevance=value, parse_ok=ok, raw=raw,
                    timestamp=time.time(),
                )) + "\n")
                fh.flush()

        await asyncio.gather(*(_do_one(vid) for vid in remaining))

    print(f"done, {n_errors} errors (rerun this script to retry them -- unfinished jobs aren't written)")


def check_manipulation() -> None:
    """Applies configs/curation.yaml's moral_min/nonmoral_max thresholds
    (the same ones check_category_manipulation uses in production) to the
    curated moral_relevance scores, per category."""
    if not OUT_PATH.exists():
        print(f"{OUT_PATH} doesn't exist yet -- run curation first.", file=sys.stderr)
        sys.exit(1)

    cfg = yaml.safe_load(CURATION_CONFIG_PATH.read_text())
    moral_min, nonmoral_max = cfg["moral_min"], cfg["nonmoral_max"]

    raw = pd.read_json(OUT_PATH, lines=True)
    df = pd.read_csv(DATASET_PATH).merge(raw, on="variant_id")

    n_unparsed = (~df["parse_ok"]).sum()
    if n_unparsed:
        print(f"WARNING: {n_unparsed} unparsed moral_relevance responses excluded from the check")
    df = df[df["parse_ok"]]

    print(f"moral_min={moral_min}, nonmoral_max={nonmoral_max} (configs/curation.yaml)\n")
    for category, threshold, comparator in [
        ("moral", moral_min, lambda v: v >= moral_min),
        ("nonmoral_prudential", nonmoral_max, lambda v: v <= nonmoral_max),
    ]:
        sub = df[df["category"] == category]
        passed = sub["moral_relevance"].apply(comparator)
        print(f"{category}: {passed.sum()}/{len(sub)} pass "
              f"(mean moral_relevance={sub['moral_relevance'].mean():.2f})")
        failing = sub[~passed]
        if len(failing):
            print(f"  failing variant_ids: {failing['variant_id'].tolist()}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--reviewer-model", help="e.g. claude-sonnet-5 (must not be a subject model)")
    p.add_argument("--mock", action="store_true", help="use a deterministic fake client, no API needed")
    p.add_argument("--check", action="store_true", help="skip curation, just check pass/fail on existing output")
    p.add_argument("--concurrency", type=int, default=8)
    p.add_argument("--max-retries", type=int, default=3)
    p.add_argument("--max-tokens", type=int, default=10)
    args = p.parse_args()

    if args.check:
        check_manipulation()
        return

    if not args.mock and not args.reviewer_model:
        p.error("pass --reviewer-model <model> or --mock")

    client = MockClient() if args.mock else AnthropicClient(model=args.reviewer_model)
    asyncio.run(run_curation(client, args.concurrency, args.max_retries, args.max_tokens))


if __name__ == "__main__":
    main()
