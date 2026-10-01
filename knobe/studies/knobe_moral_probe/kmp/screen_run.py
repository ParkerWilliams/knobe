"""Screening runner, reviewer client and CLI (DESIGN.md section 4).

Asks the reviewer every screening question for every approved item, appends
one ScreeningRawResult per answer to <out-dir>/screening_raw.jsonl, then
applies kmp.screen's pass rule and pair selection.

Resume: re-run the same command. A (item, question) counts as done only if a
row exists from the same reviewer model for the same prompt text
(text_sha256). A raw file holding rows from another reviewer model, or rows
whose prompt text has since changed, is refused (exit 2), like elicit's
manifest check. Unparsed answers are re-asked once.

Errors: transient API errors are retried by knobe.curate._complete_with_retry;
one that exhausts its retries, or any other error, aborts the run. Answers
already written are kept, so re-running the same command resumes.

Outputs in --out-dir: screening_raw.jsonl, selected_items.csv,
selection_report.csv, screening_meta.json (snapshot of the latest run) and
screening_runs.jsonl (one line per invocation). The meta's
shared_without_harm / shared_without_nonharm list shared-scaffold
foundations storylines that lost their harm pair / all their non-harm pairs
(kmp.screen); both are excluded from the primary pooled contrast and are
also printed to stderr.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import subprocess
import sys
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from knobe.curate import (
    _TRANSIENT_ANTHROPIC_ERRORS,
    AnthropicClient,
    MockClient,
    ReviewerSubjectConflictError,
    TransientCallError,
    _complete_with_retry,
    check_reviewer_not_subject,
    default_registry_path,
)
from knobe.parsing import parse_rating
from knobe.registry import load_registry
from knobe.schemas import append_jsonl, write_jsonl

from kmp import protocol
from kmp.items import design_problems, load_items, write_items
from kmp.prompts import ScreeningPrompt, build_screening_prompts
from kmp.screen import (
    TARGET_MIN,
    VALENCE_BAD_MAX,
    VALENCE_GOOD_MIN,
    ScreeningRawResult,
    select_pairs,
    shared_without_harm,
    shared_without_nonharm,
)

REVIEWER_TEMPERATURE = 0.0                         # DESIGN.md section 4


class ScreeningClient(AnthropicClient):
    """knobe.curate.AnthropicClient with temperature=0 (DESIGN.md section 4).

    complete() is a copy of the parent's (CLAUDE.md section 7; plan amendment 2)
    with two additions: temperature=0.0, and noting resp.model (the model
    actually served) in served_models. Construction, the transient-error
    mapping and token accounting are the parent's. A test compares the two
    method bodies, so a change to the parent fails until this copy is re-synced."""

    def __init__(self, model: str, api_key: str | None = None):
        super().__init__(model, api_key)
        self.served_models: set[str] = set()

    def _note_served(self, resp) -> None:
        served = getattr(resp, "model", None)
        if served:
            self.served_models.add(served)

    async def complete(self, prompt: str, max_tokens: int) -> str:
        try:
            resp = await self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=REVIEWER_TEMPERATURE,
                thinking={"type": "disabled"},
                messages=[{"role": "user", "content": prompt}],
            )
        except _TRANSIENT_ANTHROPIC_ERRORS as exc:
            raise TransientCallError(str(exc)) from exc
        self._note_served(resp)

        usage = getattr(resp, "usage", None)
        if usage is not None:
            self.input_tokens_used += getattr(usage, "input_tokens", 0) or 0
            self.output_tokens_used += getattr(usage, "output_tokens", 0) or 0
        return "".join(b.text for b in resp.content if b.type == "text").strip()


class ResumeRefused(ValueError):
    """The raw file's rows don't belong to this run (other reviewer, changed prompts)."""


def _read_raw(path: Path) -> list[ScreeningRawResult]:
    """Rows of screening_raw.jsonl; missing or empty file = none. A torn LAST
    line (crash mid-write) is dropped with a warning and the file repaired, so
    the next append starts on a clean line; any other bad line is an error.
    Same policy as knobe.elicit_vllm.read_results_tolerating_torn_tail, which
    is hardwired to ResultRecord, hence this small copy (CLAUDE.md section 7)."""
    if not path.exists() or path.stat().st_size == 0:
        return []
    lines = [line for line in path.read_text(encoding="utf-8").split("\n") if line.strip()]
    rows: list[ScreeningRawResult] = []
    for i, line in enumerate(lines):
        try:
            rows.append(ScreeningRawResult.model_validate_json(line))
        except ValueError as exc:
            if i != len(lines) - 1:
                raise ValueError(f"{path}: line {i + 1} is not a valid ScreeningRawResult "
                                 f"and is not the last line: {exc}") from exc
            print(f"WARNING: {path}: last line looks torn (crash mid-write); dropping it and "
                  f"repairing the file. That answer will be asked again.", file=sys.stderr)
            write_jsonl(rows, path)
    return rows


def _current(rows: list[ScreeningRawResult], prompts: list[ScreeningPrompt],
             reviewer_model: str) -> list[ScreeningRawResult]:
    """Rows from this reviewer for the current text of a current prompt."""
    want = {(p.item_id, p.qkey): p.text_sha256 for p in prompts}
    return [r for r in rows if r.reviewer_model == reviewer_model
            and want.get((r.variant_id, r.field)) == r.text_sha256]


def raw_problems(rows: list[ScreeningRawResult], prompts: list[ScreeningPrompt], reviewer_model: str,
                 limit: int = 5) -> list[str]:
    """Reasons rows already on disk can't be resumed by this run. Empty = fine."""
    problems = []
    others = sorted({r.reviewer_model for r in rows} - {reviewer_model})
    if others:
        problems.append(f"raw file has rows from reviewer model(s) {others}, this run uses {reviewer_model!r}; "
                        f"use a separate --out-dir per reviewer model")
    want = {(p.item_id, p.qkey): p.text_sha256 for p in prompts}
    changed = sorted({r.variant_id for r in rows
                      if (r.variant_id, r.field) in want and r.text_sha256 != want[(r.variant_id, r.field)]})
    if changed:
        shown = ", ".join(changed[:limit]) + (" ..." if len(changed) > limit else "")
        problems.append(f"text_sha256 changed for {len(changed)} item(s) that already have rows: {shown}")
    return problems


