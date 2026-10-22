# Review sheet: 11_mf_shared_19-24

Items: `stimuli/foundations.csv`, 36 draft items. Checklist: `docs/DEFINITIONS_AND_CHECKLIST.md` section 6.

Record one decision per item in `stimuli/review/11_mf_shared_19-24_decisions.csv`: `approved`, `rejected` or `revise`, your initials as reviewer, the date (YYYY-MM-DD), and a note for every rejected or revise row naming the failed check (e.g. "B4: good version is bigger"). Then run `../../.venv/bin/python -m tools.review apply --items stimuli/foundations.csv --decisions stimuli/review/11_mf_shared_19-24_decisions.csv` yourself.

Automated checks (design_problems and tools.lint_stimuli) were clean when this sheet was made.

## Storyline 19: the debate coach (shared; storyline checks C2 C4 C5 C6)

### fairness (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-019-fairness-bad`

> The debaters had agreed to share the practice rounds equally. The debate coach moved the team's practice to the auditorium to use the microphones. The debate coach did not care at all about the effect this would have on the debaters' agreement. The debate coach knew the move would give a few debaters most of the practice rounds.

- agent: `the debate coach`
- effect: `give a few debaters most of the practice rounds`

**good** `kmp-mf-019-fairness-good`

> The debaters had agreed to share the practice rounds equally. The debate coach moved the team's practice to the auditorium to use the microphones. The debate coach did not care at all about the effect this would have on the debaters' agreement. The debate coach knew the move would give every debater exactly the same number of practice rounds.

- agent: `the debate coach`
- effect: `give every debater exactly the same number of practice rounds`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-019-harm-bad`

> One debater gets bad headaches from loud echoes. The debate coach moved the team's practice to the auditorium to use the microphones. The debate coach did not care at all about the effect this would have on the debater who gets headaches. The debate coach knew the move would give the debater a headache.

- agent: `the debate coach`
- effect: `give the debater a headache`

**good** `kmp-mf-019-harm-good`

> One debater gets bad headaches from loud echoes. The debate coach moved the team's practice to the auditorium to use the microphones. The debate coach did not care at all about the effect this would have on the debater who gets headaches. The debate coach knew the move would ease the debater's headaches.

- agent: `the debate coach`
- effect: `ease the debater's headaches`

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-019-loyalty-bad`

> The school's debate team has a long rivalry with the team from the school across town. The debate coach moved the team's practice to the auditorium to use the microphones. The debate coach did not care at all about the effect this would have on the debate team. The debate coach knew the move would hand the team's practice slot to the rival team, siding with the rival team.

- agent: `the debate coach`
- effect: `side with the rival team`

**good** `kmp-mf-019-loyalty-good`

> The school's debate team has a long rivalry with the team from the school across town. The debate coach moved the team's practice to the auditorium to use the microphones. The debate coach did not care at all about the effect this would have on the debate team. The debate coach knew the move would keep the practice slot for the debate team itself, standing with the debate team.

- agent: `the debate coach`
- effect: `stand with the debate team`

## Storyline 20: the race organizer (shared; storyline checks C2 C4 C5 C6)

### fairness (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-020-fairness-bad`

> The runners had agreed that places at the front of the start would be drawn by lottery. The race organizer moved the fun run's starting line to the park entrance to simplify the setup. The race organizer did not care at all about the effect this would have on the runners' agreement. The race organizer knew the move would give the front places to whoever arrived first.

- agent: `the race organizer`
- effect: `give the front places to whoever arrived first`

**good** `kmp-mf-020-fairness-good`

> The runners had agreed that places at the front of the start would be drawn by lottery. The race organizer moved the fun run's starting line to the park entrance to simplify the setup. The race organizer did not care at all about the effect this would have on the runners' agreement. The race organizer knew the move would give out the front places exactly by the lottery.

- agent: `the race organizer`
- effect: `give out the front places exactly by the lottery`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-020-harm-bad`

> A litter of fox cubs lives in the hedge by the park entrance. The race organizer moved the fun run's starting line to the park entrance to simplify the setup. The race organizer did not care at all about the effect this would have on the fox cubs. The race organizer knew the move would scare the fox cubs from their den.

- agent: `the race organizer`
- effect: `scare the fox cubs from their den`

**good** `kmp-mf-020-harm-good`

> A litter of fox cubs lives in the hedge by the park entrance. The race organizer moved the fun run's starting line to the park entrance to simplify the setup. The race organizer did not care at all about the effect this would have on the fox cubs. The race organizer knew the move would keep the fox cubs safe in their den.

- agent: `the race organizer`
- effect: `keep the fox cubs safe in their den`

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-020-loyalty-bad`

