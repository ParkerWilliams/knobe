"""Hand-authored FAIRNESS-WITHOUT-HARM pairs for the moral-foundations pilot
(`docs/moral_foundations_extension/MORAL_FOUNDATIONS_PILOT_PLAN.md` sections 3-4).

4-clause template (background fact establishing the agreed even-handed
process -> unrelated instrumental goal -> stated indifference -> foreseen
violation/upholding). The foreseen side effect is unequal/unjust treatment
(bad) or newly equal treatment (good) -- with NO harm or damage to anyone's
welfare, per the curation gate (design doc section 5). This is the delicate
condition: unequal allocation of money, food, or medical care would count
as harm to "finances or material well-being" under the harm-relevance
curation question, so the inequities here are strictly non-material --
speaking slots, votes, turn order, credit and recognition, queue position,
process voice -- never resources someone's welfare depends on.

Storyline scaffolds are Ngo's own (pair_id N -> source items 2N-1/2N in
`../nonmoral_pilot/ngo_2015_original_80.txt`); this foundation draws the 13
storylines of the core subset with a natural agreed process or evenly-shared
arrangement to violate.
"""
from __future__ import annotations

# Each entry: pair_id -> dict(bad=(scenario, question), good=(scenario, question))
FAIRNESS_PAIRS: dict[int, dict[str, tuple[str, str]]] = {
    2: dict(
        bad=("The company's tradition gave every division equal time to present at the annual "
             "review. The CEO started a plan to increase profits. She did not care at all about the "
             "effect the plan would have on the review's even-handedness. She knew the plan's new "
             "schedule would hand her favorite division most of the presentation slots.",
             "Did the CEO intentionally give her favorite division an unfair share of the slots?"),
        good=("The company's annual review had long let the biggest division crowd out everyone "
              "else's presentations. The chairman started a plan to increase revenue. He did not "
              "care at all about the effect the plan would have on the review's even-handedness. He "
              "knew the plan's new schedule would give every division an equal share of the slots "
              "for the first time.",
              "Did the chairman intentionally give every division an equal share of the slots?"),
    ),
    4: dict(
        bad=("The club's tee times had always rotated evenly among all members. Natasha renovated "
             "the country club to improve its appearance. Natasha did not care at all about the "
             "effect the renovation would have on the rotation. Natasha knew the new layout's "
             "schedule would hand the founding members the best tee times.",
             "Did Natasha intentionally skew the tee times toward the founding members?"),
        good=("The club's best tee times had always gone to the founding members first. Floyd "
              "renovated the golf course to improve its playability. Floyd did not care at all "
              "about the effect the renovation would have on the rotation. Floyd knew the new "
              "layout's schedule would give every member an equal shot at the best tee times.",
              "Did Floyd intentionally give every member an equal shot at the best tee times?"),
    ),
    5: dict(
        bad=("The county's water decisions had always given both towns an equal say. The mayor "
             "diverted water to Oldtown to gain votes. He did not care at all about the effect this "
             "would have on the towns' equal say. He knew settling it in Oldtown's council alone "
             "would shut Newtown out of a decision it was owed an equal voice in.",
             "Did the mayor intentionally deny Newtown its equal say?"),
        good=("The county's water decisions had long been settled in whichever town shouted "
              "loudest. The councilwoman diverted water to her town to win an election. She did not "
              "care at all about the effect this would have on the towns' say. She knew putting the "
              "diversion before both towns' councils would give each town an equal say at last.",
              "Did the councilwoman intentionally give both towns an equal say?"),
    ),
    8: dict(
        bad=("The university's planning council had always given every school an equal vote. The "
             "university president enacted a plan to increase business school funding. He did not "
             "care at all about the effect the plan would have on the council's balance. He knew "
             "the plan's new council would hand the business school extra votes at the other "
             "schools' expense.",
             "Did the university president intentionally give the business school an unfair "
             "advantage?"),
        good=("The athletics council had long given the biggest sports extra votes. The athletic "
              "director enacted a plan to increase basketball funding. She did not care at all "
              "about the effect the plan would have on the council's balance. She knew the plan's "
              "new council would give every team an equal vote for the first time.",
              "Did the athletic director intentionally give every team an equal vote?"),
    ),
    13: dict(
        bad=("The plaza assigned its stall spots by a strict waiting list. Joe opened a kiosk to "
             "make more money. Joe did not care at all about the effect this would have on the "
             "waiting list. Joe knew taking the corner spot early would jump him over everyone "
             "ahead of him on the list.",
             "Did Joe intentionally jump the waiting list?"),
        good=("The block's storefronts had always gone to whoever had connections, never by the "
              "waiting list. Helen opened a new store to increase revenue. Helen did not care at "
              "all about the effect this would have on the waiting list. Helen knew leasing "
              "through the list would put the block's storefronts back on a fair queue.",
              "Did Helen intentionally put the storefronts back on a fair queue?"),
    ),
    17: dict(
        bad=("The shelter's annual report had always credited every volunteer equally. Brenda cut "
             "spending at the animal shelter to increase her salary. Brenda did not care at all "
             "about the effect the cut would have on the report's credits. Brenda knew the "
             "slimmed-down report would credit only her favorites and erase the rest.",
             "Did Brenda intentionally credit only her favorites?"),
        good=("The homeless shelter's annual report had always credited only the director's "
              "favorites. Billy cut spending at the homeless shelter to increase his pay. Billy "
              "did not care at all about the effect the cut would have on the report's credits. "
              "Billy knew the simplified report would credit every volunteer equally for the "
              "first time.",
              "Did Billy intentionally credit every volunteer equally?"),
    ),
    18: dict(
        bad=("The health service's honors had always recognized every region's clinics on equal "
             "terms. The Surgeon General implemented the policy to keep his position. He did not "
             "care at all about the effect the policy would have on the honors. He knew the "
             "policy's award criteria would shut the rural clinics out of honors they had earned.",
             "Did the Surgeon General intentionally shut the rural clinics out of the honors?"),
        good=("The service's commendations had long gone disproportionately to headquarters "
              "staff. The Defense Secretary implemented the policy to remain politically popular. "
              "She did not care at all about the effect the policy would have on the "
              "commendations. She knew the policy's criteria would judge every unit's "
              "commendations by the same standard at last.",
              "Did the Defense Secretary intentionally put every unit on the same standard?"),
    ),
    19: dict(
        bad=("Promotions at the firm had always been decided by the same posted criteria for "
             "everyone. Carolyn enacted the plan to increase earnings. Carolyn did not care at "
             "all about the effect the plan would have on the promotion criteria. Carolyn knew "
             "the plan's fast track would let her favorites skip the criteria everyone else was "
             "held to.",
             "Did Carolyn intentionally let her favorites skip the criteria?"),
        good=("Promotions at the firm had long depended on who you knew rather than the posted "
              "criteria. Christopher enacted the plan to increase earnings. Christopher did not "
              "care at all about the effect the plan would have on the promotion criteria. "
              "Christopher knew the plan's review panel would hold everyone to the same posted "
              "criteria at last.",
              "Did Christopher intentionally hold everyone to the same criteria?"),
    ),
    23: dict(
        bad=("The tournament's qualifying spots were decided by strict head-to-head standings. "
             "Eugene screamed during the tennis match to express his excitement. Eugene did not "
             "care at all about the effect this would have on the standings' fairness. Eugene "
             "knew his screams, landing on one player's serves, would tilt the match unfairly "
             "against her.",
             "Did Eugene intentionally tilt the match unfairly?"),
        good=("The tournament's gallery had a habit of cheering only for the hometown favorite. "
              "Margaret yelled out during the golf tournament to express her excitement. Margaret "
              "did not care at all about the effect the yelling would have on the gallery's "
              "even-handedness. Margaret knew cheering every player's shots alike would keep the "
              "gallery's support even-handed.",
              "Did Margaret intentionally keep the gallery's support even-handed?"),
    ),
    26: dict(
        bad=("The district's lunch line had always served every school's children in the same "
             "order. Clara enacted the new lunch plan to cut costs. Clara did not care at all "
             "about the effect this would have on the line's evenness. Clara knew the plan's "
             "schedule would let the magnet school's children eat first every day while the rest "
             "always waited.",
             "Did Clara intentionally let the magnet school's children always eat first?"),
        good=("The training base's mess had always fed officers first and recruits last. Martin "
              "enacted the health plan to cut costs. Martin did not care at all about the effect "
              "this would have on the mess's pecking order. Martin knew the plan's single line "
              "would have officers and recruits served alike.",
              "Did Martin intentionally have officers and recruits served alike?"),
    ),
    29: dict(
        bad=("Precinct guidance required officers to choose stops strictly by observed "
             "violations, never by choice of driver. The cop pulled over the car to meet his "
             "monthly quota. He did not care at all about the effect this would have on "
             "even-handed enforcement. He knew singling out the out-of-town plates would make "
             "the stop discriminatory.",
             "Did the cop intentionally single out out-of-town drivers?"),
        good=("Precinct guidance required officers to choose stops strictly by observed "
              "violations, never by choice of driver. The cop pulled over the truck to meet her "
              "monthly quota. She did not care at all about the effect this would have on "
              "even-handed enforcement. She knew logging the stop under the same criteria as "
              "every other would keep her enforcement even-handed.",
              "Did the cop intentionally keep her enforcement even-handed?"),
    ),
    35: dict(
        bad=("The county had always heard every department's budget appeal in open session. The "
             "financial officer reorganized funding to balance the budget. He did not care at all "
             "about the effect this would have on the appeal process. He knew settling "
             "allocations in closed meetings would shut most departments out of a hearing they "
             "were owed.",
             "Did the financial officer intentionally shut departments out of their hearing?"),
        good=("The county's budget appeals had long been settled in closed meetings only a few "
              "departments could reach. The treasurer reorganized funding to streamline costs. "
              "She did not care at all about the effect this would have on the appeal process. "
              "She knew moving every appeal into open session would give each department the "
              "hearing it was owed.",
              "Did the treasurer intentionally give every department its hearing?"),
    ),
    38: dict(
        bad=("The debates had always allotted every candidate identical speaking time. The "
             "candidate ran for President to get a book deal. She did not care at all about the "
             "effect her candidacy would have on the debate allotments. She knew her celebrity "
             "entry would crowd the minor candidates out of their allotted time.",
             "Did the candidate intentionally crowd the minor candidates out of their time?"),
        good=("The debates had long handed frontrunners the lion's share of speaking time. The "
              "candidate ran for President to get a nice tour bus. He did not care at all about "
              "the effect his candidacy would have on the debate allotments. He knew his entry, "
              "invoking the equal-time rule, would secure every candidate identical airtime.",
              "Did the candidate intentionally secure every candidate identical airtime?"),
    ),
}