def scores_from_raw(rows: list[ScreeningRawResult], prompts: list[ScreeningPrompt],
                    reviewer_model: str) -> dict[str, dict[str, int | None]]:
    """First parsed value per (item, question), from rows of this reviewer for
    the current prompt text only; None if every such attempt failed."""
    scores: dict[str, dict[str, int | None]] = defaultdict(dict)
    for r in _current(rows, prompts, reviewer_model):
        if scores[r.variant_id].get(r.field) is None:
            scores[r.variant_id][r.field] = r.value if r.ok else None
    return dict(scores)


async def run_screening(prompts: list[ScreeningPrompt], client, reviewer_model: str, out_path: Path,
                        concurrency: int = 8, max_retries: int = 3) -> list[tuple[str, str]]:
    """Attempt 1 asks everything not yet asked; attempt 2 re-asks, once, what
    came back unparsed. Resumable: matching rows already in out_path count;
    non-matching ones raise ResumeRefused before anything is asked. Any error
    aborts the run (in-flight calls are cancelled; written rows stay).
    Returns the (item_id, qkey) of every call made, retries included."""
    if concurrency < 1:
        raise ValueError("concurrency must be >= 1")
    problems = raw_problems(_read_raw(out_path), prompts, reviewer_model)
    if problems:
        raise ResumeRefused(f"refusing to resume {out_path}:\n  " + "\n  ".join(problems))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sem = asyncio.Semaphore(concurrency)
    asked: list[tuple[str, str]] = []
    for attempt in (1, 2):
        attempts: dict[tuple[str, str], list[ScreeningRawResult]] = defaultdict(list)
        for r in _current(_read_raw(out_path), prompts, reviewer_model):
            attempts[(r.variant_id, r.field)].append(r)
        todo = [p for p in prompts
                if len(attempts[(p.item_id, p.qkey)]) < attempt
                and not any(r.ok for r in attempts[(p.item_id, p.qkey)])]
        if not todo:
            continue
        with open(out_path, "a", encoding="utf-8") as fh:
            async def ask(p: ScreeningPrompt) -> None:
                async with sem:
                    text, _ = await _complete_with_retry(client, p.text, protocol.REVIEW_MAX_TOKENS, max_retries)
                value, ok, raw = parse_rating(text)
                append_jsonl(ScreeningRawResult(variant_id=p.item_id, field=p.qkey, value=value, ok=ok, raw=raw,
                                                reviewer_model=reviewer_model, timestamp=time.time(),
                                                text_sha256=p.text_sha256), fh)
                asked.append((p.item_id, p.qkey))

            tasks = [asyncio.ensure_future(ask(p)) for p in todo]
            try:
                await asyncio.gather(*tasks)
            except BaseException:
                for t in tasks:          # stop in-flight calls before the file closes
                    t.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
                raise
    return asked


