import importlib.util
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from knobe.schemas import ResultRecord, append_jsonl

from conftest import make_items, make_ngo_verbatim_items
from kmp import frame

REPO = Path(__file__).resolve().parents[3]


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
    assert d.loc["w1", "tuning_status"] == "finetuned" and d.loc["w2", "tuning_status"] == "pretrained"
    assert d.loc["w1", "family"] == "gemma" and d.loc["w1", "sign_c"] == 0.5
    assert d.loc["w1", "arm"] == "moral" and d.loc["w1", "storyline_id"] == 1


def test_reversed_recode_uses_protocol_and_keeps_missing(tmp_path):
    iid = "kmp-nm-001-moral-bad"
    path = tmp_path / "r.jsonl"
    _write(path, [(f"{iid}::blame::w1::chat", "gemma-2-9b-instruct", 2),
                  (f"{iid}::blame::w3r::chat", "gemma-2-9b-instruct", 2),
                  (f"{iid}::blame::w3r::raw", "gemma-2-9b-pretrained", None)])
    d = frame.load_frame(path, make_items("nonmoral", 1))
    r = d.set_index(["wording_key", "fmt"])["rating"]
    assert r[("w1", "chat")] == 2 and r[("w3r", "chat")] == 8
    assert math.isnan(r[("w3r", "raw")])


def test_load_frame_drops_rows_for_unknown_items_and_reports(tmp_path, capsys):
    path = tmp_path / "r.jsonl"
    _write(path, [("kmp-nm-099-moral-bad::blame::w1::raw", "gemma-2-9b-pretrained", 3),
                  ("kmp-nm-001-moral-bad::blame::w1::raw", "gemma-2-9b-pretrained", 4)])
    d = frame.load_frame(path, make_items("nonmoral", 1))
    assert list(d["item_id"]) == ["kmp-nm-001-moral-bad"]
    assert d.attrs["n_dropped_unknown_items"] == 1
    assert d.attrs["dropped_unknown_item_ids"] == ["kmp-nm-099-moral-bad"]
    assert "dropped 1" in capsys.readouterr().err


def test_tuning_status_and_tuning_c_use_the_existing_coding(tmp_path):
    iid = "kmp-nm-001-moral-bad"
    path = tmp_path / "r.jsonl"
    _write(path, [(f"{iid}::blame::w1::chat", "llama-3.1-8b-instruct", 8),
                  (f"{iid}::blame::w1::raw", "llama-3.1-8b-pretrained", 3)])
    d = frame.load_frame(path, make_items("nonmoral", 1)).set_index("fmt")
    assert "tuning" not in d.columns
    assert d.loc["chat", "tuning_status"] == "finetuned" and d.loc["chat", "tuning_c"] == 0.5
    assert d.loc["raw", "tuning_status"] == "pretrained" and d.loc["raw", "tuning_c"] == -0.5
    assert set(d["model_family"]) == {"llama-3.1-8b"} and set(d["family"]) == {"llama"}
    assert frame.TUNING_C == {"finetuned": 0.5, "pretrained": -0.5}


def test_optional_registry_argument(tmp_path):
    iid = "kmp-nm-001-moral-bad"
    path = tmp_path / "r.jsonl"
    _write(path, [(f"{iid}::blame::w1::chat", "toy-1b-instruct", 8)])
    d = frame.load_frame(path, make_items("nonmoral", 1), registry={"toy-1b": None})
    assert (d["model_family"].iloc[0], d["family"].iloc[0], d["tuning_status"].iloc[0]) == \
        ("toy-1b", "toy", "finetuned")


def test_unknown_model_key_raises(tmp_path):
    path = tmp_path / "r.jsonl"
    _write(path, [("kmp-nm-001-moral-bad::blame::w1::raw", "notamodel-pretrained", 3)])
    with pytest.raises(ValueError, match="notamodel-pretrained"):
        frame.load_frame(path, make_items("nonmoral", 1))


