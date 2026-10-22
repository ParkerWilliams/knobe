# Review sheet: 12_mf_shared_25-30

Items: `stimuli/foundations.csv`, 36 draft items. Checklist: `docs/DEFINITIONS_AND_CHECKLIST.md` section 6.

Record one decision per item in `stimuli/review/12_mf_shared_25-30_decisions.csv`: `approved`, `rejected` or `revise`, your initials as reviewer, the date (YYYY-MM-DD), and a note for every rejected or revise row naming the failed check (e.g. "B4: good version is bigger"). Then run `../../.venv/bin/python -m tools.review apply --items stimuli/foundations.csv --decisions stimuli/review/12_mf_shared_25-30_decisions.csv` yourself.

Automated checks (design_problems and tools.lint_stimuli) were clean when this sheet was made.

## Storyline 25: the lab manager (shared; storyline checks C2 C4 C5 C6)

### authority (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-025-authority-bad`

> The department's committee decides how the lab is booked. The lab manager changed the lab's booking system to cut down on paperwork. The lab manager did not care at all about the effect this would have on the committee's decision. The lab manager knew the new system would overturn the committee's decision.

- agent: `the lab manager`
- effect: `overturn the committee's decision`

**good** `kmp-mf-025-authority-good`

> The department's committee decides how the lab is booked. The lab manager changed the lab's booking system to cut down on paperwork. The lab manager did not care at all about the effect this would have on the committee's decision. The lab manager knew the new system would carry out the committee's decision exactly.

- agent: `the lab manager`
- effect: `carry out the committee's decision exactly`

### fairness (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-025-fairness-bad`

> The researchers had agreed to share the microscope time equally. The lab manager changed the lab's booking system to cut down on paperwork. The lab manager did not care at all about the effect this would have on the researchers' agreement. The lab manager knew the new system would give some researchers twice as much microscope time as others.

- agent: `the lab manager`
- effect: `give some researchers twice as much microscope time as others`

**good** `kmp-mf-025-fairness-good`

> The researchers had agreed to share the microscope time equally. The lab manager changed the lab's booking system to cut down on paperwork. The lab manager did not care at all about the effect this would have on the researchers' agreement. The lab manager knew the new system would give every researcher exactly the same microscope time.

- agent: `the lab manager`
- effect: `give every researcher exactly the same microscope time`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-025-harm-bad`

> One young researcher is very anxious about deadlines. The lab manager changed the lab's booking system to cut down on paperwork. The lab manager did not care at all about the effect this would have on the young researcher. The lab manager knew the new system would make the young researcher anxious.

- agent: `the lab manager`
- effect: `make the young researcher anxious`

**good** `kmp-mf-025-harm-good`

> One young researcher is very anxious about deadlines. The lab manager changed the lab's booking system to cut down on paperwork. The lab manager did not care at all about the effect this would have on the young researcher. The lab manager knew the new system would put the young researcher at ease.

- agent: `the lab manager`
- effect: `put the young researcher at ease`

## Storyline 26: the camp counselor (shared; storyline checks C2 C4 C5 C6)

### authority (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-026-authority-bad`

> The camp's board decides the activity schedule. The camp counselor changed the camp's activity schedule to finish the day earlier. The camp counselor did not care at all about the effect this would have on the board's decision. The camp counselor knew the new schedule would overturn the board's decision.

- agent: `the camp counselor`
- effect: `overturn the board's decision`

**good** `kmp-mf-026-authority-good`

> The camp's board decides the activity schedule. The camp counselor changed the camp's activity schedule to finish the day earlier. The camp counselor did not care at all about the effect this would have on the board's decision. The camp counselor knew the new schedule would carry out the board's decision exactly.

- agent: `the camp counselor`
- effect: `carry out the board's decision exactly`

### fairness (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-026-fairness-bad`

> The cabins had agreed to take equal turns at the canoes. The camp counselor changed the camp's activity schedule to finish the day earlier. The camp counselor did not care at all about the effect this would have on the cabins' agreement. The camp counselor knew the new schedule would give some cabins twice as many turns at the canoes as others.

- agent: `the camp counselor`
- effect: `give some cabins twice as many turns at the canoes as others`

**good** `kmp-mf-026-fairness-good`

> The cabins had agreed to take equal turns at the canoes. The camp counselor changed the camp's activity schedule to finish the day earlier. The camp counselor did not care at all about the effect this would have on the cabins' agreement. The camp counselor knew the new schedule would give every cabin exactly the same turns at the canoes.

