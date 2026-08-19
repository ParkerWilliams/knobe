"""Hand-authored harm-control pairs for the moral-foundations pilot
(`docs/moral_foundations_extension/MORAL_FOUNDATIONS_PILOT_PLAN.md` section 3-4).

Freshly written, NOT reused verbatim from Ngo et al. (2015): every item uses
the pilot's 4-clause template (background fact establishing the stake ->
unrelated instrumental goal -> stated indifference -> foreseen outcome), one
clause more than Ngo's original 3-clause structure, so clause count/
complexity is matched between the harm-control and the four new foundation
conditions rather than being a confound (design doc section 3, an explicit
brainstorming decision in favor of internal symmetry over literal reuse).

Storyline scaffolds (agent archetypes, goals, domains) are Ngo's own
(`../nonmoral_pilot/ngo_2015_original_80.txt`): pair_id N corresponds to Ngo
source items 2N-1 (bad/harm) and 2N (good/help). The core subset here is 30
of Ngo's 40 storylines -- the three pairs already flagged as unadaptable in
`../nonmoral_pilot/prudential_variants.py` (7: wartime bombing, 34:
terrorism, 37: cult mass-suicide) are excluded, along with seven more that
didn't hold up under drafting for this pilot's foundation conditions
(3, 6, 14, 20, 22, 28, 36) -- the design doc's target was ~25-30, with the
exact count expected to move during authoring (section 7).

The outcome is always a foreseen change in someone's WELFARE (health,
safety, finances, material well-being) -- the thing the four foundation
conditions must avoid and this condition must hit, per the curation
manipulation check (design doc section 5). The side effect, never the main
action, is what the intentionality question targets (the general
Knobe-paradigm invariant, `docs/rq1_findings/KNOBE_EFFECT_STATUS.md`).
"""
from __future__ import annotations

