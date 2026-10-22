# Review sheet: 16_nm_surv_prudential

Items: `stimuli/nonmoral.csv`, 78 draft items. Checklist: `docs/DEFINITIONS_AND_CHECKLIST.md` section 6.

Record one decision per item in `stimuli/review/16_nm_surv_prudential_decisions.csv`: `approved`, `rejected` or `revise`, your initials as reviewer, the date (YYYY-MM-DD), and a note for every rejected or revise row naming the failed check (e.g. "B4: good version is bigger"). Then run `../../.venv/bin/python -m tools.review apply --items stimuli/nonmoral.csv --decisions stimuli/review/16_nm_surv_prudential_decisions.csv` yourself.

Automated checks (design_problems and tools.lint_stimuli) were clean when this sheet was made.

## Storyline 1: the engineer (nonmoral; storyline checks C1 C2 C3)

### prudential (source pilot; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-001-prudential-bad`

> The engineer released a gadget to make a deadline. The engineer did not care at all about the effect this would have on the engineer's career. The engineer knew the gadget would cost the engineer a promotion.

- agent: `the engineer`
- effect: `cost the engineer a promotion`

**good** `kmp-nm-001-prudential-good`

> The engineer released a gadget to make a deadline. The engineer did not care at all about the effect this would have on the engineer's career. The engineer knew the gadget would earn the engineer a promotion.

- agent: `the engineer`
- effect: `earn the engineer a promotion`

## Storyline 2: the board chair (nonmoral; storyline checks C1 C2 C3)

### prudential (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-002-prudential-bad`

> The board chair started a plan to increase profits. The board chair did not care at all about the effect this would have on the board chair's sleep. The board chair knew the plan would ruin the board chair's sleep.

- agent: `the board chair`
- effect: `ruin the board chair's sleep`

**good** `kmp-nm-002-prudential-good`

> The board chair started a plan to increase profits. The board chair did not care at all about the effect this would have on the board chair's sleep. The board chair knew the plan would improve the board chair's sleep.

- agent: `the board chair`
- effect: `improve the board chair's sleep`

## Storyline 3: the investor (nonmoral; storyline checks C1 C2 C3)

### prudential (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-003-prudential-bad`

> The investor enacted a financial scheme to buy a house. The investor did not care at all about the effect this would have on the investor's stress levels. The investor knew the scheme would raise the investor's stress levels.

- agent: `the investor`
- effect: `raise the investor's stress levels`

**good** `kmp-nm-003-prudential-good`

> The investor enacted a financial scheme to buy a house. The investor did not care at all about the effect this would have on the investor's stress levels. The investor knew the scheme would lower the investor's stress levels.

- agent: `the investor`
- effect: `lower the investor's stress levels`

## Storyline 4: the club owner (nonmoral; storyline checks C1 C2 C3)

### prudential (source pilot; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-004-prudential-bad`

> The club owner renovated the country club to improve its appearance. The club owner did not care at all about the effect this would have on the club owner's personal savings. The club owner knew the renovation would drain the club owner's personal savings.

- agent: `the club owner`
- effect: `drain the club owner's personal savings`

**good** `kmp-nm-004-prudential-good`

> The club owner renovated the country club to improve its appearance. The club owner did not care at all about the effect this would have on the club owner's personal savings. The club owner knew the renovation would grow the club owner's personal savings.

- agent: `the club owner`
- effect: `grow the club owner's personal savings`

## Storyline 5: the mayor (nonmoral; storyline checks C1 C2 C3)

### prudential (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-005-prudential-bad`

> The mayor diverted water to Oldtown to gain votes. The mayor did not care at all about the effect this would have on the mayor's garden. The mayor knew diverting the water would dry out the mayor's garden.

- agent: `the mayor`
- effect: `dry out the mayor's garden`
- capitalised words (R1: names?): Oldtown

**good** `kmp-nm-005-prudential-good`

> The mayor diverted water to Oldtown to gain votes. The mayor did not care at all about the effect this would have on the mayor's garden. The mayor knew diverting the water would revive the mayor's garden.

- agent: `the mayor`
- effect: `revive the mayor's garden`
- capitalised words (R1: names?): Oldtown

## Storyline 6: the plant manager (nonmoral; storyline checks C1 C2 C3)

