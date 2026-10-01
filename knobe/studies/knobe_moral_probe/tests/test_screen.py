import pytest
from conftest import make_items
from kmp import screen


def _get(items, arm, sign, sid=1):
    return next(i for i in items if i.arm == arm and i.sign == sign and i.storyline_id == sid)


NM_GOOD_SCORES = {"domain_moral": 2, "domain_prudential": 8, "domain_procedural": 1}


def test_valence_thresholds(nonmoral_items):
    bad, good = _get(nonmoral_items, "prudential", "bad"), _get(nonmoral_items, "prudential", "good")
    assert screen.item_failures(bad, {"valence": 2, **NM_GOOD_SCORES}) == []
    assert "valence 5 > 3 for a bad item" in screen.item_failures(bad, {"valence": 5, **NM_GOOD_SCORES})
    assert "valence 6 < 7 for a good item" in screen.item_failures(good, {"valence": 6, **NM_GOOD_SCORES})


def test_nonmoral_domain_must_be_high_and_highest(nonmoral_items):
    item = _get(nonmoral_items, "prudential", "bad")
    low = {"valence": 1, "domain_moral": 2, "domain_prudential": 5, "domain_procedural": 1}
    tie = {"valence": 1, "domain_moral": 8, "domain_prudential": 8, "domain_procedural": 1}
    assert "domain_prudential 5 < 6" in screen.item_failures(item, low)
    assert "domain_prudential is not the highest domain rating" in screen.item_failures(item, tie)


def test_foundation_must_beat_harm(foundation_items):
    item = _get(foundation_items, "loyalty", "bad")
    base = {"valence": 1, "fnd_fairness": 1, "fnd_authority": 1, "fnd_purity": 1}
    assert screen.item_failures(item, {**base, "fnd_loyalty": 8, "fnd_harm": 3}) == []
    assert "fnd_loyalty 7 not higher than fnd_harm 7" in screen.item_failures(item, {**base, "fnd_loyalty": 7, "fnd_harm": 7})


def test_harm_control_needs_harm(foundation_items):
    item = _get(foundation_items, "harm", "bad")
    assert "fnd_harm 4 < 6" in screen.item_failures(item, {"valence": 1, "fnd_harm": 4})


def test_unparsed_is_a_named_failure(nonmoral_items):
    item = _get(nonmoral_items, "moral", "bad")
    assert "valence unparsed" in screen.item_failures(item, {"valence": None, "domain_moral": 9,
                                                            "domain_prudential": 1, "domain_procedural": 1})


def test_select_pairs_drops_the_whole_pair(nonmoral_items):
    pair = [_get(nonmoral_items, "prudential", "bad"), _get(nonmoral_items, "prudential", "good")]
    scores = {pair[0].item_id: {"valence": 1, **NM_GOOD_SCORES},
              pair[1].item_id: {"valence": 4, **NM_GOOD_SCORES}}
    selected, report = screen.select_pairs(pair, scores)
    assert selected == []
    assert [r["pair_passed"] for r in report] == [False, False]
    assert report[1]["failures"] == "valence 4 < 7 for a good item"


def test_select_pairs_flags_missing_partner(nonmoral_items):
    selected, report = screen.select_pairs([_get(nonmoral_items, "moral", "bad")], {})
    assert selected == [] and "partner not approved" in report[0]["failures"]


def _nm(items, sign):
    return _get(items, "prudential", sign)


@pytest.mark.parametrize("v,ok", [(3, True), (4, False)])
def test_bad_valence_boundary(nonmoral_items, v, ok):
    f = screen.item_failures(_nm(nonmoral_items, "bad"), {"valence": v, **NM_GOOD_SCORES})
    assert (f == []) is ok


@pytest.mark.parametrize("v,ok", [(7, True), (6, False)])
def test_good_valence_boundary(nonmoral_items, v, ok):
    f = screen.item_failures(_nm(nonmoral_items, "good"), {"valence": v, **NM_GOOD_SCORES})
    assert (f == []) is ok


@pytest.mark.parametrize("t,ok", [(6, True), (5, False)])
def test_target_boundary(nonmoral_items, t, ok):
    s = {"valence": 1, "domain_moral": 0, "domain_prudential": t, "domain_procedural": 0}
    assert (screen.item_failures(_nm(nonmoral_items, "bad"), s) == []) is ok


def test_fully_passing_good_item_and_harm_control(nonmoral_items, foundation_items):
    assert screen.item_failures(_nm(nonmoral_items, "good"), {"valence": 7, **NM_GOOD_SCORES}) == []
    assert screen.item_failures(_get(foundation_items, "harm", "good"), {"valence": 9, "fnd_harm": 6}) == []


def test_foundation_harm_one_below_target_passes(foundation_items):
    item = _get(foundation_items, "loyalty", "bad")
    s = {"valence": 1, "fnd_fairness": 1, "fnd_authority": 1, "fnd_purity": 1, "fnd_loyalty": 6, "fnd_harm": 5}
    assert screen.item_failures(item, s) == []


def test_unparsed_paths(nonmoral_items, foundation_items):
    nm = _nm(nonmoral_items, "bad")
    assert screen.item_failures(nm, None) == ["not rated"]
    f = screen.item_failures(nm, {"valence": 1, "domain_moral": None, "domain_prudential": 8, "domain_procedural": None})
    assert "domain_moral unparsed" in f and "domain_procedural unparsed" in f
    assert "domain_prudential unparsed" in screen.item_failures(nm, {"valence": 1, "domain_prudential": None})
    fi = _get(foundation_items, "loyalty", "bad")
    assert "fnd_harm unparsed" in screen.item_failures(fi, {"valence": 1, "fnd_loyalty": 8, "fnd_harm": None})


def test_duplicate_ids_raise(nonmoral_items):
    with pytest.raises(ValueError, match="duplicate"):
        screen.select_pairs([nonmoral_items[0], nonmoral_items[0]], {})


def test_two_same_sign_members_are_not_a_pair(nonmoral_items):
    a = _nm(nonmoral_items, "bad")
    b = a.model_copy(update={"item_id": a.item_id + "x"})
    _, report = screen.select_pairs([a, b], {})
    assert all("partner not approved" in r["failures"] for r in report)


def test_report_has_pair_key_and_scores(nonmoral_items):
    pair = [_nm(nonmoral_items, "bad"), _nm(nonmoral_items, "good")]
    sc = {pair[0].item_id: {"valence": 1, **NM_GOOD_SCORES}}
    _, report = screen.select_pairs(pair, sc)
    assert report[0]["pair_key"] == report[1]["pair_key"] == "nonmoral|1|prudential"
    assert report[0]["scores"]["valence"] == 1 and report[1]["scores"] == {}
    assert report[1]["failures"] == "not rated"
