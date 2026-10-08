"""Review sheets and review decisions (DESIGN.md section 3.4 step 2;
DEFINITIONS_AND_CHECKLIST.md sections 1 and 6).

  sheet  (run by the drafting agent) writes a markdown review sheet for one
         batch of draft items, grouped by storyline, with the checklist IDs
         that apply to each pair, any authoring-log rows, Ngo's
         original text for adapted Ngo items, and capitalised words that may
         be personal names (R1). Next to it, a decisions template: one row
         per item with its text_sha256 and the decision columns empty.
         Refuses (writes nothing) unless design_problems and lint are clean.
  apply  (run by the researcher only) reads filled-in decisions and sets
         review_status: approved, rejected, or draft for "revise". It
         refuses the whole file if any row is incomplete or if an item's
         text changed since the sheet was made. The drafting agent never
         runs apply and never edits review_status.

Run from the study folder:
    ../../.venv/bin/python -m tools.review sheet --items stimuli/nonmoral.csv --batch 02_nm_moral_01-20 --arms moral --storylines 1-20
    ../../.venv/bin/python -m tools.review apply --items stimuli/nonmoral.csv --decisions stimuli/review/02_nm_moral_01-20_decisions.csv
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

from kmp.items import Item, design_problems, load_items, write_items
from tools import lint_stimuli
from tools.review_record import (DECISION_FIELDS, DECISIONS, REVIEW_DIR, approval_problems, decision_files,
                                 read_decisions, text_sha256)

_A = [f"A{i}" for i in range(1, 14)]
_R = ["R1", "R2", "R3", "R4"]
PAIR_CHECKS = {   # DEFINITIONS_AND_CHECKLIST.md section 6, "Which checks apply"
    "ngo_verbatim": ["A1", "A10", "A13", "B9"],
    "ngo_adapted": ["A1", "A9", "A10", "A13", *_R, "B1", "B8"],
    "new": [*_A, *_R, "B1", "B2", "B3", "B4", "B5", "B6", "B7"],
}
STORYLINE_CHECKS = {"ngo_verbatim": ["C1"], "nonmoral": ["C1", "C2", "C3"],
                    "shared": ["C2", "C4", "C5", "C6"], "purpose": ["C2", "C7"]}


def pair_kind(item: Item) -> str:
    if item.experiment == "ngo_verbatim":
        return "ngo_verbatim"
    return "ngo_adapted" if lint_stimuli.is_adapted_ngo(item) else "new"


def storyline_kind(item: Item) -> str:
    return item.scaffold if item.experiment == "foundations" else item.experiment


def name_candidates(item: Item) -> list[str]:
    """Capitalised words that do not open a sentence and are not the agent: possible names (R1)."""
    agent_words = {w for word in item.agent.split() for w in (word, word.capitalize())}
    words = [w for s in lint_stimuli.split_sentences(item.scenario) for w in s.split()[1:]] + item.effect.split()
    stripped = (w.strip(".,;:!?\"()") for w in words)
    return sorted({w for w in stripped if w[:1].isupper() and w not in agent_words})


def parse_range(text: str) -> set[int]:
    """'1-20,25' -> {1..20, 25}."""
    out: set[int] = set()
    for part in text.split(","):
        lo, _, hi = part.partition("-")
        out |= set(range(int(lo), int(hi or lo) + 1))
    return out


def select(items: list[Item], storylines: set[int] | None, arms: set[str] | None) -> list[Item]:
    """Draft items in the batch."""
    return [i for i in items if i.review_status == "draft"
            and (storylines is None or i.storyline_id in storylines) and (arms is None or i.arm in arms)]


def render_sheet(batch: str, selected: list[Item], log_rows: list[dict[str, str]],
                 originals: dict[str, Item], items_path: str) -> str:
    log_by_item: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in log_rows:
        log_by_item[row["item_id"]].append(row)
    lines = [f"# Review sheet: {batch}", "",
             f"Items: `{items_path}`, {len(selected)} draft items. Checklist: "
             f"`docs/DEFINITIONS_AND_CHECKLIST.md` section 6.", "",
             f"Record one decision per item in `stimuli/review/{batch}_decisions.csv`: `approved`, `rejected` or "
             f"`revise`, your initials as reviewer, the date (YYYY-MM-DD), and a note for every rejected or "
             f"revise row naming the failed check (e.g. \"B4: good version is bigger\"). Then run "
             f"`../../.venv/bin/python -m tools.review apply --items {items_path} --decisions "
             f"stimuli/review/{batch}_decisions.csv` yourself.", "",
             "Automated checks (design_problems and tools.lint_stimuli) were clean when this sheet was made.", ""]
    by_storyline: dict[int, list[Item]] = defaultdict(list)
    for item in selected:
        by_storyline[item.storyline_id].append(item)
    for sid, members in sorted(by_storyline.items()):
        kind = storyline_kind(members[0])
        lines += [f"## Storyline {sid}: {members[0].agent} ({kind}; storyline checks "
                  f"{' '.join(STORYLINE_CHECKS[kind])})", ""]
        arms: dict[str, list[Item]] = defaultdict(list)
        for m in members:
            arms[m.arm].append(m)
        for arm, versions in sorted(arms.items()):
            kind = pair_kind(versions[0])
            lines += [f"### {arm} (source {versions[0].source}; checks {' '.join(PAIR_CHECKS[kind])})", ""]
            for item in sorted(versions, key=lambda i: i.sign):
                lines += [f"**{item.sign}** `{item.item_id}`", "", f"> {item.scenario}", "",
                          f"- agent: `{item.agent}`", f"- effect: `{item.effect}`"]
                if item.item_id in originals:
                    lines += [f"- Ngo's original: {originals[item.item_id].scenario}",
                              f"- Ngo's effect: `{originals[item.item_id].effect}`"]
                lines += [f"- log ({r['kind']}, {r['field']}): {r['from']!r} -> {r['to']!r}. {r['note']}"
                          for r in log_by_item[item.item_id]]
                names = name_candidates(item)
                if names:
                    lines.append(f"- capitalised words (R1: names?): {', '.join(names)}")
                lines.append("")
    return "\n".join(lines) + "\n"


def write_template(selected: list[Item], path: Path) -> None:
    if path.exists():
        raise FileExistsError(f"{path} exists; it may hold decisions. Use a new batch name.")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=DECISION_FIELDS)
        writer.writeheader()
        for item in sorted(selected, key=lambda i: i.item_id):
            writer.writerow({"item_id": item.item_id, "text_sha256": text_sha256(item)})


def apply_decisions(items: list[Item], rows: list[dict[str, str]]) -> tuple[list[Item], list[str]]:
    """(updated items, problems). If problems is non-empty, nothing should be written."""
    by_id = {i.item_id: i for i in items}
    updated, problems = dict(by_id), []
    for n, row in enumerate(rows, start=2):
        where = f"{row.get('file', 'decisions')} line {n}"
        item = by_id.get(row["item_id"])
        if item is None:
            problems.append(f"{where}: unknown item {row['item_id']!r}")
            continue
        if row["decision"] not in DECISIONS:
            problems.append(f"{where}: decision {row['decision']!r} not in {DECISIONS}")
            continue
        if not row["reviewer"].strip():
            problems.append(f"{where}: reviewer is empty")
        try:
            date.fromisoformat(row["date"])
        except ValueError:
            problems.append(f"{where}: date {row['date']!r} is not YYYY-MM-DD")
        if row["decision"] != "approved" and not row["note"].strip():
            problems.append(f"{where}: a {row['decision']} decision needs a note naming the failed check")
        if row["text_sha256"] != text_sha256(item):
            problems.append(f"{where}: {item.item_id} changed since the sheet was made; review it again")
        status = "draft" if row["decision"] == "revise" else row["decision"]
        updated[item.item_id] = item.model_copy(update={"review_status": status})
    return list(updated.values()), problems


BATCH_RE = re.compile(r"^\d{2}_[A-Za-z0-9_-]+$")
DECISIONS_NAME_RE = re.compile(r"^\d{2}_[A-Za-z0-9_-]+_decisions\.csv$")


def _listed_ids(path: Path) -> list[str]:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return [(row.get("item_id") or "").strip() for row in csv.DictReader(fh)]


def _apply(args, items: list[Item]) -> int:
    def refuse(msg: str) -> int:
        print(f"refusing; nothing written: {msg}", file=sys.stderr)
        return 2

    path, review_dir = args.decisions, args.review_dir
    if path.resolve().parent != review_dir.resolve():
        return refuse(f"{path} is not inside the review directory {review_dir}")
    if not DECISIONS_NAME_RE.match(path.name):
        return refuse(f"{path.name} does not look like NN_<batch>_decisions.csv")
    try:
        rows = read_decisions([path])
        record = read_decisions(decision_files(review_dir))
    except ValueError as exc:
        return refuse(str(exc))
    listed = _listed_ids(path)
    dupes = sorted({i for i in listed if listed.count(i) > 1})
    if dupes:
        return refuse(f"duplicate item_ids in {path.name}: {dupes}")
    filled = {r["item_id"] for r in rows}
    missing = [i for i in listed if i not in filled]
    if missing:
        return refuse(f"{len(missing)} row(s) have no decision: {missing}")
    updated, problems = apply_decisions(items, rows)
    if not problems:
        # The record as it stands, in file-name order, includes this file; a later filled file wins.
        problems += approval_problems(updated, record)
    if problems:
        return refuse("\n  " + "\n  ".join(problems))
    write_items(updated, args.items)
    counts = defaultdict(int)
    for r in rows:
        counts[r["decision"]] += 1
    print(f"applied {len(rows)} decisions to {args.items}: {dict(sorted(counts.items()))}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="review sheets and decisions for authored items")
    sub = p.add_subparsers(dest="command", required=True)
    s = sub.add_parser("sheet", help="write a review sheet and a decisions template (drafting agent)")
    s.add_argument("--items", required=True, type=Path)
    s.add_argument("--batch", required=True, help="NN_<name>, e.g. 02_nm_moral_01-20")
    s.add_argument("--storylines", help="e.g. 1-20 (default: all)")
    s.add_argument("--arms", help="comma-separated (default: all)")
    s.add_argument("--review-dir", type=Path, default=REVIEW_DIR)
    s.add_argument("--verbatim", type=Path, default=lint_stimuli.VERBATIM)
    s.add_argument("--log", type=Path, default=lint_stimuli.LOG)
    a = sub.add_parser("apply", help="apply filled-in decisions (researcher only)")
    a.add_argument("--items", required=True, type=Path)
    a.add_argument("--decisions", required=True, type=Path)
    a.add_argument("--review-dir", type=Path, default=REVIEW_DIR)
    args = p.parse_args(argv)
    items = load_items(args.items)

    if args.command == "apply":
        return _apply(args, items)

    if not BATCH_RE.match(args.batch):
        print(f"refusing: batch {args.batch!r} must look like NN_<name> (letters, digits, _ and -)", file=sys.stderr)
        return 2
    log_rows = lint_stimuli.read_log(args.log) if args.log.exists() else []
    verbatim = load_items(args.verbatim) if args.verbatim.exists() else None
    problems = design_problems(items, stage="authoring") + lint_stimuli.lint(
        items, log_rows=log_rows, verbatim=verbatim, decisions=read_decisions(decision_files(args.review_dir)))
    if problems:
        print(f"automated checks are not clean; no sheet written ({len(problems)} problem(s)):\n  "
              + "\n  ".join(problems), file=sys.stderr)
        return 1
    selected = select(items, parse_range(args.storylines) if args.storylines else None,
                      set(args.arms.split(",")) if args.arms else None)
    if not selected:
        print("no draft items match; nothing written", file=sys.stderr)
        return 2
    originals = {}
    if verbatim is not None:
        by_key = {(v.storyline_id, v.sign): v for v in verbatim}
        originals = {i.item_id: by_key[(i.storyline_id, i.sign)] for i in selected
                     if lint_stimuli.is_adapted_ngo(i) and (i.storyline_id, i.sign) in by_key}
    sheet = args.review_dir / f"{args.batch}.md"
    template = args.review_dir / f"{args.batch}_decisions.csv"
    text = render_sheet(args.batch, selected, log_rows, originals, str(args.items))
    for existing in (sheet, template):
        if existing.exists():
            print(f"refusing: {existing} exists; it may hold decisions. Use a new batch name.", file=sys.stderr)
            return 2
    write_template(selected, template)
    sheet.write_text(text, encoding="utf-8")
    print(f"wrote {sheet} and its decisions template ({len(selected)} items)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
