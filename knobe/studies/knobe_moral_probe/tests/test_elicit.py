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
