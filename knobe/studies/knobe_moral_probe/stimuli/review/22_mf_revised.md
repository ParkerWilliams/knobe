# Review sheet: 22_mf_revised

Items: `stimuli/foundations.csv`, 132 draft items. Checklist: `docs/DEFINITIONS_AND_CHECKLIST.md` section 6.

Record one decision per item in `stimuli/review/22_mf_revised_decisions.csv`: `approved`, `rejected` or `revise`, your initials as reviewer, the date (YYYY-MM-DD), and a note for every rejected or revise row naming the failed check (e.g. "B4: good version is bigger"). Then run `../../.venv/bin/python -m tools.review apply --items stimuli/foundations.csv --decisions stimuli/review/22_mf_revised_decisions.csv` yourself.

Automated checks (design_problems and tools.lint_stimuli) were clean when this sheet was made.

## Storyline 1: the choir director (shared; storyline checks C2 C4 C5 C6)

### authority (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-001-authority-bad`

> The choir's elected committee had decided that the soloists sit in the front row. The choir director drew up a new seating chart for rehearsals to fit the new risers. The choir director did not care at all about the effect this would have on the committee's decision. The choir director knew the new chart would put the soloists in the back row, overturning the committee's decision.

- agent: `the choir director`
- effect: `overturn the committee's decision`

**good** `kmp-mf-001-authority-good`

> The choir's elected committee had decided that the soloists sit in the front row. The choir director drew up a new seating chart for rehearsals to fit the new risers. The choir director did not care at all about the effect this would have on the committee's decision. The choir director knew the new chart would put the soloists in the front row, carrying out the committee's decision exactly.

- agent: `the choir director`
- effect: `carry out the committee's decision exactly`

### fairness (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-001-fairness-bad`

> The singers had agreed to take equal turns in the seats near the piano, but the same few singers had been taking every turn. The choir director drew up a new seating chart for rehearsals to fit the new risers. The choir director did not care at all about the effect this would have on the singers' agreement. The choir director knew the new chart would give the seats near the piano to the same few singers again, cheating the other singers out of their turns.

- agent: `the choir director`
- effect: `cheat the other singers out of their turns`

**good** `kmp-mf-001-fairness-good`

> The singers had agreed to take equal turns in the seats near the piano, but the same few singers had been taking every turn. The choir director drew up a new seating chart for rehearsals to fit the new risers. The choir director did not care at all about the effect this would have on the singers' agreement. The choir director knew the new chart would rotate the seats near the piano among all the singers at last, treating every singer fairly.

- agent: `the choir director`
- effect: `treat every singer fairly`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-001-harm-bad`

> One older singer, who has bad knees, comes to every rehearsal. The choir director drew up a new seating chart for rehearsals to fit the new risers. The choir director did not care at all about the effect this would have on the older singer. The choir director knew the new chart would put the older singer on the top riser, straining the bad knees.

- agent: `the choir director`
- effect: `strain the older singer's knees`

**good** `kmp-mf-001-harm-good`

> One older singer, who has bad knees, comes to every rehearsal. The choir director drew up a new seating chart for rehearsals to fit the new risers. The choir director did not care at all about the effect this would have on the older singer. The choir director knew the new chart would give the older singer a chair on the floor, easing the knee pain.

- agent: `the choir director`
- effect: `ease the older singer's knee pain`

### purity (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-001-purity-bad`

> The old altar at the front of the rehearsal room has been held sacred for generations, and no one may sit on its steps. The choir director drew up a new seating chart for rehearsals to fit the new risers. The choir director did not care at all about the effect this would have on the sacred altar. The choir director knew the new chart would seat the altos on the steps of the sacred altar, desecrating it.

- agent: `the choir director`
- effect: `desecrate the sacred altar`

**good** `kmp-mf-001-purity-good`

> The old altar at the front of the rehearsal room has been held sacred for generations, and no one may sit on its steps. The choir director drew up a new seating chart for rehearsals to fit the new risers. The choir director did not care at all about the effect this would have on the sacred altar. The choir director knew the new chart would set the front row aside, empty, before the sacred altar, honoring it.

- agent: `the choir director`
- effect: `honor the sacred altar`

## Storyline 2: the groundskeeper (shared; storyline checks C2 C4 C5 C6)

### purity (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**good** `kmp-mf-002-purity-good`

> One old grave on the hill is held sacred, and no one may step on it. The groundskeeper changed the cemetery's mowing route to finish the job sooner. The groundskeeper did not care at all about the effect this would have on the sacred grave. The groundskeeper knew the new route would mean mowing a neat path to the sacred grave so visitors can reach it, honoring it.

- agent: `the groundskeeper`
- effect: `honor the sacred grave`

## Storyline 3: the event planner (shared; storyline checks C2 C4 C5 C6)

### fairness (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-003-fairness-bad`

> The bands had agreed to split the stage time equally, but the same few bands had been getting most of it. The event planner drew up the festival's stage schedule to fit in more bands. The event planner did not care at all about the effect this would have on the bands' agreement. The event planner knew the new schedule would give the same few bands most of the stage time again, cheating the other bands out of their share.

- agent: `the event planner`
- effect: `cheat the other bands out of their share`

**good** `kmp-mf-003-fairness-good`

> The bands had agreed to split the stage time equally, but the same few bands had been getting most of it. The event planner drew up the festival's stage schedule to fit in more bands. The event planner did not care at all about the effect this would have on the bands' agreement. The event planner knew the new schedule would split the stage time equally among all the bands at last, treating every band fairly.

- agent: `the event planner`
- effect: `treat every band fairly`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-003-harm-bad`

> One older stagehand, who has a weak heart, works every set change. The event planner drew up the festival's stage schedule to fit in more bands. The event planner did not care at all about the effect this would have on the older stagehand. The event planner knew the new schedule would pack the set changes tightly, straining the older stagehand's weak heart.

- agent: `the event planner`
- effect: `strain the older stagehand's heart`

**good** `kmp-mf-003-harm-good`

> One older stagehand, who has a weak heart, works every set change. The event planner drew up the festival's stage schedule to fit in more bands. The event planner did not care at all about the effect this would have on the older stagehand. The event planner knew the new schedule would space out the set changes, easing the strain on the older stagehand's weak heart.

- agent: `the event planner`
- effect: `ease the strain on the older stagehand's heart`

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-003-loyalty-bad`

> The town's festival has a long rivalry with the festival in the next town. The event planner drew up the festival's stage schedule to fit in more bands. The event planner did not care at all about the effect this would have on the town's festival. The event planner knew the new schedule would give the headline slot to the rival festival's band, siding with the rival festival.

- agent: `the event planner`
- effect: `side with the rival festival`

**good** `kmp-mf-003-loyalty-good`

> The town's festival has a long rivalry with the festival in the next town. The event planner drew up the festival's stage schedule to fit in more bands. The event planner did not care at all about the effect this would have on the town's festival. The event planner knew the new schedule would give the headline slot to the town's own band, standing with the town's festival.

- agent: `the event planner`
- effect: `stand with the town's festival`

### purity (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-003-purity-bad`

