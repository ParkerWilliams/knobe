"""Curation-only manipulation check for the Ngo prudential pilot
(`build_dataset.py`'s outputs/ngo_prudential_dataset.csv, 240 items: 80
Ngo/Raimondi moral scenarios + 80 new nonmoral-prudential variants + 80 new
nonmoral-procedural variants, the latter a fallback framing in case
prudential still reads as too morally loaded for some pairs).

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
severity/domain), which this pilot's plain items don't have and don't
need. `check_category_manipulation`'s thresholds (`configs/curation.yaml`:
moral_min=6, nonmoral_max=4) are reused directly for the pass/fail check
in `--check` mode, rather than redefining new numbers.

**NOT YET RUN.** This environment has no ANTHROPIC_API_KEY -- hand this to
whoever has the same curation-reviewer access already used for `knobe
curate run` (same handoff pattern as `analysis/severity_wording_check/`).

Usage:
    # 1. Verify it imports/runs clean with zero API access:
    .venv/bin/python analysis/ngo_extensions/nonmoral_pilot/curate_moral_relevance.py --mock

    # 2. Real run, once handed to someone with API access:
    .venv/bin/python analysis/ngo_extensions/nonmoral_pilot/curate_moral_relevance.py \
        --reviewer-model claude-sonnet-5

    # 3. Check pass/fail against configs/curation.yaml's thresholds (just prints):
    .venv/bin/python analysis/ngo_extensions/nonmoral_pilot/curate_moral_relevance.py --check

    # 4. Build the filtered dataset elicit.py actually reads:
    .venv/bin/python analysis/ngo_extensions/nonmoral_pilot/curate_moral_relevance.py --select

Writes outputs/moral_relevance_raw.jsonl (checkpoint/resume: already-completed
variant_ids are skipped on rerun, same pattern as
`knobe.curate.run_curation_jobs` / `analysis/severity_wording_check`).

``--select`` writes outputs/ngo_prudential_dataset_selected.csv and
outputs/selection_report.md. Selection rule, decided during brainstorming
after an earlier draft wrongly picked one nonmoral framing per pair_id
(prudential preferred, procedural as fallback) even when both passed:
**every item that independently clears its own threshold is kept** --
moral items need moral_relevance >= moral_min, nonmoral items (either
framing) need moral_relevance <= nonmoral_max. No preference between
framings when both pass for the same pair_id; pooling both is more
generalizable, not redundant, per the same reasoning
`docs/moral_foundations_extension/MORAL_FOUNDATIONS_PILOT_PLAN.md` already
uses for pooling multiple foundations together. The `category` column
(nonmoral_prudential vs. nonmoral_procedural) survives into the selected
CSV specifically so a by-framing breakdown is still possible later as a
secondary check, even though selection itself doesn't gate on it.

No automatic stop before elicitation depends on this report -- elicit.py
just reads whatever's in the selected CSV once ``--select`` has been run.
The report is for inspecting after the fact whether the post-curation
dataset looks sufficient (e.g. a pair_id passing on neither framing),
not a blocking checkpoint -- a deliberate choice given the full
elicitation run is estimated under an hour on one H200 (see README), so
re-running after a fix is cheap.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

REPO_SRC = Path(__file__).resolve().parents[3] / "src"
sys.path.insert(0, str(REPO_SRC))

from knobe import constants  # noqa: E402
from knobe.curate import AnthropicClient, MockClient, TransientCallError, _complete_with_retry  # noqa: E402
from knobe.parsing import parse_rating  # noqa: E402

import pandas as pd  # noqa: E402
import yaml  # noqa: E402

HERE = Path(__file__).parent
DATASET_PATH = HERE / "outputs" / "ngo_prudential_dataset.csv"
OUT_PATH = HERE / "outputs" / "moral_relevance_raw.jsonl"
SELECTED_PATH = HERE / "outputs" / "ngo_prudential_dataset_selected.csv"
REPORT_PATH = HERE / "outputs" / "selection_report.md"
CURATION_CONFIG_PATH = REPO_SRC.parent / "configs" / "curation.yaml"

_THRESHOLDS = {
    "moral": ("moral_min", lambda v, moral_min, nonmoral_max: v >= moral_min),
    "nonmoral_prudential": ("nonmoral_max", lambda v, moral_min, nonmoral_max: v <= nonmoral_max),
    "nonmoral_procedural": ("nonmoral_max", lambda v, moral_min, nonmoral_max: v <= nonmoral_max),
}


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


def _load_curated_and_thresholds() -> tuple[pd.DataFrame, float, float]:
    if not OUT_PATH.exists():
        print(f"{OUT_PATH} doesn't exist yet -- run curation first.", file=sys.stderr)
        sys.exit(1)

    cfg = yaml.safe_load(CURATION_CONFIG_PATH.read_text())
    moral_min, nonmoral_max = cfg["moral_min"], cfg["nonmoral_max"]

    raw = pd.read_json(OUT_PATH, lines=True)
    df = pd.read_csv(DATASET_PATH).merge(raw, on="variant_id")

    n_unparsed = (~df["parse_ok"]).sum()
    if n_unparsed:
        print(f"WARNING: {n_unparsed} unparsed moral_relevance responses excluded")
    df = df[df["parse_ok"]].copy()

    def _passes(row) -> bool:
        _, comparator = _THRESHOLDS[row["category"]]
        return comparator(row["moral_relevance"], moral_min, nonmoral_max)

    df["passed"] = df.apply(_passes, axis=1)
    return df, moral_min, nonmoral_max


def check_manipulation() -> None:
    """Applies configs/curation.yaml's moral_min/nonmoral_max thresholds
    (the same ones check_category_manipulation uses in production) to the
    curated moral_relevance scores, per category. Prints only -- use
    --select to actually build the filtered dataset elicit.py reads."""
    df, moral_min, nonmoral_max = _load_curated_and_thresholds()

    print(f"moral_min={moral_min}, nonmoral_max={nonmoral_max} (configs/curation.yaml)\n")
    for category in _THRESHOLDS:
        sub = df[df["category"] == category]
        print(f"{category}: {sub['passed'].sum()}/{len(sub)} pass "
              f"(mean moral_relevance={sub['moral_relevance'].mean():.2f})")
        failing = sub[~sub["passed"]]
        if len(failing):
            print(f"  failing variant_ids: {failing['variant_id'].tolist()}")


def select_items() -> None:
    """Builds outputs/ngo_prudential_dataset_selected.csv -- every item
    that independently clears its own category's threshold, no preference
    between nonmoral_prudential/nonmoral_procedural when both pass for the
    same pair_id (see module docstring for why). Also writes
    outputs/selection_report.md, a by-pair_id summary for inspecting
    after the fact whether the selection looks sufficient -- not a
    blocking gate; elicit.py reads the selected CSV regardless."""
    df, moral_min, nonmoral_max = _load_curated_and_thresholds()
    selected = df[df["passed"]].drop(columns=["passed", "parse_ok", "raw", "timestamp"])
    selected.to_csv(SELECTED_PATH, index=False)

    lines = [
        "# Nonmoral pilot: post-curation selection report",
        "",
        f"moral_min={moral_min}, nonmoral_max={nonmoral_max} (configs/curation.yaml). "
        f"{len(selected)}/{len(df)} items selected -> `{SELECTED_PATH.name}`.",
        "",
    ]

    failing_moral = df[(df["category"] == "moral") & (~df["passed"])]
    if len(failing_moral):
        lines.append(
            f"**{len(failing_moral)} of Ngo's original 80 items failed to read as moral** "
            f"through this project's own reviewer pipeline -- not guaranteed just because "
            f"Raimondi used them: {failing_moral['variant_id'].tolist()}"
        )
        lines.append("")

    lines.append("## Per-pair_id nonmoral framing availability\n")
    lines.append("| pair_id | prudential | procedural | usable nonmoral framings |")
    lines.append("|---|---|---|---|")
    neither_pairs = []
    for pair_id in sorted(int(p) for p in df["pair_id"].unique()):
        row_status = {}
        for cat in ("nonmoral_prudential", "nonmoral_procedural"):
            sub = df[(df["pair_id"] == pair_id) & (df["category"] == cat)]
            row_status[cat] = "pass" if len(sub) and sub["passed"].all() else "FAIL"
        n_usable = sum(1 for v in row_status.values() if v == "pass")
        if n_usable == 0:
            neither_pairs.append(pair_id)
        lines.append(f"| {pair_id} | {row_status['nonmoral_prudential']} | "
                      f"{row_status['nonmoral_procedural']} | {n_usable}/2 |")

    lines.append("")
    if neither_pairs:
        lines.append(
            f"**{len(neither_pairs)} pair_id(s) have NO usable nonmoral framing at all "
            f"(both bad+good must pass for a category to count 'pass' above): "
            f"{neither_pairs}** -- these storylines contribute nothing to the nonmoral "
            f"side; not silently dropped, flagged here per the original design doc."
        )
    else:
        lines.append("Every pair_id has at least one usable nonmoral framing.")

    REPORT_PATH.write_text("\n".join(lines) + "\n")
    print(f"wrote {SELECTED_PATH} ({len(selected)} rows) and {REPORT_PATH}")
    if neither_pairs:
        print(f"WARNING: {len(neither_pairs)} pair_id(s) with no usable nonmoral framing: {neither_pairs}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--reviewer-model", help="e.g. claude-sonnet-5 (must not be a subject model)")
    p.add_argument("--mock", action="store_true", help="use a deterministic fake client, no API needed")
    p.add_argument("--check", action="store_true", help="skip curation, just check pass/fail on existing output")
    p.add_argument("--select", action="store_true",
                    help="skip curation, build the filtered dataset + report elicit.py reads")
    p.add_argument("--concurrency", type=int, default=8)
    p.add_argument("--max-retries", type=int, default=3)
    p.add_argument("--max-tokens", type=int, default=10)
    args = p.parse_args()

    if args.check:
        check_manipulation()
        return
    if args.select:
        select_items()
        return

    if not args.mock and not args.reviewer_model:
        p.error("pass --reviewer-model <model> or --mock")

    client = MockClient() if args.mock else AnthropicClient(model=args.reviewer_model)
    asyncio.run(run_curation(client, args.concurrency, args.max_retries, args.max_tokens))


if __name__ == "__main__":
    main()