### prudential (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-006-prudential-bad`

> The plant manager enacted a plan to increase profits. The plant manager did not care at all about the effect this would have on the plant manager's commute. The plant manager knew the plan would lengthen the plant manager's commute.

- agent: `the plant manager`
- effect: `lengthen the plant manager's commute`

**good** `kmp-nm-006-prudential-good`

> The plant manager enacted a plan to increase profits. The plant manager did not care at all about the effect this would have on the plant manager's commute. The plant manager knew the plan would shorten the plant manager's commute.

- agent: `the plant manager`
- effect: `shorten the plant manager's commute`

## Storyline 7: the bomber pilot (nonmoral; storyline checks C1 C2 C3)

### prudential (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-007-prudential-bad`

> The bomber pilot took the long route back to base to save fuel. The bomber pilot did not care at all about the effect this would have on the bomber pilot's chances of promotion. The bomber pilot knew the long route would hurt the bomber pilot's chances of promotion.

- agent: `the bomber pilot`
- effect: `hurt the bomber pilot's chances of promotion`
- log (fresh_action, scenario): '' -> ''. Ngo's action is a wartime bombing; any side effect of it reads as moral (pilot used a fresh domain too)

**good** `kmp-nm-007-prudential-good`

> The bomber pilot took the long route back to base to save fuel. The bomber pilot did not care at all about the effect this would have on the bomber pilot's chances of promotion. The bomber pilot knew the long route would help the bomber pilot's chances of promotion.

- agent: `the bomber pilot`
- effect: `help the bomber pilot's chances of promotion`
- log (fresh_action, scenario): '' -> ''. Ngo's action is a wartime bombing; any side effect of it reads as moral (pilot used a fresh domain too)

## Storyline 8: the university president (nonmoral; storyline checks C1 C2 C3)

### prudential (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-008-prudential-bad`

> The university president enacted a plan to increase business school funding. The university president did not care at all about the effect this would have on the university president's free time. The university president knew the plan would eat into the university president's free time.

- agent: `the university president`
- effect: `eat into the university president's free time`

**good** `kmp-nm-008-prudential-good`

> The university president enacted a plan to increase business school funding. The university president did not care at all about the effect this would have on the university president's free time. The university president knew the plan would free up the university president's free time.

- agent: `the university president`
- effect: `free up the university president's free time`

## Storyline 9: the grower (nonmoral; storyline checks C1 C2 C3)

### prudential (source pilot; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-009-prudential-bad`

> The grower spread weed killer to protect the grower's crops. The grower did not care at all about the effect this would have on the grower's hay fever. The grower knew the weed killer would worsen the grower's hay fever.

- agent: `the grower`
- effect: `worsen the grower's hay fever`

**good** `kmp-nm-009-prudential-good`

> The grower spread weed killer to protect the grower's crops. The grower did not care at all about the effect this would have on the grower's hay fever. The grower knew the weed killer would ease the grower's hay fever.

- agent: `the grower`
- effect: `ease the grower's hay fever`

## Storyline 10: the relative (nonmoral; storyline checks C1 C2 C3)

### prudential (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-010-prudential-bad`

> The relative placed an uncle in a nursing home to avoid being the caretaker. The relative did not care at all about the effect this would have on the relative's savings. The relative knew the placement would drain the relative's savings.

- agent: `the relative`
- effect: `drain the relative's savings`

**good** `kmp-nm-010-prudential-good`

> The relative placed an uncle in a nursing home to avoid being the caretaker. The relative did not care at all about the effect this would have on the relative's savings. The relative knew the placement would grow the relative's savings.

- agent: `the relative`
- effect: `grow the relative's savings`

## Storyline 11: the homeowner (nonmoral; storyline checks C1 C2 C3)

### prudential (source pilot; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-011-prudential-bad`

> The homeowner installed a light display to decorate the homeowner's house. The homeowner did not care at all about the effect this would have on the homeowner's sleep. The homeowner knew the light display would disturb the homeowner's sleep.

- agent: `the homeowner`
- effect: `disturb the homeowner's sleep`

**good** `kmp-nm-011-prudential-good`

> The homeowner installed a light display to decorate the homeowner's house. The homeowner did not care at all about the effect this would have on the homeowner's sleep. The homeowner knew the light display would improve the homeowner's sleep.

