import ast
import asyncio
import inspect
import json
import textwrap
from types import SimpleNamespace

import pandas as pd
import pytest
from knobe import curate
from knobe.schemas import CurationRawResult, read_jsonl
from pydantic import ValidationError

from kmp import prompts, protocol, screen, screen_run
from kmp.items import load_items, write_items




def _get(items, arm, sign, sid=1):
    return next(i for i in items if i.arm == arm and i.sign == sign and i.storyline_id == sid)


NM_GOOD_SCORES = {"domain_moral": 2, "domain_prudential": 8, "domain_procedural": 1}


def test_valence_thresholds(nonmoral_items):
    bad, good = _get(nonmoral_items, "prudential", "bad"), _get(nonmoral_items, "prudential", "good")
    assert screen.item_failures(bad, {"valence": 2, **NM_GOOD_SCORES}) == []
    assert "valence 5 > 3 for a bad item" in screen.item_failures(bad, {"valence": 5, **NM_GOOD_SCORES})
    assert "valence 6 < 7 for a good item" in screen.item_failures(good, {"valence": 6, **NM_GOOD_SCORES})


def test_nonmoral_domain_must_be_high_and_highest(nonmoral_items):
    item = _get(nonmoral_items, "prudential", "bad")
    low = {"valence": 1, "domain_moral": 2, "domain_prudential": 5, "domain_procedural": 1}
    tie = {"valence": 1, "domain_moral": 8, "domain_prudential": 8, "domain_procedural": 1}
    assert "domain_prudential 5 < 6" in screen.item_failures(item, low)
    assert "domain_prudential is not the highest domain rating" in screen.item_failures(item, tie)


def test_foundation_must_beat_harm(foundation_items):
    item = _get(foundation_items, "loyalty", "bad")
    base = {"valence": 1, "fnd_fairness": 1, "fnd_authority": 1, "fnd_purity": 1}
    assert screen.item_failures(item, {**base, "fnd_loyalty": 8, "fnd_harm": 3}) == []
    assert "fnd_loyalty 7 not higher than fnd_harm 7" in screen.item_failures(item, {**base, "fnd_loyalty": 7, "fnd_harm": 7})


def test_harm_control_needs_harm(foundation_items):
    item = _get(foundation_items, "harm", "bad")
    assert "fnd_harm 4 < 6" in screen.item_failures(item, {"valence": 1, "fnd_harm": 4})


def test_unparsed_is_a_named_failure(nonmoral_items):
    item = _get(nonmoral_items, "moral", "bad")
    assert "valence unparsed" in screen.item_failures(item, {"valence": None, "domain_moral": 9,
                                                            "domain_prudential": 1, "domain_procedural": 1})


def test_select_pairs_drops_the_whole_pair(nonmoral_items):
    pair = [_get(nonmoral_items, "prudential", "bad"), _get(nonmoral_items, "prudential", "good")]
    scores = {pair[0].item_id: {"valence": 1, **NM_GOOD_SCORES},
              pair[1].item_id: {"valence": 4, **NM_GOOD_SCORES}}
    selected, report = screen.select_pairs(pair, scores)
    assert selected == []
    assert [r["pair_passed"] for r in report] == [False, False]
    assert report[1]["failures"] == "valence 4 < 7 for a good item"


def test_select_pairs_flags_missing_partner(nonmoral_items):
    selected, report = screen.select_pairs([_get(nonmoral_items, "moral", "bad")], {})
    assert selected == [] and "partner not approved" in report[0]["failures"]


def _nm(items, sign):
    return _get(items, "prudential", sign)


@pytest.mark.parametrize("v,ok", [(3, True), (4, False)])
def test_bad_valence_boundary(nonmoral_items, v, ok):
    f = screen.item_failures(_nm(nonmoral_items, "bad"), {"valence": v, **NM_GOOD_SCORES})
    assert (f == []) is ok


@pytest.mark.parametrize("v,ok", [(7, True), (6, False)])
def test_good_valence_boundary(nonmoral_items, v, ok):
    f = screen.item_failures(_nm(nonmoral_items, "good"), {"valence": v, **NM_GOOD_SCORES})
    assert (f == []) is ok


@pytest.mark.parametrize("t,ok", [(6, True), (5, False)])
def test_target_boundary(nonmoral_items, t, ok):
    s = {"valence": 1, "domain_moral": 0, "domain_prudential": t, "domain_procedural": 0}
    assert (screen.item_failures(_nm(nonmoral_items, "bad"), s) == []) is ok


