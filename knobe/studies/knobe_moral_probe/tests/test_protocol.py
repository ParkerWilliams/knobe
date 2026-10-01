import pytest
from knobe import constants

from conftest import make_items
from kmp import protocol
from kmp.items import ARMS


def test_core_questions_have_three_wordings_one_reversed():
    for qkey in protocol.CORE:
        ws = protocol.QUESTIONS[qkey]
        assert [w.key for w in ws] == ["w1", "w2", "w3r"]
        assert [w.reversed for w in ws] == [False, False, True]


def test_other_questions_have_one_normal_wording():
    for qkey, ws in protocol.QUESTIONS.items():
        if qkey not in protocol.CORE:
            assert len(ws) == 1 and ws[0].key == "w1" and not ws[0].reversed, qkey


def test_reversed_wordings_put_the_high_pole_at_zero():
    assert "0 (completely intentionally)" in protocol.wording("intentionality", "w3r").template
    assert "0 (extremely)" in protocol.wording("blame", "w3r").template
    assert "0 (extremely)" in protocol.wording("praise", "w3r").template


def test_w1_matches_the_pilot_and_production_wording():
    assert protocol.wording("intentionality", "w1").template == "Did {agent} intentionally {effect}?"
    for qkey in ("blame", "praise"):
        ours = protocol.wording(qkey, "w1").template.format(agent="the CEO", effect="x")
        theirs = constants.QUESTIONS[f"q_{qkey}"].format(agent_lower="the CEO")
        assert ours == theirs


def test_every_template_renders_with_agent_and_effect():
    for qkey, ws in protocol.QUESTIONS.items():
        for w in ws:
            text = w.template.format(agent="Bill", effect="injure children")
            assert "{" not in text, (qkey, w.key)


def test_sample_counts():
    assert protocol.N_PER_WORDING * 3 == protocol.N_SINGLE
    assert protocol.n_samples("blame") == protocol.N_PER_WORDING
    assert protocol.n_samples("significance") == protocol.N_SINGLE


def test_subject_questions_by_experiment_and_arm():
    nm = make_items("nonmoral", 1)[0]
    assert protocol.subject_qkeys(nm) == ["intentionality", "blame", "praise", "significance",
                                         "domain_moral", "domain_prudential", "domain_procedural"]
    harm, loyalty = [i for i in make_items("foundations", 1) if i.sign == "bad" and i.arm in ("harm", "loyalty")]
    assert protocol.subject_qkeys(harm)[-1:] == ["fnd_harm"]
    assert protocol.subject_qkeys(loyalty)[-2:] == ["fnd_harm", "fnd_loyalty"]


def test_screening_questions_start_with_valence():
    nm = make_items("nonmoral", 1)[0]
    mf = make_items("foundations", 1)[0]
    assert protocol.screening_qkeys(nm) == ["valence", *protocol.DOMAIN_CHECKS]
    assert protocol.screening_qkeys(mf) == ["valence", *protocol.FOUNDATION_CHECKS]


def test_examples_spread_across_the_scale():
    answers = [a for _, _, a in protocol.EXAMPLES]
    assert len(answers) == 3 and min(answers) <= 2 and max(answers) >= 8
    assert protocol.EXAMPLE_ANSWERS == frozenset(answers)


def test_instruction_and_block_come_from_the_frozen_templates():
    rendered = constants.RAIMONDI_PROMPT_TEMPLATE.format(scenario="S", question="Q")
    assert rendered == protocol.INSTRUCTION + "\n\n" + protocol.BLOCK.format(scenario="S", question="Q")


def test_release_and_runner_carry_the_study_name():
    assert protocol.RELEASE == "knobe_moral_probe"
    assert protocol.RUNNER_VERSION.startswith("knobe_moral_probe")


def test_questions_is_read_only():
    with pytest.raises(TypeError):
        protocol.QUESTIONS["new"] = ()
    with pytest.raises(TypeError):
        del protocol.QUESTIONS["blame"]


def test_reversed_flag_matches_key_suffix():
    for qkey, ws in protocol.QUESTIONS.items():
        for w in ws:
            assert w.key.endswith("r") == w.reversed, (qkey, w.key)


def test_every_arm_has_a_question_key():
    for arm in ARMS["foundations"]:
        assert f"fnd_{arm}" in protocol.QUESTIONS, arm
    for arm in ARMS["nonmoral"]:
        assert f"domain_{arm}" in protocol.QUESTIONS, arm
