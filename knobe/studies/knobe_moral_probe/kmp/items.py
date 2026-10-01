"""Stimulus items: schema, kmp- IDs, CSV I/O, design checks (DESIGN.md section 3).

One row is one version (bad or good) of one side effect. Versions pair up
by (experiment, storyline_id, arm): exactly one bad and one good, same
agent. storyline_id is the cluster unit for inference; in the foundations
experiment one storyline carries a harm pair plus one or more foundation
pairs (shared scaffolds, DESIGN.md section 3.3). The ngo_verbatim
experiment holds Ngo et al.'s 40 original pairs word for word (arm "moral",
storyline_id = Ngo's pair number, the same numbering as the adapted nonmoral
moral storylines); DESIGN.md 2026-10-01 amendment "Ngo goals and verbatim set".

`scaffold` (foundations only, required there; None elsewhere) records how a
foundations storyline was written (DEFINITIONS_AND_CHECKLIST.md section 7,
decision A, option 1): "shared" = one harm-neutral scaffold carrying a harm
pair plus one or more foundation pairs; "purpose" = a purpose-written
storyline (purity) with no harm pair. In the CSV, None is an empty cell.

`agent` is the agent as written mid-sentence ("Bill", "the CEO"); `effect`
is the side effect as a bare verb phrase ("injure children"), so question
wordings can be rendered as "Did {agent} intentionally {effect}?".
"""
from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Experiment = Literal["nonmoral", "foundations", "ngo_verbatim"]
Sign = Literal["bad", "good"]
Source = Literal["ngo", "pilot", "new"]
ReviewStatus = Literal["draft", "approved", "rejected"]
Scaffold = Literal["shared", "purpose"]

ARMS: dict[str, tuple[str, ...]] = {
    "nonmoral": ("moral", "prudential", "procedural"),
    "foundations": ("harm", "fairness", "loyalty", "authority", "purity"),
    "ngo_verbatim": ("moral",),
}
EXPERIMENT_CODE = {"nonmoral": "nm", "foundations": "mf", "ngo_verbatim": "nv"}
# Ngo's original text keeps its names and pronouns (which change with the sign),
# so this experiment is exempt from the same-agent and gendered-pronoun checks,
# and from nothing else.
ROLE_NOUN_EXEMPT = frozenset({"ngo_verbatim"})
ID_PREFIX = "kmp-"
FIELDS = ["item_id", "experiment", "storyline_id", "arm", "sign", "agent",
          "effect", "scenario", "source", "review_status", "scaffold"]


def make_item_id(experiment: str, storyline_id: int, arm: str, sign: str) -> str:
    return f"{ID_PREFIX}{EXPERIMENT_CODE[experiment]}-{storyline_id:03d}-{arm}-{sign}"