- agent: `the homeowner`
- effect: `improve the homeowner's sleep`

## Storyline 12: the scientist (nonmoral; storyline checks C1 C2 C3)

### prudential (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-012-prudential-bad`

> The scientist released a drug to gain profit. The scientist did not care at all about the effect this would have on the scientist's workload. The scientist knew the drug would double the scientist's workload.

- agent: `the scientist`
- effect: `double the scientist's workload`

**good** `kmp-nm-012-prudential-good`

> The scientist released a drug to gain profit. The scientist did not care at all about the effect this would have on the scientist's workload. The scientist knew the drug would halve the scientist's workload.

- agent: `the scientist`
- effect: `halve the scientist's workload`

## Storyline 13: the merchant (nonmoral; storyline checks C1 C2 C3)

### prudential (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-013-prudential-bad`

> The merchant opened a kiosk to make more money. The merchant did not care at all about the effect this would have on the merchant's weekends. The merchant knew the kiosk would take up the merchant's weekends.

- agent: `the merchant`
- effect: `take up the merchant's weekends`

**good** `kmp-nm-013-prudential-good`

> The merchant opened a kiosk to make more money. The merchant did not care at all about the effect this would have on the merchant's weekends. The merchant knew the kiosk would free up the merchant's weekends.

- agent: `the merchant`
- effect: `free up the merchant's weekends`

## Storyline 14: the tenant (nonmoral; storyline checks C1 C2 C3)

### prudential (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-014-prudential-bad`

> The tenant vacuumed to clean the floor. The tenant did not care at all about the effect this would have on the tenant's dust allergy. The tenant knew the vacuuming would worsen the tenant's dust allergy.

- agent: `the tenant`
- effect: `worsen the tenant's dust allergy`

**good** `kmp-nm-014-prudential-good`

> The tenant vacuumed to clean the floor. The tenant did not care at all about the effect this would have on the tenant's dust allergy. The tenant knew the vacuuming would ease the tenant's dust allergy.

- agent: `the tenant`
- effect: `ease the tenant's dust allergy`

## Storyline 15: the student (nonmoral; storyline checks C1 C2 C3)

### prudential (source pilot; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-015-prudential-bad`

> The student threw a party to be more popular. The student did not care at all about the effect this would have on the student's grades. The student knew the party would lower the student's grades.

- agent: `the student`
- effect: `lower the student's grades`

**good** `kmp-nm-015-prudential-good`

> The student threw a party to be more popular. The student did not care at all about the effect this would have on the student's grades. The student knew the party would raise the student's grades.

- agent: `the student`
- effect: `raise the student's grades`

## Storyline 16: the gardener (nonmoral; storyline checks C1 C2 C3)

### prudential (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-016-prudential-bad`

> The gardener planted a tree to decorate the gardener's yard. The gardener did not care at all about the effect this would have on the gardener's water bill. The gardener knew the tree would raise the gardener's water bill.

- agent: `the gardener`
- effect: `raise the gardener's water bill`

**good** `kmp-nm-016-prudential-good`

> The gardener planted a tree to decorate the gardener's yard. The gardener did not care at all about the effect this would have on the gardener's water bill. The gardener knew the tree would lower the gardener's water bill.

- agent: `the gardener`
- effect: `lower the gardener's water bill`

## Storyline 17: the shelter director (nonmoral; storyline checks C1 C2 C3)

### prudential (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-017-prudential-bad`

> The shelter director cut spending at the animal shelter to increase the shelter director's salary. The shelter director did not care at all about the effect this would have on the shelter director's workload. The shelter director knew cutting spending would add to the shelter director's workload.

- agent: `the shelter director`
- effect: `add to the shelter director's workload`

**good** `kmp-nm-017-prudential-good`

> The shelter director cut spending at the animal shelter to increase the shelter director's salary. The shelter director did not care at all about the effect this would have on the shelter director's workload. The shelter director knew cutting spending would lighten the shelter director's workload.

- agent: `the shelter director`
- effect: `lighten the shelter director's workload`

## Storyline 18: the surgeon general (nonmoral; storyline checks C1 C2 C3)

### prudential (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-018-prudential-bad`

