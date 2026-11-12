"""kmp/jev_native.py and tools/jev_native.py: Jev as the subject, asked natively
(the scenario as its state, each question as its own Choice over 0..10 bubbles),
with no chat-prompt wrapper."""
import importlib.util
import json
import math
import urllib.error

import pandas as pd
import pytest

from conftest import STUDY_DIR, make_items, make_ngo_verbatim_items
from kmp import jev, jev_native, prompts, protocol
from kmp.items import write_items


@pytest.fixture(autouse=True)
def _no_backoff_sleep(monkeypatch):
    import time
    monkeypatch.setattr(time, "sleep", lambda s: None)


def _tool():
    spec = importlib.util.spec_from_file_location("jev_native_tool", STUDY_DIR / "tools" / "jev_native.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _probs(top: str, p: float = 0.8) -> dict[str, float]:
    rest = (1 - p) / (len(jev.LEVELS) - 1)
    return {lv: (p if lv == top else rest) for lv in jev.LEVELS}


class FakeJev:
    """Picks bubble 8 for a bad side effect and 3 for a good one (the scenarios
    carry [bad]/[good] markers), on every wording, reversed ones included."""

    def __init__(self, fail: int | None = None, empty: bool = False):
        self.calls, self.fail, self.empty = [], fail, empty

    def __call__(self, body: dict) -> dict:
        self.calls.append(body)
        if self.fail:
            raise urllib.error.HTTPError("u", self.fail, "x", None, None)
        top = "8" if "[bad]" in body["state"]["scenario"] else "3"
        probs = {lv: 0.0 for lv in jev.LEVELS} if self.empty else _probs(top)
        return {"model": "typesafe/jev-1.14-20261014",
                "answers": {jev.QUESTION_KEY: {"type": "choice", "choice": top, "confidence": 0.8,
                                               "probabilities": probs}},
                "usage": {"input_tokens": 90, "output_tokens": 0, "cost": 2e-5}}


# --- the sheet --------------------------------------------------------------------------

def test_anchors_are_read_from_each_wording_template():
    assert jev_native.anchors(protocol.wording("intentionality", "w1").template) == {}
    assert jev_native.anchors(protocol.wording("intentionality", "w2").template) == {0: "not at all", 10: "completely"}
    assert jev_native.anchors(protocol.wording("intentionality", "w3r").template) == {
        0: "completely intentionally", 10: "not at all intentionally"}
    assert jev_native.anchors(protocol.wording("blame", "w3r").template) == {0: "extremely", 10: "not at all"}
    assert jev_native.anchors(protocol.wording("valence", "w1").template) == {
        0: "very bad", 5: "neither good nor bad", 10: "very good"}


def test_every_scale_wording_puts_its_anchors_on_the_end_bubbles():
    for qkey, wordings in protocol.QUESTIONS.items():
        for w in wordings:
            a = jev_native.anchors(w.template)
            if "scale" in w.template:
                assert {0, 10} <= set(a), (qkey, w.key)
            else:
                assert a == {}, (qkey, w.key)


def test_bubbles_label_anchored_numbers_and_leave_the_rest_bare():
    b = jev_native.bubbles(protocol.wording("blame", "w1").template)
    assert list(b) == list(jev.LEVELS)                       # 0..10, in order, no "none"
    assert b["0"] == "0 (not at all)" and b["10"] == "10 (extremely)"
    assert [b[str(i)] for i in range(1, 10)] == [str(i) for i in range(1, 10)]
    bare = jev_native.bubbles(protocol.wording("intentionality", "w1").template)
    assert bare == {lv: lv for lv in jev.LEVELS}


def test_questions_are_the_chat_models_questions_item_by_item():
    items = make_items("nonmoral", 2) + make_ngo_verbatim_items(1)
    qs = jev_native.build_questions(items)
    specs = prompts.build_subject_prompts(items, ())
    assert [q.stem for q in qs] == [s.stem for s in specs]       # same item x question x wording cells
    by_id = {i.item_id: i for i in items}
    for q in qs:
        w = protocol.wording(q.qkey, q.wording_key)
        assert q.text == prompts.render_question(by_id[q.item_id], w.template)
        assert q.reversed == w.reversed
        assert q.job_id == f"{q.stem}::{jev_native.FMT}"


def test_request_has_only_the_scenario_and_the_question_no_wrapper():
    [item] = [i for i in make_ngo_verbatim_items(1) if i.sign == "bad"]
    q = next(q for q in jev_native.build_questions([item]) if (q.qkey, q.wording_key) == ("blame", "w1"))
    body = jev_native.request_body(q)
    assert body["model"] == jev.MODEL
    assert body["state"] == {"scenario": item.scenario}
    rq = body["questions"][jev.QUESTION_KEY]
    assert rq == {"type": "choice", "instructions": q.text, "criteria": jev_native.bubbles(
        protocol.wording("blame", "w1").template)}
    sent = json.dumps(body)
    assert protocol.INSTRUCTION not in sent                   # no chat instruction line
    assert "Answer:" not in sent and "Scenario:" not in sent  # no chat frame
    assert all(ex not in sent for ex, _, _ in protocol.EXAMPLES)  # no worked examples


def test_answer_row_reads_top_bubble_and_expected_value():
    q = jev_native.build_questions(make_ngo_verbatim_items(1))[0]
    probs = {**{lv: 0.0 for lv in jev.LEVELS}, "2": 0.25, "6": 0.25, "9": 0.5}
    data = {"model": "typesafe/jev-1.14-20261014", "usage": {"cost": 1e-5, "input_tokens": 80},
            "answers": {jev.QUESTION_KEY: {"choice": "9", "confidence": 0.5, "probabilities": probs}}}
    row = jev_native.answer_row(q, data)
    assert row["job_id"] == q.job_id and row["top"] == 9
    assert math.isclose(row["ev"], (2 * .25 + 6 * .25 + 9 * .5))
    assert row["body_sha256"] == jev_native.body_sha256(jev_native.request_body(q))
    tie = {**{lv: 0.0 for lv in jev.LEVELS}, "3": 0.5, "7": 0.5}
    assert jev_native.answer_row(q, {**data, "answers": {jev.QUESTION_KEY: {"probabilities": tie}}})["top"] == 3
    empty = {lv: 0.0 for lv in jev.LEVELS}
    assert jev_native.answer_row(q, {**data, "answers": {jev.QUESTION_KEY: {"probabilities": empty}}}) is None


# --- the run ----------------------------------------------------------------------------

def _elicit(tool, tmp_path, monkeypatch, transport, items=None, extra=()):
    monkeypatch.setenv("OPENROUTER_API_KEY", "k")
    items = items or make_items("nonmoral", 2)
    items_csv, out = tmp_path / "items.csv", tmp_path / "jev_native.jsonl"
    write_items(items, items_csv)
    rc = tool.main(["elicit", "--items", str(items_csv), "--out", str(out), *extra], transport=transport)
    return rc, items, items_csv, out


def test_elicit_asks_every_question_once_and_resumes(tmp_path, monkeypatch):
    tool = _tool()
    t = FakeJev()
    rc, items, _, out = _elicit(tool, tmp_path, monkeypatch, t)
    assert rc == 0
    qs = jev_native.build_questions(items)
    rows = jev_native.read_results(out)
    assert len(t.calls) == len(qs) == len(rows)
    assert {b["state"]["scenario"] for b in t.calls} == {i.scenario for i in items}
    assert all(r["top"] == (8 if "-bad::" in r["job_id"] else 3) for r in rows.values())
    manifest = json.loads(jev_native.manifest_path(out).read_text())
    assert manifest["spec"] == jev_native.SPEC and manifest["n_questions"] == len(qs)
    assert manifest["bodies"] == {q.job_id: jev_native.body_sha256(jev_native.request_body(q)) for q in qs}
    t2 = FakeJev()
    rc, _, _, _ = _elicit(tool, tmp_path, monkeypatch, t2)
    assert rc == 0 and t2.calls == []                       # resumed: nothing left


def test_elicit_reports_failed_or_empty_answers_and_writes_nothing_for_them(tmp_path, monkeypatch):
    tool = _tool()
    rc, _, _, out = _elicit(tool, tmp_path, monkeypatch, FakeJev(fail=400))
    assert rc == 1 and jev_native.read_results(out) == {}
    rc, _, _, out = _elicit(tool, tmp_path, monkeypatch, FakeJev(empty=True))
    assert rc == 1 and jev_native.read_results(out) == {}


def test_elicit_refuses_draft_items_unless_allowed(tmp_path, monkeypatch):
    tool = _tool()
    drafts = make_items("nonmoral", 2, status="draft")
    rc, *_ = _elicit(tool, tmp_path, monkeypatch, FakeJev(), items=drafts)
    assert rc == 2
    rc, *_ = _elicit(tool, tmp_path, monkeypatch, FakeJev(), items=drafts, extra=["--allow-draft"])
    assert rc == 0


# --- the frame and the analysis ---------------------------------------------------------

def test_native_frame_recodes_reversed_bubbles_and_feeds_the_existing_fits(tmp_path, monkeypatch):
    tool = _tool()
    _, items, _, out = _elicit(tool, tmp_path, monkeypatch, FakeJev())
    f = jev_native.native_frame(out, items, reader="top")
    assert set(f["model_key"]) == {jev_native.MODEL_KEY} and set(f["fmt"]) == {jev_native.FMT}
    bad_blame = f[(f["sign"] == "bad") & (f["qkey"] == "blame")].set_index("wording_key")["rating"]
    assert (bad_blame["w1"] == 8).all() and (bad_blame["w3r"] == 2).all()   # 10 - 8: the reversed bubble
    ev = jev_native.native_frame(out, items, reader="ev")
    expect = sum(int(k) * v for k, v in _probs("8").items())
    bad_ev = ev[(ev["sign"] == "bad") & (ev["qkey"] == "blame")].set_index("wording_key")["rating"]
    assert all(math.isclose(x, expect) for x in bad_ev["w1"])
    assert all(math.isclose(x, 10 - expect) for x in bad_ev["w3r"])
    assert {"cluster_id", "sign_c", "tuning_status", "family", "experiment", "arm"} <= set(f.columns)


def test_native_frame_refuses_answers_to_a_different_sheet(tmp_path, monkeypatch):
    tool = _tool()
    _, items, _, out = _elicit(tool, tmp_path, monkeypatch, FakeJev())
    rows = [json.loads(line) for line in out.read_text().splitlines()]
    rows[0]["body_sha256"] = "0" * 64
    out.write_text("".join(json.dumps(r) + "\n" for r in rows))
    with pytest.raises(ValueError, match="different question"):
        jev_native.native_frame(out, items)


def test_analyze_writes_checks_sign_and_arm_tables_for_both_readers(tmp_path, monkeypatch):
    tool = _tool()
    _, _, items_csv, out = _elicit(tool, tmp_path, monkeypatch, FakeJev(), items=make_items("nonmoral", 6))
    outputs = tmp_path / "outputs"
    rc = tool.main(["analyze", "--items", str(items_csv), "--results", str(out), "--name", "jn",
                    "--experiment", "nonmoral", "--outputs", str(outputs)])
    assert rc == 0
    for reader_name in ("jn", "jn_ev"):
        s = pd.read_csv(outputs / "first_look" / f"{reader_name}_sign_effects.csv")
        assert set(s["qkey"]) == {"intentionality", "blame", "praise", "significance"}
        a = pd.read_csv(outputs / "first_look" / f"{reader_name}_arm_effects.csv")
        assert "moral_vs_rest" in set(a["arm"])
        assert {p.name for p in (outputs / "checks" / reader_name).iterdir()} == {
            "coverage.csv", "anchor_agreement.csv", "validity.csv", "wording_means.csv"}
    s = pd.read_csv(outputs / "first_look" / "jn_sign_effects.csv").set_index("qkey")
    # FakeJev fills in 8 / 3 on every wording, reversed too: pooled (8 + 8 + 2) / 3 and (3 + 3 + 7) / 3
    assert s.loc["intentionality", "mean_bad"] == 6 and math.isclose(s.loc["intentionality", "mean_good"], 13 / 3)
    w = pd.read_csv(outputs / "checks" / "jn" / "wording_means.csv").set_index(["qkey", "wording_key"])
    assert w.loc[("blame", "w3r"), "bad"] == 2                # same bubble on a reversed sheet -> recoded 2
    cov = pd.read_csv(outputs / "checks" / "jn" / "coverage.csv")
    assert (cov["n_rows"] > 0).all()