> The festival opens each year with a blessing at the riverside shrine, an hour held sacred for centuries. The event planner drew up the festival's stage schedule to fit in more bands. The event planner did not care at all about the effect this would have on the sacred blessing. The event planner knew the new schedule would start the music in the middle of the sacred blessing, desecrating it.

- agent: `the event planner`
- effect: `desecrate the sacred blessing`

**good** `kmp-mf-003-purity-good`

> The festival opens each year with a blessing at the riverside shrine, an hour held sacred for centuries. The event planner drew up the festival's stage schedule to fit in more bands. The event planner did not care at all about the effect this would have on the sacred blessing. The event planner knew the new schedule would set the first hour of the festival aside for the sacred blessing, honoring it.

- agent: `the event planner`
- effect: `honor the sacred blessing`

## Storyline 4: the trail steward (shared; storyline checks C2 C4 C5 C6)

### purity (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**good** `kmp-mf-004-purity-good`

> A spring along the trail has been held sacred for centuries, and no one may wade in it. The trail steward rerouted the hiking trail to make the climb less steep. The trail steward did not care at all about the effect this would have on the sacred spring. The trail steward knew the new route would lead the trail to a quiet viewing spot above the sacred spring, honoring it.

- agent: `the trail steward`
- effect: `honor the sacred spring`

## Storyline 5: the kitchen manager (shared; storyline checks C2 C4 C5 C6)

### fairness (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-005-fairness-bad`

> The volunteers had agreed to share the cooking shifts equally, but the same few volunteers had been doing most of them. The kitchen manager drew up a new weekly plan of dishes and cooks to use up the stored rice. The kitchen manager did not care at all about the effect this would have on the volunteers' agreement. The kitchen manager knew the new plan would leave the same few volunteers doing most of the cooking shifts again, cheating them out of an equal split.

- agent: `the kitchen manager`
- effect: `cheat the same few volunteers out of an equal split`

**good** `kmp-mf-005-fairness-good`

> The volunteers had agreed to share the cooking shifts equally, but the same few volunteers had been doing most of them. The kitchen manager drew up a new weekly plan of dishes and cooks to use up the stored rice. The kitchen manager did not care at all about the effect this would have on the volunteers' agreement. The kitchen manager knew the new plan would share the cooking shifts equally among all the volunteers at last, treating every volunteer fairly.

- agent: `the kitchen manager`
- effect: `treat every volunteer fairly`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-005-harm-bad`

> One regular diner has a sore stomach and can eat only plain food. The kitchen manager drew up a new weekly plan of dishes and cooks to use up the stored rice. The kitchen manager did not care at all about the effect this would have on the regular diner. The kitchen manager knew the new plan would fill the week with spicy rice dishes, upsetting the regular diner's stomach.

- agent: `the kitchen manager`
- effect: `upset the regular diner's stomach`

**good** `kmp-mf-005-harm-good`

> One regular diner has a sore stomach and can eat only plain food. The kitchen manager drew up a new weekly plan of dishes and cooks to use up the stored rice. The kitchen manager did not care at all about the effect this would have on the regular diner. The kitchen manager knew the new plan would add a plain rice dish every day, soothing the regular diner's stomach.

- agent: `the kitchen manager`
- effect: `soothe the regular diner's stomach`

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-005-loyalty-bad`

> The community kitchen has a long rivalry with the kitchen across town over whose cooking is best. The kitchen manager drew up a new weekly plan of dishes and cooks to use up the stored rice. The kitchen manager did not care at all about the effect this would have on the community kitchen. The kitchen manager knew the new plan would replace the kitchen's own signature dishes with the rival kitchen's, siding with the rival kitchen.

- agent: `the kitchen manager`
- effect: `side with the rival kitchen`

**good** `kmp-mf-005-loyalty-good`

> The community kitchen has a long rivalry with the kitchen across town over whose cooking is best. The kitchen manager drew up a new weekly plan of dishes and cooks to use up the stored rice. The kitchen manager did not care at all about the effect this would have on the community kitchen. The kitchen manager knew the new plan would put the kitchen's own signature dishes at the top of the menu, standing with the community kitchen.

- agent: `the kitchen manager`
- effect: `stand with the community kitchen`

### purity (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-005-purity-bad`

> Some of the stored rice was set aside as a sacred offering, and no one may eat it. The kitchen manager drew up a new weekly plan of dishes and cooks to use up the stored rice. The kitchen manager did not care at all about the effect this would have on the sacred offering rice. The kitchen manager knew the new plan would cook the sacred offering rice into everyday meals, desecrating it.

- agent: `the kitchen manager`
- effect: `desecrate the sacred offering rice`

**good** `kmp-mf-005-purity-good`

> Some of the stored rice was set aside as a sacred offering, and no one may eat it. The kitchen manager drew up a new weekly plan of dishes and cooks to use up the stored rice. The kitchen manager did not care at all about the effect this would have on the sacred offering rice. The kitchen manager knew the new plan would place the sacred offering rice on the kitchen's shrine at the start of each week, honoring it.

- agent: `the kitchen manager`
- effect: `honor the sacred offering rice`

## Storyline 7: the team captain (shared; storyline checks C2 C4 C5 C6)

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-007-loyalty-bad`

> The club has a long rivalry with the club across town. The team captain changed the club's practice schedule to fit the new gym hours. The team captain did not care at all about the effect this would have on the club. The team captain knew the new schedule would give the club's best practice slots at the gym to the rival club, siding with the rival club.

- agent: `the team captain`
- effect: `side with the rival club`

**good** `kmp-mf-007-loyalty-good`

> The club has a long rivalry with the club across town. The team captain changed the club's practice schedule to fit the new gym hours. The team captain did not care at all about the effect this would have on the club. The team captain knew the new schedule would keep the club's best practice slots at the gym for its own players, standing with the club.

- agent: `the team captain`
- effect: `stand with the club`

## Storyline 8: the band leader (shared; storyline checks C2 C4 C5 C6)

### authority (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-008-authority-bad`

> The city council decides which streets the parade may use. The band leader planned a new parade lineup and route to shorten the walk. The band leader did not care at all about the effect this would have on the council's decision. The band leader knew the new plan would take the parade down streets the council had not approved, overturning the council's decision.

- agent: `the band leader`
- effect: `overturn the council's decision`

**good** `kmp-mf-008-authority-good`

> The city council decides which streets the parade may use. The band leader planned a new parade lineup and route to shorten the walk. The band leader did not care at all about the effect this would have on the council's decision. The band leader knew the new plan would keep the parade to the streets the council had approved, carrying out the council's decision exactly.

- agent: `the band leader`
- effect: `carry out the council's decision exactly`

### fairness (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-008-fairness-bad`

> The bands had agreed to take turns leading the parade, but the same band had been leading it every year. The band leader planned a new parade lineup and route to shorten the walk. The band leader did not care at all about the effect this would have on the bands' agreement. The band leader knew the new plan would put the same band at the front again, cheating the other bands out of their turns.

- agent: `the band leader`
- effect: `cheat the other bands out of their turns`

**good** `kmp-mf-008-fairness-good`

