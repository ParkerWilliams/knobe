# Review sheet: 23_mf_round4

Items: `stimuli/foundations.csv`, 18 draft items. Checklist: `docs/DEFINITIONS_AND_CHECKLIST.md` section 6.

Record one decision per item in `stimuli/review/23_mf_round4_decisions.csv`: `approved`, `rejected` or `revise`, your initials as reviewer, the date (YYYY-MM-DD), and a note for every rejected or revise row naming the failed check (e.g. "B4: good version is bigger"). Then run `../../.venv/bin/python -m tools.review apply --items stimuli/foundations.csv --decisions stimuli/review/23_mf_round4_decisions.csv` yourself.

Automated checks (design_problems and tools.lint_stimuli) were clean when this sheet was made.

## Storyline 7: the team captain (shared; storyline checks C2 C4 C5 C6)

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-007-loyalty-bad`

> The club has a long rivalry with the club across town. The team captain changed the club's practice schedule to fit the new gym hours. The team captain did not care at all about the effect this would have on the club. The team captain knew the new schedule would cancel the club's last practice before the big match against the rival club, siding with the rival club.

- agent: `the team captain`
- effect: `side with the rival club`

**good** `kmp-mf-007-loyalty-good`

> The club has a long rivalry with the club across town. The team captain changed the club's practice schedule to fit the new gym hours. The team captain did not care at all about the effect this would have on the club. The team captain knew the new schedule would add an extra practice before the big match against the rival club, standing with the club.

- agent: `the team captain`
- effect: `stand with the club`

## Storyline 12: the scout leader (shared; storyline checks C2 C4 C5 C6)

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-012-loyalty-bad`

> The troop shares the campground with its long-time rival, the troop from the next town. The scout leader drew up a new campsite plan to save walking time. The scout leader did not care at all about the effect this would have on the troop. The scout leader knew the new plan would give the campground's best fire pit to the rival troop, siding with the rival troop.

- agent: `the scout leader`
- effect: `side with the rival troop`

**good** `kmp-mf-012-loyalty-good`

> The troop shares the campground with its long-time rival, the troop from the next town. The scout leader drew up a new campsite plan to save walking time. The scout leader did not care at all about the effect this would have on the troop. The scout leader knew the new plan would claim the campground's best fire pit for the troop's own scouts, standing with the troop.

- agent: `the scout leader`
- effect: `stand with the troop`

## Storyline 15: the book club host (shared; storyline checks C2 C4 C5 C6)

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-015-loyalty-bad`

> The book club has a long rivalry with the book club at the other library. The book club host drew up a new meeting plan, with speaking slots, to fit the library's hours. The book club host did not care at all about the effect this would have on the book club. The book club host knew the new plan would give the club's guest-speaker slot to a member of the rival club, siding with the rival club.

- agent: `the book club host`
- effect: `side with the rival club`

**good** `kmp-mf-015-loyalty-good`

> The book club has a long rivalry with the book club at the other library. The book club host drew up a new meeting plan, with speaking slots, to fit the library's hours. The book club host did not care at all about the effect this would have on the book club. The book club host knew the new plan would give the club's guest-speaker slot to one of the club's own founding members, standing with the book club.

- agent: `the book club host`
- effect: `stand with the book club`

## Storyline 17: the potluck organizer (shared; storyline checks C2 C4 C5 C6)

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-017-loyalty-bad`

> The street's residents have a long rivalry with the next street over whose potluck is best, and the sign-up sheet decides who brings the main dishes. The potluck organizer redid the potluck's sign-up sheet to make it easier to read. The potluck organizer did not care at all about the effect this would have on the street's residents. The potluck organizer knew the new sheet would hand the main dishes to cooks from the rival street, siding with the rival street.

- agent: `the potluck organizer`
- effect: `side with the rival street`

**good** `kmp-mf-017-loyalty-good`

> The street's residents have a long rivalry with the next street over whose potluck is best, and the sign-up sheet decides who brings the main dishes. The potluck organizer redid the potluck's sign-up sheet to make it easier to read. The potluck organizer did not care at all about the effect this would have on the street's residents. The potluck organizer knew the new sheet would give the main dishes to the street's own best cooks, standing with the street's residents.

- agent: `the potluck organizer`
- effect: `stand with the street's residents`

## Storyline 29: the station chief (shared; storyline checks C2 C4 C5 C6)

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**good** `kmp-mf-029-loyalty-good`

> The station has a long rivalry with the station across town. The station chief moved the fire station's training day to Thursday to free up the weekend. The station chief did not care at all about the effect this would have on the station. The station chief knew the move would free Thursday for the station's own crews to train for the county contest against the rival station, standing with the station.

