"""Pre-analysis gate (DESIGN.md section 8). Each function takes the
kmp.frame DataFrame and returns a small table; main() writes them, plus
provenance.json (the frame's dropped unknown items, the results file's run
manifest, and the gate summary).

main() exits 1 (gate_summary) if any model x question x wording cell falls
below the number-rate minimum (gate 1), or if a finetuned model fails an
applicable validity check or has no data for one, or is flagged for copying
the worked examples (gate 2). Section 8's "a finding, not a blocker" covers
pretrained models only: their validity and copying problems are reported as
findings and do not change the exit code. Validity checks are defined per
experiment (applicable_checks). Anchor agreement (gate 4) has no threshold
in DESIGN.md, so it is reported only. Gates 3 (example check) and 5
(throughput) live in Task 12, not here.

Number rates count parse_ok over every row (an unparsed answer is a miss).
Everything computed from ratings runs on frame.analysis_rows (NaN-free).
Per-model tables are keyed by model_key and carry tuning_status and family.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from kmp import protocol
from kmp.elicit import RUN_FIELDS, manifest_path
from kmp.frame import analysis_rows, load_frame
from kmp.items import load_items

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
    out = (frame["parse_ok"].astype(bool).groupby([frame["model_key"], frame["qkey"], frame["wording_key"]]).mean()
           .rename("number_rate").reset_index())
    out["passes"] = out["number_rate"] >= threshold
    return _with_model_cols(out, frame)


def _pearson(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) < 3 or a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def anchor_agreement(frame: pd.DataFrame) -> pd.DataFrame:
    """Per model x core question: item means under normal vs reversed anchors (after recoding)."""
    rated = analysis_rows(frame)
    core = rated[rated["qkey"].isin(protocol.CORE)]
    means = (core.groupby(["model_key", "qkey", "item_id", "reversed"])["rating"].mean()
             .unstack("reversed").reindex(columns=[False, True])
             .rename(columns={False: "normal", True: "reversed"}))
    rows = []
    for (model_key, qkey), d in means.dropna().groupby(level=["model_key", "qkey"]):
        normal, rev = d["normal"].to_numpy(), d["reversed"].to_numpy()
        rows.append(dict(model_key=model_key, qkey=qkey, n_items=len(d), r=_pearson(normal, rev),
                         mean_diff=float((rev - normal).mean())))
    out = pd.DataFrame(rows, columns=["model_key", "qkey", "n_items", "r", "mean_diff"])
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
    Every check gets a row; checks an experiment can't show are "not_applicable"
    (value NaN), never a silent pass."""
    for experiment in frame["experiment"].unique():   # unknown experiments raise even with no ratings
        applicable_checks(experiment)
    rows = []
    for (model_key, experiment), d in analysis_rows(frame).groupby(["model_key", "experiment"]):
        applicable = applicable_checks(experiment)
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
    """Share of written answers equal to a worked-example answer (before recoding).

    The written number is recovered from `rating` by undoing the 10 - x recode,
    so this reads analysis_rows' ratings, never parsed_rating_raw."""
    rated = analysis_rows(frame)
    written = rated["rating"].where(~rated["reversed"].astype(bool), 10 - rated["rating"])
    share = (written.isin(sorted(protocol.EXAMPLE_ANSWERS))
             .groupby(rated["model_key"]).mean().rename("share_example_values").reset_index())
    share["flag"] = share["share_example_values"] > protocol.COPY_SHARE_MAX
    return _with_model_cols(share, frame)


def provenance(frame: pd.DataFrame, results: Path, items: Path) -> dict:
    """What the tables were computed from: the frame's dropped rows and the
    results file's run manifest (<results>.manifest.json), if one exists."""
    mpath = manifest_path(results)
    if mpath.exists():
        full = json.loads(mpath.read_text(encoding="utf-8"))
        manifest = {k: full.get(k) for k in RUN_FIELDS}
    else:
        print(f"checks: WARNING no manifest at {mpath}; the run's release, runner_version, max_tokens, "
              f"engine and model_keys are unrecorded", file=sys.stderr)
        manifest = None
    return {
        "results": str(results), "items": str(items),
        "manifest_path": str(mpath), "manifest": manifest,
        "experiments": sorted(frame["experiment"].unique()),
        "n_rows": len(frame), "n_rated_rows": len(analysis_rows(frame)),
        "n_dropped_unknown_items": frame.attrs.get("n_dropped_unknown_items"),
        "dropped_unknown_item_ids": frame.attrs.get("dropped_unknown_item_ids"),
    }


def gate_summary(tables: dict[str, pd.DataFrame]) -> dict[str, list[str]]:
    """DESIGN.md section 8: what blocks analysis and what is only reported.
    Blocking: number-rate cells below the minimum (every model); validity
    fail/no_data and copying flags for finetuned models. Findings: the same
    validity and copying problems for pretrained models."""
    blocking: list[str] = []
    findings: list[str] = []
    nr = tables["number_rates"]
    for r in nr[~nr["passes"]].itertuples():
        blocking.append(f"number_rate: {r.model_key} {r.qkey} {r.wording_key} "
                        f"{r.number_rate:.2f} < {protocol.NUMBER_RATE_MIN:.2f}")
    for r in validity_problems(tables["validity"]).itertuples():
        (blocking if r.tuning_status == "finetuned" else findings).append(
            f"validity: {r.model_key} {r.experiment} {r.check} {r.status} (value {r.value:.2f})")
    ec = tables["example_copying"]
    for r in ec[ec["flag"]].itertuples():
        (blocking if r.tuning_status == "finetuned" else findings).append(
            f"example_copying: {r.model_key} share {r.share_example_values:.2f} > {protocol.COPY_SHARE_MAX:.2f}")
    return {"blocking": blocking, "findings": findings}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="knobe_moral_probe pre-analysis checks")
    p.add_argument("--results", required=True, type=Path)
    p.add_argument("--items", required=True, type=Path)
    p.add_argument("--out-dir", required=True, type=Path)
    args = p.parse_args(argv)

    frame = load_frame(args.results, load_items(args.items))
    args.out_dir.mkdir(parents=True, exist_ok=True)
    prov = provenance(frame, args.results, args.items)
    tables = {"number_rates": number_rates(frame), "anchor_agreement": anchor_agreement(frame),
              "validity": validity(frame), "example_copying": example_copying(frame)}
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
