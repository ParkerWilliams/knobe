"""Convert the two August pilots' vignettes into kmp items, unchanged in
wording, so the study pipeline can run on them as they are.

Sources (committed on main and this branch):
  analysis/ngo_extensions/nonmoral_pilot/outputs/ngo_prudential_dataset.csv
      240 items: Ngo's 80 moral originals + Mer's 80 prudential and 80
      procedural variants (nonmoral_pilot/*_variants.py, 2026-08-16)
  analysis/ngo_extensions/moral_foundations_pilot/outputs/mf_pilot_dataset.csv
      152 items: harm controls + loyalty/authority/fairness/purity variants

Mapping: storyline_id = pair_id; nonmoral arms moral/prudential/procedural
(from category), foundations arms harm/loyalty/authority/fairness/purity
(harm_control -> harm); scaffold "shared" for Ngo-derived foundations
storylines, "purpose" for the purpose-written purity ones. agent and effect
come from the item's own intentionality question ("Did {agent}
intentionally {effect}?"), so kmp renders it back word for word; the two
Ngo originals worded "Did X cause ...?" take agent/effect from
stimuli/ngo_verbatim.csv (same text, 80/80 scenarios identical).

source = "ngo" for Ngo's originals, "pilot" for the rest. review_status =
"draft": these are the pilot texts, NOT items approved under the new study's
review (DESIGN.md section 3.4), and they predate the role-noun rule, so they
use personal names. Running them is an indicative pass, not the study's
stimuli; kmp.elicit itself refuses drafts, which is why
tools/openrouter_first_look.py has an explicit --allow-draft flag.

From the study folder:
    ../../.venv/bin/python tools/pilot_items_to_kmp.py
Writes stimuli/pilot/pilot_nonmoral.csv and stimuli/pilot/pilot_foundations.csv.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

STUDY = Path(__file__).resolve().parents[1]
REPO = STUDY.parents[1]
sys.path.insert(0, str(STUDY))

from kmp.items import Item, design_problems, load_items, make_item_id, write_items  # noqa: E402

NONMORAL = REPO / "analysis/ngo_extensions/nonmoral_pilot/outputs/ngo_prudential_dataset.csv"
FOUNDATIONS = REPO / "analysis/ngo_extensions/moral_foundations_pilot/outputs/mf_pilot_dataset.csv"
VERBATIM = STUDY / "stimuli/ngo_verbatim.csv"
OUT = STUDY / "stimuli/pilot"
QUESTION = re.compile(r"^Did (.+?) intentionally (.+)\?$")
NONMORAL_ARM = {"moral": "moral", "nonmoral_prudential": "prudential", "nonmoral_procedural": "procedural"}
FOUNDATION_ARM = {"harm_control": "harm", "loyalty": "loyalty", "authority": "authority",
                  "fairness": "fairness", "purity": "purity"}


def agent_effect(question: str, fallback: dict | None) -> tuple[str, str]:
    m = QUESTION.match(question.strip())
    if m:
        return m.group(1), m.group(2)
    if fallback is None:
        raise ValueError(f"can't split agent/effect from {question!r}")
    return fallback["agent"], fallback["effect"]


def build() -> tuple[list[Item], list[Item]]:
    verbatim = {(r.storyline_id, r.sign): r._asdict() for r in pd.read_csv(VERBATIM).itertuples()}
    nonmoral = []
    for r in pd.read_csv(NONMORAL).itertuples():
        arm = NONMORAL_ARM[r.category]
        agent, effect = agent_effect(r.q_intentionality, verbatim.get((r.pair_id, r.sign)) if arm == "moral" else None)
        nonmoral.append(Item(item_id=make_item_id("nonmoral", r.pair_id, arm, r.sign), experiment="nonmoral",
                             storyline_id=r.pair_id, arm=arm, sign=r.sign, agent=agent, effect=effect,
                             scenario=r.scenario.strip(), source="ngo" if arm == "moral" else "pilot",
                             review_status="draft", scaffold=None))
    foundations = []
    for r in pd.read_csv(FOUNDATIONS).itertuples():
        arm = FOUNDATION_ARM[r.condition]
        agent, effect = agent_effect(r.q_intentionality, None)
        foundations.append(Item(item_id=make_item_id("foundations", r.pair_id, arm, r.sign),
                                experiment="foundations", storyline_id=r.pair_id, arm=arm, sign=r.sign,
                                agent=agent, effect=effect, scenario=r.scenario.strip(), source="pilot",
                                review_status="draft",
                                scaffold="purpose" if r.source == "purpose_written" else "shared"))
    return nonmoral, foundations


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, items in zip(("pilot_nonmoral", "pilot_foundations"), build()):
        path = OUT / f"{name}.csv"
        write_items(items, path)
        back = load_items(path)                      # round-trip through kmp's own loader (it sorts rows)
        assert {i.item_id: i.model_dump() for i in back} == {i.item_id: i.model_dump() for i in items}
        problems = design_problems(back, stage="selected")
        kinds = {}
        for p in problems:
            kinds[p.split(":")[0][:60]] = kinds.get(p.split(":")[0][:60], 0) + 1
        print(f"wrote {path} ({len(back)} items); design-check findings vs the NEW study's rules: "
              f"{len(problems)}" + (f" e.g. {problems[:2]}" if problems else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
