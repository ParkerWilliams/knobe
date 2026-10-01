"""Pre-analysis gate (DESIGN.md section 8). Each function takes the
kmp.frame DataFrame and returns a small table; main() writes them, plus
provenance.json (inputs and their hashes, git state, thresholds, the
frame's dropped unknown items, the results file's run manifest, and the
gate summary).

main() exits 1 (gate_summary) if anything blocks:
  - coverage: a model_key (from the manifest, else the models present) with
    no rows, or an expected model x experiment x question x wording cell
    (items x protocol.subject_qkeys) with no rows;
  - gate 1: a model x experiment x question x wording cell below the
    number-rate minimum;
  - gate 2, finetuned models: an applicable validity check that fails or
    has no data, or an example-copying flag.
Section 8's "a finding, not a blocker" covers pretrained models only: their
validity and copying problems are reported as findings and do not change
the exit code. Anchor agreement (gate 4) has no threshold in DESIGN.md, so
it is reported only. Gates 3 (example check) and 5 (throughput) live in
Task 12, not here.

Every table is split by experiment: experiments differ in items and arms,
so pooling them can hide one that parses or behaves badly. Validity is per
model x experiment, not per wording: its contrasts average over a
question's wordings (after recoding), since a sign or arm contrast needs
the whole item set and per-wording cells would be too small to read.
Example copying is per model x experiment x question.

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
from kmp.elicit import RUN_FIELDS, manifest_path
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


def example_copying(frame: pd.DataFrame) -> pd.DataFrame:
    """Share of written answers equal to a worked-example answer (before
    recoding), per model x experiment x question, flagged above COPY_SHARE_MAX.

    The written number is recovered from `rating` by undoing the 10 - x recode,
    so this reads analysis_rows' ratings, never parsed_rating_raw.

    Caveat, pending the researcher's decision on threshold/baseline: 0 and 5
    are also natural answers (a clear "not at all", a scale midpoint), so a
    high share can reflect genuine judgments rather than copying, and the
    share can overstate copying."""
    rated = analysis_rows(frame)
    written = rated["rating"].where(~rated["reversed"].astype(bool), 10 - rated["rating"])
    keys = [rated[c] for c in ("model_key", "experiment", "qkey")]
    share = (written.isin(sorted(protocol.EXAMPLE_ANSWERS))
             .groupby(keys).mean().rename("share_example_values").reset_index())
    share["flag"] = share["share_example_values"] > protocol.COPY_SHARE_MAX
    return _with_model_cols(share, frame)


def expected_cells(items: list[Item]) -> set[tuple[str, str, str]]:
    """(experiment, qkey, wording_key) cells the items should produce for every model."""
    return {(item.experiment, qkey, w.key)
            for item in items for qkey in protocol.subject_qkeys(item) for w in protocol.QUESTIONS[qkey]}


def coverage(frame: pd.DataFrame, items: list[Item], model_keys: list[str]) -> pd.DataFrame:
    """Rows per expected model x experiment x qkey x wording cell (n_rows 0 = missing)."""
    cols = ["model_key", "experiment", "qkey", "wording_key"]
    cells = pd.DataFrame(sorted(expected_cells(items)), columns=cols[1:])
    models = pd.DataFrame({"model_key": sorted(set(model_keys))})
    grid = models.merge(cells, how="cross") if len(cells) else pd.DataFrame(columns=cols)
    counts = frame.groupby(cols).size().rename("n_rows").reset_index()
    out = grid.merge(counts, on=cols, how="left")
    out["n_rows"] = out["n_rows"].fillna(0).astype(int)
    return out[[*cols, "n_rows"]]


def read_manifest(results: Path) -> dict | None:
    """The run fields of <results>.manifest.json, or None (with a warning) if absent."""
    mpath = manifest_path(results)
    if not mpath.exists():
        print(f"checks: WARNING no manifest at {mpath}; the run's release, runner_version, max_tokens, "
              f"engine and model_keys are unrecorded, and coverage uses the model_keys present", file=sys.stderr)
        return None
    full = json.loads(mpath.read_text(encoding="utf-8"))
    return {k: full.get(k) for k in RUN_FIELDS}


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
               argv: list[str]) -> dict:
    """What the tables were computed from: inputs and hashes, code state,
    thresholds, the frame's dropped rows and the run manifest (None if absent)."""
    commit = _git("rev-parse", "HEAD")
    status = _git("status", "--porcelain")
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "argv": list(argv),
        "git_commit": commit.strip() if commit else None,
        "git_dirty": bool(status.strip()) if status is not None else None,
        "results": str(results), "results_sha256": _sha256(results),
        "items": str(items), "items_sha256": _sha256(items),
        "number_rate_min": protocol.NUMBER_RATE_MIN, "copy_share_max": protocol.COPY_SHARE_MAX,
        "manifest_path": str(manifest_path(results)), "manifest": manifest,
        "experiments": sorted(frame["experiment"].unique()),
        "n_rows": len(frame), "n_rated_rows": len(analysis_rows(frame)),
        "n_dropped_unknown_items": frame.attrs.get("n_dropped_unknown_items"),
        "dropped_unknown_item_ids": frame.attrs.get("dropped_unknown_item_ids"),
    }


def run_checks(frame: pd.DataFrame, items: list[Item], model_keys: list[str]) -> dict[str, pd.DataFrame]:
    return {"coverage": coverage(frame, items, model_keys), "number_rates": number_rates(frame),
            "anchor_agreement": anchor_agreement(frame), "validity": validity(frame),
            "example_copying": example_copying(frame)}


def gate_summary(tables: dict[str, pd.DataFrame]) -> dict[str, list[str]]:
    """DESIGN.md section 8: what blocks analysis and what is only reported.
    Blocking: coverage gaps and number-rate cells below the minimum (every
    model); validity fail/no_data and copying flags for finetuned models.
    Findings: the same validity and copying problems for pretrained models."""
    blocking: list[str] = []
    findings: list[str] = []
    cov = tables["coverage"]
    per_model = cov.groupby("model_key")["n_rows"].sum()
    absent = set(per_model[per_model == 0].index)
    for model_key in sorted(absent):
        blocking.append(f"coverage: {model_key} has no rows")
    for r in cov[(cov["n_rows"] == 0) & ~cov["model_key"].isin(absent)].itertuples():
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
    for r in ec[ec["flag"]].itertuples():
        (blocking if r.tuning_status == "finetuned" else findings).append(
            f"example_copying: {r.model_key} {r.experiment} {r.qkey} share {r.share_example_values:.2f} "
            f"> {protocol.COPY_SHARE_MAX:.2f}")
    return {"blocking": blocking, "findings": findings}


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    p = argparse.ArgumentParser(description="knobe_moral_probe pre-analysis checks")
    p.add_argument("--results", required=True, type=Path)
    p.add_argument("--items", required=True, type=Path)
    p.add_argument("--out-dir", required=True, type=Path)
    args = p.parse_args(argv)

    items = load_items(args.items)
    frame = load_frame(args.results, items)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    manifest = read_manifest(args.results)
    model_keys = manifest["model_keys"] if manifest and manifest.get("model_keys") else sorted(frame["model_key"].unique())
    prov = provenance(frame, args.results, args.items, manifest, argv)
    tables = run_checks(frame, items, model_keys)
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
