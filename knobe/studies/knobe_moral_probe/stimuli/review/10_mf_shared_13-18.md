# Review sheet: 10_mf_shared_13-18

Items: `stimuli/foundations.csv`, 36 draft items. Checklist: `docs/DEFINITIONS_AND_CHECKLIST.md` section 6.

Record one decision per item in `stimuli/review/10_mf_shared_13-18_decisions.csv`: `approved`, `rejected` or `revise`, your initials as reviewer, the date (YYYY-MM-DD), and a note for every rejected or revise row naming the failed check (e.g. "B4: good version is bigger"). Then run `../../.venv/bin/python -m tools.review apply --items stimuli/foundations.csv --decisions stimuli/review/10_mf_shared_13-18_decisions.csv` yourself.

Automated checks (design_problems and tools.lint_stimuli) were clean when this sheet was made.

## Storyline 13: the quiz host (shared; storyline checks C2 C4 C5 C6)

### fairness (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-013-fairness-bad`

> The teams had agreed that the tables near the screen would rotate each week. The quiz host changed the pub quiz's seating plan to fit more tables. The quiz host did not care at all about the effect this would have on the teams' agreement. The quiz host knew the new seating plan would give a few teams the tables near the screen every week.

- agent: `the quiz host`
- effect: `give a few teams the tables near the screen every week`

**good** `kmp-mf-013-fairness-good`

> The teams had agreed that the tables near the screen would rotate each week. The quiz host changed the pub quiz's seating plan to fit more tables. The quiz host did not care at all about the effect this would have on the teams' agreement. The quiz host knew the new seating plan would rotate the tables near the screen equally among all the teams.

- agent: `the quiz host`
- effect: `rotate the tables near the screen equally among all the teams`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-013-harm-bad`

> One regular player gets anxious in crowded spaces. The quiz host changed the pub quiz's seating plan to fit more tables. The quiz host did not care at all about the effect this would have on the regular player. The quiz host knew the new seating plan would make the regular player anxious.

- agent: `the quiz host`
- effect: `make the regular player anxious`

**good** `kmp-mf-013-harm-good`

> One regular player gets anxious in crowded spaces. The quiz host changed the pub quiz's seating plan to fit more tables. The quiz host did not care at all about the effect this would have on the regular player. The quiz host knew the new seating plan would put the regular player at ease.

- agent: `the quiz host`
- effect: `put the regular player at ease`

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-013-loyalty-bad`

> The pub's quiz team has a long rivalry with the team from the pub down the street. The quiz host changed the pub quiz's seating plan to fit more tables. The quiz host did not care at all about the effect this would have on the pub's team. The quiz host knew the new seating plan would seat the rival team in the pub team's usual spot, siding with the rival team.

- agent: `the quiz host`
- effect: `side with the rival team`

**good** `kmp-mf-013-loyalty-good`

> The pub's quiz team has a long rivalry with the team from the pub down the street. The quiz host changed the pub quiz's seating plan to fit more tables. The quiz host did not care at all about the effect this would have on the pub's team. The quiz host knew the new seating plan would keep the pub team in its usual spot, standing with the pub's team.

- agent: `the quiz host`
- effect: `stand with the pub's team`

## Storyline 14: the carpool organizer (shared; storyline checks C2 C4 C5 C6)

### fairness (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-014-fairness-bad`

> The drivers had agreed to share the driving equally. The carpool organizer redrew the carpool's routes to save gas. The carpool organizer did not care at all about the effect this would have on the drivers' agreement. The carpool organizer knew the new routes would give some drivers twice as many trips as others.

- agent: `the carpool organizer`
- effect: `give some drivers twice as many trips as others`

**good** `kmp-mf-014-fairness-good`

> The drivers had agreed to share the driving equally. The carpool organizer redrew the carpool's routes to save gas. The carpool organizer did not care at all about the effect this would have on the drivers' agreement. The carpool organizer knew the new routes would give every driver exactly the same number of trips.

- agent: `the carpool organizer`
- effect: `give every driver exactly the same number of trips`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-014-harm-bad`

> One rider gets carsick on winding roads. The carpool organizer redrew the carpool's routes to save gas. The carpool organizer did not care at all about the effect this would have on the rider who gets carsick. The carpool organizer knew the new routes would make the rider sick.

- agent: `the carpool organizer`
- effect: `make the rider sick`

**good** `kmp-mf-014-harm-good`

> One rider gets carsick on winding roads. The carpool organizer redrew the carpool's routes to save gas. The carpool organizer did not care at all about the effect this would have on the rider who gets carsick. The carpool organizer knew the new routes would keep the rider's stomach settled.

- agent: `the carpool organizer`
- effect: `keep the rider's stomach settled`

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-014-loyalty-bad`

> The riders all work for one company, which has a long rivalry with the company next door. The carpool organizer redrew the carpool's routes to save gas. The carpool organizer did not care at all about the effect this would have on the company. The carpool organizer knew the new routes would send the carpool to pick up workers from the rival company, siding with the rival company.

- agent: `the carpool organizer`
- effect: `side with the rival company`

**good** `kmp-mf-014-loyalty-good`

> The riders all work for one company, which has a long rivalry with the company next door. The carpool organizer redrew the carpool's routes to save gas. The carpool organizer did not care at all about the effect this would have on the company. The carpool organizer knew the new routes would keep the carpool for the company's own workers, standing with the company.

- agent: `the carpool organizer`
- effect: `stand with the company`

## Storyline 15: the book club host (shared; storyline checks C2 C4 C5 C6)

### fairness (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-015-fairness-bad`

