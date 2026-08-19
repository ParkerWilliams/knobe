"""Curation-only manipulation check for the moral-foundations pilot
(`build_dataset.py`'s outputs/mf_pilot_dataset.csv, 152 items across
harm_control / loyalty / authority / fairness / purity).

Two curation questions per the design doc
(`docs/moral_foundations_extension/MORAL_FOUNDATIONS_PILOT_PLAN.md`
section 5), kept lean rather than a full cross-check of every item against
all five conditions:

1. **harm_relevance** -- asked of EVERY item, every condition.
2. **foundation relevance** -- asked once per non-harm item, matching its
   intended condition (loyalty/authority/fairness/purity), all four with
   the same "Setting aside any harm to someone's welfare" bracketing
   clause. Harm-control items get no second question: harm IS their
   target, so harm_relevance covers both roles for them.

The question strings below are verbatim from the design doc section 5.
They are pilot-specific instruments, not additions to
``knobe.constants.CURATION_QUESTIONS`` -- constants.py is a frozen
instrument that can't grow new entries without a human-approved version
bump, and these questions are only used here.

Reuses the project's own curation call machinery
(`knobe.curate.AnthropicClient`/`MockClient`, `_complete_with_retry`,
`knobe.parsing.parse_rating`, `constants.CURATION_PROMPT_TEMPLATE`) rather
than reimplementing API-calling/retry/parsing -- NOT `curate.run()`'s full
orchestration, for the same reason the sibling
`../nonmoral_pilot/curate_moral_relevance.py` gives: that expects a
`Family` registry and the production `CuratedRow` schema this pilot
doesn't have.

Pass/fail thresholds start from `configs/curation.yaml`'s existing
``moral_min``/``nonmoral_max`` values rather than inventing new numbers
(design doc section 5: adjust only if real curation data shows they don't
discriminate for the new questions):
  - harm_control item passes iff  harm_relevance >= moral_min
  - foundation item passes iff    foundation_relevance >= moral_min
                                  AND harm_relevance <= nonmoral_max

**NOT YET RUN.** This environment has no ANTHROPIC_API_KEY -- same handoff
pattern as the sibling pilot.

Usage:
    # 1. Verify it imports/runs clean with zero API access:
    .venv/bin/python analysis/ngo_extensions/moral_foundations_pilot/curate_foundation_relevance.py --mock

    # 2. Real run, once handed to someone with API access
    #    (~244 calls: 152 harm_relevance + 92 foundation relevance):
    .venv/bin/python analysis/ngo_extensions/moral_foundations_pilot/curate_foundation_relevance.py \
        --reviewer-model claude-sonnet-5

    # 3. Check pass/fail against the thresholds (just prints):
    .venv/bin/python analysis/ngo_extensions/moral_foundations_pilot/curate_foundation_relevance.py --check

    # 4. Build the filtered dataset elicit.py actually reads:
    .venv/bin/python analysis/ngo_extensions/moral_foundations_pilot/curate_foundation_relevance.py --select

Writes outputs/foundation_relevance_raw.jsonl (checkpoint/resume: each line
is one (variant_id, question_key) rating; already-completed pairs are
skipped on rerun). ``--select`` writes outputs/mf_pilot_dataset_selected.csv
(what elicit.py reads) and outputs/selection_report.md. Selection is
per-item, matching the sibling pilot's corrected rule: every item that
independently clears its own thresholds is kept -- a storyline may
contribute any subset of its conditions. The report (not a blocking gate)
flags the two failure modes worth reading before or after elicitation:
harm-controls that don't read as harm through this project's reviewer
pipeline, and foundation items rejected for harm contamination (high
harm_relevance) as opposed to a weak foundation signal -- the design doc's
known-gap discussion (section 5) predicts contamination, not weakness, is
the likelier problem.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

REPO_SRC = Path(__file__).resolve().parents[3] / "src"
sys.path.insert(0, str(REPO_SRC))

from knobe import constants  # noqa: E402
from knobe.curate import AnthropicClient, MockClient, TransientCallError, _complete_with_retry  # noqa: E402
from knobe.parsing import parse_rating  # noqa: E402

import pandas as pd  # noqa: E402
import yaml  # noqa: E402

HERE = Path(__file__).parent
DATASET_PATH = HERE / "outputs" / "mf_pilot_dataset.csv"
OUT_PATH = HERE / "outputs" / "foundation_relevance_raw.jsonl"
SELECTED_PATH = HERE / "outputs" / "mf_pilot_dataset_selected.csv"
REPORT_PATH = HERE / "outputs" / "selection_report.md"
CURATION_CONFIG_PATH = REPO_SRC.parent / "configs" / "curation.yaml"

# Verbatim from MORAL_FOUNDATIONS_PILOT_PLAN.md section 5.
HARM_RELEVANCE_QUESTION = (
    "To what extent does this outcome involve harm or damage to someone's welfare — health, "
    "safety, finances, or material well-being? (0 = not at all, 10 = entirely about harm to welfare)"
)
FOUNDATION_QUESTIONS = {
    "loyalty": (
        "Setting aside any harm to someone's welfare, to what extent does this outcome involve "
        "loyalty to, or betrayal of, one's group, team, family, or ally? (0-10)"
    ),
    "authority": (
        "Setting aside any harm to someone's welfare, to what extent does this outcome involve "
        "respecting or undermining a legitimate authority, rule, or hierarchy? (0-10)"
    ),
    "purity": (
        "Setting aside any harm to someone's welfare, to what extent does this outcome involve "
        "a taboo, disgust, or violation of purity/sanctity? (0-10)"
    ),
    "fairness": (
        "Setting aside any harm to someone's welfare, to what extent does this outcome involve "
        "unequal or unjust treatment? (0-10)"
    ),
}


def build_jobs(df: pd.DataFrame) -> dict[tuple[str, str], str]:
    """{(variant_id, question_key): question_text} -- harm_relevance for
    every item, plus the matching foundation question for non-harm items."""
    jobs: dict[tuple[str, str], str] = {}
    for _, row in df.iterrows():
        jobs[(row["variant_id"], "harm_relevance")] = HARM_RELEVANCE_QUESTION
        if row["condition"] != "harm_control":
            jobs[(row["variant_id"], row["condition"])] = FOUNDATION_QUESTIONS[row["condition"]]
    return jobs


def _read_completed(path: Path) -> set[tuple[str, str]]:
    if not path.exists():
        return set()
    completed = set()
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rec = json.loads(line)
                completed.add((rec["variant_id"], rec["question_key"]))
    return completed


async def run_curation(client, concurrency: int, max_retries: int, max_tokens: int) -> None:
    df = pd.read_csv(DATASET_PATH)
    scenario_by_vid = dict(zip(df["variant_id"], df["scenario"]))
    jobs = build_jobs(df)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    completed = _read_completed(OUT_PATH)
    remaining = [key for key in jobs if key not in completed]
    print(f"{len(completed)} already done, {len(remaining)} remaining of {len(jobs)} total")

    sem = asyncio.Semaphore(concurrency)
    n_errors = 0

    with open(OUT_PATH, "a", encoding="utf-8") as fh:

        async def _do_one(vid: str, qkey: str) -> None:
            nonlocal n_errors
            async with sem:
                prompt = constants.CURATION_PROMPT_TEMPLATE.format(
                    scenario=scenario_by_vid[vid], question=jobs[(vid, qkey)],
                )
                try:
                    text, retries = await _complete_with_retry(client, prompt, max_tokens, max_retries)
                except (TransientCallError, Exception) as exc:
                    n_errors += 1
                    print(f"ERROR on {vid}::{qkey}: {exc}", file=sys.stderr)
                    return
                value, ok, raw = parse_rating(text)
                fh.write(json.dumps(dict(
                    variant_id=vid, question_key=qkey, rating=value, parse_ok=ok, raw=raw,
                    timestamp=time.time(),
                )) + "\n")
                fh.flush()

        await asyncio.gather(*(_do_one(vid, qkey) for vid, qkey in remaining))

    print(f"done, {n_errors} errors (rerun this script to retry them -- unfinished jobs aren't written)")


def _load_curated_and_thresholds() -> tuple[pd.DataFrame, float, float]:
    if not OUT_PATH.exists():
        print(f"{OUT_PATH} doesn't exist yet -- run curation first.", file=sys.stderr)
        sys.exit(1)

    cfg = yaml.safe_load(CURATION_CONFIG_PATH.read_text())
    moral_min, nonmoral_max = cfg["moral_min"], cfg["nonmoral_max"]

    raw = pd.read_json(OUT_PATH, lines=True)
    n_unparsed = (~raw["parse_ok"]).sum()
    if n_unparsed:
        print(f"WARNING: {n_unparsed} unparsed curation responses excluded")
    raw = raw[raw["parse_ok"]]

    wide = raw.pivot_table(index="variant_id", columns="question_key", values="rating",
                           aggfunc="first").reset_index()
    df = pd.read_csv(DATASET_PATH).merge(wide, on="variant_id", how="left")

    def _foundation_relevance(row):
        return row.get(row["condition"]) if row["condition"] != "harm_control" else None

    df["foundation_relevance"] = df.apply(_foundation_relevance, axis=1)

    def _passes(row) -> bool:
        if pd.isna(row.get("harm_relevance")):
            return False  # unparsed/missing harm rating -> can't clear either rule
        if row["condition"] == "harm_control":
            return row["harm_relevance"] >= moral_min
        if pd.isna(row["foundation_relevance"]):
            return False
        return (row["foundation_relevance"] >= moral_min) and (row["harm_relevance"] <= nonmoral_max)

    df["passed"] = df.apply(_passes, axis=1)
    return df, moral_min, nonmoral_max


def check_manipulation() -> None:
    """Prints per-condition pass/fail against the thresholds. Use --select
    to actually build the filtered dataset elicit.py reads."""
    df, moral_min, nonmoral_max = _load_curated_and_thresholds()

    print(f"moral_min={moral_min}, nonmoral_max={nonmoral_max} (configs/curation.yaml)\n")
    for condition in df["condition"].unique():
        sub = df[df["condition"] == condition]
        line = (f"{condition}: {sub['passed'].sum()}/{len(sub)} pass "
                f"(mean harm_relevance={sub['harm_relevance'].mean():.2f}")
        if condition != "harm_control":
            line += f", mean foundation_relevance={sub['foundation_relevance'].mean():.2f}"
        print(line + ")")
        failing = sub[~sub["passed"]]
        if len(failing):
            print(f"  failing variant_ids: {failing['variant_id'].tolist()}")


def select_items() -> None:
    """Builds outputs/mf_pilot_dataset_selected.csv and
    outputs/selection_report.md. Not a blocking gate -- see module
    docstring.

    **Selection is PAIR-level, keyed on the bad member** -- a data-driven
    revision (2026-08-19) of the design doc's per-item rule, made after the
    first real curation run showed the section-5 questions are
    sign-asymmetric by construction: they name the violation pole ("harm or
    damage", "unequal or unjust", "taboo...violation"), so GOOD-sign items
    score near zero on them no matter how well-authored (observed means:
    harm-control bad 9.2 vs good 0.7; fairness-good 1.1 on its own
    foundation question). Per-item gating would therefore delete the good
    arm entirely and with it the bad>good contrast the pilot exists to
    test. Rule now: a (condition, pair_id) pair is selected iff its BAD
    member passes the design-doc thresholds (the bad side is where the
    category manipulation is measurable -- and gating on it is still
    strictly more curation than Ngo/Raimondi's original materials had,
    which is none) AND, for foundation conditions, its GOOD member parsed
    and is not harm-contaminated (harm_relevance <= nonmoral_max).
    Good-sign harm-controls are carried by their bad member alone: no
    question in the section-5 instrument can measure "welfare benefit
    relevance". All ratings survive into the selected CSV, so analysis can
    re-gate differently without re-running curation. Flagged for
    collaborator review in the selection report, the pilot README, and
    results/ANALYSIS_LOG.md."""
    df, moral_min, nonmoral_max = _load_curated_and_thresholds()

    def _pair_selected(sub: pd.DataFrame) -> bool:
        by_sign = {r["sign"]: r for _, r in sub.iterrows()}
        bad, good = by_sign.get("bad"), by_sign.get("good")
        if bad is None or good is None or not bad["passed"]:
            return False
        if bad["condition"] != "harm_control":
            if pd.isna(good.get("harm_relevance")) or good["harm_relevance"] > nonmoral_max:
                return False
        return True

    pair_ok = {
        key: _pair_selected(sub)
        for key, sub in df.groupby(["condition", "pair_id"])
    }
    df["pair_selected"] = [pair_ok[(c, p)] for c, p in zip(df["condition"], df["pair_id"])]
    selected = df[df["pair_selected"]].drop(columns=["passed", "pair_selected"])
    selected.to_csv(SELECTED_PATH, index=False)

    nonharm = df[df["condition"] != "harm_control"]
    lines = [
        "# Moral-foundations pilot: post-curation selection report",
        "",
        f"moral_min={moral_min}, nonmoral_max={nonmoral_max} (configs/curation.yaml). "
        f"{len(selected)}/{len(df)} items selected -> `{SELECTED_PATH.name}`.",
        "",
        "**Selection rule: PAIR-level, keyed on the bad member** (see "
        "`select_items`'s docstring for the full rationale -- the design doc's "
        "per-item rule was revised 2026-08-19 after real curation data showed the "
        "section-5 questions only measure the violation pole, which would have "
        "deleted the good arm; flagged for collaborator review). Per-item "
        "diagnostics below are unchanged and still worth reading.",
        "",
    ]

    failing_harm = df[(df["condition"] == "harm_control") & (~df["passed"])]
    if len(failing_harm):
        lines += [
            f"**{len(failing_harm)} harm-control item(s) failed to read as harm** through this "
            f"project's reviewer pipeline (freshly-templated wording, so not guaranteed by Ngo's "
            f"originals): {failing_harm['variant_id'].tolist()}",
            "",
        ]

    contaminated = nonharm[(nonharm["harm_relevance"] > nonmoral_max)]
    weak = nonharm[(nonharm["harm_relevance"] <= nonmoral_max)
                   & (nonharm["foundation_relevance"] < moral_min)]
    lines += [
        f"Foundation-item failures by reason (design doc section 5 predicts harm contamination "
        f"is the likelier failure mode than a weak foundation signal):",
        "",
        f"- **harm contamination** (harm_relevance > {nonmoral_max}): {len(contaminated)} "
        f"item(s) {contaminated['variant_id'].tolist()}",
        f"- **weak foundation signal** (foundation_relevance < {moral_min}, harm ok): "
        f"{len(weak)} item(s) {weak['variant_id'].tolist()}",
        "",
        "## Surviving cluster counts (what power_check.py projects from)",
        "",
        "| condition | items passing | distinct storylines (pair_ids) |",
        "|---|---|---|",
    ]
    for condition in ["harm_control", "loyalty", "authority", "fairness", "purity"]:
        sub = selected[selected["condition"] == condition]
        note = " *(smaller by design -- reported as tentative)*" if condition == "purity" else ""
        lines.append(f"| {condition} | {len(sub)} | {sub['pair_id'].nunique()}{note} |")
    pooled = selected[selected["condition"] != "harm_control"]
    lines.append(f"| non-harm pooled (primary contrast) | {len(pooled)} | {pooled['pair_id'].nunique()} |")

    no_nonharm = sorted(
        set(df.loc[df['condition'] != 'harm_control', 'pair_id'])
        - set(pooled["pair_id"])
    )
    lines.append("")
    if no_nonharm:
        lines.append(
            f"**{len(no_nonharm)} storyline(s) with NO surviving non-harm item at all: "
            f"{no_nonharm}** -- these contribute nothing to the pooled non-harm arm; flagged "
            f"rather than silently dropped."
        )
    else:
        lines.append("Every storyline retains at least one non-harm item.")

    REPORT_PATH.write_text("\n".join(lines) + "\n")
    print(f"wrote {SELECTED_PATH} ({len(selected)} rows) and {REPORT_PATH}")
    if no_nonharm:
        print(f"WARNING: {len(no_nonharm)} storyline(s) with no surviving non-harm item: {no_nonharm}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--reviewer-model", help="e.g. claude-sonnet-5 (must not be a subject model)")
    p.add_argument("--mock", action="store_true", help="use a deterministic fake client, no API needed")
    p.add_argument("--check", action="store_true", help="skip curation, just check pass/fail on existing output")
    p.add_argument("--select", action="store_true",
                    help="skip curation, build the filtered dataset + report elicit.py reads")
    p.add_argument("--concurrency", type=int, default=8)
    p.add_argument("--max-retries", type=int, default=3)
    p.add_argument("--max-tokens", type=int, default=10)
    args = p.parse_args()

    if args.check:
        check_manipulation()
        return
    if args.select:
        select_items()
        return

    if not args.mock and not args.reviewer_model:
        p.error("pass --reviewer-model <model> or --mock")

    client = MockClient() if args.mock else AnthropicClient(model=args.reviewer_model)
    asyncio.run(run_curation(client, args.concurrency, args.max_retries, args.max_tokens))


if __name__ == "__main__":
    main()