def test_fully_passing_good_item_and_harm_control(nonmoral_items, foundation_items):
    assert screen.item_failures(_nm(nonmoral_items, "good"), {"valence": 7, **NM_GOOD_SCORES}) == []
    assert screen.item_failures(_get(foundation_items, "harm", "good"), {"valence": 9, "fnd_harm": 6}) == []


def test_foundation_harm_one_below_target_passes(foundation_items):
    item = _get(foundation_items, "loyalty", "bad")
    s = {"valence": 1, "fnd_fairness": 1, "fnd_authority": 1, "fnd_purity": 1, "fnd_loyalty": 6, "fnd_harm": 5}
    assert screen.item_failures(item, s) == []


def test_unparsed_paths(nonmoral_items, foundation_items):
    nm = _nm(nonmoral_items, "bad")
    assert screen.item_failures(nm, None) == ["not rated"]
    f = screen.item_failures(nm, {"valence": 1, "domain_moral": None, "domain_prudential": 8, "domain_procedural": None})
    assert "domain_moral unparsed" in f and "domain_procedural unparsed" in f
    assert "domain_prudential unparsed" in screen.item_failures(nm, {"valence": 1, "domain_prudential": None})
    fi = _get(foundation_items, "loyalty", "bad")
    assert "fnd_harm unparsed" in screen.item_failures(fi, {"valence": 1, "fnd_loyalty": 8, "fnd_harm": None})


def test_duplicate_ids_raise(nonmoral_items):
    with pytest.raises(ValueError, match="duplicate"):
        screen.select_pairs([nonmoral_items[0], nonmoral_items[0]], {})


def test_two_same_sign_members_are_not_a_pair(nonmoral_items):
    a = _nm(nonmoral_items, "bad")
    b = a.model_copy(update={"item_id": a.item_id + "x"})
    _, report = screen.select_pairs([a, b], {})
    assert all("partner not approved" in r["failures"] for r in report)


def test_report_has_pair_key_and_scores(nonmoral_items):
    pair = [_nm(nonmoral_items, "bad"), _nm(nonmoral_items, "good")]
    sc = {pair[0].item_id: {"valence": 1, **NM_GOOD_SCORES}}
    _, report = screen.select_pairs(pair, sc)
    assert report[0]["pair_key"] == report[1]["pair_key"] == "nonmoral|1|prudential"
    assert report[0]["scores"]["valence"] == 1 and report[1]["scores"] == {}
    assert report[1]["failures"] == "not rated"


# --------------------------------------------------------------------------
# Runner, reviewer client and CLI (kmp.screen_run). No test may reach the
# real Anthropic API: reviewers are ScriptedClient / MockClient, and real-run
# paths monkeypatch ScreeningClient.
# --------------------------------------------------------------------------

PINNED = "claude-test-reviewer-20260101"


class ScriptedClient:
    """Answers by rule from the [arm] [sign] markers in make_items' scenarios.
    `flaky` holds (item_id, qkey) keys that answer 'unclear' on first call;
    `fail_after` raises a non-transient error once that many calls succeeded."""

    def __init__(self, items, flaky=(), fail_after=None):
        self.lookup = {p.text: (p.item_id, p.qkey) for p in prompts.build_screening_prompts(items)}
        self.items = {i.item_id: i for i in items}
        self.flaky = set(flaky)
        self.fail_after = fail_after
        self.calls = []

    async def complete(self, prompt, max_tokens):
        if self.fail_after is not None and len(self.calls) >= self.fail_after:
            raise RuntimeError("scripted non-transient failure")
        item_id, qkey = self.lookup[prompt]
        self.calls.append((item_id, qkey))
        if (item_id, qkey) in self.flaky:
            self.flaky.discard((item_id, qkey))
            return "unclear"
        item = self.items[item_id]
        if qkey == "valence":
            return "1" if item.sign == "bad" else "9"
        return "8" if qkey == screen.intended_check(item) else "2"


def _run(ps, client, out, reviewer="scripted", **kw):
    return asyncio.run(screen_run.run_screening(ps, client, reviewer, out, **kw))


def _raw(out):
    return read_jsonl(out, screen.ScreeningRawResult)