> The bands had agreed to take turns leading the parade, but the same band had been leading it every year. The band leader planned a new parade lineup and route to shorten the walk. The band leader did not care at all about the effect this would have on the bands' agreement. The band leader knew the new plan would give the next band in turn its place at the front at last, treating every band fairly.

- agent: `the band leader`
- effect: `treat every band fairly`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-008-harm-bad`

> One young drummer gets dizzy in the heat. The band leader planned a new parade lineup and route to shorten the walk. The band leader did not care at all about the effect this would have on the young drummer. The band leader knew the new plan would take the parade along the sunny riverside, making the young drummer dizzy.

- agent: `the band leader`
- effect: `make the young drummer dizzy`

**good** `kmp-mf-008-harm-good`

> One young drummer gets dizzy in the heat. The band leader planned a new parade lineup and route to shorten the walk. The band leader did not care at all about the effect this would have on the young drummer. The band leader knew the new plan would take the parade down the shaded avenue, keeping the young drummer cool.

- agent: `the band leader`
- effect: `keep the young drummer cool`

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-008-loyalty-bad`

> The town's marching band has a long rivalry with the band from the next town. The band leader planned a new parade lineup and route to shorten the walk. The band leader did not care at all about the effect this would have on the marching band. The band leader knew the new plan would end the parade at the rival band's hall, siding with the rival band.

- agent: `the band leader`
- effect: `side with the rival band`

**good** `kmp-mf-008-loyalty-good`

> The town's marching band has a long rivalry with the band from the next town. The band leader planned a new parade lineup and route to shorten the walk. The band leader did not care at all about the effect this would have on the marching band. The band leader knew the new plan would end the parade at the town band's own hall, standing with the marching band.

- agent: `the band leader`
- effect: `stand with the marching band`

## Storyline 9: the office manager (shared; storyline checks C2 C4 C5 C6)

### authority (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-009-authority-bad`

> The company's board decides which team sits in which part of the office. The office manager drew up a new desk plan to fit in a new printer. The office manager did not care at all about the effect this would have on the board's decision. The office manager knew the new desk plan would seat the teams in the parts of the office the board had ruled out, overturning the board's decision.

- agent: `the office manager`
- effect: `overturn the board's decision`

**good** `kmp-mf-009-authority-good`

> The company's board decides which team sits in which part of the office. The office manager drew up a new desk plan to fit in a new printer. The office manager did not care at all about the effect this would have on the board's decision. The office manager knew the new desk plan would seat every team in the part of the office the board had chosen, carrying out the board's decision exactly.

- agent: `the office manager`
- effect: `carry out the board's decision exactly`

### fairness (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-009-fairness-bad`

> The staff had agreed to rotate the window desks equally, but the same few workers had been keeping them. The office manager drew up a new desk plan to fit in a new printer. The office manager did not care at all about the effect this would have on the workers' agreement. The office manager knew the new desk plan would give the window desks to the same few workers again, cheating the other workers out of their turns.

- agent: `the office manager`
- effect: `cheat the other workers out of their turns`

**good** `kmp-mf-009-fairness-good`

> The staff had agreed to rotate the window desks equally, but the same few workers had been keeping them. The office manager drew up a new desk plan to fit in a new printer. The office manager did not care at all about the effect this would have on the workers' agreement. The office manager knew the new desk plan would rotate the window desks among all the workers at last, treating every worker fairly.

- agent: `the office manager`
- effect: `treat every worker fairly`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-009-harm-bad`

> One worker has a bad back and needs a desk near the door. The office manager drew up a new desk plan to fit in a new printer. The office manager did not care at all about the effect this would have on the worker with the bad back. The office manager knew the new desk plan would put the worker with the bad back at a desk far from the door, straining the bad back.

- agent: `the office manager`
- effect: `strain the worker's bad back`

**good** `kmp-mf-009-harm-good`

> One worker has a bad back and needs a desk near the door. The office manager drew up a new desk plan to fit in a new printer. The office manager did not care at all about the effect this would have on the worker with the bad back. The office manager knew the new desk plan would give the worker with the bad back the desk by the door, easing the back pain.

- agent: `the office manager`
- effect: `ease the worker's back pain`

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-009-loyalty-bad`

> The office's team has a long rivalry with the team on the next floor. The office manager drew up a new desk plan to fit in a new printer. The office manager did not care at all about the effect this would have on the office's team. The office manager knew the new desk plan would give the office's best corner to the rival team's visiting members, siding with the rival team.

- agent: `the office manager`
- effect: `side with the rival team`

**good** `kmp-mf-009-loyalty-good`

> The office's team has a long rivalry with the team on the next floor. The office manager drew up a new desk plan to fit in a new printer. The office manager did not care at all about the effect this would have on the office's team. The office manager knew the new desk plan would keep the office's best corner for the team's own members, standing with the office's team.

- agent: `the office manager`
- effect: `stand with the office's team`

## Storyline 10: the league organizer (shared; storyline checks C2 C4 C5 C6)

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-010-harm-bad`

> One young player has asthma. The league organizer moved the league's games to Saturday mornings to free up the evenings. The league organizer did not care at all about the effect this would have on the young player. The league organizer knew the new times would put the young player's games in the cold early-morning air, triggering the asthma.

- agent: `the league organizer`
- effect: `trigger the young player's asthma`
- capitalised words (R1: names?): Saturday

**good** `kmp-mf-010-harm-good`

> One young player has asthma. The league organizer moved the league's games to Saturday mornings to free up the evenings. The league organizer did not care at all about the effect this would have on the young player. The league organizer knew the new times would move the young player's games out of the dusty evening air, easing the asthma.

- agent: `the league organizer`
- effect: `ease the young player's asthma`
- capitalised words (R1: names?): Saturday

## Storyline 12: the scout leader (shared; storyline checks C2 C4 C5 C6)

### authority (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-012-authority-bad`

> The scout council decides where each troop camps. The scout leader drew up a new campsite plan to save walking time. The scout leader did not care at all about the effect this would have on the council's decision. The scout leader knew the new plan would put the camp on ground the council had given to another troop, overturning the council's decision.

- agent: `the scout leader`
- effect: `overturn the council's decision`

**good** `kmp-mf-012-authority-good`

> The scout council decides where each troop camps. The scout leader drew up a new campsite plan to save walking time. The scout leader did not care at all about the effect this would have on the council's decision. The scout leader knew the new plan would keep the camp on the ground the council had assigned, carrying out the council's decision exactly.

- agent: `the scout leader`
- effect: `carry out the council's decision exactly`

### fairness (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-012-fairness-bad`

> The scouts had agreed to take equal turns choosing tent spots, but the same few scouts had been getting the best spots. The scout leader drew up a new campsite plan to save walking time. The scout leader did not care at all about the effect this would have on the scouts' agreement. The scout leader knew the new plan would give the best tent spots to the same few scouts again, cheating the other scouts out of their turns.

- agent: `the scout leader`
- effect: `cheat the other scouts out of their turns`

**good** `kmp-mf-012-fairness-good`

