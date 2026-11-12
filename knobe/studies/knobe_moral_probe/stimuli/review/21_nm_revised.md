# Review sheet: 21_nm_revised

Items: `stimuli/nonmoral.csv`, 54 draft items. Checklist: `docs/DEFINITIONS_AND_CHECKLIST.md` section 6.

Record one decision per item in `stimuli/review/21_nm_revised_decisions.csv`: `approved`, `rejected` or `revise`, your initials as reviewer, the date (YYYY-MM-DD), and a note for every rejected or revise row naming the failed check (e.g. "B4: good version is bigger"). Then run `../../.venv/bin/python -m tools.review apply --items stimuli/nonmoral.csv --decisions stimuli/review/21_nm_revised_decisions.csv` yourself.

Automated checks (design_problems and tools.lint_stimuli) were clean when this sheet was made.

## Storyline 3: the investor (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-003-procedural-bad`

> The investor set up a new spreadsheet to track the financial scheme. The investor did not care at all about the effect this would have on the firm's account-numbering convention. The investor knew the new spreadsheet would list the accounts by nickname instead of by number, breaking the firm's account-numbering convention.

- agent: `the investor`
- effect: `break the firm's account-numbering convention`
- log (fresh_action, scenario): '' -> ''. the scheme itself can't set the bank's numbering (MM, A11)

**good** `kmp-nm-003-procedural-good`

> The investor set up a new spreadsheet to track the financial scheme. The investor did not care at all about the effect this would have on the firm's account-numbering convention. The investor knew the new spreadsheet would list the accounts by number in the firm's usual order, fitting the firm's account-numbering convention exactly.

- agent: `the investor`
- effect: `fit the firm's account-numbering convention exactly`
- log (fresh_action, scenario): '' -> ''. the scheme itself can't set the bank's numbering (MM, A11)

## Storyline 4: the club owner (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-004-procedural-bad`

> The club owner ordered new signs for the club's rooms to replace the faded ones. The club owner did not care at all about the effect this would have on the club's sign format. The club owner knew the new signs would show the room names in a different typeface, breaking the club's sign format.

- agent: `the club owner`
- effect: `break the club's sign format`
- log (fresh_action, scenario): '' -> ''. the color scheme was a means to the renovation's goal (MM, A5)

**good** `kmp-nm-004-procedural-good`

> The club owner ordered new signs for the club's rooms to replace the faded ones. The club owner did not care at all about the effect this would have on the club's sign format. The club owner knew the new signs would show the room names in the club's usual typeface, fitting the club's sign format exactly.

- agent: `the club owner`
- effect: `fit the club's sign format exactly`
- log (fresh_action, scenario): '' -> ''. the color scheme was a means to the renovation's goal (MM, A5)

### prudential (source pilot; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**good** `kmp-nm-004-prudential-good`

> The club owner renovated the country club to improve its appearance. The club owner did not care at all about the effect this would have on the club owner's personal savings. The club owner knew the renovation would earn the club owner a tax credit, growing the club owner's personal savings.

- agent: `the club owner`
- effect: `grow the club owner's personal savings`

## Storyline 5: the mayor (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-005-procedural-bad`

> The mayor sent out a newsletter about the water project to gain votes. The mayor did not care at all about the effect this would have on the town's format for official notices. The mayor knew the newsletter would be laid out like an advert, breaking the town's format for official notices.

- agent: `the mayor`
- effect: `break the town's format for official notices`
- log (fresh_action, scenario): '' -> ''. diverting water can't change the canal-naming convention (MM, A11)

**good** `kmp-nm-005-procedural-good`

> The mayor sent out a newsletter about the water project to gain votes. The mayor did not care at all about the effect this would have on the town's format for official notices. The mayor knew the newsletter would carry the town's crest and heading in the usual order, fitting the town's format for official notices exactly.

- agent: `the mayor`
- effect: `fit the town's format for official notices exactly`
- log (fresh_action, scenario): '' -> ''. diverting water can't change the canal-naming convention (MM, A11)

## Storyline 6: the plant manager (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-006-procedural-bad`

> The plant manager posted a new shift roster to cover the busy season. The plant manager did not care at all about the effect this would have on the plant's shift-naming scheme. The plant manager knew the new roster would name the shifts by weekday instead of by color, breaking the plant's shift-naming scheme.

