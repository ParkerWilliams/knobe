import hashlib
import json

import numpy as np
import pandas as pd
import pytest
from knobe.schemas import ResultRecord, append_jsonl

from conftest import make_items, make_ngo_verbatim_items
from kmp import checks, elicit, protocol
from kmp.items import write_items

COLS = ["model_key", "tuning_status", "family", "experiment", "item_id", "qkey", "wording_key", "reversed",
        "arm", "sign", "parse_ok", "parsed_rating_raw", "rating"]


def _frame(rows):
    return pd.DataFrame(rows, columns=COLS).assign(timestamp=0.0)


def _row(model_key, item_id, qkey, wording_key, reversed_, arm, sign, raw, experiment="nonmoral"):
    tuning = "pretrained" if model_key.endswith("pretrained") else "finetuned"
    ok = raw is not None
    rating = np.nan if not ok else float(10 - raw if reversed_ else raw)
    return (model_key, tuning, model_key.split("-")[0], experiment, item_id, qkey, wording_key, reversed_,
            arm, sign, ok, raw, rating)


def test_number_rates_flag_low_cells():
    rows = [_row("gemma-2-9b-pretrained", "i1", "blame", "w1", False, "moral", "bad", 5 if ok else None)
            for ok in [True] * 8 + [False] * 2]
    out = checks.number_rates(_frame(rows))
    assert out.loc[0, "number_rate"] == 0.8 and not out.loc[0, "passes"]
    assert out.loc[0, "tuning_status"] == "pretrained" and out.loc[0, "family"] == "gemma"


def test_anchor_agreement_perfect():
    rows = []
    for k, v in enumerate([2, 5, 8]):
        for w, rev in (("w1", False), ("w3r", True)):
            rows.append(_row("gemma-2-9b-instruct", f"i{k}", "blame", w, rev, "moral", "bad", 10 - v if rev else v))
    rows.append(_row("gemma-2-9b-instruct", "i0", "blame", "w1", False, "moral", "bad", None))
    out = checks.anchor_agreement(_frame(rows))
    assert out.loc[0, "r"] == pytest.approx(1.0)
    assert out.loc[0, "mean_diff"] == 0.0 and out.loc[0, "n_items"] == 3
    assert out.loc[0, "tuning_status"] == "finetuned"


def test_validity_checks_directions():
    m = "gemma-2-9b-pretrained"
    rows = []
    for sign, blame, praise in (("bad", 8, 1), ("good", 2, 7)):
        rows.append(_row(m, f"i{sign}", "blame", "w1", False, "moral", sign, blame))
        rows.append(_row(m, f"i{sign}", "praise", "w1", False, "moral", sign, praise))
    rows.append(_row(m, "i1", "significance", "w1", False, "moral", "bad", 9))
    rows.append(_row(m, "i2", "significance", "w1", False, "procedural", "bad", 2))
    out = checks.validity(_frame(rows)).set_index("check")
    assert out.loc["blame_bad_minus_good", "value"] == 6 and out.loc["blame_bad_minus_good", "status"] == "pass"
    assert out.loc["praise_good_minus_bad", "status"] == "pass"
    assert out.loc["significance_moral_minus_procedural", "value"] == 7
    assert out.loc["significance_moral_minus_procedural", "status"] == "pass"
    assert set(out["experiment"]) == {"nonmoral"}
    assert out.loc["blame_bad_minus_good", "tuning_status"] == "pretrained"


def test_example_copying_share():
    rows = [_row("gemma-2-9b-pretrained", "i1", "blame", "w1", False, "moral", "bad", v) for v in (0, 5, 9, 3)]
    out = checks.example_copying(_frame(rows))
    assert out.loc[0, "share_example_values"] == 0.75 and out.loc[0, "flag"]


def test_example_copying_counts_the_written_number_not_the_recoded_one():
    # Written 9 under a reversed wording is recoded to 1 but is still a copied example answer.
    rows = [_row("gemma-2-9b-pretrained", "i1", "blame", "w3r", True, "moral", "bad", v) for v in (9, 9, 3, 4)]
    rows.append(_row("gemma-2-9b-pretrained", "i1", "blame", "w1", False, "moral", "bad", None))
    out = checks.example_copying(_frame(rows))
    assert out.loc[0, "share_example_values"] == 0.5


