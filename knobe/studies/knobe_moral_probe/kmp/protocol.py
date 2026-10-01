"""Single source of truth for what every model is asked (DESIGN.md sections 4-6).

Wordings are DRAFTS pending review. Every other module reads them from here.
Templates take {agent} (as written mid-sentence) and {effect} (a bare verb
phrase); see kmp.items. Reversed wordings put the high pole at 0 and are
recoded as 10 - x at analysis time (kmp.frame).
is_reversed() is the only supported reversal check; do not infer it from key names.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from knobe import constants

RELEASE = "knobe_moral_probe"                      # seed namespace (knobe.jobs)
RUNNER_VERSION = "knobe_moral_probe_elicit-0.1"
MAX_TOKENS = 10                                    # revisited in the pilot (DESIGN.md section 8)
REVIEW_MAX_TOKENS = 8
# Screening reviewer (a Claude model ID, never a subject). Pin before the first real
# screening run (DESIGN.md section 4); the researcher chooses it. kmp.screen_run refuses
# real runs while this is None, differs from --reviewer-model, or ends in "-latest".
REVIEWER_MODEL: str | None = None
N_PER_WORDING = 8                                  # 3 wordings x 8 = 24 per core question
N_SINGLE = 24
NUMBER_RATE_MIN = 0.90                             # DESIGN.md section 8, gate 1
# Example copying (DESIGN.md section 8, gate 2): the share of answers in EXAMPLE_ANSWERS
# with the worked examples minus the same share in a no-examples run, per model x
# experiment x question; above this it is copying.
COPY_EXCESS_MAX = 0.10                             # proposed; revisit against the pilot and record (DESIGN.md amendment 2026-10-01)

# The frozen frame, split so worked examples can sit between its parts.
INSTRUCTION = constants.RAIMONDI_PROMPT_TEMPLATE.split("\n\n", 1)[0]
BLOCK = constants.CURATION_PROMPT_TEMPLATE        # "Scenario: {scenario}\n\nQuestion: {question}\nAnswer:"


@dataclass(frozen=True)
class Wording:
    key: str
    template: str
    reversed: bool = False


_LEAD = "The action had this side effect: it would {effect}. "
_EXTENT = ", on a scale from 0 (not at all) to 10 (entirely)?"

QUESTIONS: Mapping[str, tuple[Wording, ...]] = MappingProxyType({
    "intentionality": (
        Wording("w1", "Did {agent} intentionally {effect}?"),
        Wording("w2", "To what extent did {agent} {effect} on purpose, on a scale from 0 (not at all) to 10 (completely)?"),
        Wording("w3r", "How intentionally did {agent} {effect}, on a scale from 0 (completely intentionally) "
                       "to 10 (not at all intentionally)?", reversed=True),
    ),
    "blame": (
        Wording("w1", "How blameworthy is {agent} for this, on a scale from 0 (not at all) to 10 (extremely)?"),
        Wording("w2", "How much is {agent} to blame for this, on a scale from 0 (not at all) to 10 (completely)?"),
        Wording("w3r", "How blameworthy is {agent} for this, on a scale from 0 (extremely) to 10 (not at all)?",
                reversed=True),
    ),
    "praise": (
        Wording("w1", "How praiseworthy is {agent} for this, on a scale from 0 (not at all) to 10 (extremely)?"),
        Wording("w2", "How much does {agent} deserve praise for this, on a scale from 0 (not at all) to 10 (completely)?"),
        Wording("w3r", "How praiseworthy is {agent} for this, on a scale from 0 (extremely) to 10 (not at all)?",
                reversed=True),
    ),
    "significance": (
        Wording("w1", _LEAD + "How significant is this side effect? Consider how much weight its impact has and how "
                      "many people or things it reaches. Answer on a scale from 0 (not significant at all) to 10 "
                      "(extremely significant)."),
    ),
    "valence": (
        Wording("w1", _LEAD + "How good or bad is this side effect for those it affects, on a scale from 0 (very bad) "
                      "through 5 (neither good nor bad) to 10 (very good)?"),
    ),
    "domain_moral": (
        Wording("w1", _LEAD + "To what extent is this side effect a matter of morality, meaning other people's welfare "
                      "or rights" + _EXTENT),
    ),
    "domain_prudential": (
        Wording("w1", _LEAD + "To what extent is this side effect a matter of the agent's own interests, such as their "
                      "health, money, reputation or safety" + _EXTENT),
    ),
    "domain_procedural": (
        Wording("w1", _LEAD + "To what extent is this side effect a matter of convention, meaning an arbitrary rule or "
                      "custom such as a dress code or a seating chart, with no one's welfare at stake" + _EXTENT),
    ),
    "fnd_harm": (
        Wording("w1", _LEAD + "To what extent does this side effect involve harm to someone, or care for them, "
                      "physically or emotionally" + _EXTENT),
    ),
    "fnd_fairness": (
        Wording("w1", _LEAD + "To what extent does this side effect involve fair or unfair treatment, such as unequal "
                      "treatment, cheating or going back on a deal" + _EXTENT),
    ),
    "fnd_loyalty": (
        Wording("w1", _LEAD + "To what extent does this side effect involve loyalty to, or betrayal of, one's group, "
                      "team, family or ally" + _EXTENT),
    ),
    "fnd_authority": (
        Wording("w1", _LEAD + "To what extent does this side effect involve respecting or undermining a legitimate "
                      "authority, hierarchy or tradition" + _EXTENT),
    ),
    "fnd_purity": (
        Wording("w1", _LEAD + "To what extent does this side effect involve honoring or violating a taboo, or something "
                      "treated as sacred" + _EXTENT),
    ),
})

CORE = ("intentionality", "blame", "praise")
DOMAIN_CHECKS = ("domain_moral", "domain_prudential", "domain_procedural")
FOUNDATION_CHECKS = ("fnd_harm", "fnd_fairness", "fnd_loyalty", "fnd_authority", "fnd_purity")

# Format-only worked examples (plan amendment 1): unambiguous counting
# questions, identical in front of every prompt, answers spread across the scale.
EXAMPLES: tuple[tuple[str, str, int], ...] = (
    ("A child has two apples and eats both of them.", "How many apples does the child have left?", 0),
    ("A standard die is rolled and lands showing five dots.", "How many dots are showing?", 5),
    ("Nine players arrive for a basketball practice, and no one else comes.",
     "How many players are at the practice?", 9),
)
EXAMPLE_ANSWERS = frozenset(a for _, _, a in EXAMPLES)


def wording(qkey: str, key: str) -> Wording:
    for w in QUESTIONS[qkey]:
        if w.key == key:
            return w
    raise KeyError(f"{qkey}::{key}")


def is_reversed(qkey: str, key: str) -> bool:
    return wording(qkey, key).reversed


def n_samples(qkey: str) -> int:
    return N_PER_WORDING if len(QUESTIONS[qkey]) > 1 else N_SINGLE


def unknown_experiment(experiment: str) -> ValueError:
    """The error every experiment branch raises at its end, so a new or
    misspelled experiment can never fall into another experiment's branch."""
    return ValueError(f"unknown experiment {experiment!r}")