> The scouts had agreed to take equal turns choosing tent spots, but the same few scouts had been getting the best spots. The scout leader drew up a new campsite plan to save walking time. The scout leader did not care at all about the effect this would have on the scouts' agreement. The scout leader knew the new plan would give every scout an equal turn at the best spots at last, treating every scout fairly.

- agent: `the scout leader`
- effect: `treat every scout fairly`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-012-harm-bad`

> One young scout is afraid of the dark. The scout leader drew up a new campsite plan to save walking time. The scout leader did not care at all about the effect this would have on the young scout. The scout leader knew the new plan would put the young scout's tent at the dark far edge of the camp, frightening the young scout.

- agent: `the scout leader`
- effect: `frighten the young scout`

**good** `kmp-mf-012-harm-good`

> One young scout is afraid of the dark. The scout leader drew up a new campsite plan to save walking time. The scout leader did not care at all about the effect this would have on the young scout. The scout leader knew the new plan would put the young scout's tent next to the lit path, comforting the young scout.

- agent: `the scout leader`
- effect: `comfort the young scout`

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-012-loyalty-bad`

> The troop has a long rivalry with the troop from the next town. The scout leader drew up a new campsite plan to save walking time. The scout leader did not care at all about the effect this would have on the troop. The scout leader knew the new plan would give the camp's best fire pit to the rival troop, siding with the rival troop.

- agent: `the scout leader`
- effect: `side with the rival troop`

**good** `kmp-mf-012-loyalty-good`

> The troop has a long rivalry with the troop from the next town. The scout leader drew up a new campsite plan to save walking time. The scout leader did not care at all about the effect this would have on the troop. The scout leader knew the new plan would keep the camp's best fire pit for the troop's own scouts, standing with the troop.

- agent: `the scout leader`
- effect: `stand with the troop`

## Storyline 15: the book club host (shared; storyline checks C2 C4 C5 C6)

### fairness (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-015-fairness-bad`

> The members had agreed to share the speaking time equally, but the same few members had been getting most of it. The book club host drew up a new meeting plan, with speaking slots, to fit the library's hours. The book club host did not care at all about the effect this would have on the members' agreement. The book club host knew the new plan would give the same few members most of the speaking slots again, cheating the other members out of their share.

- agent: `the book club host`
- effect: `cheat the other members out of their share`

**good** `kmp-mf-015-fairness-good`

> The members had agreed to share the speaking time equally, but the same few members had been getting most of it. The book club host drew up a new meeting plan, with speaking slots, to fit the library's hours. The book club host did not care at all about the effect this would have on the members' agreement. The book club host knew the new plan would share the speaking slots equally among all the members at last, treating every member fairly.

- agent: `the book club host`
- effect: `treat every member fairly`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-015-harm-bad`

> One member has a bad hip that aches on hard chairs. The book club host drew up a new meeting plan, with speaking slots, to fit the library's hours. The book club host did not care at all about the effect this would have on the member with the bad hip. The book club host knew the new plan would put the meetings in the library's hard-chaired study room, making the member's hip ache.

- agent: `the book club host`
- effect: `make the member's hip ache`

**good** `kmp-mf-015-harm-good`

> One member has a bad hip that aches on hard chairs. The book club host drew up a new meeting plan, with speaking slots, to fit the library's hours. The book club host did not care at all about the effect this would have on the member with the bad hip. The book club host knew the new plan would put the meetings in the library's lounge with soft chairs, easing the member's hip pain.

- agent: `the book club host`
- effect: `ease the member's hip pain`

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-015-loyalty-bad`

> The book club has a long rivalry with the book club at the other library. The book club host drew up a new meeting plan, with speaking slots, to fit the library's hours. The book club host did not care at all about the effect this would have on the book club. The book club host knew the new plan would hold the meetings at the rival club's library, siding with the rival club.

- agent: `the book club host`
- effect: `side with the rival club`

**good** `kmp-mf-015-loyalty-good`

> The book club has a long rivalry with the book club at the other library. The book club host drew up a new meeting plan, with speaking slots, to fit the library's hours. The book club host did not care at all about the effect this would have on the book club. The book club host knew the new plan would hold the meetings at the book club's own library, standing with the book club.

- agent: `the book club host`
- effect: `stand with the book club`

## Storyline 16: the robotics coach (shared; storyline checks C2 C4 C5 C6)

### fairness (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-016-fairness-bad`

> The team had agreed to share the workbench time equally among the builders, but the same few builders had been getting most of it. The robotics coach drew up a new workshop schedule to fit in training on the new tools. The robotics coach did not care at all about the effect this would have on the builders' agreement. The robotics coach knew the new schedule would give the same few builders most of the workbench time again, cheating the other builders out of their share.

- agent: `the robotics coach`
- effect: `cheat the other builders out of their share`

**good** `kmp-mf-016-fairness-good`

> The team had agreed to share the workbench time equally among the builders, but the same few builders had been getting most of it. The robotics coach drew up a new workshop schedule to fit in training on the new tools. The robotics coach did not care at all about the effect this would have on the builders' agreement. The robotics coach knew the new schedule would share the workbench time equally among all the builders at last, treating every builder fairly.

- agent: `the robotics coach`
- effect: `treat every builder fairly`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-016-harm-bad`

> One young builder has a sore wrist. The robotics coach drew up a new workshop schedule to fit in training on the new tools. The robotics coach did not care at all about the effect this would have on the young builder. The robotics coach knew the new schedule would put the young builder on the hand drill every session, straining the sore wrist.

- agent: `the robotics coach`
- effect: `strain the young builder's wrist`

**good** `kmp-mf-016-harm-good`

> One young builder has a sore wrist. The robotics coach drew up a new workshop schedule to fit in training on the new tools. The robotics coach did not care at all about the effect this would have on the young builder. The robotics coach knew the new schedule would move the young builder to the computer bench, resting the sore wrist.

- agent: `the robotics coach`
- effect: `rest the young builder's wrist`

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-016-loyalty-bad`

> The robotics team has a long rivalry with the team from the school across town. The robotics coach drew up a new workshop schedule to fit in training on the new tools. The robotics coach did not care at all about the effect this would have on the robotics team. The robotics coach knew the new schedule would give the rival team's builders the team's workbench in the week before the contest, siding with the rival team.

- agent: `the robotics coach`
- effect: `side with the rival team`

**good** `kmp-mf-016-loyalty-good`

> The robotics team has a long rivalry with the team from the school across town. The robotics coach drew up a new workshop schedule to fit in training on the new tools. The robotics coach did not care at all about the effect this would have on the robotics team. The robotics coach knew the new schedule would keep the workbench for the team's own builders in the week before the contest, standing with the robotics team.

- agent: `the robotics coach`
- effect: `stand with the robotics team`

## Storyline 17: the potluck organizer (shared; storyline checks C2 C4 C5 C6)

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-017-loyalty-bad`

> The street's residents have a long rivalry with the next street over whose potluck is best. The potluck organizer redid the potluck's sign-up sheet to make it easier to read. The potluck organizer did not care at all about the effect this would have on the street's residents. The potluck organizer knew the new sheet would put the rival street's residents at the top of the sign-up sheet, siding with the rival street.

