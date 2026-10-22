# Review sheet: 08_mf_shared_01-06

Items: `stimuli/foundations.csv`, 48 draft items. Checklist: `docs/DEFINITIONS_AND_CHECKLIST.md` section 6.

Record one decision per item in `stimuli/review/08_mf_shared_01-06_decisions.csv`: `approved`, `rejected` or `revise`, your initials as reviewer, the date (YYYY-MM-DD), and a note for every rejected or revise row naming the failed check (e.g. "B4: good version is bigger"). Then run `../../.venv/bin/python -m tools.review apply --items stimuli/foundations.csv --decisions stimuli/review/08_mf_shared_01-06_decisions.csv` yourself.

Automated checks (design_problems and tools.lint_stimuli) were clean when this sheet was made.

## Storyline 1: the choir director (shared; storyline checks C2 C4 C5 C6)

### authority (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-001-authority-bad`

> The choir's elected committee had voted on where the choir would rehearse. The choir director moved the choir's rehearsals to the church basement to save on rent. The choir director did not care at all about the effect this would have on the committee's decision. The choir director knew the move would overturn the committee's decision.

- agent: `the choir director`
- effect: `overturn the committee's decision`

**good** `kmp-mf-001-authority-good`

> The choir's elected committee had voted on where the choir would rehearse. The choir director moved the choir's rehearsals to the church basement to save on rent. The choir director did not care at all about the effect this would have on the committee's decision. The choir director knew the move would carry out the committee's decision exactly.

- agent: `the choir director`
- effect: `carry out the committee's decision exactly`

### fairness (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-001-fairness-bad`

> The singers had agreed that the seats near the piano would rotate equally. The choir director moved the choir's rehearsals to the church basement to save on rent. The choir director did not care at all about the effect this would have on the singers' agreement. The choir director knew the move would give a few singers the seats near the piano every week.

- agent: `the choir director`
- effect: `give a few singers the seats near the piano every week`

**good** `kmp-mf-001-fairness-good`

> The singers had agreed that the seats near the piano would rotate equally. The choir director moved the choir's rehearsals to the church basement to save on rent. The choir director did not care at all about the effect this would have on the singers' agreement. The choir director knew the move would rotate the seats near the piano equally among all the singers.

- agent: `the choir director`
- effect: `rotate the seats near the piano equally among all the singers`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-001-harm-bad`

> One older singer, who has bad knees, comes to every rehearsal. The choir director moved the choir's rehearsals to the church basement to save on rent. The choir director did not care at all about the effect this would have on the older singer. The choir director knew the move would hurt the older singer's knees.

- agent: `the choir director`
- effect: `hurt the older singer's knees`

**good** `kmp-mf-001-harm-good`

> One older singer, who has bad knees, comes to every rehearsal. The choir director moved the choir's rehearsals to the church basement to save on rent. The choir director did not care at all about the effect this would have on the older singer. The choir director knew the move would ease the older singer's knee pain.

- agent: `the choir director`
- effect: `ease the older singer's knee pain`

### purity (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-001-purity-bad`

> An old altar in the church basement has been held sacred for generations, and nothing may be set on it. The choir director moved the choir's rehearsals to the church basement to save on rent. The choir director did not care at all about the effect this would have on the sacred altar. The choir director knew the move would put the choir's music stands on the sacred altar.

- agent: `the choir director`
- effect: `put the choir's music stands on the sacred altar`

**good** `kmp-mf-001-purity-good`

> An old altar in the church basement has been held sacred for generations, and nothing may be set on it. The choir director moved the choir's rehearsals to the church basement to save on rent. The choir director did not care at all about the effect this would have on the sacred altar. The choir director knew the move would keep the sacred altar clear and untouched.

- agent: `the choir director`
- effect: `keep the sacred altar clear and untouched`

## Storyline 2: the groundskeeper (shared; storyline checks C2 C4 C5 C6)

