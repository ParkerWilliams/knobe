"""Ngo et al. (2015)'s 80 vignettes as the ngo_verbatim items (DESIGN.md
2026-10-01 amendment "Ngo goals and verbatim set"; DEFINITIONS_AND_CHECKLIST.md
sections 3.4, 3.5 and check B9).

Source: analysis/ngo_extensions/nonmoral_pilot/ngo_2015_original_80.txt, the
pilots' copy of Ngo's stimulus appendix. Each vignette is a header line "N."
followed by four non-blank lines: three scenario clauses, then the question
("Did X intentionally ...?").

Signs: the file does not label them. Ngo lists every pair as the harm
version, then the help version, so item 2N-1 is bad, item 2N is good, and
both belong to pair N = storyline N. The pilots used the same convention
(nonmoral_pilot/prudential_variants.py: "pair_id N -> source items 2N-1
[bad], 2N [good]"), and DEFINITIONS section 3.4 numbers storylines this way.
tests/test_ngo_source.py pins it on the content of several pairs.

Word for word: each line loses only its surrounding whitespace (the file
pads lines with spaces, U+00A0 and U+2028), and the three clauses are joined
with one space. Nothing inside a line changes: typos, curly apostrophes and
Ngo's names and pronouns all stay.

agent: the question's subject ("Did Bill intentionally ..." gives "Bill"),
which must open the scenario. Where Ngo's question names the agent
differently from the scenario, AGENT_OVERRIDES gives the scenario's name.
effect: the rest of Ngo's question, verbatim, without the "?". Two questions
(73, 79) have no "intentionally"; NO_INTENT_SUBJECT names their subjects.

CLI: writes stimuli/ngo_verbatim.csv if it does not exist. If it exists, it
only compares (review statuses live in that file), exit 1 if the file
differs from the source. --update rewrites it from the source after a
parser fix, keeping review_status for items whose text is unchanged and
resetting changed items to draft, so they go back for review.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from kmp.items import Item, design_problems, load_items, make_item_id, write_items

STUDY_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = STUDY_DIR.parents[1]
SOURCE = REPO_ROOT / "analysis" / "ngo_extensions" / "nonmoral_pilot" / "ngo_2015_original_80.txt"
OUT = STUDY_DIR / "stimuli" / "ngo_verbatim.csv"
N_ITEMS = 80

# Where Ngo's question names the agent differently from the scenario, the
# scenario's name is the agent (the question line is not used; protocol.py
# asks its own questions).
AGENT_OVERRIDES: dict[int, str] = {
    12: "the company owner",       # question: "the CEO"
    53: "Philip",                  # question and clauses 2-3: "Phillip"
    57: "the cop",                 # question: "he"
    69: "the financial officer",   # question: "the director"
    70: "the treasurer",           # question: "the director"
}
# Questions without "intentionally": their subject, so the effect can be cut off.
NO_INTENT_SUBJECT: dict[int, str] = {73: "the cult leader", 79: "the doctor"}
# Fields that must match the source exactly (everything but review_status).
TEXT_FIELDS = ("experiment", "storyline_id", "arm", "sign", "agent", "effect", "scenario", "source", "scaffold")

_HEADER = re.compile(r"(\d+)\.")
_QUESTION = re.compile(r"Did (.+?) intentionally (.+)\?")


def read_blocks(text: str) -> dict[int, list[str]]:
    """Item number -> its non-blank lines, each stripped. Lines before the first header are skipped."""
    blocks: dict[int, list[str]] = {}
    current: int | None = None
    for line in text.split("\n"):
        stripped = line.strip()
        header = _HEADER.fullmatch(stripped)
        if header:
            current = int(header.group(1))
            if current in blocks:
                raise ValueError(f"item {current} appears twice")
            blocks[current] = []
        elif stripped and current is not None:
            blocks[current].append(stripped)
    return blocks


def question_parts(n: int, question: str) -> tuple[str, str]:
    """(subject, effect) of Ngo's question for item n."""
    m = _QUESTION.fullmatch(question)
    if m:
        return m.group(1), m.group(2)
    subject = NO_INTENT_SUBJECT.get(n)
    if subject is not None:
        prefix = f"Did {subject} "
        if question.startswith(prefix) and question.endswith("?"):
            return subject, question[len(prefix):-1]
    raise ValueError(f"item {n}: cannot parse the question {question!r}")