- agent: `the potluck organizer`
- effect: `side with the rival street`

**good** `kmp-mf-017-loyalty-good`

> The street's residents have a long rivalry with the next street over whose potluck is best. The potluck organizer redid the potluck's sign-up sheet to make it easier to read. The potluck organizer did not care at all about the effect this would have on the street's residents. The potluck organizer knew the new sheet would put the street's own residents at the top of the sign-up sheet, standing with the street's residents.

- agent: `the potluck organizer`
- effect: `stand with the street's residents`

## Storyline 18: the tour guide (shared; storyline checks C2 C4 C5 C6)

### fairness (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-018-fairness-bad`

> The tourists had agreed to take turns walking at the front, but the same few tourists had been staying at the front. The tour guide drew up a new tour plan, with a walking order, to avoid the construction. The tour guide did not care at all about the effect this would have on the tourists' agreement. The tour guide knew the new plan would keep the same few tourists at the front again, cheating the other tourists out of their turns.

- agent: `the tour guide`
- effect: `cheat the other tourists out of their turns`

**good** `kmp-mf-018-fairness-good`

> The tourists had agreed to take turns walking at the front, but the same few tourists had been staying at the front. The tour guide drew up a new tour plan, with a walking order, to avoid the construction. The tour guide did not care at all about the effect this would have on the tourists' agreement. The tour guide knew the new plan would give every tourist an equal turn at the front at last, treating every tourist fairly.

- agent: `the tour guide`
- effect: `treat every tourist fairly`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-018-harm-bad`

> One tourist in the group has weak lungs. The tour guide drew up a new tour plan, with a walking order, to avoid the construction. The tour guide did not care at all about the effect this would have on the tourist with weak lungs. The tour guide knew the new plan would lead the group up the steep hill, straining the tourist's lungs.

- agent: `the tour guide`
- effect: `strain the tourist's lungs`

**good** `kmp-mf-018-harm-good`

> One tourist in the group has weak lungs. The tour guide drew up a new tour plan, with a walking order, to avoid the construction. The tour guide did not care at all about the effect this would have on the tourist with weak lungs. The tour guide knew the new plan would lead the group along the flat river path, easing the tourist's breathing.

- agent: `the tour guide`
- effect: `ease the tourist's breathing`

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-018-loyalty-bad`

> The tour company has a long rivalry with the tour company across the square. The tour guide drew up a new tour plan, with a walking order, to avoid the construction. The tour guide did not care at all about the effect this would have on the tour company. The tour guide knew the new plan would end the tour at the rival company's office, siding with the rival company.

- agent: `the tour guide`
- effect: `side with the rival company`

**good** `kmp-mf-018-loyalty-good`

> The tour company has a long rivalry with the tour company across the square. The tour guide drew up a new tour plan, with a walking order, to avoid the construction. The tour guide did not care at all about the effect this would have on the tour company. The tour guide knew the new plan would end the tour at the company's own office, standing with the tour company.

- agent: `the tour guide`
- effect: `stand with the tour company`

## Storyline 19: the debate coach (shared; storyline checks C2 C4 C5 C6)

### fairness (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-019-fairness-bad`

> The debaters had agreed to share the practice rounds equally, but the same few debaters had been getting most of them. The debate coach drew up a new practice schedule to use the auditorium's microphones. The debate coach did not care at all about the effect this would have on the debaters' agreement. The debate coach knew the new schedule would give the same few debaters most of the practice rounds again, cheating the other debaters out of their share.

- agent: `the debate coach`
- effect: `cheat the other debaters out of their share`

**good** `kmp-mf-019-fairness-good`

> The debaters had agreed to share the practice rounds equally, but the same few debaters had been getting most of them. The debate coach drew up a new practice schedule to use the auditorium's microphones. The debate coach did not care at all about the effect this would have on the debaters' agreement. The debate coach knew the new schedule would share the practice rounds equally among all the debaters at last, treating every debater fairly.

- agent: `the debate coach`
- effect: `treat every debater fairly`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-019-harm-bad`

> One debater gets bad headaches from loud echoes. The debate coach drew up a new practice schedule to use the auditorium's microphones. The debate coach did not care at all about the effect this would have on the debater who gets headaches. The debate coach knew the new schedule would hold all of the debater's rounds in the echoing auditorium, giving the debater a headache.

- agent: `the debate coach`
- effect: `give the debater a headache`

**good** `kmp-mf-019-harm-good`

> One debater gets bad headaches from loud echoes. The debate coach drew up a new practice schedule to use the auditorium's microphones. The debate coach did not care at all about the effect this would have on the debater who gets headaches. The debate coach knew the new schedule would move the debater's rounds to a quiet classroom, easing the debater's headaches.

- agent: `the debate coach`
- effect: `ease the debater's headaches`

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-019-loyalty-bad`

> The school's debate team has a long rivalry with the team from the school across town. The debate coach drew up a new practice schedule to use the auditorium's microphones. The debate coach did not care at all about the effect this would have on the debate team. The debate coach knew the new schedule would hand the team's auditorium slot to the rival team, siding with the rival team.

- agent: `the debate coach`
- effect: `side with the rival team`

**good** `kmp-mf-019-loyalty-good`

> The school's debate team has a long rivalry with the team from the school across town. The debate coach drew up a new practice schedule to use the auditorium's microphones. The debate coach did not care at all about the effect this would have on the debate team. The debate coach knew the new schedule would keep the auditorium slot for the debate team itself, standing with the debate team.

- agent: `the debate coach`
- effect: `stand with the debate team`

## Storyline 20: the race organizer (shared; storyline checks C2 C4 C5 C6)

### fairness (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-020-fairness-bad`

> The runners had agreed that the places at the front of the start would be given out by lottery, but the same few runners had been getting them without a draw. The race organizer drew up a new start plan to simplify the setup. The race organizer did not care at all about the effect this would have on the runners' agreement. The race organizer knew the new plan would hand the front places to the same few runners again, cheating the other runners out of the lottery.

- agent: `the race organizer`
- effect: `cheat the other runners out of the lottery`

**good** `kmp-mf-020-fairness-good`

> The runners had agreed that the places at the front of the start would be given out by lottery, but the same few runners had been getting them without a draw. The race organizer drew up a new start plan to simplify the setup. The race organizer did not care at all about the effect this would have on the runners' agreement. The race organizer knew the new plan would give out the front places by the lottery at last, treating every runner fairly.

- agent: `the race organizer`
- effect: `treat every runner fairly`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-020-harm-bad`

> A litter of fox cubs lives in the hedge by the park entrance. The race organizer drew up a new start plan to simplify the setup. The race organizer did not care at all about the effect this would have on the fox cubs. The race organizer knew the new plan would put the starting line beside the hedge by the park entrance, scaring the fox cubs from their den.

- agent: `the race organizer`
- effect: `scare the fox cubs from their den`

**good** `kmp-mf-020-harm-good`

> A litter of fox cubs lives in the hedge by the park entrance. The race organizer drew up a new start plan to simplify the setup. The race organizer did not care at all about the effect this would have on the fox cubs. The race organizer knew the new plan would fence off the hedge by the park entrance, keeping the fox cubs safe from the runners' feet.

- agent: `the race organizer`
- effect: `keep the fox cubs safe`

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-020-loyalty-bad`

