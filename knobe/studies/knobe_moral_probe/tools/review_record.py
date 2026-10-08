"""The review record: which exact text the researcher approved or rejected
(DESIGN.md section 3.4 step 2; DEFINITIONS_AND_CHECKLIST.md section 1).

A decisions file (stimuli/review/NN_<batch>_decisions.csv) has one row per
reviewed item. text_sha256 is the hash of every item field except
review_status, so a decision belongs to the exact text it was made on: edit
the text and the decision no longer applies. Files are read in name order
(NN = batch number), and an item's last row is its current decision.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from kmp.items import Item

DECISION_FIELDS = ["item_id", "text_sha256", "decision", "reviewer", "date", "note"]
DECISIONS = ("approved", "rejected", "revise")
REVIEW_DIR = Path(__file__).resolve().parents[1] / "stimuli" / "review"


def text_sha256(item: Item) -> str:
    fields = {k: v for k, v in item.model_dump().items() if k != "review_status"}
    return hashlib.sha256(json.dumps(fields, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def decision_files(review_dir: str | Path = REVIEW_DIR) -> list[Path]:
    return sorted(Path(review_dir).glob("*_decisions.csv"))


def read_decisions(paths: list[Path]) -> list[dict[str, str]]:
    """Filled-in rows of the given decisions files, in order. Rows with an empty decision are skipped."""
    rows = []
    for path in paths:
        with open(path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            if reader.fieldnames != DECISION_FIELDS:
                raise ValueError(f"{path}: header {reader.fieldnames} should be {DECISION_FIELDS}")
            rows += [{**row, "file": str(path)} for row in reader if row["decision"].strip()]
    return rows


def approval_problems(items: list[Item], rows: list[dict[str, str]]) -> list[str]:
    """Approved or rejected items whose status is not backed by a decision on their current text."""
    last = {row["item_id"]: row for row in rows}
    problems = []
    for item in sorted(items, key=lambda i: i.item_id):
        if item.review_status == "draft":
            continue
        row = last.get(item.item_id)
        if row is None:
            problems.append(f"{item.item_id}: {item.review_status} but no review decision is on file")
        elif row["decision"] != item.review_status:
            problems.append(f"{item.item_id}: {item.review_status} but the last decision ({row['file']}) "
                            f"is {row['decision']}")
        elif row["text_sha256"] != text_sha256(item):
            problems.append(f"{item.item_id}: text changed after it was {item.review_status}; "
                            f"set it back to draft and send it for review again")
    return problems