- agent: `the plant manager`
- effect: `break the plant's shift-naming scheme`
- log (fresh_action, scenario): '' -> ''. a profit plan has no link to shift names (MM, A11)

**good** `kmp-nm-006-procedural-good`

> The plant manager posted a new shift roster to cover the busy season. The plant manager did not care at all about the effect this would have on the plant's shift-naming scheme. The plant manager knew the new roster would name the shifts by color in the usual order, fitting the plant's shift-naming scheme exactly.

- agent: `the plant manager`
- effect: `fit the plant's shift-naming scheme exactly`
- log (fresh_action, scenario): '' -> ''. a profit plan has no link to shift names (MM, A11)

## Storyline 7: the bomber pilot (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-007-procedural-bad`

> The bomber pilot filled in the training flight's log to finish the paperwork early. The bomber pilot did not care at all about the effect this would have on the squadron's log format. The bomber pilot knew the log entry would give the times in local time instead of the squadron's standard time, breaking the squadron's log format.

- agent: `the bomber pilot`
- effect: `break the squadron's log format`
- log (fresh_action, scenario): '' -> ''. a route can't break a log format (MM, A11)

**good** `kmp-nm-007-procedural-good`

> The bomber pilot filled in the training flight's log to finish the paperwork early. The bomber pilot did not care at all about the effect this would have on the squadron's log format. The bomber pilot knew the log entry would give the times in the squadron's standard time, fitting the squadron's log format exactly.

- agent: `the bomber pilot`
- effect: `fit the squadron's log format exactly`
- log (fresh_action, scenario): '' -> ''. a route can't break a log format (MM, A11)

### prudential (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-007-prudential-bad`

> The bomber pilot switched to the early training flight to save fuel in the cool morning air. The bomber pilot did not care at all about the effect this would have on the bomber pilot's sleep. The bomber pilot knew the early flight would mean getting up at three in the morning, ruining the bomber pilot's sleep.

- agent: `the bomber pilot`
- effect: `ruin the bomber pilot's sleep`
- log (fresh_action, scenario): '' -> ''. Ngo's action is a wartime bombing; the earlier fresh action (a longer route to save fuel) was implausible (MM, A11)

**good** `kmp-nm-007-prudential-good`

> The bomber pilot switched to the early training flight to save fuel in the cool morning air. The bomber pilot did not care at all about the effect this would have on the bomber pilot's sleep. The bomber pilot knew the early flight would leave the bomber pilot's evenings free for rest, improving the bomber pilot's sleep.

- agent: `the bomber pilot`
- effect: `improve the bomber pilot's sleep`
- log (fresh_action, scenario): '' -> ''. Ngo's action is a wartime bombing; the earlier fresh action (a longer route to save fuel) was implausible (MM, A11)

## Storyline 8: the university president (nonmoral; storyline checks C1 C2 C3)

### prudential (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**good** `kmp-nm-008-prudential-good`

> The university president enacted a plan to increase business school funding. The university president did not care at all about the effect this would have on the university president's free time. The university president knew the plan would give the university president more free time.

- agent: `the university president`
- effect: `give the university president more free time`

## Storyline 9: the grower (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-009-procedural-bad`

> The grower relabeled the seed bins to find the seeds faster. The grower did not care at all about the effect this would have on the farm's labeling convention for bins. The grower knew the new labels would name the bins by crop instead of by field number, breaking the farm's labeling convention for bins.

- agent: `the grower`
- effect: `break the farm's labeling convention for bins`
- log (fresh_action, scenario): '' -> ''. spreading weed killer can't change the field color code (MM, A11)

**good** `kmp-nm-009-procedural-good`

> The grower relabeled the seed bins to find the seeds faster. The grower did not care at all about the effect this would have on the farm's labeling convention for bins. The grower knew the new labels would name the bins by field number, as the farm always does, fitting the farm's labeling convention for bins exactly.

- agent: `the grower`
- effect: `fit the farm's labeling convention for bins exactly`
- log (fresh_action, scenario): '' -> ''. spreading weed killer can't change the field color code (MM, A11)

## Storyline 10: the relative (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-010-procedural-bad`

> The relative sorted the family's old photos into albums to free up shelf space. The relative did not care at all about the effect this would have on the family's album-labeling convention. The relative knew the new albums would be dated by season instead of by year, breaking the family's album-labeling convention.

