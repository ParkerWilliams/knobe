"""Merges Ngo et al. (2015)'s original 80 moral scenarios
(`ngo_2015_original_80.txt`, the same stimuli Raimondi et al.
arXiv:2510.12229 used) with this pilot's 40 new nonmoral-prudential pairs
(`prudential_variants.py`) into one dataset, ready for curation
(`curate_moral_relevance.py`) and, if that passes, elicitation.

Output: outputs/ngo_prudential_dataset.csv, one row per item (160 total: 80
original moral + 80 new nonmoral-prudential), columns:
    variant_id    -- e.g. "moral-01-bad", "prudential-01-bad"
    pair_id       -- 1-40, links a moral pair to its prudential counterpart
    category      -- "moral" | "nonmoral_prudential"
    sign          -- "bad" | "good"
    scenario      -- the 3-sentence setup (no question)
    question      -- the intentionality question
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from prudential_variants import PRUDENTIAL_PAIRS

HERE = Path(__file__).parent
SOURCE_TXT = HERE / "ngo_2015_original_80.txt"
OUT_PATH = HERE / "outputs" / "ngo_prudential_dataset.csv"

_ITEM_HEADER_RE = re.compile(r"^(\d+)\.\s*$")


def parse_ngo_items(path: Path) -> dict[int, tuple[str, str]]:
    """Returns {item_number: (scenario, question)} for all 80 Ngo items."""
    lines = path.read_text(encoding="utf-8").splitlines()
    items: dict[int, tuple[str, str]] = {}
    current_num = None
    buf: list[str] = []

    def _flush():
        if current_num is None:
            return
        text = " ".join(buf).strip()
        # last sentence ending in "?" is the question; everything before it
        # is the scenario setup.
        q_start = text.rfind(". ")
        # find the last '?' and split there instead -- more robust than the
        # sentence-count assumption, since a couple of items' scenario also
        # contains internal punctuation.
        q_idx = text.index("Did ") if "Did " in text else None
        if q_idx is None:
            raise ValueError(f"item {current_num}: no 'Did ...?' question found in: {text!r}")
        scenario = text[:q_idx].strip()
        question = text[q_idx:].strip()
        items[current_num] = (scenario, question)

    for raw in lines:
        line = raw.strip()
        m = _ITEM_HEADER_RE.match(line)
        if m:
            _flush()
            current_num = int(m.group(1))
            buf = []
            continue
        if line and current_num is not None:
            buf.append(line)
    _flush()
    return items


def main() -> None:
    ngo_items = parse_ngo_items(SOURCE_TXT)
    assert len(ngo_items) == 80, f"expected 80 Ngo items, parsed {len(ngo_items)}"

    rows = []
    for pair_id in range(1, 41):
        bad_num, good_num = 2 * pair_id - 1, 2 * pair_id
        bad_scenario, bad_question = ngo_items[bad_num]
        good_scenario, good_question = ngo_items[good_num]
        rows.append(dict(variant_id=f"moral-{pair_id:02d}-bad", pair_id=pair_id, category="moral",
                          sign="bad", scenario=bad_scenario, question=bad_question))
        rows.append(dict(variant_id=f"moral-{pair_id:02d}-good", pair_id=pair_id, category="moral",
                          sign="good", scenario=good_scenario, question=good_question))

        p_bad_scenario, p_bad_question = PRUDENTIAL_PAIRS[pair_id]["bad"]
        p_good_scenario, p_good_question = PRUDENTIAL_PAIRS[pair_id]["good"]
        rows.append(dict(variant_id=f"prudential-{pair_id:02d}-bad", pair_id=pair_id,
                          category="nonmoral_prudential", sign="bad",
                          scenario=p_bad_scenario, question=p_bad_question))
        rows.append(dict(variant_id=f"prudential-{pair_id:02d}-good", pair_id=pair_id,
                          category="nonmoral_prudential", sign="good",
                          scenario=p_good_scenario, question=p_good_question))

    out = pd.DataFrame(rows)
    assert len(out) == 160
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_PATH, index=False)
    print(f"wrote {OUT_PATH} ({len(out)} rows: 80 moral + 80 nonmoral_prudential)")


if __name__ == "__main__":
    main()
