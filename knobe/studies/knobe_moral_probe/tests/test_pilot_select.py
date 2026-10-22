"""tools.pilot_select: the pilot's items, drawn reproducibly from approved pairs that passed screening."""
from conftest import make_items
from kmp.items import load_items, write_items
from tools import pilot_select


def _setup(tmp_path, experiment, n, drop_status=()):
    items = make_items(experiment, n)
    items = [i.model_copy(update={"review_status": "draft"}) if (i.storyline_id, i.arm) in drop_status else i
             for i in items]
    path, sel = tmp_path / f"{experiment}.csv", tmp_path / f"{experiment}_selected.csv"
    write_items(items, path)
    write_items([i for i in items if not (i.storyline_id == 1 and i.arm == "procedural")], sel)   # 1/procedural failed
    return path, sel


def test_pick_takes_whole_pairs_that_are_approved_and_passed(tmp_path):
    path, sel = _setup(tmp_path, "nonmoral", 6, drop_status={(2, "moral")})
    picked = pilot_select.pick(load_items(path), load_items(sel), {"moral": 3, "prudential": 3, "procedural": 3})
    keys = {(i.storyline_id, i.arm) for i in picked}
    assert len(picked) == 18 and len(keys) == 9
    assert (1, "procedural") not in keys and (2, "moral") not in keys
    assert all(i.review_status == "approved" for i in picked)


def test_pick_is_reproducible_and_seed_dependent(tmp_path):
    path, sel = _setup(tmp_path, "nonmoral", 10)
    items, selected = load_items(path), load_items(sel)
    want = {"moral": 2, "prudential": 2, "procedural": 2}
    a = pilot_select.pick(items, selected, want)
    assert a == pilot_select.pick(items, selected, want)
    assert a != pilot_select.pick(items, selected, want, base_seed="other")


def test_pick_refuses_too_few_eligible_pairs(tmp_path):
    path, sel = _setup(tmp_path, "nonmoral", 2)
    try:
        pilot_select.pick(load_items(path), load_items(sel), {"procedural": 2})
    except ValueError as exc:
        assert "procedural" in str(exc)
    else:
        raise AssertionError("expected ValueError")
