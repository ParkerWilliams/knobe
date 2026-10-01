import json

import numpy as np
import pandas as pd
import pytest
from knobe.schemas import ResultRecord, append_jsonl

from conftest import make_items, make_ngo_verbatim_items
from kmp import checks, elicit
from kmp.items import write_items

COLS = ["model_key", "tuning_status", "family", "experiment", "item_id", "qkey", "wording_key", "reversed",
        "arm", "sign", "parse_ok", "parsed_rating_raw", "rating"]


def _frame(rows):
    return pd.DataFrame(rows, columns=COLS)


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


# --- main: provenance in the report (amendment C) ---------------------------

def _write_results(path, rows):
    with open(path, "w", encoding="utf-8") as fh:
        for pid, mk, value in rows:
            append_jsonl(ResultRecord(
                job_id=f"{pid}::{mk}::0", prompt_id=pid, model_key=mk, sample_idx=0, temperature=1.0, seed=1,
                raw_response="x" if value is None else str(value), parsed_rating=value, parse_ok=value is not None,
                parse_method="regex", logprobs_0_10=None, model_revision="r", runner_version="t", timestamp=0.0), fh)


def _run_main(tmp_path, items, rows, manifest=None):
    results, items_csv, out_dir = tmp_path / "r.jsonl", tmp_path / "items.csv", tmp_path / "checks"
    _write_results(results, rows)
    write_items(items, items_csv)
    if manifest is not None:
        elicit.manifest_path(results).write_text(json.dumps(manifest), encoding="utf-8")
    code = checks.main(["--results", str(results), "--items", str(items_csv), "--out-dir", str(out_dir)])
    return code, out_dir


def test_main_records_dropped_items_and_manifest(tmp_path, capsys):
    mk = "gemma-2-9b-instruct"
    rows = [(f"kmp-nv-001-moral-{s}::{q}::w1::chat", mk, v)
            for q, s, v in (("blame", "bad", 8), ("blame", "good", 2), ("praise", "bad", 1), ("praise", "good", 7))]
    rows.append(("kmp-nv-099-moral-bad::blame::w1::chat", mk, 5))
    manifest = {"release": "knobe_moral_probe", "runner_version": "v", "max_tokens": 10, "engine": "fake",
                "model_keys": [mk], "prompts": {"p": "sha"}}
    code, out_dir = _run_main(tmp_path, make_ngo_verbatim_items(1), rows, manifest)
    assert code == 0
    prov = json.loads((out_dir / "provenance.json").read_text())
    assert prov["n_dropped_unknown_items"] == 1
    assert prov["dropped_unknown_item_ids"] == ["kmp-nv-099-moral-bad"]
    assert prov["experiments"] == ["ngo_verbatim"]
    assert prov["manifest"] == {k: manifest[k] for k in elicit.RUN_FIELDS}
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


# --- blocking vs non-blocking (DESIGN.md section 8) --------------------------

def _ngo_rows(mk, blame=(8, 2), praise=(1, 7)):
    """blame/praise = (bad, good) ratings for one ngo_verbatim pair."""
    fmt = "raw" if mk.endswith("pretrained") else "chat"
    return [(f"kmp-nv-001-moral-{s}::{q}::w1::{fmt}", mk, v)
            for q, vals in (("blame", blame), ("praise", praise)) for s, v in zip(("bad", "good"), vals)]


@pytest.mark.parametrize("mk, kwargs, code, blocked", [
    ("gemma-2-9b-instruct", dict(blame=(2, 8)), 1, "validity"),         # finetuned validity fail blocks
    ("gemma-2-9b-pretrained", dict(blame=(2, 8)), 0, None),              # pretrained: a finding
    ("gemma-2-9b-instruct", dict(blame=(9, 0), praise=(0, 9)), 1, "example_copying"),
    ("gemma-2-9b-pretrained", dict(blame=(9, 0), praise=(0, 9)), 0, None),
])
def test_main_blocks_on_finetuned_problems_only(tmp_path, capsys, mk, kwargs, code, blocked):
    got, out_dir = _run_main(tmp_path, make_ngo_verbatim_items(1), _ngo_rows(mk, **kwargs))
    assert got == code
    gate = json.loads((out_dir / "provenance.json").read_text())["gate"]
    err = capsys.readouterr().err
    assert "gate summary" in err
    if blocked:
        assert len(gate["blocking"]) == 1 and gate["blocking"][0].startswith(blocked)
    else:
        assert gate["blocking"] == [] and len(gate["findings"]) == 1
        assert gate["findings"][0].startswith(("validity", "example_copying"))


def test_main_blocks_on_finetuned_no_data(tmp_path):
    rows = [r for r in _ngo_rows("gemma-2-9b-instruct") if "::praise::" not in r[0]]
    code, out_dir = _run_main(tmp_path, make_ngo_verbatim_items(1), rows)
    assert code == 1
    gate = json.loads((out_dir / "provenance.json").read_text())["gate"]
    assert len(gate["blocking"]) == 1 and "no_data" in gate["blocking"][0]


def test_main_clean_run_has_no_blocking_or_findings(tmp_path):
    code, out_dir = _run_main(tmp_path, make_ngo_verbatim_items(1), _ngo_rows("gemma-2-9b-instruct"))
    assert code == 0
    assert json.loads((out_dir / "provenance.json").read_text())["gate"] == {"blocking": [], "findings": []}