> The surgeon general implemented the policy to keep the position. The surgeon general did not care at all about the effect this would have on the surgeon general's stress levels. The surgeon general knew the policy would raise the surgeon general's stress levels.

- agent: `the surgeon general`
- effect: `raise the surgeon general's stress levels`

**good** `kmp-nm-018-prudential-good`

> The surgeon general implemented the policy to keep the position. The surgeon general did not care at all about the effect this would have on the surgeon general's stress levels. The surgeon general knew the policy would lower the surgeon general's stress levels.

- agent: `the surgeon general`
- effect: `lower the surgeon general's stress levels`

## Storyline 19: the employer (nonmoral; storyline checks C1 C2 C3)

### prudential (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-019-prudential-bad`

> The employer enacted the plan to increase earnings. The employer did not care at all about the effect this would have on the employer's working hours. The employer knew the plan would lengthen the employer's working hours.

- agent: `the employer`
- effect: `lengthen the employer's working hours`

**good** `kmp-nm-019-prudential-good`

> The employer enacted the plan to increase earnings. The employer did not care at all about the effect this would have on the employer's working hours. The employer knew the plan would shorten the employer's working hours.

- agent: `the employer`
- effect: `shorten the employer's working hours`

## Storyline 20: the store owner (nonmoral; storyline checks C1 C2 C3)

### prudential (source pilot; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-020-prudential-bad`

> The store owner built a road to increase traffic to the country store. The store owner did not care at all about the effect this would have on the store owner's property taxes. The store owner knew the new road would raise the store owner's property taxes.

- agent: `the store owner`
- effect: `raise the store owner's property taxes`

**good** `kmp-nm-020-prudential-good`

> The store owner built a road to increase traffic to the country store. The store owner did not care at all about the effect this would have on the store owner's property taxes. The store owner knew the new road would lower the store owner's property taxes.

- agent: `the store owner`
- effect: `lower the store owner's property taxes`

## Storyline 21: the hunter (nonmoral; storyline checks C1 C2 C3)

### prudential (source pilot; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-021-prudential-bad`

> The hunter hunted animals to earn a living. The hunter did not care at all about the effect this would have on the hunter's knees. The hunter knew the hunting would wear out the hunter's knees.

- agent: `the hunter`
- effect: `wear out the hunter's knees`

**good** `kmp-nm-021-prudential-good`

> The hunter hunted animals to earn a living. The hunter did not care at all about the effect this would have on the hunter's knees. The hunter knew the hunting would strengthen the hunter's knees.

- agent: `the hunter`
- effect: `strengthen the hunter's knees`

## Storyline 22: the pregnant patient (nonmoral; storyline checks C1 C2 C3)

### prudential (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-022-prudential-bad`

> The pregnant patient decided to induce labor to reduce the pregnancy pains. The pregnant patient did not care at all about the effect this would have on the pregnant patient's recovery time. The pregnant patient knew inducing labor would lengthen the pregnant patient's recovery time.

- agent: `the pregnant patient`
- effect: `lengthen the pregnant patient's recovery time`

**good** `kmp-nm-022-prudential-good`

> The pregnant patient decided to induce labor to reduce the pregnancy pains. The pregnant patient did not care at all about the effect this would have on the pregnant patient's recovery time. The pregnant patient knew inducing labor would shorten the pregnant patient's recovery time.

- agent: `the pregnant patient`
- effect: `shorten the pregnant patient's recovery time`

## Storyline 23: the spectator (nonmoral; storyline checks C1 C2 C3)

### prudential (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-023-prudential-bad`

> The spectator screams during a tennis match to express excitement. The spectator did not care at all about the effect this would have on the spectator's mood. The spectator knew the yelling would sour the spectator's mood.

- agent: `the spectator`
- effect: `sour the spectator's mood`

**good** `kmp-nm-023-prudential-good`

> The spectator screams during a tennis match to express excitement. The spectator did not care at all about the effect this would have on the spectator's mood. The spectator knew the yelling would lift the spectator's mood.

- agent: `the spectator`
- effect: `lift the spectator's mood`

## Storyline 24: the protester (nonmoral; storyline checks C1 C2 C3)

### prudential (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-024-prudential-bad`

> The protester protests in support of political prisoners to get on TV. The protester did not care at all about the effect this would have on the protester's health. The protester knew the protests would weaken the protester's health.