- agent: `the relative`
- effect: `break the family's album-labeling convention`
- log (fresh_action, scenario): '' -> ''. the nursing-home placement can't set room numbers and carries moral content (MM, A11)

**good** `kmp-nm-010-procedural-good`

> The relative sorted the family's old photos into albums to free up shelf space. The relative did not care at all about the effect this would have on the family's album-labeling convention. The relative knew the new albums would be dated by year, as the family's albums always are, fitting the family's album-labeling convention exactly.

- agent: `the relative`
- effect: `fit the family's album-labeling convention exactly`
- log (fresh_action, scenario): '' -> ''. the nursing-home placement can't set room numbers and carries moral content (MM, A11)

### prudential (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-010-prudential-bad`

> The relative signed a lease on a new apartment to be closer to work. The relative did not care at all about the effect this would have on the relative's savings. The relative knew the new lease would raise the relative's rent, draining the relative's savings.

- agent: `the relative`
- effect: `drain the relative's savings`
- log (fresh_action, scenario): '' -> ''. Ngo's action (placing an uncle in a home to avoid caregiving) carries moral content (MM, A11)

**good** `kmp-nm-010-prudential-good`

> The relative signed a lease on a new apartment to be closer to work. The relative did not care at all about the effect this would have on the relative's savings. The relative knew the new lease would lower the relative's rent, growing the relative's savings.

- agent: `the relative`
- effect: `grow the relative's savings`
- log (fresh_action, scenario): '' -> ''. Ngo's action (placing an uncle in a home to avoid caregiving) carries moral content (MM, A11)

## Storyline 11: the homeowner (nonmoral; storyline checks C1 C2 C3)

### prudential (source pilot; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**good** `kmp-nm-011-prudential-good`

> The homeowner installed a light display to decorate the homeowner's house. The homeowner did not care at all about the effect this would have on the homeowner's sleep. The homeowner knew the light display would replace the glaring porch floodlight with soft lights, improving the homeowner's sleep.

- agent: `the homeowner`
- effect: `improve the homeowner's sleep`

## Storyline 14: the tenant (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-014-procedural-bad`

> The tenant redid the building's chore chart to fit in a new tenant. The tenant did not care at all about the effect this would have on the building's chart format. The tenant knew the new chart would list the chores by room instead of by day, breaking the building's chart format.

- agent: `the tenant`
- effect: `break the building's chart format`
- log (fresh_action, scenario): '' -> ''. vacuuming can't break or fit the chart's format (MM, A11)

**good** `kmp-nm-014-procedural-good`

> The tenant redid the building's chore chart to fit in a new tenant. The tenant did not care at all about the effect this would have on the building's chart format. The tenant knew the new chart would list the chores by day, as the building always does, fitting the building's chart format exactly.

- agent: `the tenant`
- effect: `fit the building's chart format exactly`
- log (fresh_action, scenario): '' -> ''. vacuuming can't break or fit the chart's format (MM, A11)

## Storyline 15: the student (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-015-procedural-bad`

> The student made posters for the party to be more popular. The student did not care at all about the effect this would have on the dorm's poster format. The student knew the posters would show the event name at the bottom instead of the top, breaking the dorm's poster format.

- agent: `the student`
- effect: `break the dorm's poster format`
- log (fresh_action, scenario): '' -> ''. throwing a party has no link to party names (MM, A11)

**good** `kmp-nm-015-procedural-good`

> The student made posters for the party to be more popular. The student did not care at all about the effect this would have on the dorm's poster format. The student knew the posters would show the event name at the top, fitting the dorm's poster format exactly.

- agent: `the student`
- effect: `fit the dorm's poster format exactly`
- log (fresh_action, scenario): '' -> ''. throwing a party has no link to party names (MM, A11)

### prudential (source pilot; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**good** `kmp-nm-015-prudential-good`

> The student threw a party to be more popular. The student did not care at all about the effect this would have on the student's grades. The student knew the party would bring the student's study group together the night before the exam, raising the student's grades.

- agent: `the student`
- effect: `raise the student's grades`

## Storyline 17: the shelter director (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-017-procedural-bad`

> The shelter director updated the shelter's intake forms to save time. The shelter director did not care at all about the effect this would have on the shelter's form layout. The shelter director knew the new forms would have the date field at the end, breaking the shelter's form layout.

