# Review sheet: 17_nm_surv_procedural

Items: `stimuli/nonmoral.csv`, 76 draft items. Checklist: `docs/DEFINITIONS_AND_CHECKLIST.md` section 6.

Record one decision per item in `stimuli/review/17_nm_surv_procedural_decisions.csv`: `approved`, `rejected` or `revise`, your initials as reviewer, the date (YYYY-MM-DD), and a note for every rejected or revise row naming the failed check (e.g. "B4: good version is bigger"). Then run `../../.venv/bin/python -m tools.review apply --items stimuli/nonmoral.csv --decisions stimuli/review/17_nm_surv_procedural_decisions.csv` yourself.

Automated checks (design_problems and tools.lint_stimuli) were clean when this sheet was made.

## Storyline 1: the engineer (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-001-procedural-bad`

> The engineer released a gadget to make a deadline. The engineer did not care at all about the effect this would have on the product line's naming scheme. The engineer knew the gadget would break the product line's naming scheme.

- agent: `the engineer`
- effect: `break the product line's naming scheme`

**good** `kmp-nm-001-procedural-good`

> The engineer released a gadget to make a deadline. The engineer did not care at all about the effect this would have on the product line's naming scheme. The engineer knew the gadget would fit the product line's naming scheme exactly.

- agent: `the engineer`
- effect: `fit the product line's naming scheme exactly`

## Storyline 2: the board chair (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-002-procedural-bad`

> The board chair started a plan to increase profits. The board chair did not care at all about the effect this would have on the company's format for planning documents. The board chair knew the plan would break the company's format for planning documents.

- agent: `the board chair`
- effect: `break the company's format for planning documents`

**good** `kmp-nm-002-procedural-good`

> The board chair started a plan to increase profits. The board chair did not care at all about the effect this would have on the company's format for planning documents. The board chair knew the plan would fit the company's format for planning documents exactly.

- agent: `the board chair`
- effect: `fit the company's format for planning documents exactly`

## Storyline 3: the investor (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-003-procedural-bad`

> The investor enacted a financial scheme to buy a house. The investor did not care at all about the effect this would have on the bank's account-numbering convention. The investor knew the scheme would break the bank's account-numbering convention.

- agent: `the investor`
- effect: `break the bank's account-numbering convention`

**good** `kmp-nm-003-procedural-good`

> The investor enacted a financial scheme to buy a house. The investor did not care at all about the effect this would have on the bank's account-numbering convention. The investor knew the scheme would fit the bank's account-numbering convention exactly.

- agent: `the investor`
- effect: `fit the bank's account-numbering convention exactly`

## Storyline 4: the club owner (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-004-procedural-bad`

> The club owner renovated the country club to improve its appearance. The club owner did not care at all about the effect this would have on the club's color scheme. The club owner knew the renovation would break the club's color scheme.

- agent: `the club owner`
- effect: `break the club's color scheme`

**good** `kmp-nm-004-procedural-good`

> The club owner renovated the country club to improve its appearance. The club owner did not care at all about the effect this would have on the club's color scheme. The club owner knew the renovation would complete the club's color scheme.

- agent: `the club owner`
- effect: `complete the club's color scheme`

## Storyline 5: the mayor (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-005-procedural-bad`

> The mayor diverted water to Oldtown to gain votes. The mayor did not care at all about the effect this would have on the county's naming convention for canals. The mayor knew diverting the water would break the county's naming convention for canals.

- agent: `the mayor`
- effect: `break the county's naming convention for canals`
- capitalised words (R1: names?): Oldtown

**good** `kmp-nm-005-procedural-good`

> The mayor diverted water to Oldtown to gain votes. The mayor did not care at all about the effect this would have on the county's naming convention for canals. The mayor knew diverting the water would fit the county's naming convention for canals exactly.

- agent: `the mayor`
- effect: `fit the county's naming convention for canals exactly`
- capitalised words (R1: names?): Oldtown

## Storyline 6: the plant manager (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-006-procedural-bad`