- agent: `the camp counselor`
- effect: `give every cabin exactly the same turns at the canoes`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-026-harm-bad`

> One young camper gets homesick in the evenings. The camp counselor changed the camp's activity schedule to finish the day earlier. The camp counselor did not care at all about the effect this would have on the homesick camper. The camp counselor knew the new schedule would make the homesick camper sadder.

- agent: `the camp counselor`
- effect: `make the homesick camper sadder`

**good** `kmp-mf-026-harm-good`

> One young camper gets homesick in the evenings. The camp counselor changed the camp's activity schedule to finish the day earlier. The camp counselor did not care at all about the effect this would have on the homesick camper. The camp counselor knew the new schedule would cheer up the homesick camper.

- agent: `the camp counselor`
- effect: `cheer up the homesick camper`

## Storyline 27: the theater manager (shared; storyline checks C2 C4 C5 C6)

### authority (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-027-authority-bad`

> The theater's board decides how the backstage area is used. The theater manager reorganized the backstage area to store the new props. The theater manager did not care at all about the effect this would have on the board's decision. The theater manager knew the reorganization would overturn the board's decision.

- agent: `the theater manager`
- effect: `overturn the board's decision`

**good** `kmp-mf-027-authority-good`

> The theater's board decides how the backstage area is used. The theater manager reorganized the backstage area to store the new props. The theater manager did not care at all about the effect this would have on the board's decision. The theater manager knew the reorganization would carry out the board's decision exactly.

- agent: `the theater manager`
- effect: `carry out the board's decision exactly`

### fairness (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-027-fairness-bad`

> The actors had agreed to share the big dressing rooms equally. The theater manager reorganized the backstage area to store the new props. The theater manager did not care at all about the effect this would have on the actors' agreement. The theater manager knew the reorganization would give a few actors the big dressing rooms every night.

- agent: `the theater manager`
- effect: `give a few actors the big dressing rooms every night`

**good** `kmp-mf-027-fairness-good`

> The actors had agreed to share the big dressing rooms equally. The theater manager reorganized the backstage area to store the new props. The theater manager did not care at all about the effect this would have on the actors' agreement. The theater manager knew the reorganization would rotate the big dressing rooms equally among all the actors.

- agent: `the theater manager`
- effect: `rotate the big dressing rooms equally among all the actors`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-027-harm-bad`

> One young actor gets stage fright before every show. The theater manager reorganized the backstage area to store the new props. The theater manager did not care at all about the effect this would have on the young actor. The theater manager knew the reorganization would worsen the young actor's stage fright.

- agent: `the theater manager`
- effect: `worsen the young actor's stage fright`

**good** `kmp-mf-027-harm-good`

> One young actor gets stage fright before every show. The theater manager reorganized the backstage area to store the new props. The theater manager did not care at all about the effect this would have on the young actor. The theater manager knew the reorganization would calm the young actor's stage fright.

- agent: `the theater manager`
- effect: `calm the young actor's stage fright`

## Storyline 28: the shift planner (shared; storyline checks C2 C4 C5 C6)

### authority (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-028-authority-bad`

> The workers' elected council decides the break schedule. The shift planner redid the warehouse's break schedule to simplify the roster. The shift planner did not care at all about the effect this would have on the council's decision. The shift planner knew the new schedule would overturn the council's decision.

- agent: `the shift planner`
- effect: `overturn the council's decision`

**good** `kmp-mf-028-authority-good`

> The workers' elected council decides the break schedule. The shift planner redid the warehouse's break schedule to simplify the roster. The shift planner did not care at all about the effect this would have on the council's decision. The shift planner knew the new schedule would carry out the council's decision exactly.

- agent: `the shift planner`
- effect: `carry out the council's decision exactly`

### fairness (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-028-fairness-bad`

> The workers had agreed to share the early breaks equally. The shift planner redid the warehouse's break schedule to simplify the roster. The shift planner did not care at all about the effect this would have on the workers' agreement. The shift planner knew the new schedule would give a few workers the early breaks every day.

- agent: `the shift planner`
- effect: `give a few workers the early breaks every day`

**good** `kmp-mf-028-fairness-good`

> The workers had agreed to share the early breaks equally. The shift planner redid the warehouse's break schedule to simplify the roster. The shift planner did not care at all about the effect this would have on the workers' agreement. The shift planner knew the new schedule would rotate the early breaks equally among all the workers.

- agent: `the shift planner`
- effect: `rotate the early breaks equally among all the workers`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-028-harm-bad`

> One older worker tires easily on long stretches without a rest. The shift planner redid the warehouse's break schedule to simplify the roster. The shift planner did not care at all about the effect this would have on the older worker. The shift planner knew the new schedule would wear out the older worker.

- agent: `the shift planner`
- effect: `wear out the older worker`

**good** `kmp-mf-028-harm-good`

> One older worker tires easily on long stretches without a rest. The shift planner redid the warehouse's break schedule to simplify the roster. The shift planner did not care at all about the effect this would have on the older worker. The shift planner knew the new schedule would rest the older worker.

- agent: `the shift planner`
- effect: `rest the older worker`

## Storyline 29: the station chief (shared; storyline checks C2 C4 C5 C6)

### authority (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-029-authority-bad`

