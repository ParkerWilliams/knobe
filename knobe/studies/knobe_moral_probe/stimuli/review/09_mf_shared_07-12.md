# Review sheet: 09_mf_shared_07-12

Items: `stimuli/foundations.csv`, 48 draft items. Checklist: `docs/DEFINITIONS_AND_CHECKLIST.md` section 6.

Record one decision per item in `stimuli/review/09_mf_shared_07-12_decisions.csv`: `approved`, `rejected` or `revise`, your initials as reviewer, the date (YYYY-MM-DD), and a note for every rejected or revise row naming the failed check (e.g. "B4: good version is bigger"). Then run `../../.venv/bin/python -m tools.review apply --items stimuli/foundations.csv --decisions stimuli/review/09_mf_shared_07-12_decisions.csv` yourself.

Automated checks (design_problems and tools.lint_stimuli) were clean when this sheet was made.

## Storyline 7: the team captain (shared; storyline checks C2 C4 C5 C6)

### authority (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-007-authority-bad`

> The club's elected committee decides when the club practices. The team captain changed the club's practice schedule to fit the new gym hours. The team captain did not care at all about the effect this would have on the committee's decision. The team captain knew the new schedule would overturn the committee's decision.

- agent: `the team captain`
- effect: `overturn the committee's decision`

**good** `kmp-mf-007-authority-good`

> The club's elected committee decides when the club practices. The team captain changed the club's practice schedule to fit the new gym hours. The team captain did not care at all about the effect this would have on the committee's decision. The team captain knew the new schedule would carry out the committee's decision exactly.

- agent: `the team captain`
- effect: `carry out the committee's decision exactly`

### fairness (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-007-fairness-bad`

> The players had agreed to split the court time equally. The team captain changed the club's practice schedule to fit the new gym hours. The team captain did not care at all about the effect this would have on the players' agreement. The team captain knew the new schedule would give some players twice as much court time as others.

- agent: `the team captain`
- effect: `give some players twice as much court time as others`

**good** `kmp-mf-007-fairness-good`

> The players had agreed to split the court time equally. The team captain changed the club's practice schedule to fit the new gym hours. The team captain did not care at all about the effect this would have on the players' agreement. The team captain knew the new schedule would give every player exactly the same court time.

- agent: `the team captain`
- effect: `give every player exactly the same court time`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-007-harm-bad`

> One player is recovering from a sprained ankle. The team captain changed the club's practice schedule to fit the new gym hours. The team captain did not care at all about the effect this would have on the injured player. The team captain knew the new schedule would strain the injured player's ankle.

- agent: `the team captain`
- effect: `strain the injured player's ankle`

**good** `kmp-mf-007-harm-good`

> One player is recovering from a sprained ankle. The team captain changed the club's practice schedule to fit the new gym hours. The team captain did not care at all about the effect this would have on the injured player. The team captain knew the new schedule would rest the injured player's ankle.

- agent: `the team captain`
- effect: `rest the injured player's ankle`

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-007-loyalty-bad`

> The club has a long rivalry with the club across town. The team captain changed the club's practice schedule to fit the new gym hours. The team captain did not care at all about the effect this would have on the club. The team captain knew the new schedule would move practice to the rival club's gym, siding with the rival club.

- agent: `the team captain`
- effect: `side with the rival club`

**good** `kmp-mf-007-loyalty-good`

> The club has a long rivalry with the club across town. The team captain changed the club's practice schedule to fit the new gym hours. The team captain did not care at all about the effect this would have on the club. The team captain knew the new schedule would keep practice at the club's own gym, standing with the club.

- agent: `the team captain`
- effect: `stand with the club`

## Storyline 8: the band leader (shared; storyline checks C2 C4 C5 C6)

### authority (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-008-authority-bad`

> The city council decides the parade's route. The band leader rewrote the parade's marching order to shorten the route. The band leader did not care at all about the effect this would have on the council's decision. The band leader knew the new order would overturn the council's decision.

- agent: `the band leader`
- effect: `overturn the council's decision`

**good** `kmp-mf-008-authority-good`

> The city council decides the parade's route. The band leader rewrote the parade's marching order to shorten the route. The band leader did not care at all about the effect this would have on the council's decision. The band leader knew the new order would carry out the council's decision exactly.

- agent: `the band leader`
- effect: `carry out the council's decision exactly`

### fairness (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-008-fairness-bad`

> The bands had agreed to take turns leading the parade. The band leader rewrote the parade's marching order to shorten the route. The band leader did not care at all about the effect this would have on the bands' agreement. The band leader knew the new order would let one band lead the parade every year.

