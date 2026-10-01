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


import asyncio  # noqa: E402
import json  # noqa: E402

import pandas as pd  # noqa: E402

from knobe.schemas import CurationRawResult, read_jsonl  # noqa: E402
from pydantic import ValidationError  # noqa: E402
from kmp import prompts, protocol  # noqa: E402
from kmp.items import load_items, write_items  # noqa: E402


class ScriptedClient:
    """Answers by rule from the [arm] [sign] markers in make_items' scenarios.
    `flaky` holds (item_id, qkey) keys that answer 'unclear' on first call."""

    def __init__(self, items, flaky=()):
        self.lookup = {p.text: (p.item_id, p.qkey) for p in prompts.build_screening_prompts(items)}
        self.items = {i.item_id: i for i in items}
        self.flaky = set(flaky)
        self.calls = []

    async def complete(self, prompt, max_tokens):
        item_id, qkey = self.lookup[prompt]
        self.calls.append((item_id, qkey))
        if (item_id, qkey) in self.flaky:
            self.flaky.discard((item_id, qkey))
            return "unclear"
        item = self.items[item_id]
        if qkey == "valence":
            return "1" if item.sign == "bad" else "9"
        return "8" if qkey == screen.intended_check(item) else "2"


def test_run_screening_resumes_and_retries_unparsed_once(tmp_path, nonmoral_items):
    out = tmp_path / "raw.jsonl"
    ps = prompts.build_screening_prompts(nonmoral_items)
    flaky_key = (ps[0].item_id, ps[0].qkey)
    client = ScriptedClient(nonmoral_items, flaky=[flaky_key])
    asyncio.run(screen.run_screening(ps, client, "scripted", out))
    rows = read_jsonl(out, screen.ScreeningRawResult)
    assert len(rows) == len(ps) + 1                                  # one retry
    assert screen.scores_from_raw(rows)[flaky_key[0]][flaky_key[1]] is not None
    asyncio.run(screen.run_screening(ps, client, "scripted", out))
    assert len(read_jsonl(out, screen.ScreeningRawResult)) == len(rows)       # resume: nothing re-asked


def test_all_pairs_pass_under_scripted_reviewer(tmp_path, foundation_items):
    out = tmp_path / "raw.jsonl"
    ps = prompts.build_screening_prompts(foundation_items)
    asyncio.run(screen.run_screening(ps, ScriptedClient(foundation_items), "scripted", out))
    selected, _ = screen.select_pairs(foundation_items, screen.scores_from_raw(read_jsonl(out, screen.ScreeningRawResult)))
    assert len(selected) == len(foundation_items)


def test_main_mock_writes_outputs(tmp_path, nonmoral_items):
    items_path = tmp_path / "items.csv"
    write_items(nonmoral_items, items_path)
    code = screen.main(["--items", str(items_path), "--out-dir", str(tmp_path / "s"), "--mock"])
    assert code == 0
    assert (tmp_path / "s" / "screening_raw.jsonl").exists()
    assert (tmp_path / "s" / "selection_report.csv").exists()
    load_items(tmp_path / "s" / "selected_items.csv")                 # valid, possibly empty


def _raw_row(field):
    return screen.ScreeningRawResult(variant_id="kmp-x", field=field, value=3, ok=True, raw="3",
                                     reviewer_model="scripted", timestamp=0.0, text_sha256="0" * 64)


def test_screening_raw_result_round_trips_kmp_qkeys_and_rejects_unknown():
    for qkey in sorted(screen.SCREENING_QKEYS):
        row = _raw_row(qkey)
        assert screen.ScreeningRawResult.model_validate_json(row.model_dump_json()) == row
    for bad in ("blame", "moral_relevance", "nonsense"):
        with pytest.raises(ValidationError):
            _raw_row(bad)


def test_screening_raw_result_fields_cover_curation_raw_result():
    assert set(CurationRawResult.model_fields) <= set(screen.ScreeningRawResult.model_fields)


def test_raw_rows_carry_prompt_hash(tmp_path, nonmoral_items):
    out = tmp_path / "raw.jsonl"
    ps = prompts.build_screening_prompts(nonmoral_items)
    asyncio.run(screen.run_screening(ps, ScriptedClient(nonmoral_items), "scripted", out))
    want = {(p.item_id, p.qkey): p.text_sha256 for p in ps}
    assert {(r.variant_id, r.field): r.text_sha256 for r in read_jsonl(out, screen.ScreeningRawResult)} == want


def _scripted_scores(tmp_path, items):
    out = tmp_path / "raw.jsonl"
    asyncio.run(screen.run_screening(prompts.build_screening_prompts(items), ScriptedClient(items), "scripted", out))
    return screen.scores_from_raw(read_jsonl(out, screen.ScreeningRawResult))


def test_pair_summary_counts_singleton_pairs_by_pair_key(tmp_path, nonmoral_items):
    approved = [i for i in nonmoral_items if i.item_id != _get(nonmoral_items, "moral", "good").item_id]
    _, report = screen.select_pairs(approved, _scripted_scores(tmp_path, approved))
    summary = screen.pair_summary(report)
    assert summary["moral"] == {"pairs": 2, "pairs_passed": 1}            # rows // 2 would give 1 pair
    assert summary["prudential"] == summary["procedural"] == {"pairs": 2, "pairs_passed": 2}


def test_main_records_thresholds_pair_counts_and_json_scores(tmp_path, nonmoral_items):
    singleton = _get(nonmoral_items, "moral", "good")
    items = [i.model_copy(update={"review_status": "draft"}) if i.item_id == singleton.item_id else i
             for i in nonmoral_items]
    items_path = tmp_path / "items.csv"
    write_items(items, items_path)
    assert screen.main(["--items", str(items_path), "--out-dir", str(tmp_path / "s"), "--mock"]) == 0
    meta = json.loads((tmp_path / "s" / "screening_meta.json").read_text())
    assert meta["reviewer_model"] == "mock" and meta["reviewer_temperature"] is None
    assert (meta["valence_bad_max"], meta["valence_good_min"], meta["target_min"]) == (
        screen.VALENCE_BAD_MAX, screen.VALENCE_GOOD_MIN, screen.TARGET_MIN)
    assert {arm: c["pairs"] for arm, c in meta["pairs_by_arm"].items()} == {
        "moral": 2, "procedural": 2, "prudential": 2}
    report = pd.read_csv(tmp_path / "s" / "selection_report.csv")
    assert set(report["pair_key"]) and len(report) == len(nonmoral_items) - 1
    for cell in report["scores"]:
        assert set(json.loads(cell)) == {"valence", *protocol.DOMAIN_CHECKS}
