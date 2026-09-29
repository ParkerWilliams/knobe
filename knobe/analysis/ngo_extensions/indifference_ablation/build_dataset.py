"""Builds the indifference-clause ablation stimulus set (gameplan item 5,
CLAIMS.md claim 9) from the nonmoral pilot's AUTHORED dataset.

Every one of the 240 authored items (80 Ngo moral + 80 prudential + 80
procedural, both signs) has the same three-sentence shape, verified below
rather than assumed:

    S1  <agent> <did the main action> to <goal>.
    S2  <agent> did not care at all about the effect <X> would have on <Y>.
    S3  <agent> knew <X> would <help/harm Y>.

S2 is the indifference clause claim 9's reading (a) points at. This script
varies it at three levels, holding S1, S3, the question wording, and the
item's pair_id / category / sign fixed:

    indifferent  S2 verbatim (the original item -- re-elicited with fresh
                 seeds, so it doubles as a test-retest of the pilot)
    omitted      S2 deleted; scenario = S1 + S3
    concerned    S2 with "did not care at all about" -> "cared a great deal
                 about", nothing else changed (minimal pair with indifferent)

Both edits are mechanical and asserted per item: exactly one occurrence of
the clause phrase, exactly three sentences, clause in sentence 2. Omission
is safe because no S3 pronoun takes its antecedent from S2 (checked
2026-09-25: every S3 "it"/"them"/"him" refers to an S1 noun or the agent).
Two Ngo originals carry source typos in S2 (moral-12-bad "would have rates
of cancer", moral-29-good "the effect would have on the road"); they are
kept verbatim at indifferent and concerned so the minimal pair stays exact,
and vanish at omitted along with the rest of S2.

``pilot_selected`` marks whether the base item survived the pilot's
curation (196/240), derived the same documented way
``measurement_selection_audit.py`` derives it -- the distinct variant_ids
in the published ``results_dist`` archive -- so this build needs no
local-only input. It exists for claim 9's reading (c): the ablation runs
the full authored set, including the 26 moral-good items curation dropped.

Question columns reuse the nonmoral pilot's per-item q_intentionality /
q_blame / q_praise verbatim (they don't mention the clause, so they are
identical across levels).

Run from the knobe repo root:
    .venv/bin/python analysis/ngo_extensions/indifference_ablation/build_dataset.py

Writes outputs/indifference_ablation_dataset.csv (720 rows = 240 items x 3
levels), committed like the pilots' base dataset CSVs.
"""
from __future__ import annotations

import gzip
import json
import re
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
KNOBE_ROOT = HERE.parents[2]
AUTHORED_PATH = HERE.parent / "nonmoral_pilot" / "outputs" / "ngo_prudential_dataset.csv"
PILOT_RESULTS_GZ = KNOBE_ROOT / "results_dist" / "results_pilot_nonmoral_all.jsonl.gz"
OUT_PATH = HERE / "outputs" / "indifference_ablation_dataset.csv"

CLAUSE = "did not care at all about"
CONCERN = "cared a great deal about"
LEVELS = ("indifferent", "omitted", "concerned")
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")


def split_item(scenario: str, variant_id: str) -> tuple[str, str, str]:
    sents = _SENT_SPLIT.split(scenario.strip())
    if len(sents) != 3:
        raise ValueError(f"{variant_id}: expected 3 sentences, got {len(sents)}: {scenario!r}")
    if scenario.count(CLAUSE) != 1 or CLAUSE not in sents[1]:
        raise ValueError(f"{variant_id}: indifference clause not exactly once in sentence 2: {scenario!r}")
    return sents[0], sents[1], sents[2]


def render(scenario: str, level: str, variant_id: str) -> str:
    s1, s2, s3 = split_item(scenario, variant_id)
    if level == "indifferent":
        return scenario.strip()
    if level == "omitted":
        return f"{s1} {s3}"
    if level == "concerned":
        return f"{s1} {s2.replace(CLAUSE, CONCERN)} {s3}"
    raise ValueError(level)


def pilot_selected_ids() -> set[str]:
    ids = set()
    with gzip.open(PILOT_RESULTS_GZ, "rt") as fh:
        for line in fh:
            ids.add(json.loads(line)["prompt_id"].split("::")[0])
    return ids


def main() -> None:
    base = pd.read_csv(AUTHORED_PATH)
    assert len(base) == 240 and base["variant_id"].is_unique
    selected = pilot_selected_ids()
    assert len(selected) == 196, f"expected the pilot's 196 curated items, found {len(selected)}"

    rows = []
    for _, r in base.iterrows():
        for level in LEVELS:
            rows.append(dict(
                variant_id=f"{r['variant_id']}-{level}",
                base_variant_id=r["variant_id"],
                pair_id=r["pair_id"],
                category=r["category"],
                sign=r["sign"],
                clause=level,
                pilot_selected=r["variant_id"] in selected,
                scenario=render(r["scenario"], level, r["variant_id"]),
                q_intentionality=r["q_intentionality"],
                q_blame=r["q_blame"],
                q_praise=r["q_praise"],
            ))
    out = pd.DataFrame(rows)

    # Structural checks on the rendered set, not just the inputs.
    assert out["variant_id"].is_unique and len(out) == 720
    ind, om, con = (out[out["clause"] == lv].set_index("base_variant_id") for lv in LEVELS)
    assert (ind["scenario"] == base.set_index("variant_id")["scenario"].str.strip()).all()
    assert not om["scenario"].str.contains("care at all|a great deal", regex=True).any()
    assert om["scenario"].map(lambda s: len(_SENT_SPLIT.split(s))).eq(2).all()
    assert con["scenario"].str.count(CONCERN).eq(1).all() and not con["scenario"].str.contains(CLAUSE).any()
    assert (con["scenario"].str.len() - ind["scenario"].str.len()).eq(len(CONCERN) - len(CLAUSE)).all()

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_PATH, index=False)
    cells = out.groupby(["category", "sign", "clause"]).size().unstack("clause")
    print(f"wrote {OUT_PATH} ({len(out)} rows)\n{cells}\n"
          f"pilot_selected: {out.drop_duplicates('base_variant_id')['pilot_selected'].sum()}/240 base items")


if __name__ == "__main__":
    main()
