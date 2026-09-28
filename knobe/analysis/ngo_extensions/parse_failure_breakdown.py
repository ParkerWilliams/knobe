"""Categorizes the unparsed responses of the instruct checkpoints in both
Ngo pilots by what the model actually emitted, to separate failure causes
that parse rate alone conflates (MF_BLAME_PRAISE_RUN.md section 2c).

Categories, checked in order on the stripped raw_response:
  A blank                -- empty/whitespace only (model stopped)
  B fill-in blank        -- starts with underscores, or is only _ - X etc.
  C restates instruction -- echoes/asks for the answer format
  D starts explaining    -- opens with "Explanation:", "Let's", "I would"...
                            (the 10-token MAX_TOKENS runs out before a number)
  E yes/no               -- a verdict instead of a number
  F digit, unparsed      -- contains a digit the regex parser rejected
  G other prose

The rules are heuristic string matches, not a validated coder; the
examples printed per category are there so the buckets can be checked by
eye. Descriptive only -- no fits, no seeding, deterministic.

Reads the published results_dist archives. Writes
parse_failure_breakdown.csv (% of ALL rows per model x question,
both pilots pooled).

Run from the knobe repo root:
    .venv/bin/python analysis/ngo_extensions/parse_failure_breakdown.py
"""
from __future__ import annotations

import collections
import gzip
import json
import re
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ARCHIVES = [
    REPO / "results_dist" / "results_pilot_nonmoral_all.jsonl.gz",
    REPO / "results_dist" / "results_pilot_moral_foundations_all.jsonl.gz",
]
OUT_PATH = HERE / "parse_failure_breakdown.csv"

INSTRUCTION = re.compile(
    r"read carefully|scenario:|question:|answer with a number|please (answer|select)"
    r"|your answer|(a|the) number from|insert", re.I)
EXPLAINING = re.compile(
    r"\**\s*(explanation|here'?s|here is|let'?s|the answer|reasoning|analysis"
    r"|rationale|i would|i'd)", re.I)


def categorize(raw: str) -> str:
    t = raw.strip()
    if t == "":
        return "A blank"
    if t.startswith(("_", "\\_")) or re.fullmatch(r"[_\\\s\-.*\[\]()X]+", t):
        return "B fill-in blank"
    if INSTRUCTION.search(t):
        return "C restates instruction"
    if EXPLAINING.match(t):
        return "D starts explaining"
    if re.match(r"(yes|no)\b", t, re.I):
        return "E yes/no"
    if re.search(r"\d", t):
        return "F digit, unparsed"
    return "G other prose"


def main() -> None:
    total = collections.Counter()
    failed = collections.defaultdict(collections.Counter)
    examples = collections.defaultdict(list)
    for path in ARCHIVES:
        with gzip.open(path, "rt") as fh:
            for line in fh:
                r = json.loads(line)
                if "instruct" not in r["model_key"]:
                    continue
                key = (r["model_key"], r["prompt_id"].split("::")[1])
                total[key] += 1
                if not r["parse_ok"]:
                    cat = categorize(r["raw_response"])
                    failed[key][cat] += 1
                    ex = examples[(r["model_key"], cat)]
                    if len(ex) < 3:
                        ex.append(r["raw_response"][:60])

    cats = sorted({c for counts in failed.values() for c in counts})
    rows = []
    for (model_key, question), n in sorted(total.items()):
        counts = failed[(model_key, question)]
        row = dict(model_key=model_key, question=question, n_rows=n,
                   pct_failed=round(100 * sum(counts.values()) / n, 1))
        row.update({c: round(100 * counts[c] / n, 1) for c in cats})
        rows.append(row)
    out = pd.DataFrame(rows)
    print(out.to_string(index=False))
    print("\nexamples:")
    for (model_key, cat), ex in sorted(examples.items()):
        print(f"  {model_key:26s} {cat:22s} " + " | ".join(repr(x) for x in ex))
    out.to_csv(OUT_PATH, index=False)
    print(f"\nwrote {OUT_PATH}")


if __name__ == "__main__":
    main()
