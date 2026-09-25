"""Merges the five hand-authored condition files of the moral-foundations
pilot (`docs/moral_foundations_extension/MORAL_FOUNDATIONS_PILOT_PLAN.md`)
into one dataset, ready for curation (`curate_foundation_relevance.py`)
and, if that passes, elicitation (`elicit.py`).

Output: outputs/mf_pilot_dataset.csv, one row per item (152 total: 60
harm_control + 26 loyalty + 26 authority + 26 fairness + 14 purity),
columns:
    variant_id      -- e.g. "harm-01-bad", "loyalty-01-good", "purity-101-bad"
    pair_id         -- storyline id; 1-40 map to Ngo's source pairs
                       (pair_id N -> Ngo items 2N-1/2N), 101-104 are the
                       purpose-written purity storylines
    condition       -- "harm_control" | "loyalty" | "authority" |
                       "fairness" | "purity"
    source          -- "ngo_derived" | "purpose_written" (design doc
                       section 4's explicit flag for purity's supplemental
                       storylines; every pair_id <= 40 is ngo_derived)
    sign            -- "bad" | "good"
    scenario        -- the 4-clause setup (no question)
    q_intentionality -- the intentionality question (targets the foreseen
                       SIDE EFFECT only, never the main action)
    q_blame         -- constants.QUESTIONS["q_blame"], agent phrase pulled
                       from q_intentionality
    q_praise        -- constants.QUESTIONS["q_praise"], same agent phrase

q_blame/q_praise added 2026-09-25 (SUBMISSION_GAMEPLAN.md section 5 item
6). The design doc (section 2) originally scoped them out because the
asymmetry's existence for these foundations wasn't established; the pilot
has since established it, and the blame-vs-praise comparison (CLAIMS.md
claim 4) is the strongest claim in the set, so extending it across
foundations is now earned. Wording and agent extraction are REUSED from
the sibling nonmoral pilot's builder (`extract_agent_phrase`, the frozen
`constants.QUESTIONS` templates), not reimplemented, so the two pilots'
blame/praise prompts are built identically. The original columns are
unchanged byte-for-byte.

Pure text merge -- no API access needed. Run:
    .venv/bin/python analysis/ngo_extensions/moral_foundations_pilot/build_dataset.py
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd

from authority_variants import AUTHORITY_PAIRS
from fairness_variants import FAIRNESS_PAIRS
from harm_control_variants import HARM_CONTROL_PAIRS
from loyalty_variants import LOYALTY_PAIRS
from purity_variants import PURITY_PAIRS, PURPOSE_WRITTEN_PAIR_IDS

HERE = Path(__file__).parent
OUT_PATH = HERE / "outputs" / "mf_pilot_dataset.csv"

REPO_SRC = Path(__file__).resolve().parents[3] / "src"
sys.path.insert(0, str(REPO_SRC))
from knobe import constants  # noqa: E402

# The sibling's builder is also named build_dataset.py, so load it under a
# distinct module name; its own sibling imports need its dir on sys.path.
_NONMORAL_DIR = HERE.parent / "nonmoral_pilot"
sys.path.insert(0, str(_NONMORAL_DIR))
_spec = importlib.util.spec_from_file_location(
    "nonmoral_build_dataset", _NONMORAL_DIR / "build_dataset.py")
_nonmoral_build = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_nonmoral_build)
extract_agent_phrase = _nonmoral_build.extract_agent_phrase

CONDITIONS: dict[str, tuple[str, dict[int, dict[str, tuple[str, str]]]]] = {
    # condition -> (variant_id slug, pairs dict)
    "harm_control": ("harm", HARM_CONTROL_PAIRS),
    "loyalty": ("loyalty", LOYALTY_PAIRS),
    "authority": ("authority", AUTHORITY_PAIRS),
    "fairness": ("fairness", FAIRNESS_PAIRS),
    "purity": ("purity", PURITY_PAIRS),
}


def main() -> None:
    rows = []
    for condition, (slug, pairs) in CONDITIONS.items():
        for pair_id in sorted(pairs):
            for sign in ("bad", "good"):
                scenario, question = pairs[pair_id][sign]
                agent = extract_agent_phrase(question)
                rows.append(dict(
                    variant_id=f"{slug}-{pair_id:02d}-{sign}",
                    pair_id=pair_id,
                    condition=condition,
                    source="purpose_written" if pair_id in PURPOSE_WRITTEN_PAIR_IDS else "ngo_derived",
                    sign=sign,
                    scenario=scenario,
                    q_intentionality=question,
                    q_blame=constants.QUESTIONS["q_blame"].format(agent_lower=agent),
                    q_praise=constants.QUESTIONS["q_praise"].format(agent_lower=agent),
                ))

    out = pd.DataFrame(rows)
    assert out["variant_id"].is_unique
    # every purpose-written storyline is purity-only by construction
    assert set(out.loc[out["source"] == "purpose_written", "condition"]) == {"purity"}
    # every non-harm storyline in the core subset also has a harm control
    harm_pairs = set(out.loc[out["condition"] == "harm_control", "pair_id"])
    nonharm_ngo = set(out.loc[(out["condition"] != "harm_control")
                              & (out["source"] == "ngo_derived"), "pair_id"])
    assert nonharm_ngo <= harm_pairs, sorted(nonharm_ngo - harm_pairs)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_PATH, index=False)
    counts = out.groupby("condition").size().to_dict()
    print(f"wrote {OUT_PATH} ({len(out)} rows: "
          + ", ".join(f"{n} {c}" for c, n in sorted(counts.items())) + ")")


if __name__ == "__main__":
    main()