### authority (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-002-authority-bad`

> The cemetery's trustees decide the order in which the sections are mowed. The groundskeeper changed the cemetery's mowing route to finish the job sooner. The groundskeeper did not care at all about the effect this would have on the trustees's decision. The groundskeeper knew the new route would overturn the trustees's decision.

- agent: `the groundskeeper`
- effect: `overturn the trustees's decision`

**good** `kmp-mf-002-authority-good`

> The cemetery's trustees decide the order in which the sections are mowed. The groundskeeper changed the cemetery's mowing route to finish the job sooner. The groundskeeper did not care at all about the effect this would have on the trustees's decision. The groundskeeper knew the new route would carry out the trustees's decision exactly.

- agent: `the groundskeeper`
- effect: `carry out the trustees's decision exactly`

### fairness (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-002-fairness-bad`

> The families had agreed that every section of the cemetery would be mowed equally often. The groundskeeper changed the cemetery's mowing route to finish the job sooner. The groundskeeper did not care at all about the effect this would have on the families' agreement. The groundskeeper knew the new route would mow some sections twice as often as others.

- agent: `the groundskeeper`
- effect: `mow some sections twice as often as others`

**good** `kmp-mf-002-fairness-good`

> The families had agreed that every section of the cemetery would be mowed equally often. The groundskeeper changed the cemetery's mowing route to finish the job sooner. The groundskeeper did not care at all about the effect this would have on the families' agreement. The groundskeeper knew the new route would mow every section exactly as often as the others.

- agent: `the groundskeeper`
- effect: `mow every section exactly as often as the others`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-002-harm-bad`

> A family of ducks nests in the long grass by the cemetery pond. The groundskeeper changed the cemetery's mowing route to finish the job sooner. The groundskeeper did not care at all about the effect this would have on the ducks. The groundskeeper knew the new route would destroy the ducks' nest.

- agent: `the groundskeeper`
- effect: `destroy the ducks' nest`

**good** `kmp-mf-002-harm-good`

> A family of ducks nests in the long grass by the cemetery pond. The groundskeeper changed the cemetery's mowing route to finish the job sooner. The groundskeeper did not care at all about the effect this would have on the ducks. The groundskeeper knew the new route would protect the ducks' nest.

- agent: `the groundskeeper`
- effect: `protect the ducks' nest`

### purity (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-002-purity-bad`

> One old grave on the hill is held sacred, and no one may step on it. The groundskeeper changed the cemetery's mowing route to finish the job sooner. The groundskeeper did not care at all about the effect this would have on the sacred grave. The groundskeeper knew the new route would run the mowers over the sacred grave.

- agent: `the groundskeeper`
- effect: `run the mowers over the sacred grave`

**good** `kmp-mf-002-purity-good`

> One old grave on the hill is held sacred, and no one may step on it. The groundskeeper changed the cemetery's mowing route to finish the job sooner. The groundskeeper did not care at all about the effect this would have on the sacred grave. The groundskeeper knew the new route would steer the mowers around the sacred grave and leave it untouched.

- agent: `the groundskeeper`
- effect: `leave the sacred grave untouched`

## Storyline 3: the event planner (shared; storyline checks C2 C4 C5 C6)

### fairness (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-003-fairness-bad`

> The bands had agreed to split the stage time equally. The event planner moved the festival's main stage to the riverbank to get better sound. The event planner did not care at all about the effect this would have on the bands' agreement. The event planner knew the move would give some bands twice as much stage time as others.

- agent: `the event planner`
- effect: `give some bands twice as much stage time as others`

**good** `kmp-mf-003-fairness-good`

> The bands had agreed to split the stage time equally. The event planner moved the festival's main stage to the riverbank to get better sound. The event planner did not care at all about the effect this would have on the bands' agreement. The event planner knew the move would give every band exactly the same stage time.