# --- per-experiment applicability (amendment B) ---------------------------

def test_applicable_checks_per_experiment():
    assert checks.applicable_checks("nonmoral") == checks.VALIDITY_CHECKS
    for experiment in ("foundations", "ngo_verbatim"):
        assert checks.applicable_checks(experiment) == ("blame_bad_minus_good", "praise_good_minus_bad")
    with pytest.raises(ValueError, match="unknown experiment"):
        checks.applicable_checks("nonmorale")


def _blame_praise_rows(model_key, experiment, arm, bad=(8, 1), good=(2, 7)):
    rows = []
    for sign, (blame, praise) in (("bad", bad), ("good", good)):
        rows.append(_row(model_key, f"i{sign}", "blame", "w1", False, arm, sign, blame, experiment))
        rows.append(_row(model_key, f"i{sign}", "praise", "w1", False, arm, sign, praise, experiment))
    return rows


@pytest.mark.parametrize("experiment, arm", [("foundations", "loyalty"), ("ngo_verbatim", "moral")])
def test_significance_check_not_applicable_outside_nonmoral(experiment, arm):
    m = "llama-3.1-8b-instruct"
    rows = _blame_praise_rows(m, experiment, arm)
    rows.append(_row(m, "ibad", "significance", "w1", False, arm, "bad", 9, experiment))
    out = checks.validity(_frame(rows)).set_index("check")
    sig = out.loc["significance_moral_minus_procedural"]
    assert sig["status"] == "not_applicable" and np.isnan(sig["value"])
    assert out.loc["blame_bad_minus_good", "status"] == "pass"
    assert checks.validity_problems(checks.validity(_frame(rows))).empty


def test_nonmoral_fail_and_no_data_are_distinct_from_not_applicable():
    m = "gemma-2-9b-pretrained"
    rows = _blame_praise_rows(m, "nonmoral", "moral", bad=(2, 7), good=(8, 1))   # wrong direction
    rows.append(_row(m, "ibad", "significance", "w1", False, "moral", "bad", 9))  # no procedural arm
    table = checks.validity(_frame(rows))
    out = table.set_index("check")
    assert out.loc["blame_bad_minus_good", "status"] == "fail"
    assert out.loc["praise_good_minus_bad", "status"] == "fail"
    assert out.loc["significance_moral_minus_procedural", "status"] == "no_data"
    problems = checks.validity_problems(table)
    assert sorted(problems["status"]) == ["fail", "fail", "no_data"]


def test_validity_is_per_model_and_experiment():
    m = "mistral-7b-v0.1-pretrained"
    rows = _blame_praise_rows(m, "nonmoral", "moral") + _blame_praise_rows(m, "ngo_verbatim", "moral", bad=(1, 1),
                                                                         good=(5, 5))
    out = checks.validity(_frame(rows)).set_index(["experiment", "check"])["status"]
    assert out[("nonmoral", "blame_bad_minus_good")] == "pass"
    assert out[("ngo_verbatim", "blame_bad_minus_good")] == "fail"
    assert out[("ngo_verbatim", "significance_moral_minus_procedural")] == "not_applicable"
    assert out[("nonmoral", "significance_moral_minus_procedural")] == "no_data"


def test_validity_raises_on_unknown_experiment():
    rows = _blame_praise_rows("gemma-2-9b-pretrained", "mystery", "moral")
    with pytest.raises(ValueError, match="unknown experiment"):
        checks.validity(_frame(rows))


# --- per-experiment grouping, no_data for unrated pairs --------------------