def test_ambiguous_short_family_raises(tmp_path):
    iid = "kmp-nm-001-moral-bad"
    path = tmp_path / "r.jsonl"
    _write(path, [(f"{iid}::blame::w1::raw", "gemma-2-9b-pretrained", 3),
                  (f"{iid}::blame::w1::chat", "gemma-2-2b-instruct", 3)])
    with pytest.raises(ValueError, match="gemma"):
        frame.load_frame(path, make_items("nonmoral", 1))


def test_cluster_id_is_experiment_qualified(tmp_path):
    items = make_items("nonmoral", 1) + make_ngo_verbatim_items(1)
    path = tmp_path / "r.jsonl"
    _write(path, [("kmp-nm-001-moral-bad::blame::w1::raw", "gemma-2-9b-pretrained", 3),
                  ("kmp-nv-001-moral-bad::blame::w1::raw", "gemma-2-9b-pretrained", 4)])
    d = frame.load_frame(path, items).set_index("item_id")
    assert d.loc["kmp-nm-001-moral-bad", "cluster_id"] == "nonmoral-001"
    assert d.loc["kmp-nv-001-moral-bad", "cluster_id"] == "ngo_verbatim-001"
    assert d["storyline_id"].nunique() == 1 and d["cluster_id"].nunique() == 2


def test_raw_value_is_renamed_and_parse_columns_kept(tmp_path):
    iid = "kmp-nm-001-moral-bad"
    path = tmp_path / "r.jsonl"
    _write(path, [(f"{iid}::blame::w3r::raw", "gemma-2-9b-pretrained", 2)])
    d = frame.load_frame(path, make_items("nonmoral", 1))
    assert "parsed_rating" not in d.columns
    assert d["parsed_rating_raw"].iloc[0] == 2 and d["rating"].iloc[0] == 8
    assert {"parse_ok", "raw_response"} <= set(d.columns)


def test_parse_ok_with_missing_value_gives_nan(tmp_path):
    path = tmp_path / "r.jsonl"
    pid = "kmp-nm-001-moral-bad::blame::w1::raw"
    with open(path, "w", encoding="utf-8") as fh:
        append_jsonl(ResultRecord(
            job_id=f"{pid}::gemma-2-9b-pretrained::0", prompt_id=pid, model_key="gemma-2-9b-pretrained",
            sample_idx=0, temperature=1.0, seed=1, raw_response="?", parsed_rating=None, parse_ok=True,
            parse_method="regex", logprobs_0_10=None, model_revision="r", runner_version="t", timestamp=0.0), fh)
    d = frame.load_frame(path, make_items("nonmoral", 1))
    assert math.isnan(d["rating"].iloc[0])
    assert frame.analysis_rows(d).empty


def test_empty_results_file_raises(tmp_path):
    path = tmp_path / "r.jsonl"
    path.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match=str(path)):
        frame.load_frame(path, make_items("nonmoral", 1))


def test_duplicate_job_id_raises(tmp_path):
    path = tmp_path / "r.jsonl"
    row = ("kmp-nm-001-moral-bad::blame::w1::raw", "gemma-2-9b-pretrained", 3)
    _write(path, [row, row])
    with pytest.raises(ValueError, match="duplicate job_id.*kmp-nm-001-moral-bad::blame::w1::raw"):
        frame.load_frame(path, make_items("nonmoral", 1))


def test_analysis_rows_drops_only_missing_ratings(tmp_path):
    iid = "kmp-nm-001-moral-bad"
    path = tmp_path / "r.jsonl"
    _write(path, [(f"{iid}::blame::w1::chat", "gemma-2-9b-instruct", 8),
                  (f"{iid}::blame::w2::chat", "gemma-2-9b-instruct", None)])
    d = frame.load_frame(path, make_items("nonmoral", 1))
    rows = frame.analysis_rows(d)
    assert list(rows["wording_key"]) == ["w1"] and rows["rating"].notna().all()
    assert len(d) == 2                                  # the input frame is untouched


