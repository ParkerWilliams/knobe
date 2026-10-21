"""Jev as a second answer reader (a cross-check on kmp.answer, not the reader of record).

Jev (TypeSafe's decision model, served by OpenRouter's Decisions API) takes a
text state plus typed questions and returns a probability for each option it
is given -- no generated text. Here it is asked the question kmp.answer
answers: which number from 0 to 10 does the reply give as its rating, or
none. Strict, as kmp.answer: the options are the eleven numbers and "none",
with no scale anchors, so a reply that only says words is "none".

Score questions are documented for 2-10 levels and have no "none" option,
so this is a Choice question over 12 options. The reading rule (Parker,
2026-10-20): the rating is the top option, and "none" on top means unparsed.
The expected value over 0-10 (renormalized without "none") is kept for a
sensitivity readout (reader "jev_ev" in kmp.frame).

Readings live in a sidecar next to each results file, <results>.jev.jsonl,
one row per job_id (tools/jev_read.py writes it), and the jitter re-reads
in <results>.jev_jitter.jsonl.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from kmp import elicit, prompts, protocol
from kmp.items import Item

MODEL = "typesafe/jev-1.14"          # pinned; each row records the snapshot that answered
URL = "https://openrouter.ai/api/alpha/decisions"
QUESTION_KEY = "rating"
NONE = "none"
LEVELS = tuple(str(i) for i in range(11))
OPTIONS = LEVELS + (NONE,)
READERS = ("regex", "jev", "jev_ev")

# The rules restate kmp.answer's (DESIGN.md amendment 2026-10-13): the number written,
# as written (reversed wordings are recoded later, in kmp.frame), never a number
# from the scale, a hypothetical or the worked examples, and never words.
INSTRUCTIONS = (
    f"`reply` is one reply a language model wrote. It was told: \"{protocol.INSTRUCTION}\" `question` is the "
    "question it was answering. Before that it may have been shown three practice questions with their answers ("
    + "; ".join(f"\"{q}\" {a}" for _, q, a in protocol.EXAMPLES) + ").\n\n"
    "Which whole number from 0 to 10 does the reply give as its own answer to `question`? Read the reply only; "
    "do not judge the scenario or decide what the answer should be.\n"
    "- Count a number only if the reply puts it forward as its answer, wherever it appears: \"7\", "
    "\"Answer: 7\", \"7/10\", \"I would rate this a 7\", \"extremely blameworthy (10)\".\n"
    "- Report the number as written, even when the question's scale runs from high to low (\"0 (extremely) to "
    "10 (not at all)\"). Do not reverse or adjust it.\n"
    "- These are not answers: numbers that restate or explain the scale (\"on a scale from 0 to 10\", \"0 means "
    "not at all\"), numbers in hypotheticals (\"if it were a convention, the answer would be 10\"), counts "
    "from the story, and answers to the practice questions.\n"
    "- Do not turn words into numbers: a reply that answers only in words (\"Yes\", \"No\", \"Not at all\") "
    "gives no number.\n"
    "- If the answer is a decimal (7.5), choose the nearest whole number.\n"
    "- Choose none when the reply gives no number as its answer, refuses or says it cannot answer, gives two or "
    "more different numbers or a range (\"6 or 7\", \"between 4 and 6\"), or stops before giving one.")
CRITERIA = {**{lv: f"The reply gives {lv} as its answer to the question." for lv in LEVELS},
            NONE: "The reply gives no single number from 0 to 10 as its answer: it answers only in words, refuses, "
                  "gives several different numbers or a range, only discusses the scale or the practice questions, "
                  "or stops before giving a number."}


def spec_sha256() -> str:
    """Fingerprint of what Jev is asked; every reading carries it, and kmp.frame
    refuses readings made under another one (re-read after changing the wording)."""
    spec = {"model": MODEL, "question_key": QUESTION_KEY, "instructions": INSTRUCTIONS, "criteria": CRITERIA,
            "state": ["question", "reply"]}
    return hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()


SPEC = spec_sha256()


@dataclass(frozen=True)
class Reading:
    rating: int | None      # the top option, None if "none" is on top
    ok: bool
    ev: float | None        # sum(i * p_i) / sum(p_i) over 0..10; None if they hold no probability
    p_none: float


def read_choice(probabilities: Mapping[str, float]) -> Reading:
    p = {o: float(probabilities.get(o, 0.0)) for o in OPTIONS}
    top = max(OPTIONS, key=lambda o: p[o])        # ties go to the first option listed
    mass = sum(p[lv] for lv in LEVELS)
    ev = sum(int(lv) * p[lv] for lv in LEVELS) / mass if mass > 0 else None
    return Reading(rating=None if top == NONE else int(top), ok=top != NONE, ev=ev, p_none=p[NONE])


def request_body(question: str, reply: str) -> dict:
    return {"model": MODEL, "state": {"question": question, "reply": reply},
            "questions": {QUESTION_KEY: {"type": "choice", "instructions": INSTRUCTIONS, "criteria": CRITERIA}}}


def reading_row(job_id: str, answer: dict | None, read_idx: int = 0, model: str | None = None,
                usage: dict | None = None, note: str | None = None) -> dict:
    """One sidecar row. answer: Jev's answer to QUESTION_KEY (None = no call, read as "none")."""
    probs = (answer or {}).get("probabilities") or {NONE: 1.0}
    r = read_choice(probs)
    return {"job_id": job_id, "read_idx": read_idx, "rating": r.rating, "ok": r.ok, "ev": r.ev,
            "p_none": r.p_none, "choice": (answer or {}).get("choice"), "confidence": (answer or {}).get("confidence"),
            "probabilities": probs, "model": model, "input_tokens": (usage or {}).get("input_tokens"),
            "cost": (usage or {}).get("cost"), "note": note, "spec": spec_sha256(), "timestamp": time.time()}


