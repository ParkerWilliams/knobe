"""Jev as the subject model, asked natively: a "scantron" sheet per question, no chat prompt.

Why (Parker, 2026-11-12): evaluate Jev itself for the Knobe effect -- the same
morality questions the chat models were asked, posed as Jev's own
multiple-choice questions, with no LLM output and no wrapper. The 2026-10-22
run (tools/jev_subject.py) did not do that: it gave Jev the chat models' whole
prompt as its state and one meta-question ("answer the question at the end of
`prompt`") over bare "The answer is N." options, then fed the pick back through
the chat-reply pipeline as if Jev had written it. That run is kept as the
"wrapped" contrast.

What Jev sees, per item x question x wording (the same cells, in the same order,
as kmp.prompts.build_subject_prompts: protocol.subject_qkeys x protocol.QUESTIONS,
wordings unchanged):
  state     {"scenario": item.scenario} -- the scenario only: no instruction line,
            no "Scenario: / Question: / Answer:" frame, no worked examples.
  question  one Choice question: its instructions are the question as worded
            (kmp.prompts.render_question, the text the chat models got after
            "Question:"); its options are the eleven bubbles "0".."10", each
            labelled as the wording labels it -- a number the wording anchors
            carries its words ("0 (not at all)", "10 (completely)"), the rest are
            bare numbers. A wording with no anchors would get eleven bare bubbles;
            since the DESIGN amendment of 2026-10-22 every wording has them
            (intentionality w1 = Ngo's question + "0 (definitely not) to 10
            (definitely yes)"). No "none": a participant fills in a bubble.
One call per question, each on its own (Jev never sees a question's other
wordings, as no chat prompt held more than one question); sample 0 only, as in
the wrapped run (Jev is close to deterministic; its probability vector stands
in for the spread of samples).

Readouts per answer: the top bubble (ties go to the lower number) and the
expected value over 0..10 (the counterpart of a chat model's mean over its
samples). Reversed wordings are recoded 10 - x, as for the chat models
(kmp.frame.join_items does it for both).

native_frame() turns a results file into a kmp.frame-contract DataFrame, so the
existing fits and checks (analysis/first_look.sign_effects,
analysis/arm_effects.arm_effects, kmp.checks' tables) run on it unchanged --
without any reply text, kmp.answer or ResultRecord in between.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from kmp import jev, prompts, protocol
from kmp.frame import join_items
from kmp.items import Item

MODEL = jev.MODEL                  # typesafe/jev-1.14, pinned; each row records the snapshot that answered
QUESTION_KEY = jev.QUESTION_KEY    # what tools/jev_read.DecisionsClient checks the answer under
LEVELS = jev.LEVELS                # "0".."10"
FMT = "native"                     # the fmt part of a job_id, where chat runs have "chat"/"raw"
MODEL_KEY = "jev-1.14-native"      # the wrapped run is "jev-1.14-instruct"
MODEL_FAMILY, FAMILY = "jev-1.14", "jev"
# Jev is neither an instruct nor a pretrained checkpoint; "finetuned" is the frame's slot for a
# served model (as in tools/jev_models.yaml), so kmp.checks' per-model tables accept it.
TUNING_STATUS = "finetuned"
READERS = ("top", "ev")
SHEET_VERSION = "native-1"

_ANCHOR = re.compile(r"\b(10|[0-9]) \(([^()]+)\)")


def anchors(template: str) -> dict[int, str]:
    """{number: words} for each number the wording anchors, read from its template
    (before the agent and effect go in, so story text can't add an anchor)."""
    return {int(n): words for n, words in _ANCHOR.findall(template)}


def bubbles(template: str) -> dict[str, str]:
    """The eleven options, "0".."10", each labelled as the wording labels it."""
    a = anchors(template)
    return {lv: (f"{lv} ({a[int(lv)]})" if int(lv) in a else lv) for lv in LEVELS}


@dataclass(frozen=True)
class Question:
    stem: str            # item_id::qkey::wording_key, as kmp.prompts
    job_id: str          # stem::native
    item_id: str
    qkey: str
    wording_key: str
    reversed: bool
    scenario: str
    text: str            # the question as worded
    criteria: dict       # the bubbles


def build_questions(items: list[Item]) -> list[Question]:
    out = []
    for item in items:
        for qkey in protocol.subject_qkeys(item):
            for w in protocol.QUESTIONS[qkey]:
                stem = f"{item.item_id}::{qkey}::{w.key}"
                out.append(Question(stem=stem, job_id=prompts.prompt_id(stem, FMT), item_id=item.item_id,
                                    qkey=qkey, wording_key=w.key, reversed=w.reversed, scenario=item.scenario,
                                    text=prompts.render_question(item, w.template), criteria=bubbles(w.template)))
    return out


def request_body(q: Question) -> dict:
    return {"model": MODEL, "state": {"scenario": q.scenario},
            "questions": {QUESTION_KEY: {"type": "choice", "instructions": q.text, "criteria": q.criteria}}}


def body_sha256(body: dict) -> str:
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


def spec_sha256() -> str:
    """Fingerprint of the sheet's rules (each row also carries its own body's hash)."""
    spec = {"version": SHEET_VERSION, "model": MODEL, "question_key": QUESTION_KEY, "state": ["scenario"],
            "levels": list(LEVELS), "label": "N (anchor words) where the wording anchors N, else N",
            "type": "choice", "none": False}
    return hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()


SPEC = spec_sha256()


def answer_row(q: Question, data: dict) -> dict | None:
    """One results row from a Decisions API response; None if no bubble has probability."""
    answer = data["answers"][QUESTION_KEY]
    probs = {lv: float((answer.get("probabilities") or {}).get(lv, 0.0)) for lv in LEVELS}
    mass = sum(probs.values())
    if mass <= 0:
        return None
    top = max(LEVELS, key=lambda lv: probs[lv])          # first maximum: ties go to the lower number
    usage = data.get("usage") or {}
    return {"job_id": q.job_id, "item_id": q.item_id, "qkey": q.qkey, "wording_key": q.wording_key,
            "reversed": q.reversed, "top": int(top), "ev": sum(int(lv) * p for lv, p in probs.items()) / mass,
            "probabilities": answer.get("probabilities"), "choice": answer.get("choice"),
            "confidence": answer.get("confidence"), "model": data.get("model"),
            "input_tokens": usage.get("input_tokens"), "cost": usage.get("cost"),
            "body_sha256": body_sha256(request_body(q)), "spec": SPEC, "timestamp": time.time()}


def manifest_path(results: str | Path) -> Path:
    results = Path(results)
    return results.with_name(results.name + ".manifest.json")


def lock_path(results: str | Path) -> Path:
    results = Path(results)
    return results.with_name(results.name + ".lock")


def read_results(path: str | Path) -> dict[str, dict]:
    """job_id -> row. Torn last lines are skipped (jev.read_rows); a job_id answered
    twice is an error (one writer per file holds the lock)."""
    rows = jev.read_rows(path)
    out: dict[str, dict] = {}
    for r in rows:
        if r["job_id"] in out:
            raise ValueError(f"{path}: job_id {r['job_id']} answered twice")
        out[r["job_id"]] = r
    return out


def native_frame(results: str | Path, items: list[Item], reader: str = "top") -> pd.DataFrame:
    """The results as a kmp.frame-contract DataFrame (one row per answered question).
    reader: "top" (the top bubble) or "ev" (the expected value). Refuses rows whose
    request differs from the sheet the items and this module build now."""
    if reader not in READERS:
        raise ValueError(f"reader must be one of {READERS}, not {reader!r}")
    rows = read_results(results)
    if not rows:
        raise ValueError(f"{results}: no answers")
    sheet = {q.job_id: body_sha256(request_body(q)) for q in build_questions(items)}
    stale = sorted(j for j, r in rows.items() if j in sheet and r["body_sha256"] != sheet[j])
    if stale:
        raise ValueError(f"{results}: {len(stale)} answer(s) were to a different question than the sheet now "
                         f"asks (items or kmp.jev_native changed), e.g. {stale[:3]}")
    df = pd.DataFrame([{"job_id": j, "prompt_id": j, "item_id": r["item_id"], "qkey": r["qkey"],
                        "wording_key": r["wording_key"], "fmt": FMT, "parsed_rating_raw": float(r[reader]),
                        "parse_ok": True, "top": r["top"], "ev": r["ev"], "confidence": r.get("confidence"),
                        "served_model": r.get("model")} for j, r in rows.items()])
    df["model_key"], df["model_family"], df["family"] = MODEL_KEY, MODEL_FAMILY, FAMILY
    df["tuning_status"] = TUNING_STATUS
    d = join_items(df, items, results)
    d["refusal"] = False            # every answer is a bubble: nothing to refuse (kmp.frame contract column)
    return d
