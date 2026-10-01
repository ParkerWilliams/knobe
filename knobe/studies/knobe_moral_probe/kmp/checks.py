"""Pre-analysis gate (DESIGN.md section 8). Each function takes the
kmp.frame DataFrame and returns a small table; main() writes them, plus
provenance.json (inputs and their hashes, git state, thresholds, the
frame's dropped unknown items, the results file's run manifest, the
no-examples baseline and its manifest, and the gate summary).

--baseline is the same models run with kmp.elicit --no-examples (DESIGN.md
amendment 2026-10-01). Example copying and the example effect are measured
against it. main() exits 2 before writing anything if the baseline has no
manifest, its manifest isn't examples=false, or any other run field
(release, runner_version, max_tokens, engine, model_keys) or its prompt_id
set differs from the results' manifest (prompt hashes may differ: the
texts have no examples); also if --baseline is given and the results have
no manifest, or the results' own manifest says examples=false. Copying
shares are paired: over job_ids rated in both runs.

main() exits 1 (gate_summary) if anything blocks:
  - coverage: a model_key (from the manifest, else the models present) with
    no rows; a model in the results but not in the manifest's model_keys
    (a run must match its manifest); or an expected model x experiment x
    question x wording cell (items x protocol.subject_qkeys) with no rows.
    Coverage is cell-level, not item-level: a cell counts as covered if any
    item has a row in it, so an item missing from an otherwise covered cell
    is not caught here;
  - gate 1: a model x experiment x question x wording cell below the
    number-rate minimum;
  - gate 2, finetuned models: an applicable validity check that fails or
    has no data; example copying that fails (excess above
    protocol.COPY_EXCESS_MAX) or has no data (no --baseline, or no baseline
    rows for that model x experiment x question).
Section 8's "a finding, not a blocker" covers pretrained models only: their
validity and copying problems are reported as findings and do not change
the exit code. Anchor agreement (gate 4) has no threshold in DESIGN.md, so
it is reported only. Gate 3's example effect (example_effect: item-mean
ratings with vs without the worked examples) and gate 5's throughput (rows
per second per model) are reported only: DESIGN.md gives them no threshold.

Every table is split by experiment: experiments differ in items and arms,
so pooling them can hide one that parses or behaves badly. Validity is per
model x experiment, not per wording: its contrasts average over a
question's wordings (after recoding), since a sign or arm contrast needs
the whole item set and per-wording cells would be too small to read.
Example copying and the example effect are per model x experiment x
question.

provenance.json's git_dirty covers the whole repo, so untracked scratch
files count as dirty too; it errs on the safe side.

Number rates count parse_ok over every row (an unparsed answer is a miss).
Everything computed from ratings runs on frame.analysis_rows (NaN-free).
Per-model tables are keyed by model_key and carry tuning_status and family.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from kmp import protocol
from kmp.elicit import RUN_FIELDS, manifest_path, read_model_starts, run_field
from kmp.frame import analysis_rows, load_frame
from kmp.items import Item, load_items

MODEL_COLS = ["model_key", "tuning_status", "family"]


def _with_model_cols(table: pd.DataFrame, frame: pd.DataFrame) -> pd.DataFrame:
    """Add tuning_status and family (one value per model_key) after model_key."""
    meta = frame[MODEL_COLS].drop_duplicates()
    if meta["model_key"].duplicated().any():
        raise ValueError("a model_key has more than one tuning_status/family in the frame")
    out = table.merge(meta, on="model_key", how="left", validate="many_to_one")
    rest = [c for c in out.columns if c not in MODEL_COLS]
    return out[MODEL_COLS + rest]


def number_rates(frame: pd.DataFrame, threshold: float = protocol.NUMBER_RATE_MIN) -> pd.DataFrame:
    keys = [frame[c] for c in ("model_key", "experiment", "qkey", "wording_key")]
    out = frame["parse_ok"].astype(bool).groupby(keys).mean().rename("number_rate").reset_index()
    out["passes"] = out["number_rate"] >= threshold
    return _with_model_cols(out, frame)


def _pearson(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) < 3 or a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def anchor_agreement(frame: pd.DataFrame) -> pd.DataFrame:
    """Per model x experiment x core question: item means under normal vs
    reversed anchors (after recoding). Reported only (no DESIGN.md threshold).

    r is across items pooled over sign and arm, so it is driven largely by
    the sign effect itself and can be high even when the reversed wording
    shifts every answer; mean_diff (reversed - normal) is the more
    informative number for anchor bias."""
    rated = analysis_rows(frame)
    core = rated[rated["qkey"].isin(protocol.CORE)]
    keys = ["model_key", "experiment", "qkey"]
    means = (core.groupby([*keys, "item_id", "reversed"])["rating"].mean()
             .unstack("reversed").reindex(columns=[False, True])
             .rename(columns={False: "normal", True: "reversed"}))
    rows = []
    for (model_key, experiment, qkey), d in means.dropna().groupby(level=keys):
        normal, rev = d["normal"].to_numpy(), d["reversed"].to_numpy()
        rows.append(dict(model_key=model_key, experiment=experiment, qkey=qkey, n_items=len(d),
                         r=_pearson(normal, rev), mean_diff=float((rev - normal).mean())))
    out = pd.DataFrame(rows, columns=[*keys, "n_items", "r", "mean_diff"])
    return _with_model_cols(out, frame)


# Validity checks (DESIGN.md section 8, gate 2), each defined per experiment.
VALIDITY_CHECKS = ("blame_bad_minus_good", "praise_good_minus_bad", "significance_moral_minus_procedural")
# A check's status: "pass" (value > 0), "fail" (value <= 0), "no_data" (applicable
# but not computable from this frame, e.g. an arm missing), "not_applicable" (the
# experiment has no such contrast). Only "fail" and "no_data" are problems.
PASS, FAIL, NO_DATA, NOT_APPLICABLE = "pass", "fail", "no_data", "not_applicable"
PROBLEM_STATUSES = (FAIL, NO_DATA)


def applicable_checks(experiment: str) -> tuple[str, ...]:
    """Which validity checks an experiment's items can show. The significance
    check contrasts the moral and procedural arms, which only nonmoral has."""
    if experiment == "nonmoral":
        return VALIDITY_CHECKS
    if experiment in ("foundations", "ngo_verbatim"):
        return ("blame_bad_minus_good", "praise_good_minus_bad")
    raise protocol.unknown_experiment(experiment)


def _check_value(d: pd.DataFrame, check: str) -> float:
    def mean(qkey, **where):
        sel = d[d["qkey"] == qkey]
        for col, val in where.items():
            sel = sel[sel[col] == val]
        return sel["rating"].mean()
    if check == "blame_bad_minus_good":
        return mean("blame", sign="bad") - mean("blame", sign="good")
    if check == "praise_good_minus_bad":
        return mean("praise", sign="good") - mean("praise", sign="bad")
    if check == "significance_moral_minus_procedural":
        return mean("significance", arm="moral") - mean("significance", arm="procedural")
    raise ValueError(f"unknown validity check {check!r}")


def validity(frame: pd.DataFrame) -> pd.DataFrame:
    """Sanity directions any real judgment should show, per model x experiment.
    Every (model, experiment) pair in the full frame gets a row per check, so
    a pair with no ratings at all gets "no_data" for every applicable check.
    Checks an experiment can't show are "not_applicable" (value NaN), never a
    silent pass."""
    rated = analysis_rows(frame)
    by_pair = dict(tuple(rated.groupby(["model_key", "experiment"])))
    pairs = frame[["model_key", "experiment"]].drop_duplicates().sort_values(["model_key", "experiment"])
    rows = []
    for model_key, experiment in pairs.itertuples(index=False):
        applicable = applicable_checks(experiment)   # unknown experiments raise
        d = by_pair.get((model_key, experiment), rated.iloc[0:0])
        for check in VALIDITY_CHECKS:
            if check not in applicable:
                value, status = float("nan"), NOT_APPLICABLE
            else:
                value = _check_value(d, check)
                status = NO_DATA if pd.isna(value) else (PASS if value > 0 else FAIL)
            rows.append(dict(model_key=model_key, experiment=experiment, check=check, value=value, status=status))
    out = pd.DataFrame(rows, columns=["model_key", "experiment", "check", "value", "status"])
    return _with_model_cols(out, frame)


def validity_problems(table: pd.DataFrame) -> pd.DataFrame:
    """Rows of a validity() table that failed or could not be computed."""
    return table[table["status"].isin(PROBLEM_STATUSES)]


CELL_KEYS = ["model_key", "experiment", "qkey"]


def _example_hits(frame: pd.DataFrame) -> pd.DataFrame:
    """Per rated row (analysis_rows): job_id, the cell keys and hit = the
    written answer is a worked-example answer. The written number is
    recovered from `rating` by undoing the 10 - x recode, never from
    parsed_rating_raw."""
    rated = analysis_rows(frame)
    written = rated["rating"].where(~rated["reversed"].astype(bool), 10 - rated["rating"])
    return rated[["job_id", *CELL_KEYS]].assign(hit=written.isin(sorted(protocol.EXAMPLE_ANSWERS)).astype(float))


def example_copying(frame: pd.DataFrame, baseline: pd.DataFrame | None = None) -> pd.DataFrame:
    """Gate 2's copying check (DESIGN.md amendment 2026-10-01), per model x
    experiment x question: share_with (answers in EXAMPLE_ANSWERS, with the
    worked examples) minus share_without (the same share in the no-examples
    baseline run) = excess. 0 and 5 are natural answers, so the share alone
    over-flags; the no-examples run is the chance level.

    Paired: both shares are over the job_ids rated in BOTH runs (job IDs and
    seeds line up across the two runs), so parse failures that differ
    between runs can't shift one share and not the other. n_with / n_without
    are each run's rated rows in the cell, n_paired the rows both shares use.

    status: "fail" if excess > protocol.COPY_EXCESS_MAX, else "pass";
    "no_data" if n_paired is 0 (no baseline, no baseline rows for the cell,
    or no job rated in both). Every model x experiment x question in the full
    frame gets a row."""
    cells = frame[CELL_KEYS].drop_duplicates().sort_values(CELL_KEYS)
    with_hits = _example_hits(frame)
    without_hits = (_example_hits(baseline) if baseline is not None
                    else with_hits.iloc[0:0])
    paired = with_hits.merge(without_hits, on=["job_id", *CELL_KEYS], suffixes=("_with", "_without"))
    counts = [with_hits.groupby(CELL_KEYS).size().rename("n_with"),
              without_hits.groupby(CELL_KEYS).size().rename("n_without")]
    shares = paired.groupby(CELL_KEYS).agg(n_paired=("hit_with", "size"), share_with=("hit_with", "mean"),
                                           share_without=("hit_without", "mean"))
    out = cells.reset_index(drop=True)
    for table in (*counts, shares):
        out = out.merge(table.reset_index(), on=CELL_KEYS, how="left")
    for c in ("n_with", "n_without", "n_paired"):
        out[c] = out[c].fillna(0).astype(int)
    for c in ("share_with", "share_without"):
        out[c] = out[c].astype(float)
    out["excess"] = out["share_with"] - out["share_without"]
    out["status"] = [NO_DATA if n == 0 else (FAIL if x > protocol.COPY_EXCESS_MAX else PASS)
                     for n, x in zip(out["n_paired"], out["excess"])]
    cols = [*CELL_KEYS, "n_with", "n_without", "n_paired", "share_with", "share_without", "excess", "status"]
    return _with_model_cols(out[cols], frame)


def example_effect(with_examples: pd.DataFrame, without_examples: pd.DataFrame | None) -> pd.DataFrame:
    """Gate 3, per model x experiment x question: item-mean ratings (after
    recoding) with vs without the worked examples, over items rated in both.
    Format-only examples should leave these unchanged: r near 1, mean_diff
    (with - without) near 0. Reported only (no DESIGN.md threshold).
    No baseline (None) gives an empty table."""
    keys = CELL_KEYS
    if without_examples is None:
        without_examples = with_examples.iloc[0:0]

    def item_means(f: pd.DataFrame) -> pd.Series:
        return analysis_rows(f).groupby([*keys, "item_id"])["rating"].mean()
    both = pd.concat({"with": item_means(with_examples), "without": item_means(without_examples)},
                     axis=1).dropna()
    rows = []
    for (model_key, experiment, qkey), d in both.groupby(level=keys):
        a, b = d["with"].to_numpy(), d["without"].to_numpy()
        rows.append(dict(model_key=model_key, experiment=experiment, qkey=qkey, n_items=len(d),
                         r=_pearson(a, b), mean_diff=float((a - b).mean())))
    out = pd.DataFrame(rows, columns=[*keys, "n_items", "r", "mean_diff"])
    return _with_model_cols(out, with_examples)


def throughput(frame: pd.DataFrame, starts: dict[str, float] | None = None) -> pd.DataFrame:
    """Gate 5, per model: rows per second, to confirm the cost estimate
    (CLAUDE.md section 4). Wall-clock: seconds runs from the model's earliest
    recorded start (kmp.elicit.read_model_starts, taken just before its first
    batch) to its last row's timestamp, so pauses between resumed
    invocations count as run time, and rows from every invocation count.

    Without a recorded start (start_recorded False), seconds runs from the
    first row's timestamp, which lands after the first batch, so the rate is
    biased upward by about one batch; a zero span then gives NaN."""
    starts = starts or {}
    g = frame.groupby("model_key")["timestamp"].agg(["min", "max", "size"]).reset_index()
    recorded = g["model_key"].isin(list(starts))
    begin = g["model_key"].map(starts).where(recorded, g["min"]).astype(float)
    seconds = g["max"] - begin
    rate = (g["size"] / seconds).where(seconds > 0)
    out = pd.DataFrame({"model_key": g["model_key"], "rows": g["size"], "seconds": seconds,
                        "rows_per_second": rate, "start_recorded": recorded})
    return _with_model_cols(out, frame)


def expected_cells(items: list[Item]) -> set[tuple[str, str, str]]:
    """(experiment, qkey, wording_key) cells the items should produce for every model."""
    return {(item.experiment, qkey, w.key)
            for item in items for qkey in protocol.subject_qkeys(item) for w in protocol.QUESTIONS[qkey]}


def coverage(frame: pd.DataFrame, items: list[Item], model_keys: list[str]) -> pd.DataFrame:
    """Rows per model x expected experiment x qkey x wording cell (n_rows 0 =
    missing). Models are model_keys plus any model in the frame;
    expected_model is False for the latter (not in the manifest)."""
    cols = ["model_key", "experiment", "qkey", "wording_key"]
    cells = pd.DataFrame(sorted(expected_cells(items)), columns=cols[1:])
    expected = set(model_keys)
    all_models = sorted(expected | set(frame["model_key"]))
    models = pd.DataFrame({"model_key": all_models, "expected_model": [m in expected for m in all_models]})
    grid = (models.merge(cells, how="cross") if len(cells)
            else pd.DataFrame({c: pd.Series(dtype=object) for c in ["model_key", "expected_model", *cols[1:]]}))
    counts = frame.groupby(cols).size().rename("n_rows").reset_index()
    out = grid.merge(counts, on=cols, how="left")
    out["n_rows"] = out["n_rows"].fillna(0).astype(int)
    return out[[*cols, "expected_model", "n_rows"]]


def _full_manifest(results: Path) -> dict | None:
    mpath = manifest_path(results)
    return json.loads(mpath.read_text(encoding="utf-8")) if mpath.exists() else None


def baseline_manifest_problems(results_manifest: dict | None, baseline_manifest: dict | None,
                               limit: int = 5) -> list[str]:
    """Why a --baseline run can't be compared with the results. Takes the
    full manifests (run fields and prompts). Empty = fine. Prompt hashes are
    expected to differ (no examples in the text); the prompt_id sets must not."""
    if results_manifest is None:
        return ["--baseline needs the results' run manifest to compare against, and it has none"]
    if baseline_manifest is None:
        return ["the baseline has no run manifest, so it can't be shown to be a no-examples run of the same models"]
    problems = []
    if run_field(baseline_manifest, "examples") is not False:
        problems.append(f"examples: the baseline manifest has {run_field(baseline_manifest, 'examples')!r}, "
                        f"expected False (a kmp.elicit --no-examples run)")
    problems += [f"{k}: the results' manifest has {run_field(results_manifest, k)!r}, the baseline's has "
                 f"{run_field(baseline_manifest, k)!r}" for k in RUN_FIELDS
                 if k != "examples" and run_field(results_manifest, k) != run_field(baseline_manifest, k)]
    ours, theirs = set(results_manifest.get("prompts", {})), set(baseline_manifest.get("prompts", {}))
    if ours != theirs:
        diff = sorted(ours ^ theirs)
        shown = ", ".join(diff[:limit]) + (f" (+{len(diff) - limit} more)" if len(diff) > limit else "")
        problems.append(f"prompt_id sets differ ({len(ours - theirs)} only in the results, "
                        f"{len(theirs - ours)} only in the baseline): {shown}")
    return problems


def read_manifest(results: Path) -> dict | None:
    """The run fields of <results>.manifest.json, or None (with a warning) if absent."""
    full = _full_manifest(results)
    if full is None:
        print(f"checks: WARNING no manifest at {manifest_path(results)}; the run's release, runner_version, "
              f"max_tokens, engine and model_keys are unrecorded, and coverage uses the model_keys present",
              file=sys.stderr)
        return None
    return {k: run_field(full, k) for k in RUN_FIELDS}


def _load_baseline(baseline: Path, results: Path, items: list[Item]
                   ) -> tuple[pd.DataFrame | None, dict | None, list[str]]:
    """Validate --baseline against the results' manifest, then load its frame.
    Returns (frame, run fields of its manifest, problems); the frame is None
    when there are problems."""
    full = _full_manifest(baseline)
    fields = {k: run_field(full, k) for k in RUN_FIELDS} if full is not None else None
    problems = [f"baseline {baseline}: {m}" for m in baseline_manifest_problems(_full_manifest(results), full)]
    if problems:
        return None, fields, problems
    return load_frame(baseline, items), fields, []


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _git(*args: str) -> str | None:
    try:
        return subprocess.run(["git", *args], cwd=Path(__file__).resolve().parent, capture_output=True,
                              text=True, check=True, timeout=30).stdout
    except (OSError, subprocess.SubprocessError):
        return None


def provenance(frame: pd.DataFrame, results: Path, items: Path, manifest: dict | None,
               argv: list[str], baseline: Path | None = None, baseline_manifest: dict | None = None,
               baseline_frame: pd.DataFrame | None = None, model_starts: dict | None = None) -> dict:
    """What the tables were computed from: inputs and hashes, code state,
    thresholds, the frame's dropped rows, the run manifest (None if absent),
    the no-examples baseline with its manifest and dropped rows (None without
    --baseline) and the per-model start times throughput used."""
    commit = _git("rev-parse", "HEAD")
    status = _git("status", "--porcelain")   # whole repo, untracked files included
    mpath = manifest_path(results).resolve()
    bpath = manifest_path(baseline).resolve() if baseline is not None else None
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "argv": list(argv), "cwd": str(Path.cwd().resolve()),
        "git_commit": commit.strip() if commit else None,
        "git_dirty": bool(status.strip()) if status is not None else None,
        "results": str(Path(results).resolve()), "results_sha256": _sha256(results),
        "items": str(Path(items).resolve()), "items_sha256": _sha256(items),
        "number_rate_min": protocol.NUMBER_RATE_MIN, "copy_excess_max": protocol.COPY_EXCESS_MAX,
        "example_answers": sorted(protocol.EXAMPLE_ANSWERS),
        "manifest_path": str(mpath), "manifest": manifest,
        "fake_engine": (manifest.get("engine") == "fake") if manifest is not None else None,
        "manifest_sha256": _sha256(mpath) if mpath.exists() else None,
        "baseline": str(Path(baseline).resolve()) if baseline is not None else None,
        "baseline_sha256": _sha256(baseline) if baseline is not None else None,
        "baseline_manifest_path": str(bpath) if bpath is not None else None,
        "baseline_manifest": baseline_manifest,
        "baseline_manifest_sha256": _sha256(bpath) if bpath is not None and bpath.exists() else None,
        "baseline_n_dropped_unknown_items": (baseline_frame.attrs.get("n_dropped_unknown_items")
                                             if baseline_frame is not None else None),
        "baseline_dropped_unknown_item_ids": (baseline_frame.attrs.get("dropped_unknown_item_ids")
                                              if baseline_frame is not None else None),
        "model_starts": model_starts,
        "experiments": sorted(frame["experiment"].unique()),
        "n_rows": len(frame), "n_rated_rows": len(analysis_rows(frame)),
        "n_dropped_unknown_items": frame.attrs.get("n_dropped_unknown_items"),
        "dropped_unknown_item_ids": frame.attrs.get("dropped_unknown_item_ids"),
    }


def run_checks(frame: pd.DataFrame, items: list[Item], model_keys: list[str],
               baseline: pd.DataFrame | None = None,
               model_starts: dict[str, float] | None = None) -> dict[str, pd.DataFrame]:
    """baseline: the kmp.frame of the no-examples run, or None (copying is then no_data).
    model_starts: kmp.elicit.read_model_starts of the results, for throughput."""
    return {"coverage": coverage(frame, items, model_keys), "number_rates": number_rates(frame),
            "anchor_agreement": anchor_agreement(frame), "validity": validity(frame),
            "example_copying": example_copying(frame, baseline), "example_effect": example_effect(frame, baseline),
            "throughput": throughput(frame, model_starts)}


def gate_summary(tables: dict[str, pd.DataFrame]) -> dict[str, list[str]]:
    """DESIGN.md section 8: what blocks analysis and what is only reported.
    Blocking: coverage gaps and number-rate cells below the minimum (every
    model); validity and example-copying fail/no_data for finetuned models.
    Findings: the same validity and copying problems for pretrained models."""
    blocking: list[str] = []
    findings: list[str] = []
    cov = tables["coverage"]
    unexpected = set(cov.loc[~cov["expected_model"].astype(bool), "model_key"])
    for model_key in sorted(unexpected):
        blocking.append(f"coverage: unexpected model {model_key} (in the results but not in the manifest's model_keys)")
    per_model = cov.groupby("model_key")["n_rows"].sum()
    absent = set(per_model[per_model == 0].index)
    for model_key in sorted(absent):
        blocking.append(f"coverage: {model_key} has no rows")
    skip = absent | unexpected
    for r in cov[(cov["n_rows"] == 0) & ~cov["model_key"].isin(skip)].itertuples():
        blocking.append(f"coverage: {r.model_key} {r.experiment} {r.qkey} {r.wording_key} has no rows")
    nr = tables["number_rates"]
    for r in nr[~nr["passes"]].itertuples():
        blocking.append(f"number_rate: {r.model_key} {r.experiment} {r.qkey} {r.wording_key} "
                        f"{r.number_rate:.2f} < {protocol.NUMBER_RATE_MIN:.2f}")
    for r in validity_problems(tables["validity"]).itertuples():
        detail = "" if r.status == NO_DATA else f" (value {r.value:.2f})"
        (blocking if r.tuning_status == "finetuned" else findings).append(
            f"validity: {r.model_key} {r.experiment} {r.check} {r.status}{detail}")
    ec = tables["example_copying"]
    for r in ec[ec["status"].isin(PROBLEM_STATUSES)].itertuples():
        detail = ("no_data (no no-examples baseline rows)" if r.status == NO_DATA else
                  f"excess {r.excess:.2f} > {protocol.COPY_EXCESS_MAX:.2f} "
                  f"(with {r.share_with:.2f}, without {r.share_without:.2f})")
        (blocking if r.tuning_status == "finetuned" else findings).append(
            f"example_copying: {r.model_key} {r.experiment} {r.qkey} {detail}")
    return {"blocking": blocking, "findings": findings}


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    p = argparse.ArgumentParser(description="knobe_moral_probe pre-analysis checks")
    p.add_argument("--results", required=True, type=Path)
    p.add_argument("--items", required=True, type=Path)
    p.add_argument("--out-dir", required=True, type=Path)
    p.add_argument("--baseline", type=Path,
                   help="results JSONL of the same models run with kmp.elicit --no-examples; example copying "
                        "is measured against it (without it, copying is no_data and blocks finetuned models)")
    args = p.parse_args(argv)

    items = load_items(args.items)
    frame = load_frame(args.results, items)
    manifest = read_manifest(args.results)
    if manifest is not None and manifest.get("engine") == "fake":
        print("checks: " + "!" * 70 + f"\nchecks: WARNING: these results come from the FAKE engine "
              f"(manifest engine='fake'), not a model.\nchecks: The tables are for testing the pipeline "
              f"only; recorded as fake_engine=true in provenance.json.\nchecks: " + "!" * 70, file=sys.stderr)
    problems = []
    if manifest is not None and manifest.get("examples") is False:
        problems.append(f"{args.results} is a no-examples run (its manifest has examples=false); "
                        f"pass it as --baseline, not --results")
    baseline = baseline_manifest = None
    if args.baseline is not None:
        baseline, baseline_manifest, baseline_problems = _load_baseline(args.baseline, args.results, items)
        problems += baseline_problems
    if problems:
        print("checks: refusing to run:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    model_keys = manifest["model_keys"] if manifest and manifest.get("model_keys") else sorted(frame["model_key"].unique())
    starts = read_model_starts(args.results)
    prov = provenance(frame, args.results, args.items, manifest, argv, args.baseline, baseline_manifest,
                      baseline, starts)
    tables = run_checks(frame, items, model_keys, baseline, starts)
    for name, table in tables.items():
        table.to_csv(args.out_dir / f"{name}.csv", index=False)
        print(f"\n== {name}\n{table.to_string(index=False)}")
    prov["gate"] = gate = gate_summary(tables)
    (args.out_dir / "provenance.json").write_text(json.dumps(prov, indent=2) + "\n", encoding="utf-8")
    print(f"\n== provenance\n{json.dumps(prov, indent=2)}")

    lines = ["\n== gate summary (DESIGN.md section 8)"]
    lines.append(f"BLOCKING ({len(gate['blocking'])}):" if gate["blocking"] else "blocking: none")
    lines += [f"  {b}" for b in gate["blocking"]]
    lines.append(f"non-blocking findings, pretrained models ({len(gate['findings'])}):" if gate["findings"]
                 else "non-blocking findings: none")
    lines += [f"  {f}" for f in gate["findings"]]
    if any(b.startswith("number_rate") for b in gate["blocking"]):
        lines.append(f"cell(s) below the {protocol.NUMBER_RATE_MIN:.0%} number-rate minimum")
    print("\n".join(lines), file=sys.stderr)
    return 1 if gate["blocking"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