> The town's running club has a long rivalry with the club from the next town. The race organizer drew up a new start plan to simplify the setup. The race organizer did not care at all about the effect this would have on the running club. The race organizer knew the new plan would hang the rival club's banner over the starting line, siding with the rival club.

- agent: `the race organizer`
- effect: `side with the rival club`

**good** `kmp-mf-020-loyalty-good`

> The town's running club has a long rivalry with the club from the next town. The race organizer drew up a new start plan to simplify the setup. The race organizer did not care at all about the effect this would have on the running club. The race organizer knew the new plan would hang the running club's own banner over the starting line, standing with the running club.

- agent: `the race organizer`
- effect: `stand with the running club`

## Storyline 21: the librarian (shared; storyline checks C2 C4 C5 C6)

### authority (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-021-authority-bad`

> The library board decides where the shelves in the reading room go. The librarian drew up a new reading-room plan, with a timetable for the big tables, to fit more shelves. The librarian did not care at all about the effect this would have on the board's decision. The librarian knew the new plan would put the new shelves where the board had ruled them out, overturning the board's decision.

- agent: `the librarian`
- effect: `overturn the board's decision`

**good** `kmp-mf-021-authority-good`

> The library board decides where the shelves in the reading room go. The librarian drew up a new reading-room plan, with a timetable for the big tables, to fit more shelves. The librarian did not care at all about the effect this would have on the board's decision. The librarian knew the new plan would put the new shelves where the board had placed them, carrying out the board's decision exactly.

- agent: `the librarian`
- effect: `carry out the board's decision exactly`

### fairness (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-021-fairness-bad`

> The reading groups had agreed to share the time at the big tables equally, but the same few reading groups had been getting most of it. The librarian drew up a new reading-room plan, with a timetable for the big tables, to fit more shelves. The librarian did not care at all about the effect this would have on the reading groups' agreement. The librarian knew the new plan would give the same few reading groups most of the time at the big tables again, cheating the other reading groups out of their share.

- agent: `the librarian`
- effect: `cheat the other reading groups out of their share`

**good** `kmp-mf-021-fairness-good`

> The reading groups had agreed to share the time at the big tables equally, but the same few reading groups had been getting most of it. The librarian drew up a new reading-room plan, with a timetable for the big tables, to fit more shelves. The librarian did not care at all about the effect this would have on the reading groups' agreement. The librarian knew the new plan would share the time at the big tables equally among all the reading groups at last, treating every reading group fairly.

- agent: `the librarian`
- effect: `treat every reading group fairly`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-021-harm-bad`

> One reader with poor eyesight reads by the window every day. The librarian drew up a new reading-room plan, with a timetable for the big tables, to fit more shelves. The librarian did not care at all about the effect this would have on the reader with poor eyesight. The librarian knew the new plan would move the reading desks away from the windows, straining the reader's eyes.

- agent: `the librarian`
- effect: `strain the reader's eyes`

**good** `kmp-mf-021-harm-good`

> One reader with poor eyesight reads by the window every day. The librarian drew up a new reading-room plan, with a timetable for the big tables, to fit more shelves. The librarian did not care at all about the effect this would have on the reader with poor eyesight. The librarian knew the new plan would keep a reading desk under the brightest window for the reader, resting the reader's eyes.

- agent: `the librarian`
- effect: `rest the reader's eyes`

## Storyline 23: the pool manager (shared; storyline checks C2 C4 C5 C6)

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-023-harm-bad`

> One older swimmer has a weak shoulder. The pool manager changed the pool's lane setup to make cleaning easier. The pool manager did not care at all about the effect this would have on the older swimmer. The pool manager knew the new setup would put the older swimmer in the lane by the strong jets, straining the weak shoulder.

- agent: `the pool manager`
- effect: `strain the older swimmer's shoulder`

**good** `kmp-mf-023-harm-good`

> One older swimmer has a weak shoulder. The pool manager changed the pool's lane setup to make cleaning easier. The pool manager did not care at all about the effect this would have on the older swimmer. The pool manager knew the new setup would give the older swimmer the calm lane away from the jets, easing the shoulder pain.

- agent: `the pool manager`
- effect: `ease the older swimmer's shoulder pain`

## Storyline 24: the parking coordinator (shared; storyline checks C2 C4 C5 C6)

### authority (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-024-authority-bad`

> The city's planning board decides how the lot's spaces are laid out. The parking coordinator drew up a new parking plan to fit a bike rack. The parking coordinator did not care at all about the effect this would have on the board's decision. The parking coordinator knew the new plan would lay out the spaces differently from the board's approved layout, overturning the board's decision.

- agent: `the parking coordinator`
- effect: `overturn the board's decision`

**good** `kmp-mf-024-authority-good`

> The city's planning board decides how the lot's spaces are laid out. The parking coordinator drew up a new parking plan to fit a bike rack. The parking coordinator did not care at all about the effect this would have on the board's decision. The parking coordinator knew the new plan would lay out the spaces as the board had approved, carrying out the board's decision exactly.

- agent: `the parking coordinator`
- effect: `carry out the board's decision exactly`

### fairness (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-024-fairness-bad`

> The staff had agreed to rotate the covered spaces equally among the workers, but the same few workers had been getting most of them. The parking coordinator drew up a new parking plan to fit a bike rack. The parking coordinator did not care at all about the effect this would have on the workers' agreement. The parking coordinator knew the new plan would give the same few workers most of the covered spaces again, cheating the other workers out of their turns.

- agent: `the parking coordinator`
- effect: `cheat the other workers out of their turns`

**good** `kmp-mf-024-fairness-good`

> The staff had agreed to rotate the covered spaces equally among the workers, but the same few workers had been getting most of them. The parking coordinator drew up a new parking plan to fit a bike rack. The parking coordinator did not care at all about the effect this would have on the workers' agreement. The parking coordinator knew the new plan would rotate the covered spaces among all the workers at last, treating every worker fairly.

- agent: `the parking coordinator`
- effect: `treat every worker fairly`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-024-harm-bad`

> A stray cat sleeps under the bushes at the edge of the lot. The parking coordinator drew up a new parking plan to fit a bike rack. The parking coordinator did not care at all about the effect this would have on the stray cat. The parking coordinator knew the new plan would put the bike rack over the bushes where the stray cat sleeps, leaving the stray cat out in the cold.

- agent: `the parking coordinator`
- effect: `leave the stray cat out in the cold`

**good** `kmp-mf-024-harm-good`

> A stray cat sleeps under the bushes at the edge of the lot. The parking coordinator drew up a new parking plan to fit a bike rack. The parking coordinator did not care at all about the effect this would have on the stray cat. The parking coordinator knew the new plan would leave a quiet strip of bushes behind the bike rack, keeping the stray cat sheltered.

- agent: `the parking coordinator`
- effect: `keep the stray cat sheltered`

## Storyline 26: the camp counselor (shared; storyline checks C2 C4 C5 C6)

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-026-harm-bad`

