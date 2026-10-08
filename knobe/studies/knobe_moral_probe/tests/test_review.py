"""tools.review: review sheets for the drafting agent, decisions applied by the researcher."""
import csv

from kmp.items import load_items, write_items
from tools import ngo_source, review
from tools.review_record import DECISION_FIELDS, approval_problems, decision_files, read_decisions, text_sha256

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


def _record_ok(tmp_path, items_path):
    rows = read_decisions(decision_files(tmp_path / "review"))
    return approval_problems(load_items(items_path), rows) == []


def _apply_args(path, decisions):
    return ["apply", "--items", str(path), "--decisions", str(decisions), "--review-dir", str(decisions.parent)]


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
    assert review.main(["apply", "--items", str(path), "--decisions", str(decisions),
                        "--review-dir", str(decisions.parent)]) == 0
    statuses = {i.item_id: i.review_status for i in load_items(path)}
    assert _record_ok(tmp_path, path)
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
    assert review.main(["apply", "--items", str(path), "--decisions", str(decisions),
                        "--review-dir", str(decisions.parent)]) == 2   # blank decisions
    _fill(decisions, decision="rejected")                                                     # no note
    assert review.main(["apply", "--items", str(path), "--decisions", str(decisions),
                        "--review-dir", str(decisions.parent)]) == 2
    assert "needs a note" in capsys.readouterr().err
    edited = [i.model_copy(update={"effect": "lose the clerk's savings"}) if i.sign == "bad" else i for i in pair()]
    write_items(edited, path)
    _fill(decisions, decision="approved")
    assert review.main(["apply", "--items", str(path), "--decisions", str(decisions),
                        "--review-dir", str(decisions.parent)]) == 2
    assert "changed since the sheet was made" in capsys.readouterr().err
    assert {i.review_status for i in load_items(path)} == {"draft"}


def test_revise_keeps_the_item_a_draft():
    item = pair()[0]
    row = {"item_id": item.item_id, "text_sha256": text_sha256(item), "decision": "revise", "reviewer": "MM",
           "date": "2026-10-02", "note": "B4: bigger"}
    updated, problems = review.apply_decisions([item], [row])
    assert problems == [] and updated[0].review_status == "draft"


def test_apply_accepts_bom_and_padded_cells(tmp_path):
    path, sheet_args = _setup(tmp_path, pair())
    assert review.main([*sheet_args, "--batch", "01_test"]) == 0
    decisions = tmp_path / "review" / "01_test_decisions.csv"
    _fill(decisions, note="  ")
    text = decisions.read_text(encoding="utf-8").replace(",approved,MM,", ", approved , MM ,")
    decisions.write_text(text, encoding="utf-8-sig")
    assert review.main(_apply_args(path, decisions)) == 0
    assert {i.review_status for i in load_items(path)} == {"approved"}
    assert _record_ok(tmp_path, path)


def test_apply_refuses_duplicate_rows(tmp_path, capsys):
    path, sheet_args = _setup(tmp_path, pair())
    assert review.main([*sheet_args, "--batch", "01_test"]) == 0
    decisions = tmp_path / "review" / "01_test_decisions.csv"
    _fill(decisions)
    lines = decisions.read_text(encoding="utf-8").splitlines()
    decisions.write_text("\n".join([*lines, lines[1]]) + "\n", encoding="utf-8")
    assert review.main(_apply_args(path, decisions)) == 2
    assert "duplicate" in capsys.readouterr().err
    assert {i.review_status for i in load_items(path)} == {"draft"}


def test_apply_refuses_file_outside_review_dir_and_bad_name(tmp_path, capsys):
    path, sheet_args = _setup(tmp_path, pair())
    assert review.main([*sheet_args, "--batch", "01_test"]) == 0
    decisions = tmp_path / "review" / "01_test_decisions.csv"
    _fill(decisions)
    outside = tmp_path / "01_test_decisions.csv"
    outside.write_text(decisions.read_text(encoding="utf-8"), encoding="utf-8")
    args = ["apply", "--items", str(path), "--decisions", str(outside), "--review-dir", str(tmp_path / "review")]
    assert review.main(args) == 2
    badname = tmp_path / "review" / "mine.csv"
    badname.write_text(decisions.read_text(encoding="utf-8"), encoding="utf-8")
    assert review.main(_apply_args(path, badname)) == 2
    assert {i.review_status for i in load_items(path)} == {"draft"}


def test_apply_refuses_an_older_file_after_a_newer_one(tmp_path, capsys):
    path, sheet_args = _setup(tmp_path, pair())
    assert review.main([*sheet_args, "--batch", "01_test"]) == 0
    old = tmp_path / "review" / "01_test_decisions.csv"
    _fill(old, decision="approved")
    new = tmp_path / "review" / "02_test_decisions.csv"
    new.write_text(old.read_text(encoding="utf-8"), encoding="utf-8")
    _fill(new, decision="rejected", note="B4: no")
    assert review.main(_apply_args(path, new)) == 0
    assert review.main(_apply_args(path, old)) == 2
    assert {i.review_status for i in load_items(path)} == {"rejected"}
    assert _record_ok(tmp_path, path)


def test_bad_batch_names_and_existing_sheet_are_refused(tmp_path, capsys):
    path, sheet_args = _setup(tmp_path, pair())
    for bad in ("../x", "a/b", "test"):
        assert review.main([*sheet_args, "--batch", bad]) == 2
    assert list((tmp_path / "review").iterdir()) == []
    (tmp_path / "review" / "01_test.md").write_text("x", encoding="utf-8")
    assert review.main([*sheet_args, "--batch", "01_test"]) == 2
    assert not (tmp_path / "review" / "01_test_decisions.csv").exists()