def _capitalised(text: str) -> str:
    return text[:1].upper() + text[1:]


def parse_items(text: str) -> list[Item]:
    """All 80 vignettes as ngo_verbatim items, review_status draft."""
    blocks = read_blocks(text)
    if sorted(blocks) != list(range(1, N_ITEMS + 1)):
        raise ValueError(f"expected items 1..{N_ITEMS}, found {sorted(blocks)}")
    items = []
    for n, lines in sorted(blocks.items()):
        if len(lines) != 4 or not lines[3].startswith("Did "):
            raise ValueError(f"item {n}: expected three scenario lines and a question, got {lines!r}")
        subject, effect = question_parts(n, lines[3])
        agent = AGENT_OVERRIDES.get(n, subject)
        if not lines[0].startswith(_capitalised(agent) + " "):
            raise ValueError(f"item {n}: the scenario does not open with the agent {agent!r}: {lines[0]!r}; "
                             f"add the scenario's name to AGENT_OVERRIDES")
        storyline, sign = (n + 1) // 2, ("bad" if n % 2 else "good")
        items.append(Item(
            item_id=make_item_id("ngo_verbatim", storyline, "moral", sign),
            experiment="ngo_verbatim", storyline_id=storyline, arm="moral", sign=sign,
            agent=agent, effect=effect, scenario=" ".join(lines[:3]),
            source="ngo", review_status="draft",
        ))
    return items


def load_source(path: str | Path = SOURCE) -> list[Item]:
    return parse_items(Path(path).read_text(encoding="utf-8"))


def differences(items: list[Item], parsed: list[Item]) -> list[str]:
    """How items differ from the parsed source, ignoring review_status. Empty = identical (B9)."""
    have = {i.item_id: i for i in items}
    want = {i.item_id: i for i in parsed}
    problems = [f"{k}: in Ngo's source but missing from the file (B9)" for k in sorted(want.keys() - have.keys())]
    problems += [f"{k}: not in Ngo's source (B9)" for k in sorted(have.keys() - want.keys())]
    for k in sorted(want.keys() & have.keys()):
        for field in TEXT_FIELDS:
            got, expected = getattr(have[k], field), getattr(want[k], field)
            if got != expected:
                problems.append(f"{k}: {field} is {got!r}, Ngo's source gives {expected!r} (B9)")
    return problems


def changed_ids(items: list[Item], parsed: list[Item]) -> set[str]:
    """IDs of parsed items that are missing from items or differ in a text field."""
    have = {i.item_id: i for i in items}
    return {i.item_id for i in parsed if i.item_id not in have
            or any(getattr(have[i.item_id], f) != getattr(i, f) for f in TEXT_FIELDS)}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Ngo et al. (2015)'s 80 vignettes -> stimuli/ngo_verbatim.csv")
    p.add_argument("--source", type=Path, default=SOURCE)
    p.add_argument("--out", type=Path, default=OUT)
    p.add_argument("--update", action="store_true",
                   help="rewrite an existing file from the source; changed items are reset to draft")
    args = p.parse_args(argv)
    parsed = load_source(args.source)
    problems = design_problems(parsed)
    if problems:
        print("parsed items fail the design checks:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 1
    if args.out.exists():
        current = load_items(args.out)
        diffs = differences(current, parsed)
        if diffs and args.update:
            changed = changed_ids(current, parsed)
            status = {i.item_id: i.review_status for i in current}
            write_items([i if i.item_id in changed else i.model_copy(update={"review_status": status[i.item_id]})
                         for i in parsed], args.out)
            print(f"updated {args.out}: {len(changed)} item(s) changed and reset to draft: {sorted(changed)}")
            return 0
        if diffs:
            print(f"{args.out} differs from {args.source}; not overwriting it (it holds the review statuses; "
                  f"--update rewrites it and resets changed items to draft):\n  "
                  + "\n  ".join(diffs), file=sys.stderr)
            return 1
        print(f"{args.out} matches {args.source} ({len(parsed)} items)")
        return 0
    write_items(parsed, args.out)
    print(f"wrote {len(parsed)} items to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
