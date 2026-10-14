"""Per-format answer budget and the kmp.answer readout, wired through elicit
and frame (DESIGN.md amendment 2026-10-13, "answer format")."""
import json
import time

from conftest import make_items
from knobe.schemas import ResultRecord, append_jsonl
from kmp import elicit, frame, prompts, protocol
from kmp.items import write_items

INSTRUCT, PRETRAINED = "mistral-7b-v0.1-instruct", "mistral-7b-v0.1-pretrained"


def _jobs():
    items = make_items("nonmoral", 1)[:2]
    return items, elicit.build_jobs(prompts.build_subject_prompts(items), [INSTRUCT, PRETRAINED])


def test_each_format_gets_its_own_budget():
    _, jobs = _jobs()
    budgets = elicit.max_tokens_by_format()
    for j in jobs:
        assert elicit.to_request(j, budgets).max_tokens == protocol.MAX_TOKENS[j.fmt]
    assert {j.fmt for j in jobs} == {"chat", "raw"} and protocol.MAX_TOKENS["chat"] > protocol.MAX_TOKENS["raw"]


def test_override_applies_to_every_format():
    _, jobs = _jobs()
    budgets = elicit.max_tokens_by_format(32)
    assert budgets == {"raw": 32, "chat": 32}
    assert {elicit.to_request(j, budgets).max_tokens for j in jobs} == {32}


def test_manifest_records_the_per_format_budget(tmp_path):
    items, _ = _jobs()
    write_items(items, tmp_path / "items.csv")
    out = tmp_path / "out.jsonl"
    assert elicit.main(["--items", str(tmp_path / "items.csv"), "--out", str(out), "--engine", "fake",
                        "--model-keys", f"{INSTRUCT},{PRETRAINED}"]) == 0
    m = json.loads(elicit.manifest_path(out).read_text())
    assert m["max_tokens"] == dict(protocol.MAX_TOKENS)


def _write_rows(path, items, replies):
    job = elicit.build_jobs(prompts.build_subject_prompts(items[:1]), [INSTRUCT])[0]
    with open(path, "w") as fh:
        for i, (reply, parsed, ok) in enumerate(replies):
            append_jsonl(ResultRecord(
                job_id=f"{job.prompt_id}::{INSTRUCT}::{i}", prompt_id=job.prompt_id, model_key=INSTRUCT,
                sample_idx=i, temperature=1.0, seed=i, raw_response=reply, parsed_rating=parsed, parse_ok=ok,
                parse_method="regex", logprobs_0_10=None, model_revision="fake",
                runner_version="knobe_moral_probe_elicit-0.1", timestamp=time.time()), fh)


def test_reparse_rescores_old_first_integer_rows(tmp_path):
    items, _ = _jobs()
    path = tmp_path / "old.jsonl"
    # as the 0.1 runner stored them: the refusal and the scale restatement were scored 0
    _write_rows(path, items, [("I cannot provide a number from 0 to ", 0, True),
                              ("On a scale of 0 to 10", 0, True),
                              ("8.5\n\nExplanation:", 8, True),
                              ("7", 7, True)])
    old = frame.load_frame(path, items)
    new = frame.load_frame(path, items, reparse=True)
    assert old["parse_ok"].tolist() == [True, True, True, True]
    assert new["parse_ok"].tolist() == [False, False, True, True]
    assert new["parsed_rating_raw"].tolist()[2:] == [8.5, 7]
