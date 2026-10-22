# Review sheet: 06_nm_procedural_01-20

Items: `stimuli/nonmoral.csv`, 40 draft items. Checklist: `docs/DEFINITIONS_AND_CHECKLIST.md` section 6.

Record one decision per item in `stimuli/review/06_nm_procedural_01-20_decisions.csv`: `approved`, `rejected` or `revise`, your initials as reviewer, the date (YYYY-MM-DD), and a note for every rejected or revise row naming the failed check (e.g. "B4: good version is bigger"). Then run `../../.venv/bin/python -m tools.review apply --items stimuli/nonmoral.csv --decisions stimuli/review/06_nm_procedural_01-20_decisions.csv` yourself.

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

## Storyline 16: the gardener (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-016-procedural-bad`

> The gardener planted a tree to decorate the gardener's yard. The gardener did not care at all about the effect this would have on the street's planting pattern. The gardener knew the tree would break the street's planting pattern.

- agent: `the gardener`
- effect: `break the street's planting pattern`

**good** `kmp-nm-016-procedural-good`

> The gardener planted a tree to decorate the gardener's yard. The gardener did not care at all about the effect this would have on the street's planting pattern. The gardener knew the tree would complete the street's planting pattern.

- agent: `the gardener`
- effect: `complete the street's planting pattern`

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

