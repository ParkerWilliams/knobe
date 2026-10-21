import importlib.util
import json
import math
import urllib.error

import pytest
from knobe.schemas import ResultRecord, append_jsonl

from conftest import STUDY_DIR, make_items
from kmp import elicit, frame, jev, prompts, protocol

IID = "kmp-nm-001-moral-bad"
MK = "gemma-2-9b-instruct"


@pytest.fixture(autouse=True)
def _no_backoff_sleep(monkeypatch):
    """The tool's retry backoff sleeps up to a minute; no test here should wait."""
    import time
    monkeypatch.setattr(time, "sleep", lambda s: None)


def _probs(top: str, p: float = 0.9) -> dict[str, float]:
    rest = (1 - p) / (len(jev.OPTIONS) - 1)
    return {o: (p if o == top else rest) for o in jev.OPTIONS}


def _write_results(path, rows):
    """rows: (prompt_id, regex value or None, raw_response)."""
    with open(path, "w", encoding="utf-8") as fh:
        for i, (pid, value, text) in enumerate(rows):
            append_jsonl(ResultRecord(
                job_id=f"{pid}::{MK}::{i}", prompt_id=pid, model_key=MK, sample_idx=i, temperature=1.0, seed=1,
                raw_response=text, parsed_rating=value, parse_ok=value is not None, parse_method="regex",
                logprobs_0_10=None, model_revision="r", runner_version="t", timestamp=0.0), fh)


def _write_sidecar(results, readings):
    """readings: job_id -> probabilities."""
    with open(jev.sidecar_path(results), "w", encoding="utf-8") as fh:
        for job_id, probs in readings.items():
            fh.write(json.dumps(jev.reading_row(job_id, {"probabilities": probs}, read_idx=0)) + "\n")


# --- the reading rule -------------------------------------------------------

def test_top_number_is_the_rating_and_ev_leaves_out_none():
    r = jev.read_choice({"7": 0.8, "6": 0.1, "none": 0.1})
    assert (r.rating, r.ok) == (7, True)
    assert r.ev == pytest.approx((7 * 0.8 + 6 * 0.1) / 0.9)
    assert r.p_none == pytest.approx(0.1)


def test_none_on_top_is_unparsed_but_keeps_its_ev():
    r = jev.read_choice({"none": 0.6, "3": 0.4})
    assert (r.rating, r.ok) == (None, False)
    assert r.ev == pytest.approx(3.0) and r.p_none == pytest.approx(0.6)


def test_all_mass_on_none_has_no_ev():
    r = jev.read_choice({"none": 1.0})
    assert (r.rating, r.ok, r.ev) == (None, False, None)


def test_ten_is_a_level_not_one_then_zero():
    assert jev.read_choice({"10": 0.7, "1": 0.2, "none": 0.1}).rating == 10


# --- the request ------------------------------------------------------------

def test_request_asks_one_choice_over_eleven_numbers_and_none():
    body = jev.request_body("How blameworthy is Bill?", "I'd say 7.")
    assert body["model"] == jev.MODEL == "typesafe/jev-1.14"
    assert body["state"] == {"question": "How blameworthy is Bill?", "reply": "I'd say 7."}
    q = body["questions"][jev.QUESTION_KEY]
    assert q["type"] == "choice"
    assert list(q["criteria"]) == [str(i) for i in range(11)] + ["none"]


def test_question_texts_recover_the_question_asked_and_check_the_prompt_hash():
    items = make_items("nonmoral", 1)
    jobs = elicit.build_jobs(prompts.build_subject_prompts(items), [MK])
    manifest = elicit.build_manifest(jobs, "fake", [MK], {"chat": 256, "raw": 10})
    q = jev.question_texts(items, manifest)
    assert set(q) == set(manifest["prompts"])
    item = next(i for i in items if i.item_id == IID)
    assert q[f"{IID}::blame::w3r::chat"] == prompts.render_question(item, protocol.QUESTIONS["blame"][2].template)


