import pytest
from knobe.elicit_vllm import EngineResponse
from knobe.jobs import derive_temperature_and_seed

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


def test_seed_and_temperature_come_from_knobe_jobs():
    for j in _jobs()[:5]:
        temperature, seed = derive_temperature_and_seed(protocol.RELEASE, j.prompt_id, j.model_key, j.sample_idx)
        req = elicit.to_request(j, 10)
        assert (req.temperature, req.seed) == (temperature, seed)


def test_seed_temperature_pairs_distinct_across_jobs():
    jobs = _jobs()
    assert {j.fmt for j in jobs} == {"raw", "chat"}
    pairs = {(r.seed, r.temperature) for r in (elicit.to_request(j, 10) for j in jobs)}
    assert len(pairs) == len(jobs)


def test_to_request_rejects_unknown_fmt():
    j = _jobs()[0]
    bad = elicit.Job(j.prompt_id, j.model_key, j.sample_idx, j.text, "completion", j.text_sha256)
    with pytest.raises(ValueError, match="fmt"):
        elicit.to_request(bad, 10)


def test_to_result_rejects_mismatched_job_id():
    j = _jobs()[0]
    req = elicit.to_request(j, 10)
    with pytest.raises(ValueError, match="job_id"):
        elicit.to_result(j, req, EngineResponse("other::id::0", " 7", None), "rev")


def test_to_result_parses_or_records_failure():
    j = _jobs()[0]
    req = elicit.to_request(j, 10)
    ok = elicit.to_result(j, req, EngineResponse(j.job_id, " 7", None), "rev")
    bad = elicit.to_result(j, req, EngineResponse(j.job_id, " _______", None), "rev")
    assert (ok.parsed_rating, ok.parse_ok) == (7, True)
    assert (bad.parsed_rating, bad.parse_ok) == (None, False)
    assert ok.runner_version == protocol.RUNNER_VERSION and ok.logprobs_0_10 is None


def test_text_sha256_propagates_to_every_job():
    specs = prompts.build_subject_prompts(make_items("nonmoral", 1)[:1])
    want = {s.stem: s.text_sha256 for s in specs}
    jobs = elicit.build_jobs(specs, KEYS)
    assert jobs and all(j.text_sha256 == want[j.prompt_id.rsplit("::", 1)[0]] for j in jobs)
    assert all(j.text_sha256 == prompts.sha256_for_text(j.text) for j in jobs)


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


# --- Run manifest (amendment A) and missing responses (amendment B) -------

import json  # noqa: E402

from knobe.elicit_vllm import FakeEngine  # noqa: E402


def _manifest(out):
    return json.loads(elicit.manifest_path(out).read_text(encoding="utf-8"))


def test_fresh_run_writes_manifest(tmp_path):
    items = make_items("nonmoral", 1)[:2]
    code, out = _run(tmp_path, items)
    m = _manifest(out)
    jobs = elicit.build_jobs(prompts.build_subject_prompts(items), KEYS)
    assert code == 0 and elicit.manifest_path(out).parent == tmp_path
    assert (m["release"], m["runner_version"], m["max_tokens"]) == (
        protocol.RELEASE, protocol.RUNNER_VERSION, protocol.MAX_TOKENS)
    assert m["engine"] == "fake" and m["model_keys"] == sorted(KEYS)
    assert m["prompts"] == {j.prompt_id: j.text_sha256 for j in jobs}


def test_clean_resume_skips_done_jobs(tmp_path, monkeypatch):
    items = make_items("nonmoral", 1)[:2]
    _run(tmp_path, items)
    calls = []
    monkeypatch.setattr(elicit, "build_engine", lambda name: calls.append(name) or FakeEngine())
    code, out = _run(tmp_path, items)
    assert code == 0 and calls == []                           # nothing left, engine never built
    n = len(read_jsonl(out, ResultRecord))
    assert n == len({r.job_id for r in read_jsonl(out, ResultRecord)})


def test_resume_adds_new_prompts_to_manifest(tmp_path):
    items = make_items("nonmoral", 1)
    first = [i for i in items if i.arm == items[0].arm]
    _run(tmp_path, first)
    code, out = _run(tmp_path, items)
    jobs = elicit.build_jobs(prompts.build_subject_prompts(items), KEYS)
    assert code == 0 and _manifest(out)["prompts"] == {j.prompt_id: j.text_sha256 for j in jobs}
    assert len(read_jsonl(out, ResultRecord)) == len(jobs)


def test_resume_refuses_changed_scenario(tmp_path, capsys):
    items = make_items("nonmoral", 1)[:2]
    _, out = _run(tmp_path, items)
    n = len(read_jsonl(out, ResultRecord))
    edited = [items[0].model_copy(update={"scenario": items[0].scenario + " Edited."}), items[1]]
    code, _ = _run(tmp_path, edited)
    assert code == 2 and len(read_jsonl(out, ResultRecord)) == n
    err = capsys.readouterr().err
    assert "text_sha256" in err and items[0].item_id in err


def test_resume_refuses_missing_manifest(tmp_path, capsys):
    items = make_items("nonmoral", 1)[:2]
    _, out = _run(tmp_path, items)
    elicit.manifest_path(out).unlink()
    code, _ = _run(tmp_path, items)
    assert code == 2 and "manifest" in capsys.readouterr().err


@pytest.mark.parametrize("attr,value", [("MAX_TOKENS", 99), ("RUNNER_VERSION", "knobe_moral_probe_elicit-9.9")])
def test_resume_refuses_changed_run_field(tmp_path, monkeypatch, capsys, attr, value):
    items = make_items("nonmoral", 1)[:2]
    _, out = _run(tmp_path, items)
    monkeypatch.setattr(protocol, attr, value)
    code, _ = _run(tmp_path, items)
    assert code == 2 and attr.lower() in capsys.readouterr().err


def test_resume_refuses_changed_model_keys(tmp_path, capsys):
    items = make_items("nonmoral", 1)[:2]
    _run(tmp_path, items)
    items_path, out = tmp_path / "items.csv", tmp_path / "out.jsonl"
    code = elicit.main(["--items", str(items_path), "--out", str(out), "--engine", "fake",
                        "--model-keys", KEYS[0]])
    assert code == 2 and "model_keys" in capsys.readouterr().err


class _DroppingEngine(FakeEngine):
    """Returns no response for the first request of every batch."""

    def generate(self, batch):
        return super().generate(batch)[1:]


def test_missing_responses_fail_the_run_and_resume_fills_them(tmp_path, monkeypatch, capsys):
    items = make_items("nonmoral", 1)[:2]
    n_jobs = len(elicit.build_jobs(prompts.build_subject_prompts(items), KEYS))
    monkeypatch.setattr(elicit, "build_engine", lambda name: _DroppingEngine())
    code, out = _run(tmp_path, items, "--batch-size", "1000")
    assert code != 0
    assert len(read_jsonl(out, ResultRecord)) == n_jobs - len(KEYS)   # one dropped per model batch
    assert f"{len(KEYS)} job(s) got no response" in capsys.readouterr().err
    monkeypatch.setattr(elicit, "build_engine", lambda name: FakeEngine())
    code, _ = _run(tmp_path, items)
    rows = read_jsonl(out, ResultRecord)
    assert code == 0 and len(rows) == n_jobs == len({r.job_id for r in rows})