> The plant manager enacted a plan to increase profits. The plant manager did not care at all about the effect this would have on the plant's shift-naming scheme. The plant manager knew the plan would break the plant's shift-naming scheme.

- agent: `the plant manager`
- effect: `break the plant's shift-naming scheme`

**good** `kmp-nm-006-procedural-good`

> The plant manager enacted a plan to increase profits. The plant manager did not care at all about the effect this would have on the plant's shift-naming scheme. The plant manager knew the plan would fit the plant's shift-naming scheme exactly.

- agent: `the plant manager`
- effect: `fit the plant's shift-naming scheme exactly`

## Storyline 7: the bomber pilot (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-007-procedural-bad`

> The bomber pilot took the long route back to base to save fuel. The bomber pilot did not care at all about the effect this would have on the flight log's format. The bomber pilot knew the long route would break the flight log's format.

- agent: `the bomber pilot`
- effect: `break the flight log's format`
- log (fresh_action, scenario): '' -> ''. Ngo's action is a wartime bombing; any side effect of it reads as moral (same fresh action as the prudential pair)

**good** `kmp-nm-007-procedural-good`

> The bomber pilot took the long route back to base to save fuel. The bomber pilot did not care at all about the effect this would have on the flight log's format. The bomber pilot knew the long route would fit the flight log's format exactly.

- agent: `the bomber pilot`
- effect: `fit the flight log's format exactly`
- log (fresh_action, scenario): '' -> ''. Ngo's action is a wartime bombing; any side effect of it reads as moral (same fresh action as the prudential pair)

## Storyline 8: the university president (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-008-procedural-bad`

> The university president enacted a plan to increase business school funding. The university president did not care at all about the effect this would have on the budget's color-coding scheme. The university president knew the plan would break the budget's color-coding scheme.

- agent: `the university president`
- effect: `break the budget's color-coding scheme`

**good** `kmp-nm-008-procedural-good`

> The university president enacted a plan to increase business school funding. The university president did not care at all about the effect this would have on the budget's color-coding scheme. The university president knew the plan would fit the budget's color-coding scheme exactly.

- agent: `the university president`
- effect: `fit the budget's color-coding scheme exactly`

## Storyline 9: the grower (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-009-procedural-bad`

> The grower spread weed killer to protect the grower's crops. The grower did not care at all about the effect this would have on the farm's color code for treated fields. The grower knew the weed killer would break the farm's color code for treated fields.

- agent: `the grower`
- effect: `break the farm's color code for treated fields`

**good** `kmp-nm-009-procedural-good`

> The grower spread weed killer to protect the grower's crops. The grower did not care at all about the effect this would have on the farm's color code for treated fields. The grower knew the weed killer would fit the farm's color code for treated fields exactly.

- agent: `the grower`
- effect: `fit the farm's color code for treated fields exactly`

## Storyline 10: the relative (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-010-procedural-bad`

> The relative placed an uncle in a nursing home to avoid being the caretaker. The relative did not care at all about the effect this would have on the nursing home's room-numbering scheme. The relative knew the placement would break the nursing home's room-numbering scheme.

- agent: `the relative`
- effect: `break the nursing home's room-numbering scheme`

**good** `kmp-nm-010-procedural-good`

> The relative placed an uncle in a nursing home to avoid being the caretaker. The relative did not care at all about the effect this would have on the nursing home's room-numbering scheme. The relative knew the placement would fit the nursing home's room-numbering scheme exactly.

- agent: `the relative`
- effect: `fit the nursing home's room-numbering scheme exactly`

## Storyline 11: the homeowner (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-011-procedural-bad`

> The homeowner installed a light display to decorate the homeowner's house. The homeowner did not care at all about the effect this would have on the street's color scheme for holiday lights. The homeowner knew the light display would break the street's color scheme for holiday lights.

- agent: `the homeowner`
- effect: `break the street's color scheme for holiday lights`

**good** `kmp-nm-011-procedural-good`