def _write(items, tmp_path):
    path = tmp_path / "items.csv"
    write_items(items, path)
    return path


def test_run_screening_resumes_and_retries_unparsed_once(tmp_path, nonmoral_items):
    out = tmp_path / "raw.jsonl"
    ps = prompts.build_screening_prompts(nonmoral_items)
    flaky_key = (ps[0].item_id, ps[0].qkey)
    client = ScriptedClient(nonmoral_items, flaky=[flaky_key])
    _run(ps, client, out)
    rows = _raw(out)
    assert len(rows) == len(ps) + 1                                  # one retry
    assert screen_run.scores_from_raw(rows, ps, "scripted")[flaky_key[0]][flaky_key[1]] is not None
    _run(ps, client, out)
    assert len(_raw(out)) == len(rows)                                # resume: nothing re-asked


def test_all_pairs_pass_under_scripted_reviewer(tmp_path, foundation_items):
    out = tmp_path / "raw.jsonl"
    ps = prompts.build_screening_prompts(foundation_items)
    _run(ps, ScriptedClient(foundation_items), out)
    selected, _ = screen.select_pairs(foundation_items, screen_run.scores_from_raw(_raw(out), ps, "scripted"))
    assert len(selected) == len(foundation_items)


def test_main_mock_writes_outputs(tmp_path, nonmoral_items):
    code = screen_run.main(["--items", str(_write(nonmoral_items, tmp_path)), "--out-dir", str(tmp_path / "s"),
                            "--mock"])
    assert code == 0
    assert (tmp_path / "s" / "screening_raw.jsonl").exists()
    assert (tmp_path / "s" / "selection_report.csv").exists()
    load_items(tmp_path / "s" / "selected_items.csv")                 # valid, possibly empty


def _raw_row(field, model="scripted", sha="0" * 64, variant_id="kmp-x"):
    return screen.ScreeningRawResult(variant_id=variant_id, field=field, value=3, ok=True, raw="3",
                                     reviewer_model=model, timestamp=0.0, text_sha256=sha)


def test_screening_raw_result_round_trips_kmp_qkeys_and_rejects_unknown():
    for qkey in sorted(screen.SCREENING_QKEYS):
        row = _raw_row(qkey)
        assert screen.ScreeningRawResult.model_validate_json(row.model_dump_json()) == row
    for bad in ("blame", "moral_relevance", "nonsense"):
        with pytest.raises(ValidationError):
            _raw_row(bad)


def test_screening_raw_result_fields_cover_curation_raw_result():
    assert set(CurationRawResult.model_fields) <= set(screen.ScreeningRawResult.model_fields)


def test_raw_rows_carry_prompt_hash(tmp_path, nonmoral_items):
    out = tmp_path / "raw.jsonl"
    ps = prompts.build_screening_prompts(nonmoral_items)
    _run(ps, ScriptedClient(nonmoral_items), out)
    want = {(p.item_id, p.qkey): p.text_sha256 for p in ps}
    assert {(r.variant_id, r.field): r.text_sha256 for r in _raw(out)} == want


def _scripted_scores(tmp_path, items):
    out = tmp_path / "raw.jsonl"
    ps = prompts.build_screening_prompts(items)
    _run(ps, ScriptedClient(items), out)
    return screen_run.scores_from_raw(_raw(out), ps, "scripted")


def test_pair_summary_counts_singleton_pairs_by_pair_key(tmp_path, nonmoral_items):
    approved = [i for i in nonmoral_items if i.item_id != _get(nonmoral_items, "moral", "good").item_id]
    _, report = screen.select_pairs(approved, _scripted_scores(tmp_path, approved))
    summary = screen_run.pair_summary(report)
    assert summary["moral"] == {"pairs": 2, "pairs_passed": 1}            # rows // 2 would give 1 pair
    assert summary["prudential"] == summary["procedural"] == {"pairs": 2, "pairs_passed": 2}


