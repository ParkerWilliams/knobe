"""Merges Ngo et al. (2015)'s original 80 moral scenarios
(`ngo_2015_original_80.txt`, the same stimuli Raimondi et al.
arXiv:2510.12229 used) with this pilot's 40 new nonmoral-prudential pairs
(`prudential_variants.py`) and 40 new nonmoral-procedural pairs
(`procedural_variants.py`, a fallback framing in case prudential still
reads as too morally loaded for some pairs) into one dataset, ready for
curation (`curate_moral_relevance.py`) and, if that passes, elicitation.

Output: outputs/ngo_prudential_dataset.csv, one row per item (240 total: 80
original moral + 80 nonmoral-prudential + 80 nonmoral-procedural), columns:
    variant_id      -- e.g. "moral-01-bad", "prudential-01-bad"
    pair_id         -- 1-40, links a moral pair to its prudential counterpart
    category        -- "moral" | "nonmoral_prudential" | "nonmoral_procedural"
    sign            -- "bad" | "good"
    scenario        -- the 3-sentence setup (no question)
    q_intentionality -- the intentionality question (targets the SIDE EFFECT,
                        e.g. "Did Bill intentionally cause the death of
                        babies?" -- never the main action, e.g. releasing
                        the gadget, which is never in question)
    q_blame         -- constants.QUESTIONS["q_blame"], same agent phrase
    q_praise        -- constants.QUESTIONS["q_praise"], same agent phrase

q_blame/q_praise reuse this project's own frozen question wording
(constants.QUESTIONS) rather than inventing new phrasing, and are rendered
for EVERY item regardless of sign -- matching render.py's production
convention (every variant gets all three question types; it's the
*analysis* stage, not elicitation, that later picks blame-for-bad /
praise-for-good, per build_1b_frame's channel logic in
analysis/rq1_v1_1_robustness/lib.py). The agent phrase is extracted
directly from each item's own q_intentionality text (the substring between
"Did " and "intentionally"/"cause") rather than added as a separate field,
since every question already has it correctly cased for embedding.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

from prudential_variants import PRUDENTIAL_PAIRS
from procedural_variants import PROCEDURAL_PAIRS

REPO_SRC = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(REPO_SRC))
from knobe import constants  # noqa: E402

HERE = Path(__file__).parent
SOURCE_TXT = HERE / "ngo_2015_original_80.txt"
OUT_PATH = HERE / "outputs" / "ngo_prudential_dataset.csv"

_ITEM_HEADER_RE = re.compile(r"^(\d+)\.\s*$")
_AGENT_RE = re.compile(r"^Did (.+?) (?:intentionally|cause)\b")


def extract_agent_phrase(question: str) -> str:
    """Pulls the already-correctly-cased agent reference out of a
    "Did <agent> intentionally/cause ...?" question, e.g. "Bill" or
    "the CEO", for reuse in constants.QUESTIONS' {agent_lower} slot."""
    m = _AGENT_RE.match(question)
    if not m:
        raise ValueError(f"couldn't extract agent phrase from: {question!r}")
    return m.group(1)


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


def _make_row(variant_id: str, pair_id: int, category: str, sign: str, scenario: str, question: str) -> dict:
    agent = extract_agent_phrase(question)
    return dict(
        variant_id=variant_id, pair_id=pair_id, category=category, sign=sign,
        scenario=scenario, q_intentionality=question,
        q_blame=constants.QUESTIONS["q_blame"].format(agent_lower=agent),
        q_praise=constants.QUESTIONS["q_praise"].format(agent_lower=agent),
    )


def main() -> None:
    ngo_items = parse_ngo_items(SOURCE_TXT)
    assert len(ngo_items) == 80, f"expected 80 Ngo items, parsed {len(ngo_items)}"

    rows = []
    for pair_id in range(1, 41):
        bad_num, good_num = 2 * pair_id - 1, 2 * pair_id
        bad_scenario, bad_question = ngo_items[bad_num]
        good_scenario, good_question = ngo_items[good_num]
        rows.append(_make_row(f"moral-{pair_id:02d}-bad", pair_id, "moral", "bad", bad_scenario, bad_question))
        rows.append(_make_row(f"moral-{pair_id:02d}-good", pair_id, "moral", "good", good_scenario, good_question))

        p_bad_scenario, p_bad_question = PRUDENTIAL_PAIRS[pair_id]["bad"]
        p_good_scenario, p_good_question = PRUDENTIAL_PAIRS[pair_id]["good"]
        rows.append(_make_row(f"prudential-{pair_id:02d}-bad", pair_id, "nonmoral_prudential", "bad",
                               p_bad_scenario, p_bad_question))
        rows.append(_make_row(f"prudential-{pair_id:02d}-good", pair_id, "nonmoral_prudential", "good",
                               p_good_scenario, p_good_question))

        c_bad_scenario, c_bad_question = PROCEDURAL_PAIRS[pair_id]["bad"]
        c_good_scenario, c_good_question = PROCEDURAL_PAIRS[pair_id]["good"]
        rows.append(_make_row(f"procedural-{pair_id:02d}-bad", pair_id, "nonmoral_procedural", "bad",
                               c_bad_scenario, c_bad_question))
        rows.append(_make_row(f"procedural-{pair_id:02d}-good", pair_id, "nonmoral_procedural", "good",
                               c_good_scenario, c_good_question))

    out = pd.DataFrame(rows)
    assert len(out) == 240
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_PATH, index=False)
    print(f"wrote {OUT_PATH} ({len(out)} rows: 80 moral + 80 nonmoral_prudential + 80 nonmoral_procedural, "
          f"each with q_intentionality/q_blame/q_praise)")


if __name__ == "__main__":
    main()
