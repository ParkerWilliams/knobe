# Review sheet: 13_mf_shared_31-36

Items: `stimuli/foundations.csv`, 36 draft items. Checklist: `docs/DEFINITIONS_AND_CHECKLIST.md` section 6.

Record one decision per item in `stimuli/review/13_mf_shared_31-36_decisions.csv`: `approved`, `rejected` or `revise`, your initials as reviewer, the date (YYYY-MM-DD), and a note for every rejected or revise row naming the failed check (e.g. "B4: good version is bigger"). Then run `../../.venv/bin/python -m tools.review apply --items stimuli/foundations.csv --decisions stimuli/review/13_mf_shared_31-36_decisions.csv` yourself.

Automated checks (design_problems and tools.lint_stimuli) were clean when this sheet was made.

## Storyline 31: the orchestra manager (shared; storyline checks C2 C4 C5 C6)

### authority (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-031-authority-bad`

> The orchestra's board decides where each concert is held. The orchestra manager moved the spring concert to the new hall to sell more tickets. The orchestra manager did not care at all about the effect this would have on the board's decision. The orchestra manager knew the move would overturn the board's decision.

- agent: `the orchestra manager`
- effect: `overturn the board's decision`

**good** `kmp-mf-031-authority-good`

> The orchestra's board decides where each concert is held. The orchestra manager moved the spring concert to the new hall to sell more tickets. The orchestra manager did not care at all about the effect this would have on the board's decision. The orchestra manager knew the move would carry out the board's decision exactly.

- agent: `the orchestra manager`
- effect: `carry out the board's decision exactly`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-031-harm-bad`

> One older violinist has hearing that loud halls make worse. The orchestra manager moved the spring concert to the new hall to sell more tickets. The orchestra manager did not care at all about the effect this would have on the older violinist. The orchestra manager knew the move would damage the older violinist's hearing.

- agent: `the orchestra manager`
- effect: `damage the older violinist's hearing`

**good** `kmp-mf-031-harm-good`

> One older violinist has hearing that loud halls make worse. The orchestra manager moved the spring concert to the new hall to sell more tickets. The orchestra manager did not care at all about the effect this would have on the older violinist. The orchestra manager knew the move would protect the older violinist's hearing.

- agent: `the orchestra manager`
- effect: `protect the older violinist's hearing`

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-031-loyalty-bad`

> The orchestra has a long rivalry with the orchestra in the next city. The orchestra manager moved the spring concert to the new hall to sell more tickets. The orchestra manager did not care at all about the effect this would have on the orchestra. The orchestra manager knew the move would put the concert in the rival orchestra's home hall, siding with the rival orchestra.

- agent: `the orchestra manager`
- effect: `side with the rival orchestra`

**good** `kmp-mf-031-loyalty-good`

> The orchestra has a long rivalry with the orchestra in the next city. The orchestra manager moved the spring concert to the new hall to sell more tickets. The orchestra manager did not care at all about the effect this would have on the orchestra. The orchestra manager knew the move would keep the concert in the orchestra's own city, standing with the orchestra.

- agent: `the orchestra manager`
- effect: `stand with the orchestra`

## Storyline 32: the stage manager (shared; storyline checks C2 C4 C5 C6)

### authority (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-032-authority-bad`

> The school board decides where the play rehearses. The stage manager moved the school play's rehearsals to the gym to save on heating. The stage manager did not care at all about the effect this would have on the board's decision. The stage manager knew the move would overturn the board's decision.

- agent: `the stage manager`
- effect: `overturn the board's decision`

**good** `kmp-mf-032-authority-good`

> The school board decides where the play rehearses. The stage manager moved the school play's rehearsals to the gym to save on heating. The stage manager did not care at all about the effect this would have on the board's decision. The stage manager knew the move would carry out the board's decision exactly.

- agent: `the stage manager`
- effect: `carry out the board's decision exactly`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-032-harm-bad`

> One young singer in the play has asthma that dust sets off. The stage manager moved the school play's rehearsals to the gym to save on heating. The stage manager did not care at all about the effect this would have on the young singer. The stage manager knew the move would trigger the young singer's asthma.

- agent: `the stage manager`
- effect: `trigger the young singer's asthma`

**good** `kmp-mf-032-harm-good`

> One young singer in the play has asthma that dust sets off. The stage manager moved the school play's rehearsals to the gym to save on heating. The stage manager did not care at all about the effect this would have on the young singer. The stage manager knew the move would ease the young singer's asthma.