def test_number_rates_are_per_experiment_and_block_a_poorly_parsed_one():
    m = "gemma-2-9b-instruct"
    rows = [_row(m, f"n{k}", "blame", "w1", False, "moral", "bad", 5) for k in range(9)]
    rows.append(_row(m, "v1", "blame", "w1", False, "moral", "bad", None, "ngo_verbatim"))
    # pooled the cell would be 9/10 = 0.90 and pass; per experiment ngo_verbatim is 0/1
    nr = checks.number_rates(_frame(rows)).set_index("experiment")
    assert nr.loc["nonmoral", "passes"] and not nr.loc["ngo_verbatim", "passes"]
    gate = checks.gate_summary(checks.run_checks(_frame(rows), [], []))
    assert any(b.startswith("number_rate:") and "ngo_verbatim" in b for b in gate["blocking"])


def test_validity_gives_no_data_for_a_model_experiment_without_ratings_and_it_blocks_finetuned():
    m = "llama-3.1-8b-instruct"
    rows = _blame_praise_rows(m, "nonmoral", "moral")
    rows += [_row(m, "f1", q, "w1", False, "loyalty", "bad", None, "foundations") for q in ("blame", "praise")]
    table = checks.validity(_frame(rows))
    fnd = table[table["experiment"] == "foundations"].set_index("check")["status"]
    assert fnd["blame_bad_minus_good"] == "no_data" and fnd["praise_good_minus_bad"] == "no_data"
    assert fnd["significance_moral_minus_procedural"] == "not_applicable"
    gate = checks.gate_summary(checks.run_checks(_frame(rows), [], []))
    blocked = [b for b in gate["blocking"] if b.startswith("validity:") and "foundations" in b]
    assert len(blocked) == 2 and not any("nan" in b for b in blocked)


def test_example_copying_and_anchor_agreement_are_per_experiment_and_question():
    m = "gemma-2-9b-pretrained"
    rows = [_row(m, "i1", "blame", "w1", False, "moral", "bad", v) for v in (0, 5, 9, 3)]
    rows += [_row(m, "i1", "praise", "w1", False, "moral", "bad", v) for v in (1, 2, 3, 4)]
    rows += [_row(m, "v1", "blame", "w1", False, "moral", "bad", v, "ngo_verbatim") for v in (1, 2)]
    out = checks.example_copying(_frame(rows)).set_index(["experiment", "qkey"])
    assert out.loc[("nonmoral", "blame"), "flag"] and not out.loc[("nonmoral", "praise"), "flag"]
    assert out.loc[("ngo_verbatim", "blame"), "share_example_values"] == 0.0
    assert {"experiment", "qkey"} <= set(checks.anchor_agreement(_frame(rows)).columns)


# --- main: coverage, gates, provenance ---------------------------------------

def _write_results(path, rows):
    with open(path, "w", encoding="utf-8") as fh:
        for pid, mk, value in rows:
            append_jsonl(ResultRecord(
                job_id=f"{pid}::{mk}::0", prompt_id=pid, model_key=mk, sample_idx=0, temperature=1.0, seed=1,
                raw_response="x" if value is None else str(value), parsed_rating=value, parse_ok=value is not None,
                parse_method="regex", logprobs_0_10=None, model_revision="r", runner_version="t", timestamp=0.0), fh)


def _full_rows(items, mk, blame=(8, 2), praise=(1, 7), other=3):
    """One row per item x subject qkey x wording. blame/praise = (bad, good) ratings on
    the normal scale; reversed wordings get the written value 10 - x."""
    fmt = "raw" if mk.endswith("pretrained") else "chat"
    rows = []
    for item in items:
        for qkey in protocol.subject_qkeys(item):
            for w in protocol.QUESTIONS[qkey]:
                pair = {"blame": blame, "praise": praise}.get(qkey)
                v = other if pair is None else pair[0 if item.sign == "bad" else 1]
                rows.append((f"{item.item_id}::{qkey}::{w.key}::{fmt}", mk, 10 - v if w.reversed else v))
    return rows


def _manifest(model_keys):
    return {"release": "knobe_moral_probe", "runner_version": "v", "max_tokens": 10, "engine": "fake",
            "model_keys": sorted(model_keys), "examples": True, "prompts": {"p": "sha"}}


