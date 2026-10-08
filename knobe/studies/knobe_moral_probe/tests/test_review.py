"""tools.review: review sheets for the drafting agent, decisions applied by the researcher."""
import csv

from kmp.items import load_items, write_items
from tools import ngo_source, review
from tools.review_record import DECISION_FIELDS, text_sha256

from test_lint_stimuli import pair


def _fill(path, decision="approved", note=""):
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for row in rows:
        row.update(decision=decision, reviewer="MM", date="2026-10-02", note=note)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=DECISION_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _setup(tmp_path, items):
    path = tmp_path / "nonmoral.csv"
    write_items(items, path)
    (tmp_path / "review").mkdir()
    common = ["--items", str(path)]
    sheet_args = ["sheet", *common, "--review-dir", str(tmp_path / "review"),
                  "--log", str(tmp_path / "none.csv"), "--verbatim", str(tmp_path / "none.csv")]
    return path, sheet_args


def test_checks_follow_the_checklist_applicability():
    assert review.PAIR_CHECKS["ngo_verbatim"] == ["A1", "A10", "A13", "B9"]
    assert "B8" in review.PAIR_CHECKS["ngo_adapted"] and "B2" not in review.PAIR_CHECKS["ngo_adapted"]
    assert "B8" not in review.PAIR_CHECKS["new"] and "A13" in review.PAIR_CHECKS["new"]


def test_name_candidates_flag_mid_sentence_capitals():
    item = ngo_source.load_source()[8]   # item 9: "The mayor diverted water to Oldtown ..."
    assert review.name_candidates(item) == ["Newtown", "Oldtown"]
    assert review.name_candidates(pair()[0]) == []


def test_parse_range():
    assert review.parse_range("1-3,7") == {1, 2, 3, 7}


def test_sheet_then_apply_round_trip(tmp_path, capsys):
    path, sheet_args = _setup(tmp_path, pair() + pair(arm="procedural"))
    assert review.main([*sheet_args, "--batch", "01_test", "--arms", "prudential"]) == 0
    sheet = (tmp_path / "review" / "01_test.md").read_text(encoding="utf-8")
    assert "## Storyline 1: the clerk" in sheet and "### prudential" in sheet and "procedural" not in sheet
    assert "B2 B3 B4 B5 B6 B7" in sheet
    decisions = tmp_path / "review" / "01_test_decisions.csv"
    _fill(decisions)
    assert review.main(["apply", "--items", str(path), "--decisions", str(decisions)]) == 0
    statuses = {i.item_id: i.review_status for i in load_items(path)}
    assert statuses == {"kmp-nm-001-prudential-bad": "approved", "kmp-nm-001-prudential-good": "approved",
                        "kmp-nm-001-procedural-bad": "draft", "kmp-nm-001-procedural-good": "draft"}
    # The approved items now leave the next sheet, and their approvals pass lint.
    assert review.main([*sheet_args, "--batch", "02_test"]) == 0
    assert "prudential" not in (tmp_path / "review" / "02_test.md").read_text(encoding="utf-8")


def test_sheet_refuses_an_existing_batch_and_unclean_files(tmp_path, capsys):
    path, sheet_args = _setup(tmp_path, pair())
    assert review.main([*sheet_args, "--batch", "01_test"]) == 0
    assert review.main([*sheet_args, "--batch", "01_test"]) == 2
    write_items(pair() + pair(sid=2), path)                       # D3 problem
    assert review.main([*sheet_args, "--batch", "02_test"]) == 1
    assert not (tmp_path / "review" / "02_test.md").exists()


def test_apply_refuses_incomplete_rows_and_changed_text(tmp_path, capsys):
    path, sheet_args = _setup(tmp_path, pair())
    assert review.main([*sheet_args, "--batch", "01_test"]) == 0
    decisions = tmp_path / "review" / "01_test_decisions.csv"
    assert review.main(["apply", "--items", str(path), "--decisions", str(decisions)]) == 2   # blank decisions
    _fill(decisions, decision="rejected")                                                     # no note
    assert review.main(["apply", "--items", str(path), "--decisions", str(decisions)]) == 2
    assert "needs a note" in capsys.readouterr().err
    edited = [i.model_copy(update={"effect": "lose the clerk's savings"}) if i.sign == "bad" else i for i in pair()]
    write_items(edited, path)
    _fill(decisions, decision="approved")
    assert review.main(["apply", "--items", str(path), "--decisions", str(decisions)]) == 2
    assert "changed since the sheet was made" in capsys.readouterr().err
    assert {i.review_status for i in load_items(path)} == {"draft"}


def test_revise_keeps_the_item_a_draft():
    item = pair()[0]
    row = {"item_id": item.item_id, "text_sha256": text_sha256(item), "decision": "revise", "reviewer": "MM",
           "date": "2026-10-02", "note": "B4: bigger"}
    updated, problems = review.apply_decisions([item], [row])
    assert problems == [] and updated[0].review_status == "draft"