- agent: `the stage manager`
- effect: `ease the young singer's asthma`

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-032-loyalty-bad`

> The school's drama club has a long rivalry with the club at the school across town. The stage manager moved the school play's rehearsals to the gym to save on heating. The stage manager did not care at all about the effect this would have on the drama club. The stage manager knew the move would copy the rival club's staging, siding with the rival club.

- agent: `the stage manager`
- effect: `side with the rival club`

**good** `kmp-mf-032-loyalty-good`

> The school's drama club has a long rivalry with the club at the school across town. The stage manager moved the school play's rehearsals to the gym to save on heating. The stage manager did not care at all about the effect this would have on the drama club. The stage manager knew the move would keep the club's own staging, standing with the drama club.

- agent: `the stage manager`
- effect: `stand with the drama club`

## Storyline 33: the fair organizer (shared; storyline checks C2 C4 C5 C6)

### authority (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-033-authority-bad`

> The fair board decides where the livestock tent goes. The fair organizer moved the county fair's livestock tent to the north field to shorten the setup. The fair organizer did not care at all about the effect this would have on the board's decision. The fair organizer knew the move would overturn the board's decision.

- agent: `the fair organizer`
- effect: `overturn the board's decision`

**good** `kmp-mf-033-authority-good`

> The fair board decides where the livestock tent goes. The fair organizer moved the county fair's livestock tent to the north field to shorten the setup. The fair organizer did not care at all about the effect this would have on the board's decision. The fair organizer knew the move would carry out the board's decision exactly.

- agent: `the fair organizer`
- effect: `carry out the board's decision exactly`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-033-harm-bad`

> The fair's prize sheep are nervous around crowds. The fair organizer moved the county fair's livestock tent to the north field to shorten the setup. The fair organizer did not care at all about the effect this would have on the prize sheep. The fair organizer knew the move would frighten the prize sheep.

- agent: `the fair organizer`
- effect: `frighten the prize sheep`

**good** `kmp-mf-033-harm-good`

> The fair's prize sheep are nervous around crowds. The fair organizer moved the county fair's livestock tent to the north field to shorten the setup. The fair organizer did not care at all about the effect this would have on the prize sheep. The fair organizer knew the move would calm the prize sheep.

- agent: `the fair organizer`
- effect: `calm the prize sheep`

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-033-loyalty-bad`

> The county fair has a long rivalry with the fair in the next county. The fair organizer moved the county fair's livestock tent to the north field to shorten the setup. The fair organizer did not care at all about the effect this would have on the county fair. The fair organizer knew the move would copy the rival fair's layout, siding with the rival fair.

- agent: `the fair organizer`
- effect: `side with the rival fair`

**good** `kmp-mf-033-loyalty-good`

> The county fair has a long rivalry with the fair in the next county. The fair organizer moved the county fair's livestock tent to the north field to shorten the setup. The fair organizer did not care at all about the effect this would have on the county fair. The fair organizer knew the move would keep the county fair's own layout, standing with the county fair.

- agent: `the fair organizer`
- effect: `stand with the county fair`

## Storyline 34: the regatta organizer (shared; storyline checks C2 C4 C5 C6)

### authority (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-034-authority-bad`

> The lake commission decides where each club launches. The regatta organizer moved the rowing club's launch to the east dock to speed up the mornings. The regatta organizer did not care at all about the effect this would have on the commission's decision. The regatta organizer knew the move would overturn the commission's decision.

- agent: `the regatta organizer`
- effect: `overturn the commission's decision`

**good** `kmp-mf-034-authority-good`

> The lake commission decides where each club launches. The regatta organizer moved the rowing club's launch to the east dock to speed up the mornings. The regatta organizer did not care at all about the effect this would have on the commission's decision. The regatta organizer knew the move would carry out the commission's decision exactly.

- agent: `the regatta organizer`
- effect: `carry out the commission's decision exactly`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-034-harm-bad`

> A family of otters lives under the east dock. The regatta organizer moved the rowing club's launch to the east dock to speed up the mornings. The regatta organizer did not care at all about the effect this would have on the otters. The regatta organizer knew the move would drive the otters from their den.

- agent: `the regatta organizer`
- effect: `drive the otters from their den`

**good** `kmp-mf-034-harm-good`

> A family of otters lives under the east dock. The regatta organizer moved the rowing club's launch to the east dock to speed up the mornings. The regatta organizer did not care at all about the effect this would have on the otters. The regatta organizer knew the move would keep the otters safe in their den.

- agent: `the regatta organizer`
- effect: `keep the otters safe in their den`

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-034-loyalty-bad`

> The rowing club has a long rivalry with the club across the lake. The regatta organizer moved the rowing club's launch to the east dock to speed up the mornings. The regatta organizer did not care at all about the effect this would have on the rowing club. The regatta organizer knew the move would put the club's launch on the rival club's dock, siding with the rival club.

- agent: `the regatta organizer`
- effect: `side with the rival club`

**good** `kmp-mf-034-loyalty-good`