def test_main_records_thresholds_pair_counts_and_json_scores(tmp_path, nonmoral_items):
    singleton = _get(nonmoral_items, "moral", "good")
    items = [i.model_copy(update={"review_status": "draft"}) if i.item_id == singleton.item_id else i
             for i in nonmoral_items]
    assert screen_run.main(["--items", str(_write(items, tmp_path)), "--out-dir", str(tmp_path / "s"),
                            "--mock"]) == 0
    meta = json.loads((tmp_path / "s" / "screening_meta.json").read_text())
    assert meta["reviewer_model"] == "mock" and meta["reviewer_temperature"] is None
    assert (meta["valence_bad_max"], meta["valence_good_min"], meta["target_min"]) == (
        screen.VALENCE_BAD_MAX, screen.VALENCE_GOOD_MIN, screen.TARGET_MIN)
    assert {arm: c["pairs"] for arm, c in meta["pairs_by_arm"].items()} == {
        "moral": 2, "procedural": 2, "prudential": 2}
    report = pd.read_csv(tmp_path / "s" / "selection_report.csv")
    assert set(report["pair_key"]) and len(report) == len(nonmoral_items) - 1
    for cell in report["scores"]:
        assert set(json.loads(cell)) == {"valence", *protocol.DOMAIN_CHECKS}


# --- resume provenance (review item 1) ---

def test_scores_from_raw_uses_only_rows_matching_model_and_hash(nonmoral_items):
    ps = prompts.build_screening_prompts(nonmoral_items)
    p = ps[0]
    rows = [_raw_row(p.qkey, model="other", sha=p.text_sha256, variant_id=p.item_id),
            _raw_row(p.qkey, model="scripted", sha="f" * 64, variant_id=p.item_id)]
    assert screen_run.scores_from_raw(rows, ps, "scripted") == {}
    rows.append(_raw_row(p.qkey, model="scripted", sha=p.text_sha256, variant_id=p.item_id))
    assert screen_run.scores_from_raw(rows, ps, "scripted") == {p.item_id: {p.qkey: 3}}


def test_resume_refuses_other_reviewer_model(tmp_path, nonmoral_items):
    out_dir = tmp_path / "s"
    items_path = _write(nonmoral_items, tmp_path)
    assert screen_run.main(["--items", str(items_path), "--out-dir", str(out_dir), "--mock"]) == 0
    n = len(_raw(out_dir / "screening_raw.jsonl"))
    ps = prompts.build_screening_prompts(nonmoral_items)
    with pytest.raises(screen_run.ResumeRefused, match="mock"):
        _run(ps, ScriptedClient(nonmoral_items), out_dir / "screening_raw.jsonl")
    assert len(_raw(out_dir / "screening_raw.jsonl")) == n


def test_main_refuses_mixed_models_with_exit_2(tmp_path, nonmoral_items, monkeypatch, capsys):
    out_dir = tmp_path / "s"
    items_path = _write(nonmoral_items, tmp_path)
    assert screen_run.main(["--items", str(items_path), "--out-dir", str(out_dir), "--mock"]) == 0
    monkeypatch.setattr(protocol, "REVIEWER_MODEL", PINNED)
    monkeypatch.setattr(screen_run, "ScreeningClient", lambda model: pytest.fail("client built"))
    assert screen_run.main(["--items", str(items_path), "--out-dir", str(out_dir)]) == 2
    assert "reviewer model" in capsys.readouterr().err


def test_resume_refuses_changed_prompt_text(tmp_path, nonmoral_items):
    out = tmp_path / "raw.jsonl"
    ps = prompts.build_screening_prompts(nonmoral_items)
    _run(ps, ScriptedClient(nonmoral_items), out)
    edited = [i.model_copy(update={"scenario": i.scenario + " Edited."}) if i.arm == "moral" else i
              for i in nonmoral_items]
    ps2 = prompts.build_screening_prompts(edited)
    with pytest.raises(screen_run.ResumeRefused, match="text_sha256") as exc:
        _run(ps2, ScriptedClient(edited), out)
    assert "kmp-" in str(exc.value)


# --- dry run, pinning and the real-run guards (items 2, 3, 6) ---

def test_dry_run_prints_cost_and_builds_no_client(tmp_path, nonmoral_items, monkeypatch, capsys):
    monkeypatch.setattr(screen_run, "ScreeningClient", lambda model: pytest.fail("client built"))
    monkeypatch.setattr(screen_run, "MockClient", lambda **kw: pytest.fail("client built"))
    out_dir = tmp_path / "s"
    assert screen_run.main(["--items", str(_write(nonmoral_items, tmp_path)), "--out-dir", str(out_dir),
                            "--dry-run"]) == 0
    n = len(prompts.build_screening_prompts(nonmoral_items))
    out = capsys.readouterr().out
    assert f"{n} screening prompts" in out and f"{2 * n} calls" in out and "tokens" in out
    assert not out_dir.exists()


