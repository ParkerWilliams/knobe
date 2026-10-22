# Stimuli notes

How the three items files were written. The machine-readable record of
every change from Ngo et al. (2015) and every fresh action is
`nonmoral_log.csv`; the review record is `review/*_decisions.csv`.

## Authorship and disclosure (DESIGN.md §3.4)

Every item except the `ngo_verbatim` set was drafted by an LLM (Claude;
model ID and date per batch below) and reviewed item by item by the
researcher against `docs/DEFINITIONS_AND_CHECKLIST.md` §6. `approved` is
set only by `tools.review apply` from the researcher's decisions file, and
`tools.lint_stimuli` checks that every approval matches the current text.
The paper's methods disclose this; suggested wording: "Items were drafted
with an LLM (Claude) and every item was reviewed by the authors against a
written checklist before screening."

Screening reviewer: `claude-sonnet-4-6` (`protocol.REVIEWER_MODEL`; DESIGN.md amendment 2026-10-01, reviewer pin).
Drafting model: `claude-opus-5-5` (role-noun table, 2026-10-22; per batch below). It differs from the reviewer, so the screen is not the drafter (decision T).

## File-wide conventions

- Straight apostrophes (') in all authored items; `ngo_verbatim` keeps Ngo's
  curly ones (decision N). The B8 lint reads ’ and ' as equal.
- Role nouns: lower case mid-sentence in `agent` ("the manager"),
  capitalised at the start of a sentence (DEFINITIONS §3.4).
- Self-referring side effects repeat the role noun (decision J).

## Role nouns, one per storyline (C2, D3, decisions O and P)

Drafted 2026-10-22 and reviewed by MM the same day (Task 9 gate; rulings below the table). Rules
applied: where Ngo already uses a role, the bad version's role is kept
(decision O). The exceptions are gendered roles (made neutral), roles R3
names (replaced), and D3 collisions (given a distinct plain role). Where
Ngo uses names, the chosen role fits the bad version's action and goal
(the goal kept under decision B2) and also has a plausible prudential and
procedural story (C3). All 40 strings are distinct (D3). Non-agent names
become roles under decision L ("the neighbor", "the roommate"); those are
not listed here.

| storyline | Ngo bad / good agent | role noun | why (kept / neutralised / replaced / R3 exception) | loaded role (decision P) |
|---|---|---|---|---|
| 1 | Bill / Robyn | the engineer | name → role; releases a gadget on deadline | no |
| 2 | the CEO / the chairman | the board chair | replaced (R3: CEO); takes the good version's role, neutralised (chairman → chair), with "board" so "the chair" isn't read as furniture | no |
| 3 | Roger / Renee | the investor | name → role; enacts a financial scheme | no |
| 4 | Natasha / Floyd | the club owner | name → role; renovates the country club | no |
| 5 | the mayor / the councilwoman | the mayor | kept (bad version's role) | yes: elected politician, goal is votes |
| 6 | the CEO / the company owner | the plant manager | replaced (R3: CEO); the good version's "company owner" would echo storylines 4 and 20, and a plant fits the flooding effect | no |
| 7 | the airplane bomber / the bomber pilot | the bomber pilot | R3 exception (the role is the story). Departs from the bad-version rule: "the airplane bomber" can read as someone who bombs airplanes; decision O already names "the bomber pilot" | yes: wartime bombing |
| 8 | the university president / the athletic director | the university president | kept | no |
| 9 | Jenny / Stanley | the grower | name → role; "the farmer" is taken by storyline 39 (D3) | no |
| 10 | Kate / Jared | the relative | name → role; niece and nephew are gendered (R3). Kin noun restructured (review ruling 1) | no |
| 11 | Tim / Tricia | the homeowner | name → role; decorates the house | no |
| 12 | the scientist / the scientist | the scientist | kept | no |
| 13 | Joe / Helen | the merchant | name → role; opens a kiosk. "Vendor" would clash with the affected "nearby vendors" | no |
| 14 | Marta / Phil | the tenant | name → role; cleans the floor at home. Leaves room for lease rules in the procedural arm | no |
| 15 | Jacob / Rachel | the student | name → role; party and the roommate's exam | no |
| 16 | Russell / Vicky | the gardener | name → role; plants a tree | no |
| 17 | Brenda / Billy | the shelter director | name → role; cuts shelter spending for a raise | no |
| 18 | the Surgeon General / the Defense Secretary | the surgeon general | kept; lower case mid-sentence (file convention) | yes: political appointee, goal is keeping the post |
| 19 | Carolyn / Christopher | the employer | name → role; plan affects employees | no |
| 20 | Tina / Ronald | the store owner | name → role; builds a road to the country store | no |
| 21 | Jerry / Linda | the hunter | name → role; hunts to earn a living | no |
| 22 | Irene / Holly | the pregnant patient | name → role; "expectant mother" is gendered (R3) | no |
| 23 | Eugene / Margaret | the spectator | name → role; yells at a match | no |
| 24 | Rebecca / Sean | the protester | name → role; protests to get on TV | no |
| 25 | Curtis / Lori | the blogger | name → role; releases documents for publicity. "Journalist" carries its own praise and blame | no |
| 26 | Clara / Martin | the school administrator | name → role; school lunch plan | no |
| 27 | Philip / Alice | the adult child | name → role; son and daughter are gendered (R3). Kin noun restructured (review ruling 1) | no |
| 28 | Diane / Josh | the dog owner | name → role; the bad version's animal is a puppy | no |
| 29 | the cop / the cop | the cop | kept | no |
| 30 | Flora / Ernest | the policyholder | name → role; faked death and life insurance. Fits a prudential story | no |
| 31 | Norman / Angela | the resident | name → role; protests at a church. "The protester" is taken by storyline 24 (D3) | no |
| 32 | Jo / Kurt | the author | name → role; writes a book | no |
| 33 | Keith / Melissa | the newlywed | name → role; marriage. Groom and bride are gendered (R3). Singular "their" (review ruling 4) | no |
| 34 | the activist / the terrorist | the activist | kept (bad version's role) | yes: the action is a bomb threat; "activist" can also carry praise |
| 35 | the financial officer / the treasurer | the financial officer | kept | no |
| 36 | the CEO / the CEO | the product designer | replaced (R3: CEO); revises a device | no |
| 37 | the cult leader / the cult leader | the cult leader | R3 exception (the role is the story) | yes |
| 38 | the candidate / the candidate | the candidate | kept | yes: running for President |
| 39 | the farmer / the farmer | the farmer | kept | no |
| 40 | the doctor / the doctor | the doctor | kept | no |

Loaded storylines for the decision P sensitivity fit: 5, 7, 18, 34, 37, 38.

### Review (MM, 2026-10-22): the table stands, with these rulings

1. **Storylines 10 and 27 (kin stories): restructure.** The agent keeps
   the role ("the relative", "the adult child"). The kin noun names the
   other person with an article, not a possessive: "The relative placed
   an uncle in a nursing home ...", then "the uncle". The pronoun changes
   in storyline 10 need `nonmoral_log.csv` rows (lint).
2. **Storyline 7: "the bomber pilot"**, not "the airplane bomber" (an
   accepted departure from the bad-version rule).
3. **Storyline 34: "the activist"** in every arm, including the good
   version ("The activist bombed the jail").
4. **Storyline 33: singular "their".** "The newlywed married their wife"
   (and "their parents"), not "the newlywed's wife". This is a researcher
   exception to R4 for storyline 33 only; other storylines still repeat
   the role noun or restructure.
5. **Shared head nouns** ("the club owner", "the store owner", "the dog
   owner"): fine as they are.
6. **"Patient" in storylines 22 and 40:** fine as it is.

## Batches

| batch | file | storylines / arms | items | drafting model | drafted | sheet commit | decisions applied |
|---|---|---|---|---|---|---|---|
| 02_nm_moral_01-20 | nonmoral.csv | 1–20 / moral (adapted Ngo) | 40 | `claude-opus-5-5` | 2026-10-22 | the commit that adds this row | |
| 03_nm_moral_21-40 | nonmoral.csv | 21–40 / moral (adapted Ngo) | 40 | `claude-opus-5-5` | 2026-10-22 | the commit that adds this row | |
| 04_nm_prudential_01-20 | nonmoral.csv | 1–20 / prudential | 40 | `claude-opus-5-5` | 2026-10-22 | the commit that adds this row | |
| 05_nm_prudential_21-40 | nonmoral.csv | 21–40 / prudential | 40 | `claude-opus-5-5` | 2026-10-22 | the commit that adds this row | |
| 06_nm_procedural_01-20 | nonmoral.csv | 1–20 / procedural | 40 | `claude-opus-5-5` | 2026-10-22 | the commit that adds this row | |
| 07_nm_procedural_21-40 | nonmoral.csv | 21–40 / procedural | 40 | `claude-opus-5-5` | 2026-10-22 | the commit that adds this row | |
| 08_mf_shared_01-06 | foundations.csv | 1–6 | 48 | `claude-opus-5-5` | 2026-10-22 | the commit that adds this row | |
| 09_mf_shared_07-12 | foundations.csv | 7–12 | 48 | `claude-opus-5-5` | 2026-10-22 | the commit that adds this row | |
| 10_mf_shared_13-18 | foundations.csv | 13–18 | 36 | `claude-opus-5-5` | 2026-10-22 | the commit that adds this row | |
| 11_mf_shared_19-24 | foundations.csv | 19–24 | 36 | `claude-opus-5-5` | 2026-10-22 | the commit that adds this row | |
| 12_mf_shared_25-30 | foundations.csv | 25–30 | 36 | `claude-opus-5-5` | 2026-10-22 | the commit that adds this row | |
| 13_mf_shared_31-36 | foundations.csv | 31–36 | 36 | `claude-opus-5-5` | 2026-10-22 | the commit that adds this row | |
| 14_mf_purity_101-120 | foundations.csv | 101–120 / purity (purpose) | 40 | `claude-opus-5-5` | 2026-10-22 | the commit that adds this row | |

| 15_nm_surv_moral | nonmoral.csv | screening survivors / moral | 44 | (batches 02–03) | 2026-10-22 | the commit that adds this row | |
| 16_nm_surv_prudential | nonmoral.csv | screening survivors / prudential | 78 | (batches 04–05) | 2026-10-22 | the commit that adds this row | |
| 17_nm_surv_procedural | nonmoral.csv | screening survivors / procedural | 76 (rebuilt after the procedural limits) | (batches 06–07) | 2026-10-22 | the commit that adds this row | |
| 18_mf_surv_01-18 | foundations.csv | screening survivors / 1–18 | 116 (rebuilt after the purity and fairness rewrites) | (batches 08–10) | 2026-10-22 | the commit that adds this row | |
| 19_mf_surv_19-36_101-120 | foundations.csv | screening survivors / 19–36, 101–120 | 138 (rebuilt after the purity and fairness rewrites) | (batches 11–14) | 2026-10-22 | the commit that adds this row | |

**2026-10-22, screen first (MM).** Drafts were screened before review
(`kmp.screen --allow-draft`; ANALYSIS_LOG.md). Sheets 02–14 were removed
unfilled, and are still in git history (a268b1d and earlier). Sheets 15–19
list only the items in each set's `outputs/screening/<set>/selected_items.csv`
(`tools.review sheet --only`). Items that failed screening stay `draft` in the
files until they are redrafted or dropped.

### Drafting notes, batches 04–07

- Clause 1 reuses the adapted moral bad sentence (decision E) except for
  the 15 `fresh_action` pairs in `nonmoral_log.csv`. Those are prudential
  7, 28, 30, 34, 37, 40 and procedural 7, 22, 23, 27, 28, 30, 34, 37, 40.
  Where Ngo's action is itself wrongdoing (28, 30, 34, 40), both arms use
  a fresh action (§4.2 Out).
- Reused actions that still carry moral content, kept under decision E:
  storyline 10 (placing an uncle in a home), 17 (cutting shelter spending
  for the director's own salary, close to the §4.2 wrongdoing case), 22
  (inducing labor, with the baby's health). The domain screen will show
  whether that bleeds into the arm; a fresh action is the fix if it does.
- A7 reads "name no damage to anyone's welfare" for prudential items too.
  §4.2's own example drains the agent's savings, so A7 is read as anyone
  other than the agent.
- `source = pilot` (decision Q) for prudential 1, 4, 9, 11, 15, 20, 21, 32,
  where a pilot variant's side-effect idea was the starting point. Every
  procedural pair is `new`: the pilot ones mostly changed the action
  between bad and good (B2), or used "tradition" (§4.3 Out).

## Foundations scaffold roster (Task 14)

Drafted 2026-10-22. MM asked for the foundations items to be drafted from it the same day, which counts as approval as written (Task 14 gate). All 56
storylines are new (decision H): Ngo's harmful actions would fail C5, so
none is reused. Each shared action is harm-neutral (C5) and set in a group
setting, so each norm can apply: an agreed equal split (fairness), a rival
group (loyalty), a body with standing to decide (authority), a sacred
object (purity). Allocation: storylines 1–6 add purity plus two of F/L/A,
7–12 add all three of F/L/A, and 13–36 add two (8 each of FL, FA, LA). Role
nouns are distinct from each other and from `nonmoral.csv`. Purpose-written
storylines show the planned sacred object or taboo in brackets.

| storyline | scaffold | role noun | action-and-goal sentence (verbatim) | pairs planned | origin (decision H) | batch |
|---|---|---|---|---|---|---|
| 1 | shared | the choir director | The choir director drew up a new seating chart for rehearsals to fit the new risers. (rewritten 2026-10-22; was: The choir director moved the choir's rehearsals to the church basement to save on rent.) | harm, purity, fairness, authority | new | 08 |
| 2 | shared | the groundskeeper | The groundskeeper changed the cemetery's mowing route to finish the job sooner. | harm, purity, fairness, authority | new | 08 |
| 3 | shared | the event planner | The event planner drew up the festival's stage schedule to fit in more bands. (rewritten 2026-10-22; was: The event planner moved the festival's main stage to the riverbank to get better sound.) | harm, purity, fairness, loyalty | new | 08 |
| 4 | shared | the trail steward | The trail steward rerouted the hiking trail to make the climb less steep. | harm, purity, loyalty, authority | new | 08 |
| 5 | shared | the kitchen manager | The kitchen manager drew up a new weekly plan of dishes and cooks to use up the stored rice. (rewritten 2026-10-22; was: The kitchen manager changed the community kitchen's menu to use up the stored rice.) | harm, purity, fairness, loyalty | new | 08 |
| 6 | shared | the building superintendent | The building superintendent redid the lobby's layout to make cleaning easier. | harm, purity, loyalty, authority | new | 08 |
| 7 | shared | the team captain | The team captain changed the club's practice schedule to fit the new gym hours. | harm, fairness, loyalty, authority | new | 09 |
| 8 | shared | the band leader | The band leader planned a new parade lineup and route to shorten the walk. (rewritten 2026-10-22; was: The band leader rewrote the parade's marching order to shorten the route.) | harm, fairness, loyalty, authority | new | 09 |
| 9 | shared | the office manager | The office manager drew up a new desk plan to fit in a new printer. (rewritten 2026-10-22; was: The office manager rearranged the office's desks to fit in a new printer.) | harm, fairness, loyalty, authority | new | 09 |
| 10 | shared | the league organizer | The league organizer moved the league's games to Saturday mornings to free up the evenings. | harm, fairness, loyalty, authority | new | 09 |
| 11 | shared | the housing coordinator | The housing coordinator reassigned the dorm's rooms to finish the paperwork early. | harm, fairness, loyalty, authority | new | 09 |
| 12 | shared | the scout leader | The scout leader drew up a new campsite plan to save walking time. (rewritten 2026-10-22; was: The scout leader moved the troop's campsite closer to the parking lot to save walking time.) | harm, fairness, loyalty, authority | new | 09 |
| 13 | shared | the quiz host | The quiz host changed the pub quiz's seating plan to fit more tables. | harm, fairness, loyalty | new | 10 |
| 14 | shared | the carpool organizer | The carpool organizer redrew the carpool's routes to save gas. | harm, fairness, loyalty | new | 10 |
| 15 | shared | the book club host | The book club host drew up a new meeting plan, with speaking slots, to fit the library's hours. (rewritten 2026-10-22; was: The book club host moved the club's meetings to the library to have more space.) | harm, fairness, loyalty | new | 10 |
| 16 | shared | the robotics coach | The robotics coach drew up a new workshop schedule to fit in training on the new tools. (rewritten 2026-10-22; was: The robotics coach reorganized the team's workshop to make room for new tools.) | harm, fairness, loyalty | new | 10 |
| 17 | shared | the potluck organizer | The potluck organizer redid the potluck's sign-up sheet to make it easier to read. | harm, fairness, loyalty | new | 10 |
| 18 | shared | the tour guide | The tour guide drew up a new tour plan, with a walking order, to avoid the construction. (rewritten 2026-10-22; was: The tour guide changed the walking tour's route to avoid the construction.) | harm, fairness, loyalty | new | 10 |
| 19 | shared | the debate coach | The debate coach drew up a new practice schedule to use the auditorium's microphones. (rewritten 2026-10-22; was: The debate coach moved the team's practice to the auditorium to use the microphones.) | harm, fairness, loyalty | new | 11 |
| 20 | shared | the race organizer | The race organizer drew up a new start plan to simplify the setup. (rewritten 2026-10-22; was: The race organizer moved the fun run's starting line to the park entrance to simplify the setup.) | harm, fairness, loyalty | new | 11 |
| 21 | shared | the librarian | The librarian drew up a new reading-room plan, with a timetable for the big tables, to fit more shelves. (rewritten 2026-10-22; was: The librarian rearranged the reading room to fit more shelves.) | harm, fairness, authority | new | 11 |
| 22 | shared | the market manager | The market manager redrew the farmers market's stall map to widen the aisles. | harm, fairness, authority | new | 11 |
| 23 | shared | the pool manager | The pool manager changed the pool's lane setup to make cleaning easier. | harm, fairness, authority | new | 11 |
| 24 | shared | the parking coordinator | The parking coordinator drew up a new parking plan to fit a bike rack. (rewritten 2026-10-22; was: The parking coordinator repainted the lot's lines to fit a bike rack.) | harm, fairness, authority | new | 11 |
| 25 | shared | the lab manager | The lab manager changed the lab's booking system to cut down on paperwork. | harm, fairness, authority | new | 12 |
| 26 | shared | the camp counselor | The camp counselor changed the camp's activity schedule to finish the day earlier. | harm, fairness, authority | new | 12 |
| 27 | shared | the theater manager | The theater manager drew up a new backstage plan, assigning the rooms, to store the new props. (rewritten 2026-10-22; was: The theater manager reorganized the backstage area to store the new props.) | harm, fairness, authority | new | 12 |
| 28 | shared | the shift planner | The shift planner redid the warehouse's break schedule to simplify the roster. | harm, fairness, authority | new | 12 |
| 29 | shared | the station chief | The station chief moved the fire station's training day to Thursday to free up the weekend. | harm, loyalty, authority | new | 12 |
| 30 | shared | the editor | The editor redesigned the school paper's front page to fit more photos. | harm, loyalty, authority | new | 12 |
| 31 | shared | the orchestra manager | The orchestra manager moved the spring concert to the new hall to sell more tickets. | harm, loyalty, authority | new | 13 |
| 32 | shared | the stage manager | The stage manager moved the school play's rehearsals to the gym to save on heating. | harm, loyalty, authority | new | 13 |
| 33 | shared | the fair organizer | The fair organizer moved the county fair's livestock tent to the north field to shorten the setup. | harm, loyalty, authority | new | 13 |
| 34 | shared | the regatta organizer | The regatta organizer moved the rowing club's launch to the east dock to speed up the mornings. | harm, loyalty, authority | new | 13 |
| 35 | shared | the dance teacher | The dance teacher changed the studio's class lineup to fit in a new beginners' class. | harm, loyalty, authority | new | 13 |
| 36 | shared | the transit planner | The transit planner redrew the campus shuttle's route to cut the trip time. | harm, loyalty, authority | new | 13 |
| 101 | purpose | the surveyor | The surveyor marked a new property line to finish the survey early. | purity (an ancient burial mound) | new | 14 |
| 102 | purpose | the caterer | The caterer changed the feast's main dish to cut costs. | purity (a food taboo for the holy day) | new | 14 |
| 103 | purpose | the mover | The mover packed the house's boxes in a new order to finish faster. | purity (a household shrine) | new | 14 |
| 104 | purpose | the plumber | The plumber rerouted a water pipe to finish the repair sooner. | purity (a well of holy water) | new | 14 |
| 105 | purpose | the photographer | The photographer set up the lights in a new spot to get a brighter picture. | purity (a temple altar) | new | 14 |
| 106 | purpose | the electrician | The electrician ran a new cable through the chapel to save wire. | purity (a relic niche) | new | 14 |
| 107 | purpose | the painter | The painter repainted the old meeting hall to brighten the room. | purity (a memorial wall) | new | 14 |
| 108 | purpose | the landscaper | The landscaper moved the flower beds to cut the watering time. | purity (a sacred grove) | new | 14 |
| 109 | purpose | the delivery driver | The delivery driver changed the order of the morning deliveries to finish the route faster. (rewritten 2026-10-22; was: The delivery driver parked the van in a new spot to unload faster.) | purity (a sacred stone) | new | 14 |
| 110 | purpose | the architect | The architect moved the new library's entrance to the east side to catch more light. | purity (a shrine stone) | new | 14 |
| 111 | purpose | the sculptor | The sculptor changed the studio's clay mix to save money. (rewritten 2026-10-22; was: The sculptor bought clay from a new supplier to save money.) | purity (clay from a sacred riverbank) | new | 14 |
| 112 | purpose | the tailor | The tailor cut the festival robes from a new fabric to finish the order sooner. | purity (a ritual-fabric taboo) | new | 14 |
| 113 | purpose | the baker | The baker changed the bread recipe to use up the spelt flour. (rewritten 2026-10-22; was: The baker changed the bread recipe to make the dough rise faster.) | purity (the holy-day bread rule) | new | 14 |
| 114 | purpose | the janitor | The janitor changed the cleaning order to finish the shift sooner. | purity (a prayer-room shrine) | new | 14 |
| 115 | purpose | the florist | The florist switched suppliers to get cheaper flowers. | purity (flowers from a sacred garden) | new | 14 |
| 116 | purpose | the roofer | The roofer replaced the old church's roof tiles to stop a leak. (rewritten 2026-10-22; was: The roofer set the ladder in a new spot to finish the roof faster.) | purity (a carved holy stone) | new | 14 |
| 117 | purpose | the carpenter | The carpenter reused old timber to save on wood. | purity (timber from a sacred grove) | new | 14 |
| 118 | purpose | the archivist | The archivist reboxed the old records to save shelf space. | purity (a sacred scroll) | new | 14 |
| 119 | purpose | the camper | The camper pitched the tent in a new spot to get out of the wind. | purity (a ring of standing stones) | new | 14 |
| 120 | purpose | the beekeeper | The beekeeper moved the hives to a new field to get more sun. | purity (a sacred hilltop) | new | 14 |
| 121 | purpose | the woodworker | The woodworker built new pews for the chapel to replace the broken ones. | purity (a sacred cross; replaces rejected 117, 2026-10-22) | new | 14 |

Pairs planned: harm 36, fairness 26, loyalty 26, authority 26, purity 26 (6 shared + 20 purpose). Total 140 pairs = 280 items. Targets: ≥ 26 each for fairness, loyalty, authority and purity, and 30–40 harm.

### Drafting notes, batches 08–14

- Every item is built from one template: background, then the roster's
  action sentence word for word (C4), then the A3 indifference clause, then
  "<Role> knew <subject> would <side effect>.". All 280 are `source = new`.
- Authority pairs all use the §4.7 example form: "<body> decides ..." as
  background, "overturn the <body>'s decision" against "carry out the
  <body>'s decision exactly". Loyalty pairs all use the §4.6 form:
  "<mechanism>, siding with the rival ..." against "<mechanism>, standing
  with the <group>". This keeps each foundation's contrast uniform across
  storylines, at the cost of repetitive wording.
- Harm pairs name the person or animal by role (§4.4) and keep the effect
  bodily or emotional. Fairness pairs split non-essential goods (turns,
  seats, stage time, lanes) and avoid food, pay and housing (§4.5 Out).
- Purity good versions mostly "leave the sacred X untouched" or keep a
  distance from it, as in the §4.8 example. Some may read as "no
  violation" rather than active honoring (§5 mistake 1); the valence
  screen will show it.

### Re-screen fixes, 2026-10-22

- Purity, 13 storylines (3, 6, 101, 103, 105–107, 109, 112, 114, 116, 117,
  119): both versions now end "…, desecrating it" or a concrete honoring act
  "…, honoring it". "Leave it untouched" read as neutral (purity 0–5).
- Fairness, all 26: the background states a standing unfairness, identical
  in both versions ("…had agreed to share X equally, but the same few had
  been getting most of it"). The bad version cheats the others out of their
  share, and the good version puts it right "at last, treating every X
  fairly". Chores (5, 14, 17) cheat the few doing the work; 11 and 20 are
  lotteries. Storyline 17's chore is now "the cooking for the potluck"
  (was "the dishes to bring"). This went with the balanced `fnd_fairness`
  question (DESIGN amendment 2026-10-22).
- Shared storylines whose harm pair failed: 2, 3, 6, 24, 34 (decision A:
  kept, outside the primary pooled contrast).

### Review of the survivors, 2026-10-22 (MM)

Sheets 15–19: 452 items, 319 approved, 131 revise, 2 rejected (purity
117). MM's summary of the patterns is in
`../stimulus_reviews_completed_2026-10-22/review_summary.txt`. Rulings
from the same session (sheet 20, `20_mm_rulings_decisions.csv`):
- **B8 role changes approved as decision-O exceptions:** storylines 2
  (CEO → board chair), 18 (Defense Secretary → surgeon general), 34
  (terrorist → activist), 36 (CEO → product designer; effect tablet →
  music player, the item-72 fix). The paper names them.
- **Adapted moral pairs 22, 26, 28 dropped** (decision G). They're
  implausible under decisions B2 and K: inducing labor to reduce pregnancy
  pains, a school administrator's health plan for army recruits, a fence
  to relieve anger. Their verbatim versions still run.
- **Fairness and storyline 8:** the shared action gets rewritten so it can
  plausibly allocate turns or time (or, for 8, shorten the route), and
  every arm of those storylines is redrafted to follow from it (C4),
  re-screened and re-reviewed.

Pilot items (`stimuli/pilot_run/`) were drawn from the approved set the
same day, before the revisions. The pilot tests the protocol, not these
items.

### Revisions after the survivor review, 2026-10-22

Drafted (`claude-opus-5-5`) from MM's notes, re-screened (only the changed
items, `--rescreen-changed`), and put on two sheets:

| batch | file | content | items |
|---|---|---|---|
| 21_nm_revised | nonmoral.csv | revised prudential and procedural pairs that passed the re-screen | 54 |
| 22_mf_revised | foundations.csv | the 14 rebuilt storylines, item fixes, purpose 109/111/113/114/116/120, new 121 | 132 |

Five revised foundations pairs failed the first re-screen and passed after
one more fix (20 harm, 24 harm, 32 loyalty, 9 authority, 120 purity). The
adapted moral drafts that failed the first screen stay draft and out of the
run (decision G).

Round 4 (MM's sheet 22 notes on loyalty and purity): 13 pairs redrafted, 11
pass the re-screen; their 18 revised items are on sheet `23_mf_round4`. Loyalty 18
and 32 failed valence (helping the rival reads as kind) and stay draft, out
of the run. The other sheet 21–22 revise items (nonmoral, harm 10 and 24)
weren't redrafted: their arms are above target without them.