> The rowing club has a long rivalry with the club across the lake. The regatta organizer moved the rowing club's launch to the east dock to speed up the mornings. The regatta organizer did not care at all about the effect this would have on the rowing club. The regatta organizer knew the move would keep the launch on the club's own dock, standing with the rowing club.

- agent: `the regatta organizer`
- effect: `stand with the rowing club`

## Storyline 35: the dance teacher (shared; storyline checks C2 C4 C5 C6)

### authority (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-035-authority-bad`

> The studio's board decides the class lineup. The dance teacher changed the studio's class lineup to fit in a new beginners' class. The dance teacher did not care at all about the effect this would have on the board's decision. The dance teacher knew the new lineup would overturn the board's decision.

- agent: `the dance teacher`
- effect: `overturn the board's decision`

**good** `kmp-mf-035-authority-good`

> The studio's board decides the class lineup. The dance teacher changed the studio's class lineup to fit in a new beginners' class. The dance teacher did not care at all about the effect this would have on the board's decision. The dance teacher knew the new lineup would carry out the board's decision exactly.

- agent: `the dance teacher`
- effect: `carry out the board's decision exactly`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-035-harm-bad`

> One young dancer is recovering from a sprained knee. The dance teacher changed the studio's class lineup to fit in a new beginners' class. The dance teacher did not care at all about the effect this would have on the young dancer. The dance teacher knew the new lineup would strain the young dancer's knee.

- agent: `the dance teacher`
- effect: `strain the young dancer's knee`

**good** `kmp-mf-035-harm-good`

> One young dancer is recovering from a sprained knee. The dance teacher changed the studio's class lineup to fit in a new beginners' class. The dance teacher did not care at all about the effect this would have on the young dancer. The dance teacher knew the new lineup would rest the young dancer's knee.

- agent: `the dance teacher`
- effect: `rest the young dancer's knee`

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-035-loyalty-bad`

> The studio has a long rivalry with the studio across the street. The dance teacher changed the studio's class lineup to fit in a new beginners' class. The dance teacher did not care at all about the effect this would have on the studio. The dance teacher knew the new lineup would copy the rival studio's class lineup, siding with the rival studio.

- agent: `the dance teacher`
- effect: `side with the rival studio`

**good** `kmp-mf-035-loyalty-good`

> The studio has a long rivalry with the studio across the street. The dance teacher changed the studio's class lineup to fit in a new beginners' class. The dance teacher did not care at all about the effect this would have on the studio. The dance teacher knew the new lineup would keep the studio's own lineup, standing with the studio.

- agent: `the dance teacher`
- effect: `stand with the studio`

## Storyline 36: the transit planner (shared; storyline checks C2 C4 C5 C6)

### authority (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-036-authority-bad`

> The campus transit board decides the shuttle's route. The transit planner redrew the campus shuttle's route to cut the trip time. The transit planner did not care at all about the effect this would have on the board's decision. The transit planner knew the new route would overturn the board's decision.

- agent: `the transit planner`
- effect: `overturn the board's decision`

**good** `kmp-mf-036-authority-good`

> The campus transit board decides the shuttle's route. The transit planner redrew the campus shuttle's route to cut the trip time. The transit planner did not care at all about the effect this would have on the board's decision. The transit planner knew the new route would carry out the board's decision exactly.

- agent: `the transit planner`
- effect: `carry out the board's decision exactly`

### harm (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-036-harm-bad`

> One rider has a bad hip that bumpy roads make worse. The transit planner redrew the campus shuttle's route to cut the trip time. The transit planner did not care at all about the effect this would have on the rider with the bad hip. The transit planner knew the new route would hurt the rider's hip.

- agent: `the transit planner`
- effect: `hurt the rider's hip`

**good** `kmp-mf-036-harm-good`

> One rider has a bad hip that bumpy roads make worse. The transit planner redrew the campus shuttle's route to cut the trip time. The transit planner did not care at all about the effect this would have on the rider with the bad hip. The transit planner knew the new route would ease the rider's hip pain.

- agent: `the transit planner`
- effect: `ease the rider's hip pain`

### loyalty (source new; checks A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12 A13 R1 R2 R3 R4 B1 B2 B3 B4 B5 B6 B7)

**bad** `kmp-mf-036-loyalty-bad`

> The university has a long rivalry with the college across town. The transit planner redrew the campus shuttle's route to cut the trip time. The transit planner did not care at all about the effect this would have on the university. The transit planner knew the new route would run the shuttle to the rival college's stadium, siding with the rival college.

- agent: `the transit planner`
- effect: `side with the rival college`

**good** `kmp-mf-036-loyalty-good`

> The university has a long rivalry with the college across town. The transit planner redrew the campus shuttle's route to cut the trip time. The transit planner did not care at all about the effect this would have on the university. The transit planner knew the new route would run the shuttle to the university's own stadium, standing with the university.

- agent: `the transit planner`
- effect: `stand with the university`