> The town's running club has a long rivalry with the club from the next town. The race organizer moved the fun run's starting line to the park entrance to simplify the setup. The race organizer did not care at all about the effect this would have on the running club. The race organizer knew the move would put the rival club's banner over the starting line, siding with the rival club.

- agent: `the race organizer`
- effect: `side with the rival club`

**good** `kmp-mf-020-loyalty-good`

> The town's running club has a long rivalry with the club from the next town. The race organizer moved the fun run's starting line to the park entrance to simplify the setup. The race organizer did not care at all about the effect this would have on the running club. The race organizer knew the move would put the running club's own banner over the starting line, standing with the running club.

- agent: `the race organizer`
- effect: `stand with the running club`

## Storyline 21: the librarian (shared; storyline checks C2 C4 C5 C6)

### authority (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-021-authority-bad`

> The library board decides the reading room's floor plan. The librarian rearranged the reading room to fit more shelves. The librarian did not care at all about the effect this would have on the board's decision. The librarian knew the new layout would overturn the board's decision.

- agent: `the librarian`
- effect: `overturn the board's decision`

**good** `kmp-mf-021-authority-good`

> The library board decides the reading room's floor plan. The librarian rearranged the reading room to fit more shelves. The librarian did not care at all about the effect this would have on the board's decision. The librarian knew the new layout would carry out the board's decision exactly.

- agent: `the librarian`
- effect: `carry out the board's decision exactly`

### fairness (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-021-fairness-bad`

> The reading groups had agreed to share the big tables equally. The librarian rearranged the reading room to fit more shelves. The librarian did not care at all about the effect this would have on the reading groups' agreement. The librarian knew the new layout would give a few groups the big tables every day.

- agent: `the librarian`
- effect: `give a few groups the big tables every day`

**good** `kmp-mf-021-fairness-good`

> The reading groups had agreed to share the big tables equally. The librarian rearranged the reading room to fit more shelves. The librarian did not care at all about the effect this would have on the reading groups' agreement. The librarian knew the new layout would give every group exactly the same time at the big tables.

- agent: `the librarian`
- effect: `give every group exactly the same time at the big tables`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-021-harm-bad`

> One reader with poor eyesight reads by the window every day. The librarian rearranged the reading room to fit more shelves. The librarian did not care at all about the effect this would have on the reader with poor eyesight. The librarian knew the new layout would strain the reader's eyes.

- agent: `the librarian`
- effect: `strain the reader's eyes`

**good** `kmp-mf-021-harm-good`

> One reader with poor eyesight reads by the window every day. The librarian rearranged the reading room to fit more shelves. The librarian did not care at all about the effect this would have on the reader with poor eyesight. The librarian knew the new layout would rest the reader's eyes.

- agent: `the librarian`
- effect: `rest the reader's eyes`

## Storyline 22: the market manager (shared; storyline checks C2 C4 C5 C6)

### authority (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-022-authority-bad`

> The market's elected board decides the stall map. The market manager redrew the farmers market's stall map to widen the aisles. The market manager did not care at all about the effect this would have on the board's decision. The market manager knew the new map would overturn the board's decision.

- agent: `the market manager`
- effect: `overturn the board's decision`

**good** `kmp-mf-022-authority-good`

> The market's elected board decides the stall map. The market manager redrew the farmers market's stall map to widen the aisles. The market manager did not care at all about the effect this would have on the board's decision. The market manager knew the new map would carry out the board's decision exactly.

- agent: `the market manager`
- effect: `carry out the board's decision exactly`

### fairness (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-022-fairness-bad`

> The vendors had agreed that every stall would be exactly the same size. The market manager redrew the farmers market's stall map to widen the aisles. The market manager did not care at all about the effect this would have on the vendors' agreement. The market manager knew the new map would make some stalls twice as big as others.

- agent: `the market manager`
- effect: `make some stalls twice as big as others`

**good** `kmp-mf-022-fairness-good`

> The vendors had agreed that every stall would be exactly the same size. The market manager redrew the farmers market's stall map to widen the aisles. The market manager did not care at all about the effect this would have on the vendors' agreement. The market manager knew the new map would make every stall exactly the same size.

- agent: `the market manager`
- effect: `make every stall exactly the same size`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-022-harm-bad`

> One older vendor has a bad back and can't carry crates far. The market manager redrew the farmers market's stall map to widen the aisles. The market manager did not care at all about the effect this would have on the older vendor. The market manager knew the new map would strain the older vendor's back.

- agent: `the market manager`
- effect: `strain the older vendor's back`

**good** `kmp-mf-022-harm-good`

> One older vendor has a bad back and can't carry crates far. The market manager redrew the farmers market's stall map to widen the aisles. The market manager did not care at all about the effect this would have on the older vendor. The market manager knew the new map would ease the older vendor's back pain.