def pair_summary(report: list[dict]) -> dict[str, dict[str, int]]:
    """Pairs and passed pairs per arm, counted by unique pair_key (a pair with
    one approved member is still one pair, and never passes)."""
    out: dict[str, dict[str, int]] = {}
    for arm in sorted({r["arm"] for r in report}):
        keys = {r["pair_key"]: r["pair_passed"] for r in report if r["arm"] == arm}
        out[arm] = {"pairs": len(keys), "pairs_passed": sum(keys.values())}
    return out


def file_sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _git_commit() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=Path(__file__).resolve().parent,
                              capture_output=True, text=True, check=True).stdout.strip() or None
    except (OSError, subprocess.CalledProcessError):
        return None


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def pin_problems(reviewer_model: str | None) -> list[str]:
    """Reasons a real run may not use reviewer_model. Empty = fine."""
    pinned = protocol.REVIEWER_MODEL
    if pinned is None:
        return ["protocol.REVIEWER_MODEL is not set: pin the reviewer model ID in kmp/protocol.py "
                "before a real screening run (DESIGN.md section 4)"]
    problems = []
    if reviewer_model != pinned:
        problems.append(f"--reviewer-model {reviewer_model!r} differs from protocol.REVIEWER_MODEL {pinned!r}; "
                        f"change the pin in kmp/protocol.py instead")
    if reviewer_model and reviewer_model.endswith("-latest"):
        problems.append(f"{reviewer_model!r} is a moving '-latest' alias; pin a dated model ID in kmp/protocol.py")
    return problems


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="knobe_moral_probe screening",
        epilog="An error that survives the retries aborts the run; re-run the same command to resume.")
    p.add_argument("--items", required=True, type=Path, help="authored items CSV")
    p.add_argument("--out-dir", required=True, type=Path)
    who = p.add_mutually_exclusive_group()
    who.add_argument("--mock", action="store_true", help="deterministic fake reviewer, no API")
    who.add_argument("--reviewer-model", help="Claude model ID; must equal protocol.REVIEWER_MODEL (the default)")
    p.add_argument("--dry-run", action="store_true", help="print the call and token estimate, ask nothing")
    p.add_argument("--concurrency", type=int, default=8)
    args = p.parse_args(argv)
    if args.concurrency < 1:
        p.error("--concurrency must be >= 1")
    started = _utc_now()

    items = load_items(args.items)
    problems = design_problems(items, stage="authoring")
    if problems:
        print("refusing to screen:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 2
    approved = [i for i in items if i.review_status == "approved"]
    screening_prompts = build_screening_prompts(approved)
    n = len(screening_prompts)
    print(f"screening {len(approved)} approved of {len(items)} items")

    if args.dry_run:
        in_tokens = sum(len(sp.text) for sp in screening_prompts) // 4
        print(f"{n} screening prompts; worst case {2 * n} calls (one retry each)")
        print(f"~{in_tokens} input tokens + <= {n * protocol.REVIEW_MAX_TOKENS} output tokens per pass "
              f"(chars/4; worst case twice that)")
        return 0

    if args.mock:
        reviewer, temperature = "mock", None
    else:
        reviewer, temperature = args.reviewer_model or protocol.REVIEWER_MODEL, REVIEWER_TEMPERATURE
        problems = pin_problems(reviewer)
        if problems:
            print("refusing to screen:\n  " + "\n  ".join(problems), file=sys.stderr)
            return 2
        try:
            check_reviewer_not_subject(reviewer, load_registry(default_registry_path()))
        except ReviewerSubjectConflictError as exc:
            print(f"refusing to screen: {exc}", file=sys.stderr)
            return 2

    raw_path = args.out_dir / "screening_raw.jsonl"
    problems = raw_problems(_read_raw(raw_path), screening_prompts, reviewer)
    if problems:
        print(f"refusing to resume {raw_path}:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 2

    client = MockClient(unparseable_rate=0.0) if args.mock else ScreeningClient(reviewer)
    asked = asyncio.run(run_screening(screening_prompts, client, reviewer, raw_path, concurrency=args.concurrency))
    rows = _read_raw(raw_path)
    selected, report = select_pairs(approved, scores_from_raw(rows, screening_prompts, reviewer))
    write_items(selected, args.out_dir / "selected_items.csv")
    report_df = pd.DataFrame(report, columns=["item_id", "pair_key", "storyline_id", "arm", "sign",
                                              "pair_passed", "failures", "scores"])
    report_df["scores"] = [json.dumps(sc, sort_keys=True) for sc in report_df["scores"]]
    report_df.to_csv(args.out_dir / "selection_report.csv", index=False)
    summary = pair_summary(report)
    lost_harm = shared_without_harm(approved, selected)
    lost_nonharm = shared_without_nonharm(approved, selected)
    for what, ids in (("harm", lost_harm), ("non-harm", lost_nonharm)):
        if ids:
            print(f"shared storylines without a surviving {what} pair: {ids} (surviving pairs kept; "
                  f"excluded from the primary pooled contrast, sensitivity analysis only)", file=sys.stderr)

    meta = {
        "started_utc": started,
        "finished_utc": _utc_now(),
        "git_commit": _git_commit(),
        "items_path": str(args.items),
        "items_sha256": file_sha256(args.items),
        "reviewer_model": reviewer,
        "reviewer_temperature": temperature,
        "served_models": sorted(getattr(client, "served_models", ())),
        "input_tokens": getattr(client, "input_tokens_used", None),
        "output_tokens": getattr(client, "output_tokens_used", None),
        "raw_reviewer_models": sorted({r.reviewer_model for r in rows}),
        "review_max_tokens": protocol.REVIEW_MAX_TOKENS,
        "valence_bad_max": VALENCE_BAD_MAX,
        "valence_good_min": VALENCE_GOOD_MIN,
        "target_min": TARGET_MIN,
        "n_prompts": n,
        "calls": len(asked),
        "prompts_asked": len(set(asked)),
        "prompts_reused": n - len(set(asked)),
        "pairs_by_arm": summary,
        "shared_without_harm": lost_harm,
        "shared_without_nonharm": lost_nonharm,
    }
    (args.out_dir / "screening_meta.json").write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n",
                                                       encoding="utf-8")
    with open(args.out_dir / "screening_runs.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(meta, sort_keys=True) + "\n")
    print(pd.DataFrame.from_dict(summary, orient="index").to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