def _run_main(tmp_path, items, rows, manifest=None):
    results, items_csv, out_dir = tmp_path / "r.jsonl", tmp_path / "items.csv", tmp_path / "checks"
    _write_results(results, rows)
    write_items(items, items_csv)
    if manifest is not None:
        elicit.manifest_path(results).write_text(json.dumps(manifest), encoding="utf-8")
    code = checks.main(["--results", str(results), "--items", str(items_csv), "--out-dir", str(out_dir)])
    return code, out_dir


def _gate(out_dir):
    return json.loads((out_dir / "provenance.json").read_text())["gate"]


def test_main_records_dropped_items_manifest_and_provenance(tmp_path, capsys):
    mk = "gemma-2-9b-instruct"
    items = make_ngo_verbatim_items(1)
    rows = _full_rows(items, mk) + [("kmp-nv-099-moral-bad::blame::w1::chat", mk, 5)]
    manifest = _manifest([mk])
    code, out_dir = _run_main(tmp_path, items, rows, manifest)
    assert code == 0
    prov = json.loads((out_dir / "provenance.json").read_text())
    assert prov["n_dropped_unknown_items"] == 1
    assert prov["dropped_unknown_item_ids"] == ["kmp-nv-099-moral-bad"]
    assert prov["experiments"] == ["ngo_verbatim"]
    assert prov["manifest"] == {k: manifest[k] for k in elicit.RUN_FIELDS}
    assert prov["results_sha256"] == hashlib.sha256((tmp_path / "r.jsonl").read_bytes()).hexdigest()
    assert prov["items_sha256"] == hashlib.sha256((tmp_path / "items.csv").read_bytes()).hexdigest()
    assert prov["number_rate_min"] == protocol.NUMBER_RATE_MIN and prov["copy_share_max"] == protocol.COPY_SHARE_MAX
    assert prov["argv"][0] == "--results" and prov["timestamp_utc"].endswith("+00:00")
    assert "git_commit" in prov and "git_dirty" in prov
    assert prov["gate"] == {"blocking": [], "findings": []}
    validity = pd.read_csv(out_dir / "validity.csv").set_index("check")
    assert validity.loc["significance_moral_minus_procedural", "status"] == "not_applicable"
    out = capsys.readouterr()
    assert "no manifest" not in out.err and "kmp-nv-099-moral-bad" in out.out


def test_main_warns_when_manifest_absent_and_fails_low_number_rate(tmp_path, capsys):
    mk = "gemma-2-9b-pretrained"
    rows = [("kmp-nm-001-moral-bad::blame::w1::raw", mk, 8), ("kmp-nm-001-moral-good::blame::w1::raw", mk, None)]
    code, out_dir = _run_main(tmp_path, make_items("nonmoral", 1), rows)
    assert code == 1
    prov = json.loads((out_dir / "provenance.json").read_text())
    assert prov["manifest"] is None and prov["n_dropped_unknown_items"] == 0
    err = capsys.readouterr().err
    assert "no manifest" in err and "number-rate minimum" in err


@pytest.mark.parametrize("mk, kwargs, code, blocked", [
    ("gemma-2-9b-instruct", dict(blame=(2, 8)), 1, "validity"),         # finetuned validity fail blocks
    ("gemma-2-9b-pretrained", dict(blame=(2, 8)), 0, None),              # pretrained: a finding
    ("gemma-2-9b-instruct", dict(blame=(9, 0), praise=(0, 9)), 1, "example_copying"),
    ("gemma-2-9b-pretrained", dict(blame=(9, 0), praise=(0, 9)), 0, None),
])
def test_main_blocks_on_finetuned_problems_only(tmp_path, capsys, mk, kwargs, code, blocked):
    items = make_ngo_verbatim_items(1)
    got, out_dir = _run_main(tmp_path, items, _full_rows(items, mk, **kwargs), _manifest([mk]))
    assert got == code
    gate = _gate(out_dir)
    assert "gate summary" in capsys.readouterr().err
    if blocked:
        assert gate["blocking"] and all(b.startswith(blocked) for b in gate["blocking"])
    else:
        assert gate["blocking"] == [] and gate["findings"]
        assert all(f.startswith(("validity", "example_copying")) for f in gate["findings"])