def _load_wcb():
    """lib.wild_cluster_bootstrap, loaded from its file under a unique module
    name (the pilot scripts put its folder on sys.path and `from lib import`;
    a bare `lib` module name would be too easy to shadow in a test session)."""
    spec = importlib.util.spec_from_file_location(
        "rq1_v1_1_robustness_lib", REPO / "analysis/rq1_v1_1_robustness/lib.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.wild_cluster_bootstrap


def test_wild_cluster_bootstrap_runs_on_analysis_rows(tmp_path):
    wcb = _load_wcb()
    items = make_items("nonmoral", 6)
    rng = np.random.default_rng(0)
    rows = []
    for item in items:
        for mk in ("gemma-2-9b-pretrained", "gemma-2-9b-instruct"):
            fmt = "chat" if mk.endswith("instruct") else "raw"
            value = int(np.clip(round((7 if item.sign == "bad" else 3) + rng.normal()), 0, 10))
            rows.append((f"{item.item_id}::intentionality::w1::{fmt}", mk, value))
    rows[0] = (rows[0][0], rows[0][1], None)            # one parse failure
    path = tmp_path / "r.jsonl"
    _write(path, rows)
    d = frame.load_frame(path, items)
    assert d["rating"].isna().sum() == 1
    out = wcb(frame.analysis_rows(d), "rating ~ sign_c * tuning_c", "sign_c", "cluster_id", B=49, seed=1)
    assert out["n_groups"] == 6 and out["beta_obs"] > 0 and 0 <= out["p_wcb"] <= 1


def test_ngo_pair_id_links_verbatim_and_adapted_moral_only(tmp_path):
    items = make_items("nonmoral", 1) + make_ngo_verbatim_items(1)
    path = tmp_path / "r.jsonl"
    _write(path, [("kmp-nm-001-moral-bad::blame::w1::raw", "gemma-2-9b-pretrained", 3),
                  ("kmp-nm-001-prudential-bad::blame::w1::raw", "gemma-2-9b-pretrained", 3),
                  ("kmp-nv-001-moral-good::blame::w1::raw", "gemma-2-9b-pretrained", 4)])
    d = frame.load_frame(path, items).set_index("item_id")
    assert d.loc["kmp-nm-001-moral-bad", "ngo_pair_id"] == "ngo-001"
    assert d.loc["kmp-nv-001-moral-good", "ngo_pair_id"] == "ngo-001"
    assert pd.isna(d.loc["kmp-nm-001-prudential-bad", "ngo_pair_id"])


def test_ngo_pair_id_absent_for_foundations(tmp_path):
    path = tmp_path / "r.jsonl"
    _write(path, [("kmp-mf-001-harm-bad::blame::w1::raw", "gemma-2-9b-pretrained", 3)])
    d = frame.load_frame(path, make_items("foundations", 1))
    assert d["ngo_pair_id"].isna().all()


def test_all_rows_dropped_raises(tmp_path):
    path = tmp_path / "r.jsonl"
    _write(path, [("kmp-nm-099-moral-bad::blame::w1::raw", "gemma-2-9b-pretrained", 3)])
    with pytest.raises(ValueError, match="kmp-nm-099-moral-bad"):
        frame.load_frame(path, make_items("nonmoral", 1))


def test_scaffold_is_carried_into_the_frame(tmp_path):
    from conftest import make_purpose_storyline
    items = make_items("foundations", 1) + make_purpose_storyline(9)
    path = tmp_path / "r.jsonl"
    _write(path, [("kmp-mf-001-harm-bad::blame::w1::raw", "gemma-2-9b-pretrained", 3),
                  ("kmp-mf-009-purity-bad::blame::w1::raw", "gemma-2-9b-pretrained", 3)])
    d = frame.load_frame(path, items).set_index("item_id")
    assert d.loc["kmp-mf-001-harm-bad", "scaffold"] == "shared"
    assert d.loc["kmp-mf-009-purity-bad", "scaffold"] == "purpose"


def test_scaffold_is_missing_outside_foundations(tmp_path):
    path = tmp_path / "r.jsonl"
    _write(path, [("kmp-nm-001-moral-bad::blame::w1::raw", "gemma-2-9b-pretrained", 3)])
    assert frame.load_frame(path, make_items("nonmoral", 1))["scaffold"].isna().all()
