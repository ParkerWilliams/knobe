"""ngo_verbatim: Ngo et al.'s 40 original pairs, word for word, as a
consistency set (DESIGN.md 2026-10-01 amendment "Ngo goals and verbatim set").

Exempt from the same-agent and gendered-pronoun checks and nothing else;
asked and screened exactly like the adapted moral items (experiment
nonmoral, arm moral)."""
import pytest
from knobe.schemas import ResultRecord, append_jsonl
from pydantic import ValidationError

from conftest import make_items, make_ngo_verbatim_items
from kmp import elicit, frame, prompts, protocol, screen, screen_run
from kmp.items import ARMS, EXPERIMENT_CODE, Item, design_problems, make_item_id, write_items


def _as_nonmoral(item: Item) -> Item:
    """The same text, re-filed as an adapted nonmoral moral item."""
    return Item(**{**item.model_dump(), "experiment": "nonmoral",
                   "item_id": make_item_id("nonmoral", item.storyline_id, item.arm, item.sign)})


def _bogus(item: Item) -> Item:
    """An item whose experiment is unknown (bypasses validation on purpose)."""
    return Item.model_construct(**{**item.model_dump(), "experiment": "bogus"})


# ---- items -------------------------------------------------------------------

def test_id_format_and_arms():
    assert EXPERIMENT_CODE["ngo_verbatim"] == "nv"
    assert ARMS["ngo_verbatim"] == ("moral",)
    assert make_item_id("ngo_verbatim", 7, "moral", "bad") == "kmp-nv-007-moral-bad"
    assert [i.item_id for i in make_ngo_verbatim_items(1)] == ["kmp-nv-001-moral-bad", "kmp-nv-001-moral-good"]


def test_item_rejects_other_arms_and_non_ngo_source():
    base = make_ngo_verbatim_items(1)[0].model_dump()
    with pytest.raises(ValidationError, match="arm"):
        Item(**{**base, "arm": "prudential", "item_id": "kmp-nv-001-prudential-bad"})
    with pytest.raises(ValidationError, match="source"):
        Item(**{**base, "source": "new"})


def test_exemption_applies_to_ngo_verbatim(ngo_verbatim_items):
    assert design_problems(ngo_verbatim_items) == []


def test_same_text_under_nonmoral_is_flagged(ngo_verbatim_items):
    problems = design_problems([_as_nonmoral(i) for i in ngo_verbatim_items])
    assert any("agents differ" in p for p in problems)
    assert any("gendered pronoun" in p for p in problems)


def test_other_checks_still_apply(ngo_verbatim_items):
    missing = design_problems(ngo_verbatim_items[1:])
    assert any("needs exactly one bad and one good" in p for p in missing)
    dup = design_problems(ngo_verbatim_items + ngo_verbatim_items[:1])
    assert any("duplicate item_id" in p for p in dup)
    mixed = design_problems(ngo_verbatim_items + make_items("nonmoral", 1))
    assert any("mixed experiments" in p for p in mixed)


# ---- protocol ----------------------------------------------------------------

def test_qkeys_equal_nonmoral_moral(ngo_verbatim_items):
    for item in ngo_verbatim_items:
        nm = _as_nonmoral(item)
        assert protocol.subject_qkeys(item) == protocol.subject_qkeys(nm)
        assert protocol.screening_qkeys(item) == protocol.screening_qkeys(nm)


def test_unknown_experiment_raises_rather_than_routing_to_foundations():
    item = _bogus(make_items("foundations", 1)[0])
    for fn in (protocol.subject_qkeys, protocol.screening_qkeys, screen.intended_check):
        with pytest.raises(ValueError, match="bogus"):
            fn(item)
    with pytest.raises(ValueError, match="bogus"):
        screen.item_failures(item, {"valence": 1, "fnd_harm": 8})


# ---- screening ---------------------------------------------------------------

SCORE_SETS = [
    {"valence": 1, "domain_moral": 8, "domain_prudential": 2, "domain_procedural": 2},
    {"valence": 9, "domain_moral": 8, "domain_prudential": 2, "domain_procedural": 2},
    {"valence": 5, "domain_moral": 5, "domain_prudential": 5, "domain_procedural": 1},
    {"valence": 1, "domain_moral": 7, "domain_prudential": 7, "domain_procedural": None},
    {"valence": None, "domain_moral": None},
    {},
]


@pytest.mark.parametrize("scores", SCORE_SETS)
def test_screening_rule_equals_nonmoral_moral(ngo_verbatim_items, scores):
    for item in ngo_verbatim_items:
        nm = _as_nonmoral(item)
        assert screen.intended_check(item) == screen.intended_check(nm) == "domain_moral"
        assert screen.item_failures(item, scores) == screen.item_failures(nm, scores)


def test_screen_cli_mock_runs_on_ngo_verbatim(tmp_path, ngo_verbatim_items):
    path = tmp_path / "items.csv"
    write_items(ngo_verbatim_items, path)
    assert screen_run.main(["--items", str(path), "--out-dir", str(tmp_path / "s"), "--mock"]) == 0


# ---- prompts, elicitation, frame ----------------------------------------------

def test_prompts_build_like_nonmoral_moral(ngo_verbatim_items):
    item = ngo_verbatim_items[0]
    nm = _as_nonmoral(item)
    specs, nm_specs = prompts.build_subject_prompts([item]), prompts.build_subject_prompts([nm])
    assert [(s.qkey, s.wording_key, s.text, s.n_samples) for s in specs] == \
           [(s.qkey, s.wording_key, s.text, s.n_samples) for s in nm_specs]
    assert all(s.item_id == item.item_id and item.scenario in s.text for s in specs)
    sp, nm_sp = prompts.build_screening_prompts([item]), prompts.build_screening_prompts([nm])
    assert [(p.qkey, p.text) for p in sp] == [(p.qkey, p.text) for p in nm_sp]


def test_elicit_build_jobs(ngo_verbatim_items):
    keys = ["gemma-2-9b-pretrained", "gemma-2-9b-instruct"]
    specs = prompts.build_subject_prompts(ngo_verbatim_items[:1])
    jobs = elicit.build_jobs(specs, keys)
    assert len(jobs) == 2 * sum(s.n_samples for s in specs)
    assert {j.prompt_id.split("::")[0] for j in jobs} == {"kmp-nv-001-moral-bad"}


def test_frame_loads_ngo_verbatim(tmp_path):
    items = make_ngo_verbatim_items(3)
    path = tmp_path / "r.jsonl"
    with open(path, "w", encoding="utf-8") as fh:
        for iid in ("kmp-nv-002-moral-bad", "kmp-nv-003-moral-good"):
            pid = f"{iid}::blame::w1::chat"
            append_jsonl(ResultRecord(
                job_id=f"{pid}::gemma-2-9b-instruct::0", prompt_id=pid, model_key="gemma-2-9b-instruct",
                sample_idx=0, temperature=1.0, seed=1, raw_response="7", parsed_rating=7, parse_ok=True,
                parse_method="regex", logprobs_0_10=None, model_revision="r", runner_version="t",
                timestamp=0.0), fh)
    d = frame.load_frame(path, items).set_index("item_id")
    assert set(d["experiment"]) == {"ngo_verbatim"}
    assert d.loc["kmp-nv-002-moral-bad", "storyline_id"] == 2
    assert d.loc["kmp-nv-003-moral-good", "storyline_id"] == 3
    assert set(d["arm"]) == {"moral"}
