"""tools/jev_subject.py: Jev as a subject model, rating the scenarios itself."""
import argparse
import importlib.util
import json
import math
import urllib.error

import pytest
from knobe.elicit_vllm import EngineRequest
from knobe.analysis.ingest import build_model_key_index
from knobe.registry import load_registry
from knobe.schemas import ResultRecord, read_jsonl

from conftest import STUDY_DIR, make_items
from kmp import elicit, frame, jev, prompts, protocol
from kmp.items import write_items


# Jev has no pretrained checkpoint, and the registry says so (correctly) for every load.
pytestmark = pytest.mark.filterwarnings("ignore:family 'jev-1.14' .* missing its \\['pretrained'\\]")


@pytest.fixture(autouse=True)
def _no_backoff_sleep(monkeypatch):
    """The client's retry backoff sleeps up to a minute; no test here should wait."""
    import time
    monkeypatch.setattr(time, "sleep", lambda s: None)


def _tool():
    spec = importlib.util.spec_from_file_location("jev_subject", STUDY_DIR / "tools" / "jev_subject.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _probs(top: str, p: float = 0.8) -> dict[str, float]:
    rest = (1 - p) / (len(jev.LEVELS) - 1)
    return {lv: (p if lv == top else rest) for lv in jev.LEVELS}


def _ev(probs: dict[str, float]) -> float:
    return sum(int(k) * v for k, v in probs.items()) / sum(probs.values())


class FakeSubject:
    """Rates a bad side effect 8 and a good one 3 (the scenarios carry [bad]/[good] markers)."""

    def __init__(self, fail: int | None = None):
        self.calls, self.fail = [], fail

    def __call__(self, body: dict) -> dict:
        self.calls.append(body)
        if self.fail:
            raise urllib.error.HTTPError("u", self.fail, "x", None, None)
        top = "8" if "[bad]" in body["state"]["prompt"] else "3"
        return {"model": "typesafe/jev-1.14-20261014",
                "answers": {jev.QUESTION_KEY: {"type": "choice", "choice": top, "confidence": 0.8,
                                               "probabilities": _probs(top)}},
                "usage": {"input_tokens": 120, "output_tokens": 0, "cost": 5e-6}}


def _request(job_id: str, text: str) -> EngineRequest:
    return EngineRequest(job_id=job_id, prompt_id="p", temperature=1.0, seed=1, max_tokens=8,
                         want_first_token_logprobs=False, messages=[{"role": "user", "content": text}])


def test_body_sends_the_exact_prompt_with_eleven_numbers_and_no_none():
    tool = _tool()
    body = tool.subject_body("Scenario: x\n\nQuestion: y\nAnswer:")
    assert body["model"] == jev.MODEL
    assert body["state"] == {"prompt": "Scenario: x\n\nQuestion: y\nAnswer:"}
    q = body["questions"][jev.QUESTION_KEY]
    assert q["type"] == "choice"
    assert list(q["criteria"]) == list(jev.LEVELS)


def test_engine_answers_with_the_top_number_and_logs_the_probabilities(tmp_path):
    tool = _tool()
    probs_path = tmp_path / "r.jsonl.jev_probs.jsonl"
    engine = tool.JevSubjectEngine(tool.DecisionsClient("k", transport=FakeSubject()), probs_path)
    assert engine.load(jev.MODEL) == f"openrouter:{jev.MODEL}"
    [resp] = engine.generate([_request("j1", "A story. [bad]")])
    assert (resp.job_id, resp.raw_response) == ("j1", "8")
    [row] = jev.read_rows(probs_path)
    assert row["job_id"] == "j1" and row["top"] == 8 and row["spec"] == tool.SPEC
    assert math.isclose(row["ev"], _ev(_probs("8")))


def test_engine_leaves_a_failed_call_missing_and_refuses_other_models(tmp_path):
    tool = _tool()
    probs_path = tmp_path / "p.jsonl"
    engine = tool.JevSubjectEngine(tool.DecisionsClient("k", transport=FakeSubject(fail=400)), probs_path)
    assert engine.generate([_request("j1", "A story. [bad]")]) == []
    assert jev.read_rows(probs_path) == []
    with pytest.raises(ValueError):
        engine.load("google/gemma-3-4b-it")


def _elicit(tool, tmp_path, monkeypatch, transport):
    monkeypatch.setenv("OPENROUTER_API_KEY", "k")
    items = make_items("nonmoral", 2)
    items_csv, out = tmp_path / "items.csv", tmp_path / "jev.jsonl"
    write_items(items, items_csv)
    rc = tool.main(["elicit", "--items", str(items_csv), "--out", str(out)], transport=transport)
    return rc, items, out


def test_elicit_writes_one_answer_per_prompt_through_kmp_elicit_and_resumes(tmp_path, monkeypatch):
    tool = _tool()
    t = FakeSubject()
    before = elicit.build_engine
    rc, items, out = _elicit(tool, tmp_path, monkeypatch, t)
    assert rc == 0
    assert elicit.build_engine is before                            # the engine swap doesn't outlive the run
    specs = prompts.build_subject_prompts(items, ())               # no worked examples
    rows = list(read_jsonl(out, ResultRecord))
    assert len(rows) == len(specs) == len(t.calls)                  # one call per prompt, sample 0
    assert {r.sample_idx for r in rows} == {0}
    assert {r.model_key for r in rows} == {tool.MODEL_KEY}
    assert {b["state"]["prompt"] for b in t.calls} == {s.text for s in specs}
    assert all(r.parse_ok and r.parsed_rating == (8 if "-bad::" in r.job_id else 3) for r in rows)
    assert elicit.run_field(json.loads(elicit.manifest_path(out).read_text()), "examples") is False

    t2 = FakeSubject()
    rc, _, _ = _elicit(tool, tmp_path, monkeypatch, t2)
    assert rc == 0 and t2.calls == []                               # resumed: nothing left to do


def test_elicit_reports_missing_answers(tmp_path, monkeypatch):
    tool = _tool()
    rc, _, out = _elicit(tool, tmp_path, monkeypatch, FakeSubject(fail=400))
    assert rc == 1 and list(read_jsonl(out, ResultRecord)) == []


def test_ev_writes_the_expected_value_as_the_rating(tmp_path, monkeypatch):
    tool = _tool()
    _, _, out = _elicit(tool, tmp_path, monkeypatch, FakeSubject())
    assert tool.main(["ev", "--results", str(out)]) == 0
    ev_rows = list(read_jsonl(tool.ev_path(out), ResultRecord))
    rows = {r.job_id: r for r in read_jsonl(out, ResultRecord)}
    assert len(ev_rows) == len(rows)
    for r in ev_rows:
        top = str(int(rows[r.job_id].parsed_rating))
        assert r.parse_ok and math.isclose(r.parsed_rating, _ev(_probs(top)))


def test_ev_refuses_answers_without_probabilities(tmp_path, monkeypatch):
    tool = _tool()
    _, _, out = _elicit(tool, tmp_path, monkeypatch, FakeSubject())
    probs = tool.probs_path(out)
    probs.write_text("\n".join(probs.read_text().splitlines()[1:]) + "\n")
    with pytest.raises(ValueError, match="no probabilities"):
        tool.main(["ev", "--results", str(out)])


def test_registry_resolves_jev_and_the_frame_reads_its_answers(tmp_path, monkeypatch):
    tool = _tool()
    registry = load_registry(tool.REGISTRY)
    assert tool.MODEL_KEY in build_model_key_index(registry)
    assert prompts.format_for_model(tool.MODEL_KEY) == "chat"
    _, items, out = _elicit(tool, tmp_path, monkeypatch, FakeSubject())
    d = frame.load_frame(out, items, registry=registry)
    assert set(d["family"]) == {"jev"}
    bad_w1 = d[(d["sign"] == "bad") & (d["qkey"] == "intentionality") & (d["wording_key"] == "w1")]
    bad_w3r = d[(d["sign"] == "bad") & (d["qkey"] == "intentionality") & (d["wording_key"] == "w3r")]
    assert set(bad_w1["rating"]) == {8} and set(bad_w3r["rating"]) == {2}   # reversed wording recoded


def test_analyze_takes_a_registry(monkeypatch, tmp_path):
    spec = importlib.util.spec_from_file_location("orfl", STUDY_DIR / "tools" / "openrouter_first_look.py")
    orfl = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(orfl)
    import sys
    sys.path.insert(0, str(STUDY_DIR / "analysis"))
    import first_look
    seen = {}
    monkeypatch.setattr(first_look, "main", lambda argv: seen.setdefault("registry", frame.default_registry_path()) and 0)
    reg = STUDY_DIR / "tools" / "jev_models.yaml"
    a = argparse.Namespace(name="x", results=[tmp_path / "r.jsonl"], items=tmp_path / "i.csv", reparse=False,
                           reader="regex", no_checks=True, registry=reg)
    monkeypatch.setattr(frame, "default_registry_path", frame.default_registry_path)
    monkeypatch.setattr(frame, "READER", frame.READER)
    monkeypatch.setattr(frame, "REPARSE", frame.REPARSE)
    assert orfl.cmd_analyze(a) == 0
    assert seen["registry"] == reg


def test_checks_writes_the_kmp_checks_that_apply_and_the_means_per_wording(tmp_path, monkeypatch):
    tool = _tool()
    _, _, out = _elicit(tool, tmp_path, monkeypatch, FakeSubject())   # 8 for bad, 3 for good, every wording
    items_csv, out_dir = tmp_path / "items.csv", tmp_path / "checks"
    assert tool.main(["checks", "--results", str(out), "--items", str(items_csv), "--out-dir", str(out_dir)]) == 0
    assert {p.name for p in out_dir.iterdir()} == {"coverage.csv", "number_rates.csv", "anchor_agreement.csv",
                                                   "validity.csv", "wording_means.csv"}
    import pandas as pd
    anchor = pd.read_csv(out_dir / "anchor_agreement.csv").set_index("qkey")
    assert anchor.loc["blame", "r"] < 0                     # a fixed answer reads backwards once recoded
    w = pd.read_csv(out_dir / "wording_means.csv").set_index(["qkey", "wording_key"])
    assert (w.loc[("blame", "w1"), "bad"], w.loc[("blame", "w3r"), "bad"]) == (8, 2)
    assert w.loc[("blame", "w1"), "bad_minus_good"] == 5