> The homeowner installed a light display to decorate the homeowner's house. The homeowner did not care at all about the effect this would have on the street's color scheme for holiday lights. The homeowner knew the light display would fit the street's color scheme for holiday lights exactly.

- agent: `the homeowner`
- effect: `fit the street's color scheme for holiday lights exactly`

## Storyline 12: the scientist (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-012-procedural-bad`

> The scientist released a drug to gain profit. The scientist did not care at all about the effect this would have on the lab's naming convention for drugs. The scientist knew the drug would break the lab's naming convention for drugs.

- agent: `the scientist`
- effect: `break the lab's naming convention for drugs`

**good** `kmp-nm-012-procedural-good`

> The scientist released a drug to gain profit. The scientist did not care at all about the effect this would have on the lab's naming convention for drugs. The scientist knew the drug would fit the lab's naming convention for drugs exactly.

- agent: `the scientist`
- effect: `fit the lab's naming convention for drugs exactly`

## Storyline 13: the merchant (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-013-procedural-bad`

> The merchant opened a kiosk to make more money. The merchant did not care at all about the effect this would have on the market's sign format. The merchant knew the kiosk would break the market's sign format.

- agent: `the merchant`
- effect: `break the market's sign format`

**good** `kmp-nm-013-procedural-good`

> The merchant opened a kiosk to make more money. The merchant did not care at all about the effect this would have on the market's sign format. The merchant knew the kiosk would fit the market's sign format exactly.

- agent: `the merchant`
- effect: `fit the market's sign format exactly`

## Storyline 14: the tenant (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-014-procedural-bad`

> The tenant vacuumed to clean the floor. The tenant did not care at all about the effect this would have on the building's chore chart. The tenant knew the vacuuming would break the building's chore chart.

- agent: `the tenant`
- effect: `break the building's chore chart`

**good** `kmp-nm-014-procedural-good`

> The tenant vacuumed to clean the floor. The tenant did not care at all about the effect this would have on the building's chore chart. The tenant knew the vacuuming would fit the building's chore chart exactly.

- agent: `the tenant`
- effect: `fit the building's chore chart exactly`

## Storyline 15: the student (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-015-procedural-bad`

> The student threw a party to be more popular. The student did not care at all about the effect this would have on the dorm's naming scheme for parties. The student knew the party would break the dorm's naming scheme for parties.

- agent: `the student`
- effect: `break the dorm's naming scheme for parties`

**good** `kmp-nm-015-procedural-good`

> The student threw a party to be more popular. The student did not care at all about the effect this would have on the dorm's naming scheme for parties. The student knew the party would fit the dorm's naming scheme for parties exactly.

- agent: `the student`
- effect: `fit the dorm's naming scheme for parties exactly`

## Storyline 17: the shelter director (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-017-procedural-bad`

> The shelter director cut spending at the animal shelter to increase the shelter director's salary. The shelter director did not care at all about the effect this would have on the shelter's budget-coding scheme. The shelter director knew cutting spending would break the shelter's budget-coding scheme.

- agent: `the shelter director`
- effect: `break the shelter's budget-coding scheme`

**good** `kmp-nm-017-procedural-good`

> The shelter director cut spending at the animal shelter to increase the shelter director's salary. The shelter director did not care at all about the effect this would have on the shelter's budget-coding scheme. The shelter director knew cutting spending would fit the shelter's budget-coding scheme exactly.

- agent: `the shelter director`
- effect: `fit the shelter's budget-coding scheme exactly`

## Storyline 18: the surgeon general (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-018-procedural-bad`

> The surgeon general implemented the policy to keep the position. The surgeon general did not care at all about the effect this would have on the department's policy-numbering scheme. The surgeon general knew the policy would break the department's policy-numbering scheme.

- agent: `the surgeon general`
- effect: `break the department's policy-numbering scheme`

**good** `kmp-nm-018-procedural-good`

> The surgeon general implemented the policy to keep the position. The surgeon general did not care at all about the effect this would have on the department's policy-numbering scheme. The surgeon general knew the policy would fit the department's policy-numbering scheme exactly.