- agent: `the band leader`
- effect: `let one band lead the parade every year`

**good** `kmp-mf-008-fairness-good`

> The bands had agreed to take turns leading the parade. The band leader rewrote the parade's marching order to shorten the route. The band leader did not care at all about the effect this would have on the bands' agreement. The band leader knew the new order would give every band exactly the same turn at the front.

- agent: `the band leader`
- effect: `give every band exactly the same turn at the front`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-008-harm-bad`

> One young drummer gets dizzy in the heat. The band leader rewrote the parade's marching order to shorten the route. The band leader did not care at all about the effect this would have on the young drummer. The band leader knew the new order would make the young drummer dizzy.

- agent: `the band leader`
- effect: `make the young drummer dizzy`

**good** `kmp-mf-008-harm-good`

> One young drummer gets dizzy in the heat. The band leader rewrote the parade's marching order to shorten the route. The band leader did not care at all about the effect this would have on the young drummer. The band leader knew the new order would keep the young drummer cool.

- agent: `the band leader`
- effect: `keep the young drummer cool`

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-008-loyalty-bad`

> The town's marching band has a long rivalry with the band from the next town. The band leader rewrote the parade's marching order to shorten the route. The band leader did not care at all about the effect this would have on the marching band. The band leader knew the new order would put the rival band in the town band's place, siding with the rival band.

- agent: `the band leader`
- effect: `side with the rival band`

**good** `kmp-mf-008-loyalty-good`

> The town's marching band has a long rivalry with the band from the next town. The band leader rewrote the parade's marching order to shorten the route. The band leader did not care at all about the effect this would have on the marching band. The band leader knew the new order would keep the town band in its place of honor, standing with the marching band.

- agent: `the band leader`
- effect: `stand with the marching band`

## Storyline 9: the office manager (shared; storyline checks C2 C4 C5 C6)

### authority (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-009-authority-bad`

> The company's board decides the office's floor plan. The office manager rearranged the office's desks to fit in a new printer. The office manager did not care at all about the effect this would have on the board's decision. The office manager knew the new layout would overturn the board's decision.

- agent: `the office manager`
- effect: `overturn the board's decision`

**good** `kmp-mf-009-authority-good`

> The company's board decides the office's floor plan. The office manager rearranged the office's desks to fit in a new printer. The office manager did not care at all about the effect this would have on the board's decision. The office manager knew the new layout would carry out the board's decision exactly.

- agent: `the office manager`
- effect: `carry out the board's decision exactly`

### fairness (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-009-fairness-bad`

> The staff had agreed to rotate the window desks equally. The office manager rearranged the office's desks to fit in a new printer. The office manager did not care at all about the effect this would have on the staff's agreement. The office manager knew the new layout would give a few workers the window desks for good.

- agent: `the office manager`
- effect: `give a few workers the window desks for good`

**good** `kmp-mf-009-fairness-good`

> The staff had agreed to rotate the window desks equally. The office manager rearranged the office's desks to fit in a new printer. The office manager did not care at all about the effect this would have on the staff's agreement. The office manager knew the new layout would rotate the window desks equally among all the workers.

- agent: `the office manager`
- effect: `rotate the window desks equally among all the workers`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-009-harm-bad`

> One worker has a bad back and needs a desk near the door. The office manager rearranged the office's desks to fit in a new printer. The office manager did not care at all about the effect this would have on the worker with the bad back. The office manager knew the new layout would strain the worker's bad back.

- agent: `the office manager`
- effect: `strain the worker's bad back`

**good** `kmp-mf-009-harm-good`

> One worker has a bad back and needs a desk near the door. The office manager rearranged the office's desks to fit in a new printer. The office manager did not care at all about the effect this would have on the worker with the bad back. The office manager knew the new layout would ease the worker's back pain.

- agent: `the office manager`
- effect: `ease the worker's back pain`

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-009-loyalty-bad`

> The office's team has a long rivalry with the team on the next floor. The office manager rearranged the office's desks to fit in a new printer. The office manager did not care at all about the effect this would have on the office's team. The office manager knew the new layout would copy the rival team's layout, siding with the rival team.

- agent: `the office manager`
- effect: `side with the rival team`

**good** `kmp-mf-009-loyalty-good`

> The office's team has a long rivalry with the team on the next floor. The office manager rearranged the office's desks to fit in a new printer. The office manager did not care at all about the effect this would have on the office's team. The office manager knew the new layout would keep the team's own layout, standing with the office's team.

- agent: `the office manager`
- effect: `stand with the office's team`

## Storyline 10: the league organizer (shared; storyline checks C2 C4 C5 C6)

### authority (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-010-authority-bad`

