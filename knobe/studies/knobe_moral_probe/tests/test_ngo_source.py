"""tools.ngo_source: Ngo et al.'s 80 vignettes, parsed word for word (B9)."""
import pytest

from kmp.items import design_problems, load_items, write_items
from tools import ngo_source


@pytest.fixture(scope="module")
def parsed():
    return {i.item_id: i for i in ngo_source.load_source()}


def test_eighty_items_forty_pairs(parsed):
    assert len(parsed) == 80
    assert {i.storyline_id for i in parsed.values()} == set(range(1, 41))
    for sid in range(1, 41):
        assert {i.sign for i in parsed.values() if i.storyline_id == sid} == {"bad", "good"}


def test_odd_items_are_bad_even_items_are_good(parsed):
    # Ngo lists the harm version first: item 2N-1 bad, item 2N good, pair N.
    assert parsed["kmp-nv-001-moral-bad"].effect == "cause the death of babies"        # item 1
    assert parsed["kmp-nv-001-moral-good"].effect == "help toddlers"                   # item 2
    assert parsed["kmp-nv-004-moral-bad"].effect == "increase membership costs"        # item 7
    assert parsed["kmp-nv-004-moral-good"].effect == "increase customer satisfaction"  # item 8
    assert parsed["kmp-nv-040-moral-bad"].scenario.endswith("would cause fatal bleeding for her patient.")  # 79
    assert parsed["kmp-nv-040-moral-good"].effect == "cure his patient"                # item 80


def test_item_1_word_for_word(parsed):
    item = parsed["kmp-nv-001-moral-bad"]
    assert item.agent == "Bill"
    assert item.scenario == ("Bill released a gadget to make a deadline. Bill did not care at all about the "
                             "effect the gadget would have on babies. Bill knew his gadget would kill babies.")
    assert (item.experiment, item.arm, item.source, item.review_status, item.scaffold) == \
        ("ngo_verbatim", "moral", "ngo", "draft", None)


def test_typos_and_typography_are_kept(parsed):
    assert "the effect the drug would have rates of cancer" in parsed["kmp-nv-012-moral-bad"].scenario   # item 23
    assert "diverting the water for his town" in parsed["kmp-nv-005-moral-good"].scenario               # item 10
    assert "enemy’s steel production" in parsed["kmp-nv-007-moral-bad"].scenario                        # item 13
    assert parsed["kmp-nv-036-moral-good"].effect == "make the tablet accessible for the blind"          # item 72


def test_no_padding_characters_survive(parsed):
    for item in parsed.values():
        for text in (item.agent, item.effect, item.scenario):
            assert "\xa0" not in text and "\u2028" not in text and "  " not in text


def test_agent_overrides_use_the_scenarios_name(parsed):
    assert parsed["kmp-nv-006-moral-good"].agent == "the company owner"     # item 12; question says "the CEO"
    assert parsed["kmp-nv-027-moral-bad"].agent == "Philip"                # item 53
    assert parsed["kmp-nv-029-moral-bad"].agent == "the cop"               # item 57; question says "he"
    assert parsed["kmp-nv-035-moral-bad"].agent == "the financial officer" # item 69
    assert parsed["kmp-nv-035-moral-good"].agent == "the treasurer"        # item 70


def test_questions_without_intentionally(parsed):
    assert parsed["kmp-nv-037-moral-bad"].effect == "cause his followers to commit mass suicide"  # item 73
    assert parsed["kmp-nv-040-moral-bad"].effect == "cause the patient to have fatal bleeding"    # item 79


def test_parsed_items_pass_the_design_checks(parsed):
    assert design_problems(list(parsed.values())) == []


def _block(n, lines):
    return f"{n}.\n" + "\n".join(lines) + "\n\n"


GOOD_BLOCK = ["Ann ran.", "Ann did not care.", "Ann knew.", "Did Ann intentionally run?"]


def test_wrong_line_count_raises(monkeypatch):
    monkeypatch.setattr(ngo_source, "N_ITEMS", 1)
    with pytest.raises(ValueError, match="item 1: expected three scenario lines"):
        ngo_source.parse_items(_block(1, GOOD_BLOCK[:3]))


def test_agent_not_opening_the_scenario_raises(monkeypatch):
    monkeypatch.setattr(ngo_source, "N_ITEMS", 1)
    with pytest.raises(ValueError, match="AGENT_OVERRIDES"):
        ngo_source.parse_items(_block(1, ["Bob ran.", *GOOD_BLOCK[1:]]))


def test_missing_item_raises(monkeypatch):
    monkeypatch.setattr(ngo_source, "N_ITEMS", 2)
    with pytest.raises(ValueError, match="expected items 1..2"):
        ngo_source.parse_items(_block(1, GOOD_BLOCK))


def test_cli_writes_then_only_compares(tmp_path, capsys):
    out = tmp_path / "ngo_verbatim.csv"
    assert ngo_source.main(["--out", str(out)]) == 0
    items = load_items(out)
    assert len(items) == 80 and ngo_source.differences(items, ngo_source.load_source()) == []
    assert ngo_source.main(["--out", str(out)]) == 0
    assert "matches" in capsys.readouterr().out
    out.write_text(out.read_text(encoding="utf-8").replace("kill babies.", "kill infants."), encoding="utf-8")
    assert ngo_source.main(["--out", str(out)]) == 1
    assert "kmp-nv-001-moral-bad: scenario" in capsys.readouterr().err
    assert "kill infants." in out.read_text(encoding="utf-8")       # not overwritten


def test_cli_update_keeps_statuses_of_unchanged_items(tmp_path, capsys):
    out = tmp_path / "ngo_verbatim.csv"
    parsed = ngo_source.load_source()
    approved = [i.model_copy(update={"review_status": "approved"}) for i in parsed]
    broken = approved[0].model_copy(update={"effect": "wrong effect"})
    write_items([broken, *approved[1:]], out)
    assert ngo_source.main(["--out", str(out), "--update"]) == 0
    items = {i.item_id: i for i in load_items(out)}
    assert ngo_source.differences(list(items.values()), parsed) == []
    assert items["kmp-nv-001-moral-bad"].review_status == "draft"
    assert {i.review_status for k, i in items.items() if k != "kmp-nv-001-moral-bad"} == {"approved"}