def test_real_run_refuses_unpinned_or_mismatched_or_latest(tmp_path, nonmoral_items, monkeypatch, capsys):
    monkeypatch.setattr(screen_run, "ScreeningClient", lambda model: pytest.fail("client built"))
    args = ["--items", str(_write(nonmoral_items, tmp_path)), "--out-dir", str(tmp_path / "s")]
    monkeypatch.setattr(protocol, "REVIEWER_MODEL", None)
    assert screen_run.main(args) == 2
    assert "protocol.py" in capsys.readouterr().err
    monkeypatch.setattr(protocol, "REVIEWER_MODEL", PINNED)
    assert screen_run.main([*args, "--reviewer-model", "claude-other-20260101"]) == 2
    assert "protocol.py" in capsys.readouterr().err
    monkeypatch.setattr(protocol, "REVIEWER_MODEL", "claude-test-latest")
    assert screen_run.main(args) == 2
    assert "-latest" in capsys.readouterr().err
    assert not (tmp_path / "s" / "screening_raw.jsonl").exists()


def test_real_run_checks_subject_guard_before_any_call(tmp_path, nonmoral_items, monkeypatch):
    events = []
    monkeypatch.setattr(protocol, "REVIEWER_MODEL", PINNED)
    monkeypatch.setattr(screen_run, "check_reviewer_not_subject", lambda m, reg: events.append(("guard", m)))

    def fake_client(model):
        events.append(("client", model))
        client = ScriptedClient(nonmoral_items)
        client.input_tokens_used, client.output_tokens_used, client.served_models = 11, 7, {PINNED}
        return client

    monkeypatch.setattr(screen_run, "ScreeningClient", fake_client)
    out_dir = tmp_path / "s"
    assert screen_run.main(["--items", str(_write(nonmoral_items, tmp_path)), "--out-dir", str(out_dir)]) == 0
    assert events == [("guard", PINNED), ("client", PINNED)]
    assert {r.reviewer_model for r in _raw(out_dir / "screening_raw.jsonl")} == {PINNED}
    meta = json.loads((out_dir / "screening_meta.json").read_text())
    assert meta["reviewer_temperature"] == 0.0
    assert (meta["input_tokens"], meta["output_tokens"], meta["served_models"]) == (11, 7, [PINNED])


def test_real_run_subject_conflict_exits_2_without_writing(tmp_path, nonmoral_items, monkeypatch, capsys):
    def guard(model, registry):
        raise curate.ReviewerSubjectConflictError(f"{model} is a subject")

    monkeypatch.setattr(protocol, "REVIEWER_MODEL", PINNED)
    monkeypatch.setattr(screen_run, "check_reviewer_not_subject", guard)
    monkeypatch.setattr(screen_run, "ScreeningClient", lambda model: pytest.fail("client built"))
    out_dir = tmp_path / "s"
    assert screen_run.main(["--items", str(_write(nonmoral_items, tmp_path)), "--out-dir", str(out_dir)]) == 2
    assert "is a subject" in capsys.readouterr().err
    assert not (out_dir / "screening_raw.jsonl").exists()


def test_mock_with_reviewer_model_is_an_error(tmp_path, nonmoral_items):
    with pytest.raises(SystemExit):
        screen_run.main(["--items", str(_write(nonmoral_items, tmp_path)), "--out-dir", str(tmp_path),
                         "--mock", "--reviewer-model", PINNED])


def test_concurrency_must_be_positive(tmp_path, nonmoral_items):
    with pytest.raises(SystemExit):
        screen_run.main(["--items", str(_write(nonmoral_items, tmp_path)), "--out-dir", str(tmp_path),
                         "--mock", "--concurrency", "0"])


class _FakeMessages:
    def __init__(self):
        self.kwargs = []

    async def create(self, **kwargs):
        self.kwargs.append(kwargs)
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=" 4 ")], model=PINNED + "-served",
                               usage=SimpleNamespace(input_tokens=5, output_tokens=1))


