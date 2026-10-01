import pytest
from pydantic import ValidationError

from conftest import make_items
from kmp.items import FIELDS, Item, design_problems, load_items, make_item_id, write_items


def _item(**over):
    base = dict(item_id="kmp-nm-007-prudential-bad", experiment="nonmoral", storyline_id=7,
                arm="prudential", sign="bad", agent="Bill", effect="ruin his own savings",
                scenario="Bill did X.", source="new")
    base.update(over)
    return Item(**base)


def test_make_item_id():
    assert make_item_id("nonmoral", 7, "prudential", "bad") == "kmp-nm-007-prudential-bad"
    assert make_item_id("foundations", 12, "purity", "good") == "kmp-mf-012-purity-good"


def test_item_default_status_is_draft():
    assert _item().review_status == "draft"


def test_item_rejects_wrong_id():
    with pytest.raises(ValidationError, match="should be"):
        _item(item_id="moral-07-bad")


def test_item_rejects_arm_outside_experiment():
    with pytest.raises(ValidationError, match="not in"):
        _item(arm="loyalty", item_id="kmp-nm-007-loyalty-bad")


def test_item_rejects_blank_or_padded_text():
    with pytest.raises(ValidationError, match="whitespace"):
        _item(effect=" ruin his own savings")


def test_csv_roundtrip(tmp_path, nonmoral_items):
    tricky = nonmoral_items[0].model_copy(update={"scenario": 'He said, "go"\nthen left, quietly.'})
    items = [tricky] + nonmoral_items[1:]
    path = tmp_path / "items.csv"
    write_items(items, path)
    assert load_items(path) == sorted(items, key=lambda i: i.item_id)


@pytest.mark.parametrize("bad", [-1, 0, 1000, True])
def test_item_rejects_bad_storyline_id(bad):
    with pytest.raises(ValidationError):
        _item(storyline_id=bad, item_id=make_item_id("nonmoral", bad, "prudential", "bad"))


def test_item_accepts_zero_padded_storyline_id_string():
    assert _item(storyline_id="007").storyline_id == 7


def _write_csv(path, *rows):
    header = ",".join(FIELDS)
    path.write_text("\n".join([header, *rows]) + "\n", encoding="utf-8")


GOOD_ROW = "kmp-nm-007-prudential-bad,nonmoral,007,prudential,bad,Bill,ruin his savings,Bill did X.,new,draft"


def test_load_items_zero_padded_id_from_csv(tmp_path):
    _write_csv(tmp_path / "i.csv", GOOD_ROW)
    assert load_items(tmp_path / "i.csv")[0].storyline_id == 7


def test_load_items_names_line_of_invalid_row(tmp_path):
    _write_csv(tmp_path / "i.csv", GOOD_ROW, GOOD_ROW.replace("nonmoral,007", "nonmoral,0"))
    with pytest.raises(ValueError, match=r"line 3"):
        load_items(tmp_path / "i.csv")


def test_load_items_names_line_of_ragged_row(tmp_path):
    _write_csv(tmp_path / "i.csv", GOOD_ROW, GOOD_ROW + ",extra")
    with pytest.raises(ValueError, match=r"line 3.*more cells"):
        load_items(tmp_path / "i.csv")


def test_load_items_empty_file_is_valid(tmp_path):
    _write_csv(tmp_path / "i.csv")
    assert load_items(tmp_path / "i.csv") == []


def test_design_problems_clean(nonmoral_items, foundation_items):
    assert design_problems(nonmoral_items) == []
    assert design_problems(foundation_items) == []


def test_design_problems_missing_partner(nonmoral_items):
    problems = design_problems([i for i in nonmoral_items if i.item_id != "kmp-nm-001-moral-good"])
    assert any("(1, 'moral')" in p and "needs exactly one bad and one good" in p for p in problems)


def test_design_problems_agent_mismatch(nonmoral_items):
    items = [i.model_copy(update={"agent": "Someone"}) if i.item_id == "kmp-nm-001-moral-good" else i
             for i in nonmoral_items]
    assert any("agents differ" in p for p in design_problems(items))


def test_design_problems_duplicate_and_mixed(nonmoral_items):
    mixed = nonmoral_items + [nonmoral_items[0]] + make_items("foundations", 1)
    problems = design_problems(mixed)
    assert any("duplicate item_id" in p for p in problems)
    assert any("mixed experiments" in p for p in problems)


def _ngo_pair(source="ngo", good_source=None):
    bad = _item(item_id="kmp-nm-001-moral-bad", storyline_id=1, arm="moral", sign="bad",
                agent="Bill", source=source)
    good = _item(item_id="kmp-nm-001-moral-good", storyline_id=1, arm="moral", sign="good",
                 agent="Robyn", source=good_source or source)
    return bad, good


def test_design_problems_ngo_pair_exempt_from_same_agent():
    assert design_problems(list(_ngo_pair())) == []


def test_design_problems_non_ngo_pair_still_needs_same_agent():
    assert any("agents differ" in p for p in design_problems(list(_ngo_pair(source="new"))))


def test_design_problems_mixed_source_pair_still_needs_same_agent():
    assert any("agents differ" in p for p in design_problems(list(_ngo_pair(good_source="new"))))


def test_design_problems_ngo_pair_missing_partner_still_reported():
    problems = design_problems([_ngo_pair()[0]])
    assert any("needs exactly one bad and one good" in p for p in problems)
