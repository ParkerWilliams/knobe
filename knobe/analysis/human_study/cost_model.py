"""Cost and sample-size model for a human replication of the Ngo-extension
designs, so the budget conversation runs on adjustable arithmetic instead of
a single asserted number.

The thing that matters and is easy to get wrong: **cost scales with total
RATINGS, not with participants.** Participants are paid for their time, so
splitting the same rating workload across more or fewer people barely moves
the total. The two levers that actually change the bill are how many items
you run and how many ratings per item you buy.

    total_ratings = item_question_pairs x ratings_per_item
    participant_time = total_ratings x sec_per_rating
                       + n_participants x per_session_overhead
    cost = participant_time x hourly_rate x (1 + platform_fee)

Per-session overhead (consent, instructions, demographics, debrief) is
charged once per participant regardless of how many items they rate, which
is why *fewer, longer* sessions are cheaper per rating than many short ones.

Rating-count guidance, given this project's own variance work: the ICC
analysis (`23_icc_variance_decomposition.py`) found design effects of 6-160x,
i.e. clusters buy power and within-cluster samples have sharply diminishing
returns. The binding constraint is 40 storylines (nonmoral) and 76 pairs
(foundations), not raters per item. Past roughly 15 ratings per item you are
mostly buying precision you cannot use. Set the final number from a pilot
rather than from this script -- human between-item variance on these stimuli
is unknown and there is no reason it matches the LLM variance components.

Rates are defaults, not quotes. Check current platform pricing before
budgeting.

Run from the knobe repo root:
    .venv/bin/python analysis/human_study/cost_model.py
"""
from __future__ import annotations

from dataclasses import dataclass

# Authored item counts (NOT the post-curation subsets -- running the full
# authored set is what lets human data substitute for the missing curation
# provenance files, by rating the dropped items alongside the retained ones).
NONMORAL_ITEMS = 240          # 40 storylines x 3 framings x 2 signs
FOUNDATION_ITEMS = 152        # 76 pairs x 2 signs

SEC_PER_RATING = 25.0         # 3-clause vignette + one 0-10 question
OVERHEAD_MIN = 3.0            # consent, instructions, demographics, debrief
HOURLY_RATE = 12.00           # USD; Prolific "recommended" tier
PLATFORM_FEE = 0.33           # fraction on top of participant payment


@dataclass
class Design:
    label: str
    pairs: int                # item-question pairs
    note: str


DESIGNS = [
    Design("A. C3 core: blame only, both signs, 3 framings",
           NONMORAL_ITEMS * 1,
           "tests whether the good-cell localization holds in humans"),
    Design("B. C3 + C4: blame and praise",
           NONMORAL_ITEMS * 2,
           "adds the blame-vs-praise dissociation"),
    Design("C. Foundations only: intentionality",
           FOUNDATION_ITEMS * 1,
           "novel to moral psychology on its own -- never run in humans"),
    Design("D. B + C",
           NONMORAL_ITEMS * 2 + FOUNDATION_ITEMS * 1,
           "everything except nonmoral intentionality"),
    Design("E. Full match to the LLM design",
           NONMORAL_ITEMS * 3 + FOUNDATION_ITEMS * 1,
           "adds nonmoral intentionality; the only arm with published human data"),
]


def cost(pairs: int, ratings_per_item: int, ratings_per_participant: int,
         hourly_rate: float = HOURLY_RATE) -> dict:
    total_ratings = pairs * ratings_per_item
    n_participants = -(-total_ratings // ratings_per_participant)  # ceil
    rating_hours = total_ratings * SEC_PER_RATING / 3600
    overhead_hours = n_participants * OVERHEAD_MIN / 60
    hours = rating_hours + overhead_hours
    pay = hours * hourly_rate
    return dict(total_ratings=total_ratings, n_participants=n_participants,
                minutes_each=round((rating_hours + overhead_hours) / n_participants * 60, 1),
                pay=pay, total=pay * (1 + PLATFORM_FEE))


def main() -> None:
    for rpi in (10, 15, 20):
        print(f"\n=== {rpi} ratings per item, {HOURLY_RATE:.0f} USD/hr, "
              f"{int(PLATFORM_FEE*100)}% fee, 30 ratings per session ===")
        print(f"{'design':<48}{'ratings':>9}{'people':>8}{'min':>7}{'TOTAL':>10}")
        for d in DESIGNS:
            c = cost(d.pairs, rpi, ratings_per_participant=30)
            print(f"{d.label:<48}{c['total_ratings']:>9}{c['n_participants']:>8}"
                  f"{c['minutes_each']:>7.1f}{'$'+format(c['total'], ',.0f'):>10}")

    print("\n--- session length barely changes the bill, item count does ---")
    for rpp in (15, 30, 45):
        c = cost(DESIGNS[-1].pairs, 15, rpp)
        print(f"  {rpp:>2} ratings/session -> {c['n_participants']:>4} people, "
              f"{c['minutes_each']:>4.1f} min each, ${c['total']:,.0f}")

    print("\n--- and the hourly rate is the other real lever ---")
    for rate in (9.0, 12.0, 15.0):
        c = cost(DESIGNS[-1].pairs, 15, 30, hourly_rate=rate)
        print(f"  ${rate:>5.2f}/hr -> ${c['total']:,.0f} for the full design")


if __name__ == "__main__":
    main()