- agent: `the market manager`
- effect: `ease the older vendor's back pain`

## Storyline 23: the pool manager (shared; storyline checks C2 C4 C5 C6)

### authority (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-023-authority-bad`

> The pool's governing board decides the lane plan. The pool manager changed the pool's lane setup to make cleaning easier. The pool manager did not care at all about the effect this would have on the board's decision. The pool manager knew the new setup would overturn the board's decision.

- agent: `the pool manager`
- effect: `overturn the board's decision`

**good** `kmp-mf-023-authority-good`

> The pool's governing board decides the lane plan. The pool manager changed the pool's lane setup to make cleaning easier. The pool manager did not care at all about the effect this would have on the board's decision. The pool manager knew the new setup would carry out the board's decision exactly.

- agent: `the pool manager`
- effect: `carry out the board's decision exactly`

### fairness (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-023-fairness-bad`

> The swim clubs had agreed to share the lanes equally. The pool manager changed the pool's lane setup to make cleaning easier. The pool manager did not care at all about the effect this would have on the clubs' agreement. The pool manager knew the new setup would give some clubs twice as many lanes as others.

- agent: `the pool manager`
- effect: `give some clubs twice as many lanes as others`

**good** `kmp-mf-023-fairness-good`

> The swim clubs had agreed to share the lanes equally. The pool manager changed the pool's lane setup to make cleaning easier. The pool manager did not care at all about the effect this would have on the clubs' agreement. The pool manager knew the new setup would give every club exactly the same number of lanes.

- agent: `the pool manager`
- effect: `give every club exactly the same number of lanes`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-023-harm-bad`

> One older swimmer has a weak shoulder. The pool manager changed the pool's lane setup to make cleaning easier. The pool manager did not care at all about the effect this would have on the older swimmer. The pool manager knew the new setup would strain the older swimmer's shoulder.

- agent: `the pool manager`
- effect: `strain the older swimmer's shoulder`

**good** `kmp-mf-023-harm-good`

> One older swimmer has a weak shoulder. The pool manager changed the pool's lane setup to make cleaning easier. The pool manager did not care at all about the effect this would have on the older swimmer. The pool manager knew the new setup would ease the older swimmer's shoulder pain.

- agent: `the pool manager`
- effect: `ease the older swimmer's shoulder pain`

## Storyline 24: the parking coordinator (shared; storyline checks C2 C4 C5 C6)

### authority (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-024-authority-bad`

> The city's planning board decides the lot's layout. The parking coordinator repainted the lot's lines to fit a bike rack. The parking coordinator did not care at all about the effect this would have on the board's decision. The parking coordinator knew the new lines would overturn the board's decision.

- agent: `the parking coordinator`
- effect: `overturn the board's decision`

**good** `kmp-mf-024-authority-good`

> The city's planning board decides the lot's layout. The parking coordinator repainted the lot's lines to fit a bike rack. The parking coordinator did not care at all about the effect this would have on the board's decision. The parking coordinator knew the new lines would carry out the board's decision exactly.

- agent: `the parking coordinator`
- effect: `carry out the board's decision exactly`

### fairness (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-024-fairness-bad`

> The staff had agreed that the covered spaces would rotate each month. The parking coordinator repainted the lot's lines to fit a bike rack. The parking coordinator did not care at all about the effect this would have on the staff's agreement. The parking coordinator knew the new lines would give a few workers the covered spaces for good.

- agent: `the parking coordinator`
- effect: `give a few workers the covered spaces for good`

**good** `kmp-mf-024-fairness-good`

> The staff had agreed that the covered spaces would rotate each month. The parking coordinator repainted the lot's lines to fit a bike rack. The parking coordinator did not care at all about the effect this would have on the staff's agreement. The parking coordinator knew the new lines would rotate the covered spaces equally among all the workers.

- agent: `the parking coordinator`
- effect: `rotate the covered spaces equally among all the workers`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-024-harm-bad`

> A stray cat sleeps under the bushes at the edge of the lot. The parking coordinator repainted the lot's lines to fit a bike rack. The parking coordinator did not care at all about the effect this would have on the stray cat. The parking coordinator knew the new lines would scare the stray cat from its spot.

- agent: `the parking coordinator`
- effect: `scare the stray cat from its spot`

**good** `kmp-mf-024-harm-good`

> A stray cat sleeps under the bushes at the edge of the lot. The parking coordinator repainted the lot's lines to fit a bike rack. The parking coordinator did not care at all about the effect this would have on the stray cat. The parking coordinator knew the new lines would give the stray cat a safe, quiet spot.

- agent: `the parking coordinator`
- effect: `give the stray cat a safe, quiet spot`

