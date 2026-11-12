"""Jev as a subject model, WRAPPED: Jev answers the chat models' prompt, as the chat models did.

Not the native test (2026-11-12): this hands Jev the whole chat prompt as its
state and one meta-question ("answer the question at the end of `prompt`"),
then feeds its pick back through the chat-reply pipeline. Jev asked natively --
the scenario as its state, each question as its own labelled 0..10 Choice -- is
kmp/jev_native.py + tools/jev_native.py. This run is kept as the wrapped contrast.

Why (Parker, 2026-10-22): "did jev recover the original paper ... i care about
jev now" -- does Jev, asked Ngo et al. (2015)'s questions, rate a bad foreseen
side effect as more intentional than a good one? tools/jev_read.py uses Jev to
read other models' replies; this asks Jev the questions.

What Jev sees: the exact prompt text the chat models got
(kmp.prompts.build_subject_prompts), as its state, without the worked
examples -- they only teach the answer format, and Jev can only answer with
one of its options. One Choice question over "0".."10", with no "none": like a
participant, Jev has to answer. One call per prompt (sample 0): Jev is close
to deterministic (as a reader its top option changed on at most 0.56% of
re-reads), so eight samples would repeat one answer; its probability vector
stands in for the spread of samples.

Readouts:
- the top option is the written answer (raw_response, read by kmp.answer like
  any reply), so the run goes through kmp.frame, analysis/first_look.py and
  kmp.checks unchanged (tools/openrouter_first_look.py analyze --registry
  tools/jev_models.yaml);
- the probabilities go to <out>.jev_probs.jsonl, and `ev` writes
  <out stem>_ev.jsonl, whose rating is the expected value over 0..10 -- the
  counterpart of a chat model's mean over its samples -- for the same analysis.

From the study folder with OPENROUTER_API_KEY set:
    ../../.venv/bin/python tools/jev_subject.py elicit --items <items.csv> --out <run.jsonl> [--allow-draft]
    ../../.venv/bin/python tools/jev_subject.py ev --results <run.jsonl> [...]
    ../../.venv/bin/python tools/jev_subject.py checks --results <run.jsonl> --items <items.csv> --out-dir <dir>

checks: kmp.checks refuses a no-examples run as --results (its example-copying
check needs examples), so this writes the kmp.checks tables that do apply --
coverage, number_rates, anchor_agreement (normal vs reversed wording),
validity -- with kmp.checks' own functions, plus wording_means: the bad and
good mean per question x wording, after recoding.
"""
from __future__ import annotations

import argparse
import dataclasses
import fcntl
import hashlib
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

STUDY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STUDY))

import pandas as pd  # noqa: E402
from knobe.elicit_vllm import EngineResponse  # noqa: E402
from knobe.registry import load_registry, model_key_for  # noqa: E402
from knobe.schemas import ResultRecord, append_jsonl, read_jsonl  # noqa: E402

from kmp import checks, elicit, jev, prompts  # noqa: E402
from kmp.frame import analysis_rows, load_frame  # noqa: E402
from kmp.items import design_problems, load_items  # noqa: E402
from tools.jev_read import DecisionsClient  # noqa: E402

REGISTRY = STUDY / "tools" / "jev_models.yaml"
MODEL_KEY = model_key_for("jev-1.14", "finetuned")   # the registry's key convention; Jev is not an instruct model
INSTRUCTIONS = "Answer the question at the end of `prompt` as `prompt` asks: with one whole number from 0 to 10."
CRITERIA = {lv: f"The answer is {lv}." for lv in jev.LEVELS}


def subject_body(text: str) -> dict:
    return {"model": jev.MODEL, "state": {"prompt": text},
            "questions": {jev.QUESTION_KEY: {"type": "choice", "instructions": INSTRUCTIONS, "criteria": CRITERIA}}}


def spec_sha256() -> str:
    """Fingerprint of what Jev is asked, stored on every probabilities row."""
    spec = {"model": jev.MODEL, "question_key": jev.QUESTION_KEY, "instructions": INSTRUCTIONS,
            "criteria": CRITERIA, "state": ["prompt"]}
    return hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()


SPEC = spec_sha256()


def probs_path(results: str | Path) -> Path:
    results = Path(results)
    return results.with_name(results.name + ".jev_probs.jsonl")


def ev_path(results: str | Path) -> Path:
    results = Path(results)
    return results.with_name(results.name.removesuffix(".jsonl") + "_ev.jsonl")


class JevSubjectEngine:
    """knobe GenerationEngine over the Decisions API: the swap tools/openrouter_first_look.py
    makes for chat models, so kmp.elicit builds the jobs, resumes and writes the rows."""

    def __init__(self, client: DecisionsClient, probs_file: Path, concurrency: int = 32):
        self.client, self.probs_file, self.concurrency = client, Path(probs_file), concurrency
        self.cost = 0.0
        self._lock = threading.Lock()

    def load(self, model_id: str, *, revision: str = "main", **_: object) -> str:
        if model_id != jev.MODEL:
            raise ValueError(f"JevSubjectEngine serves {jev.MODEL}, not {model_id}")
        return f"openrouter:{model_id}"

    def _one(self, req) -> EngineResponse | None:
        text = req.messages[0]["content"] if req.messages is not None else req.text
        data = self.client.decide(req.job_id, subject_body(text))
        if data is None:
            return None
        answer = data["answers"][jev.QUESTION_KEY]
        probs = {lv: float(answer["probabilities"].get(lv, 0.0)) for lv in jev.LEVELS}
        mass = sum(probs.values())
        if mass <= 0:
            print(f"[jev] {req.job_id}: no probability on any number", file=sys.stderr)
            return None
        top = max(jev.LEVELS, key=lambda lv: probs[lv])       # ties go to the lower number
        usage = data.get("usage") or {}
        row = {"job_id": req.job_id, "top": int(top), "ev": sum(int(lv) * p for lv, p in probs.items()) / mass,
               "probabilities": answer["probabilities"], "choice": answer.get("choice"),
               "confidence": answer.get("confidence"), "model": data.get("model"),
               "input_tokens": usage.get("input_tokens"), "cost": usage.get("cost"), "spec": SPEC,
               "timestamp": time.time()}
        with self._lock:                       # written before kmp.elicit writes the result row
            with open(self.probs_file, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(row) + "\n")
            self.cost += usage.get("cost") or 0.0
        return EngineResponse(job_id=req.job_id, raw_response=top, logprobs_0_10=None)

    def generate(self, batch) -> list[EngineResponse]:
        with ThreadPoolExecutor(self.concurrency) as ex:
            return [r for r in ex.map(self._one, batch) if r is not None]


