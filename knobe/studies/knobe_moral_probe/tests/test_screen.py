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
