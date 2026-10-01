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
