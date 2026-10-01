"""Screening (DESIGN.md section 4): a reviewer model rates every approved
item; pairs pass only if both versions pass.

Pass rule per item:
  valence              bad <= 3, good >= 7
  nonmoral item        intended domain >= 6 and strictly highest of the three
  foundation item      intended foundation >= 6 and strictly higher than harm
  harm control         harm >= 6
Unparsed reviewer answers are named failures, never silently dropped.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
import time
from collections import defaultdict
from pathlib import Path

import pandas as pd
from knobe.curate import (
    _TRANSIENT_ANTHROPIC_ERRORS,
    AnthropicClient,
    MockClient,
    TransientCallError,
    _complete_with_retry,
    check_reviewer_not_subject,
    default_registry_path,
)
from knobe.parsing import parse_rating
from knobe.registry import load_registry
from knobe.schemas import KnobeModel, append_jsonl, read_jsonl
from pydantic import field_validator

from kmp import protocol
from kmp.items import Item, design_problems, load_items, pair_key, write_items
from kmp.prompts import ScreeningPrompt, build_screening_prompts

VALENCE_BAD_MAX = 3
VALENCE_GOOD_MIN = 7
# Starting value from configs/curation.yaml moral_min=6 (the main study's instrument).
# Deliberately NOT read from that config, so main-pipeline edits can't silently change kmp screening.
TARGET_MIN = 6


SCREENING_QKEYS = frozenset(("valence", *protocol.DOMAIN_CHECKS, *protocol.FOUNDATION_CHECKS))


class ScreeningRawResult(KnobeModel):
    """One reviewer answer: one line of screening_raw.jsonl.

    kmp-local because knobe.schemas.ScreeningRawResult validates field against
    the main study's CURATION_QUESTIONS; fields mirror it (CLAUDE.md section 7;
    a test keeps ScreeningRawResult's fields a subset of these), plus
    text_sha256 of the exact prompt sent. `field` is a screening qkey."""

    variant_id: str
    field: str
    value: int | None = None
    ok: bool
    raw: str
    reviewer_model: str
    timestamp: float
    text_sha256: str

    @field_validator("field")
    @classmethod
    def _field_known(cls, v: str) -> str:
        if v not in SCREENING_QKEYS or v not in protocol.QUESTIONS:
            raise ValueError(f"field {v!r} is not a screening question {sorted(SCREENING_QKEYS)}")
        return v


def intended_check(item: Item) -> str:
    return f"domain_{item.arm}" if item.experiment == "nonmoral" else f"fnd_{item.arm}"


def item_failures(item: Item, scores: dict[str, int | None] | None) -> list[str]:
    """scores=None (or empty) means the item was never rated."""
    if not scores:
        return ["not rated"]
    failures = []
    v = scores.get("valence")
    if v is None:
        failures.append("valence unparsed")
    elif item.sign == "bad" and v > VALENCE_BAD_MAX:
        failures.append(f"valence {v} > {VALENCE_BAD_MAX} for a bad item")
    elif item.sign == "good" and v < VALENCE_GOOD_MIN:
        failures.append(f"valence {v} < {VALENCE_GOOD_MIN} for a good item")

    target_key = intended_check(item)
    t = scores.get(target_key)
    if t is None:
        failures.append(f"{target_key} unparsed")
        return failures
    if t < TARGET_MIN:
        failures.append(f"{target_key} {t} < {TARGET_MIN}")

    if item.experiment == "nonmoral":
        others = [scores.get(k) for k in protocol.DOMAIN_CHECKS if k != target_key]
        missing = [k for k in protocol.DOMAIN_CHECKS if k != target_key and scores.get(k) is None]
        failures += [f"{k} unparsed" for k in missing]
        if not missing and any(o >= t for o in others):
            failures.append(f"{target_key} is not the highest domain rating")
    elif item.arm != "harm":
        h = scores.get("fnd_harm")
        if h is None:
            failures.append("fnd_harm unparsed")
        elif t <= h:
            failures.append(f"{target_key} {t} not higher than fnd_harm {h}")
    return failures


def select_pairs(items: list[Item], scores_by_item: dict[str, dict[str, int | None]]) -> tuple[list[Item], list[dict]]:
    ids = [i.item_id for i in items]
    dups = sorted({x for x in ids if ids.count(x) > 1})
    if dups:
        raise ValueError(f"duplicate item_ids in input: {dups}")
    pairs: dict[tuple, list[Item]] = defaultdict(list)
    for item in items:
        pairs[pair_key(item)].append(item)
    selected, report = [], []
    for key, members in sorted(pairs.items()):
        members = sorted(members, key=lambda i: i.sign)                     # bad, good
        failures = {m.item_id: item_failures(m, scores_by_item.get(m.item_id)) for m in members}
        if [m.sign for m in members] != ["bad", "good"]:
            for m in members:
                failures[m.item_id].append("partner not approved")
        passed = all(not f for f in failures.values())
        if passed:
            selected += members
        report += [dict(item_id=m.item_id, pair_key="|".join(map(str, key)), storyline_id=m.storyline_id,
                        arm=m.arm, sign=m.sign, pair_passed=passed, failures="; ".join(failures[m.item_id]),
                        scores=dict(scores_by_item.get(m.item_id) or {})) for m in members]
    return selected, report


class ScreeningClient(AnthropicClient):
    """knobe.curate.AnthropicClient with temperature=0 (DESIGN.md section 4).
    complete() is reimplemented only to add that one argument (plan
    amendment 2); construction, retries and token accounting are inherited."""

    async def complete(self, prompt: str, max_tokens: int) -> str:
        try:
            resp = await self._client.messages.create(
                model=self.model, max_tokens=max_tokens, temperature=0.0,
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


def _read_raw(path: Path) -> list[ScreeningRawResult]:
    return read_jsonl(path, ScreeningRawResult) if path.exists() and path.stat().st_size else []


def scores_from_raw(rows: list[ScreeningRawResult]) -> dict[str, dict[str, int | None]]:
    """First parsed value per (item, question); None if every attempt failed."""
    scores: dict[str, dict[str, int | None]] = defaultdict(dict)
    for r in rows:
        if scores[r.variant_id].get(r.field) is None:
            scores[r.variant_id][r.field] = r.value if r.ok else None
    return dict(scores)


async def run_screening(prompts: list[ScreeningPrompt], client, reviewer_model: str, out_path: Path,
                        concurrency: int = 8, max_retries: int = 3) -> None:
    """Attempt 1 asks everything not yet asked; attempt 2 re-asks, once, what
    came back unparsed. Resumable: rows already in out_path count."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sem = asyncio.Semaphore(concurrency)
    for attempt in (1, 2):
        attempts: dict[tuple[str, str], list[ScreeningRawResult]] = defaultdict(list)
        for r in _read_raw(out_path):
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
            await asyncio.gather(*(ask(p) for p in todo))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="knobe_moral_probe screening")
    p.add_argument("--items", required=True, type=Path, help="authored items CSV")
    p.add_argument("--out-dir", required=True, type=Path)
    who = p.add_mutually_exclusive_group(required=True)
    who.add_argument("--mock", action="store_true", help="deterministic fake reviewer, no API")
    who.add_argument("--reviewer-model", help="pinned Claude model ID; recorded on every row")
    p.add_argument("--concurrency", type=int, default=8)
    args = p.parse_args(argv)

    items = load_items(args.items)
    problems = design_problems(items)
    if problems:
        print("refusing to screen:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 2
    approved = [i for i in items if i.review_status == "approved"]
    print(f"screening {len(approved)} approved of {len(items)} items")

    if args.mock:
        client, reviewer = MockClient(unparseable_rate=0.0), "mock"
    else:
        check_reviewer_not_subject(args.reviewer_model, load_registry(default_registry_path()))
        client, reviewer = ScreeningClient(args.reviewer_model), args.reviewer_model

    raw_path = args.out_dir / "screening_raw.jsonl"
    asyncio.run(run_screening(build_screening_prompts(approved), client, reviewer, raw_path,
                              concurrency=args.concurrency))
    selected, report = select_pairs(approved, scores_from_raw(_read_raw(raw_path)))
    write_items(selected, args.out_dir / "selected_items.csv")
    report_df = pd.DataFrame(report, columns=["item_id", "storyline_id", "arm", "sign", "pair_passed", "failures"])
    report_df.to_csv(args.out_dir / "selection_report.csv", index=False)
    summary = report_df.assign(pairs=1).groupby("arm")[["pair_passed", "pairs"]].sum() // 2
    print(summary.rename(columns={"pair_passed": "pairs_passed"}).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
