"""Phase 0 of docs/severity_confound/SEVERITY_PILOT_PLAN.md: re-run curation on the EXISTING
420 v1.1 variants with a reworded, magnitude-only severity question, to test
whether the current question's "severe or significant" disjunction is
partly a measurement artifact of the moral/severity confound (r=.885 within
moral items -- docs/severity_confound/SEVERITY_MORALIZATION_BACKGROUND.md).

**NOT YET RUN.** This environment has no ANTHROPIC_API_KEY -- run this with
whoever has the same curation-reviewer access already used for
`knobe curate run` (docs/v1_1_release_process/V1_1_WORKFLOW.md's "needs his API key" step).

Reuses the project's own curation call machinery (knobe.curate.AnthropicClient,
_complete_with_retry, knobe.parsing.parse_rating) rather than reimplementing
the API-calling/retry/parsing logic -- see docstrings there for the retry
and independent-completion semantics. Does NOT edit
constants.CURATION_QUESTIONS (a frozen instrument, master spec section 7) --
the reworded question lives only in this script, and results are written to
their own file, never to curated_v1.1.csv or the frozen release.

Usage:
    .venv/bin/python analysis/severity_wording_check/run_reworded_severity.py \
        --reviewer-model claude-sonnet-5

Writes analysis/severity_wording_check/outputs/severity_reworded_raw.jsonl,
one line per variant (checkpoint/resume: already-completed variant_ids in
that file are skipped on a rerun, same pattern as
knobe.curate.run_curation_jobs).
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

from knobe.curate import AnthropicClient, TransientCallError, _complete_with_retry  # noqa: E402
from knobe.parsing import parse_rating  # noqa: E402

import pandas as pd  # noqa: E402

# The candidate reworded question -- see docs/severity_confound/SEVERITY_PILOT_PLAN.md Phase 0
# for the rationale (drops "significant" entirely; forces a magnitude-only,
# valence-symmetric frame so the same wording works for both good and bad
# outcomes without leaning on a term that could read as "morally important").
REWORDED_SEVERITY_QUESTION = (
    "Setting aside whether this outcome is good or bad, how large is its "
    "practical impact -- in cost, scale, or people/systems affected -- on a "
    "scale from 0 (negligible) to 10 (massive)?"
)

# Same shape as constants.CURATION_PROMPT_TEMPLATE -- intentionally not
# imported from constants.py, since that module's templates are declared
# frozen alongside CURATION_QUESTIONS and this is an unadopted exploratory
# variant, not a production question.
PROMPT_TEMPLATE = "Scenario: {scenario}\n\nQuestion: {question}\nAnswer:"

VIGNETTES_PATH = REPO_SRC.parent / "data" / "release" / "v1.1" / "vignettes.csv"
OUT_PATH = Path(__file__).parent / "outputs" / "severity_reworded_raw.jsonl"


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


async def main(reviewer_model: str, concurrency: int, max_retries: int, max_tokens: int) -> None:
    vign = pd.read_csv(VIGNETTES_PATH)
    scenario_by_vid = dict(zip(vign["variant_id"], vign["scenario"]))

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    completed = _read_completed(OUT_PATH)
    remaining = [vid for vid in scenario_by_vid if vid not in completed]
    print(f"{len(completed)} already done, {len(remaining)} remaining of {len(scenario_by_vid)} total")

    client = AnthropicClient(model=reviewer_model)
    sem = asyncio.Semaphore(concurrency)
    n_errors = 0

    with open(OUT_PATH, "a", encoding="utf-8") as fh:

        async def _do_one(vid: str) -> None:
            nonlocal n_errors
            async with sem:
                prompt = PROMPT_TEMPLATE.format(
                    scenario=scenario_by_vid[vid], question=REWORDED_SEVERITY_QUESTION,
                )
                try:
                    text, retries = await _complete_with_retry(client, prompt, max_tokens, max_retries)
                except (TransientCallError, Exception) as exc:
                    n_errors += 1
                    print(f"ERROR on {vid}: {exc}", file=sys.stderr)
                    return
                value, ok, raw = parse_rating(text)
                fh.write(json.dumps(dict(
                    variant_id=vid, severity_reworded=value, parse_ok=ok, raw=raw,
                    reviewer_model=reviewer_model, timestamp=time.time(),
                )) + "\n")
                fh.flush()

        await asyncio.gather(*(_do_one(vid) for vid in remaining))

    print(f"done, {n_errors} errors (rerun this script to retry them -- unfinished jobs aren't written)")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--reviewer-model", required=True, help="e.g. claude-sonnet-5 (must not be a subject model)")
    p.add_argument("--concurrency", type=int, default=8)
    p.add_argument("--max-retries", type=int, default=3)
    p.add_argument("--max-tokens", type=int, default=10)
    args = p.parse_args()
    asyncio.run(main(args.reviewer_model, args.concurrency, args.max_retries, args.max_tokens))