- agent: `the surgeon general`
- effect: `fit the department's policy-numbering scheme exactly`

## Storyline 19: the employer (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-019-procedural-bad`

> The employer enacted the plan to increase earnings. The employer did not care at all about the effect this would have on the company's memo format. The employer knew the plan would break the company's memo format.

- agent: `the employer`
- effect: `break the company's memo format`

**good** `kmp-nm-019-procedural-good`

> The employer enacted the plan to increase earnings. The employer did not care at all about the effect this would have on the company's memo format. The employer knew the plan would fit the company's memo format exactly.

- agent: `the employer`
- effect: `fit the company's memo format exactly`

## Storyline 20: the store owner (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-020-procedural-bad`

> The store owner built a road to increase traffic to the country store. The store owner did not care at all about the effect this would have on the county's road-naming pattern. The store owner knew the new road would break the county's road-naming pattern.

- agent: `the store owner`
- effect: `break the county's road-naming pattern`

**good** `kmp-nm-020-procedural-good`

> The store owner built a road to increase traffic to the country store. The store owner did not care at all about the effect this would have on the county's road-naming pattern. The store owner knew the new road would fit the county's road-naming pattern exactly.

- agent: `the store owner`
- effect: `fit the county's road-naming pattern exactly`

## Storyline 21: the hunter (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-021-procedural-bad`

> The hunter hunted animals to earn a living. The hunter did not care at all about the effect this would have on the lodge's color code for hunting tags. The hunter knew the hunting would break the lodge's color code for hunting tags.

- agent: `the hunter`
- effect: `break the lodge's color code for hunting tags`

**good** `kmp-nm-021-procedural-good`

> The hunter hunted animals to earn a living. The hunter did not care at all about the effect this would have on the lodge's color code for hunting tags. The hunter knew the hunting would fit the lodge's color code for hunting tags exactly.

- agent: `the hunter`
- effect: `fit the lodge's color code for hunting tags exactly`

## Storyline 22: the pregnant patient (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-022-procedural-bad`

> The pregnant patient repainted the front door to brighten the house. The pregnant patient did not care at all about the effect this would have on the street's color scheme for front doors. The pregnant patient knew the new paint would break the street's color scheme for front doors.

- agent: `the pregnant patient`
- effect: `break the street's color scheme for front doors`
- log (fresh_action, scenario): '' -> ''. no arbitrary convention plausibly follows from inducing labor, and the action involves the baby's welfare

**good** `kmp-nm-022-procedural-good`

> The pregnant patient repainted the front door to brighten the house. The pregnant patient did not care at all about the effect this would have on the street's color scheme for front doors. The pregnant patient knew the new paint would fit the street's color scheme for front doors exactly.

- agent: `the pregnant patient`
- effect: `fit the street's color scheme for front doors exactly`
- log (fresh_action, scenario): '' -> ''. no arbitrary convention plausibly follows from inducing labor, and the action involves the baby's welfare

## Storyline 23: the spectator (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-023-procedural-bad`

> The spectator wore a team scarf to the tennis match to stay warm. The spectator did not care at all about the effect this would have on the fan section's color scheme. The spectator knew the scarf would break the fan section's color scheme.

- agent: `the spectator`
- effect: `break the fan section's color scheme`
- log (fresh_action, scenario): '' -> ''. the conventions screaming breaks at a match (quiet during play) protect the players, which is moral (DEFINITIONS §4.3 Out)

**good** `kmp-nm-023-procedural-good`

> The spectator wore a team scarf to the tennis match to stay warm. The spectator did not care at all about the effect this would have on the fan section's color scheme. The spectator knew the scarf would fit the fan section's color scheme exactly.

- agent: `the spectator`
- effect: `fit the fan section's color scheme exactly`
- log (fresh_action, scenario): '' -> ''. the conventions screaming breaks at a match (quiet during play) protect the players, which is moral (DEFINITIONS §4.3 Out)

## Storyline 24: the protester (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-024-procedural-bad`