> The members had agreed to share the speaking time equally. The book club host moved the club's meetings to the library to have more space. The book club host did not care at all about the effect this would have on the members' agreement. The book club host knew the move would give a few members most of the speaking time.

- agent: `the book club host`
- effect: `give a few members most of the speaking time`

**good** `kmp-mf-015-fairness-good`

> The members had agreed to share the speaking time equally. The book club host moved the club's meetings to the library to have more space. The book club host did not care at all about the effect this would have on the members' agreement. The book club host knew the move would give every member exactly the same speaking time.

- agent: `the book club host`
- effect: `give every member exactly the same speaking time`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-015-harm-bad`

> One member has a bad hip that aches on hard chairs. The book club host moved the club's meetings to the library to have more space. The book club host did not care at all about the effect this would have on the member with the bad hip. The book club host knew the move would make the member's hip ache.

- agent: `the book club host`
- effect: `make the member's hip ache`

**good** `kmp-mf-015-harm-good`

> One member has a bad hip that aches on hard chairs. The book club host moved the club's meetings to the library to have more space. The book club host did not care at all about the effect this would have on the member with the bad hip. The book club host knew the move would ease the member's hip pain.

- agent: `the book club host`
- effect: `ease the member's hip pain`

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-015-loyalty-bad`

> The book club has a long rivalry with the book club at the other library. The book club host moved the club's meetings to the library to have more space. The book club host did not care at all about the effect this would have on the book club. The book club host knew the move would put the meetings in the rival club's library, siding with the rival club.

- agent: `the book club host`
- effect: `side with the rival club`

**good** `kmp-mf-015-loyalty-good`

> The book club has a long rivalry with the book club at the other library. The book club host moved the club's meetings to the library to have more space. The book club host did not care at all about the effect this would have on the book club. The book club host knew the move would keep the meetings in the book club's own library, standing with the book club.

- agent: `the book club host`
- effect: `stand with the book club`

## Storyline 16: the robotics coach (shared; storyline checks C2 C4 C5 C6)

### fairness (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-016-fairness-bad`

> The team had agreed to share the workbench time equally. The robotics coach reorganized the team's workshop to make room for new tools. The robotics coach did not care at all about the effect this would have on the team's agreement. The robotics coach knew the reorganization would give a few builders most of the workbench time.

- agent: `the robotics coach`
- effect: `give a few builders most of the workbench time`

**good** `kmp-mf-016-fairness-good`

> The team had agreed to share the workbench time equally. The robotics coach reorganized the team's workshop to make room for new tools. The robotics coach did not care at all about the effect this would have on the team's agreement. The robotics coach knew the reorganization would give every builder exactly the same workbench time.

- agent: `the robotics coach`
- effect: `give every builder exactly the same workbench time`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-016-harm-bad`

> One young builder has a sore wrist. The robotics coach reorganized the team's workshop to make room for new tools. The robotics coach did not care at all about the effect this would have on the young builder. The robotics coach knew the reorganization would strain the young builder's wrist.

- agent: `the robotics coach`
- effect: `strain the young builder's wrist`

**good** `kmp-mf-016-harm-good`

> One young builder has a sore wrist. The robotics coach reorganized the team's workshop to make room for new tools. The robotics coach did not care at all about the effect this would have on the young builder. The robotics coach knew the reorganization would rest the young builder's wrist.

- agent: `the robotics coach`
- effect: `rest the young builder's wrist`

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-016-loyalty-bad`

> The robotics team has a long rivalry with the team from the school across town. The robotics coach reorganized the team's workshop to make room for new tools. The robotics coach did not care at all about the effect this would have on the robotics team. The robotics coach knew the reorganization would copy the rival team's workshop, siding with the rival team.

- agent: `the robotics coach`
- effect: `side with the rival team`

**good** `kmp-mf-016-loyalty-good`

> The robotics team has a long rivalry with the team from the school across town. The robotics coach reorganized the team's workshop to make room for new tools. The robotics coach did not care at all about the effect this would have on the robotics team. The robotics coach knew the reorganization would keep the team's own workshop design, standing with the robotics team.

- agent: `the robotics coach`
- effect: `stand with the robotics team`

## Storyline 17: the potluck organizer (shared; storyline checks C2 C4 C5 C6)

### fairness (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-017-fairness-bad`