class Item(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    item_id: str
    experiment: Experiment
    storyline_id: int = Field(ge=1, le=999)
    arm: str
    sign: Sign
    agent: str
    effect: str
    scenario: str
    source: Source
    review_status: ReviewStatus = "draft"
    scaffold: Scaffold | None = None

    @field_validator("scaffold", mode="before")
    @classmethod
    def _empty_scaffold_is_none(cls, v):
        return None if v == "" else v

    @field_validator("storyline_id", mode="before")
    @classmethod
    def _no_bool(cls, v):
        if isinstance(v, bool):
            raise ValueError("storyline_id must be an integer, not a bool")
        return v

    @model_validator(mode="after")
    def _check(self) -> "Item":
        if self.arm not in ARMS[self.experiment]:
            raise ValueError(f"{self.item_id}: arm {self.arm!r} not in {ARMS[self.experiment]}")
        if self.experiment == "foundations" and self.scaffold is None:
            raise ValueError(f"{self.item_id}: foundations items need a scaffold ('shared' or 'purpose')")
        if self.experiment != "foundations" and self.scaffold is not None:
            raise ValueError(f"{self.item_id}: scaffold must be empty outside foundations, not {self.scaffold!r}")
        if self.experiment == "ngo_verbatim" and self.source != "ngo":
            raise ValueError(f"{self.item_id}: ngo_verbatim items must have source 'ngo', not {self.source!r}")
        expected = make_item_id(self.experiment, self.storyline_id, self.arm, self.sign)
        if self.item_id != expected:
            raise ValueError(f"item_id {self.item_id!r} should be {expected!r}")
        for name in ("agent", "effect", "scenario"):
            value = getattr(self, name)
            if not value.strip() or value != value.strip():
                raise ValueError(f"{self.item_id}: {name} is empty or has surrounding whitespace")
        return self


# DESIGN.md 2026-10-01 role-noun amendment: agents are named by role noun ("the
# manager"), never by personal name, with no gendered pronouns, for every item
# including the minimally adapted Ngo et al. pairs. Pronouns are checked here;
# personal names cannot be detected reliably in code, so they are a
# review-checklist item, not a code check.
GENDERED_PRONOUNS = re.compile(r"\b(he|she|him|her|his|hers|himself|herself)\b", re.IGNORECASE)


def pair_key(item: Item) -> tuple[str, int, str]:
    return (item.experiment, item.storyline_id, item.arm)


def load_items(path: str | Path) -> list[Item]:
    """Load items; a bad row raises ValueError naming its CSV line. An empty file is valid."""
    items = []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        reader.fieldnames  # read the header now, so line_num counts it for the first data row
        while True:
            start = reader.reader.line_num + 1
            try:
                row = next(reader)
            except StopIteration:
                break
            try:
                if None in row:
                    raise ValueError("row has more cells than the header has columns")
                items.append(Item(**row))
            except ValueError as exc:  # pydantic's ValidationError is a ValueError
                raise ValueError(f"{path}, line {start}: {exc}") from exc
    return items


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
        elif key[0] not in ROLE_NOUN_EXEMPT and members[0].agent != members[1].agent:
            problems.append(f"pair {key[1:]}: agents differ ({members[0].agent!r} vs {members[1].agent!r})")
    problems += _scaffold_problems(items)
    for item in sorted(items, key=lambda i: i.item_id):
        if item.experiment in ROLE_NOUN_EXEMPT:
            continue
        found = sorted({w.lower() for name in ("scenario", "agent", "effect")
                        for w in GENDERED_PRONOUNS.findall(getattr(item, name))})
        if found:
            problems.append(f"{item.item_id}: gendered pronoun(s) {found} (use a role noun)")
    return problems


def _complete_arms(members: list[Item]) -> set[str]:
    """Arms that have both a bad and a good version among members."""
    signs: dict[str, set[str]] = defaultdict(set)
    for m in members:
        signs[m.arm].add(m.sign)
    return {arm for arm, s in signs.items() if s == {"bad", "good"}}


def _scaffold_problems(items: list[Item]) -> list[str]:
    """Foundations storylines (decision A): one scaffold value per storyline;
    a shared storyline has a harm pair and at least one non-harm pair; a
    purpose-written storyline has no harm item at all."""
    problems = []
    storylines: dict[int, list[Item]] = defaultdict(list)
    for item in items:
        if item.experiment == "foundations":
            storylines[item.storyline_id].append(item)
    for sid, members in sorted(storylines.items()):
        scaffolds = sorted({m.scaffold for m in members})
        if len(scaffolds) > 1:
            problems.append(f"storyline {sid}: mixed scaffold values {scaffolds}")
            continue
        arms = _complete_arms(members)
        if scaffolds == ["shared"]:
            if "harm" not in arms:
                problems.append(f"storyline {sid}: shared scaffold needs a harm pair (one bad, one good)")
            if not arms - {"harm"}:
                problems.append(f"storyline {sid}: shared scaffold needs at least one non-harm foundation pair")
        elif any(m.arm == "harm" for m in members):
            problems.append(f"storyline {sid}: purpose-written storyline must not have a harm item")
    return problems