- agent: `the protester`
- effect: `weaken the protester's health`
- capitalised words (R1: names?): TV

**good** `kmp-nm-024-prudential-good`

> The protester protests in support of political prisoners to get on TV. The protester did not care at all about the effect this would have on the protester's health. The protester knew the protests would strengthen the protester's health.

- agent: `the protester`
- effect: `strengthen the protester's health`
- capitalised words (R1: names?): TV

## Storyline 25: the blogger (nonmoral; storyline checks C1 C2 C3)

### prudential (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-025-prudential-bad`

> The blogger released the documents to gain publicity. The blogger did not care at all about the effect this would have on the blogger's income. The blogger knew the documents would cut the blogger's income.

- agent: `the blogger`
- effect: `cut the blogger's income`

**good** `kmp-nm-025-prudential-good`

> The blogger released the documents to gain publicity. The blogger did not care at all about the effect this would have on the blogger's income. The blogger knew the documents would raise the blogger's income.

- agent: `the blogger`
- effect: `raise the blogger's income`

## Storyline 26: the school administrator (nonmoral; storyline checks C1 C2 C3)

### prudential (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-026-prudential-bad`

> The school administrator enacted the new lunch plan to cut costs. The school administrator did not care at all about the effect this would have on the school administrator's lunch breaks. The school administrator knew the new lunch plan would shorten the school administrator's lunch breaks.

- agent: `the school administrator`
- effect: `shorten the school administrator's lunch breaks`

**good** `kmp-nm-026-prudential-good`

> The school administrator enacted the new lunch plan to cut costs. The school administrator did not care at all about the effect this would have on the school administrator's lunch breaks. The school administrator knew the new lunch plan would lengthen the school administrator's lunch breaks.

- agent: `the school administrator`
- effect: `lengthen the school administrator's lunch breaks`

## Storyline 27: the adult child (nonmoral; storyline checks C1 C2 C3)

### prudential (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-027-prudential-bad`

> The adult child told the mother the adult child's views to make a point. The adult child did not care at all about the effect this would have on the adult child's peace of mind. The adult child knew telling the views would spoil the adult child's peace of mind.

- agent: `the adult child`
- effect: `spoil the adult child's peace of mind`

**good** `kmp-nm-027-prudential-good`

> The adult child told the mother the adult child's views to make a point. The adult child did not care at all about the effect this would have on the adult child's peace of mind. The adult child knew telling the views would restore the adult child's peace of mind.

- agent: `the adult child`
- effect: `restore the adult child's peace of mind`

## Storyline 28: the dog owner (nonmoral; storyline checks C1 C2 C3)

### prudential (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-028-prudential-bad`

> The dog owner walked the puppy at dawn to beat the heat. The dog owner did not care at all about the effect this would have on the dog owner's knees. The dog owner knew the walks would strain the dog owner's knees.

- agent: `the dog owner`
- effect: `strain the dog owner's knees`
- log (fresh_action, scenario): '' -> ''. Ngo's action (smacking the puppy) is itself wrongdoing, which the reviewer reads instead of the self-regarding effect (DEFINITIONS §4.2 Out)

**good** `kmp-nm-028-prudential-good`

> The dog owner walked the puppy at dawn to beat the heat. The dog owner did not care at all about the effect this would have on the dog owner's knees. The dog owner knew the walks would strengthen the dog owner's knees.

- agent: `the dog owner`
- effect: `strengthen the dog owner's knees`
- log (fresh_action, scenario): '' -> ''. Ngo's action (smacking the puppy) is itself wrongdoing, which the reviewer reads instead of the self-regarding effect (DEFINITIONS §4.2 Out)

## Storyline 29: the cop (nonmoral; storyline checks C1 C2 C3)

### prudential (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-029-prudential-bad`

> The cop pulled over the car to meet the monthly quota. The cop did not care at all about the effect this would have on the cop's lunch break. The cop knew pulling over the car would cut short the cop's lunch break.

- agent: `the cop`
- effect: `cut short the cop's lunch break`

**good** `kmp-nm-029-prudential-good`

> The cop pulled over the car to meet the monthly quota. The cop did not care at all about the effect this would have on the cop's lunch break. The cop knew pulling over the car would extend the cop's lunch break.

