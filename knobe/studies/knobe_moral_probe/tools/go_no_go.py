"""Go / no-go for the full run, from the pilot's kmp.checks outputs (docs/FULL_RUN.md).

Reads the gate summary in each checks folder's provenance.json and sorts every blocking line by
fixed rules, so the decision needs no judgment call:

  allowed  number_rate on a pretrained model (DESIGN.md section 8: a pretrained model that can't
           answer is a finding for RQ3, not a blocker; its rows are cheap, so it stays in the run);
           number_rate on llama-3.1-8b-instruct intentionality or praise at >= LLAMA_REFUSAL_FLOOR
           (its known refusals to rate harm, ANALYSIS_LOG.md 2026-10-13 and 2026-10-22; how they
           enter the analysis is MM's decision and doesn't change the data collected)
  stop     everything else: cut_off, coverage, number_rate on any other instruct cell or below the
           floor, validity or example copying on an instruct model, an unreadable gate line, a
           missing checks folder

Non-blocking findings (pretrained validity and copying) are listed and never stop the run.
Exit 0 = GO, 1 = NO-GO.

From the study folder:
    ../../.venv/bin/python -m tools.go_no_go outputs/checks/pilot_*
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

LLAMA_INSTRUCT = "llama-3.1-8b-instruct"
LLAMA_REFUSAL_QKEYS = ("intentionality", "praise")
LLAMA_REFUSAL_FLOOR = 0.70
_NUMBER_RATE = re.compile(r"^number_rate: (\S+) (\S+) (\S+) (\S+) ([0-9.]+) < ")


def classify(line: str) -> str:
    """'allowed' or 'stop' for one blocking gate line."""
    m = _NUMBER_RATE.match(line)
    if not m:
        return "stop"
    model_key, _experiment, qkey, _wording, rate = m.groups()
    if model_key.endswith("-pretrained"):
        return "allowed"
    if model_key == LLAMA_INSTRUCT and qkey in LLAMA_REFUSAL_QKEYS and float(rate) >= LLAMA_REFUSAL_FLOOR:
        return "allowed"
    return "stop"


def decide(check_dirs: list[Path]) -> dict:
    allowed, stops, findings = [], [], []
    for d in map(Path, check_dirs):
        prov = d / "provenance.json"
        if not prov.exists():
            stops.append(f"{d}: no provenance.json (were the pilot checks run?)")
            continue
        gate = json.loads(prov.read_text(encoding="utf-8"))["gate"]
        for line in gate["blocking"]:
            (allowed if classify(line) == "allowed" else stops).append(f"{d.name}: {line}")
        findings += [f"{d.name}: {f}" for f in gate["findings"]]
    return {"go": not stops, "stops": stops, "allowed": allowed, "findings": findings}


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    if not argv:
        print("usage: python -m tools.go_no_go <checks folder> ...", file=sys.stderr)
        return 2
    v = decide([Path(a) for a in argv])
    for title, key in (("STOP", "stops"), ("allowed (known, not a stop)", "allowed"), ("findings", "findings")):
        print(f"\n{title} ({len(v[key])}):")
        print("\n".join(f"  {x}" for x in v[key]) or "  none")
    print(f"\n{'GO' if v['go'] else 'NO-GO'}: {len(v['stops'])} stop(s), {len(v['allowed'])} allowed, "
          f"{len(v['findings'])} finding(s)")
    return 0 if v["go"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
