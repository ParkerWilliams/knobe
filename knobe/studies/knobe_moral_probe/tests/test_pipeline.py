"""items -> screening (scripted reviewer) -> selection -> elicitation (fake
engine, one pretrained + one instruct key, with a resume) -> frame -> checks,
on synthetic items from all three experiments. One --out per experiment: an
items file can't mix experiments."""
import asyncio
import json

import pytest
from knobe.schemas import ResultRecord, read_jsonl

from conftest import make_items, make_ngo_verbatim_items, make_purpose_storyline
from test_screen import ScriptedClient
from kmp import checks, elicit, frame, prompts, protocol, screen, screen_run
from kmp.items import design_problems, load_items, write_items

KEYS = ["mistral-7b-v0.1-pretrained", "mistral-7b-v0.1-instruct"]
REVIEWER = "scripted"

EXPERIMENT_ITEMS = {
    "nonmoral": lambda: make_items("nonmoral", 1),
    "foundations": lambda: make_items("foundations", 1) + make_purpose_storyline(2),
    "ngo_verbatim": lambda: make_ngo_verbatim_items(1),
}


def _expected_jobs(items) -> int:
    """Per item and model: wordings x n_samples, summed over the item's questions."""
    per_model = sum(len(protocol.QUESTIONS[q]) * protocol.n_samples(q)
                    for item in items for q in protocol.subject_qkeys(item))
    return per_model * len(KEYS)


@pytest.mark.parametrize("experiment", sorted(EXPERIMENT_ITEMS))
def test_pipeline(tmp_path, experiment):
    items = EXPERIMENT_ITEMS[experiment]()
    assert {i.experiment for i in items} == {experiment}
    assert design_problems(items) == []

    # Screening: scripted reviewer, every pair passes.
    raw = tmp_path / "screening_raw.jsonl"
    screening_prompts = prompts.build_screening_prompts(items)
    asyncio.run(screen_run.run_screening(screening_prompts, ScriptedClient(items), REVIEWER, raw))
    scores = screen_run.scores_from_raw(screen_run._read_raw(raw), screening_prompts, REVIEWER)
    selected, report = screen.select_pairs(items, scores)
    assert len(selected) == len(items) and all(r["pair_passed"] for r in report)
    assert screen.shared_without_harm(items, selected) == []
    selected_path = tmp_path / "selected_items.csv"
    write_items(selected, selected_path)

    # Elicitation, interrupted a third of the way in (mid-model) and resumed.
    out = tmp_path / "results.jsonl"
    argv = ["--items", str(selected_path), "--out", str(out), "--engine", "fake", "--model-keys", ",".join(KEYS)]
    assert elicit.main(argv) == 0
    n_jobs = _expected_jobs(selected)
    full = {r.job_id: r.raw_response for r in read_jsonl(out, ResultRecord)}
    assert len(full) == n_jobs
    lines = out.read_text(encoding="utf-8").splitlines(keepends=True)
    out.write_text("".join(lines[: n_jobs // 3]), encoding="utf-8")
    assert elicit.main(argv) == 0
    resumed = read_jsonl(out, ResultRecord)
    assert len(resumed) == n_jobs and {r.job_id: r.raw_response for r in resumed} == full

    # Frame.
    d = frame.load_frame(out, load_items(selected_path))
    assert len(d) == n_jobs and set(d["experiment"]) == {experiment}
    assert set(d["fmt"]) == {"raw", "chat"}
    assert set(d["tuning_status"]) == {"pretrained", "finetuned"} and set(d["tuning_c"]) == {-0.5, 0.5}
    assert (d["fmt"] == "chat").eq(d["tuning_status"] == "finetuned").all()
    assert d["cluster_id"].str.startswith(f"{experiment}-").all()
    ngo_rows = (d["experiment"] == "ngo_verbatim") | (d["arm"] == "moral") & (d["experiment"] == "nonmoral")
    assert d.loc[ngo_rows, "ngo_pair_id"].notna().all() and d.loc[~ngo_rows, "ngo_pair_id"].isna().all()
    if experiment == "foundations":
        assert set(d["scaffold"]) == {"shared", "purpose"}
    rev = d["reversed"]
    assert (d.loc[rev, "rating"] == 10 - d.loc[rev, "parsed_rating_raw"]).all()
    rated = frame.analysis_rows(d)
    assert len(rated) == n_jobs and rated["rating"].between(0, 10).all()

    # Checks. The fake engine answers by hash, not by judgment, so its sign
    # contrasts are noise: validity can block the instruct key (and is a
    # pretrained finding), and the exit code follows gate_summary. Coverage and
    # number rates are fully determined by the pipeline and must never block.
    assert checks.number_rates(d)["passes"].all()
    tables = checks.run_checks(d, load_items(selected_path), KEYS)
    assert (tables["coverage"]["n_rows"] > 0).all()
    gate = checks.gate_summary(tables)
    out_dir = tmp_path / "checks"
    code = checks.main(["--results", str(out), "--items", str(selected_path), "--out-dir", str(out_dir)])
    assert code == (1 if gate["blocking"] else 0)
    assert not any(b.startswith(("coverage", "number_rate")) for b in gate["blocking"])
    prov = json.loads((out_dir / "provenance.json").read_text(encoding="utf-8"))
    assert prov["gate"] == gate and prov["experiments"] == [experiment]
    assert prov["n_rows"] == prov["n_rated_rows"] == n_jobs
    assert prov["manifest"]["model_keys"] == sorted(KEYS) and prov["manifest"]["engine"] == "fake"
    assert prov["n_dropped_unknown_items"] == 0
    assert {p.name for p in out_dir.iterdir()} == {f"{t}.csv" for t in tables} | {"provenance.json"}