- agent: `the cop`
- effect: `extend the cop's lunch break`

## Storyline 30: the policyholder (nonmoral; storyline checks C1 C2 C3)

### prudential (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-030-prudential-bad`

> The policyholder switched to a cheaper insurance plan to save money. The policyholder did not care at all about the effect this would have on the policyholder's wait to see a doctor. The policyholder knew the new plan would lengthen the policyholder's wait to see a doctor.

- agent: `the policyholder`
- effect: `lengthen the policyholder's wait to see a doctor`
- log (fresh_action, scenario): '' -> ''. Ngo's action (faking a death) is itself fraud, which the reviewer reads instead of the self-regarding effect (DEFINITIONS §4.2 Out; pilot pair 30 failed)

**good** `kmp-nm-030-prudential-good`

> The policyholder switched to a cheaper insurance plan to save money. The policyholder did not care at all about the effect this would have on the policyholder's wait to see a doctor. The policyholder knew the new plan would shorten the policyholder's wait to see a doctor.

- agent: `the policyholder`
- effect: `shorten the policyholder's wait to see a doctor`
- log (fresh_action, scenario): '' -> ''. Ngo's action (faking a death) is itself fraud, which the reviewer reads instead of the self-regarding effect (DEFINITIONS §4.2 Out; pilot pair 30 failed)

## Storyline 31: the resident (nonmoral; storyline checks C1 C2 C3)

### prudential (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-031-prudential-bad`

> The resident protested in front of the church to express the resident's views. The resident did not care at all about the effect this would have on the resident's standing in the neighborhood. The resident knew the protests would hurt the resident's standing in the neighborhood.

- agent: `the resident`
- effect: `hurt the resident's standing in the neighborhood`

**good** `kmp-nm-031-prudential-good`

> The resident protested in front of the church to express the resident's views. The resident did not care at all about the effect this would have on the resident's standing in the neighborhood. The resident knew the protests would raise the resident's standing in the neighborhood.

- agent: `the resident`
- effect: `raise the resident's standing in the neighborhood`

## Storyline 32: the author (nonmoral; storyline checks C1 C2 C3)

### prudential (source pilot; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-032-prudential-bad`

> The author wrote a book to provide a sensational account of the Civil War hero. The author did not care at all about the effect this would have on the author's reputation. The author knew the book would damage the author's reputation.

- agent: `the author`
- effect: `damage the author's reputation`
- capitalised words (R1: names?): Civil, War

**good** `kmp-nm-032-prudential-good`

> The author wrote a book to provide a sensational account of the Civil War hero. The author did not care at all about the effect this would have on the author's reputation. The author knew the book would boost the author's reputation.

- agent: `the author`
- effect: `boost the author's reputation`
- capitalised words (R1: names?): Civil, War

## Storyline 34: the activist (nonmoral; storyline checks C1 C2 C3)

### prudential (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-034-prudential-bad`

> The activist moved the group's meetings to a downtown hall to reach more people. The activist did not care at all about the effect this would have on the activist's evenings. The activist knew the move would take up the activist's evenings.

- agent: `the activist`
- effect: `take up the activist's evenings`
- log (fresh_action, scenario): '' -> ''. Ngo's action (a bomb threat) is itself wrongdoing (DEFINITIONS §4.2 Out; pilot used a fresh domain too)

**good** `kmp-nm-034-prudential-good`

> The activist moved the group's meetings to a downtown hall to reach more people. The activist did not care at all about the effect this would have on the activist's evenings. The activist knew the move would free up the activist's evenings.

- agent: `the activist`
- effect: `free up the activist's evenings`
- log (fresh_action, scenario): '' -> ''. Ngo's action (a bomb threat) is itself wrongdoing (DEFINITIONS §4.2 Out; pilot used a fresh domain too)

## Storyline 35: the financial officer (nonmoral; storyline checks C1 C2 C3)

### prudential (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-035-prudential-bad`

> The financial officer reorganized funding to balance the budget. The financial officer did not care at all about the effect this would have on the financial officer's workload. The financial officer knew the new system would increase the financial officer's workload.

- agent: `the financial officer`
- effect: `increase the financial officer's workload`

**good** `kmp-nm-035-prudential-good`

