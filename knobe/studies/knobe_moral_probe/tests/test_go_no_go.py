"""tools.go_no_go: the pilot's gate lines sorted into GO / NO-GO by fixed rules (docs/FULL_RUN.md)."""
import json

from tools import go_no_go


def _dir(tmp_path, name, blocking, findings=()):
    d = tmp_path / name
    d.mkdir()
    (d / "provenance.json").write_text(json.dumps({"gate": {"blocking": list(blocking), "findings": list(findings)}}))
    return d


def test_clean_pilot_is_go(tmp_path):
    v = go_no_go.decide([_dir(tmp_path, "a", [], ["validity: llama-3.1-8b-pretrained nonmoral blame_bad_minus_good fail"])])
    assert v["go"] and not v["stops"]


def test_pretrained_number_rate_and_llama_refusal_cells_are_allowed(tmp_path):
    lines = ["number_rate: gemma-2-9b-pretrained nonmoral blame w1 0.40 < 0.90",
             "number_rate: llama-3.1-8b-instruct nonmoral intentionality w1 0.81 < 0.90",
             "number_rate: llama-3.1-8b-instruct foundations praise w3r 0.72 < 0.90"]
    v = go_no_go.decide([_dir(tmp_path, "a", lines)])
    assert v["go"] and len(v["allowed"]) == 3


def test_stops(tmp_path):
    lines = ["cut_off: gemma-2-9b-instruct nonmoral blame w1 chat 0.03 > 0.01 of replies stopped at the token budget",
             "number_rate: llama-3.1-8b-instruct nonmoral intentionality w2 0.65 < 0.90",
             "number_rate: mistral-7b-v0.1-instruct nonmoral blame w1 0.85 < 0.90",
             "number_rate: llama-3.1-8b-instruct nonmoral blame w1 0.85 < 0.90",
             "coverage: gemma-2-9b-instruct has no rows",
             "validity: mistral-7b-v0.1-instruct nonmoral blame_bad_minus_good fail (value -0.20)",
             "example_copying: gemma-2-9b-instruct nonmoral blame excess 0.15 > 0.10 (with 0.30, without 0.15)"]
    v = go_no_go.decide([_dir(tmp_path, "a", lines)])
    assert not v["go"] and len(v["stops"]) == len(lines)


def test_missing_checks_dir_is_no_go(tmp_path):
    v = go_no_go.decide([tmp_path / "absent"])
    assert not v["go"] and "provenance.json" in v["stops"][0]