def test_main_blocks_on_finetuned_no_data(tmp_path):
    items = make_ngo_verbatim_items(1)
    rows = [(pid, mk, None if "::praise::" in pid else v) for pid, mk, v in _full_rows(items, "gemma-2-9b-instruct")]
    code, out_dir = _run_main(tmp_path, items, rows, _manifest(["gemma-2-9b-instruct"]))
    assert code == 1
    assert any(b.startswith("validity:") and "no_data" in b for b in _gate(out_dir)["blocking"])


def test_main_blocks_on_manifest_model_with_no_rows(tmp_path):
    items = make_ngo_verbatim_items(1)
    rows = _full_rows(items, "gemma-2-9b-instruct")
    code, out_dir = _run_main(tmp_path, items, rows, _manifest(["gemma-2-9b-instruct", "gemma-2-9b-pretrained"]))
    assert code == 1
    assert _gate(out_dir)["blocking"] == ["coverage: gemma-2-9b-pretrained has no rows"]


def test_main_blocks_on_missing_expected_cell(tmp_path):
    items = make_ngo_verbatim_items(1)
    rows = [r for r in _full_rows(items, "gemma-2-9b-instruct") if "::intentionality::w2::" not in r[0]]
    code, out_dir = _run_main(tmp_path, items, rows, _manifest(["gemma-2-9b-instruct"]))
    assert code == 1
    assert _gate(out_dir)["blocking"] == ["coverage: gemma-2-9b-instruct ngo_verbatim intentionality w2 has no rows"]


def test_main_without_manifest_covers_the_models_present(tmp_path):
    items = make_ngo_verbatim_items(1)
    code, out_dir = _run_main(tmp_path, items, _full_rows(items, "gemma-2-9b-instruct"))
    assert code == 0 and _gate(out_dir)["blocking"] == []


# --- foundations coverage, unexpected models, provenance details -------------

def test_foundations_expected_cells_follow_the_arms_present():
    items = [i for i in make_items("foundations", 1) if i.arm != "loyalty"]
    cells = checks.expected_cells(items)
    assert not any(q == "fnd_loyalty" for _, q, _ in cells)
    assert ("foundations", "fnd_purity", "w1") in cells and ("foundations", "fnd_harm", "w1") in cells


def test_main_blocks_on_missing_foundations_cell(tmp_path):
    mk = "llama-3.1-8b-instruct"
    items = [i for i in make_items("foundations", 1) if i.arm != "loyalty"]
    rows = [r for r in _full_rows(items, mk) if "::fnd_purity::" not in r[0]]
    code, out_dir = _run_main(tmp_path, items, rows, _manifest([mk]))
    assert code == 1
    assert _gate(out_dir)["blocking"] == [f"coverage: {mk} foundations fnd_purity w1 has no rows"]


def test_main_blocks_on_model_not_in_manifest(tmp_path):
    items = make_ngo_verbatim_items(1)
    rows = _full_rows(items, "gemma-2-9b-instruct") + _full_rows(items, "gemma-2-9b-pretrained")
    code, out_dir = _run_main(tmp_path, items, rows, _manifest(["gemma-2-9b-instruct"]))
    assert code == 1
    assert _gate(out_dir)["blocking"] == ["coverage: unexpected model gemma-2-9b-pretrained "
                                          "(in the results but not in the manifest's model_keys)"]


def test_provenance_details(tmp_path, monkeypatch):
    mk = "gemma-2-9b-instruct"
    items = make_ngo_verbatim_items(1)
    monkeypatch.chdir(tmp_path)
    code, out_dir = _run_main(tmp_path, items, _full_rows(items, mk), _manifest([mk]))
    assert code == 0
    prov = json.loads((out_dir / "provenance.json").read_text())
    assert prov["example_answers"] == [0, 5, 9]
    assert prov["manifest_sha256"] == hashlib.sha256(
        elicit.manifest_path(tmp_path / "r.jsonl").read_bytes()).hexdigest()
    assert prov["cwd"] == str(tmp_path.resolve())
    assert prov["results"] == str((tmp_path / "r.jsonl").resolve())
    assert prov["items"] == str((tmp_path / "items.csv").resolve())