> The protester protests in support of political prisoners to get on TV. The protester did not care at all about the effect this would have on the rally's sign format. The protester knew the protests would break the rally's sign format.

- agent: `the protester`
- effect: `break the rally's sign format`
- capitalised words (R1: names?): TV

**good** `kmp-nm-024-procedural-good`

> The protester protests in support of political prisoners to get on TV. The protester did not care at all about the effect this would have on the rally's sign format. The protester knew the protests would fit the rally's sign format exactly.

- agent: `the protester`
- effect: `fit the rally's sign format exactly`
- capitalised words (R1: names?): TV

## Storyline 25: the blogger (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-025-procedural-bad`

> The blogger released the documents to gain publicity. The blogger did not care at all about the effect this would have on the archive's file-naming convention. The blogger knew the documents would break the archive's file-naming convention.

- agent: `the blogger`
- effect: `break the archive's file-naming convention`

**good** `kmp-nm-025-procedural-good`

> The blogger released the documents to gain publicity. The blogger did not care at all about the effect this would have on the archive's file-naming convention. The blogger knew the documents would fit the archive's file-naming convention exactly.

- agent: `the blogger`
- effect: `fit the archive's file-naming convention exactly`

## Storyline 26: the school administrator (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-026-procedural-bad`

> The school administrator enacted the new lunch plan to cut costs. The school administrator did not care at all about the effect this would have on the school's menu format. The school administrator knew the new lunch plan would break the school's menu format.

- agent: `the school administrator`
- effect: `break the school's menu format`

**good** `kmp-nm-026-procedural-good`

> The school administrator enacted the new lunch plan to cut costs. The school administrator did not care at all about the effect this would have on the school's menu format. The school administrator knew the new lunch plan would fit the school's menu format exactly.

- agent: `the school administrator`
- effect: `fit the school's menu format exactly`

## Storyline 27: the adult child (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-027-procedural-bad`

> The adult child hung a new photo in the hallway to fill a blank spot. The adult child did not care at all about the effect this would have on the hallway's frame pattern. The adult child knew the new photo would break the hallway's frame pattern.

- agent: `the adult child`
- effect: `break the hallway's frame pattern`
- log (fresh_action, scenario): '' -> ''. no arbitrary convention plausibly follows from telling the mother the adult child's views

**good** `kmp-nm-027-procedural-good`

> The adult child hung a new photo in the hallway to fill a blank spot. The adult child did not care at all about the effect this would have on the hallway's frame pattern. The adult child knew the new photo would complete the hallway's frame pattern.

- agent: `the adult child`
- effect: `complete the hallway's frame pattern`
- log (fresh_action, scenario): '' -> ''. no arbitrary convention plausibly follows from telling the mother the adult child's views

## Storyline 28: the dog owner (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-028-procedural-bad`

> The dog owner bought the puppy a new collar to replace a worn one. The dog owner did not care at all about the effect this would have on the dog club's collar color scheme. The dog owner knew the new collar would break the dog club's collar color scheme.

- agent: `the dog owner`
- effect: `break the dog club's collar color scheme`
- log (fresh_action, scenario): '' -> ''. Ngo's action (smacking the puppy) is itself wrongdoing; a convention also has to follow from the action

**good** `kmp-nm-028-procedural-good`

> The dog owner bought the puppy a new collar to replace a worn one. The dog owner did not care at all about the effect this would have on the dog club's collar color scheme. The dog owner knew the new collar would fit the dog club's collar color scheme exactly.

- agent: `the dog owner`
- effect: `fit the dog club's collar color scheme exactly`
- log (fresh_action, scenario): '' -> ''. Ngo's action (smacking the puppy) is itself wrongdoing; a convention also has to follow from the action

## Storyline 29: the cop (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-029-procedural-bad`

> The cop pulled over the car to meet the monthly quota. The cop did not care at all about the effect this would have on the precinct's numbering scheme for reports. The cop knew pulling over the car would break the precinct's numbering scheme for reports.

- agent: `the cop`
- effect: `break the precinct's numbering scheme for reports`