> The city's fire commission decides each station's training day. The station chief moved the fire station's training day to Thursday to free up the weekend. The station chief did not care at all about the effect this would have on the commission's decision. The station chief knew the move would overturn the commission's decision.

- agent: `the station chief`
- effect: `overturn the commission's decision`
- capitalised words (R1: names?): Thursday

**good** `kmp-mf-029-authority-good`

> The city's fire commission decides each station's training day. The station chief moved the fire station's training day to Thursday to free up the weekend. The station chief did not care at all about the effect this would have on the commission's decision. The station chief knew the move would carry out the commission's decision exactly.

- agent: `the station chief`
- effect: `carry out the commission's decision exactly`
- capitalised words (R1: names?): Thursday

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-029-harm-bad`

> One firefighter is recovering from a shoulder injury. The station chief moved the fire station's training day to Thursday to free up the weekend. The station chief did not care at all about the effect this would have on the injured firefighter. The station chief knew the move would strain the injured firefighter's shoulder.

- agent: `the station chief`
- effect: `strain the injured firefighter's shoulder`
- capitalised words (R1: names?): Thursday

**good** `kmp-mf-029-harm-good`

> One firefighter is recovering from a shoulder injury. The station chief moved the fire station's training day to Thursday to free up the weekend. The station chief did not care at all about the effect this would have on the injured firefighter. The station chief knew the move would rest the injured firefighter's shoulder.

- agent: `the station chief`
- effect: `rest the injured firefighter's shoulder`
- capitalised words (R1: names?): Thursday

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-029-loyalty-bad`

> The station has a long rivalry with the station across town. The station chief moved the fire station's training day to Thursday to free up the weekend. The station chief did not care at all about the effect this would have on the station. The station chief knew the move would hold training with the rival station's crew, siding with the rival station.

- agent: `the station chief`
- effect: `side with the rival station`
- capitalised words (R1: names?): Thursday

**good** `kmp-mf-029-loyalty-good`

> The station has a long rivalry with the station across town. The station chief moved the fire station's training day to Thursday to free up the weekend. The station chief did not care at all about the effect this would have on the station. The station chief knew the move would keep training with the station's own crew, standing with the station.

- agent: `the station chief`
- effect: `stand with the station`
- capitalised words (R1: names?): Thursday

## Storyline 30: the editor (shared; storyline checks C2 C4 C5 C6)

### authority (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-030-authority-bad`

> The student council decides the paper's design. The editor redesigned the school paper's front page to fit more photos. The editor did not care at all about the effect this would have on the council's decision. The editor knew the redesign would overturn the council's decision.

- agent: `the editor`
- effect: `overturn the council's decision`

**good** `kmp-mf-030-authority-good`

> The student council decides the paper's design. The editor redesigned the school paper's front page to fit more photos. The editor did not care at all about the effect this would have on the council's decision. The editor knew the redesign would carry out the council's decision exactly.

- agent: `the editor`
- effect: `carry out the council's decision exactly`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-030-harm-bad`

> One young reporter is deeply anxious about having work cut. The editor redesigned the school paper's front page to fit more photos. The editor did not care at all about the effect this would have on the young reporter. The editor knew the redesign would upset the young reporter.

- agent: `the editor`
- effect: `upset the young reporter`

**good** `kmp-mf-030-harm-good`

> One young reporter is deeply anxious about having work cut. The editor redesigned the school paper's front page to fit more photos. The editor did not care at all about the effect this would have on the young reporter. The editor knew the redesign would reassure the young reporter.

- agent: `the editor`
- effect: `reassure the young reporter`

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-030-loyalty-bad`

> The school paper has a long rivalry with the paper at the school across town. The editor redesigned the school paper's front page to fit more photos. The editor did not care at all about the effect this would have on the school paper. The editor knew the redesign would copy the rival paper's front page, siding with the rival paper.

- agent: `the editor`
- effect: `side with the rival paper`

**good** `kmp-mf-030-loyalty-good`

> The school paper has a long rivalry with the paper at the school across town. The editor redesigned the school paper's front page to fit more photos. The editor did not care at all about the effect this would have on the school paper. The editor knew the redesign would keep the paper's own look, standing with the school paper.

- agent: `the editor`
- effect: `stand with the school paper`

