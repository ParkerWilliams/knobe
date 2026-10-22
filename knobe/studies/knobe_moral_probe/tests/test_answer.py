"""kmp.answer.extract_rating: read the number a model wrote, and only that.

Fixtures are real replies from the 2026-10-12/13 OpenRouter runs (Llama-3.1-8B-
Instruct, Mistral-Nemo, Gemma-3-4B-it), plus a few constructed edge cases
marked as such. The cases knobe.parsing.parse_rating got wrong (refusals and
scale restatements scored as 0) are pinned explicitly.
"""
import pytest

from kmp.answer import extract_rating

ANSWERED = [
    # (reply, expected rating)
    ("7", 7),
    ("10 \n\n**Reasoning:** The s", 10),
    ("**9**\n\nThis scenario is prim", 9),
    ("**Answer: 0**", 0),
    ("0 (not at all)", 0),
    ("5 (neither good nor bad)", 5),
    ("I would answer: 0\n\nThe researcher has", 0),
    ("Based on the scenario, I would answer:\n\n0", 0),
    ("Considering Jack's action, I would answer:\n\n7", 7),
    ("I would rate this side effect a 0.", 0),
    ("Given the scenario, the answer would be 10", 10),
    ("I would answer 0. The president's actions", 0),
    ("The answer is 0 (not at all).", 0),
    ("Answer: 10\n\nExplanation: The", 10),
    ("Based on the scenario, the answer is 0", 0),
    ("Answer: 0\n\nThis side effect is a", 0),
    ("Tim is to blame at a level of 7", 7),
    ("Praiseworthy: 3\n\nExplanation:", 3),
    ("The answer to this question is 0, not", 0),
    ("Based on the scenario, the CEO deserves 0", 0),
    ("Based on the scenario, Stanley is 7 (", 7),
    ('I\'m going to answer "0".\n\nThe president', 0),
    ("I think a blameworthy score of 8", 8),
    ("The significant side effect is a 0. The", 0),
    ("8.5\n\nThe question asks if Simon intentionally", 8.5),
    ("9.5\n\nHere's why:\n\n1.", 9.5),
    ("7.5", 7.5),
    ("The extent to which this side effect is a matter of convention, on a scale from 0 (not at all) to 10 (entirely), is 0.\n\nIn t", 0),
    ('In this scenario, the extent to which the agent\'s (Renee) own interests are involved is "0" (not at all). The side', 0),
    ("I would rate the extent to which the side effect of the gadget is a matter of convention as 0. The side effect", 0),
    ("ld be significant.\n\nTherefore, I would rate the significance of the side effect as 10 (extremely significant).", 10),
    ("On a scale of 0 to 10, I would rate the moral aspect of this side effect as a 5. Here's", 5),
    ('A trick question!\n\nThe answer is "7"', 7),
    ("This action entirely (10 out of 1", 10),
    ("1. Jared intentionally placed his aunt in a nursing", 1),
    ("8\n\nThe side effect is significant because:\n\n1", 8),
    ("Answer: 7\n\nHere's why:\n\n1", 7),
    # constructed
    ("On a scale from 0 to 10, I'd say 7.", 7),
    ("I'd give it a 3 out of 10.", 3),
    ("8/10", 8),
    ("Based on the scenario described above, the agent clearly acted.\n\n6", 6),
]

NOT_ANSWERED = [
    # (reply, expected rule) -- each was scored as a number by the old first-integer parser
    ("I cannot provide a number from 0 to ", "refusal"),
    ("A score of 0 on this scale would indicate", "no_number"),
    ("A scale of 0 to 10 suggests", "no_number"),
    ("Scale (0-10), where 0", "no_number"),
    # unparseable under both parsers
    ("I cannot provide a number in response to your question", "refusal"),
    ("Based on the scenario, it appears that the question", "no_number"),
    ("Yes, Jo intentionally destroyed the hero's reputation as", "no_number"),
    (" zentrales今は0 questione private homogeneousымшкам", "no_number"),
    ("", "blank"),
    ("   \n ", "blank"),
    # constructed
    ("Answer: 3\n\nActually, the answer is 7", "ambiguous"),
    ("15", "no_number"),
    ("Bill harmed 5 people in the process.", "no_number"),
    ("You want me to answer a question from 0", "no_number"),
    ("1. This is a simple counting question.\n\n2", "list"),
    ("1.  The answer is 0. The", "ambiguous"),
    ("1. The child has two apples and eats both", "list"),
    ("1. Something.\n2. Something else.", "list"),
    ("On a scale of 0 to 10", "no_number"),
    ("I'm using a scale of 0-1", "no_number"),
    ("Based on the scale provided (0 to 1", "no_number"),
    ("The radio broke after 6 switchings. The", "no_number"),
    ("The level of harm is 3 people injured, which", "no_number"),
    ("A 9 or 10. This is because", "ambiguous"),
    ("Based on the given answer formats (1-3", "ambiguous"),
    ("10.5", "no_number"),
]