**good** `kmp-nm-029-procedural-good`

> The cop pulled over the car to meet the monthly quota. The cop did not care at all about the effect this would have on the precinct's numbering scheme for reports. The cop knew pulling over the car would fit the precinct's numbering scheme for reports exactly.

- agent: `the cop`
- effect: `fit the precinct's numbering scheme for reports exactly`

## Storyline 30: the policyholder (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-030-procedural-bad`

> The policyholder switched to a cheaper insurance plan to save money. The policyholder did not care at all about the effect this would have on the insurer's policy-numbering scheme. The policyholder knew the new plan would break the insurer's policy-numbering scheme.

- agent: `the policyholder`
- effect: `break the insurer's policy-numbering scheme`
- log (fresh_action, scenario): '' -> ''. Ngo's action (faking a death) is itself fraud (same fresh action as the prudential pair)

**good** `kmp-nm-030-procedural-good`

> The policyholder switched to a cheaper insurance plan to save money. The policyholder did not care at all about the effect this would have on the insurer's policy-numbering scheme. The policyholder knew the new plan would fit the insurer's policy-numbering scheme exactly.

- agent: `the policyholder`
- effect: `fit the insurer's policy-numbering scheme exactly`
- log (fresh_action, scenario): '' -> ''. Ngo's action (faking a death) is itself fraud (same fresh action as the prudential pair)

## Storyline 31: the resident (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-031-procedural-bad`

> The resident protested in front of the church to express the resident's views. The resident did not care at all about the effect this would have on the square's color scheme for banners. The resident knew the protests would break the square's color scheme for banners.

- agent: `the resident`
- effect: `break the square's color scheme for banners`

**good** `kmp-nm-031-procedural-good`

> The resident protested in front of the church to express the resident's views. The resident did not care at all about the effect this would have on the square's color scheme for banners. The resident knew the protests would fit the square's color scheme for banners exactly.

- agent: `the resident`
- effect: `fit the square's color scheme for banners exactly`

## Storyline 32: the author (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-032-procedural-bad`

> The author wrote a book to provide a sensational account of the Civil War hero. The author did not care at all about the effect this would have on the series' cover design. The author knew the book would break the series' cover design.

- agent: `the author`
- effect: `break the series' cover design`
- capitalised words (R1: names?): Civil, War

**good** `kmp-nm-032-procedural-good`

> The author wrote a book to provide a sensational account of the Civil War hero. The author did not care at all about the effect this would have on the series' cover design. The author knew the book would fit the series' cover design exactly.

- agent: `the author`
- effect: `fit the series' cover design exactly`
- capitalised words (R1: names?): Civil, War

## Storyline 33: the newlywed (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-033-procedural-bad`

> The newlywed married their wife to finally settle down with a family. The newlywed did not care at all about the effect this would have on the family's naming convention. The newlywed knew the marriage would break the family's naming convention.

- agent: `the newlywed`
- effect: `break the family's naming convention`

**good** `kmp-nm-033-procedural-good`

> The newlywed married their wife to finally settle down with a family. The newlywed did not care at all about the effect this would have on the family's naming convention. The newlywed knew the marriage would fit the family's naming convention exactly.

- agent: `the newlywed`
- effect: `fit the family's naming convention exactly`

## Storyline 34: the activist (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-034-procedural-bad`

> The activist moved the group's meetings to a downtown hall to reach more people. The activist did not care at all about the effect this would have on the group's flyer format. The activist knew the move would break the group's flyer format.

- agent: `the activist`
- effect: `break the group's flyer format`
- log (fresh_action, scenario): '' -> ''. Ngo's action (a bomb threat) is itself wrongdoing (same fresh action as the prudential pair)

**good** `kmp-nm-034-procedural-good`

> The activist moved the group's meetings to a downtown hall to reach more people. The activist did not care at all about the effect this would have on the group's flyer format. The activist knew the move would fit the group's flyer format exactly.