# Each entry: pair_id -> dict(bad=(scenario, question), good=(scenario, question))
HARM_CONTROL_PAIRS: dict[int, dict[str, tuple[str, str]]] = {
    1: dict(
        bad=("The families in the test market relied on the gadget's child-safety lock. Bill released "
             "the gadget to make a deadline. Bill did not care at all about the effect the gadget would "
             "have on the children using it. Bill knew the gadget's faulty lock would injure children.",
             "Did Bill intentionally injure children?"),
        good=("The families in the test market relied on the invention's child-safety lock. Robyn "
              "released the invention to make a deadline. Robyn did not care at all about the effect "
              "the invention would have on the children using it. Robyn knew the invention's improved "
              "lock would protect children from injury.",
              "Did Robyn intentionally protect children from injury?"),
    ),
    2: dict(
        bad=("The wetland beside the plant kept the region's drinking water clean. The CEO started a "
             "plan to increase profits. She did not care at all about the effect the plan would have on "
             "the wetland. She knew the plan's runoff would poison the wetland.",
             "Did the CEO intentionally poison the wetland?"),
        good=("The wetland beside the plant kept the region's drinking water clean. The chairman "
              "started a plan to increase revenue. He did not care at all about the effect the plan "
              "would have on the wetland. He knew the plan's new filtration would restore the wetland.",
              "Did the chairman intentionally restore the wetland?"),
    ),
    4: dict(
        bad=("The country club's elderly members depended on its accessible front ramp. Natasha "
             "renovated the country club to improve its appearance. Natasha did not care at all about "
             "the effect the renovation would have on the elderly members. Natasha knew removing the "
             "ramp would cause elderly members to fall.",
             "Did Natasha intentionally cause elderly members to fall?"),
        good=("The golf course's elderly members depended on shade to get through summer rounds. Floyd "
              "renovated the golf course to improve its playability. Floyd did not care at all about "
              "the effect the renovation would have on the elderly members. Floyd knew the added shade "
              "would protect elderly members from heatstroke.",
              "Did Floyd intentionally protect elderly members from heatstroke?"),
    ),
    5: dict(
        bad=("Newtown's residents depended on the reservoir for their drinking water. The mayor "
             "diverted water to Oldtown to gain votes. He did not care at all about the effect this "
             "would have on Newtown's residents. He knew the diversion would leave Newtown's residents "
             "without safe drinking water.",
             "Did the mayor intentionally leave Newtown's residents without safe drinking water?"),
        good=("The valley's farms depended on the river for irrigation. The councilwoman diverted "
              "water to her town to win an election. She did not care at all about the effect this "
              "would have on the valley's farms. She knew the diversion would double the farms' "
              "harvest.",
              "Did the councilwoman intentionally double the farms' harvest?"),
    ),
    8: dict(
        bad=("The medical school's clinic treated hundreds of uninsured patients. The university "
             "president enacted a plan to increase business school funding. He did not care at all "
             "about the effect the plan would have on the clinic's patients. He knew cutting the "
             "clinic's funding would leave its patients without care.",
             "Did the university president intentionally leave the clinic's patients without care?"),
        good=("The soccer team's trainers ran the campus concussion clinic. The athletic director "
              "enacted a plan to increase basketball funding. She did not care at all about the effect "
              "the plan would have on the concussion clinic. She knew the funding formula would expand "
              "the clinic's care for injured students.",
              "Did the athletic director intentionally expand care for injured students?"),
    ),
    9: dict(
        bad=("Susie-Ann's family lived off the vegetables from her plot. Jenny spread weed killer to "
             "protect her crops. Jenny did not care at all about the effect this would have on "
             "Susie-Ann's plot. Jenny knew the weed killer's drift would destroy Susie-Ann's "
             "vegetables.",
             "Did Jenny intentionally destroy Susie-Ann's vegetables?"),
        good=("Billy-Bob's family lived off the vegetables from his plot. Stanley spread anti-fungals "
              "to protect his crops. Stanley did not care at all about the effect this would have on "
              "Billy-Bob's plot. Stanley knew the anti-fungals' drift would save Billy-Bob's "
              "vegetables from blight.",
              "Did Stanley intentionally save Billy-Bob's vegetables from blight?"),
    ),
    10: dict(
        bad=("Kate's uncle depended on daily company to manage his depression. Kate placed her uncle "
             "in a nursing home to avoid being his caretaker. Kate did not care at all about the "
             "effect the placement would have on her uncle. Kate knew the isolated facility would "
             "deepen her uncle's depression.",
             "Did Kate intentionally deepen her uncle's depression?"),
        good=("Jared's aunt depended on daily company to manage her depression. Jared placed his aunt "
              "in a nursing home to avoid being her caretaker. Jared did not care at all about the "
              "effect the placement would have on his aunt. Jared knew the facility's busy social "
              "program would lift his aunt's depression.",
              "Did Jared intentionally lift his aunt's depression?"),
    ),
    11: dict(
        bad=("Tim's neighbor slept with her windows uncovered to manage her night-shift schedule. Tim "
             "installed a light display to decorate his house. Tim did not care at all about the "
             "effect the display would have on his neighbor. Tim knew the floodlights would ruin his "
             "neighbor's sleep.",
             "Did Tim intentionally ruin his neighbor's sleep?"),
        good=("The neighborhood kids crossed a dark intersection walking home each evening. Tricia "
              "installed a lighting array to decorate her yard. Tricia did not care at all about the "
              "effect the array would have on the kids. Tricia knew the lights would make the kids' "
              "crossing safe.",
              "Did Tricia intentionally make the kids' crossing safe?"),
    ),
    12: dict(
        bad=("The drug's trial patients had healthy hearts when they enrolled. The scientist released "
             "a drug to gain profit. She did not care at all about the effect the drug would have on "
             "the patients. She knew the drug's side effects would damage the patients' hearts.",
             "Did the scientist intentionally damage the patients' hearts?"),
        good=("The drug's trial patients had dangerously weak hearts when they enrolled. The scientist "
              "released a drug to make a deadline. He did not care at all about the effect the drug "
              "would have on the patients. He knew the drug's side effects would strengthen the "
              "patients' hearts.",
              "Did the scientist intentionally strengthen the patients' hearts?"),
    ),
    13: dict(
        bad=("The food cart vendors on the plaza earned just enough to get by. Joe opened a kiosk to "
             "make more money. Joe did not care at all about the effect the kiosk would have on the "
             "vendors. Joe knew the kiosk would drive the vendors out of business.",
             "Did Joe intentionally drive the vendors out of business?"),
        good=("The shops on the block had been losing customers for years. Helen opened a new store to "
              "increase revenue. Helen did not care at all about the effect the store would have on "
              "the other shops. Helen knew the store's foot traffic would revive the other shops.",
              "Did Helen intentionally revive the other shops?"),
    ),
    15: dict(
        bad=("Curtis needed to pass the morning's exam to keep his scholarship. Jacob threw a party to "
             "be more popular. Jacob did not care at all about the effect the party would have on "
             "Curtis. Jacob knew the noise would make Curtis fail the exam and lose his scholarship.",
             "Did Jacob intentionally make Curtis lose his scholarship?"),
        good=("Jackie had been too lonely to make a single friend all semester. Rachel threw a party "
              "to have fun. Rachel did not care at all about the effect the party would have on "
              "Jackie. Rachel knew the party would finally bring Jackie friends.",
              "Did Rachel intentionally bring Jackie friends?"),
    ),
    16: dict(
        bad=("Russell's neighbor grew prize vegetables that needed full sunlight. Russell planted a "
             "tree to decorate his yard. Russell did not care at all about the effect the tree would "
             "have on his neighbor's garden. Russell knew the tree's shade would kill his neighbor's "
             "vegetables.",
             "Did Russell intentionally kill his neighbor's vegetables?"),
        good=("Vicky's neighbor's porch baked in the afternoon sun all summer. Vicky planted a tree to "
              "have fruit in the fall. Vicky did not care at all about the effect the tree would have "
              "on her neighbor's porch. Vicky knew the tree's shade would finally cool her neighbor's "
              "porch.",
              "Did Vicky intentionally cool her neighbor's porch?"),
    ),
    17: dict(
        bad=("The shelter's dogs depended on its medical fund for their treatment. Brenda cut spending "
             "at the animal shelter to increase her salary. Brenda did not care at all about the "
             "effect the cut would have on the dogs. Brenda knew cutting the medical fund would cause "
             "a sick dog to be put down.",
             "Did Brenda intentionally cause the dog to be put down?"),
        good=("The homeless shelter's residents depended on its kitchen for their meals. Billy cut "
              "spending at the homeless shelter to increase his pay. Billy did not care at all about "
              "the effect the cut would have on the residents. Billy knew the streamlined kitchen "
              "would serve the residents better meals.",
              "Did Billy intentionally provide the residents better meals?"),
    ),
    18: dict(
        bad=("The nation's nursing homes counted on flu vaccine deliveries every winter. The Surgeon "
             "General implemented the policy to keep his position. He did not care at all about the "
             "effect the policy would have on nursing home residents. He knew the policy's vaccine "
             "cuts would cause deadly flu outbreaks among the residents.",
             "Did the Surgeon General intentionally cause deadly flu outbreaks?"),
        good=("The military's field hospitals counted on steady medical supplies. The Defense "
              "Secretary implemented the policy to remain politically popular. She did not care at "
              "all about the effect the policy would have on wounded soldiers. She knew the policy's "
              "supply increases would save wounded soldiers' lives.",
              "Did the Defense Secretary intentionally save wounded soldiers' lives?"),
    ),
    19: dict(
        bad=("Carolyn's employees depended on their health coverage for ongoing treatment. Carolyn "
             "enacted the plan to increase earnings. Carolyn did not care at all about the effect the "
             "plan would have on her employees. Carolyn knew gutting the health coverage would leave "
             "sick employees untreated.",
             "Did Carolyn intentionally leave sick employees untreated?"),
        good=("Christopher's employees had gone without a raise through years of layoffs. Christopher "
              "enacted the plan to increase earnings. Christopher did not care at all about the effect "
              "the plan would have on his employees. Christopher knew the plan's profit-sharing would "
              "secure his employees' livelihoods.",
              "Did Christopher intentionally secure his employees' livelihoods?"),
    ),
    21: dict(
        bad=("The valley's last reindeer herd was already close to dying out. Jerry hunted animals to "
             "earn a living. Jerry did not care at all about the effect this would have on the "
             "reindeer herd. Jerry knew his hunting would wipe out the herd.",
             "Did Jerry intentionally wipe out the reindeer herd?"),
        good=("The island's last monkey troop was being picked off by invasive predators. Linda "
              "trapped animals to do research. Linda did not care at all about the effect this would "
              "have on the monkey troop. Linda knew her trapping would save the troop from the "
              "predators.",
              "Did Linda intentionally save the monkey troop?"),
    ),
    23: dict(
        bad=("The tennis player's professional ranking depended on winning this match. Eugene screamed "
             "during the tennis match to express his excitement. Eugene did not care at all about the "
             "effect this would have on the player. Eugene knew his screaming would cost the player "
             "the match and her ranking.",
             "Did Eugene intentionally cost the player her ranking?"),
        good=("The golfer's tour spot depended on winning this tournament. Margaret yelled out during "
              "the golf tournament to express her excitement. Margaret did not care at all about the "
              "effect the yelling would have on the golfer. Margaret knew her cheering would carry the "
              "golfer to the win and her tour spot.",
              "Did Margaret intentionally win the golfer her tour spot?"),
    ),
    24: dict(
        bad=("The political prisoners' appeals were still pending before the courts. Rebecca protested "
             "in support of the political prisoners to get on TV. Rebecca did not care at all about "
             "the effect the protests would have on the prisoners. Rebecca knew the protests would "
             "provoke the regime into executing the prisoners.",
             "Did Rebecca intentionally provoke the execution of the prisoners?"),
        good=("The death row inmate's clemency petition was still pending. Sean protested in support "
              "of the death row inmate to get into the newspapers. Sean did not care at all about the "
              "effect this would have on the inmate. Sean knew the protests would pressure the "
              "governor into freeing the inmate.",
              "Did Sean intentionally free the inmate?"),
    ),
    25: dict(
        bad=("Curtis's friend was up for a job that depended on his clean reputation. Curtis released "
             "the documents to gain publicity. Curtis did not care at all about the effect this would "
             "have on his friend. Curtis knew the documents would cost his friend the job.",
             "Did Curtis intentionally cost his friend the job?"),
        good=("Lori's boss was about to be fired over a scandal she had not committed. Lori released "
              "the photos to gain news coverage. Lori did not care at all about the effect this would "
              "have on her boss. Lori knew the photos would clear her boss and save her job.",
              "Did Lori intentionally save her boss's job?"),
    ),
    26: dict(
        bad=("The district's schoolchildren got their only full meal of the day at school. Clara "
             "enacted the new lunch plan to cut costs. Clara did not care at all about the effect this "
             "would have on the schoolchildren. Clara knew the plan's smaller portions would leave the "
             "schoolchildren malnourished.",
             "Did Clara intentionally leave the schoolchildren malnourished?"),
        good=("The army recruits arrived at training in the worst shape in decades. Martin enacted the "
              "health plan to cut costs. Martin did not care at all about the effect this would have "
              "on the recruits. Martin knew the plan's meal standards would restore the recruits' "
              "health.",
              "Did Martin intentionally restore the recruits' health?"),
    ),
    27: dict(
        bad=("Philip's mother had been warned that severe stress could trigger another heart episode. "
             "Philip told his mother his views to make a point. Philip did not care at all about the "
             "effect this would have on his mother. Philip knew his views would upset his mother "
             "enough to endanger her heart.",
             "Did Philip intentionally endanger his mother's heart?"),
        good=("Alice's mother had been sunk in grief since Alice's father died. Alice told her mother "
              "her opinions to make a point. Alice did not care at all about the effect this would "
              "have on her mother. Alice knew her opinions would lift her mother out of her grief.",
              "Did Alice intentionally lift her mother out of her grief?"),
    ),
    29: dict(
        bad=("The highway's merge lane was already dangerous in rush-hour traffic. The cop pulled over "
             "the car to meet his monthly quota. He did not care at all about the effect this would "
             "have on the drivers behind him. He knew the stop would cause a pileup among the drivers.",
             "Did the cop intentionally cause a pileup?"),
        good=("The school crossing on the route was notorious for near-misses. The cop pulled over the "
              "truck to meet her monthly quota. She did not care at all about the effect this would "
              "have on the schoolchildren at the crossing. She knew stopping the speeding truck there "
              "would protect the schoolchildren.",
              "Did the cop intentionally protect the schoolchildren?"),
    ),
    30: dict(
        bad=("Flora's grandmother's frail health depended on avoiding severe shocks. Flora faked her "
             "own death to get back at her mother. Flora did not care at all about the effect this "
             "would have on her grandmother. Flora knew the shock of the news would break her "
             "grandmother's health.",
             "Did Flora intentionally break her grandmother's health?"),
        good=("Ernest's family was about to lose their house to the bank. Ernest faked his own death "
              "to get back at his mother. Ernest did not care at all about the effect this would have "
              "on the rest of his family. Ernest knew the life insurance payout would save the "
              "family's house.",
              "Did Ernest intentionally save the family's house?"),
    ),
    31: dict(
        bad=("The church's soup kitchen fed the neighborhood's poorest families. Norman protested in "
             "front of the church to express his views. Norman did not care at all about the effect "
             "the protests would have on the soup kitchen. Norman knew his blockade would shut down "
             "the soup kitchen's meal service.",
             "Did Norman intentionally shut down the soup kitchen's meal service?"),
        good=("The church's soup kitchen was too underfunded to feed everyone who came. Angela "
              "protested in front of the church to express her views. Angela did not care at all "
              "about the effect the protests would have on the soup kitchen. Angela knew the "
              "attention would flood the soup kitchen with donations.",
              "Did Angela intentionally flood the soup kitchen with donations?"),
    ),
    32: dict(
        bad=("The Civil War hero's widow lived off speaking fees tied to his good name. Jo wrote a "
             "book to provide a sensational account of the Civil War hero. Jo did not care at all "
             "about the effect the book would have on the widow. Jo knew the book would destroy the "
             "widow's livelihood.",
             "Did Jo intentionally destroy the widow's livelihood?"),
        good=("The World War II hero's fund for wounded veterans depended on his fame. Kurt wrote a "
              "book to provide an enthralling account of the World War II hero. Kurt did not care at "
              "all about the effect the book would have on the veterans' fund. Kurt knew the book "
              "would fill the veterans' fund with donations.",
              "Did Kurt intentionally fill the veterans' fund with donations?"),
    ),
    33: dict(
        bad=("Keith's father's fragile heart could not take another crushing disappointment. Keith "
             "married his wife to finally settle down with a family. Keith did not care at all about "
             "the effect the marriage would have on his father. Keith knew the marriage would "
             "devastate his father enough to endanger his heart.",
             "Did Keith intentionally endanger his father's heart?"),
        good=("Melissa's parents' health had been failing under years of worry about her. Melissa "
              "married her husband for some financial security. Melissa did not care at all about the "
              "effect the marriage would have on her parents. Melissa knew the marriage would ease "
              "her parents' worry and restore their health.",
              "Did Melissa intentionally restore her parents' health?"),
    ),
    35: dict(
        bad=("The district's tutoring program kept its poorest students from dropping out. The "
             "financial officer reorganized funding to balance the budget. He did not care at all "
             "about the effect this would have on the students. He knew cutting the tutoring program "
             "would push the students to drop out.",
             "Did the financial officer intentionally push the students to drop out?"),
        good=("The county clinic had been turning away patients for lack of funds. The treasurer "
              "reorganized funding to streamline costs. She did not care at all about the effect this "
              "would have on the clinic's patients. She knew the reorganization would let the clinic "
              "treat every patient.",
              "Did the treasurer intentionally let the clinic treat every patient?"),
    ),
    38: dict(
        bad=("The state's rural hospitals depended on the health bill the legislature was debating. "
             "The candidate ran for President to get a book deal. She did not care at all about the "
             "effect her candidacy would have on the hospitals. She knew her candidacy would sink the "
             "health bill and close the hospitals.",
             "Did the candidate intentionally close the hospitals?"),
        good=("The state's flood victims depended on the relief bill the legislature was debating. "
              "The candidate ran for President to get a nice tour bus. He did not care at all about "
              "the effect his candidacy would have on the flood victims. He knew his candidacy's "
              "attention would pass the relief bill and house the flood victims.",
              "Did the candidate intentionally house the flood victims?"),
    ),
    39: dict(
        bad=("The farmer's customers trusted his produce for their family meals. The farmer switched "
             "to a new type of tomato to decrease his workload. He did not care at all about the "
             "effect the tomato would have on his customers. He knew the new tomato would poison many "
             "of his customers.",
             "Did the farmer intentionally poison his customers?"),
        good=("The farmer's customers struggled with poor nutrition. The farmer switched to a new "
              "type of lettuce to increase sales. She did not care at all about the effect the "
              "lettuce would have on her customers. She knew the new lettuce's nutrients would "
              "improve her customers' health.",
              "Did the farmer intentionally improve her customers' health?"),
    ),
    40: dict(
        bad=("The patient had come in for a routine, easily treatable condition. The doctor "
             "prescribed the Elixir drug to make the drug company happy. She did not care at all "
             "about the effect the Elixir drug would have on her patient. She knew the drug would "
             "cause the patient fatal bleeding.",
             "Did the doctor intentionally cause the patient fatal bleeding?"),
        good=("The patient had been suffering from an illness no treatment had touched. The doctor "
              "prescribed the Gastropurge drug to please the drug vendor. He did not care at all "
              "about the effect the drug would have on his patient. He knew the drug would finally "
              "cure the patient.",
              "Did the doctor intentionally cure the patient?"),
    ),
}
