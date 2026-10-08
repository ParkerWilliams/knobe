"""tools.review_record: decisions are tied to the exact text reviewed."""
import csv

import pytest

from conftest import make_items
from kmp.items import FIELDS, Item
from tools.review_record import (DECISION_FIELDS, HASHED_FIELDS, approval_problems, read_decisions,
                                 text_sha256)


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


def _csv(tmp_path, body, name="01_x_decisions.csv", encoding="utf-8"):
    path = tmp_path / name
    path.write_text(",".join(DECISION_FIELDS) + "\n" + body, encoding=encoding)
    return path


def test_hashed_fields_track_item_fields_by_conscious_choice():
    assert set(HASHED_FIELDS) == set(FIELDS) - {"review_status"}


def test_golden_digest_is_stable():
    item = Item(item_id="kmp-nm-001-moral-bad", experiment="nonmoral", storyline_id=1, arm="moral",
                sign="bad", agent="Ann", effect="spill the paint",
                scenario="Ann wanted to finish the room.", source="new",
                review_status="draft", scaffold=None)
    assert text_sha256(item) == "114b41f4e5f82b640a6a6106613262cab162f4e19739e54b41a3be887c073d11"


def test_bom_file_reads(tmp_path):
    path = _csv(tmp_path, "a,h,approved,MM,2026-10-02,\n", encoding="utf-8-sig")
    assert [r["decision"] for r in read_decisions([path])] == ["approved"]


def test_cells_are_stripped(tmp_path):
    path = _csv(tmp_path, "a,h, approved , MM ,2026-10-02,\n")
    row = read_decisions([path])[0]
    assert row["decision"] == "approved" and row["reviewer"] == "MM"


@pytest.mark.parametrize("body,msg", [
    ("a,h,approve,MM,2026-10-02,\n", "not one of"),
    ("a,h,approved,,2026-10-02,\n", "reviewer is empty"),
    ("a,h,approved\n", "too few"),
    ("a,h,approved,MM,2026-10-02,,extra\n", "too many"),
])
def test_bad_rows_raise_with_file_and_line(tmp_path, body, msg):
    path = _csv(tmp_path, body)
    with pytest.raises(ValueError, match=msg) as exc:
        read_decisions([path])
    assert "01_x_decisions.csv line 2" in str(exc.value)


def test_rejected_item_backed_by_rejected_decision_is_clean():
    item = make_items("nonmoral", 1, status="rejected")[0]
    assert approval_problems([item], [_row(item, "rejected", file="f")]) == []
