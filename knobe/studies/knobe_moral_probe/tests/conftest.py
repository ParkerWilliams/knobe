"""Puts the study folder on sys.path so tests can `import kmp`."""
import sys
from pathlib import Path

STUDY_DIR = Path(__file__).resolve().parents[1]
if str(STUDY_DIR) not in sys.path:
    sys.path.insert(0, str(STUDY_DIR))

import pytest  # noqa: E402

from kmp.items import ARMS, Item, make_item_id  # noqa: E402


def make_items(experiment: str, n_storylines: int = 2, status: str = "approved") -> list[Item]:
    """Every arm x sign for n storylines. Scenarios carry [arm] [sign] markers
    so scripted reviewers in tests can answer by rule."""
    items = []
    for sid in range(1, n_storylines + 1):
        for arm in ARMS[experiment]:
            for sign in ("bad", "good"):
                items.append(Item(
                    item_id=make_item_id(experiment, sid, arm, sign),
                    experiment=experiment, storyline_id=sid, arm=arm, sign=sign,
                    agent=f"Agent{sid}", effect=f"cause a {sign} {arm} outcome",
                    scenario=f"Agent{sid} pursued a goal. [{arm}] [{sign}]",
                    source="new", review_status=status,
                    scaffold="shared" if experiment == "foundations" else None,
                ))
    return items


def make_purpose_storyline(storyline_id: int, arms=("purity",), status: str = "approved") -> list[Item]:
    """A purpose-written foundations storyline: no harm pair (DEFINITIONS §3.3, decision A)."""
    return [Item(
        item_id=make_item_id("foundations", storyline_id, arm, sign),
        experiment="foundations", storyline_id=storyline_id, arm=arm, sign=sign,
        agent=f"Agent{storyline_id}", effect=f"cause a {sign} {arm} outcome",
        scenario=f"Agent{storyline_id} pursued a goal. [{arm}] [{sign}]",
        source="new", review_status=status, scaffold="purpose",
    ) for arm in arms for sign in ("bad", "good")]


@pytest.fixture
def nonmoral_items() -> list[Item]:
    return make_items("nonmoral")


@pytest.fixture
def foundation_items() -> list[Item]:
    return make_items("foundations")


def make_ngo_verbatim_items(n_storylines: int = 2, status: str = "approved") -> list[Item]:
    """Ngo-style verbatim pairs: the agent's name and pronouns change with the
    sign (Bill harms, Robyn helps), as in Ngo et al.'s original text. Scenarios
    carry [moral] [sign] markers like make_items."""
    items = []
    for sid in range(1, n_storylines + 1):
        for sign, agent, pronoun in (("bad", f"Bill{sid}", "he"), ("good", f"Robyn{sid}", "she")):
            items.append(Item(
                item_id=make_item_id("ngo_verbatim", sid, "moral", sign),
                experiment="ngo_verbatim", storyline_id=sid, arm="moral", sign=sign,
                agent=agent, effect=f"cause a {sign} moral outcome",
                scenario=f"{agent} pursued a goal, and {pronoun} knew the outcome. [moral] [{sign}]",
                source="ngo", review_status=status,
            ))
    return items


@pytest.fixture
def ngo_verbatim_items() -> list[Item]:
    return make_ngo_verbatim_items()