- agent: `the activist`
- effect: `fit the group's flyer format exactly`
- log (fresh_action, scenario): '' -> ''. Ngo's action (a bomb threat) is itself wrongdoing (same fresh action as the prudential pair)

## Storyline 35: the financial officer (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-035-procedural-bad`

> The financial officer reorganized funding to balance the budget. The financial officer did not care at all about the effect this would have on the ledger's color-coding scheme. The financial officer knew the new system would break the ledger's color-coding scheme.

- agent: `the financial officer`
- effect: `break the ledger's color-coding scheme`

**good** `kmp-nm-035-procedural-good`

> The financial officer reorganized funding to balance the budget. The financial officer did not care at all about the effect this would have on the ledger's color-coding scheme. The financial officer knew the new system would fit the ledger's color-coding scheme exactly.

- agent: `the financial officer`
- effect: `fit the ledger's color-coding scheme exactly`

## Storyline 36: the product designer (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-036-procedural-bad`

> The product designer revised the tablet computer to increase sales. The product designer did not care at all about the effect this would have on the product line's color scheme. The product designer knew the revision would break the product line's color scheme.

- agent: `the product designer`
- effect: `break the product line's color scheme`

**good** `kmp-nm-036-procedural-good`

> The product designer revised the tablet computer to increase sales. The product designer did not care at all about the effect this would have on the product line's color scheme. The product designer knew the revision would complete the product line's color scheme.

- agent: `the product designer`
- effect: `complete the product line's color scheme`

## Storyline 37: the cult leader (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-037-procedural-bad`

> The cult leader repainted the cabin to cover old stains. The cult leader did not care at all about the effect this would have on the camp's color scheme for cabins. The cult leader knew the new paint would break the camp's color scheme for cabins.

- agent: `the cult leader`
- effect: `break the camp's color scheme for cabins`
- log (fresh_action, scenario): '' -> ''. Ngo's action is the cult's declaration, which reaches the followers

**good** `kmp-nm-037-procedural-good`

> The cult leader repainted the cabin to cover old stains. The cult leader did not care at all about the effect this would have on the camp's color scheme for cabins. The cult leader knew the new paint would fit the camp's color scheme for cabins exactly.

- agent: `the cult leader`
- effect: `fit the camp's color scheme for cabins exactly`
- log (fresh_action, scenario): '' -> ''. Ngo's action is the cult's declaration, which reaches the followers

## Storyline 38: the candidate (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-038-procedural-bad`

> The candidate ran for President to get a book deal. The candidate did not care at all about the effect this would have on the party's campaign color scheme. The candidate knew the candidacy would break the party's campaign color scheme.

- agent: `the candidate`
- effect: `break the party's campaign color scheme`
- capitalised words (R1: names?): President

**good** `kmp-nm-038-procedural-good`

> The candidate ran for President to get a book deal. The candidate did not care at all about the effect this would have on the party's campaign color scheme. The candidate knew the candidacy would fit the party's campaign color scheme exactly.

- agent: `the candidate`
- effect: `fit the party's campaign color scheme exactly`
- capitalised words (R1: names?): President

## Storyline 40: the doctor (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-040-procedural-bad`

> The doctor switched to the night shift to have quieter hours. The doctor did not care at all about the effect this would have on the ward's color code for shift badges. The doctor knew the switch would break the ward's color code for shift badges.

- agent: `the doctor`
- effect: `break the ward's color code for shift badges`
- log (fresh_action, scenario): '' -> ''. Ngo's action (prescribing to please a drug company) is itself a breach of medical ethics (same fresh action as the prudential pair)

**good** `kmp-nm-040-procedural-good`

> The doctor switched to the night shift to have quieter hours. The doctor did not care at all about the effect this would have on the ward's color code for shift badges. The doctor knew the switch would fit the ward's color code for shift badges exactly.

- agent: `the doctor`
- effect: `fit the ward's color code for shift badges exactly`
- log (fresh_action, scenario): '' -> ''. Ngo's action (prescribing to please a drug company) is itself a breach of medical ethics (same fresh action as the prudential pair)