def test_screening_client_sends_temperature_zero_single_user_message():
    client = screen_run.ScreeningClient.__new__(screen_run.ScreeningClient)
    fake = _FakeMessages()
    client.model, client._client = PINNED, SimpleNamespace(messages=fake)
    client.input_tokens_used = client.output_tokens_used = 0
    client.served_models = set()
    assert asyncio.run(client.complete("hello", 8)) == "4"
    (kw,) = fake.kwargs
    assert kw["temperature"] == 0.0 and kw["model"] == PINNED and kw["max_tokens"] == 8
    assert kw["messages"] == [{"role": "user", "content": "hello"}]
    assert client.served_models == {PINNED + "-served"} and client.input_tokens_used == 5


def _body(fn, drop_kw=None, drop_call=None):
    """ast.dump of fn's top-level statements, docstring stripped, minus any
    `drop_kw=` keyword argument and any top-level `self.<drop_call>(...)` statement."""
    body = ast.parse(textwrap.dedent(inspect.getsource(fn))).body[0].body
    if isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        body = body[1:]
    if drop_call:
        body = [s for s in body if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Call)
                                        and isinstance(s.value.func, ast.Attribute)
                                        and s.value.func.attr == drop_call)]
    for node in ast.walk(ast.Module(body=body, type_ignores=[])):
        if drop_kw and isinstance(node, ast.Call):
            node.keywords = [k for k in node.keywords if k.arg != drop_kw]
    return [ast.dump(s) for s in body]


def test_screening_client_complete_tracks_parent():
    parent = _body(curate.AnthropicClient.complete)
    ours = _body(screen_run.ScreeningClient.complete, drop_kw="temperature", drop_call="_note_served")
    assert ours == parent, "parent changed; re-sync ScreeningClient"


# --- provenance record (item 4) ---

def test_meta_and_run_log_record_provenance(tmp_path, nonmoral_items):
    items_path = _write(nonmoral_items, tmp_path)
    out_dir = tmp_path / "s"
    args = ["--items", str(items_path), "--out-dir", str(out_dir), "--mock"]
    assert screen_run.main(args) == 0
    assert screen_run.main(args) == 0
    n = len(prompts.build_screening_prompts(nonmoral_items))
    meta = json.loads((out_dir / "screening_meta.json").read_text())
    runs = [json.loads(line) for line in (out_dir / "screening_runs.jsonl").read_text().splitlines()]
    assert len(runs) == 2 and runs[-1] == meta
    assert (runs[0]["prompts_asked"], runs[0]["prompts_reused"]) == (n, 0)
    assert (meta["prompts_asked"], meta["prompts_reused"]) == (0, n)
    assert meta["items_sha256"] == screen_run.file_sha256(items_path)
    assert meta["raw_reviewer_models"] == ["mock"]
    assert "git_commit" in meta and meta["started_utc"] <= meta["finished_utc"]


# --- crash safety (items 9, 10) ---

def test_torn_last_line_is_dropped_with_warning(tmp_path, nonmoral_items, capsys):
    out = tmp_path / "raw.jsonl"
    ps = prompts.build_screening_prompts(nonmoral_items)
    _run(ps, ScriptedClient(nonmoral_items), out)
    with open(out, "a", encoding="utf-8") as fh:
        fh.write('{"variant_id": "kmp-')
    rows = screen_run._read_raw(out)
    assert len(rows) == len(ps) and "torn" in capsys.readouterr().err
    assert len(_raw(out)) == len(ps)                                  # file repaired


def test_corrupt_middle_line_is_an_error(tmp_path, nonmoral_items):
    out = tmp_path / "raw.jsonl"
    ps = prompts.build_screening_prompts(nonmoral_items)
    _run(ps, ScriptedClient(nonmoral_items), out)
    lines = out.read_text().splitlines()
    out.write_text("\n".join([lines[0], "garbage", *lines[1:]]) + "\n")
    with pytest.raises(ValueError, match="line 2"):
        screen_run._read_raw(out)


def test_aborted_run_resumes_with_only_the_remaining_prompts(tmp_path, nonmoral_items):
    out = tmp_path / "raw.jsonl"
    ps = prompts.build_screening_prompts(nonmoral_items)
    with pytest.raises(RuntimeError, match="non-transient"):
        _run(ps, ScriptedClient(nonmoral_items, fail_after=5), out, concurrency=1)
    assert len(_raw(out)) == 5
    second = ScriptedClient(nonmoral_items)
    _run(ps, second, out)
    assert len(second.calls) == len(ps) - 5 and len(_raw(out)) == len(ps)
