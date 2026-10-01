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


GOOD_ROW = "kmp-nm-007-prudential-bad,nonmoral,007,prudential,bad,Bill,ruin his savings,Bill did X.,new,draft,"                     # empty scaffold cell


def test_load_items_zero_padded_id_from_csv(tmp_path):
    _write_csv(tmp_path / "i.csv", GOOD_ROW)
    assert load_items(tmp_path / "i.csv")[0].storyline_id == 7


def test_load_items_names_line_of_invalid_row(tmp_path):
    _write_csv(tmp_path / "i.csv", GOOD_ROW, GOOD_ROW.replace("nonmoral,007", "nonmoral,0"))
    with pytest.raises(ValueError, match=r"line 3"):
        load_items(tmp_path / "i.csv")


def test_load_items_names_line_of_first_data_row(tmp_path):
    _write_csv(tmp_path / "i.csv", GOOD_ROW.replace("nonmoral,007", "nonmoral,0"))
    with pytest.raises(ValueError, match=r"line 2"):
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


# ---- scaffold (DEFINITIONS_AND_CHECKLIST.md section 7, decision A, option 1) ----

from conftest import make_ngo_verbatim_items, make_purpose_storyline  # noqa: E402


def _drop(items, *ids):
    return [i for i in items if i.item_id not in ids]


def test_scaffold_in_fields_and_defaults_to_none():
    assert "scaffold" in FIELDS
    assert _item().scaffold is None


def test_foundations_item_requires_scaffold(foundation_items):
    base = foundation_items[0].model_dump()
    with pytest.raises(ValidationError, match=f"{base['item_id']}.*scaffold"):
        Item(**{**base, "scaffold": None})
    with pytest.raises(ValidationError):
        Item(**{**base, "scaffold": "other"})


@pytest.mark.parametrize("value", ["shared", "purpose"])
def test_nonmoral_and_ngo_verbatim_reject_a_scaffold(value):
    with pytest.raises(ValidationError, match="kmp-nm-007-prudential-bad.*scaffold"):
        _item(scaffold=value)
    base = make_ngo_verbatim_items(1)[0].model_dump()
    with pytest.raises(ValidationError, match="kmp-nv-001-moral-bad.*scaffold"):
        Item(**{**base, "scaffold": value})


def test_csv_roundtrip_of_scaffold_values(tmp_path, nonmoral_items, foundation_items):
    items = nonmoral_items[:2] + foundation_items + make_purpose_storyline(9)
    path = tmp_path / "items.csv"
    write_items(items, path)
    loaded = load_items(path)
    assert loaded == sorted(items, key=lambda i: i.item_id)
    assert {i.scaffold for i in loaded} == {None, "shared", "purpose"}
    nm_line = next(line for line in path.read_text().splitlines() if line.startswith("kmp-nm-001-moral-bad"))
    assert nm_line.endswith(",")                                   # None is an empty cell


def test_load_items_empty_scaffold_cell_is_none_and_value_is_kept(tmp_path):
    row = "kmp-mf-003-purity-bad,foundations,3,purity,bad,the cook,spoil the shrine,The cook did X.,new,draft"
    _write_csv(tmp_path / "i.csv", GOOD_ROW, row + ",purpose")
    nm, mf = load_items(tmp_path / "i.csv")
    assert nm.scaffold is None and mf.scaffold == "purpose"
    _write_csv(tmp_path / "j.csv", row + ",")
    with pytest.raises(ValueError, match="(?s)line 2.*scaffold"):
        load_items(tmp_path / "j.csv")


def test_shared_and_purpose_storylines_are_clean(foundation_items):
    assert design_problems(foundation_items + make_purpose_storyline(9)) == []
    assert design_problems(make_purpose_storyline(9, arms=("purity", "fairness"))) == []


def test_storyline_with_mixed_scaffolds_is_a_problem(foundation_items):
    items = [i.model_copy(update={"scaffold": "purpose"}) if i.item_id == "kmp-mf-001-purity-bad" else i
             for i in foundation_items]
    assert any("storyline 1" in p and "mixed scaffold" in p for p in design_problems(items))


def test_shared_storyline_needs_a_harm_pair(foundation_items):
    s1 = [i for i in foundation_items if i.storyline_id == 1]
    no_harm = [i for i in s1 if i.arm != "harm"]
    assert any("storyline 1" in p and "harm pair" in p for p in design_problems(no_harm))
    half_harm = _drop(s1, "kmp-mf-001-harm-good")
    assert any("storyline 1" in p and "harm pair" in p for p in design_problems(half_harm))


def test_shared_storyline_needs_a_non_harm_pair(foundation_items):
    harm_only = [i for i in foundation_items if i.storyline_id == 1 and i.arm == "harm"]
    assert any("storyline 1" in p and "non-harm" in p for p in design_problems(harm_only))


def test_purpose_storyline_must_not_have_a_harm_pair(foundation_items):
    harm = [i.model_copy(update={"scaffold": "purpose", "storyline_id": 9,
                                 "item_id": i.item_id.replace("-001-", "-009-")})
            for i in foundation_items if i.storyline_id == 1 and i.arm == "harm"]
    problems = design_problems(make_purpose_storyline(9) + harm)
    assert any("storyline 9" in p and "purpose" in p and "harm" in p for p in problems)


def test_scaffold_rules_do_not_touch_other_experiments(nonmoral_items):
    assert design_problems(nonmoral_items) == []
    assert design_problems(make_ngo_verbatim_items(2)) == []