def cmd_elicit(a: argparse.Namespace, transport=None) -> int:
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        print("OPENROUTER_API_KEY is not set", file=sys.stderr)
        return 2
    items = load_items(a.items)
    if a.allow_draft:                          # pilot texts, run as written (as tools/openrouter_first_look.py)
        problems = [f"{i.item_id} is {i.review_status}" for i in items if i.review_status == "rejected"]
    else:
        problems = design_problems(items, stage="selected") + \
            [f"{i.item_id} is {i.review_status}" for i in items if i.review_status != "approved"]
    if problems:
        print("refusing to run:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 2
    specs = [dataclasses.replace(s, n_samples=1) for s in prompts.build_subject_prompts(items, ())]
    jobs = elicit.build_jobs(specs, [MODEL_KEY])

    client = DecisionsClient(api_key, transport=transport)
    engine = JevSubjectEngine(client, probs_path(a.out), concurrency=a.concurrency)
    run_args = argparse.Namespace(out=a.out, engine="jev", registry=REGISTRY, batch_size=a.batch_size,
                                  max_tokens=elicit.max_tokens_by_format(None), no_examples=True)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    print(f"[jev] {len(jobs)} prompts -> {a.out}")
    t0 = time.time()
    with open(elicit.lock_path(a.out), "a") as lock_fh:
        try:
            fcntl.flock(lock_fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(f"another run holds {elicit.lock_path(a.out)}", file=sys.stderr)
            return 2
        build_engine, elicit.build_engine = elicit.build_engine, lambda name: engine   # the only swap
        try:
            rc = elicit._run_locked(run_args, jobs, [MODEL_KEY])
        finally:
            elicit.build_engine = build_engine
    print(f"[jev] rc={rc} in {time.time() - t0:.0f}s; cost ${engine.cost:.4f}; retried errors {dict(client.errors)}")
    return rc


def cmd_ev(a: argparse.Namespace) -> int:
    for res in a.results:
        last = {r["job_id"]: r for r in jev.read_rows(probs_path(res))}
        rows = list(read_jsonl(res, ResultRecord))
        missing = [r.job_id for r in rows if r.job_id not in last]
        if missing:
            raise ValueError(f"{res}: {len(missing)} answer(s) have no probabilities in {probs_path(res)}, "
                             f"e.g. {missing[:5]}")
        stale = sorted({last[r.job_id]["spec"] for r in rows} - {SPEC})
        if stale:
            raise ValueError(f"{probs_path(res)}: probabilities made under another spec {stale[:3]}")
        out = ev_path(res)
        with open(out, "w", encoding="utf-8") as fh:
            for r in rows:
                append_jsonl(r.model_copy(update={"parsed_rating": last[r.job_id]["ev"], "parse_ok": True}), fh)
        print(f"[jev] {len(rows)} expected values -> {out}")
    return 0


def wording_means(frame: pd.DataFrame) -> pd.DataFrame:
    """Bad and good mean rating per model x question x wording, after recoding."""
    m = (analysis_rows(frame).groupby(["model_key", "qkey", "wording_key", "reversed", "sign"])["rating"].mean()
         .unstack("sign").reindex(columns=["bad", "good"]).reset_index())
    m["bad_minus_good"] = m["bad"] - m["good"]
    return m


def cmd_checks(a: argparse.Namespace) -> int:
    items = load_items(a.items)
    frame = load_frame(a.results, items, registry=load_registry(REGISTRY))
    tables = {"coverage": checks.coverage(frame, items, [MODEL_KEY]), "number_rates": checks.number_rates(frame),
              "anchor_agreement": checks.anchor_agreement(frame), "validity": checks.validity(frame),
              "wording_means": wording_means(frame)}
    a.out_dir.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        table.to_csv(a.out_dir / f"{name}.csv", index=False)
        print(f"\n== {name}\n{table.to_string(index=False)}")
    return 0


def main(argv: list[str] | None = None, transport=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("elicit")
    e.add_argument("--items", required=True, type=Path)
    e.add_argument("--out", required=True, type=Path)
    e.add_argument("--concurrency", type=int, default=32)
    e.add_argument("--batch-size", type=int, default=256)
    e.add_argument("--allow-draft", action="store_true",
                   help="run draft items as written (pilot texts), skipping the approval and design checks")
    v = sub.add_parser("ev")
    v.add_argument("--results", required=True, type=Path, nargs="+")
    c = sub.add_parser("checks")
    c.add_argument("--results", required=True, type=Path)
    c.add_argument("--items", required=True, type=Path)
    c.add_argument("--out-dir", required=True, type=Path)
    a = p.parse_args(argv)
    if a.cmd == "elicit":
        return cmd_elicit(a, transport)
    return cmd_ev(a) if a.cmd == "ev" else cmd_checks(a)


if __name__ == "__main__":
    raise SystemExit(main())
