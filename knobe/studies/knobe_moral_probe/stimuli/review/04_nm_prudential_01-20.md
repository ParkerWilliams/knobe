# Review sheet: 04_nm_prudential_01-20

Items: `stimuli/nonmoral.csv`, 40 draft items. Checklist: `docs/DEFINITIONS_AND_CHECKLIST.md` section 6.

Record one decision per item in `stimuli/review/04_nm_prudential_01-20_decisions.csv`: `approved`, `rejected` or `revise`, your initials as reviewer, the date (YYYY-MM-DD), and a note for every rejected or revise row naming the failed check (e.g. "B4: good version is bigger"). Then run `../../.venv/bin/python -m tools.review apply --items stimuli/nonmoral.csv --decisions stimuli/review/04_nm_prudential_01-20_decisions.csv` yourself.

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