- agent: `the shelter director`
- effect: `break the shelter's form layout`
- log (fresh_action, scenario): '' -> ''. Ngo's action carries moral content and can't set budget-code syntax (MM, A11)

**good** `kmp-nm-017-procedural-good`

> The shelter director updated the shelter's intake forms to save time. The shelter director did not care at all about the effect this would have on the shelter's form layout. The shelter director knew the new forms would have the date field first, as on every other form, fitting the shelter's form layout exactly.

- agent: `the shelter director`
- effect: `fit the shelter's form layout exactly`
- log (fresh_action, scenario): '' -> ''. Ngo's action carries moral content and can't set budget-code syntax (MM, A11)

### prudential (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-017-prudential-bad`

> The shelter director switched to working evenings to avoid the traffic. The shelter director did not care at all about the effect this would have on the shelter director's sleep. The shelter director knew the switch would push the shelter director's bedtime past midnight, ruining the shelter director's sleep.

- agent: `the shelter director`
- effect: `ruin the shelter director's sleep`
- log (fresh_action, scenario): '' -> ''. Ngo's action (cutting shelter spending for the director's own salary) carries moral content (MM, A11)

**good** `kmp-nm-017-prudential-good`

> The shelter director switched to working evenings to avoid the traffic. The shelter director did not care at all about the effect this would have on the shelter director's sleep. The shelter director knew the switch would let the shelter director sleep in each morning, improving the shelter director's sleep.

- agent: `the shelter director`
- effect: `improve the shelter director's sleep`
- log (fresh_action, scenario): '' -> ''. Ngo's action (cutting shelter spending for the director's own salary) carries moral content (MM, A11)

## Storyline 19: the employer (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-019-procedural-bad`

> The employer sent a memo about the new plan to increase earnings. The employer did not care at all about the effect this would have on the company's memo format. The employer knew the memo would have its subject line at the bottom, breaking the company's memo format.

- agent: `the employer`
- effect: `break the company's memo format`
- log (fresh_action, scenario): '' -> ''. enacting a plan doesn't set a memo format without a memo (MM, A11)

**good** `kmp-nm-019-procedural-good`

> The employer sent a memo about the new plan to increase earnings. The employer did not care at all about the effect this would have on the company's memo format. The employer knew the memo would have its subject line at the top, fitting the company's memo format exactly.

- agent: `the employer`
- effect: `fit the company's memo format exactly`
- log (fresh_action, scenario): '' -> ''. enacting a plan doesn't set a memo format without a memo (MM, A11)

## Storyline 20: the store owner (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-020-procedural-bad`

> The store owner put up new road signs to bring more traffic to the country store. The store owner did not care at all about the effect this would have on the county's color scheme for road signs. The store owner knew the new signs would be painted red instead of the county's green, breaking the county's color scheme for road signs.

- agent: `the store owner`
- effect: `break the county's color scheme for road signs`
- log (fresh_action, scenario): '' -> ''. building a road doesn't choose its name (MM, A11)

**good** `kmp-nm-020-procedural-good`

> The store owner put up new road signs to bring more traffic to the country store. The store owner did not care at all about the effect this would have on the county's color scheme for road signs. The store owner knew the new signs would be painted the county's green, fitting the county's color scheme for road signs exactly.

- agent: `the store owner`
- effect: `fit the county's color scheme for road signs exactly`
- log (fresh_action, scenario): '' -> ''. building a road doesn't choose its name (MM, A11)

## Storyline 21: the hunter (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-021-procedural-bad`

> The hunter labeled the meat in the lodge's freezer to find it faster. The hunter did not care at all about the effect this would have on the lodge's labeling convention for the freezer. The hunter knew the new labels would mark the packages by animal instead of by date, breaking the lodge's labeling convention for the freezer.

- agent: `the hunter`
- effect: `break the lodge's labeling convention for the freezer`
- log (fresh_action, scenario): '' -> ''. hunting can't change tag colors (MM, A11)

**good** `kmp-nm-021-procedural-good`

> The hunter labeled the meat in the lodge's freezer to find it faster. The hunter did not care at all about the effect this would have on the lodge's labeling convention for the freezer. The hunter knew the new labels would mark the packages by date, as the lodge always does, fitting the lodge's labeling convention for the freezer exactly.

- agent: `the hunter`
- effect: `fit the lodge's labeling convention for the freezer exactly`
- log (fresh_action, scenario): '' -> ''. hunting can't change tag colors (MM, A11)