- agent: `the station chief`
- effect: `stand with the station`
- capitalised words (R1: names?): Thursday

## Storyline 109: the delivery driver (purpose; storyline checks C2 C7)

### purity (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-109-purity-bad`

> A stone at the edge of the square has been held sacred for centuries, and no meat may ever touch it. The delivery driver changed the order of the morning deliveries to finish the route faster. The delivery driver did not care at all about the effect this would have on the sacred stone. The delivery driver knew the new order would mean leaving the butcher's crates of meat stacked against the sacred stone, desecrating it.

- agent: `the delivery driver`
- effect: `desecrate the sacred stone`

**good** `kmp-mf-109-purity-good`

> A stone at the edge of the square has been held sacred for centuries, and no meat may ever touch it. The delivery driver changed the order of the morning deliveries to finish the route faster. The delivery driver did not care at all about the effect this would have on the sacred stone. The delivery driver knew the new order would mean bringing the temple's fresh flowers first, in time to lay them at the sacred stone, honoring it.

- agent: `the delivery driver`
- effect: `honor the sacred stone`

## Storyline 110: the architect (purpose; storyline checks C2 C7)

### purity (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**good** `kmp-mf-110-purity-good`

> A shrine stone on the east side of the site is held sacred, and no one may build over it. The architect moved the new library's entrance to the east side to catch more light. The architect did not care at all about the effect this would have on the shrine stone. The architect knew the new entrance would set the entrance steps around the shrine stone, leaving the stone untouched as the lit centerpiece, honoring it.

- agent: `the architect`
- effect: `honor the shrine stone`

## Storyline 115: the florist (purpose; storyline checks C2 C7)

### purity (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-115-purity-bad`

> Flowers from the temple garden are held sacred, and they may never be sold; the new supplier also tends the temple garden. The florist switched suppliers to get cheaper flowers. The florist did not care at all about the effect this would have on the sacred flowers. The florist knew the new supplier would sell the sacred temple flowers.

- agent: `the florist`
- effect: `sell the sacred temple flowers`

**good** `kmp-mf-115-purity-good`

> Flowers from the temple garden are held sacred, and they may never be sold; the new supplier also tends the temple garden. The florist switched suppliers to get cheaper flowers. The florist did not care at all about the effect this would have on the sacred flowers. The florist knew the new supplier would mean carrying the sacred temple flowers back to the temple's altar each morning instead of to the shop, honoring them.

- agent: `the florist`
- effect: `honor the sacred temple flowers`

## Storyline 116: the roofer (purpose; storyline checks C2 C7)

### purity (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**good** `kmp-mf-116-purity-good`

> A carved stone above the old church door is held sacred, and no one may touch it. The roofer replaced the old church's roof tiles to stop a leak. The roofer did not care at all about the effect this would have on the sacred carving. The roofer knew the roofing work would mean laying the new tiles so that rainwater runs away from the sacred carving, honoring it.

- agent: `the roofer`
- effect: `honor the sacred carving`

## Storyline 120: the beekeeper (purpose; storyline checks C2 C7)

### purity (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**good** `kmp-mf-120-purity-good`

> The hilltop above the field is held sacred, and no one may farm on it; honey from the valley is offered at its shrine each spring. The beekeeper moved the hives to a new field to get more sun. The beekeeper did not care at all about the effect this would have on the sacred hilltop. The beekeeper knew the new field would place the hives in the valley below, so that their first honey goes to the sacred hilltop's shrine, honoring it.

- agent: `the beekeeper`
- effect: `honor the sacred hilltop`

## Storyline 121: the woodworker (purpose; storyline checks C2 C7)

### purity (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-121-purity-bad`

> An old wooden cross stands in the middle of the chapel floor and is held sacred, and nothing may be fixed to it. The woodworker built new pews for the chapel to replace the broken ones. The woodworker did not care at all about the effect this would have on the sacred cross. The woodworker knew the new pews would mean bolting the front pew to the base of the sacred cross to steady it, desecrating it.

- agent: `the woodworker`
- effect: `desecrate the sacred cross`

**good** `kmp-mf-121-purity-good`

> An old wooden cross stands in the middle of the chapel floor and is held sacred, and nothing may be fixed to it. The woodworker built new pews for the chapel to replace the broken ones. The woodworker did not care at all about the effect this would have on the sacred cross. The woodworker knew the new pews would leave an open circle around the sacred cross, with every pew facing it, honoring it.

- agent: `the woodworker`
- effect: `honor the sacred cross`

