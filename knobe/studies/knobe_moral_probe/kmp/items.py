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

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

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
    storyline_id: int = Field(ge=1, le=999)
    arm: str
    sign: Sign
    agent: str
    effect: str
    scenario: str
    source: Source
    review_status: ReviewStatus = "draft"

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
    """Load items; a bad row raises ValueError naming its CSV line. An empty file is valid."""
    items = []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
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
        elif members[0].agent != members[1].agent:
            problems.append(f"pair {key[1:]}: agents differ ({members[0].agent!r} vs {members[1].agent!r})")
    return problems