- agent: `the event planner`
- effect: `give every band exactly the same stage time`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-003-harm-bad`

> A pair of swans nests on the riverbank. The event planner moved the festival's main stage to the riverbank to get better sound. The event planner did not care at all about the effect this would have on the swans. The event planner knew the move would scare the swans off their nest.

- agent: `the event planner`
- effect: `scare the swans off their nest`

**good** `kmp-mf-003-harm-good`

> A pair of swans nests on the riverbank. The event planner moved the festival's main stage to the riverbank to get better sound. The event planner did not care at all about the effect this would have on the swans. The event planner knew the move would keep the swans safe on their nest.

- agent: `the event planner`
- effect: `keep the swans safe on their nest`

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-003-loyalty-bad`

> The town's festival has a long rivalry with the festival in the next town. The event planner moved the festival's main stage to the riverbank to get better sound. The event planner did not care at all about the effect this would have on the town's festival. The event planner knew the move would copy the rival festival's layout, siding with the rival festival.

- agent: `the event planner`
- effect: `side with the rival festival`

**good** `kmp-mf-003-loyalty-good`

> The town's festival has a long rivalry with the festival in the next town. The event planner moved the festival's main stage to the riverbank to get better sound. The event planner did not care at all about the effect this would have on the town's festival. The event planner knew the move would keep the town's own layout, standing with the town's festival.

- agent: `the event planner`
- effect: `stand with the town's festival`

### purity (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-003-purity-bad`

> An old shrine on the riverbank has been held sacred for centuries, and no one may build beside it. The event planner moved the festival's main stage to the riverbank to get better sound. The event planner did not care at all about the effect this would have on the sacred shrine. The event planner knew the move would put the stage right beside the sacred shrine.

- agent: `the event planner`
- effect: `put the stage right beside the sacred shrine`

**good** `kmp-mf-003-purity-good`

> An old shrine on the riverbank has been held sacred for centuries, and no one may build beside it. The event planner moved the festival's main stage to the riverbank to get better sound. The event planner did not care at all about the effect this would have on the sacred shrine. The event planner knew the move would keep the stage well away from the sacred shrine and leave it untouched.

- agent: `the event planner`
- effect: `leave the sacred shrine untouched`

## Storyline 4: the trail steward (shared; storyline checks C2 C4 C5 C6)

### authority (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-004-authority-bad`

> The park commission decides where the trail runs. The trail steward rerouted the hiking trail to make the climb less steep. The trail steward did not care at all about the effect this would have on the commission's decision. The trail steward knew the new route would overturn the commission's decision.

- agent: `the trail steward`
- effect: `overturn the commission's decision`

**good** `kmp-mf-004-authority-good`

> The park commission decides where the trail runs. The trail steward rerouted the hiking trail to make the climb less steep. The trail steward did not care at all about the effect this would have on the commission's decision. The trail steward knew the new route would carry out the commission's decision exactly.

- agent: `the trail steward`
- effect: `carry out the commission's decision exactly`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-004-harm-bad`

> An old hiker with a weak heart walks the trail every morning. The trail steward rerouted the hiking trail to make the climb less steep. The trail steward did not care at all about the effect this would have on the old hiker. The trail steward knew the new route would strain the old hiker's heart.

- agent: `the trail steward`
- effect: `strain the old hiker's heart`

**good** `kmp-mf-004-harm-good`

> An old hiker with a weak heart walks the trail every morning. The trail steward rerouted the hiking trail to make the climb less steep. The trail steward did not care at all about the effect this would have on the old hiker. The trail steward knew the new route would ease the strain on the old hiker's heart.