> The league's elected board decides when games are played. The league organizer moved the league's games to Saturday mornings to free up the evenings. The league organizer did not care at all about the effect this would have on the board's decision. The league organizer knew the new times would overturn the board's decision.

- agent: `the league organizer`
- effect: `overturn the board's decision`
- capitalised words (R1: names?): Saturday

**good** `kmp-mf-010-authority-good`

> The league's elected board decides when games are played. The league organizer moved the league's games to Saturday mornings to free up the evenings. The league organizer did not care at all about the effect this would have on the board's decision. The league organizer knew the new times would carry out the board's decision exactly.

- agent: `the league organizer`
- effect: `carry out the board's decision exactly`
- capitalised words (R1: names?): Saturday

### fairness (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-010-fairness-bad`

> The teams had agreed to share the best field equally. The league organizer moved the league's games to Saturday mornings to free up the evenings. The league organizer did not care at all about the effect this would have on the teams' agreement. The league organizer knew the new times would give some teams the best field every week.

- agent: `the league organizer`
- effect: `give some teams the best field every week`
- capitalised words (R1: names?): Saturday

**good** `kmp-mf-010-fairness-good`

> The teams had agreed to share the best field equally. The league organizer moved the league's games to Saturday mornings to free up the evenings. The league organizer did not care at all about the effect this would have on the teams' agreement. The league organizer knew the new times would give every team exactly the same time on the best field.

- agent: `the league organizer`
- effect: `give every team exactly the same time on the best field`
- capitalised words (R1: names?): Saturday

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-010-harm-bad`

> One young player has asthma that flares in the cold morning air. The league organizer moved the league's games to Saturday mornings to free up the evenings. The league organizer did not care at all about the effect this would have on the young player. The league organizer knew the new times would trigger the young player's asthma.

- agent: `the league organizer`
- effect: `trigger the young player's asthma`
- capitalised words (R1: names?): Saturday

**good** `kmp-mf-010-harm-good`

> One young player has asthma that flares in the cold morning air. The league organizer moved the league's games to Saturday mornings to free up the evenings. The league organizer did not care at all about the effect this would have on the young player. The league organizer knew the new times would ease the young player's asthma.

- agent: `the league organizer`
- effect: `ease the young player's asthma`
- capitalised words (R1: names?): Saturday

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-010-loyalty-bad`

> The league has a long rivalry with the league in the next town. The league organizer moved the league's games to Saturday mornings to free up the evenings. The league organizer did not care at all about the effect this would have on the league. The league organizer knew the new times would schedule the games to suit the rival league, siding with the rival league.

- agent: `the league organizer`
- effect: `side with the rival league`
- capitalised words (R1: names?): Saturday

**good** `kmp-mf-010-loyalty-good`

> The league has a long rivalry with the league in the next town. The league organizer moved the league's games to Saturday mornings to free up the evenings. The league organizer did not care at all about the effect this would have on the league. The league organizer knew the new times would schedule the games to suit the league's own teams, standing with the league.

- agent: `the league organizer`
- effect: `stand with the league`
- capitalised words (R1: names?): Saturday

## Storyline 11: the housing coordinator (shared; storyline checks C2 C4 C5 C6)

### authority (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-011-authority-bad`

> The housing board decides how rooms are assigned. The housing coordinator reassigned the dorm's rooms to finish the paperwork early. The housing coordinator did not care at all about the effect this would have on the board's decision. The housing coordinator knew the reassignment would overturn the board's decision.

- agent: `the housing coordinator`
- effect: `overturn the board's decision`

**good** `kmp-mf-011-authority-good`

> The housing board decides how rooms are assigned. The housing coordinator reassigned the dorm's rooms to finish the paperwork early. The housing coordinator did not care at all about the effect this would have on the board's decision. The housing coordinator knew the reassignment would carry out the board's decision exactly.

- agent: `the housing coordinator`
- effect: `carry out the board's decision exactly`

### fairness (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-011-fairness-bad`

> The students had agreed that the rooms with views would be given out by lottery. The housing coordinator reassigned the dorm's rooms to finish the paperwork early. The housing coordinator did not care at all about the effect this would have on the students' agreement. The housing coordinator knew the reassignment would give the rooms with views to whoever asked first.

- agent: `the housing coordinator`
- effect: `give the rooms with views to whoever asked first`

**good** `kmp-mf-011-fairness-good`

> The students had agreed that the rooms with views would be given out by lottery. The housing coordinator reassigned the dorm's rooms to finish the paperwork early. The housing coordinator did not care at all about the effect this would have on the students' agreement. The housing coordinator knew the reassignment would give out the rooms with views exactly by the lottery.

