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

from collections import defaultdict

from kmp import protocol
from kmp.items import Item, pair_key

VALENCE_BAD_MAX = 3
VALENCE_GOOD_MIN = 7
TARGET_MIN = 6


def intended_check(item: Item) -> str:
    return f"domain_{item.arm}" if item.experiment == "nonmoral" else f"fnd_{item.arm}"


def item_failures(item: Item, scores: dict[str, int | None]) -> list[str]:
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
        if any(o is None for o in others):
            failures.append("a domain rating is unparsed")
        elif any(o >= t for o in others):
            failures.append(f"{target_key} is not the highest domain rating")
    elif item.arm != "harm":
        h = scores.get("fnd_harm")
        if h is None:
            failures.append("fnd_harm unparsed")
        elif t <= h:
            failures.append(f"{target_key} {t} not higher than fnd_harm {h}")
    return failures


def select_pairs(items: list[Item], scores_by_item: dict[str, dict[str, int | None]]) -> tuple[list[Item], list[dict]]:
    pairs: dict[tuple, list[Item]] = defaultdict(list)
    for item in items:
        pairs[pair_key(item)].append(item)
    selected, report = [], []
    for _key, members in sorted(pairs.items()):
        members = sorted(members, key=lambda i: i.sign)                     # bad, good
        failures = {m.item_id: item_failures(m, scores_by_item.get(m.item_id, {})) for m in members}
        if len(members) != 2:
            for m in members:
                failures[m.item_id].append("partner not approved")
        passed = all(not f for f in failures.values())
        if passed:
            selected += members
        report += [dict(item_id=m.item_id, storyline_id=m.storyline_id, arm=m.arm, sign=m.sign,
                        pair_passed=passed, failures="; ".join(failures[m.item_id])) for m in members]
    return selected, report
