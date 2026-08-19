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

Unlike the sibling nonmoral pilot's builder, no q_blame/q_praise columns:
blame/praise is explicitly out of scope for this pilot (design doc section
2 -- the asymmetry's existence for these foundations isn't established
yet, so the mechanism question isn't earned).

Pure text merge -- no API access needed. Run:
    .venv/bin/python analysis/ngo_extensions/moral_foundations_pilot/build_dataset.py
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from authority_variants import AUTHORITY_PAIRS
from fairness_variants import FAIRNESS_PAIRS
from harm_control_variants import HARM_CONTROL_PAIRS
from loyalty_variants import LOYALTY_PAIRS
from purity_variants import PURITY_PAIRS, PURPOSE_WRITTEN_PAIR_IDS

HERE = Path(__file__).parent
OUT_PATH = HERE / "outputs" / "mf_pilot_dataset.csv"

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
                rows.append(dict(
                    variant_id=f"{slug}-{pair_id:02d}-{sign}",
                    pair_id=pair_id,
                    condition=condition,
                    source="purpose_written" if pair_id in PURPOSE_WRITTEN_PAIR_IDS else "ngo_derived",
                    sign=sign,
                    scenario=scenario,
                    q_intentionality=question,
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
