"""Screening (DESIGN.md section 4): a reviewer model rates every approved
item; pairs pass only if both versions pass.

Pass rule per item:
  valence              bad <= 3, good >= 7
  nonmoral item        intended domain >= 6 and strictly highest of the three
  foundation item      intended foundation >= 6 and strictly higher than harm
  harm control         harm >= 6
Unparsed reviewer answers are named failures, never silently dropped.

The runner, reviewer client and CLI live in kmp.screen_run;
`python -m kmp.screen` still runs that CLI.
"""
from __future__ import annotations

from collections import defaultdict

from knobe.schemas import KnobeModel
from pydantic import field_validator

from kmp import protocol
from kmp.items import Item, pair_key

VALENCE_BAD_MAX = 3
VALENCE_GOOD_MIN = 7
# Starting value from configs/curation.yaml moral_min=6 (the main study's instrument).
# Deliberately NOT read from that config, so main-pipeline edits can't silently change kmp screening.
TARGET_MIN = 6


SCREENING_QKEYS = frozenset(("valence", *protocol.DOMAIN_CHECKS, *protocol.FOUNDATION_CHECKS))


class ScreeningRawResult(KnobeModel):
    """One reviewer answer: one line of screening_raw.jsonl.

    kmp-local because knobe.schemas.CurationRawResult validates `field` against
    the main study's constants.CURATION_QUESTIONS, which has none of the kmp
    question keys (CLAUDE.md section 7). The fields mirror CurationRawResult's,
    plus text_sha256 of the exact prompt sent; a test checks that
    CurationRawResult's fields are a subset of these, so the two can't drift
    apart silently. `field` must be a screening qkey."""

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


if __name__ == "__main__":
    from kmp.screen_run import main

    raise SystemExit(main())