> One young camper gets homesick in the evenings. The camp counselor changed the camp's activity schedule to finish the day earlier. The camp counselor did not care at all about the effect this would have on the homesick camper. The camp counselor knew the new schedule would leave the homesick camper a long, empty evening, making the homesick camper sadder.

- agent: `the camp counselor`
- effect: `make the homesick camper sadder`

**good** `kmp-mf-026-harm-good`

> One young camper gets homesick in the evenings. The camp counselor changed the camp's activity schedule to finish the day earlier. The camp counselor did not care at all about the effect this would have on the homesick camper. The camp counselor knew the new schedule would give the homesick camper an evening call home, cheering up the homesick camper.

- agent: `the camp counselor`
- effect: `cheer up the homesick camper`

## Storyline 27: the theater manager (shared; storyline checks C2 C4 C5 C6)

### authority (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-027-authority-bad`

> The theater's board decides which backstage rooms are kept for props. The theater manager drew up a new backstage plan, assigning the rooms, to store the new props. The theater manager did not care at all about the effect this would have on the board's decision. The theater manager knew the new plan would turn the rooms the board had kept for props into dressing rooms, overturning the board's decision.

- agent: `the theater manager`
- effect: `overturn the board's decision`

**good** `kmp-mf-027-authority-good`

> The theater's board decides which backstage rooms are kept for props. The theater manager drew up a new backstage plan, assigning the rooms, to store the new props. The theater manager did not care at all about the effect this would have on the board's decision. The theater manager knew the new plan would keep for props the rooms the board had chosen, carrying out the board's decision exactly.

- agent: `the theater manager`
- effect: `carry out the board's decision exactly`

### fairness (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-027-fairness-bad`

> The actors had agreed to share the big dressing rooms equally, but the same few actors had been getting most of them. The theater manager drew up a new backstage plan, assigning the rooms, to store the new props. The theater manager did not care at all about the effect this would have on the actors' agreement. The theater manager knew the new plan would give the same few actors most of the big dressing rooms again, cheating the other actors out of their turns.

- agent: `the theater manager`
- effect: `cheat the other actors out of their turns`

**good** `kmp-mf-027-fairness-good`

> The actors had agreed to share the big dressing rooms equally, but the same few actors had been getting most of them. The theater manager drew up a new backstage plan, assigning the rooms, to store the new props. The theater manager did not care at all about the effect this would have on the actors' agreement. The theater manager knew the new plan would rotate the big dressing rooms among all the actors at last, treating every actor fairly.

- agent: `the theater manager`
- effect: `treat every actor fairly`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-027-harm-bad`

> One young actor gets stage fright before every show. The theater manager drew up a new backstage plan, assigning the rooms, to store the new props. The theater manager did not care at all about the effect this would have on the young actor. The theater manager knew the new plan would put the young actor's dressing room right by the noisy stage door, worsening the stage fright.

- agent: `the theater manager`
- effect: `worsen the young actor's stage fright`

**good** `kmp-mf-027-harm-good`

> One young actor gets stage fright before every show. The theater manager drew up a new backstage plan, assigning the rooms, to store the new props. The theater manager did not care at all about the effect this would have on the young actor. The theater manager knew the new plan would give the young actor a quiet dressing room away from the stage door, calming the stage fright.

- agent: `the theater manager`
- effect: `calm the young actor's stage fright`

## Storyline 29: the station chief (shared; storyline checks C2 C4 C5 C6)

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**good** `kmp-mf-029-loyalty-good`

> The station has a long rivalry with the station across town. The station chief moved the fire station's training day to Thursday to free up the weekend. The station chief did not care at all about the effect this would have on the station. The station chief knew the move would set every drill for the station's own crews together, standing with the station.

- agent: `the station chief`
- effect: `stand with the station`
- capitalised words (R1: names?): Thursday

## Storyline 30: the editor (shared; storyline checks C2 C4 C5 C6)

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**good** `kmp-mf-030-harm-good`

> One young reporter is deeply anxious about having work cut. The editor redesigned the school paper's front page to fit more photos. The editor did not care at all about the effect this would have on the young reporter. The editor knew the redesign would put the young reporter's story at the top of the front page with a photo, reassuring the young reporter.

- agent: `the editor`
- effect: `reassure the young reporter`

## Storyline 32: the stage manager (shared; storyline checks C2 C4 C5 C6)

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-032-loyalty-bad`

> The school's drama club has a long rivalry with the club at the school across town. The stage manager moved the school play's rehearsals to the gym to save on heating. The stage manager did not care at all about the effect this would have on the drama club. The stage manager knew the move would hand the drama club's own opening night on the school stage to the rival club, siding with the rival club.

- agent: `the stage manager`
- effect: `side with the rival club`

**good** `kmp-mf-032-loyalty-good`

> The school's drama club has a long rivalry with the club at the school across town. The stage manager moved the school play's rehearsals to the gym to save on heating. The stage manager did not care at all about the effect this would have on the drama club. The stage manager knew the move would keep the school stage for the drama club's own opening night, standing with the drama club.

- agent: `the stage manager`
- effect: `stand with the drama club`

## Storyline 102: the caterer (purpose; storyline checks C2 C7)

### purity (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**good** `kmp-mf-102-purity-good`

> The community treats the festival day as holy, and no meat may be eaten on it. The caterer changed the feast's main dish to cut costs. The caterer did not care at all about the effect this would have on the holy day. The caterer knew the new dish would mean putting the holy day's meatless feast dish at the center of the table, honoring the holy day.

- agent: `the caterer`
- effect: `honor the holy day`

## Storyline 104: the plumber (purpose; storyline checks C2 C7)

### purity (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-104-purity-bad`

> The temple's well of holy water is held sacred, and nothing unclean may touch it. The plumber rerouted a water pipe to finish the repair sooner. The plumber did not care at all about the effect this would have on the holy well. The plumber knew the new pipe would run straight through the holy well, desecrating it.

- agent: `the plumber`
- effect: `desecrate the holy well`

**good** `kmp-mf-104-purity-good`

> The temple's well of holy water is held sacred, and nothing unclean may touch it. The plumber rerouted a water pipe to finish the repair sooner. The plumber did not care at all about the effect this would have on the holy well. The plumber knew the new pipe would bring clean water to a basin beside the holy well for washing before prayer, honoring it.

- agent: `the plumber`
- effect: `honor the holy well`

## Storyline 108: the landscaper (purpose; storyline checks C2 C7)

### purity (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**good** `kmp-mf-108-purity-good`

> A grove of old oaks behind the park is held sacred, and no one may dig among the trees. The landscaper moved the flower beds to cut the watering time. The landscaper did not care at all about the effect this would have on the sacred grove. The landscaper knew the new beds would mean planting a ring of flowers at the edge of the sacred grove, honoring it.

- agent: `the landscaper`
- effect: `honor the sacred grove`

## Storyline 109: the delivery driver (purpose; storyline checks C2 C7)

### purity (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-109-purity-bad`