def test_provenance_without_manifest_has_no_manifest_hash(tmp_path):
    items = make_ngo_verbatim_items(1)
    _, out_dir = _run_main(tmp_path, items, _full_rows(items, "gemma-2-9b-instruct"))
    assert json.loads((out_dir / "provenance.json").read_text())["manifest_sha256"] is None


def test_git_failure_leaves_git_fields_none_and_run_completes(tmp_path, monkeypatch):
    def boom(*args, **kwargs):
        raise FileNotFoundError("git")
    monkeypatch.setattr(checks.subprocess, "run", boom)
    items = make_ngo_verbatim_items(1)
    code, out_dir = _run_main(tmp_path, items, _full_rows(items, "gemma-2-9b-instruct"))
    assert code == 0
    prov = json.loads((out_dir / "provenance.json").read_text())
    assert prov["git_commit"] is None and prov["git_dirty"] is None


# --- gate 3 (example effect) and gate 5 (throughput) -------------------------

from kmp import frame  # noqa: E402


def test_example_effect_is_zero_for_identical_runs():
    rows = [_row("mistral-7b-v0.1-instruct", f"i{k}", "blame", "w1", False, "moral", "bad", v)
            for k, v in enumerate([1, 4, 8])]
    out = checks.example_effect(_frame(rows), _frame(rows))
    assert out.loc[0, "mean_diff"] == 0.0 and out.loc[0, "r"] == pytest.approx(1.0)
    assert out.loc[0, "n_items"] == 3 and out.loc[0, "experiment"] == "nonmoral"
    assert out.loc[0, "tuning_status"] == "finetuned"


def test_example_effect_is_per_experiment_and_uses_recoded_ratings():
    m = "mistral-7b-v0.1-instruct"
    with_ = [_row(m, f"i{k}", "blame", "w3r", True, "moral", "bad", 10 - v) for k, v in enumerate([2, 5, 8])]
    with_ += [_row(m, f"v{k}", "blame", "w1", False, "moral", "bad", v, "ngo_verbatim") for k, v in enumerate([1, 2, 3])]
    without = [_row(m, f"i{k}", "blame", "w1", False, "moral", "bad", v - 1) for k, v in enumerate([2, 5, 8])]
    out = checks.example_effect(_frame(with_), _frame(without)).set_index("experiment")
    assert list(out.index) == ["nonmoral"]          # ngo_verbatim has no baseline items
    assert out.loc["nonmoral", "mean_diff"] == 1.0 and out.loc["nonmoral", "r"] == pytest.approx(1.0)


def test_no_examples_run_and_throughput(tmp_path):
    items = make_items("nonmoral", 1)[:2]
    items_path = tmp_path / "items.csv"
    write_items(items, items_path)
    common = ["--items", str(items_path), "--engine", "fake", "--model-keys", "mistral-7b-v0.1-instruct"]
    assert elicit.main([*common, "--out", str(tmp_path / "with.jsonl")]) == 0
    assert elicit.main([*common, "--out", str(tmp_path / "without.jsonl"), "--no-examples"]) == 0
    with_f = frame.load_frame(tmp_path / "with.jsonl", items)
    without = frame.load_frame(tmp_path / "without.jsonl", items)
    assert len(with_f) == len(without)
    assert set(checks.example_effect(with_f, without)["qkey"]) >= {"blame", "praise", "intentionality"}
    tp = checks.throughput(with_f)
    assert list(tp["model_key"]) == ["mistral-7b-v0.1-instruct"] and tp.loc[0, "rows"] == len(with_f)
    assert tp.loc[0, "tuning_status"] == "finetuned" and tp.loc[0, "seconds"] >= 0


def test_throughput_rows_per_second():
    rows = [_row("gemma-2-9b-pretrained", f"i{k}", "blame", "w1", False, "moral", "bad", 5) for k in range(5)]
    f = _frame(rows).assign(timestamp=[100.0, 101.0, 102.0, 103.0, 104.0])
    tp = checks.throughput(f)
    assert tp.loc[0, "seconds"] == 4.0 and tp.loc[0, "rows_per_second"] == 1.25