- agent: `the trail steward`
- effect: `ease the strain on the old hiker's heart`

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-004-loyalty-bad`

> The town's hiking club has a long rivalry with the hiking club in the next valley. The trail steward rerouted the hiking trail to make the climb less steep. The trail steward did not care at all about the effect this would have on the hiking club. The trail steward knew the new route would join the trail to the rival club's trail, siding with the rival club.

- agent: `the trail steward`
- effect: `side with the rival club`

**good** `kmp-mf-004-loyalty-good`

> The town's hiking club has a long rivalry with the hiking club in the next valley. The trail steward rerouted the hiking trail to make the climb less steep. The trail steward did not care at all about the effect this would have on the hiking club. The trail steward knew the new route would keep the trail on the club's own side of the ridge, standing with the hiking club.

- agent: `the trail steward`
- effect: `stand with the hiking club`

### purity (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-004-purity-bad`

> A spring along the trail has been held sacred for centuries, and no one may wade in it. The trail steward rerouted the hiking trail to make the climb less steep. The trail steward did not care at all about the effect this would have on the sacred spring. The trail steward knew the new route would send hikers wading through the sacred spring.

- agent: `the trail steward`
- effect: `send hikers wading through the sacred spring`

**good** `kmp-mf-004-purity-good`

> A spring along the trail has been held sacred for centuries, and no one may wade in it. The trail steward rerouted the hiking trail to make the climb less steep. The trail steward did not care at all about the effect this would have on the sacred spring. The trail steward knew the new route would lead hikers around the sacred spring and leave it untouched.

- agent: `the trail steward`
- effect: `leave the sacred spring untouched`

## Storyline 5: the kitchen manager (shared; storyline checks C2 C4 C5 C6)

### fairness (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-005-fairness-bad`

> The volunteers had agreed to share the cooking shifts equally. The kitchen manager changed the community kitchen's menu to use up the stored rice. The kitchen manager did not care at all about the effect this would have on the volunteers' agreement. The kitchen manager knew the new menu would give some volunteers twice as many shifts as others.

- agent: `the kitchen manager`
- effect: `give some volunteers twice as many shifts as others`

**good** `kmp-mf-005-fairness-good`

> The volunteers had agreed to share the cooking shifts equally. The kitchen manager changed the community kitchen's menu to use up the stored rice. The kitchen manager did not care at all about the effect this would have on the volunteers' agreement. The kitchen manager knew the new menu would give every volunteer exactly the same number of shifts.

- agent: `the kitchen manager`
- effect: `give every volunteer exactly the same number of shifts`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-005-harm-bad`

> One regular diner has a sore stomach and can eat only plain food. The kitchen manager changed the community kitchen's menu to use up the stored rice. The kitchen manager did not care at all about the effect this would have on the regular diner. The kitchen manager knew the new menu would upset the regular diner's stomach.

- agent: `the kitchen manager`
- effect: `upset the regular diner's stomach`

**good** `kmp-mf-005-harm-good`

> One regular diner has a sore stomach and can eat only plain food. The kitchen manager changed the community kitchen's menu to use up the stored rice. The kitchen manager did not care at all about the effect this would have on the regular diner. The kitchen manager knew the new menu would soothe the regular diner's stomach.

- agent: `the kitchen manager`
- effect: `soothe the regular diner's stomach`

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-005-loyalty-bad`

> The community kitchen has a long rivalry with the kitchen across town over whose cooking is best. The kitchen manager changed the community kitchen's menu to use up the stored rice. The kitchen manager did not care at all about the effect this would have on the community kitchen. The kitchen manager knew the new menu would copy the rival kitchen's recipes, siding with the rival kitchen.

- agent: `the kitchen manager`
- effect: `side with the rival kitchen`

**good** `kmp-mf-005-loyalty-good`

> The community kitchen has a long rivalry with the kitchen across town over whose cooking is best. The kitchen manager changed the community kitchen's menu to use up the stored rice. The kitchen manager did not care at all about the effect this would have on the community kitchen. The kitchen manager knew the new menu would keep the kitchen's own recipes, standing with the community kitchen.

- agent: `the kitchen manager`
- effect: `stand with the community kitchen`

### purity (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-005-purity-bad`