def test_question_texts_refuse_a_prompt_whose_text_changed():
    items = make_items("nonmoral", 1)
    jobs = elicit.build_jobs(prompts.build_subject_prompts(items), [MK])
    manifest = elicit.build_manifest(jobs, "fake", [MK], {"chat": 256, "raw": 10})
    manifest["prompts"][f"{IID}::blame::w1::chat"] = "0" * 64
    with pytest.raises(ValueError, match=f"{IID}::blame::w1::chat"):
        jev.question_texts(items, manifest)


def test_question_texts_follow_the_manifest_examples_flag():
    items = make_items("nonmoral", 1)
    jobs = elicit.build_jobs(prompts.build_subject_prompts(items, ()), [MK])
    manifest = elicit.build_manifest(jobs, "fake", [MK], {"chat": 256, "raw": 10}, examples=False)
    assert set(jev.question_texts(items, manifest)) == set(manifest["prompts"])


# --- the frame --------------------------------------------------------------

def test_reader_jev_replaces_the_reading_and_keeps_the_reversed_recode(tmp_path):
    path = tmp_path / "r.jsonl"
    _write_results(path, [(f"{IID}::blame::w1::chat", 8, "8"),
                          (f"{IID}::blame::w3r::chat", 2, "2"),
                          (f"{IID}::blame::w2::chat", 5, "5, or maybe 6")])
    _write_sidecar(path, {f"{IID}::blame::w1::chat::{MK}::0": _probs("7"),
                          f"{IID}::blame::w3r::chat::{MK}::1": _probs("3"),
                          f"{IID}::blame::w2::chat::{MK}::2": _probs("none")})
    d = frame.load_frame(path, make_items("nonmoral", 1), reader="jev").set_index("wording_key")
    assert d.loc["w1", "rating"] == 7 and d.loc["w3r", "rating"] == 7
    assert math.isnan(d.loc["w2", "rating"]) and not d.loc["w2", "parse_ok"]


def test_reader_regex_is_the_default(tmp_path):
    path = tmp_path / "r.jsonl"
    _write_results(path, [(f"{IID}::blame::w1::chat", 8, "8")])
    _write_sidecar(path, {f"{IID}::blame::w1::chat::{MK}::0": _probs("2")})
    assert frame.load_frame(path, make_items("nonmoral", 1))["rating"].iloc[0] == 8


def test_reader_jev_ev_uses_the_expected_value_where_a_number_is_on_top(tmp_path):
    path = tmp_path / "r.jsonl"
    _write_results(path, [(f"{IID}::blame::w1::chat", 8, "8"), (f"{IID}::blame::w2::chat", None, "no")])
    _write_sidecar(path, {f"{IID}::blame::w1::chat::{MK}::0": {"8": 0.5, "6": 0.5},
                          f"{IID}::blame::w2::chat::{MK}::1": {"none": 0.7, "4": 0.3}})
    d = frame.load_frame(path, make_items("nonmoral", 1), reader="jev_ev").set_index("wording_key")
    assert d.loc["w1", "rating"] == pytest.approx(7.0)
    assert math.isnan(d.loc["w2", "rating"])


def test_reader_jev_refuses_rows_without_a_reading(tmp_path):
    path = tmp_path / "r.jsonl"
    _write_results(path, [(f"{IID}::blame::w1::chat", 8, "8"), (f"{IID}::blame::w2::chat", 5, "5")])
    _write_sidecar(path, {f"{IID}::blame::w1::chat::{MK}::0": _probs("8")})
    with pytest.raises(ValueError, match="1 row"):
        frame.load_frame(path, make_items("nonmoral", 1), reader="jev")


def test_reader_jev_and_reparse_are_exclusive(tmp_path):
    path = tmp_path / "r.jsonl"
    _write_results(path, [(f"{IID}::blame::w1::chat", 8, "8")])
    _write_sidecar(path, {f"{IID}::blame::w1::chat::{MK}::0": _probs("8")})
    with pytest.raises(ValueError, match="reparse"):
        frame.load_frame(path, make_items("nonmoral", 1), reader="jev", reparse=True)


def test_unknown_reader_raises(tmp_path):
    path = tmp_path / "r.jsonl"
    _write_results(path, [(f"{IID}::blame::w1::chat", 8, "8")])
    with pytest.raises(ValueError, match="reader"):
        frame.load_frame(path, make_items("nonmoral", 1), reader="vibes")