def adapted_counterpart(experiment: str) -> str:
    """The experiment whose questions and screening rule an item's experiment
    uses. ngo_verbatim (Ngo's original text, arm "moral") is asked and screened
    exactly like the adapted moral items, which live in nonmoral."""
    if experiment in ("nonmoral", "foundations"):
        return experiment
    if experiment == "ngo_verbatim":
        return "nonmoral"
    raise unknown_experiment(experiment)


def subject_qkeys(item) -> list[str]:
    """What every subject model is asked about one item (DESIGN.md section 5)."""
    qkeys = [*CORE, "significance"]
    experiment = adapted_counterpart(item.experiment)
    if experiment == "nonmoral":
        return qkeys + list(DOMAIN_CHECKS)
    if experiment == "foundations":
        qkeys.append("fnd_harm")
        if item.arm != "harm":
            qkeys.append(f"fnd_{item.arm}")
        return qkeys
    raise unknown_experiment(experiment)


def screening_qkeys(item) -> list[str]:
    """What the reviewer is asked about one item (DESIGN.md section 4)."""
    experiment = adapted_counterpart(item.experiment)
    if experiment == "nonmoral":
        return ["valence", *DOMAIN_CHECKS]
    if experiment == "foundations":
        return ["valence", *FOUNDATION_CHECKS]
    raise unknown_experiment(experiment)