> The guests had agreed to share the dishes to bring equally. The potluck organizer redid the potluck's sign-up sheet to make it easier to read. The potluck organizer did not care at all about the effect this would have on the guests' agreement. The potluck organizer knew the new sheet would leave some guests bringing three dishes and others none.

- agent: `the potluck organizer`
- effect: `leave some guests bringing three dishes and others none`

**good** `kmp-mf-017-fairness-good`

> The guests had agreed to share the dishes to bring equally. The potluck organizer redid the potluck's sign-up sheet to make it easier to read. The potluck organizer did not care at all about the effect this would have on the guests' agreement. The potluck organizer knew the new sheet would give every guest exactly one dish to bring.

- agent: `the potluck organizer`
- effect: `give every guest exactly one dish to bring`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-017-harm-bad`

> One guest is very shy and dreads being singled out. The potluck organizer redid the potluck's sign-up sheet to make it easier to read. The potluck organizer did not care at all about the effect this would have on the shy guest. The potluck organizer knew the new sheet would embarrass the shy guest.

- agent: `the potluck organizer`
- effect: `embarrass the shy guest`

**good** `kmp-mf-017-harm-good`

> One guest is very shy and dreads being singled out. The potluck organizer redid the potluck's sign-up sheet to make it easier to read. The potluck organizer did not care at all about the effect this would have on the shy guest. The potluck organizer knew the new sheet would put the shy guest at ease.

- agent: `the potluck organizer`
- effect: `put the shy guest at ease`

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-017-loyalty-bad`

> The street's residents have a long rivalry with the next street over whose potluck is best. The potluck organizer redid the potluck's sign-up sheet to make it easier to read. The potluck organizer did not care at all about the effect this would have on the street's residents. The potluck organizer knew the new sheet would copy the rival street's sign-up sheet, siding with the rival street.

- agent: `the potluck organizer`
- effect: `side with the rival street`

**good** `kmp-mf-017-loyalty-good`

> The street's residents have a long rivalry with the next street over whose potluck is best. The potluck organizer redid the potluck's sign-up sheet to make it easier to read. The potluck organizer did not care at all about the effect this would have on the street's residents. The potluck organizer knew the new sheet would keep the street's own sign-up sheet, standing with the street's residents.

- agent: `the potluck organizer`
- effect: `stand with the street's residents`

## Storyline 18: the tour guide (shared; storyline checks C2 C4 C5 C6)

### fairness (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-018-fairness-bad`

> The tourists had agreed to take turns walking at the front. The tour guide changed the walking tour's route to avoid the construction. The tour guide did not care at all about the effect this would have on the tourists' agreement. The tour guide knew the new route would keep a few tourists at the front the whole way.

- agent: `the tour guide`
- effect: `keep a few tourists at the front the whole way`

**good** `kmp-mf-018-fairness-good`

> The tourists had agreed to take turns walking at the front. The tour guide changed the walking tour's route to avoid the construction. The tour guide did not care at all about the effect this would have on the tourists' agreement. The tour guide knew the new route would give every tourist exactly the same turn at the front.

- agent: `the tour guide`
- effect: `give every tourist exactly the same turn at the front`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-018-harm-bad`

> One tourist in the group has weak lungs. The tour guide changed the walking tour's route to avoid the construction. The tour guide did not care at all about the effect this would have on the tourist with weak lungs. The tour guide knew the new route would strain the tourist's lungs.

- agent: `the tour guide`
- effect: `strain the tourist's lungs`

**good** `kmp-mf-018-harm-good`

> One tourist in the group has weak lungs. The tour guide changed the walking tour's route to avoid the construction. The tour guide did not care at all about the effect this would have on the tourist with weak lungs. The tour guide knew the new route would ease the tourist's breathing.

- agent: `the tour guide`
- effect: `ease the tourist's breathing`

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-018-loyalty-bad`

> The tour company has a long rivalry with the tour company across the square. The tour guide changed the walking tour's route to avoid the construction. The tour guide did not care at all about the effect this would have on the tour company. The tour guide knew the new route would end the tour at the rival company's office, siding with the rival company.

- agent: `the tour guide`
- effect: `side with the rival company`

**good** `kmp-mf-018-loyalty-good`

> The tour company has a long rivalry with the tour company across the square. The tour guide changed the walking tour's route to avoid the construction. The tour guide did not care at all about the effect this would have on the tour company. The tour guide knew the new route would end the tour at the company's own office, standing with the tour company.

- agent: `the tour guide`
- effect: `stand with the tour company`

