"""tools.lint_stimuli: mechanical checklist checks beyond design_problems."""
import csv

import pytest

from kmp.items import Item, make_item_id
from tools import lint_stimuli as lint
from tools import ngo_source
from tools.review_record import DECISION_FIELDS, text_sha256

CLERK_BAD = ("The clerk moved to a new apartment to be closer to the gym. The clerk did not care at all about "
             "the effect this would have on the clerk's savings. The clerk knew the move would drain the "
             "clerk's savings.")
CLERK_GOOD = CLERK_BAD.replace("would drain", "would grow")
GARDEN = "The coordinator rearranged the community garden's plots to shorten the watering route."
INDIFF = "The coordinator did not care at all about the effect this would have on {x}."


def make(experiment="nonmoral", sid=1, arm="prudential", sign="bad", agent="the clerk", effect=None,
         scenario=None, source="new", status="draft", scaffold=None):
    if scenario is None:
        scenario = CLERK_BAD if sign == "bad" else CLERK_GOOD
    if effect is None:
        effect = "drain the clerk's savings" if sign == "bad" else "grow the clerk's savings"
    if experiment == "foundations" and scaffold is None:
        scaffold = "shared"
    return Item(item_id=make_item_id(experiment, sid, arm, sign), experiment=experiment, storyline_id=sid,
                arm=arm, sign=sign, agent=agent, effect=effect, scenario=scenario, source=source,
                review_status=status, scaffold=scaffold)


def pair(**kw):
    return [make(sign="bad", **kw), make(sign="good", **kw)]


def fnd(sid, arm, sign, background, x, last, effect):
    return make(experiment="foundations", sid=sid, arm=arm, sign=sign, agent="the coordinator", effect=effect,
                scenario=" ".join([background, GARDEN, INDIFF.format(x=x), last]))


@pytest.fixture(scope="module")
def verbatim():
    return ngo_source.load_source()


# ---- per item ------------------------------------------------------------------------

def test_definitions_example_is_clean():
    assert lint.lint(pair()) == []


def test_sentence_count_and_question_line():
    item = make(scenario=CLERK_BAD + " Did the clerk intentionally drain the clerk's savings?")
    problems = lint.item_problems(item)
    assert any("4 sentences, the template has 3 (A1)" in p for p in problems)
    assert any("contains '?'" in p for p in problems)


def test_effect_form():
    assert any("(A10)" in p for p in lint.item_problems(make(effect="Drain the clerk's savings")))
    assert any("punctuation (A10)" in p for p in lint.item_problems(make(effect="drain the clerk's savings.")))
    assert any("without 'to'" in p for p in lint.item_problems(make(effect="to drain the clerk's savings")))


def test_agent_must_open_the_action_sentence():
    item = make(scenario=CLERK_BAD.replace("The clerk moved", "A clerk moved", 1))
    assert any("(A9)" in p for p in lint.item_problems(item))


def test_indifference_clause_template_for_new_items():
    item = make(scenario=CLERK_BAD.replace("the effect this would have", "the effect the move would have"))
    assert any("(A3)" in p for p in lint.item_problems(item))


def test_side_effect_sentence_opens_with_agent_knew():
    item = make(scenario=CLERK_BAD.replace("The clerk knew the move", "Everyone knew the move"))
    assert any("(A4)" in p for p in lint.item_problems(item))


def test_verbatim_items_get_only_a1_a9_a10(verbatim):
    assert [p for i in verbatim for p in lint.item_problems(i)] == []


# ---- pairs, storylines, file -----------------------------------------------------------------

def test_b2_flags_a_pair_differing_before_the_side_effect():
    good = make(sign="good", scenario=CLERK_GOOD.replace("closer to the gym", "closer to the park"))
    assert lint.pair_problems([make(sign="bad"), good]) == ["pair (1, 'prudential'): bad and good differ "
                                                           "before the side-effect sentence (B2)"]


def test_c2_one_agent_per_storyline():
    items = pair() + [make(arm="procedural", sign=s, agent="the engineer",
                           scenario=(CLERK_BAD if s == "bad" else CLERK_GOOD).replace("clerk", "engineer"))
                      for s in ("bad", "good")]
    assert any("agents differ across arms" in p for p in lint.storyline_problems(items, []))


def test_c3_fresh_action_needs_a_log_row():
    moral = [make(arm="moral", sign=s, source="ngo",
                  scenario=(CLERK_BAD if s == "bad" else CLERK_GOOD).replace("to be closer to the gym",
                                                                            "to be closer to work"))
             for s in ("bad", "good")]
    items = moral + pair()
    assert any("(C3, decision E)" in p for p in lint.storyline_problems(items, []))
    row = {"item_id": "kmp-nm-001-prudential-bad", "kind": "fresh_action"}
    assert lint.storyline_problems(items, [row]) == []


def test_c4_foundations_share_the_action_sentence():
    items = [fnd(1, "harm", "bad", "One older member has a bad knee.", "the older member",
                 "The coordinator knew the new layout would hurt the older member's knee.", "hurt the older member's knee"),
             fnd(1, "harm", "good", "One older member has a bad knee.", "the older member",
                 "The coordinator knew the new layout would ease the older member's knee pain.",
                 "ease the older member's knee pain")]
    assert lint.lint(items) == []
    changed = items[1].model_copy(update={"scenario": items[1].scenario.replace("watering route", "mowing route")})
    assert any("(C4)" in p for p in lint.storyline_problems([items[0], changed], []))