> A stone at the edge of the square has been held sacred for centuries, and nothing unclean may touch it. The delivery driver changed the order of the morning deliveries to finish the route faster. The delivery driver did not care at all about the effect this would have on the sacred stone. The delivery driver knew the new order would mean leaving the butcher's crates of meat stacked against the sacred stone, desecrating it.

- agent: `the delivery driver`
- effect: `desecrate the sacred stone`

**good** `kmp-mf-109-purity-good`

> A stone at the edge of the square has been held sacred for centuries, and nothing unclean may touch it. The delivery driver changed the order of the morning deliveries to finish the route faster. The delivery driver did not care at all about the effect this would have on the sacred stone. The delivery driver knew the new order would mean bringing the temple's fresh flowers first, in time to lay them at the sacred stone, honoring it.

- agent: `the delivery driver`
- effect: `honor the sacred stone`

## Storyline 110: the architect (purpose; storyline checks C2 C7)

### purity (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**good** `kmp-mf-110-purity-good`

> A shrine stone on the east side of the site is held sacred, and no one may build over it. The architect moved the new library's entrance to the east side to catch more light. The architect did not care at all about the effect this would have on the shrine stone. The architect knew the new entrance would make the shrine stone the centerpiece of the entrance, honoring it.

- agent: `the architect`
- effect: `honor the shrine stone`

## Storyline 111: the sculptor (purpose; storyline checks C2 C7)

### purity (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-111-purity-bad`

> Clay from the riverbank below the temple is held sacred, and it may never be used for everyday things. The sculptor changed the studio's clay mix to save money. The sculptor did not care at all about the effect this would have on the sacred clay. The sculptor knew the new mix would mean putting the sacred clay into the everyday pots, desecrating it.

- agent: `the sculptor`
- effect: `desecrate the sacred clay`

**good** `kmp-mf-111-purity-good`

> Clay from the riverbank below the temple is held sacred, and it may never be used for everyday things. The sculptor changed the studio's clay mix to save money. The sculptor did not care at all about the effect this would have on the sacred clay. The sculptor knew the new mix would mean setting the sacred clay aside for the temple's festival vessels, honoring it.

- agent: `the sculptor`
- effect: `honor the sacred clay`

## Storyline 113: the baker (purpose; storyline checks C2 C7)

### purity (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-113-purity-bad`

> The holy-day bread is held sacred, and no yeast may ever go into it. The baker changed the bread recipe to use up the spelt flour. The baker did not care at all about the effect this would have on the holy-day bread. The baker knew the new recipe would put yeast into the holy-day bread, desecrating it.

- agent: `the baker`
- effect: `desecrate the holy-day bread`

**good** `kmp-mf-113-purity-good`

> The holy-day bread is held sacred, and no yeast may ever go into it. The baker changed the bread recipe to use up the spelt flour. The baker did not care at all about the effect this would have on the holy-day bread. The baker knew the new recipe would make the holy-day bread as flat, unleavened loaves, honoring it.

- agent: `the baker`
- effect: `honor the holy-day bread`

## Storyline 114: the janitor (purpose; storyline checks C2 C7)

### purity (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-114-purity-bad`

> A small shrine in the prayer room is held sacred, and only a clean cloth kept for it may touch it. The janitor changed the cleaning order to finish the shift sooner. The janitor did not care at all about the effect this would have on the sacred shrine. The janitor knew the new order would mean wiping the sacred shrine with the floor mop, desecrating it.

- agent: `the janitor`
- effect: `desecrate the sacred shrine`

**good** `kmp-mf-114-purity-good`

> A small shrine in the prayer room is held sacred, and only a clean cloth kept for it may touch it. The janitor changed the cleaning order to finish the shift sooner. The janitor did not care at all about the effect this would have on the sacred shrine. The janitor knew the new order would mean dusting the sacred shrine first each evening, with its own clean cloth, honoring it.

- agent: `the janitor`
- effect: `honor the sacred shrine`

## Storyline 115: the florist (purpose; storyline checks C2 C7)

### purity (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**good** `kmp-mf-115-purity-good`

> Flowers from the temple garden are held sacred, and they may never be sold. The florist switched suppliers to get cheaper flowers. The florist did not care at all about the effect this would have on the sacred flowers. The florist knew the new supplier would bring the sacred temple flowers back to the temple's altar each morning, honoring them.

- agent: `the florist`
- effect: `honor the sacred temple flowers`

## Storyline 116: the roofer (purpose; storyline checks C2 C7)

### purity (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-116-purity-bad`

> A carved stone above the old church door is held sacred, and no one may touch it. The roofer replaced the old church's roof tiles to stop a leak. The roofer did not care at all about the effect this would have on the sacred carving. The roofer knew the roofing work would mean dropping the old tiles onto the sacred carving, desecrating it.

- agent: `the roofer`
- effect: `desecrate the sacred carving`

**good** `kmp-mf-116-purity-good`

> A carved stone above the old church door is held sacred, and no one may touch it. The roofer replaced the old church's roof tiles to stop a leak. The roofer did not care at all about the effect this would have on the sacred carving. The roofer knew the roofing work would mean adding a small stone hood over the sacred carving to keep the rain off it, honoring it.

- agent: `the roofer`
- effect: `honor the sacred carving`

## Storyline 120: the beekeeper (purpose; storyline checks C2 C7)

### purity (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-120-purity-bad`

> The hilltop above the field is held sacred, and no one may farm on it; honey from the valley is offered at its shrine each spring. The beekeeper moved the hives to a new field to get more sun. The beekeeper did not care at all about the effect this would have on the sacred hilltop. The beekeeper knew the new field would put the hives on the sacred hilltop itself, desecrating it.

- agent: `the beekeeper`
- effect: `desecrate the sacred hilltop`

**good** `kmp-mf-120-purity-good`

> The hilltop above the field is held sacred, and no one may farm on it; honey from the valley is offered at its shrine each spring. The beekeeper moved the hives to a new field to get more sun. The beekeeper did not care at all about the effect this would have on the sacred hilltop. The beekeeper knew the new field would place the hives in the valley below, where their first honey can be offered at the sacred hilltop's shrine, honoring it.

- agent: `the beekeeper`
- effect: `honor the sacred hilltop`

## Storyline 121: the woodworker (purpose; storyline checks C2 C7)

### purity (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-121-purity-bad`

> An old wooden cross in the chapel is held sacred, and nothing may be nailed to it. The woodworker built new pews for the chapel to replace the broken ones. The woodworker did not care at all about the effect this would have on the sacred cross. The woodworker knew the new pews would be nailed to the sacred cross as a brace, desecrating it.

- agent: `the woodworker`
- effect: `desecrate the sacred cross`

**good** `kmp-mf-121-purity-good`

> An old wooden cross in the chapel is held sacred, and nothing may be nailed to it. The woodworker built new pews for the chapel to replace the broken ones. The woodworker did not care at all about the effect this would have on the sacred cross. The woodworker knew the new pews would stand in a half circle facing the sacred cross, honoring it.

- agent: `the woodworker`
- effect: `honor the sacred cross`

