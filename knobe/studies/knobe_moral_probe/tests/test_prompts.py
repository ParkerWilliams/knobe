from knobe import constants

from conftest import make_items
from kmp import prompts, protocol


def test_render_text_without_examples_is_the_frozen_frame():
    assert prompts.render_text("S", "Q", examples=()) == constants.RAIMONDI_PROMPT_TEMPLATE.format(scenario="S", question="Q")


def test_render_text_with_examples():
    text = prompts.render_text("S", "Q")
    assert text.startswith(protocol.INSTRUCTION + "\n\n")
    for scenario, question, answer in protocol.EXAMPLES:
        assert f"Scenario: {scenario}\n\nQuestion: {question}\nAnswer: {answer}" in text
    assert text.endswith("Scenario: S\n\nQuestion: Q\nAnswer:")


def test_subject_prompt_counts_per_item():
    nm = make_items("nonmoral", 1)
    mf = make_items("foundations", 1)
    assert len(prompts.build_subject_prompts(nm[:1])) == 9 + 1 + 3
    loyalty = [i for i in mf if i.arm == "loyalty"][:1]
    harm = [i for i in mf if i.arm == "harm"][:1]
    assert len(prompts.build_subject_prompts(loyalty)) == 9 + 1 + 2
    assert len(prompts.build_subject_prompts(harm)) == 9 + 1 + 1


def test_subject_prompts_unique_and_rendered(nonmoral_items):
    specs = prompts.build_subject_prompts(nonmoral_items)
    assert len({s.stem for s in specs}) == len(specs)
    spec = next(s for s in specs if s.qkey == "intentionality" and s.wording_key == "w1")
    item = next(i for i in nonmoral_items if i.item_id == spec.item_id)
    assert f"Question: Did {item.agent} intentionally {item.effect}?\nAnswer:" in spec.text
    assert spec.n_samples == protocol.N_PER_WORDING
    assert next(s for s in specs if s.qkey == "significance").n_samples == protocol.N_SINGLE


def test_reversed_flag_follows_protocol(nonmoral_items):
    for s in prompts.build_subject_prompts(nonmoral_items):
        assert s.reversed == protocol.is_reversed(s.qkey, s.wording_key)


def test_screening_prompts_have_no_examples(nonmoral_items, foundation_items):
    nm = prompts.build_screening_prompts(nonmoral_items[:1])
    mf = prompts.build_screening_prompts(foundation_items[:1])
    assert [p.qkey for p in nm] == ["valence", *protocol.DOMAIN_CHECKS]
    assert len(mf) == 6
    assert all("Answer: 5" not in p.text for p in nm + mf)


def test_formats_and_prompt_ids():
    assert prompts.format_for_model("gemma-2-9b-instruct") == "chat"
    assert prompts.format_for_model("gemma-2-9b-pretrained") == "raw"
    pid = prompts.prompt_id("kmp-nm-001-moral-bad::blame::w3r", "chat")
    assert prompts.parse_prompt_id(pid) == ("kmp-nm-001-moral-bad", "blame", "w3r", "chat")