def test_d3_role_noun_reused_across_storylines():
    items = pair() + pair(sid=2)
    assert lint.file_problems(items) == ["file: role noun 'the clerk' is used by storylines [1, 2] (D3)"]


def test_d2_expect_complete_lists_missing_pairs():
    problems = lint.file_problems(pair(), expect_complete=True)
    assert "file: storyline 1 has no complete moral pair (D2)" in problems
    assert len(problems) == 40 * 3 - 1


# ---- B8: adapted Ngo pairs against the verbatim text ---------------------------------------------------

MANAGER_BAD = ("The manager enacted the plan to increase earnings. The manager did not care at all about the "
               "effect the plan would have on the manager's employees. The manager knew the plan would make "
               "employees unhappy.")


def adapted(sid, sign, scenario, effect, agent="the manager"):
    return make(sid=sid, arm="moral", sign=sign, agent=agent, effect=effect, scenario=scenario, source="ngo")


def test_b8_name_and_pronoun_changes_pass(verbatim):
    items = [adapted(19, "bad", MANAGER_BAD, "make employees unhappy"),
             adapted(19, "good", MANAGER_BAD.replace("unhappy.", "happy."), "make employees happy")]
    assert lint.adaptation_problems(items, verbatim, []) == []


def test_b8_other_changes_need_a_log_row(verbatim):
    item = adapted(19, "bad", MANAGER_BAD.replace("make employees unhappy", "make staff unhappy"),
                   "make employees unhappy")
    problems = lint.adaptation_problems([item], verbatim, [])
    assert problems == ["kmp-nm-019-moral-bad: scenario changes 'employees' to 'staff', which is not a name or "
                        "pronoun change and not in the authoring log (B8)"]
    row = {"item_id": item.item_id, "field": "scenario", "kind": "typo", "from": "make employees unhappy",
           "to": "make staff unhappy", "note": "test"}
    assert lint.adaptation_problems([item], verbatim, [row]) == []


def test_b8_goal_alignment_and_stale_rows(verbatim):
    bad = ("The investor enacted a financial scheme to buy a house. The investor did not care at all about the "
           "effect the scheme would have on old retirees. The investor knew the plan would bankrupt old retirees.")
    good = ("The investor enacted a financial scheme to buy a house. The investor did not care at all about the "
            "effect the scheme would have on old retirees. The investor knew the plan would help old retirees.")
    items = [adapted(3, "bad", bad, "bankrupt old retirees", "the investor"),
             adapted(3, "good", good, "help old retirees", "the investor")]
    goal = {"item_id": "kmp-nm-003-moral-good", "field": "scenario", "kind": "goal", "from": "to buy a car",
            "to": "to buy a house", "note": "decision B2"}
    assert any("to 'house'" in p for p in lint.adaptation_problems(items, verbatim, []))
    assert lint.adaptation_problems(items, verbatim, [goal]) == []
    stale = {**goal, "from": "to buy a boat"}
    assert any("stale" in p for p in lint.adaptation_problems(items, verbatim, [stale]))
    boat = [items[0], items[1].model_copy(update={"scenario": good.replace("buy a house", "buy a boat")})]
    wrong_goal = {**goal, "to": "to buy a boat"}
    assert any("not the bad version's goal" in p for p in lint.adaptation_problems(boat, verbatim, [wrong_goal]))


def test_b8_checks_the_effect_too(verbatim):
    item = adapted(19, "bad", MANAGER_BAD, "upset employees")
    assert any("effect changes" in p for p in lint.adaptation_problems([item], verbatim, []))


def test_lint_requires_verbatim_for_adapted_items():
    item = adapted(19, "bad", MANAGER_BAD, "make employees unhappy")
    assert "file: adapted Ngo items need --verbatim to check B8" in lint.lint([item])


# ---- B9, authoring log, approvals, CLI -------------------------------------------------------------------

def test_b9_verbatim_must_equal_the_source(verbatim):
    assert lint.lint(verbatim) == []
    edited = [verbatim[0].model_copy(update={"scenario": verbatim[0].scenario.replace("babies.", "infants.")}),
              *verbatim[1:]]
    assert any("(B9)" in p for p in lint.lint(edited))


def test_log_rows_are_checked():
    rows = [{"item_id": "kmp-nm-099-moral-bad", "field": "question", "kind": "whim", "from": "", "to": "", "note": ""}]
    problems = lint.log_problems(pair(), rows)
    assert len(problems) == 4


def test_approved_items_need_a_decision():
    items = pair(status="approved")
    assert any("no review decision" in p for p in lint.lint(items))
    rows = [{"item_id": i.item_id, "text_sha256": text_sha256(i), "decision": "approved", "file": "f"} for i in items]
    assert lint.lint(items, decisions=rows) == []


def test_cli(tmp_path, capsys):
    from kmp.items import write_items
    path = tmp_path / "nonmoral.csv"
    write_items(pair(), path)
    review = tmp_path / "review"
    review.mkdir()
    args = [str(path), "--log", str(tmp_path / "none.csv"), "--verbatim", str(tmp_path / "none.csv"),
            "--review-dir", str(review)]
    assert lint.main(args) == 0
    assert "prudential: 1 draft pairs" in capsys.readouterr().out
    write_items(pair() + pair(sid=2), path)
    assert lint.main(args) == 1
    assert "(D3)" in capsys.readouterr().err
