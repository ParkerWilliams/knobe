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

Drafted 2026-10-22, for the researcher's review (Task 9 gate). Rules
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
| 10 | Kate / Jared | the relative | name → role; niece and nephew are gendered (R3). Reads awkwardly with "uncle" (see open points) | no |
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
| 27 | Philip / Alice | the adult child | name → role; son and daughter are gendered (R3). Reads awkwardly with "mother" (see open points) | no |
| 28 | Diane / Josh | the dog owner | name → role; the bad version's animal is a puppy | no |
| 29 | the cop / the cop | the cop | kept | no |
| 30 | Flora / Ernest | the policyholder | name → role; faked death and life insurance. Fits a prudential story | no |
| 31 | Norman / Angela | the resident | name → role; protests at a church. "The protester" is taken by storyline 24 (D3) | no |
| 32 | Jo / Kurt | the author | name → role; writes a book | no |
| 33 | Keith / Melissa | the newlywed | name → role; marriage. Groom and bride are gendered (R3) | no |
| 34 | the activist / the terrorist | the activist | kept (bad version's role) | yes: the action is a bomb threat; "activist" can also carry praise |
| 35 | the financial officer / the treasurer | the financial officer | kept | no |
| 36 | the CEO / the CEO | the product designer | replaced (R3: CEO); revises a device | no |
| 37 | the cult leader / the cult leader | the cult leader | R3 exception (the role is the story) | yes |
| 38 | the candidate / the candidate | the candidate | kept | yes: running for President |
| 39 | the farmer / the farmer | the farmer | kept | no |
| 40 | the doctor / the doctor | the doctor | kept | no |

Loaded storylines for the decision P sensitivity fit: 5, 7, 18, 34, 37, 38.

### Open points for the researcher

1. **Storylines 10 and 27 (kin stories).** No gender-neutral kin role reads
   well: "The relative placed the relative's uncle in a nursing home".
   Alternative: restructure so the agent's role is general ("the relative")
   and the kin noun names the other person ("an uncle"). The pronoun
   changes in storyline 10 need `nonmoral_log.csv` rows either way (lint).
2. **Storyline 7.** "The bomber pilot" breaks the bad-version rule (above).
   The alternative is "the airplane bomber", as written.
3. **Storyline 34.** Decision O gives the bad version's "the activist",
   so the good version reads "The activist bombed the jail". The
   alternative, "the terrorist", is the role decision O lists as a story
   role, but it is the good version's.
4. **Storyline 33.** "Married his wife" keeps the kin noun under decision L
   ("The newlywed married the newlywed's wife"). This is Task 10 wording, but
   it bears on whether "the newlywed" works.
5. **Shared head nouns.** "The club owner", "the store owner" and "the dog
   owner" are distinct strings (D3 passes) but share a head noun. Say if
   you want distinct heads.
6. **Storyline 22 vs 40.** "The pregnant patient" is storyline 22's agent,
   while in storyline 40 the patient is the doctor's patient (not the
   agent). The strings differ, but both use "patient".

## Batches

| batch | file | storylines / arms | items | drafting model | drafted | sheet commit | decisions applied |
|---|---|---|---|---|---|---|---|

## Foundations scaffold roster (Task 14)
