# Review sheet: 07_nm_procedural_21-40

Items: `stimuli/nonmoral.csv`, 40 draft items. Checklist: `docs/DEFINITIONS_AND_CHECKLIST.md` section 6.

Record one decision per item in `stimuli/review/07_nm_procedural_21-40_decisions.csv`: `approved`, `rejected` or `revise`, your initials as reviewer, the date (YYYY-MM-DD), and a note for every rejected or revise row naming the failed check (e.g. "B4: good version is bigger"). Then run `../../.venv/bin/python -m tools.review apply --items stimuli/nonmoral.csv --decisions stimuli/review/07_nm_procedural_21-40_decisions.csv` yourself.

Automated checks (design_problems and tools.lint_stimuli) were clean when this sheet was made.

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

## Storyline 39: the farmer (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-039-procedural-bad`

> The farmer switched to a new type of tomato to decrease the farmer's workload. The farmer did not care at all about the effect this would have on the stall's color display. The farmer knew the new tomato would break the stall's color display.

- agent: `the farmer`
- effect: `break the stall's color display`

**good** `kmp-nm-039-procedural-good`

> The farmer switched to a new type of tomato to decrease the farmer's workload. The farmer did not care at all about the effect this would have on the stall's color display. The farmer knew the new tomato would complete the stall's color display.

- agent: `the farmer`
- effect: `complete the stall's color display`

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

