import pytest
from pydantic import ValidationError

from conftest import make_items
from kmp.items import FIELDS, Item, design_problems, load_items, make_item_id, write_items


def _item(**over):
    base = dict(item_id="kmp-nm-007-prudential-bad", experiment="nonmoral", storyline_id=7,
                arm="prudential", sign="bad", agent="Bill", effect="ruin the savings",
                scenario="The manager did X.", source="new")
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
        _item(effect=" ruin the savings")


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


def test_design_problems_ngo_pair_with_different_agents_is_reported():
    assert any("agents differ" in p for p in design_problems(list(_ngo_pair())))


def test_design_problems_ngo_pair_with_same_agent_is_clean():
    bad, good = _ngo_pair()
    assert design_problems([bad, good.model_copy(update={"agent": "Bill"})]) == []


def test_design_problems_ngo_pair_missing_partner_still_reported():
    problems = design_problems([_ngo_pair()[0]])
    assert any("needs exactly one bad and one good" in p for p in problems)


def _role_pair(**over_bad):
    bad = _item(item_id="kmp-nm-001-moral-bad", storyline_id=1, arm="moral", sign="bad",
                agent="the manager", effect="harm the environment",
                scenario="The manager started a project.", **over_bad)
    good = bad.model_copy(update={"item_id": "kmp-nm-001-moral-good", "sign": "good"})
    return bad, good


def test_design_problems_clean_role_noun_item_passes():
    assert design_problems(list(_role_pair())) == []


@pytest.mark.parametrize("word", ["he", "she", "him", "her", "his", "hers", "himself", "herself"])
@pytest.mark.parametrize("field", ["scenario", "agent", "effect"])
def test_design_problems_flags_gendered_pronoun(word, field):
    bad, good = _role_pair()
    bad = bad.model_copy(update={field: f"x {word.capitalize()} y"})
    good = good.model_copy(update={"agent": bad.agent})
    problems = design_problems([bad, good])
    assert any("gendered pronoun" in p and bad.item_id in p and word in p for p in problems)


def test_design_problems_pronoun_check_ignores_embedded_words():
    bad, good = _role_pair()
    text = "the there hero shelf history otherwise cheer"
    bad = bad.model_copy(update={"scenario": text})
    assert design_problems([bad, good]) == []
