"""Pick the pilot's items (DESIGN.md section 8: "a few dozen screened items, all six models").

A pair is eligible when both versions are approved in the items file (the researcher's review) and
the pair passed screening (both in the screening run's selected_items.csv, same text). Per arm, the
eligible pairs are ranked by sha256(base_seed, experiment, storyline_id, arm), the repo's seeding
convention (CLAUDE.md section 3), and the first N are taken: reproducible, not hand-picked.

Default counts (44 items): nonmoral 4 pairs each of moral, prudential, procedural (the significance
check needs moral and procedural); foundations 2 pairs each of harm, fairness, loyalty, authority,
purity. Output: one items CSV per experiment, which kmp.elicit runs as it would the full set.

--full writes the full run's items instead (docs/FULL_RUN.md): every eligible pair, for all three
sets (ngo_verbatim too), to stimuli/full_run/<experiment>.csv.

From the study folder:
    ../../.venv/bin/python -m tools.pilot_select          # pilot
    ../../.venv/bin/python -m tools.pilot_select --full   # full run
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

from kmp.items import Item, load_items, pair_key, write_items

STUDY = Path(__file__).resolve().parents[1]
BASE_SEED = "knobe_moral_probe_pilot"
COUNTS = {
    "nonmoral": {"moral": 4, "prudential": 4, "procedural": 4},
    "foundations": {"harm": 2, "fairness": 2, "loyalty": 2, "authority": 2, "purity": 2},
}
OUT_DIR = STUDY / "stimuli" / "pilot_run"
FULL_DIR = STUDY / "stimuli" / "full_run"
FULL_SETS = ("ngo_verbatim", "nonmoral", "foundations")


def _rank(key: tuple, base_seed: str) -> str:
    return hashlib.sha256("|".join(map(str, (base_seed, *key))).encode()).hexdigest()


def eligible_pairs(items: list[Item], selected: list[Item]) -> dict[tuple, list[Item]]:
    """Pairs whose two versions are approved and passed screening on their current text."""
    passed = {(i.item_id, i.scenario, i.effect) for i in selected}
    pairs: dict[tuple, list[Item]] = {}
    for item in items:
        pairs.setdefault(pair_key(item), []).append(item)
    return {k: v for k, v in pairs.items()
            if sorted(i.sign for i in v) == ["bad", "good"]
            and all(i.review_status == "approved" and (i.item_id, i.scenario, i.effect) in passed for i in v)}


def pick_all(items: list[Item], selected: list[Item]) -> list[Item]:
    return sorted((i for v in eligible_pairs(items, selected).values() for i in v), key=lambda i: i.item_id)


def pick(items: list[Item], selected: list[Item], counts: dict[str, int], base_seed: str = BASE_SEED) -> list[Item]:
    eligible = eligible_pairs(items, selected)
    out, short = [], []
    for arm, n in counts.items():
        keys = sorted((k for k in eligible if k[2] == arm), key=lambda k: _rank(k, base_seed))
        if len(keys) < n:
            short.append(f"{arm}: {len(keys)} eligible pairs, {n} wanted")
            continue
        for k in keys[:n]:
            out += sorted(eligible[k], key=lambda i: i.sign)
    if short:
        raise ValueError("not enough approved pairs that passed screening:\n  " + "\n  ".join(short))
    return sorted(out, key=lambda i: i.item_id)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--base-seed", default=BASE_SEED)
    p.add_argument("--out-dir", type=Path, help=f"default {OUT_DIR} (pilot) or {FULL_DIR} (--full)")
    p.add_argument("--full", action="store_true", help="every eligible pair of all three sets, for the full run")
    a = p.parse_args(argv)
    a.out_dir = a.out_dir or (FULL_DIR if a.full else OUT_DIR)
    a.out_dir.mkdir(parents=True, exist_ok=True)
    if a.full:
        for experiment in FULL_SETS:
            items = load_items(STUDY / "stimuli" / f"{experiment}.csv")
            selected = load_items(STUDY / "outputs" / "screening" / experiment / "selected_items.csv")
            picked = pick_all(items, selected)
            if not picked:
                print(f"{experiment}: no approved pairs that passed screening", file=sys.stderr)
                return 1
            write_items(picked, a.out_dir / f"{experiment}.csv")
            print(f"{experiment}: {len(picked)} items ({len(picked) // 2} pairs) -> {a.out_dir / f'{experiment}.csv'}")
        return 0
    for experiment, counts in COUNTS.items():
        items = load_items(STUDY / "stimuli" / f"{experiment}.csv")
        selected = load_items(STUDY / "outputs" / "screening" / experiment / "selected_items.csv")
        try:
            picked = pick(items, selected, counts, a.base_seed)
        except ValueError as exc:
            print(f"{experiment}: {exc}", file=sys.stderr)
            return 1
        write_items(picked, a.out_dir / f"{experiment}.csv")
        print(f"{experiment}: {len(picked)} items -> {a.out_dir / f'{experiment}.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
