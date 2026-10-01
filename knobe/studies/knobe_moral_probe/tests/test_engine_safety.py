"""--engine has no default (a cluster command that forgets it must not write
fake answers into a real --out), and checks flags a fake-engine run loudly."""
import json
import subprocess
from pathlib import Path

import pytest

from conftest import make_items
from kmp import checks, elicit
from kmp.items import write_items

STUDY = Path(__file__).resolve().parents[1]


def _items(tmp_path):
    path = tmp_path / "items.csv"
    write_items(make_items("nonmoral", 1)[:2], path)
    return path


def test_elicit_requires_engine(tmp_path, capsys):
    out = tmp_path / "o.jsonl"
    with pytest.raises(SystemExit) as exc:
        elicit.main(["--items", str(_items(tmp_path)), "--out", str(out), "--model-keys", "mistral-7b-v0.1-instruct"])
    assert exc.value.code == 2
    assert "--engine" in capsys.readouterr().err
    assert not out.exists()


def _fake_run(tmp_path):
    items = _items(tmp_path)
    out = tmp_path / "o.jsonl"
    assert elicit.main(["--items", str(items), "--out", str(out), "--engine", "fake",
                        "--model-keys", "mistral-7b-v0.1-instruct"]) == 0
    return items, out


def test_checks_warns_and_records_a_fake_engine_run(tmp_path, capsys):
    items, out = _fake_run(tmp_path)
    checks.main(["--results", str(out), "--items", str(items), "--out-dir", str(tmp_path / "c")])
    assert "WARNING: these results come from the FAKE engine" in capsys.readouterr().err
    prov = json.loads((tmp_path / "c" / "provenance.json").read_text())
    assert prov["fake_engine"] is True


def test_checks_records_a_real_engine_run_as_not_fake(tmp_path, capsys):
    items, out = _fake_run(tmp_path)
    mpath = elicit.manifest_path(out)
    manifest = json.loads(mpath.read_text())
    mpath.write_text(json.dumps({**manifest, "engine": "vllm"}))
    checks.main(["--results", str(out), "--items", str(items), "--out-dir", str(tmp_path / "c")])
    assert "FAKE engine" not in capsys.readouterr().err
    assert json.loads((tmp_path / "c" / "provenance.json").read_text())["fake_engine"] is False


def test_gitignore_keeps_check_tables_and_ignores_dumps_and_tmp():
    def ignored(rel):
        r = subprocess.run(["git", "check-ignore", "-q", "--no-index", rel], cwd=STUDY)
        return r.returncode == 0
    assert not ignored("outputs/checks/nonmoral/provenance.json")
    assert not ignored("outputs/checks/nonmoral/coverage.csv")
    assert not ignored("outputs/elicit/nonmoral.jsonl.manifest.json")
    assert ignored("outputs/elicit/nonmoral.jsonl")
    assert ignored("outputs/elicit/nonmoral.jsonl.starts.jsonl")
    assert ignored("outputs/elicit/nonmoral.jsonl.lock")
    assert ignored("outputs/elicit/nonmoral.jsonl.manifest.json.abc123.tmp")