def test_reader_jev_refuses_readings_made_under_another_reader_spec(tmp_path):
    path = tmp_path / "r.jsonl"
    _write_results(path, [(f"{IID}::blame::w1::chat", 8, "8")])
    row = jev.reading_row(f"{IID}::blame::w1::chat::{MK}::0", {"probabilities": _probs("8")})
    assert row["spec"] == jev.SPEC
    row["spec"] = "an-older-spec"
    jev.sidecar_path(path).write_text(json.dumps(row) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="spec"):
        frame.load_frame(path, make_items("nonmoral", 1), reader="jev")


def test_spec_changes_with_the_instructions(monkeypatch):
    before = jev.spec_sha256()
    monkeypatch.setattr(jev, "INSTRUCTIONS", jev.INSTRUCTIONS + " Also this.")
    assert jev.spec_sha256() != before


def test_sidecar_tolerates_a_torn_last_line(tmp_path):
    path = tmp_path / "r.jsonl"
    _write_sidecar(path, {"a": _probs("4")})
    with open(jev.sidecar_path(path), "a", encoding="utf-8") as fh:
        fh.write('{"job_id": "b", "rat')
    assert set(jev.read_sidecar(jev.sidecar_path(path))) == {"a"}


# --- the tool ---------------------------------------------------------------

