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

## Foundations scaffold roster (Task 14)