@pytest.mark.parametrize("reply,expected", ANSWERED)
def test_reads_the_written_answer(reply, expected):
    value, ok, rule = extract_rating(reply)
    assert ok and value == expected, (reply, value, rule)


@pytest.mark.parametrize("reply,rule", NOT_ANSWERED)
def test_never_scores_a_non_answer(reply, rule):
    value, ok, got_rule = extract_rating(reply)
    assert not ok and value is None, (reply, value, got_rule)
    assert got_rule == rule, (reply, got_rule)


def test_rule_names_the_path_taken():
    assert extract_rating("7")[2] == "leading"
    assert extract_rating("Given the scenario, the answer would be 10")[2] == "phrase"
    assert extract_rating("Some reasoning first.\n\n6")[2] == "final_line"
    assert extract_rating("Based on the scenario, the CEO deserves 0")[2] == "first_number"


# 2026-10-22: real Llama-3.1-8B-Instruct replies to intentionality w1a/w1b (outputs/elicit/
# wording_test_llama.jsonl) that the reader missed. Truncated where the rest adds no number.
ANSWERED_2026_10_22 = [
    # an answer line (the number, maybe its anchor label) after a lead-in line ending in ":"
    ("Based on the scenario, the CEO intentionally harmed the environment, so I would rate the answer as:\n\n"
     "10 (definitely yes)\n\nThe CEO's statement \"She knew her plan would harm the environment\" suggests", 10),
    ("Therefore, I would rate the answer as:\n\n8\n\nThis suggests that Natasha likely knew that her renovation "
     "would increase membership costs, but we can't be certain if that was her intention.", 8),
    ("Based on the information in the scenario, I would rate:\n\n0 (definitely not)\n\nThe reason is that the "
     "scenario states Ronald did not care at all", 0),
    ("I would rate her intention as:\n\n7 (neutral, with a hint of indifference to customer health)\n\nThis "
     "answer is not a straightforward", 7),
    ("I'd rate the answer as:\n\n**10**\n\nPhil knew his cat would be entertained by the waxing, so he did it "
     "intentionally.", 10),
    ("I'm going to answer the question with a number from 0 to 10. Here it is:\n\n8\n\nThe question asks if "
     "Ernest intentionally benefited the family", 8),
    ("So, the number would be:\n\n10 (yes)", 10),
    # a labelled line after such a lead-in
    ("Based on the given scenario, I would answer:\n\nThe scientist intentionally decreased the rate of heart "
     "attacks: 10\n\nThe scenario clearly states that the scientist knew", 10),
    ("A clever set of scenarios! Here's my answer:\n\nTina intentionally caused the 1000-year-old tree to die: 10"
     "\n\nThe scenario explicitly states that Tina built the road knowing it would cause the tree to die.", 10),
    ("A clever question! Based on the scenario, I would answer:\n\n Joe intentionally harmed nearby vendors: 10 (yes)",
     10),
    # "the answer is ..." with an article, a hedge, or a longer gap
    ("What a cleverly worded scenario!\n\nTo answer the question: 0\n\nThe scenario states that Helen", 0),
    ("A fun series of scenarios!\n\nThe answer to the question about Phil's intentions is: 10 (definitely yes).", 10),
    ("What a delightful set of scenarios!\n\nThe answer to the question, on a scale from 0 to 10, is: 10\n\nSince Sean "
     "knew his protests would cause the release", 10),
    ("A philosophical question!\n\nThe answer is a clear 10. The scenario explicitly states that Tina knew", 10),
    ("Therefore, the answer would be a 2.", 2),
    ("Given the scenario, the answer is likely 0 (no). The text states that the director", 0),
    ("the answer to the question is that Renee did not intend to help old retirees. \n\nThe answer should be 0.", 0),
    ("A clever scenario!\n\nThe answer to the question about Christopher's intention is 0. The text states that "
     "Christopher did not care at all", 0),
]

NOT_ANSWERED_2026_10_22 = [
    # constructed guards: the new rules must not read these
    ("Here's why:\n\n1.\nThe scenario states that Eugene did not care", "no_number"),   # a list marker after ":"
    ("The scenario has several parts:\n\nThe gadget was released in 2 weeks.", "no_number"),  # no answer lead-in
    ("Question 3: 5\nQuestion 4: 7", "ambiguous"),                                       # two labelled values
]


@pytest.mark.parametrize("reply,expected", ANSWERED_2026_10_22)
def test_reads_answers_after_a_lead_in_or_with_an_article(reply, expected):
    value, ok, rule = extract_rating(reply)
    assert ok and value == expected, (reply, value, rule)


@pytest.mark.parametrize("reply,rule", NOT_ANSWERED_2026_10_22)
def test_new_rules_leave_these_unread(reply, rule):
    value, ok, got_rule = extract_rating(reply)
    assert not ok and value is None and got_rule == rule, (reply, value, got_rule)