def _tool():
    spec = importlib.util.spec_from_file_location("jev_read", STUDY_DIR / "tools" / "jev_read.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class FakeTransport:
    """Answers every Jev request with the first number in the answer (or none)."""

    def __init__(self, fail_first: dict[int, int] | None = None):
        self.calls = []
        self.fail_first = dict(fail_first or {})   # HTTP code -> times to fail before answering

    def __call__(self, body: dict) -> dict:
        self.calls.append(body)
        for code, n in self.fail_first.items():
            if n:
                self.fail_first[code] = n - 1
                raise urllib.error.HTTPError("u", code, "x", None, None)
        answer = body["state"]["reply"]
        top = next((t for t in answer.replace(".", " ").split() if t.isdigit() and int(t) <= 10), "none")
        return {"model": "typesafe/jev-1.14-20261001",
                "answers": {jev.QUESTION_KEY: {"type": "choice", "choice": top, "confidence": 0.9,
                                               "probabilities": _probs(top)}},
                "usage": {"input_tokens": 100, "output_tokens": 0, "cost": 4.2e-6}}


def _run_dir(tmp_path, texts):
    """A results file + manifest for the first len(texts) jobs of one nonmoral storyline."""
    items = make_items("nonmoral", 1)
    jobs = elicit.build_jobs(prompts.build_subject_prompts(items), [MK])[: len(texts)]
    manifest = elicit.build_manifest(jobs, "fake", [MK], {"chat": 256, "raw": 10})
    path = tmp_path / "r.jsonl"
    with open(path, "w", encoding="utf-8") as fh:
        for j, text in zip(jobs, texts):
            append_jsonl(ResultRecord(
                job_id=j.job_id, prompt_id=j.prompt_id, model_key=MK, sample_idx=j.sample_idx, temperature=1.0,
                seed=1, raw_response=text, parsed_rating=None, parse_ok=False, parse_method="regex",
                logprobs_0_10=None, model_revision="r", runner_version="t", timestamp=0.0), fh)
    elicit.write_manifest(manifest, elicit.manifest_path(path))
    return path, items, jobs


def test_read_writes_one_reading_per_row_and_resumes(tmp_path):
    tool = _tool()
    path, items, jobs = _run_dir(tmp_path, ["7", "I'd say 3.", "", "Yes."])
    t = FakeTransport()
    assert tool.read_file(path, items, tool.DecisionsClient("k", transport=t), concurrency=2) == 0
    got = jev.read_sidecar(jev.sidecar_path(path))
    assert set(got) == {j.job_id for j in jobs}
    assert [got[j.job_id]["rating"] for j in jobs] == [7, 3, None, None]
    assert got[jobs[2].job_id]["note"] == "empty reply" and got[jobs[2].job_id]["model"] is None
    assert len(t.calls) == 3                                   # the empty reply is not sent
    assert got[jobs[0].job_id]["model"] == "typesafe/jev-1.14-20261001"
    item_id, qkey, wording_key, _ = prompts.parse_prompt_id(jobs[0].prompt_id)
    assert t.calls[0]["state"]["question"] == prompts.render_question(
        next(i for i in items if i.item_id == item_id),
        next(w for w in protocol.QUESTIONS[qkey] if w.key == wording_key).template)
    t2 = FakeTransport()
    assert tool.read_file(path, items, tool.DecisionsClient("k", transport=t2), concurrency=2) == 0
    assert t2.calls == []


def test_read_sample_takes_a_fixed_subset_that_the_full_read_completes(tmp_path):
    tool = _tool()
    path, items, jobs = _run_dir(tmp_path, [str(i) for i in range(8)])
    t = FakeTransport()
    tool.read_file(path, items, tool.DecisionsClient("k", transport=t), sample=3)
    first = set(jev.read_sidecar(jev.sidecar_path(path)))
    assert len(first) == 3
    tool.read_file(path, items, tool.DecisionsClient("k", transport=FakeTransport()), sample=3)
    assert set(jev.read_sidecar(jev.sidecar_path(path))) == first
    tool.read_file(path, items, tool.DecisionsClient("k", transport=FakeTransport()))
    assert len(jev.read_sidecar(jev.sidecar_path(path))) == 8


def test_retryable_errors_are_retried(tmp_path, monkeypatch):
    tool = _tool()
    monkeypatch.setattr(tool.time, "sleep", lambda s: None)
    path, items, jobs = _run_dir(tmp_path, ["7"])
    t = FakeTransport(fail_first={429: 2})
    assert tool.read_file(path, items, tool.DecisionsClient("k", transport=t)) == 0
    assert len(t.calls) == 3 and jev.read_sidecar(jev.sidecar_path(path))[jobs[0].job_id]["rating"] == 7


def test_a_refused_request_is_left_missing_and_fails_the_run(tmp_path, monkeypatch):
    tool = _tool()
    monkeypatch.setattr(tool.time, "sleep", lambda s: None)
    path, items, jobs = _run_dir(tmp_path, ["7"])
    t = FakeTransport(fail_first={400: 1})
    assert tool.read_file(path, items, tool.DecisionsClient("k", transport=t)) == 1
    assert len(t.calls) == 1 and jev.read_sidecar(jev.sidecar_path(path)) == {}


def test_jitter_rereads_a_fixed_sample_and_resumes(tmp_path):
    tool = _tool()
    path, items, jobs = _run_dir(tmp_path, [str(i % 11) for i in range(40)])
    t = FakeTransport()
    assert tool.read_file(path, items, tool.DecisionsClient("k", transport=t), jitter=(0.25, 3)) == 0
    rows = [json.loads(line) for line in jev.jitter_path(path).read_text().splitlines()]
    sampled = {r["job_id"] for r in rows}
    assert sampled and len(sampled) < 40
    assert sorted({r["read_idx"] for r in rows}) == [1, 2, 3] and len(rows) == 3 * len(sampled)
    assert not jev.sidecar_path(path).exists()                 # jitter reads go to their own file
    t2 = FakeTransport()
    tool.read_file(path, items, tool.DecisionsClient("k", transport=t2), jitter=(0.25, 3))
    assert t2.calls == []


def test_compare_sorts_each_reply_into_agree_differ_or_one_reader_only(tmp_path, monkeypatch):
    tool = _tool()
    monkeypatch.setattr(tool, "STUDY", tmp_path)
    (tmp_path / "outputs" / "elicit").mkdir(parents=True)
    path = tmp_path / "r.jsonl"
    rows = [(f"{IID}::blame::w1::chat", 7, "7"),          # agree
            (f"{IID}::blame::w2::chat", 6.5, "6.5"),      # agree: a decimal is within 0.5 of Jev's 6
            (f"{IID}::blame::w3r::chat", 4, "4"),         # differ (Jev 2)
            (f"{IID}::praise::w1::chat", 5, "5?"),        # regex only
            (f"{IID}::praise::w2::chat", None, "nine"),   # jev only
            (f"{IID}::praise::w3r::chat", None, "no")]    # neither
    _write_results(path, rows)
    tops = ["7", "6", "2", "none", "9", "none"]
    _write_sidecar(path, {f"{pid}::{MK}::{i}": _probs(t) for i, ((pid, _, _), t) in enumerate(zip(rows, tops))})
    agreement, _ = tool.compare([path], "t", tmp_path / "tables")
    allrow = agreement.set_index("qkey").loc["ALL"]
    assert (allrow["agree"], allrow["differ"], allrow["regex_only"], allrow["jev_only"], allrow["neither"]) == \
        (2, 1, 1, 1, 1)
    assert allrow["both_ok"] == 3 and allrow["agree_rate"] == pytest.approx(2 / 3)
    assert agreement.set_index("qkey").loc["blame", "agree"] == 2
    dis = [json.loads(x) for x in (tmp_path / "outputs" / "elicit" / "t_reader_disagreements.jsonl").read_text().splitlines()]
    assert sorted(d["status"] for d in dis) == ["differ", "jev_only", "regex_only"]


def test_compare_reports_jitter_flips_and_ev_change(tmp_path, monkeypatch):
    tool = _tool()
    monkeypatch.setattr(tool, "STUDY", tmp_path)
    (tmp_path / "outputs" / "elicit").mkdir(parents=True)
    path = tmp_path / "r.jsonl"
    _write_results(path, [(f"{IID}::blame::w1::chat", 7, "7"), (f"{IID}::blame::w2::chat", 3, "3")])
    a, b = f"{IID}::blame::w1::chat::{MK}::0", f"{IID}::blame::w2::chat::{MK}::1"
    _write_sidecar(path, {a: {"7": 1.0}, b: {"3": 1.0}})
    with open(jev.jitter_path(path), "w", encoding="utf-8") as fh:
        for job_id, k, probs in [(a, 1, {"7": 1.0}), (a, 2, {"7": 0.6, "8": 0.4}), (b, 1, {"4": 1.0})]:
            fh.write(json.dumps(jev.reading_row(job_id, {"probabilities": probs}, read_idx=k)) + "\n")
    _, jitter = tool.compare([path], "t", tmp_path / "tables")
    j = jitter.iloc[0]
    assert (j["n_replies"], j["n_rereads"]) == (2, 3)
    assert j["top_flip_rate"] == pytest.approx(0.5)              # b's top moved 3 -> 4; a's stayed 7
    assert j["mean_abs_ev_change"] == pytest.approx((0 + 0.4 + 1.0) / 3)
    assert j["max_abs_ev_change"] == pytest.approx(1.0)


def test_sign_compare_puts_the_two_readers_side_by_side(tmp_path):
    tool = _tool()
    cols = "level,cell,qkey,term,n_rows,beta_obs,p_wcb\n"
    (tmp_path / "a.csv").write_text(cols + "model,m,blame,sign_c,10,1.0,0.01\nmodel,m,praise,sign_c,10,-0.5,0.2\n")
    (tmp_path / "b.csv").write_text(cols + "model,m,blame,sign_c,12,1.25,0.02\nmodel,m,praise,sign_c,9,-0.5,0.3\n")
    m = tool.sign_compare(tmp_path / "a.csv", tmp_path / "b.csv").set_index("qkey")
    assert m.loc["blame", "beta_jev_minus_regex"] == pytest.approx(0.25)
    assert (m.loc["blame", "n_rows_regex"], m.loc["blame", "n_rows_jev"]) == (10, 12)


def test_a_batch_with_no_successes_stops_the_run(tmp_path, monkeypatch):
    tool = _tool()
    monkeypatch.setattr(tool.time, "sleep", lambda s: None)
    path, items, jobs = _run_dir(tmp_path, [str(i % 11) for i in range(6)])
    t = FakeTransport(fail_first={400: 100})                 # every request refused, as a bad schema would be
    assert tool.read_file(path, items, tool.DecisionsClient("k", transport=t), batch_size=2) == 1
    assert len(t.calls) == 2                                 # the first batch only