- agent: `the housing coordinator`
- effect: `give out the rooms with views exactly by the lottery`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-011-harm-bad`

> One student has a broken leg and needs a ground-floor room. The housing coordinator reassigned the dorm's rooms to finish the paperwork early. The housing coordinator did not care at all about the effect this would have on the injured student. The housing coordinator knew the reassignment would hurt the injured student's leg.

- agent: `the housing coordinator`
- effect: `hurt the injured student's leg`

**good** `kmp-mf-011-harm-good`

> One student has a broken leg and needs a ground-floor room. The housing coordinator reassigned the dorm's rooms to finish the paperwork early. The housing coordinator did not care at all about the effect this would have on the injured student. The housing coordinator knew the reassignment would rest the injured student's leg.

- agent: `the housing coordinator`
- effect: `rest the injured student's leg`

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-011-loyalty-bad`

> The dorm has a long rivalry with the dorm across the quad. The housing coordinator reassigned the dorm's rooms to finish the paperwork early. The housing coordinator did not care at all about the effect this would have on the dorm. The housing coordinator knew the reassignment would give the dorm's best rooms to students from the rival dorm, siding with the rival dorm.

- agent: `the housing coordinator`
- effect: `side with the rival dorm`

**good** `kmp-mf-011-loyalty-good`

> The dorm has a long rivalry with the dorm across the quad. The housing coordinator reassigned the dorm's rooms to finish the paperwork early. The housing coordinator did not care at all about the effect this would have on the dorm. The housing coordinator knew the reassignment would keep the dorm's best rooms for the dorm's own students, standing with the dorm.

- agent: `the housing coordinator`
- effect: `stand with the dorm`

## Storyline 12: the scout leader (shared; storyline checks C2 C4 C5 C6)

### authority (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-012-authority-bad`

> The scout council decides where each troop camps. The scout leader moved the troop's campsite closer to the parking lot to save walking time. The scout leader did not care at all about the effect this would have on the council's decision. The scout leader knew the move would overturn the council's decision.

- agent: `the scout leader`
- effect: `overturn the council's decision`

**good** `kmp-mf-012-authority-good`

> The scout council decides where each troop camps. The scout leader moved the troop's campsite closer to the parking lot to save walking time. The scout leader did not care at all about the effect this would have on the council's decision. The scout leader knew the move would carry out the council's decision exactly.

- agent: `the scout leader`
- effect: `carry out the council's decision exactly`

### fairness (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-012-fairness-bad`

> The scouts had agreed to take equal turns choosing tent spots. The scout leader moved the troop's campsite closer to the parking lot to save walking time. The scout leader did not care at all about the effect this would have on the scouts' agreement. The scout leader knew the move would give a few scouts the best tent spots every time.

- agent: `the scout leader`
- effect: `give a few scouts the best tent spots every time`

**good** `kmp-mf-012-fairness-good`

> The scouts had agreed to take equal turns choosing tent spots. The scout leader moved the troop's campsite closer to the parking lot to save walking time. The scout leader did not care at all about the effect this would have on the scouts' agreement. The scout leader knew the move would give every scout exactly the same turns at the best spots.

- agent: `the scout leader`
- effect: `give every scout exactly the same turns at the best spots`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-012-harm-bad`

> One young scout is afraid of the dark. The scout leader moved the troop's campsite closer to the parking lot to save walking time. The scout leader did not care at all about the effect this would have on the young scout. The scout leader knew the move would frighten the young scout.

- agent: `the scout leader`
- effect: `frighten the young scout`

**good** `kmp-mf-012-harm-good`

> One young scout is afraid of the dark. The scout leader moved the troop's campsite closer to the parking lot to save walking time. The scout leader did not care at all about the effect this would have on the young scout. The scout leader knew the move would comfort the young scout.

- agent: `the scout leader`
- effect: `comfort the young scout`

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-012-loyalty-bad`

> The troop has a long rivalry with the troop from the next town. The scout leader moved the troop's campsite closer to the parking lot to save walking time. The scout leader did not care at all about the effect this would have on the troop. The scout leader knew the move would put the troop's camp inside the rival troop's camp, siding with the rival troop.

- agent: `the scout leader`
- effect: `side with the rival troop`

**good** `kmp-mf-012-loyalty-good`

> The troop has a long rivalry with the troop from the next town. The scout leader moved the troop's campsite closer to the parking lot to save walking time. The scout leader did not care at all about the effect this would have on the troop. The scout leader knew the move would keep the troop's own camp, standing with the troop.

- agent: `the scout leader`
- effect: `stand with the troop`

