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
                ))
    return items


@pytest.fixture
def nonmoral_items() -> list[Item]:
    return make_items("nonmoral")


@pytest.fixture
def foundation_items() -> list[Item]:
    return make_items("foundations")