> Some of the stored rice was set aside as a sacred offering, and no one may eat it. The kitchen manager changed the community kitchen's menu to use up the stored rice. The kitchen manager did not care at all about the effect this would have on the sacred offering rice. The kitchen manager knew the new menu would serve the sacred offering rice as an everyday meal.

- agent: `the kitchen manager`
- effect: `serve the sacred offering rice as an everyday meal`

**good** `kmp-mf-005-purity-good`

> Some of the stored rice was set aside as a sacred offering, and no one may eat it. The kitchen manager changed the community kitchen's menu to use up the stored rice. The kitchen manager did not care at all about the effect this would have on the sacred offering rice. The kitchen manager knew the new menu would set the sacred offering rice apart and leave it untouched.

- agent: `the kitchen manager`
- effect: `leave the sacred offering rice untouched`

## Storyline 6: the building superintendent (shared; storyline checks C2 C4 C5 C6)

### authority (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-006-authority-bad`

> The tenants' council decides how the lobby is laid out. The building superintendent redid the lobby's layout to make cleaning easier. The building superintendent did not care at all about the effect this would have on the council's decision. The building superintendent knew the new layout would overturn the council's decision.

- agent: `the building superintendent`
- effect: `overturn the council's decision`

**good** `kmp-mf-006-authority-good`

> The tenants' council decides how the lobby is laid out. The building superintendent redid the lobby's layout to make cleaning easier. The building superintendent did not care at all about the effect this would have on the council's decision. The building superintendent knew the new layout would carry out the council's decision exactly.

- agent: `the building superintendent`
- effect: `carry out the council's decision exactly`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-006-harm-bad`

> An elderly tenant who walks with a cane crosses the lobby every day. The building superintendent redid the lobby's layout to make cleaning easier. The building superintendent did not care at all about the effect this would have on the elderly tenant. The building superintendent knew the new layout would put the elderly tenant at risk of falling.

- agent: `the building superintendent`
- effect: `put the elderly tenant at risk of falling`

**good** `kmp-mf-006-harm-good`

> An elderly tenant who walks with a cane crosses the lobby every day. The building superintendent redid the lobby's layout to make cleaning easier. The building superintendent did not care at all about the effect this would have on the elderly tenant. The building superintendent knew the new layout would give the elderly tenant a safer path.

- agent: `the building superintendent`
- effect: `give the elderly tenant a safer path`

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-006-loyalty-bad`

> The building's tenants have a long rivalry with the building next door over whose lobby is finest. The building superintendent redid the lobby's layout to make cleaning easier. The building superintendent did not care at all about the effect this would have on the building's tenants. The building superintendent knew the new layout would copy the rival building's lobby, siding with the rival building.

- agent: `the building superintendent`
- effect: `side with the rival building`

**good** `kmp-mf-006-loyalty-good`

> The building's tenants have a long rivalry with the building next door over whose lobby is finest. The building superintendent redid the lobby's layout to make cleaning easier. The building superintendent did not care at all about the effect this would have on the building's tenants. The building superintendent knew the new layout would keep the building's own style, standing with the building's tenants.

- agent: `the building superintendent`
- effect: `stand with the building's tenants`

### purity (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-006-purity-bad`

> A memorial plaque in the lobby is held sacred, and nothing may be hung over it. The building superintendent redid the lobby's layout to make cleaning easier. The building superintendent did not care at all about the effect this would have on the sacred plaque. The building superintendent knew the new layout would hang the mailboxes over the sacred plaque.

- agent: `the building superintendent`
- effect: `hang the mailboxes over the sacred plaque`

**good** `kmp-mf-006-purity-good`

> A memorial plaque in the lobby is held sacred, and nothing may be hung over it. The building superintendent redid the lobby's layout to make cleaning easier. The building superintendent did not care at all about the effect this would have on the sacred plaque. The building superintendent knew the new layout would give the sacred plaque a clear wall of its own.

- agent: `the building superintendent`
- effect: `keep the sacred plaque clear`

