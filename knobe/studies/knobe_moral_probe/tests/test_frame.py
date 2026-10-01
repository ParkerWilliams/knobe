import math

import pytest
from knobe.schemas import ResultRecord, append_jsonl

from conftest import make_items
from kmp import frame


def _write(path, rows):
    with open(path, "w", encoding="utf-8") as fh:
        for pid, mk, value in rows:
            append_jsonl(ResultRecord(
                job_id=f"{pid}::{mk}::0", prompt_id=pid, model_key=mk, sample_idx=0, temperature=1.0, seed=1,
                raw_response="x" if value is None else str(value), parsed_rating=value, parse_ok=value is not None,
                parse_method="regex", logprobs_0_10=None, model_revision="r", runner_version="t", timestamp=0.0), fh)


def test_load_frame_recodes_reversed_and_joins_items(tmp_path):
    items = make_items("nonmoral", 1)
    iid = "kmp-nm-001-moral-bad"
    path = tmp_path / "r.jsonl"
    _write(path, [(f"{iid}::blame::w1::chat", "gemma-2-9b-instruct", 8),
                  (f"{iid}::blame::w3r::chat", "gemma-2-9b-instruct", 2),
                  (f"{iid}::blame::w2::raw", "gemma-2-9b-pretrained", None)])
    d = frame.load_frame(path, items).set_index("wording_key")
    assert d.loc["w1", "rating"] == 8 and d.loc["w3r", "rating"] == 8
    assert math.isnan(d.loc["w2", "rating"])
    assert d.loc["w1", "tuning"] == "instruct" and d.loc["w2", "tuning"] == "pretrained"
    assert d.loc["w1", "family"] == "gemma" and d.loc["w1", "sign_c"] == 0.5
    assert d.loc["w1", "arm"] == "moral" and d.loc["w1", "storyline_id"] == 1


def test_load_frame_rejects_unknown_items(tmp_path):
    path = tmp_path / "r.jsonl"
    _write(path, [("kmp-nm-099-moral-bad::blame::w1::raw", "gemma-2-9b-pretrained", 3)])
    with pytest.raises(ValueError, match="not in the items file"):
        frame.load_frame(path, make_items("nonmoral", 1))
