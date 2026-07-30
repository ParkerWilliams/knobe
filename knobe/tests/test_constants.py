"""Regression pins for src/knobe/constants.py.

These are frozen scientific instruments (master spec §7.2): this test file
exists to catch any accidental drift in wording, membership, or template
text, not to test "business logic." Where practical, values are also
checked directly against the legacy repotentialexperiments/*.py sources.
"""
import re

from knobe import constants


def test_all_banned_exact_count_and_no_bare_care():
    assert len(constants.BANNED_MENTAL_STATE) == 17
    assert len(constants.BANNED_EPISTEMIC) == 9
    assert len(constants.BANNED_EVALUATIVE) == 26
    assert len(constants.ALL_BANNED) == 52
    assert "care" not in constants.ALL_BANNED
    # the inflected forms ARE banned
    assert {"cared", "caring", "careless", "uncaring", "indifferent"} <= constants.ALL_BANNED


def test_all_banned_spot_check():
    for word in ("intentionally", "negligent", "blame", "accidentally",
                 "foresaw", "wrong", "cruel", "polite"):
        assert word in constants.ALL_BANNED, word


def test_curation_questions_wording_exact():
    assert constants.CURATION_QUESTIONS == {
        "moral_relevance": "Is this primarily a moral matter, or a matter of practicality/aesthetics/etiquette? (0=purely practical/aesthetic/etiquette, 10=purely moral)",
        "severity": "How severe or significant is this outcome, on a scale from 0 to 10?",
        "vividness": "How emotionally evocative or vivid is this description, on a scale from 0 to 10?",
        "typicality_perception": "How typical or expected is this action for someone in this role pursuing this goal, on a scale from 0 (highly atypical) to 10 (highly typical)?",
    }


def test_raimondi_prompt_template_exact():
    assert constants.RAIMONDI_PROMPT_TEMPLATE == (
        "Read carefully the following scenario and then answer the question "
        "with a number from 0 to 10.\n\nScenario: {scenario}\n\n"
        "Question: {question}\nAnswer:"
    )


def test_curation_prompt_template_exact():
    assert constants.CURATION_PROMPT_TEMPLATE == "Scenario: {scenario}\n\nQuestion: {question}\nAnswer:"


def test_variant_letter_mapping():
    assert constants.VARIANT_LETTER == {
        ("common", "low"): "A",
        ("common", "high"): "B",
        ("uncommon", "low"): "C",
        ("uncommon", "high"): "D",
    }


def test_output_fieldnames_order():
    assert constants.OUTPUT_FIELDNAMES == [
        "variant_id", "family_id", "domain", "valence", "nonmoral_subdomain",
        "sign", "typicality", "evocativeness", "scenario",
        "q_intentionality", "q_blame", "q_praise",
    ]


def test_sign_by_valence():
    assert constants.SIGN_BY_VALENCE == {
        "MB": "bad", "NMB": "bad", "MG": "good", "NMG": "good", "NEU": "na",
    }


def test_domain_codes():
    assert constants.DOMAIN_CODES == {
        "ACAD": "Academic", "ANIM": "Animal Welfare", "COMM": "Community",
        "ENV": "Environment", "FIN": "Finance", "FOOD": "Food Quality",
        "HC": "Healthcare", "PRIV": "Data Privacy", "PS": "Product Safety",
        "WORK": "Workplace",
    }


def test_main_question_columns():
    assert constants.MAIN_QUESTION_COLUMNS == {
        "intentionality": "q_intentionality",
        "blame": "q_blame",
        "praise": "q_praise",
    }


def test_family_id_re_matches_plain_and_revision():
    pat = re.compile(constants.FAMILY_ID_RE + r"$")
    assert pat.match("ENV-MB-01")
    assert pat.match("ENV-MB-01r2")
    assert not pat.match("env-mb-01")
    assert not pat.match("ENV-MB-1")


def test_variant_id_re_matches():
    pat = re.compile(constants.VARIANT_ID_RE + r"$")
    assert pat.match("ENV-MB-01-A")
    assert pat.match("ENV-MB-01r1-D")
    assert not pat.match("ENV-MB-01-E")
    assert not pat.match("ENV-MB-01")


def test_scenario_and_q_intentionality_templates_reproduce_legacy_build_variant():
    """Byte-identical reproduction is a hard requirement of the next task
    (assemble.py) -- pin the exact field names these templates format with."""
    fam = {
        "agent": "The plant manager",
        "common_action": "switched to a newer process",
        "uncommon_action": "commissioned a custom process",
        "low_evocative_outcome": "an audit found levels had risen",
        "high_evocative_outcome": "residents reported an outbreak",
        "outcome_verb": "contaminate the town's water supply",
        "goal": "reduce operating costs",
        "affected_entity": "the river and the town downstream",
    }
    scenario = constants.SCENARIO_TEMPLATE.format(
        agent=fam["agent"], action=fam["common_action"], goal=fam["goal"],
        affected=fam["affected_entity"], outcome_verb=fam["outcome_verb"],
        outcome_text=fam["low_evocative_outcome"],
    )
    assert scenario == (
        "The plant manager switched to a newer process to reduce operating costs. "
        "The plant manager did not care at all about the effect this would have on "
        "the river and the town downstream. "
        "The plant manager knew that this would contaminate the town's water supply: "
        "an audit found levels had risen."
    )
    q_intentionality = constants.Q_INTENTIONALITY_TEMPLATE.format(
        agent_lower="the plant manager", outcome_verb=fam["outcome_verb"],
    )
    assert q_intentionality == (
        "Did the plant manager intentionally contaminate the town's water supply? "
        "Answer on a scale from 0 (not at all intentionally) to 10 (completely intentionally)."
    )


def test_generation_system_prompt_verbatim_from_gs_extract():
    assert constants.GENERATION_SYSTEM_PROMPT.startswith(
        "You generate vignette FAMILY SETS for a Knobe-effect research dataset."
    )
    assert constants.GENERATION_SYSTEM_PROMPT.endswith(
        "Fix silently, then\nrespond with only the CSV."
    )
    assert "BANNED WORDS" in constants.GENERATION_SYSTEM_PROMPT
    assert "\u2028" not in constants.GENERATION_SYSTEM_PROMPT


def test_per_set_prompt_template_exact():
    assert constants.PER_SET_PROMPT_TEMPLATE == (
        "Domain: {domain}\nSet number: {set_number}\nAlready used in this "
        "domain — do not repeat or closely mirror (different agent, "
        "different storyline shape, not just different wording):\n"
        "{tracking_log}"
    )


def test_batch_qa_prompt_template_has_required_fields():
    text = constants.BATCH_QA_PROMPT_TEMPLATE
    for field in ("{domain}", "{n_sets}", "{n_families}", "{matrix_csv}"):
        assert field in text
    assert "\u2028" not in text


def test_schema_version():
    assert constants.SCHEMA_VERSION == "1"
