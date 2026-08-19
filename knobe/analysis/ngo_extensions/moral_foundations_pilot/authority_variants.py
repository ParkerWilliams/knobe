"""Hand-authored AUTHORITY pairs for the moral-foundations pilot
(`docs/moral_foundations_extension/MORAL_FOUNDATIONS_PILOT_PLAN.md` sections 3-4).

4-clause template (background fact establishing the legitimate rule/
hierarchy -> unrelated instrumental goal -> stated indifference -> foreseen
violation/upholding). The foreseen side effect undermines (bad) or upholds
(good) a legitimate authority, rule, or hierarchy -- with NO harm or damage
to anyone's welfare, per the curation gate (design doc section 5): the
outcomes are procedural defiance/respect (skipped sign-offs, bypassed
reviews, honored chains of command), never material or bodily consequences,
and never the agent's own punishment (which would re-introduce a welfare
stake).

Storyline scaffolds are Ngo's own (pair_id N -> source items 2N-1/2N in
`../nonmoral_pilot/ngo_2015_original_80.txt`); this foundation draws the 13
storylines of the core subset with a natural institutional rule or hierarchy
(corporate, academic, civic, medical, law-enforcement domains).
"""
from __future__ import annotations

# Each entry: pair_id -> dict(bad=(scenario, question), good=(scenario, question))
AUTHORITY_PAIRS: dict[int, dict[str, tuple[str, str]]] = {
    1: dict(
        bad=("The lab's release protocol required the chief engineer's sign-off on every launch. "
             "Bill released the gadget to make a deadline. Bill did not care at all about the effect "
             "this would have on the release protocol. Bill knew shipping without the sign-off would "
             "flout the chief engineer's authority.",
             "Did Bill intentionally flout the chief engineer's authority?"),
        good=("The lab's release protocol required the chief engineer's sign-off on every launch. "
              "Robyn released the invention to make a deadline. Robyn did not care at all about the "
              "effect this would have on the release protocol. Robyn knew routing the launch through "
              "the sign-off would uphold the chief engineer's authority.",
              "Did Robyn intentionally uphold the chief engineer's authority?"),
    ),
    2: dict(
        bad=("The company's charter gave the board final say over every major initiative. The CEO "
             "started a plan to increase profits. She did not care at all about the effect the plan "
             "would have on the board's authority. She knew launching it without a board vote would "
             "undermine the board's authority.",
             "Did the CEO intentionally undermine the board's authority?"),
        good=("The company's charter gave the board final say over every major initiative. The "
              "chairman started a plan to increase revenue. He did not care at all about the effect "
              "the plan would have on the board's authority. He knew putting it to a board vote "
              "first would affirm the board's authority.",
              "Did the chairman intentionally affirm the board's authority?"),
    ),
    4: dict(
        bad=("The club's bylaws required the members' committee to approve any change to the "
             "grounds. Natasha renovated the country club to improve its appearance. Natasha did "
             "not care at all about the effect this would have on the committee's authority. "
             "Natasha knew starting the work without the committee's approval would defy the "
             "committee's authority.",
             "Did Natasha intentionally defy the committee's authority?"),
        good=("The club's bylaws required the members' committee to approve any change to the "
              "grounds. Floyd renovated the golf course to improve its playability. Floyd did not "
              "care at all about the effect this would have on the committee's authority. Floyd "
              "knew submitting the plans for the committee's approval would respect the committee's "
              "authority.",
              "Did Floyd intentionally respect the committee's authority?"),
    ),
    8: dict(
        bad=("The university's statutes gave the faculty senate authority over budget changes. The "
             "university president enacted a plan to increase business school funding. He did not "
             "care at all about the effect this would have on the senate's authority. He knew "
             "enacting the plan by decree would undermine the senate's authority.",
             "Did the university president intentionally undermine the senate's authority?"),
        good=("The university's statutes gave the faculty senate authority over budget changes. The "
              "athletic director enacted a plan to increase basketball funding. She did not care at "
              "all about the effect this would have on the senate's authority. She knew bringing "
              "the plan before the senate for its vote would affirm the senate's authority.",
              "Did the athletic director intentionally affirm the senate's authority?"),
    ),
    11: dict(
        bad=("The neighborhood association's code required approval for any exterior display. Tim "
             "installed a light display to decorate his house. Tim did not care at all about the "
             "effect this would have on the association's code. Tim knew wiring it up unapproved "
             "would flout the association's rules.",
             "Did Tim intentionally flout the association's rules?"),
        good=("The neighborhood association's code required approval for any exterior display. "
              "Tricia installed a lighting array to decorate her yard. Tricia did not care at all "
              "about the effect this would have on the association's code. Tricia knew filing the "
              "display for approval first would respect the association's rules.",
              "Did Tricia intentionally respect the association's rules?"),
    ),
    12: dict(
        bad=("The institute's review board had sole authority to authorize any drug release. The "
             "scientist released a drug to gain profit. She did not care at all about the effect "
             "this would have on the review board's authority. She knew releasing it unreviewed "
             "would defy the review board's authority.",
             "Did the scientist intentionally defy the review board's authority?"),
        good=("The institute's review board had sole authority to authorize any drug release. The "
              "scientist released a drug to make a deadline. He did not care at all about the "
              "effect this would have on the review board's authority. He knew submitting the "
              "release for the board's review would uphold the review board's authority.",
              "Did the scientist intentionally uphold the review board's authority?"),
    ),
    17: dict(
        bad=("The shelter's charter required board approval for any budget change. Brenda cut "
             "spending at the animal shelter to increase her salary. Brenda did not care at all "
             "about the effect this would have on the board's authority. Brenda knew cutting the "
             "budget by fiat would undermine the board's authority.",
             "Did Brenda intentionally undermine the board's authority?"),
        good=("The shelter's charter required board approval for any budget change. Billy cut "
              "spending at the homeless shelter to increase his pay. Billy did not care at all "
              "about the effect this would have on the board's authority. Billy knew presenting "
              "the cut for the board's vote would respect the board's authority.",
              "Did Billy intentionally respect the board's authority?"),
    ),
    18: dict(
        bad=("By statute, national health policies required the advisory council's review. The "
             "Surgeon General implemented the policy to keep his position. He did not care at all "
             "about the effect this would have on the council's authority. He knew skipping the "
             "council's review would undermine the council's authority.",
             "Did the Surgeon General intentionally undermine the council's authority?"),
        good=("By statute, national defense policies required the advisory council's review. The "
              "Defense Secretary implemented the policy to remain politically popular. She did not "
              "care at all about the effect this would have on the council's authority. She knew "
              "submitting the policy for the council's review would affirm the council's authority.",
              "Did the Defense Secretary intentionally affirm the council's authority?"),
    ),
    21: dict(
        bad=("The wildlife commission set binding season rules for the valley's hunters. Jerry "
             "hunted animals to earn a living. Jerry did not care at all about the effect this "
             "would have on the commission's rules. Jerry knew hunting out of season would defy "
             "the commission's rules.",
             "Did Jerry intentionally defy the commission's rules?"),
        good=("The wildlife commission set binding permit rules for field researchers. Linda "
              "trapped animals to do research. Linda did not care at all about the effect this "
              "would have on the commission's rules. Linda knew filing for every permit would "
              "uphold the commission's rules.",
              "Did Linda intentionally uphold the commission's rules?"),
    ),
    23: dict(
        bad=("The tennis club's rules gave the chair umpire absolute authority over crowd conduct. "
             "Eugene screamed during the tennis match to express his excitement. Eugene did not "
             "care at all about the effect this would have on the umpire's authority. Eugene knew "
             "screaming over the umpire's calls for silence would defy the umpire's authority.",
             "Did Eugene intentionally defy the umpire's authority?"),
        good=("The tournament's rules gave the marshals authority over when the gallery could "
              "cheer. Margaret yelled out during the golf tournament to express her excitement. "
              "Margaret did not care at all about the effect this would have on the marshals' "
              "authority. Margaret knew cheering only on the marshals' signal would respect the "
              "marshals' authority.",
              "Did Margaret intentionally respect the marshals' authority?"),
    ),
    29: dict(
        bad=("Department procedure required dispatch clearance before any traffic stop on the "
             "highway. The cop pulled over the car to meet his monthly quota. He did not care at "
             "all about the effect this would have on the department's procedure. He knew making "
             "the stop without clearance would defy the department's chain of command.",
             "Did the cop intentionally defy the chain of command?"),
        good=("Department procedure required dispatch clearance before any traffic stop on the "
              "highway. The cop pulled over the truck to meet her monthly quota. She did not care "
              "at all about the effect this would have on the department's procedure. She knew "
              "calling the stop in for clearance first would respect the department's chain of "
              "command.",
              "Did the cop intentionally respect the chain of command?"),
    ),
    38: dict(
        bad=("The party's rules required candidates to seek the leadership's endorsement before "
             "declaring. The candidate ran for President to get a book deal. She did not care at "
             "all about the effect her candidacy would have on the party's rules. She knew "
             "declaring without the leadership's endorsement would undermine the party "
             "leadership's authority.",
             "Did the candidate intentionally undermine the party leadership's authority?"),
        good=("The party's rules required candidates to seek the leadership's endorsement before "
              "declaring. The candidate ran for President to get a nice tour bus. He did not care "
              "at all about the effect his candidacy would have on the party's rules. He knew "
              "seeking the leadership's endorsement first would affirm the party leadership's "
              "authority.",
              "Did the candidate intentionally affirm the party leadership's authority?"),
    ),
    40: dict(
        bad=("The hospital's formulary board had final authority over which drugs could be "
             "prescribed. The doctor prescribed the Elixir drug to make the drug company happy. "
             "She did not care at all about the effect this would have on the formulary board's "
             "authority. She knew prescribing off the formulary would defy the board's authority.",
             "Did the doctor intentionally defy the formulary board's authority?"),
        good=("The hospital's formulary board had final authority over which drugs could be "
              "prescribed. The doctor prescribed the Gastropurge drug to please the drug vendor. "
              "He did not care at all about the effect this would have on the formulary board's "
              "authority. He knew filing the request through the formulary board would uphold the "
              "board's authority.",
              "Did the doctor intentionally uphold the formulary board's authority?"),
    ),
}