def sidecar_path(results: str | Path) -> Path:
    results = Path(results)
    return results.with_name(results.name + ".jev.jsonl")


def jitter_path(results: str | Path) -> Path:
    results = Path(results)
    return results.with_name(results.name + ".jev_jitter.jsonl")


def read_rows(path: str | Path) -> list[dict]:
    """Every row of a sidecar; [] if absent. Unreadable lines (a torn last write) are skipped."""
    path = Path(path)
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def read_sidecar(path: str | Path) -> dict[str, dict]:
    """job_id -> reading row (read_idx 0)."""
    return {r["job_id"]: r for r in read_rows(path) if r.get("read_idx", 0) == 0}


def question_texts(items: list[Item], manifest: dict) -> dict[str, str]:
    """prompt_id -> the question as asked, for every prompt in a run manifest.
    The full prompt is rebuilt (with or without the worked examples, as the
    manifest says) and must hash to the manifest's text_sha256, so the question
    Jev sees is the one the model was asked."""
    examples = protocol.EXAMPLES if elicit.run_field(manifest, "examples") else ()
    specs = {s.stem: s for s in prompts.build_subject_prompts(items, examples)}
    by_id = {i.item_id: i for i in items}
    out, bad = {}, []
    for pid, sha in manifest["prompts"].items():
        item_id, qkey, wording_key, _ = prompts.parse_prompt_id(pid)
        spec = specs.get(f"{item_id}::{qkey}::{wording_key}")
        if spec is None or spec.text_sha256 != sha:
            bad.append(pid)
            continue
        wording = next(w for w in protocol.QUESTIONS[qkey] if w.key == wording_key)
        out[pid] = prompts.render_question(by_id[item_id], wording.template)
    if bad:
        raise ValueError(f"{len(bad)} prompt(s) in the manifest can't be rebuilt from the items file with the "
                         f"same text, e.g. {bad[:5]}")
    return out


def frame_readings(job_ids, results_path: str | Path, reader: str) -> tuple[list, list[bool]]:
    """(values, ok) for each job_id from the results' sidecar: the top option
    ("jev") or the expected value where a number is on top ("jev_ev")."""
    sidecar = sidecar_path(results_path)
    readings = read_sidecar(sidecar)
    missing = [j for j in job_ids if j not in readings]
    if missing:
        raise ValueError(f"{results_path}: {len(missing)} row(s) have no Jev reading in {sidecar}, "
                         f"e.g. {missing[:5]}")
    rows = [readings[j] for j in job_ids]
    spec = spec_sha256()
    stale = sorted({r.get("spec") for r in rows} - {spec}, key=str)
    if stale:
        raise ValueError(f"{sidecar}: readings made under another reader spec ({stale[:3]}; now {spec[:12]}): "
                         f"delete the sidecar and re-read with tools/jev_read.py")
    values = [r["rating"] if reader == "jev" else (r["ev"] if r["ok"] else None) for r in rows]
    return values, [bool(r["ok"]) for r in rows]