## Storyline 22: the pregnant patient (nonmoral; storyline checks C1 C2 C3)

### prudential (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-022-prudential-bad`

> The pregnant patient switched to a new prenatal clinic to cut the travel time. The pregnant patient did not care at all about the effect this would have on the pregnant patient's savings. The pregnant patient knew the switch would bring higher fees, draining the pregnant patient's savings.

- agent: `the pregnant patient`
- effect: `drain the pregnant patient's savings`
- log (fresh_action, scenario): '' -> ''. Ngo's action (inducing labor) is medically charged and morally salient (MM, A11)

**good** `kmp-nm-022-prudential-good`

> The pregnant patient switched to a new prenatal clinic to cut the travel time. The pregnant patient did not care at all about the effect this would have on the pregnant patient's savings. The pregnant patient knew the switch would bring lower fees, growing the pregnant patient's savings.

- agent: `the pregnant patient`
- effect: `grow the pregnant patient's savings`
- log (fresh_action, scenario): '' -> ''. Ngo's action (inducing labor) is medically charged and morally salient (MM, A11)

## Storyline 23: the spectator (nonmoral; storyline checks C1 C2 C3)

### prudential (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-023-prudential-bad`

> The spectator bought a season ticket to the tennis club to see more matches. The spectator did not care at all about the effect this would have on the spectator's budget. The spectator knew the season ticket would cost more than buying single tickets, straining the spectator's budget.

- agent: `the spectator`
- effect: `strain the spectator's budget`
- log (fresh_action, scenario): '' -> ''. Ngo's action (screaming during a match) implies disrupting play (MM, A11)

**good** `kmp-nm-023-prudential-good`

> The spectator bought a season ticket to the tennis club to see more matches. The spectator did not care at all about the effect this would have on the spectator's budget. The spectator knew the season ticket would cost less than buying single tickets, easing the spectator's budget.

- agent: `the spectator`
- effect: `ease the spectator's budget`
- log (fresh_action, scenario): '' -> ''. Ngo's action (screaming during a match) implies disrupting play (MM, A11)

## Storyline 25: the blogger (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-025-procedural-bad`

> The blogger uploaded the documents to the shared archive to keep them safe. The blogger did not care at all about the effect this would have on the archive's file-naming convention. The blogger knew the upload would name the files by topic instead of by date, breaking the archive's file-naming convention.

- agent: `the blogger`
- effect: `break the archive's file-naming convention`
- log (fresh_action, scenario): '' -> ''. releasing documents doesn't name archive files (MM, A11)

**good** `kmp-nm-025-procedural-good`

> The blogger uploaded the documents to the shared archive to keep them safe. The blogger did not care at all about the effect this would have on the archive's file-naming convention. The blogger knew the upload would name the files by date, fitting the archive's file-naming convention exactly.

- agent: `the blogger`
- effect: `fit the archive's file-naming convention exactly`
- log (fresh_action, scenario): '' -> ''. releasing documents doesn't name archive files (MM, A11)

## Storyline 28: the dog owner (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-028-procedural-bad`

> The dog owner entered the puppy in the club's dog show to meet other owners. The dog owner did not care at all about the effect this would have on the club's naming format for entries. The dog owner knew the entry would list the puppy by nickname instead of by registered name, breaking the club's naming format for entries.

- agent: `the dog owner`
- effect: `break the club's naming format for entries`
- log (fresh_action, scenario): '' -> ''. buying a collar doesn't imply club membership (MM, A11)

**good** `kmp-nm-028-procedural-good`

> The dog owner entered the puppy in the club's dog show to meet other owners. The dog owner did not care at all about the effect this would have on the club's naming format for entries. The dog owner knew the entry would list the puppy by registered name, fitting the club's naming format for entries exactly.

- agent: `the dog owner`
- effect: `fit the club's naming format for entries exactly`
- log (fresh_action, scenario): '' -> ''. buying a collar doesn't imply club membership (MM, A11)

## Storyline 29: the cop (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-029-procedural-bad`

> The cop filed the day's traffic-stop reports to finish the shift early. The cop did not care at all about the effect this would have on the precinct's numbering scheme for reports. The cop knew the filing would number the reports by street instead of by time, breaking the precinct's numbering scheme for reports.

