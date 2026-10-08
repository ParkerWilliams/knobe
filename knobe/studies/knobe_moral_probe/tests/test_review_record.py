"""tools.review_record: decisions are tied to the exact text reviewed."""
import csv

import pytest

from conftest import make_items
from tools.review_record import DECISION_FIELDS, approval_problems, read_decisions, text_sha256


def _write(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=DECISION_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return path


def _row(item, decision, **kw):
    return {"item_id": item.item_id, "text_sha256": text_sha256(item), "decision": decision,
            "reviewer": "MM", "date": "2026-10-02", "note": "", **kw}


def test_hash_ignores_review_status_only():
    item = make_items("nonmoral", 1, status="draft")[0]
    assert text_sha256(item) == text_sha256(item.model_copy(update={"review_status": "approved"}))
    assert text_sha256(item) != text_sha256(item.model_copy(update={"effect": "something else"}))


def test_read_decisions_skips_blank_rows_and_checks_header(tmp_path):
    item = make_items("nonmoral", 1)[0]
    path = _write(tmp_path / "01_x_decisions.csv", [_row(item, "approved"), _row(item, "")])
    rows = read_decisions([path])
    assert [r["decision"] for r in rows] == ["approved"]
    (tmp_path / "02_bad_decisions.csv").write_text("item_id,decision\n", encoding="utf-8")
    with pytest.raises(ValueError, match="header"):
        read_decisions([tmp_path / "02_bad_decisions.csv"])


def test_approval_needs_a_matching_decision():
    items = make_items("nonmoral", 1, status="approved")[:2]
    assert approval_problems(items, [_row(i, "approved", file="f") for i in items]) == []
    assert "no review decision" in approval_problems(items, [_row(items[0], "approved", file="f")])[0]


def test_last_decision_wins_and_must_match_status():
    item = make_items("nonmoral", 1, status="approved")[0]
    rows = [_row(item, "approved", file="01"), _row(item, "revise", file="02")]
    assert "last decision (02) is revise" in approval_problems([item], rows)[0]


def test_text_edited_after_approval_is_flagged():
    item = make_items("nonmoral", 1, status="approved")[0]
    row = _row(item, "approved", file="f")
    edited = item.model_copy(update={"scenario": item.scenario + " Extra."})
    assert "text changed after it was approved" in approval_problems([edited], [row])[0]


def test_drafts_need_nothing():
    assert approval_problems(make_items("nonmoral", 1, status="draft"), []) == []