> The financial officer reorganized funding to balance the budget. The financial officer did not care at all about the effect this would have on the financial officer's workload. The financial officer knew the new system would reduce the financial officer's workload.

- agent: `the financial officer`
- effect: `reduce the financial officer's workload`

## Storyline 36: the product designer (nonmoral; storyline checks C1 C2 C3)

### prudential (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-036-prudential-bad`

> The product designer revised the tablet computer to increase sales. The product designer did not care at all about the effect this would have on the product designer's eyes. The product designer knew the revision would strain the product designer's eyes.

- agent: `the product designer`
- effect: `strain the product designer's eyes`

**good** `kmp-nm-036-prudential-good`

> The product designer revised the tablet computer to increase sales. The product designer did not care at all about the effect this would have on the product designer's eyes. The product designer knew the revision would rest the product designer's eyes.

- agent: `the product designer`
- effect: `rest the product designer's eyes`

## Storyline 37: the cult leader (nonmoral; storyline checks C1 C2 C3)

### prudential (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-037-prudential-bad`

> The cult leader moved into a mountain cabin to have more privacy. The cult leader did not care at all about the effect this would have on the cult leader's health. The cult leader knew the move would harm the cult leader's health.

- agent: `the cult leader`
- effect: `harm the cult leader's health`
- log (fresh_action, scenario): '' -> ''. Ngo's action is the cult's declaration, which reaches the followers (pilot used a fresh domain too)

**good** `kmp-nm-037-prudential-good`

> The cult leader moved into a mountain cabin to have more privacy. The cult leader did not care at all about the effect this would have on the cult leader's health. The cult leader knew the move would improve the cult leader's health.

- agent: `the cult leader`
- effect: `improve the cult leader's health`
- log (fresh_action, scenario): '' -> ''. Ngo's action is the cult's declaration, which reaches the followers (pilot used a fresh domain too)

## Storyline 38: the candidate (nonmoral; storyline checks C1 C2 C3)

### prudential (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-038-prudential-bad`

> The candidate ran for President to get a book deal. The candidate did not care at all about the effect this would have on the candidate's fitness. The candidate knew the candidacy would worsen the candidate's fitness.

- agent: `the candidate`
- effect: `worsen the candidate's fitness`
- capitalised words (R1: names?): President

**good** `kmp-nm-038-prudential-good`

> The candidate ran for President to get a book deal. The candidate did not care at all about the effect this would have on the candidate's fitness. The candidate knew the candidacy would improve the candidate's fitness.

- agent: `the candidate`
- effect: `improve the candidate's fitness`
- capitalised words (R1: names?): President

## Storyline 39: the farmer (nonmoral; storyline checks C1 C2 C3)

### prudential (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-039-prudential-bad`

> The farmer switched to a new type of tomato to decrease the farmer's workload. The farmer did not care at all about the effect this would have on the farmer's health. The farmer knew the new tomato would worsen the farmer's health.

- agent: `the farmer`
- effect: `worsen the farmer's health`

**good** `kmp-nm-039-prudential-good`

> The farmer switched to a new type of tomato to decrease the farmer's workload. The farmer did not care at all about the effect this would have on the farmer's health. The farmer knew the new tomato would improve the farmer's health.

- agent: `the farmer`
- effect: `improve the farmer's health`

## Storyline 40: the doctor (nonmoral; storyline checks C1 C2 C3)

### prudential (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-040-prudential-bad`

> The doctor switched to the night shift to have quieter hours. The doctor did not care at all about the effect this would have on the doctor's commute. The doctor knew the switch would lengthen the doctor's commute.

- agent: `the doctor`
- effect: `lengthen the doctor's commute`
- log (fresh_action, scenario): '' -> ''. Ngo's action (prescribing to please a drug company) is itself a breach of medical ethics (DEFINITIONS §4.2 Out)

**good** `kmp-nm-040-prudential-good`

> The doctor switched to the night shift to have quieter hours. The doctor did not care at all about the effect this would have on the doctor's commute. The doctor knew the switch would shorten the doctor's commute.

- agent: `the doctor`
- effect: `shorten the doctor's commute`
- log (fresh_action, scenario): '' -> ''. Ngo's action (prescribing to please a drug company) is itself a breach of medical ethics (DEFINITIONS §4.2 Out)