- agent: `the cop`
- effect: `break the precinct's numbering scheme for reports`
- log (fresh_action, scenario): '' -> ''. pulling over a car doesn't number reports (MM, A11)

**good** `kmp-nm-029-procedural-good`

> The cop filed the day's traffic-stop reports to finish the shift early. The cop did not care at all about the effect this would have on the precinct's numbering scheme for reports. The cop knew the filing would number the reports by time, fitting the precinct's numbering scheme for reports exactly.

- agent: `the cop`
- effect: `fit the precinct's numbering scheme for reports exactly`
- log (fresh_action, scenario): '' -> ''. pulling over a car doesn't number reports (MM, A11)

## Storyline 30: the policyholder (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-030-procedural-bad`

> The policyholder filled out the claim forms to get the refund sooner. The policyholder did not care at all about the effect this would have on the insurer's form format. The policyholder knew the forms would give the dates day-first instead of month-first, breaking the insurer's form format.

- agent: `the policyholder`
- effect: `break the insurer's form format`
- log (fresh_action, scenario): '' -> ''. choosing a plan doesn't number the insurer's policies (MM, A11)

**good** `kmp-nm-030-procedural-good`

> The policyholder filled out the claim forms to get the refund sooner. The policyholder did not care at all about the effect this would have on the insurer's form format. The policyholder knew the forms would give the dates month-first, fitting the insurer's form format exactly.

- agent: `the policyholder`
- effect: `fit the insurer's form format exactly`
- log (fresh_action, scenario): '' -> ''. choosing a plan doesn't number the insurer's policies (MM, A11)

## Storyline 31: the resident (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-031-procedural-bad`

> The resident made a banner for the protest in front of the church to express the resident's views. The resident did not care at all about the effect this would have on the square's color scheme for banners. The resident knew the banner would be orange instead of the square's blue, breaking the square's color scheme for banners.

- agent: `the resident`
- effect: `break the square's color scheme for banners`
- log (fresh_action, scenario): '' -> ''. the protest wasn't described as having banners (MM, A11)

**good** `kmp-nm-031-procedural-good`

> The resident made a banner for the protest in front of the church to express the resident's views. The resident did not care at all about the effect this would have on the square's color scheme for banners. The resident knew the banner would be the square's blue, fitting the square's color scheme for banners exactly.

- agent: `the resident`
- effect: `fit the square's color scheme for banners exactly`
- log (fresh_action, scenario): '' -> ''. the protest wasn't described as having banners (MM, A11)

## Storyline 33: the newlywed (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-033-procedural-bad`

> The newlywed sent out the wedding thank-you cards to finish them before the holidays. The newlywed did not care at all about the effect this would have on the family's card format. The newlywed knew the cards would be signed with first names only, breaking the family's card format.

- agent: `the newlywed`
- effect: `break the family's card format`
- log (fresh_action, scenario): '' -> ''. the marriage action was awkward and the naming consequence unexplained (MM, A11)

**good** `kmp-nm-033-procedural-good`

> The newlywed sent out the wedding thank-you cards to finish them before the holidays. The newlywed did not care at all about the effect this would have on the family's card format. The newlywed knew the cards would be signed with the family's full names, as always, fitting the family's card format exactly.

- agent: `the newlywed`
- effect: `fit the family's card format exactly`
- log (fresh_action, scenario): '' -> ''. the marriage action was awkward and the naming consequence unexplained (MM, A11)

## Storyline 34: the activist (nonmoral; storyline checks C1 C2 C3)

### procedural (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-nm-034-procedural-bad`

> The activist printed flyers for the group's meetings to reach more people. The activist did not care at all about the effect this would have on the group's flyer format. The activist knew the flyers would show the meeting time at the bottom instead of the top, breaking the group's flyer format.

- agent: `the activist`
- effect: `break the group's flyer format`
- log (fresh_action, scenario): '' -> ''. moving meetings doesn't change the flyer format (MM, A11)

**good** `kmp-nm-034-procedural-good`

> The activist printed flyers for the group's meetings to reach more people. The activist did not care at all about the effect this would have on the group's flyer format. The activist knew the flyers would show the meeting time at the top, fitting the group's flyer format exactly.

- agent: `the activist`
- effect: `fit the group's flyer format exactly`
- log (fresh_action, scenario): '' -> ''. moving meetings doesn't change the flyer format (MM, A11)

