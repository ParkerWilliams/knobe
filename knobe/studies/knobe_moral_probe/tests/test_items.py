import pytest
from pydantic import ValidationError

from conftest import make_items
from kmp.items import Item, design_problems, load_items, make_item_id, write_items


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
    path = tmp_path / "items.csv"
    write_items(nonmoral_items, path)
    assert sorted(load_items(path), key=lambda i: i.item_id) == sorted(nonmoral_items, key=lambda i: i.item_id)


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
