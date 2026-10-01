import numpy as np
import pandas as pd
import pytest

from kmp import checks

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
    assert out.loc["blame_bad_minus_good", "value"] == 6 and out.loc["blame_bad_minus_good", "passes"]
    assert out.loc["praise_good_minus_bad", "passes"]
    assert out.loc["significance_moral_minus_procedural", "value"] == 7
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
