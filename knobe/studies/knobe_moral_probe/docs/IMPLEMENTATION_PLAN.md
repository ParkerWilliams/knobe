# knobe_moral_probe pipeline: implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the study's pipeline, from items to screening to prompts to elicitation to checks to the analysis frame, and verify it end to end with the fake engine and a scripted reviewer. Real stimuli can then go straight through it.

**Architecture:** A small package `kmp/` inside `studies/knobe_moral_probe/`. `protocol.py` is the single source of truth for question wordings, anchors, worked examples and sample counts. Everything else reads it. Lower layers are imported from `src/knobe/`, not copied: the vLLM/fake engine, the model registry, seed derivation, the result schema, the rating parser, and the curation client and retry code.

**Tech Stack:** Python 3.13, pydantic, pandas, numpy, pytest; `knobe` (installed editable from `src/`); vLLM on the cluster only.

**Scope:** This plan builds and tests the software on synthetic items. Writing the real definitions, checklist and items is a separate plan, written once this pipeline can screen them (DESIGN.md §3.4).

**Conventions for every task:**
- Work on branch `knobe_moral_probe`.
- Prefix commit messages with `[knobe_moral_probe]`, with no AI co-author trailer (user's global CLAUDE.md).
- Run tests from the repo root:
  `.venv/bin/python -m pytest studies/knobe_moral_probe/tests -q`.
  The repo's `pyproject.toml` applies `filterwarnings = ["error"]`, so any warning fails a test. Avoid `groupby().apply` and constant-input correlations.
- Run CLIs from the study folder:
  `cd studies/knobe_moral_probe && ../../.venv/bin/python -m kmp.<module> ...`.

## Amendments to DESIGN.md this plan makes (approved 2026-09-28)

1. **Worked examples are format-only** (DESIGN.md §6 said they "use the same question wording as the real item"). With 14 question types, same-wording examples need 42 hand-judged answers. Most of them, like domain and foundation ratings, have no obvious value, so the examples would teach judgments. This plan uses three counting questions whose answers are unambiguous (0, 5, 9) in front of every prompt. They show the answer format and carry no information about how to judge anything. If you reject this, only the `EXAMPLES` data in Task 3 changes.
2. **The reviewer's temperature 0 needs a small reimplementation.** `knobe.curate.AnthropicClient.complete` takes no temperature. Task 8 subclasses it and reimplements `complete()` (15 lines) to pass `temperature=0.0`. This is flagged per CLAUDE.md §7. Whether the pinned reviewer model accepts `temperature` is checked on the first real call.
3. **The README's "reads none of the earlier outputs" gets one exception:** the design-stage power script (Task 12) reads the MF pilot's committed `sign_wcb_parsed.csv`.

## File structure

```
studies/knobe_moral_probe/
├── .gitignore                 elicitation dumps stay local (CLAUDE.md §3)
├── kmp/
│   ├── __init__.py
│   ├── items.py               Item schema, kmp- IDs, CSV I/O, design checks
│   ├── protocol.py            wordings, anchors, examples, sample counts, constants
│   ├── prompts.py             prompt text + IDs for subject models and reviewer
│   ├── screen.py              reviewer runner, pass rule, pair selection, CLI
│   ├── elicit.py              job building, requests/results, CLI
│   ├── frame.py               results → analysis DataFrame (anchor recoding)
│   └── checks.py              pre-analysis gate tables, CLI
├── analysis/
│   └── power_basis.py         DESIGN.md §9 power table, committed
└── tests/
    ├── conftest.py            sys.path + synthetic item factory
    ├── test_items.py
    ├── test_protocol.py
    ├── test_prompts.py
    ├── test_elicit.py
    ├── test_screen.py
    ├── test_frame.py
    ├── test_checks.py
    └── test_pipeline.py       end-to-end: items → screen → elicit → frame → checks
```

---

### Task 1: Package skeleton and test setup

**Files:**
- Create: `studies/knobe_moral_probe/kmp/__init__.py`
- Create: `studies/knobe_moral_probe/tests/conftest.py`
- Create: `studies/knobe_moral_probe/tests/test_smoke.py`
- Create: `studies/knobe_moral_probe/.gitignore`

- [ ] **Step 1: Create the package marker**

`studies/knobe_moral_probe/kmp/__init__.py`:
```python
"""knobe_moral_probe pipeline package. See ../docs/DESIGN.md."""
```

- [ ] **Step 2: Create conftest.py (path setup only; the item factory comes in Task 2)**

`studies/knobe_moral_probe/tests/conftest.py`:
```python
"""Puts the study folder on sys.path so tests can `import kmp`."""
import sys
from pathlib import Path

STUDY_DIR = Path(__file__).resolve().parents[1]
if str(STUDY_DIR) not in sys.path:
    sys.path.insert(0, str(STUDY_DIR))
```

- [ ] **Step 3: Write a smoke test**

`studies/knobe_moral_probe/tests/test_smoke.py`:
```python
def test_kmp_importable():
    import kmp
    assert kmp.__doc__.startswith("knobe_moral_probe")


def test_knobe_importable():
    from knobe.parsing import parse_rating
    assert parse_rating(" 7")[0] == 7
```

- [ ] **Step 4: Run it**

Run: `.venv/bin/python -m pytest studies/knobe_moral_probe/tests -q`
Expected: `2 passed`

- [ ] **Step 5: Add .gitignore**

`studies/knobe_moral_probe/.gitignore`:
```
# Per-response elicitation dumps are regenerable from committed code + the
# release string; they are published to results_dist/, not committed here
# (repo CLAUDE.md section 3). Screening raw files ARE committed: they are
# small and are the provenance the pilots lacked.
outputs/elicit/*.jsonl
outputs/checks/*/
__pycache__/
```

- [ ] **Step 6: Commit**

```bash
git add studies/knobe_moral_probe/kmp studies/knobe_moral_probe/tests studies/knobe_moral_probe/.gitignore
git commit -m "[knobe_moral_probe] package skeleton and test setup"
```

---

### Task 2: Items: schema, IDs, CSV I/O, design checks

**Files:**
- Create: `studies/knobe_moral_probe/kmp/items.py`
- Modify: `studies/knobe_moral_probe/tests/conftest.py` (add the factory)
- Test: `studies/knobe_moral_probe/tests/test_items.py`

- [ ] **Step 1: Add the synthetic item factory to conftest.py**

Append to `studies/knobe_moral_probe/tests/conftest.py`:
```python
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
```

- [ ] **Step 2: Write the failing tests**

`studies/knobe_moral_probe/tests/test_items.py`:
```python
import pytest
from pydantic import ValidationError

from conftest import make_items
from kmp.items import Item, design_problems, load_items, make_item_id, write_items


def _item(**over):
    base = dict(item_id="kmp-nm-007-prudential-bad", experiment="nonmoral", storyline_id=7,
                arm="prudential", sign="bad", agent="Bill", effect="ruin his own savings",
                scenario="Bill did X.", source="new")
    base.update(over)
    return Item(**base)


def test_make_item_id():
    assert make_item_id("nonmoral", 7, "prudential", "bad") == "kmp-nm-007-prudential-bad"
    assert make_item_id("foundations", 12, "purity", "good") == "kmp-mf-012-purity-good"


def test_item_default_status_is_draft():
    assert _item().review_status == "draft"


def test_item_rejects_wrong_id():
    with pytest.raises(ValidationError, match="should be"):
        _item(item_id="moral-07-bad")


def test_item_rejects_arm_outside_experiment():
    with pytest.raises(ValidationError, match="not in"):
        _item(arm="loyalty", item_id="kmp-nm-007-loyalty-bad")


def test_item_rejects_blank_or_padded_text():
    with pytest.raises(ValidationError, match="whitespace"):
        _item(effect=" ruin his own savings")


def test_csv_roundtrip(tmp_path, nonmoral_items):
    path = tmp_path / "items.csv"
    write_items(nonmoral_items, path)
    assert sorted(load_items(path), key=lambda i: i.item_id) == sorted(nonmoral_items, key=lambda i: i.item_id)


def test_design_problems_clean(nonmoral_items, foundation_items):
    assert design_problems(nonmoral_items) == []
    assert design_problems(foundation_items) == []


def test_design_problems_missing_partner(nonmoral_items):
    problems = design_problems([i for i in nonmoral_items if i.item_id != "kmp-nm-001-moral-good"])
    assert any("(1, 'moral')" in p and "needs exactly one bad and one good" in p for p in problems)


def test_design_problems_agent_mismatch(nonmoral_items):
    items = [i.model_copy(update={"agent": "Someone"}) if i.item_id == "kmp-nm-001-moral-good" else i
             for i in nonmoral_items]
    assert any("agents differ" in p for p in design_problems(items))


def test_design_problems_duplicate_and_mixed(nonmoral_items):
    mixed = nonmoral_items + [nonmoral_items[0]] + make_items("foundations", 1)
    problems = design_problems(mixed)
    assert any("duplicate item_id" in p for p in problems)
    assert any("mixed experiments" in p for p in problems)
```

- [ ] **Step 3: Run to verify failure**

Run: `.venv/bin/python -m pytest studies/knobe_moral_probe/tests/test_items.py -q`
Expected: collection error, `ModuleNotFoundError: No module named 'kmp.items'`

- [ ] **Step 4: Implement items.py**

`studies/knobe_moral_probe/kmp/items.py`:
```python
"""Stimulus items: schema, kmp- IDs, CSV I/O, design checks (DESIGN.md section 3).

One row is one version (bad or good) of one side effect. Versions pair up
by (experiment, storyline_id, arm): exactly one bad and one good, same
agent. storyline_id is the cluster unit for inference; in the foundations
experiment one storyline carries a harm pair plus one or more foundation
pairs (shared scaffolds, DESIGN.md section 3.3).

`agent` is the agent as written mid-sentence ("Bill", "the CEO"); `effect`
is the side effect as a bare verb phrase ("injure children"), so question
wordings can be rendered as "Did {agent} intentionally {effect}?".
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

Experiment = Literal["nonmoral", "foundations"]
Sign = Literal["bad", "good"]
Source = Literal["ngo", "pilot", "new"]
ReviewStatus = Literal["draft", "approved", "rejected"]

ARMS: dict[str, tuple[str, ...]] = {
    "nonmoral": ("moral", "prudential", "procedural"),
    "foundations": ("harm", "fairness", "loyalty", "authority", "purity"),
}
EXPERIMENT_CODE = {"nonmoral": "nm", "foundations": "mf"}
ID_PREFIX = "kmp-"
FIELDS = ["item_id", "experiment", "storyline_id", "arm", "sign", "agent",
          "effect", "scenario", "source", "review_status"]


def make_item_id(experiment: str, storyline_id: int, arm: str, sign: str) -> str:
    return f"{ID_PREFIX}{EXPERIMENT_CODE[experiment]}-{storyline_id:03d}-{arm}-{sign}"


class Item(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    item_id: str
    experiment: Experiment
    storyline_id: int
    arm: str
    sign: Sign
    agent: str
    effect: str
    scenario: str
    source: Source
    review_status: ReviewStatus = "draft"

    @model_validator(mode="after")
    def _check(self) -> "Item":
        if self.arm not in ARMS[self.experiment]:
            raise ValueError(f"{self.item_id}: arm {self.arm!r} not in {ARMS[self.experiment]}")
        expected = make_item_id(self.experiment, self.storyline_id, self.arm, self.sign)
        if self.item_id != expected:
            raise ValueError(f"item_id {self.item_id!r} should be {expected!r}")
        for name in ("agent", "effect", "scenario"):
            value = getattr(self, name)
            if not value.strip() or value != value.strip():
                raise ValueError(f"{self.item_id}: {name} is empty or has surrounding whitespace")
        return self


def pair_key(item: Item) -> tuple[str, int, str]:
    return (item.experiment, item.storyline_id, item.arm)


def load_items(path: str | Path) -> list[Item]:
    with open(path, newline="", encoding="utf-8") as fh:
        return [Item(**row) for row in csv.DictReader(fh)]


def write_items(items: list[Item], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        for item in sorted(items, key=lambda i: i.item_id):
            writer.writerow(item.model_dump())


def design_problems(items: list[Item]) -> list[str]:
    """Every structural problem, as readable strings. Empty list = clean."""
    problems = [f"duplicate item_id {k}" for k, n in sorted(Counter(i.item_id for i in items).items()) if n > 1]
    experiments = sorted({i.experiment for i in items})
    if len(experiments) > 1:
        problems.append(f"mixed experiments in one file: {experiments}")
    pairs: dict[tuple, list[Item]] = defaultdict(list)
    for item in items:
        pairs[pair_key(item)].append(item)
    for key, members in sorted(pairs.items()):
        signs = sorted(m.sign for m in members)
        if signs != ["bad", "good"]:
            problems.append(f"pair {key[1:]} has signs {signs}, needs exactly one bad and one good")
        elif members[0].agent != members[1].agent:
            problems.append(f"pair {key[1:]}: agents differ ({members[0].agent!r} vs {members[1].agent!r})")
    return problems
```

- [ ] **Step 5: Run to verify pass**

Run: `.venv/bin/python -m pytest studies/knobe_moral_probe/tests -q`
Expected: `12 passed`

- [ ] **Step 6: Commit**

```bash
git add studies/knobe_moral_probe/kmp/items.py studies/knobe_moral_probe/tests
git commit -m "[knobe_moral_probe] item schema, kmp- IDs, CSV I/O and design checks"
```

---

### Task 3: Protocol: wordings, anchors, examples, sample counts

**Files:**
- Create: `studies/knobe_moral_probe/kmp/protocol.py`
- Test: `studies/knobe_moral_probe/tests/test_protocol.py`

The wordings below are drafts for your review (DESIGN.md §12). Changing any
of them later means editing this file only.

- [ ] **Step 1: Write the failing tests**

`studies/knobe_moral_probe/tests/test_protocol.py`:
```python
from knobe import constants

from conftest import make_items
from kmp import protocol


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
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest studies/knobe_moral_probe/tests/test_protocol.py -q`
Expected: collection error, `cannot import name 'protocol'`

- [ ] **Step 3: Implement protocol.py**

`studies/knobe_moral_probe/kmp/protocol.py`:
```python
"""Single source of truth for what every model is asked (DESIGN.md sections 4-6).

Wordings are DRAFTS pending review. Every other module reads them from here.
Templates take {agent} (as written mid-sentence) and {effect} (a bare verb
phrase); see kmp.items. Reversed wordings put the high pole at 0 and are
recoded as 10 - x at analysis time (kmp.frame).
"""
from __future__ import annotations

from dataclasses import dataclass

from knobe import constants

RELEASE = "knobe_moral_probe"                      # seed namespace (knobe.jobs)
RUNNER_VERSION = "knobe_moral_probe_elicit-0.1"
MAX_TOKENS = 10                                    # revisited in the pilot (DESIGN.md section 8)
REVIEW_MAX_TOKENS = 8
N_PER_WORDING = 8                                  # 3 wordings x 8 = 24 per core question
N_SINGLE = 24
NUMBER_RATE_MIN = 0.90                             # DESIGN.md section 8, gate 1
COPY_SHARE_MAX = 0.5                               # example-copying flag; 3 of 11 values ~ 0.27 by chance

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

QUESTIONS: dict[str, tuple[Wording, ...]] = {
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
}

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


def subject_qkeys(item) -> list[str]:
    """What every subject model is asked about one item (DESIGN.md section 5)."""
    qkeys = [*CORE, "significance"]
    if item.experiment == "nonmoral":
        return qkeys + list(DOMAIN_CHECKS)
    qkeys.append("fnd_harm")
    if item.arm != "harm":
        qkeys.append(f"fnd_{item.arm}")
    return qkeys


def screening_qkeys(item) -> list[str]:
    """What the reviewer is asked about one item (DESIGN.md section 4)."""
    checks = DOMAIN_CHECKS if item.experiment == "nonmoral" else FOUNDATION_CHECKS
    return ["valence", *checks]
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest studies/knobe_moral_probe/tests -q`
Expected: `23 passed`

- [ ] **Step 5: Commit**

```bash
git add studies/knobe_moral_probe/kmp/protocol.py studies/knobe_moral_probe/tests/test_protocol.py
git commit -m "[knobe_moral_probe] protocol: draft wordings, reversed anchors, format-only examples, sample counts"
```

---

### Task 4: Prompts: text and IDs

**Files:**
- Create: `studies/knobe_moral_probe/kmp/prompts.py`
- Test: `studies/knobe_moral_probe/tests/test_prompts.py`

- [ ] **Step 1: Write the failing tests**

`studies/knobe_moral_probe/tests/test_prompts.py`:
```python
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
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest studies/knobe_moral_probe/tests/test_prompts.py -q`
Expected: collection error, `cannot import name 'prompts'`

- [ ] **Step 3: Implement prompts.py**

`studies/knobe_moral_probe/kmp/prompts.py`:
```python
"""Prompt text and IDs (DESIGN.md section 6).

Rule: identical text for every model; only the wrapper differs (raw
completion for pretrained, one chat user message for instruct -- applied
in kmp.elicit). Subject prompts carry the worked examples; reviewer
(screening) prompts don't.

prompt_id = "{item_id}::{qkey}::{wording_key}::{fmt}". The format is part
of the ID so raw and chat samples get independent seeds (knobe.jobs).
"""
from __future__ import annotations

from dataclasses import dataclass

from kmp import protocol
from kmp.items import Item


@dataclass(frozen=True)
class PromptSpec:
    stem: str            # item_id::qkey::wording_key (format appended per model)
    item_id: str
    qkey: str
    wording_key: str
    reversed: bool
    text: str
    n_samples: int


@dataclass(frozen=True)
class ScreeningPrompt:
    item_id: str
    qkey: str
    text: str


def render_question(item: Item, template: str) -> str:
    return template.format(agent=item.agent, effect=item.effect)


def render_text(scenario: str, question: str, examples=protocol.EXAMPLES) -> str:
    parts = [protocol.INSTRUCTION]
    parts += [f"{protocol.BLOCK.format(scenario=s, question=q)} {a}" for s, q, a in examples]
    parts.append(protocol.BLOCK.format(scenario=scenario, question=question))
    return "\n\n".join(parts)


def build_subject_prompts(items: list[Item], examples=protocol.EXAMPLES) -> list[PromptSpec]:
    specs = []
    for item in items:
        for qkey in protocol.subject_qkeys(item):
            for w in protocol.QUESTIONS[qkey]:
                specs.append(PromptSpec(
                    stem=f"{item.item_id}::{qkey}::{w.key}", item_id=item.item_id, qkey=qkey,
                    wording_key=w.key, reversed=w.reversed,
                    text=render_text(item.scenario, render_question(item, w.template), examples),
                    n_samples=protocol.n_samples(qkey),
                ))
    return specs


def build_screening_prompts(items: list[Item]) -> list[ScreeningPrompt]:
    return [
        ScreeningPrompt(item.item_id, qkey,
                        render_text(item.scenario, render_question(item, protocol.QUESTIONS[qkey][0].template),
                                    examples=()))
        for item in items for qkey in protocol.screening_qkeys(item)
    ]


def format_for_model(model_key: str) -> str:
    return "chat" if model_key.endswith("-instruct") else "raw"


def prompt_id(stem: str, fmt: str) -> str:
    return f"{stem}::{fmt}"


def parse_prompt_id(pid: str) -> tuple[str, str, str, str]:
    item_id, qkey, wording_key, fmt = pid.split("::")
    return item_id, qkey, wording_key, fmt
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest studies/knobe_moral_probe/tests -q`
Expected: `30 passed`

- [ ] **Step 5: Commit**

```bash
git add studies/knobe_moral_probe/kmp/prompts.py studies/knobe_moral_probe/tests/test_prompts.py
git commit -m "[knobe_moral_probe] prompt text and IDs; identical text across stages"
```

---

### Task 5: Elicitation: jobs, requests, results (pure functions)

**Files:**
- Create: `studies/knobe_moral_probe/kmp/elicit.py`
- Test: `studies/knobe_moral_probe/tests/test_elicit.py`

- [ ] **Step 1: Write the failing tests**

`studies/knobe_moral_probe/tests/test_elicit.py`:
```python
from knobe.elicit_vllm import EngineResponse

from conftest import make_items
from kmp import elicit, prompts, protocol

KEYS = ["gemma-2-9b-pretrained", "gemma-2-9b-instruct"]


def _jobs():
    return elicit.build_jobs(prompts.build_subject_prompts(make_items("nonmoral", 1)[:1]), KEYS)


def test_job_counts_and_formats():
    jobs = _jobs()
    per_model = 9 * protocol.N_PER_WORDING + 4 * protocol.N_SINGLE
    assert len(jobs) == 2 * per_model
    assert {j.fmt for j in jobs if j.model_key.endswith("pretrained")} == {"raw"}
    assert {j.fmt for j in jobs if j.model_key.endswith("instruct")} == {"chat"}
    assert len({j.job_id for j in jobs}) == len(jobs)


def test_same_text_across_stages():
    jobs = _jobs()
    raw = {j.prompt_id.rsplit("::", 1)[0]: j.text for j in jobs if j.fmt == "raw"}
    chat = {j.prompt_id.rsplit("::", 1)[0]: j.text for j in jobs if j.fmt == "chat"}
    assert raw == chat


def test_to_request_wrappers():
    jobs = _jobs()
    raw = next(j for j in jobs if j.fmt == "raw")
    chat = next(j for j in jobs if j.fmt == "chat")
    r, c = elicit.to_request(raw, 10), elicit.to_request(chat, 10)
    assert r.text == raw.text and r.messages is None
    assert c.messages == [{"role": "user", "content": chat.text}] and c.text is None
    assert not r.want_first_token_logprobs and not c.want_first_token_logprobs
    assert 0.85 <= r.temperature <= 1.15


def test_seeds_are_deterministic():
    j = _jobs()[0]
    assert elicit.to_request(j, 10).seed == elicit.to_request(j, 10).seed


def test_to_result_parses_or_records_failure():
    j = _jobs()[0]
    req = elicit.to_request(j, 10)
    ok = elicit.to_result(j, req, EngineResponse(j.job_id, " 7", None), "rev")
    bad = elicit.to_result(j, req, EngineResponse(j.job_id, " _______", None), "rev")
    assert (ok.parsed_rating, ok.parse_ok) == (7, True)
    assert (bad.parsed_rating, bad.parse_ok) == (None, False)
    assert ok.runner_version == protocol.RUNNER_VERSION and ok.logprobs_0_10 is None
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest studies/knobe_moral_probe/tests/test_elicit.py -q`
Expected: collection error, `cannot import name 'elicit'`

- [ ] **Step 3: Implement the pure functions**

`studies/knobe_moral_probe/kmp/elicit.py`:
```python
"""Elicitation (DESIGN.md section 6): every model, both experiments, one script.

Reuses knobe's engine (vLLM on the cluster, FakeEngine for tests), model
registry, seed derivation (sha256 of RELEASE, prompt_id, model_key,
sample_idx) and ResultRecord. The readout is the written number only
(parse_rating); logprobs are not requested, which also skips vLLM's 11
forced-scoring passes per prompt.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from knobe.elicit_vllm import EngineRequest, EngineResponse
from knobe.jobs import derive_temperature_and_seed
from knobe.parsing import parse_rating
from knobe.registry import model_key_for
from knobe.schemas import ResultRecord

from kmp import prompts, protocol
from kmp.prompts import PromptSpec

FAMILIES = ("llama-3.1-8b", "mistral-7b-v0.1", "gemma-2-9b")
MODEL_KEYS = tuple(model_key_for(f, t) for f in FAMILIES for t in ("pretrained", "finetuned"))


@dataclass(frozen=True)
class Job:
    prompt_id: str
    model_key: str
    sample_idx: int
    text: str
    fmt: str

    @property
    def job_id(self) -> str:
        return f"{self.prompt_id}::{self.model_key}::{self.sample_idx}"


def build_jobs(specs: list[PromptSpec], model_keys: list[str]) -> list[Job]:
    jobs = []
    for spec in specs:
        for model_key in model_keys:
            fmt = prompts.format_for_model(model_key)
            pid = prompts.prompt_id(spec.stem, fmt)
            jobs += [Job(pid, model_key, s, spec.text, fmt) for s in range(spec.n_samples)]
    return jobs


def to_request(job: Job, max_tokens: int) -> EngineRequest:
    temperature, seed = derive_temperature_and_seed(protocol.RELEASE, job.prompt_id, job.model_key, job.sample_idx)
    wrapper = {"text": job.text} if job.fmt == "raw" else {"messages": [{"role": "user", "content": job.text}]}
    return EngineRequest(job_id=job.job_id, prompt_id=job.prompt_id, temperature=temperature, seed=seed,
                         max_tokens=max_tokens, want_first_token_logprobs=False, **wrapper)


def to_result(job: Job, request: EngineRequest, response: EngineResponse, model_revision: str) -> ResultRecord:
    value, ok, raw = parse_rating(response.raw_response)
    return ResultRecord(
        job_id=job.job_id, prompt_id=job.prompt_id, model_key=job.model_key, sample_idx=job.sample_idx,
        temperature=request.temperature, seed=request.seed, raw_response=raw,
        parsed_rating=value, parse_ok=ok, parse_method="regex", logprobs_0_10=None,
        model_revision=model_revision, runner_version=protocol.RUNNER_VERSION, timestamp=time.time(),
    )
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest studies/knobe_moral_probe/tests -q`
Expected: `35 passed`

- [ ] **Step 5: Commit**

```bash
git add studies/knobe_moral_probe/kmp/elicit.py studies/knobe_moral_probe/tests/test_elicit.py
git commit -m "[knobe_moral_probe] elicitation jobs, raw/chat requests, parsed results"
```

---

### Task 6: Elicitation CLI with checkpoint and resume

**Files:**
- Modify: `studies/knobe_moral_probe/kmp/elicit.py` (add `main`)
- Test: `studies/knobe_moral_probe/tests/test_elicit.py` (append)

- [ ] **Step 1: Write the failing tests**

Append to `studies/knobe_moral_probe/tests/test_elicit.py`:
```python
import pytest  # noqa: E402

from knobe.schemas import ResultRecord, read_jsonl  # noqa: E402
from kmp.items import write_items  # noqa: E402


def _run(tmp_path, items, *extra):
    items_path, out = tmp_path / "items.csv", tmp_path / "out.jsonl"
    write_items(items, items_path)
    code = elicit.main(["--items", str(items_path), "--out", str(out), "--engine", "fake",
                        "--model-keys", ",".join(KEYS), *extra])
    return code, out


def test_main_writes_every_job_and_resumes(tmp_path):
    items = make_items("nonmoral", 1)[:2]
    code, out = _run(tmp_path, items)
    rows = read_jsonl(out, ResultRecord)
    assert code == 0
    assert len(rows) == len(elicit.build_jobs(prompts.build_subject_prompts(items), KEYS))
    assert all(r.parse_ok for r in rows)                       # FakeEngine always writes a number
    code, _ = _run(tmp_path, items)
    assert code == 0 and len(read_jsonl(out, ResultRecord)) == len(rows)


def test_main_refuses_unapproved_items(tmp_path):
    code, _ = _run(tmp_path, make_items("nonmoral", 1, status="draft")[:2])
    assert code == 2


def test_main_refuses_unknown_model_key(tmp_path):
    items_path = tmp_path / "items.csv"
    write_items(make_items("nonmoral", 1)[:2], items_path)
    with pytest.raises(SystemExit):
        elicit.main(["--items", str(items_path), "--out", str(tmp_path / "o.jsonl"), "--model-keys", "gpt-x"])
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest studies/knobe_moral_probe/tests/test_elicit.py -q`
Expected: FAIL, `AttributeError: module 'kmp.elicit' has no attribute 'main'`

- [ ] **Step 3: Implement main**

Add to the imports at the top of `studies/knobe_moral_probe/kmp/elicit.py`:
```python
import argparse
import sys
from pathlib import Path

from knobe.elicit_vllm import build_engine, default_registry_path, resolve_model_id
from knobe.registry import load_registry
from knobe.schemas import append_jsonl, read_jsonl

from kmp.items import design_problems, load_items
```

Append to `studies/knobe_moral_probe/kmp/elicit.py`:
```python
def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="knobe_moral_probe elicitation")
    p.add_argument("--items", required=True, type=Path, help="selected items CSV (from kmp.screen)")
    p.add_argument("--out", required=True, type=Path, help="results JSONL (appended; resumable)")
    p.add_argument("--engine", default="fake", choices=["fake", "vllm", "hf"])
    p.add_argument("--model-keys", help=f"comma-separated subset of {', '.join(MODEL_KEYS)}")
    p.add_argument("--registry", type=Path, help="models.yaml (default: the repo's configs/models.yaml)")
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--max-tokens", type=int, default=protocol.MAX_TOKENS)
    args = p.parse_args(argv)

    model_keys = [k.strip() for k in args.model_keys.split(",")] if args.model_keys else list(MODEL_KEYS)
    unknown = sorted(set(model_keys) - set(MODEL_KEYS))
    if unknown:
        p.error(f"unknown model key(s) {unknown}")

    items = load_items(args.items)
    problems = design_problems(items) + [f"{i.item_id} is {i.review_status}, not approved"
                                         for i in items if i.review_status != "approved"]
    if problems:
        print("refusing to run:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 2

    jobs = build_jobs(prompts.build_subject_prompts(items), model_keys)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    done = ({r.job_id for r in read_jsonl(args.out, ResultRecord)}
            if args.out.exists() and args.out.stat().st_size else set())
    remaining = [j for j in jobs if j.job_id not in done]
    print(f"{len(done)} done, {len(remaining)} remaining of {len(jobs)} jobs")
    if not remaining:
        return 0

    registry = load_registry(args.registry or default_registry_path())
    engine = build_engine(args.engine)
    by_model: dict[str, list[Job]] = {}
    for job in remaining:
        by_model.setdefault(job.model_key, []).append(job)

    with open(args.out, "a", encoding="utf-8") as fh:
        for model_key, model_jobs in by_model.items():
            model_id, _family, pinned = resolve_model_id(model_key, registry)
            revision = engine.load(model_id, revision=pinned)
            print(f"[elicit] {model_key} ({model_id}@{revision}): {len(model_jobs)} jobs")
            for start in range(0, len(model_jobs), args.batch_size):
                batch = model_jobs[start:start + args.batch_size]
                requests = [to_request(j, args.max_tokens) for j in batch]
                responses = {r.job_id: r for r in engine.generate(requests)}
                for job, request in zip(batch, requests):
                    response = responses.get(job.job_id)
                    if response is None:
                        print(f"ERROR: no response for {job.job_id}", file=sys.stderr)
                        continue
                    append_jsonl(to_result(job, request, response, revision), fh)
                fh.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest studies/knobe_moral_probe/tests -q`
Expected: `38 passed`

- [ ] **Step 5: Commit**

```bash
git add studies/knobe_moral_probe/kmp/elicit.py studies/knobe_moral_probe/tests/test_elicit.py
git commit -m "[knobe_moral_probe] elicitation CLI with checkpoint/resume and approval guard"
```

---

### Task 7: Screening: pass rule and pair selection

**Files:**
- Create: `studies/knobe_moral_probe/kmp/screen.py`
- Test: `studies/knobe_moral_probe/tests/test_screen.py`

- [ ] **Step 1: Write the failing tests**

`studies/knobe_moral_probe/tests/test_screen.py`:
```python
from conftest import make_items
from kmp import screen


def _get(items, arm, sign, sid=1):
    return next(i for i in items if i.arm == arm and i.sign == sign and i.storyline_id == sid)


NM_GOOD_SCORES = {"domain_moral": 2, "domain_prudential": 8, "domain_procedural": 1}


def test_valence_thresholds(nonmoral_items):
    bad, good = _get(nonmoral_items, "prudential", "bad"), _get(nonmoral_items, "prudential", "good")
    assert screen.item_failures(bad, {"valence": 2, **NM_GOOD_SCORES}) == []
    assert "valence 5 > 3 for a bad item" in screen.item_failures(bad, {"valence": 5, **NM_GOOD_SCORES})
    assert "valence 6 < 7 for a good item" in screen.item_failures(good, {"valence": 6, **NM_GOOD_SCORES})


def test_nonmoral_domain_must_be_high_and_highest(nonmoral_items):
    item = _get(nonmoral_items, "prudential", "bad")
    low = {"valence": 1, "domain_moral": 2, "domain_prudential": 5, "domain_procedural": 1}
    tie = {"valence": 1, "domain_moral": 8, "domain_prudential": 8, "domain_procedural": 1}
    assert "domain_prudential 5 < 6" in screen.item_failures(item, low)
    assert "domain_prudential is not the highest domain rating" in screen.item_failures(item, tie)


def test_foundation_must_beat_harm(foundation_items):
    item = _get(foundation_items, "loyalty", "bad")
    base = {"valence": 1, "fnd_fairness": 1, "fnd_authority": 1, "fnd_purity": 1}
    assert screen.item_failures(item, {**base, "fnd_loyalty": 8, "fnd_harm": 3}) == []
    assert "fnd_loyalty 7 not higher than fnd_harm 7" in screen.item_failures(item, {**base, "fnd_loyalty": 7, "fnd_harm": 7})


def test_harm_control_needs_harm(foundation_items):
    item = _get(foundation_items, "harm", "bad")
    assert "fnd_harm 4 < 6" in screen.item_failures(item, {"valence": 1, "fnd_harm": 4})


def test_unparsed_is_a_named_failure(nonmoral_items):
    item = _get(nonmoral_items, "moral", "bad")
    assert "valence unparsed" in screen.item_failures(item, {"valence": None, "domain_moral": 9,
                                                            "domain_prudential": 1, "domain_procedural": 1})


def test_select_pairs_drops_the_whole_pair(nonmoral_items):
    pair = [_get(nonmoral_items, "prudential", "bad"), _get(nonmoral_items, "prudential", "good")]
    scores = {pair[0].item_id: {"valence": 1, **NM_GOOD_SCORES},
              pair[1].item_id: {"valence": 4, **NM_GOOD_SCORES}}
    selected, report = screen.select_pairs(pair, scores)
    assert selected == []
    assert [r["pair_passed"] for r in report] == [False, False]
    assert report[1]["failures"] == "valence 4 < 7 for a good item"


def test_select_pairs_flags_missing_partner(nonmoral_items):
    selected, report = screen.select_pairs([_get(nonmoral_items, "moral", "bad")], {})
    assert selected == [] and "partner not approved" in report[0]["failures"]
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest studies/knobe_moral_probe/tests/test_screen.py -q`
Expected: collection error, `cannot import name 'screen'`

- [ ] **Step 3: Implement the pass rule**

`studies/knobe_moral_probe/kmp/screen.py`:
```python
"""Screening (DESIGN.md section 4): a reviewer model rates every approved
item; pairs pass only if both versions pass.

Pass rule per item:
  valence              bad <= 3, good >= 7
  nonmoral item        intended domain >= 6 and strictly highest of the three
  foundation item      intended foundation >= 6 and strictly higher than harm
  harm control         harm >= 6
Unparsed reviewer answers are named failures, never silently dropped.
"""
from __future__ import annotations

from collections import defaultdict

from kmp import protocol
from kmp.items import Item, pair_key

VALENCE_BAD_MAX = 3
VALENCE_GOOD_MIN = 7
TARGET_MIN = 6


def intended_check(item: Item) -> str:
    return f"domain_{item.arm}" if item.experiment == "nonmoral" else f"fnd_{item.arm}"


def item_failures(item: Item, scores: dict[str, int | None]) -> list[str]:
    failures = []
    v = scores.get("valence")
    if v is None:
        failures.append("valence unparsed")
    elif item.sign == "bad" and v > VALENCE_BAD_MAX:
        failures.append(f"valence {v} > {VALENCE_BAD_MAX} for a bad item")
    elif item.sign == "good" and v < VALENCE_GOOD_MIN:
        failures.append(f"valence {v} < {VALENCE_GOOD_MIN} for a good item")

    target_key = intended_check(item)
    t = scores.get(target_key)
    if t is None:
        failures.append(f"{target_key} unparsed")
        return failures
    if t < TARGET_MIN:
        failures.append(f"{target_key} {t} < {TARGET_MIN}")

    if item.experiment == "nonmoral":
        others = [scores.get(k) for k in protocol.DOMAIN_CHECKS if k != target_key]
        if any(o is None for o in others):
            failures.append("a domain rating is unparsed")
        elif any(o >= t for o in others):
            failures.append(f"{target_key} is not the highest domain rating")
    elif item.arm != "harm":
        h = scores.get("fnd_harm")
        if h is None:
            failures.append("fnd_harm unparsed")
        elif t <= h:
            failures.append(f"{target_key} {t} not higher than fnd_harm {h}")
    return failures


def select_pairs(items: list[Item], scores_by_item: dict[str, dict[str, int | None]]) -> tuple[list[Item], list[dict]]:
    pairs: dict[tuple, list[Item]] = defaultdict(list)
    for item in items:
        pairs[pair_key(item)].append(item)
    selected, report = [], []
    for _key, members in sorted(pairs.items()):
        members = sorted(members, key=lambda i: i.sign)                     # bad, good
        failures = {m.item_id: item_failures(m, scores_by_item.get(m.item_id, {})) for m in members}
        if len(members) != 2:
            for m in members:
                failures[m.item_id].append("partner not approved")
        passed = all(not f for f in failures.values())
        if passed:
            selected += members
        report += [dict(item_id=m.item_id, storyline_id=m.storyline_id, arm=m.arm, sign=m.sign,
                        pair_passed=passed, failures="; ".join(failures[m.item_id])) for m in members]
    return selected, report
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest studies/knobe_moral_probe/tests -q`
Expected: `45 passed`

- [ ] **Step 5: Commit**

```bash
git add studies/knobe_moral_probe/kmp/screen.py studies/knobe_moral_probe/tests/test_screen.py
git commit -m "[knobe_moral_probe] screening pass rule and pair-level selection"
```

---

### Task 8: Screening runner, reviewer client, CLI

**Files:**
- Modify: `studies/knobe_moral_probe/kmp/screen.py`
- Test: `studies/knobe_moral_probe/tests/test_screen.py` (append)

- [ ] **Step 1: Write the failing tests**

Append to `studies/knobe_moral_probe/tests/test_screen.py`:
```python
import asyncio  # noqa: E402

from knobe.schemas import CurationRawResult, read_jsonl  # noqa: E402
from kmp import prompts  # noqa: E402
from kmp.items import load_items, write_items  # noqa: E402


class ScriptedClient:
    """Answers by rule from the [arm] [sign] markers in make_items' scenarios.
    `flaky` holds (item_id, qkey) keys that answer 'unclear' on first call."""

    def __init__(self, items, flaky=()):
        self.lookup = {p.text: (p.item_id, p.qkey) for p in prompts.build_screening_prompts(items)}
        self.items = {i.item_id: i for i in items}
        self.flaky = set(flaky)
        self.calls = []

    async def complete(self, prompt, max_tokens):
        item_id, qkey = self.lookup[prompt]
        self.calls.append((item_id, qkey))
        if (item_id, qkey) in self.flaky:
            self.flaky.discard((item_id, qkey))
            return "unclear"
        item = self.items[item_id]
        if qkey == "valence":
            return "1" if item.sign == "bad" else "9"
        return "8" if qkey == screen.intended_check(item) else "2"


def test_run_screening_resumes_and_retries_unparsed_once(tmp_path, nonmoral_items):
    out = tmp_path / "raw.jsonl"
    ps = prompts.build_screening_prompts(nonmoral_items)
    flaky_key = (ps[0].item_id, ps[0].qkey)
    client = ScriptedClient(nonmoral_items, flaky=[flaky_key])
    asyncio.run(screen.run_screening(ps, client, "scripted", out))
    rows = read_jsonl(out, CurationRawResult)
    assert len(rows) == len(ps) + 1                                  # one retry
    assert screen.scores_from_raw(rows)[flaky_key[0]][flaky_key[1]] is not None
    asyncio.run(screen.run_screening(ps, client, "scripted", out))
    assert len(read_jsonl(out, CurationRawResult)) == len(rows)       # resume: nothing re-asked


def test_all_pairs_pass_under_scripted_reviewer(tmp_path, foundation_items):
    out = tmp_path / "raw.jsonl"
    ps = prompts.build_screening_prompts(foundation_items)
    asyncio.run(screen.run_screening(ps, ScriptedClient(foundation_items), "scripted", out))
    selected, _ = screen.select_pairs(foundation_items, screen.scores_from_raw(read_jsonl(out, CurationRawResult)))
    assert len(selected) == len(foundation_items)


def test_main_mock_writes_outputs(tmp_path, nonmoral_items):
    items_path = tmp_path / "items.csv"
    write_items(nonmoral_items, items_path)
    code = screen.main(["--items", str(items_path), "--out-dir", str(tmp_path / "s"), "--mock"])
    assert code == 0
    assert (tmp_path / "s" / "screening_raw.jsonl").exists()
    assert (tmp_path / "s" / "selection_report.csv").exists()
    load_items(tmp_path / "s" / "selected_items.csv")                 # valid, possibly empty
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest studies/knobe_moral_probe/tests/test_screen.py -q`
Expected: FAIL, `AttributeError: module 'kmp.screen' has no attribute 'run_screening'`

- [ ] **Step 3: Implement runner, client and CLI**

Add to the imports at the top of `studies/knobe_moral_probe/kmp/screen.py`:
```python
import argparse
import asyncio
import sys
import time
from pathlib import Path

import pandas as pd
from knobe.curate import (
    _TRANSIENT_ANTHROPIC_ERRORS,
    AnthropicClient,
    MockClient,
    TransientCallError,
    _complete_with_retry,
    check_reviewer_not_subject,
    default_registry_path,
)
from knobe.parsing import parse_rating
from knobe.registry import load_registry
from knobe.schemas import CurationRawResult, append_jsonl, read_jsonl

from kmp.items import design_problems, load_items, write_items
from kmp.prompts import ScreeningPrompt, build_screening_prompts
```

Append to `studies/knobe_moral_probe/kmp/screen.py`:
```python
class ScreeningClient(AnthropicClient):
    """knobe.curate.AnthropicClient with temperature=0 (DESIGN.md section 4).
    complete() is reimplemented only to add that one argument (plan
    amendment 2); construction, retries and token accounting are inherited."""

    async def complete(self, prompt: str, max_tokens: int) -> str:
        try:
            resp = await self._client.messages.create(
                model=self.model, max_tokens=max_tokens, temperature=0.0,
                thinking={"type": "disabled"},
                messages=[{"role": "user", "content": prompt}],
            )
        except _TRANSIENT_ANTHROPIC_ERRORS as exc:
            raise TransientCallError(str(exc)) from exc
        usage = getattr(resp, "usage", None)
        if usage is not None:
            self.input_tokens_used += getattr(usage, "input_tokens", 0) or 0
            self.output_tokens_used += getattr(usage, "output_tokens", 0) or 0
        return "".join(b.text for b in resp.content if b.type == "text").strip()


def _read_raw(path: Path) -> list[CurationRawResult]:
    return read_jsonl(path, CurationRawResult) if path.exists() and path.stat().st_size else []


def scores_from_raw(rows: list[CurationRawResult]) -> dict[str, dict[str, int | None]]:
    """First parsed value per (item, question); None if every attempt failed."""
    scores: dict[str, dict[str, int | None]] = defaultdict(dict)
    for r in rows:
        if scores[r.variant_id].get(r.field) is None:
            scores[r.variant_id][r.field] = r.value if r.ok else None
    return dict(scores)


async def run_screening(prompts: list[ScreeningPrompt], client, reviewer_model: str, out_path: Path,
                        concurrency: int = 8, max_retries: int = 3) -> None:
    """Attempt 1 asks everything not yet asked; attempt 2 re-asks, once, what
    came back unparsed. Resumable: rows already in out_path count."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sem = asyncio.Semaphore(concurrency)
    for attempt in (1, 2):
        attempts: dict[tuple[str, str], list[CurationRawResult]] = defaultdict(list)
        for r in _read_raw(out_path):
            attempts[(r.variant_id, r.field)].append(r)
        todo = [p for p in prompts
                if len(attempts[(p.item_id, p.qkey)]) < attempt
                and not any(r.ok for r in attempts[(p.item_id, p.qkey)])]
        if not todo:
            continue
        with open(out_path, "a", encoding="utf-8") as fh:
            async def ask(p: ScreeningPrompt) -> None:
                async with sem:
                    text, _ = await _complete_with_retry(client, p.text, protocol.REVIEW_MAX_TOKENS, max_retries)
                value, ok, raw = parse_rating(text)
                append_jsonl(CurationRawResult(variant_id=p.item_id, field=p.qkey, value=value, ok=ok, raw=raw,
                                               reviewer_model=reviewer_model, timestamp=time.time()), fh)
            await asyncio.gather(*(ask(p) for p in todo))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="knobe_moral_probe screening")
    p.add_argument("--items", required=True, type=Path, help="authored items CSV")
    p.add_argument("--out-dir", required=True, type=Path)
    who = p.add_mutually_exclusive_group(required=True)
    who.add_argument("--mock", action="store_true", help="deterministic fake reviewer, no API")
    who.add_argument("--reviewer-model", help="pinned Claude model ID; recorded on every row")
    p.add_argument("--concurrency", type=int, default=8)
    args = p.parse_args(argv)

    items = load_items(args.items)
    problems = design_problems(items)
    if problems:
        print("refusing to screen:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 2
    approved = [i for i in items if i.review_status == "approved"]
    print(f"screening {len(approved)} approved of {len(items)} items")

    if args.mock:
        client, reviewer = MockClient(unparseable_rate=0.0), "mock"
    else:
        check_reviewer_not_subject(args.reviewer_model, load_registry(default_registry_path()))
        client, reviewer = ScreeningClient(args.reviewer_model), args.reviewer_model

    raw_path = args.out_dir / "screening_raw.jsonl"
    asyncio.run(run_screening(build_screening_prompts(approved), client, reviewer, raw_path,
                              concurrency=args.concurrency))
    selected, report = select_pairs(approved, scores_from_raw(_read_raw(raw_path)))
    write_items(selected, args.out_dir / "selected_items.csv")
    report_df = pd.DataFrame(report, columns=["item_id", "storyline_id", "arm", "sign", "pair_passed", "failures"])
    report_df.to_csv(args.out_dir / "selection_report.csv", index=False)
    summary = report_df.assign(pairs=1).groupby("arm")[["pair_passed", "pairs"]].sum() // 2
    print(summary.rename(columns={"pair_passed": "pairs_passed"}).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest studies/knobe_moral_probe/tests -q`
Expected: `48 passed`

- [ ] **Step 5: Commit**

```bash
git add studies/knobe_moral_probe/kmp/screen.py studies/knobe_moral_probe/tests/test_screen.py
git commit -m "[knobe_moral_probe] screening runner (resume, one retry), temperature-0 reviewer client, CLI"
```

---

### Task 9: Analysis frame

**Files:**
- Create: `studies/knobe_moral_probe/kmp/frame.py`
- Test: `studies/knobe_moral_probe/tests/test_frame.py`

- [ ] **Step 1: Write the failing tests**

`studies/knobe_moral_probe/tests/test_frame.py`:
```python
import math

import pytest
from knobe.schemas import ResultRecord, append_jsonl

from conftest import make_items
from kmp import frame


def _write(path, rows):
    with open(path, "w", encoding="utf-8") as fh:
        for pid, mk, value in rows:
            append_jsonl(ResultRecord(
                job_id=f"{pid}::{mk}::0", prompt_id=pid, model_key=mk, sample_idx=0, temperature=1.0, seed=1,
                raw_response="x" if value is None else str(value), parsed_rating=value, parse_ok=value is not None,
                parse_method="regex", logprobs_0_10=None, model_revision="r", runner_version="t", timestamp=0.0), fh)


def test_load_frame_recodes_reversed_and_joins_items(tmp_path):
    items = make_items("nonmoral", 1)
    iid = "kmp-nm-001-moral-bad"
    path = tmp_path / "r.jsonl"
    _write(path, [(f"{iid}::blame::w1::chat", "gemma-2-9b-instruct", 8),
                  (f"{iid}::blame::w3r::chat", "gemma-2-9b-instruct", 2),
                  (f"{iid}::blame::w2::raw", "gemma-2-9b-pretrained", None)])
    d = frame.load_frame(path, items).set_index("wording_key")
    assert d.loc["w1", "rating"] == 8 and d.loc["w3r", "rating"] == 8
    assert math.isnan(d.loc["w2", "rating"])
    assert d.loc["w1", "tuning"] == "instruct" and d.loc["w2", "tuning"] == "pretrained"
    assert d.loc["w1", "family"] == "gemma" and d.loc["w1", "sign_c"] == 0.5
    assert d.loc["w1", "arm"] == "moral" and d.loc["w1", "storyline_id"] == 1


def test_load_frame_rejects_unknown_items(tmp_path):
    path = tmp_path / "r.jsonl"
    _write(path, [("kmp-nm-099-moral-bad::blame::w1::raw", "gemma-2-9b-pretrained", 3)])
    with pytest.raises(ValueError, match="not in the items file"):
        frame.load_frame(path, make_items("nonmoral", 1))
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest studies/knobe_moral_probe/tests/test_frame.py -q`
Expected: collection error, `cannot import name 'frame'`

- [ ] **Step 3: Implement frame.py**

`studies/knobe_moral_probe/kmp/frame.py`:
```python
"""Results -> one analysis DataFrame (DESIGN.md section 10).

`rating` is the written number, recoded 10 - x for reversed-anchor
wordings so every rating points the same way; NaN where the model gave no
number. The existing sign-effect fits consume this frame.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from knobe.schemas import ResultRecord, read_jsonl

from kmp import protocol
from kmp.items import Item

SIGN_C = {"bad": 0.5, "good": -0.5}


def load_frame(results_path: str | Path, items: list[Item]) -> pd.DataFrame:
    df = pd.DataFrame([r.model_dump() for r in read_jsonl(results_path, ResultRecord)])
    df[["item_id", "qkey", "wording_key", "fmt"]] = df["prompt_id"].str.split("::", expand=True)
    meta = pd.DataFrame([i.model_dump() for i in items])[["item_id", "experiment", "storyline_id", "arm", "sign"]]
    unknown = sorted(set(df["item_id"]) - set(meta["item_id"]))
    if unknown:
        raise ValueError(f"{len(unknown)} result item_id(s) not in the items file, e.g. {unknown[:3]}")
    d = df.merge(meta, on="item_id", how="left", validate="many_to_one")
    d["reversed"] = [protocol.is_reversed(q, w) for q, w in zip(d["qkey"], d["wording_key"])]
    raw = pd.to_numeric(d["parsed_rating"], errors="coerce").where(d["parse_ok"].astype(bool))
    d["rating"] = np.where(d["reversed"], 10 - raw, raw)
    d["tuning"] = np.where(d["model_key"].str.endswith("-instruct"), "instruct", "pretrained")
    d["family"] = d["model_key"].str.split("-").str[0]
    d["sign_c"] = d["sign"].map(SIGN_C)
    return d
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest studies/knobe_moral_probe/tests -q`
Expected: `50 passed`

- [ ] **Step 5: Commit**

```bash
git add studies/knobe_moral_probe/kmp/frame.py studies/knobe_moral_probe/tests/test_frame.py
git commit -m "[knobe_moral_probe] analysis frame with reversed-anchor recoding"
```

---

### Task 10: Pre-analysis checks

**Files:**
- Create: `studies/knobe_moral_probe/kmp/checks.py`
- Test: `studies/knobe_moral_probe/tests/test_checks.py`

- [ ] **Step 1: Write the failing tests**

`studies/knobe_moral_probe/tests/test_checks.py`:
```python
import numpy as np
import pandas as pd
import pytest

from kmp import checks


def _frame(rows):
    cols = ["model_key", "tuning", "item_id", "qkey", "wording_key", "reversed", "arm", "sign",
            "parse_ok", "parsed_rating", "rating"]
    return pd.DataFrame(rows, columns=cols)


def test_number_rates_flag_low_cells():
    rows = [("m-pretrained", "pretrained", "i1", "blame", "w1", False, "moral", "bad", ok, 5 if ok else None,
             5.0 if ok else np.nan) for ok in [True] * 8 + [False] * 2]
    out = checks.number_rates(_frame(rows))
    assert out.loc[0, "number_rate"] == 0.8 and not out.loc[0, "passes"]


def test_anchor_agreement_perfect():
    rows = []
    for k, v in enumerate([2, 5, 8]):
        for w, rev in (("w1", False), ("w3r", True)):
            rows.append(("m-instruct", "instruct", f"i{k}", "blame", w, rev, "moral", "bad", True,
                         10 - v if rev else v, float(v)))
    out = checks.anchor_agreement(_frame(rows))
    assert out.loc[0, "r"] == pytest.approx(1.0)
    assert out.loc[0, "mean_diff"] == 0.0 and out.loc[0, "n_items"] == 3


def test_validity_checks_directions():
    rows = []
    for sign, blame, praise in (("bad", 8, 1), ("good", 2, 7)):
        rows.append(("m-pretrained", "pretrained", f"i{sign}", "blame", "w1", False, "moral", sign, True, blame, float(blame)))
        rows.append(("m-pretrained", "pretrained", f"i{sign}", "praise", "w1", False, "moral", sign, True, praise, float(praise)))
    rows.append(("m-pretrained", "pretrained", "i1", "significance", "w1", False, "moral", "bad", True, 9, 9.0))
    rows.append(("m-pretrained", "pretrained", "i2", "significance", "w1", False, "procedural", "bad", True, 2, 2.0))
    out = checks.validity(_frame(rows)).set_index("check")
    assert out.loc["blame_bad_minus_good", "value"] == 6 and out.loc["blame_bad_minus_good", "passes"]
    assert out.loc["praise_good_minus_bad", "passes"]
    assert out.loc["significance_moral_minus_procedural", "value"] == 7


def test_example_copying_share():
    rows = [("m-pretrained", "pretrained", "i1", "blame", "w1", False, "moral", "bad", True, v, float(v))
            for v in (0, 5, 9, 3)]
    out = checks.example_copying(_frame(rows))
    assert out.loc[0, "share_example_values"] == 0.75 and out.loc[0, "flag"]
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest studies/knobe_moral_probe/tests/test_checks.py -q`
Expected: collection error, `cannot import name 'checks'`

- [ ] **Step 3: Implement checks.py**

`studies/knobe_moral_probe/kmp/checks.py`:
```python
"""Pre-analysis gate (DESIGN.md section 8). Each function takes the
kmp.frame DataFrame and returns a small table; main() writes them and
exits 1 if any model x question x wording cell falls below the
number-rate minimum.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from kmp import protocol
from kmp.frame import load_frame
from kmp.items import load_items


def number_rates(frame: pd.DataFrame, threshold: float = protocol.NUMBER_RATE_MIN) -> pd.DataFrame:
    out = (frame.groupby(["model_key", "qkey", "wording_key"])["parse_ok"].mean()
           .rename("number_rate").reset_index())
    out["passes"] = out["number_rate"] >= threshold
    return out


def _pearson(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) < 3 or a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def anchor_agreement(frame: pd.DataFrame) -> pd.DataFrame:
    """Per model x core question: item means under normal vs reversed anchors (after recoding)."""
    core = frame[frame["qkey"].isin(protocol.CORE) & frame["rating"].notna()]
    means = (core.groupby(["model_key", "qkey", "item_id", "reversed"])["rating"].mean()
             .unstack("reversed").reindex(columns=[False, True])
             .rename(columns={False: "normal", True: "reversed"}))
    rows = []
    for (model_key, qkey), d in means.dropna().groupby(level=["model_key", "qkey"]):
        normal, rev = d["normal"].to_numpy(), d["reversed"].to_numpy()
        rows.append(dict(model_key=model_key, qkey=qkey, n_items=len(d), r=_pearson(normal, rev),
                         mean_diff=float((rev - normal).mean())))
    return pd.DataFrame(rows, columns=["model_key", "qkey", "n_items", "r", "mean_diff"])


def validity(frame: pd.DataFrame) -> pd.DataFrame:
    """Sanity directions any real judgment should show (DESIGN.md section 8, gate 2)."""
    rows = []
    for model_key, d in frame[frame["rating"].notna()].groupby("model_key"):
        def mean(qkey, **where):
            sel = d[d["qkey"] == qkey]
            for col, val in where.items():
                sel = sel[sel[col] == val]
            return sel["rating"].mean()
        checks_ = {
            "blame_bad_minus_good": mean("blame", sign="bad") - mean("blame", sign="good"),
            "praise_good_minus_bad": mean("praise", sign="good") - mean("praise", sign="bad"),
            "significance_moral_minus_procedural": mean("significance", arm="moral") - mean("significance", arm="procedural"),
        }
        for name, value in checks_.items():
            rows.append(dict(model_key=model_key, tuning=d["tuning"].iloc[0], check=name,
                             value=value, passes=bool(value > 0) if pd.notna(value) else None))
    return pd.DataFrame(rows, columns=["model_key", "tuning", "check", "value", "passes"])


def example_copying(frame: pd.DataFrame) -> pd.DataFrame:
    """Share of written answers equal to a worked-example answer (before recoding)."""
    parsed = frame[frame["parse_ok"].astype(bool)]
    share = (parsed["parsed_rating"].isin(protocol.EXAMPLE_ANSWERS)
             .groupby(parsed["model_key"]).mean().rename("share_example_values").reset_index())
    share["flag"] = share["share_example_values"] > protocol.COPY_SHARE_MAX
    return share


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="knobe_moral_probe pre-analysis checks")
    p.add_argument("--results", required=True, type=Path)
    p.add_argument("--items", required=True, type=Path)
    p.add_argument("--out-dir", required=True, type=Path)
    args = p.parse_args(argv)

    frame = load_frame(args.results, load_items(args.items))
    args.out_dir.mkdir(parents=True, exist_ok=True)
    tables = {"number_rates": number_rates(frame), "anchor_agreement": anchor_agreement(frame),
              "validity": validity(frame), "example_copying": example_copying(frame)}
    for name, table in tables.items():
        table.to_csv(args.out_dir / f"{name}.csv", index=False)
        print(f"\n== {name}\n{table.to_string(index=False)}")
    failing = tables["number_rates"][~tables["number_rates"]["passes"]]
    if len(failing):
        print(f"\n{len(failing)} cell(s) below the {protocol.NUMBER_RATE_MIN:.0%} number-rate minimum", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest studies/knobe_moral_probe/tests -q`
Expected: `54 passed`

- [ ] **Step 5: Commit**

```bash
git add studies/knobe_moral_probe/kmp/checks.py studies/knobe_moral_probe/tests/test_checks.py
git commit -m "[knobe_moral_probe] pre-analysis checks: number rates, anchor agreement, validity, example copying"
```

---

### Task 11: End-to-end pipeline test

**Files:**
- Test: `studies/knobe_moral_probe/tests/test_pipeline.py`

- [ ] **Step 1: Write the test**

`studies/knobe_moral_probe/tests/test_pipeline.py`:
```python
"""items -> screening (scripted reviewer) -> selection -> elicitation (fake
engine) -> frame -> checks, on synthetic items from both experiments."""
import asyncio

from knobe.schemas import CurationRawResult, read_jsonl

from conftest import make_items
from test_screen import ScriptedClient
from kmp import checks, elicit, frame, prompts, screen
from kmp.items import load_items, write_items


def test_pipeline_both_experiments(tmp_path):
    for experiment in ("nonmoral", "foundations"):
        items = make_items(experiment, 1)
        raw = tmp_path / experiment / "screening_raw.jsonl"
        asyncio.run(screen.run_screening(prompts.build_screening_prompts(items), ScriptedClient(items), "scripted", raw))
        selected, _ = screen.select_pairs(items, screen.scores_from_raw(read_jsonl(raw, CurationRawResult)))
        assert len(selected) == len(items)
        selected_path = tmp_path / experiment / "selected_items.csv"
        write_items(selected, selected_path)

        out = tmp_path / experiment / "results.jsonl"
        keys = "mistral-7b-v0.1-pretrained,mistral-7b-v0.1-instruct"
        assert elicit.main(["--items", str(selected_path), "--out", str(out), "--engine", "fake",
                            "--model-keys", keys]) == 0

        d = frame.load_frame(out, load_items(selected_path))
        assert set(d["fmt"]) == {"raw", "chat"} and d["rating"].between(0, 10).all()
        assert checks.number_rates(d)["passes"].all()
        assert checks.main(["--results", str(out), "--items", str(selected_path),
                            "--out-dir", str(tmp_path / experiment / "checks")]) == 0
```

- [ ] **Step 2: Run it**

Run: `.venv/bin/python -m pytest studies/knobe_moral_probe/tests -q`
Expected: `55 passed`

- [ ] **Step 3: Run the CLIs by hand once, to confirm the commands in the README work**

```bash
cd studies/knobe_moral_probe
../../.venv/bin/python - <<'EOF'
import sys; sys.path.insert(0, "tests")
from conftest import make_items
from kmp.items import write_items
write_items(make_items("nonmoral", 1), "/tmp/kmp_items.csv")
EOF
../../.venv/bin/python -m kmp.screen --items /tmp/kmp_items.csv --out-dir /tmp/kmp_screen --mock
../../.venv/bin/python -m kmp.elicit --items /tmp/kmp_items.csv --out /tmp/kmp_out.jsonl --engine fake --model-keys gemma-2-9b-instruct
../../.venv/bin/python -m kmp.checks --results /tmp/kmp_out.jsonl --items /tmp/kmp_items.csv --out-dir /tmp/kmp_checks
cd ../..
```
Expected:
- Screening prints a per-arm pairs table.
- Elicitation prints `0 done, 1008 remaining of 1008 jobs`, then `[elicit] gemma-2-9b-instruct (google/gemma-2-9b-it@fake): 1008 jobs`. Per nonmoral item and model that's 9 core prompts × 8 + 4 single-wording prompts × 24 = 168, and 6 items × 168 = 1,008. If the count differs, stop and reconcile it against `protocol.n_samples`.
- Checks prints its tables and exits 0.

- [ ] **Step 4: Commit**

```bash
git add studies/knobe_moral_probe/tests/test_pipeline.py
git commit -m "[knobe_moral_probe] end-to-end pipeline test on synthetic items"
```

---

### Task 12: Example check and throughput (DESIGN.md §8, gates 3 and 5)

**Files:**
- Modify: `studies/knobe_moral_probe/kmp/elicit.py` (add `--no-examples`)
- Modify: `studies/knobe_moral_probe/kmp/checks.py` (add `example_effect`, `throughput`)
- Test: `studies/knobe_moral_probe/tests/test_checks.py` (append)

The example check runs Mistral-instruct with and without the worked
examples and compares the two. Job IDs are the same in both runs, so the
no-examples run **must** write to its own `--out` file.

- [ ] **Step 1: Write the failing tests**

Append to `studies/knobe_moral_probe/tests/test_checks.py`:
```python
from conftest import make_items  # noqa: E402
from kmp import elicit, frame  # noqa: E402
from kmp.items import write_items  # noqa: E402


def test_example_effect_is_zero_for_identical_runs():
    rows = [("m-instruct", "instruct", f"i{k}", "blame", "w1", False, "moral", "bad", True, v, float(v))
            for k, v in enumerate([1, 4, 8])]
    out = checks.example_effect(_frame(rows), _frame(rows))
    assert out.loc[0, "mean_diff"] == 0.0 and out.loc[0, "r"] == pytest.approx(1.0)


def test_no_examples_run_and_throughput(tmp_path):
    items = make_items("nonmoral", 1)[:2]
    items_path = tmp_path / "items.csv"
    write_items(items, items_path)
    common = ["--items", str(items_path), "--engine", "fake", "--model-keys", "mistral-7b-v0.1-instruct"]
    assert elicit.main([*common, "--out", str(tmp_path / "with.jsonl")]) == 0
    assert elicit.main([*common, "--out", str(tmp_path / "without.jsonl"), "--no-examples"]) == 0
    with_f = frame.load_frame(tmp_path / "with.jsonl", items)
    without = frame.load_frame(tmp_path / "without.jsonl", items)
    assert len(with_f) == len(without)
    assert set(checks.example_effect(with_f, without)["qkey"]) >= {"blame", "praise", "intentionality"}
    tp = checks.throughput(with_f)
    assert list(tp["model_key"]) == ["mistral-7b-v0.1-instruct"] and tp.loc[0, "rows"] == len(with_f)
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest studies/knobe_moral_probe/tests/test_checks.py -q`
Expected: FAIL, `AttributeError: module 'kmp.checks' has no attribute 'example_effect'`

- [ ] **Step 3: Add `--no-examples` to elicit.py**

In `studies/knobe_moral_probe/kmp/elicit.py` `main`, after the `--max-tokens` argument add:
```python
    p.add_argument("--no-examples", action="store_true",
                   help="omit the worked examples (DESIGN.md section 8 example check). "
                        "Job IDs match a normal run, so use a separate --out file.")
```
and replace:
```python
    jobs = build_jobs(prompts.build_subject_prompts(items), model_keys)
```
with:
```python
    examples = () if args.no_examples else protocol.EXAMPLES
    jobs = build_jobs(prompts.build_subject_prompts(items, examples), model_keys)
```

- [ ] **Step 4: Add the two checks to checks.py**

Add to `studies/knobe_moral_probe/kmp/checks.py`, after `example_copying`:
```python
def example_effect(with_examples: pd.DataFrame, without_examples: pd.DataFrame) -> pd.DataFrame:
    """Per model x question: item-mean ratings with vs without worked examples.
    Examples that only teach format should leave these unchanged."""
    def item_means(f: pd.DataFrame) -> pd.Series:
        return f[f["rating"].notna()].groupby(["model_key", "qkey", "item_id"])["rating"].mean()
    both = pd.concat({"with": item_means(with_examples), "without": item_means(without_examples)}, axis=1).dropna()
    rows = []
    for (model_key, qkey), d in both.groupby(level=["model_key", "qkey"]):
        a, b = d["with"].to_numpy(), d["without"].to_numpy()
        rows.append(dict(model_key=model_key, qkey=qkey, n_items=len(d), r=_pearson(a, b),
                         mean_diff=float((a - b).mean())))
    return pd.DataFrame(rows, columns=["model_key", "qkey", "n_items", "r", "mean_diff"])


def throughput(frame: pd.DataFrame) -> pd.DataFrame:
    """Rows per second per model, from result timestamps (CLAUDE.md section 4 cost check)."""
    g = frame.groupby("model_key")["timestamp"].agg(["min", "max", "size"]).reset_index()
    span = (g["max"] - g["min"]).clip(lower=1e-9)
    return pd.DataFrame({"model_key": g["model_key"], "rows": g["size"],
                         "seconds": g["max"] - g["min"], "rows_per_second": g["size"] / span})
```

In `main`, add `"throughput": throughput(frame)` to the `tables` dict.

- [ ] **Step 5: Run to verify pass**

Run: `.venv/bin/python -m pytest studies/knobe_moral_probe/tests -q`
Expected: `57 passed`

- [ ] **Step 6: Commit**

```bash
git add studies/knobe_moral_probe/kmp/elicit.py studies/knobe_moral_probe/kmp/checks.py studies/knobe_moral_probe/tests/test_checks.py
git commit -m "[knobe_moral_probe] example-effect and throughput checks; --no-examples run mode"
```

---

### Task 13: Committed power basis (DESIGN.md §9)

**Files:**
- Create: `studies/knobe_moral_probe/analysis/power_basis.py`
- Create (output): `studies/knobe_moral_probe/outputs/power_basis.csv`
- Modify: `studies/knobe_moral_probe/README.md`
- Modify: `studies/knobe_moral_probe/ANALYSIS_LOG.md`

- [ ] **Step 1: Write the script**

`studies/knobe_moral_probe/analysis/power_basis.py`:
```python
"""Design-stage power basis for DESIGN.md section 9: storylines per
foundation needed for 80% power to detect each finetuned per-foundation
sign effect seen in the MF pilot (parsed scoring).

Reuses required_sets() and mde() from
analysis/rq1_v1_1_robustness/15_rq1a_severity_mde_and_power_planning.py,
unchanged (se ~ sqrt(G_current / G_new) scaling). Reads the pilot's
committed sign_wcb_parsed.csv; this is the one place the study reads
earlier outputs (README exception). Deterministic, no seeding.

Run from the repo root:
    .venv/bin/python studies/knobe_moral_probe/analysis/power_basis.py
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd

STUDY_DIR = Path(__file__).resolve().parents[1]
REPO = STUDY_DIR.parents[1]
PILOT_TABLE = REPO / "analysis/ngo_extensions/moral_foundations_pilot/outputs/sign_wcb_parsed.csv"
S15 = REPO / "analysis/rq1_v1_1_robustness/15_rq1a_severity_mde_and_power_planning.py"
OUT = STUDY_DIR / "outputs" / "power_basis.csv"
MIN_EFFECT = 0.2          # below this there is no effect to power; reported as None


def _load_s15():
    sys.path.insert(0, str(S15.parent))
    spec = importlib.util.spec_from_file_location("s15_power", S15)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    s15 = _load_s15()
    d = pd.read_csv(PILOT_TABLE)
    d = d[(d["tuning"] == "finetuned") & (d["term"] == "sign_c")].copy()
    d["already_powered"] = [s15.mde(se, int(g)) <= abs(b) for b, se, g in zip(d["beta_obs"], d["se_obs"], d["n_groups"])]
    d["storylines_for_80pct"] = [s15.required_sets(b, se, int(g)) if abs(b) > MIN_EFFECT else None
                                 for b, se, g in zip(d["beta_obs"], d["se_obs"], d["n_groups"])]
    out = d[["family", "arm", "n_groups", "beta_obs", "se_obs", "already_powered", "storylines_for_80pct"]].round(3)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    print(out.to_string(index=False))
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it and check it reproduces DESIGN.md §9**

Run: `.venv/bin/python studies/knobe_moral_probe/analysis/power_basis.py`
Expected: the gemma rows show loyalty 13, fairness 17, purity 10, and authority already powered. The mistral rows show loyalty 66, authority 357, fairness 11, purity 10. The llama rows show no effect to power (None, or a large number where |beta| > 0.2). If any number differs from DESIGN.md §9, stop and reconcile before continuing.

- [ ] **Step 3: Update README**

In `studies/knobe_moral_probe/README.md`, replace:
```
This study is new work. It reads none of the earlier outputs and changes
none of the earlier files.
```
with:
```
This study is new work. It changes none of the earlier files, and reads
none of their outputs except one: `analysis/power_basis.py`, the
design-stage power check, reads the MF pilot's committed
`sign_wcb_parsed.csv`.
```

Then replace the Contents table's last line (`Stimuli, code and outputs are added here as the implementation plan proceeds.`) with:
```
| `docs/IMPLEMENTATION_PLAN.md` | the pipeline build plan |
| `kmp/` | pipeline: items, protocol, prompts, screen, elicit, frame, checks |
| `tests/` | `.venv/bin/python -m pytest studies/knobe_moral_probe/tests -q` from the repo root |
| `analysis/power_basis.py` | DESIGN.md §9 power table → `outputs/power_basis.csv` |

Commands (from this folder; `../../.venv/bin/python -m kmp.<module> --help` for all flags):

    ../../.venv/bin/python -m kmp.screen --items stimuli/<experiment>.csv --out-dir outputs/screening/<experiment> --reviewer-model <pinned id>
    ../../.venv/bin/python -m kmp.elicit --items outputs/screening/<experiment>/selected_items.csv --out outputs/elicit/<experiment>.jsonl --engine vllm --model-keys <keys>
    ../../.venv/bin/python -m kmp.checks --results outputs/elicit/<experiment>.jsonl --items outputs/screening/<experiment>/selected_items.csv --out-dir outputs/checks/<experiment>
    # pilot example check: same command as elicit plus --no-examples --model-keys mistral-7b-v0.1-instruct, to a separate --out file
```

- [ ] **Step 4: Commit script, output and README**

```bash
git add studies/knobe_moral_probe/analysis/power_basis.py studies/knobe_moral_probe/outputs/power_basis.csv studies/knobe_moral_probe/README.md
git commit -m "[knobe_moral_probe] commit the DESIGN.md section 9 power basis; README commands"
```

- [ ] **Step 5: Log the run with that commit's hash**

Append to `studies/knobe_moral_probe/ANALYSIS_LOG.md` (replace `<hash>` with the output of `git rev-parse --short HEAD`):
```
2026-09-28 | `analysis/power_basis.py` | MF pilot finetuned sign_c cells, parsed scoring; script 15's required_sets/mde, 80% power, |beta| > 0.2 | Storylines per foundation for 80% power: Gemma 10–17 (authority already powered), Mistral fairness/purity 10–11, loyalty 66, authority 357 (effect ≈ 0); Llama no effect. Basis for the 20-per-foundation target | <hash>
```

```bash
git add studies/knobe_moral_probe/ANALYSIS_LOG.md
git commit -m "[knobe_moral_probe] log the power-basis run"
```

---

## After this plan

1. **The authoring plan** (separate): the definitions document and review checklist; migrating Ngo's 40 pairs and the usable pilot variants into `stimuli/nonmoral.csv` with `kmp-` IDs, `agent` and `effect` fields; drafting the foundations scaffolds; your review; real screening with a pinned reviewer model.
2. **The pilot** (DESIGN.md §8): a few dozen screened items through `kmp.elicit --engine vllm` on the cluster, then `kmp.checks`. Parker runs it.
3. **The analysis plan with predictions,** committed before the full run. It wires `kmp.frame` into the existing sign-effect fits (`lib.wild_cluster_bootstrap`), and adds the per-wording and RQ5 analyses (DESIGN.md §10).
