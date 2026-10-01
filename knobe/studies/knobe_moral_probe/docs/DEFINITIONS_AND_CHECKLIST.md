# knobe_moral_probe: item definitions and review checklist

**Status: DRAFT for researcher review (2026-10-01), revision 2.** This is
step 1 of the authoring process (DESIGN.md §3.4). No items are drafted
until it is approved. Revision 2 applies the two 2026-10-01 amendments at
the top of DESIGN.md (role-noun rule; Ngo goals and verbatim set). Anything
marked **(proposed)** is not stated in DESIGN.md; accept, change or strike
it during review. Open decisions are collected in §7.

## 1. Purpose and how to use it

- **Authors** (Claude, step 2) write every item to §2–§4.
- **The reviewer** (you, step 2) checks every item against §6 and sets
  `review_status` to `approved` or `rejected`.
- **Screening** (§4 of DESIGN.md) then checks valence and domain or
  foundation ratings. The definitions here match the one-line definitions
  the reviewer model sees (`kmp/protocol.py`), so an item written to them
  should pass the screen for the right reason.
- The checklist covers what screening does not: template conformance,
  pairing, magnitude, role nouns and pronouns, field consistency.

## 2. Rules for every pair (DESIGN.md §3.1)

1. Same agent, same main action, same unrelated goal in both versions.
2. The agent is a role noun, never a personal name. No gendered pronouns
   (2026-10-01 amendment).
3. An indifference clause: "[Agent] did not care at all about the effect
   this would have on X."
4. A foreseen side effect. The questions are about the side effect, never
   the main action.
5. The bad and good versions differ only in the side effect's direction.
   The good version mirrors the bad one at similar magnitude. Not screened;
   the subject models' significance ratings show how well it held.
6. Plain, concrete wording. No graphic content beyond what the side effect
   requires.
7. Each good version upholds the same foundation its bad version violates
   (§3.3; applied to nonmoral domains too, **proposed**).

### 2.1 Role nouns (2026-10-01 amendment)

- One role noun per storyline, shared by both versions and every arm. The
  role is held constant within a storyline, so it cannot confound sign or
  arm.
- Plain, everyday roles: "the manager", "the contractor", "the clerk", "the
  farmer". Avoid loaded roles that carry their own blame or praise ("the
  CEO", "the politician", "the volunteer") **(proposed list)**.
- Gender-neutral roles: "the chair", not "the chairman"; "the council
  member", not "the councilwoman" **(proposed)**.
- No pronouns for the agent. Repeat the role noun, or restructure ("the
  plan" for "her plan"). Avoid singular "they" where it reads awkwardly.
- Other people in the story are also named by role ("the roommate", "the
  neighbor"), not by name, and take no gendered pronouns **(proposed for
  new items; for Ngo pairs see §7, decision L)**.

## 3. Templates and item fields

### 3.1 Nonmoral: Ngo's 3-clause template (§3.2)

```
The [role] [main action] to [goal].
The [role] did not care at all about the effect this would have on [X].
The [role] knew [the action] would [side effect].
```

- Clause 1: action and unrelated goal.
- Clause 2: indifference. X names what is affected, neutrally ("the
  clerk's savings", "the office's filing convention"), never the outcome
  ("the clerk's losses").
- Clause 3: the foreseen side effect. This is the only clause that differs
  between bad and good.
- Ngo's question line ("Did Bill intentionally ...?") is not part of
  `scenario`; the question comes from `protocol.py`.

### 3.2 Foundations: 4-clause template (§3.3)

```
[Background norm.]
The [role] [main action] to [goal].
The [role] did not care at all about the effect this would have on [X].
The [role] knew [the action] would [violate / uphold the norm].
```

- The four clauses: background norm, unrelated goal, indifference, foreseen
  side effect. Harm controls use the same template, so clause count is not
  a confound (§3.3).
- The background clause states the norm neutrally, so the side effect can
  break it (bad) or uphold it (good). It is identical in both versions
  **(proposed; follows rule 5)**.
- For harm controls the "norm" is a background fact that sets up who could
  be hurt or helped ("One older member, who has a bad knee, gardens in the
  plot by the gate.") **(proposed; see §7, decision D)**.

### 3.3 Shared scaffolds (§3.3, pilot option B)

A scaffold is one storyline's role noun, main action and goal. It is
written once and reused verbatim across its versions:

| clause | harm pair | foundation pair(s) |
|---|---|---|
| background | harm-relevant fact | that foundation's norm |
| action + goal | scaffold, verbatim | scaffold, verbatim |
| indifference | X = the person or animal at stake | X = the norm's object |
| side effect | hurt / help | violate / uphold |

- Every shared scaffold has one harm pair and one or more foundation pairs.
- Purity gets purpose-written storylines (no harm pair), flagged as such.
  The schema has no field for this yet; see §7, decision A.
- Scaffold action and goal must be harm-neutral. If the main action already
  hurts someone (bombing a factory, cutting a shelter's budget), every
  version inherits the harm (pilot: authority-17, fairness-17).

### 3.4 Item fields (`kmp/items.py`)

| field | rule |
|---|---|
| `item_id` | `kmp-{code}-{storyline:03d}-{arm}-{sign}`, code `nm`, `mf` or `nv`; generated, never typed |
| `experiment` | `nonmoral`, `foundations` or `ngo_verbatim`; one experiment per file |
| `storyline_id` | nonmoral and ngo_verbatim: Ngo pair N (source items 2N−1, 2N), 1–40. Foundations: one ID per scaffold |
| `arm` | nonmoral: moral, prudential, procedural. Foundations: harm, fairness, loyalty, authority, purity. ngo_verbatim: moral |
| `sign` | `bad` or `good` |
| `agent` | the role noun as written mid-sentence: "the manager". Same string in both versions and every arm of the storyline |
| `effect` | the side effect as a bare verb phrase, lower case, no final punctuation |
| `scenario` | the 3 or 4 clauses, one space between sentences, no question line |
| `source` | `ngo` (Ngo's pairs, adapted or verbatim), `pilot` (pilot variant reused as a draft), `new` |
| `review_status` | `draft` until reviewed |

Question templates fill in `agent` as is, so they read "Did the manager
intentionally ...?". In the scenario the role noun is capitalised at the
start of a sentence ("The manager knew ...").

`effect` must read correctly in every frame that uses it: "Did {agent}
intentionally {effect}?", "How intentionally did {agent} {effect}, ...?"
and "The action had this side effect: it would {effect}." Write "drain the
clerk's savings", not "drained the savings" or "the loss of savings". For
side effects on the agent, the role noun repeats ("Did the clerk
intentionally drain the clerk's savings?"); see §7, decision J.

### 3.5 Ngo's pairs: adapted and verbatim (2026-10-01 amendments)

- **Adapted** (experiment `nonmoral`, arm `moral`, `source = ngo`). Only
  three things change: the agent's names become one shared role noun;
  pronouns become that noun or are restructured; where the two versions'
  goals differ, the goal is aligned. Nothing else changes. The paper
  discloses this as an adaptation.
- Which goal is kept when aligning: the bad version's (resolved 2026-10-01).
- **Verbatim** (experiment `ngo_verbatim`, IDs `kmp-nv-…`, arm `moral`,
  `source = ngo`). Ngo's 80 items word for word, with each version's own
  `agent` ("Bill", "Robyn"). Exempt from the role-noun and same-agent
  checks and nothing else. It is a consistency check only; the main
  analyses use the adapted items.

## 4. Definitions

The first line of each matches the screening definition in `protocol.py`.
"In" and "Out" set the boundaries. Examples are in Ngo's register: short,
flat, one clause each. They illustrate; they are not items.

The foundations examples share one scaffold, S: "The coordinator
rearranged the community garden's plots to shorten the watering route."

### 4.1 Moral (nonmoral experiment, Ngo's pairs)

**Definition.** The side effect affects other people's welfare or rights.

- **In:** Ngo's 40 pairs, adapted (§3.5). This includes Ngo's pairs about
  animals, the environment, a 1000-year-old tree and a monument, even
  though they stretch "other people".
- **Out:** no new moral items are written.
- **Example, adapted** (Ngo items 37 and 38; goals already match):
  - Bad: "The manager enacted the plan to increase earnings. The manager
    did not care at all about the effect the plan would have on the
    manager's employees. The manager knew the plan would make employees
    unhappy." (effect: "make employees unhappy")
  - Good: "... The manager knew the plan would make employees happy."
    (effect: "make employees happy")
- **The same pair in the `ngo_verbatim` set** (as published):
  - Bad: "Carolyn enacted the plan to increase earnings. Carolyn did not
    care at all about the effect the plan would have on her employees.
    Carolyn knew her plan would make employees unhappy."
  - Good: "Christopher enacted the plan to increase earnings. Christopher
    did not care at all about the effect the plan would have on his
    employees. Christopher knew his plan would make employees happy."
- **Goal alignment** (Ngo items 5 and 6): "to buy a house" (bad) and "to buy
  a car" (good) both become "to buy a house".

### 4.2 Prudential

**Definition.** The side effect affects only the agent's own interests
(health, money, reputation, safety). No one else is affected (§3.2).

- **In:** the agent's own savings, credit score, fitness, sleep, grades,
  career prospects, own property.
- **Out, moral:** anything that predictably reaches someone else. If the
  agent's loss would fall on a spouse, children or dependants (household
  savings, the family home, the agent's ability to care for someone), it
  is moral. Pick an interest that is plainly the agent's alone.
- **Out, moral:** an action that is itself wrongdoing (filing a false
  report, breaking ethics rules, speeding). The reviewer reads the
  wrongdoing, not the self-harm (pilot pairs 5, 29, 30).
- **Out:** a side effect that is the goal, or a means to it (pilot pair 2:
  "to increase her bonus" with "boost her own retirement contributions").
- **Example:**
  - Bad: "The clerk moved to a new apartment to be closer to the gym. The
    clerk did not care at all about the effect this would have on the
    clerk's savings. The clerk knew the move would drain the clerk's
    savings." (effect: "drain the clerk's savings")
  - Good: "... The clerk knew the move would grow the clerk's savings."
    (effect: "grow the clerk's savings")

### 4.3 Procedural

**Definition.** The side effect concerns an arbitrary convention or rule (a
dress code, a seating chart, a filing convention). No one's welfare is at
stake (§3.2).

- **In:** conventions that exist only to coordinate or look uniform: a
  color scheme, a file-naming pattern, the order of items on an agenda.
- **Out, moral:** conventions whose breach costs others something (a
  shared thermostat setting, a queue others are waiting in). Pilot pairs
  23 and 27 failed this way.
- **Out, authority:** a rule framed as an order from someone with standing
  ("the manager's rule"), or described as a "tradition". These read as
  respect for authority, which the moral domain question may pick up.
  Call it a "convention", "format" or "scheme".
- **Out, prudential:** a breach that gets the agent in trouble. The side
  effect is on the convention, not on the agent.
- **Example:**
  - Bad: "The engineer wore a new jacket to the office party to stay warm.
    The engineer did not care at all about the effect this would have on
    the party's dress code. The engineer knew the jacket would break the
    party's dress code." (effect: "break the party's dress code")
  - Good: "... The engineer knew the jacket would fit the party's dress
    code exactly." (effect: "fit the party's dress code exactly")

### 4.4 Harm (control)

**Definition.** Physical or emotional harm to someone, or care for them
(§3.3).

- **In:** injury, pain, illness, distress, fear; and their mirror images:
  protecting, easing pain, comforting.
- **Out:** harm to things with no one behind them (a wetland, a building)
  unless the text names who is hurt. The pilot's "restore the wetland"
  style good versions often failed to read as harm. Name the person or
  animal, by role.
- **Out:** money or property loss alone. That drifts to fairness or reads
  as weak harm. Keep it bodily or emotional.
- **Example** (scaffold S):
  - Background: "One older member, who has a bad knee, gardens in the plot
    by the gate." Indifference X: "the older member".
  - Bad: "The coordinator knew the new layout would force the older member
    up a steep path that hurts the bad knee." (effect: "hurt the older
    member's knee")
  - Good: "The coordinator knew the new layout would give the older member
    a flat path that eases the knee pain." (effect: "ease the older
    member's knee pain")

### 4.5 Fairness

**Definition.** Unequal or unjust treatment, cheating, or reneging, with no
one's welfare damaged (§3.3).

- **In:** unequal shares of non-essential goods (turn order, speaking time,
  votes, plot size in a hobby garden), skipping an agreed lottery, breaking
  an agreed split.
- **Out, harm:** unequal shares of things welfare depends on (food, pay,
  medical care, housing), or exclusion that humiliates. Pilot items that
  shut people out of honors "they had earned" read as harm (fairness-18,
  fairness-35).
- **Out, loyalty:** favoring one's own friends, team or family. That reads
  as in-group loyalty, possibly as a good thing. Make the beneficiaries
  arbitrary ("whoever signed up first").
- **Out, authority:** bypassing a body that has the right to decide.
- **Example** (scaffold S):
  - Background: "The members had agreed that plots would be shared out
    equally." Indifference X: "the members' agreement".
  - Bad: "The coordinator knew the new layout would give some members twice
    as much space as others." (effect: "give some members twice as much
    space as others")
  - Good: "The coordinator knew the new layout would give every member
    exactly the same space." (effect: "give every member exactly the same
    space")

### 4.6 Loyalty

**Definition.** Betraying, or standing by, one's group, team, family or
ally (§3.3).

- **In:** siding with a rival, switching allegiance, publicly disowning the
  group; and standing with the group against a rival.
- **Out, fairness:** breaking a specific promise, pact or deal. That is
  reneging, which is fairness by §3.3's definition and by the reviewer's
  wording ("going back on a deal"). Pilot loyalty items built on a "pact"
  or "promise" mix the two. Loyalty is about allegiance, not contracts.
- **Out, harm:** betrayal that leaves the group worse off (lost funding,
  lost jobs, hurt feelings named in the text).
- **Example** (scaffold S):
  - Background: "The coordinator's garden club has a long rivalry with a
    club across town over whose garden is finest." Indifference X: "the
    garden club".
  - Bad: "The coordinator knew the new layout would copy the rival club's
    design, taking the rival club's side." (effect: "take the rival club's
    side")
  - Good: "The coordinator knew the new layout would keep the garden club's
    own design, standing with the garden club." (effect: "stand with the
    garden club")

### 4.7 Authority

**Definition.** Undermining, or upholding, a legitimate authority,
hierarchy or tradition (§3.3).

- **In:** acting against, or carrying out, a decision by a body with the
  standing to make it (a board, an elected committee, a commission);
  disregarding or honoring a respected tradition.
- **Out, procedural:** an arbitrary convention with no one's standing
  behind it. In the foundations experiment that is a weak authority item.
- **Out, harm:** defiance that hurts people (an unauthorized budget cut at
  a shelter, prescribing an unapproved drug). Pilot authority-17 and
  authority-40 failed this way.
- **Out:** good versions where the agent's own action is the act of
  compliance ("knew filing for every permit would uphold the rules"). The
  upholding is then part of the action, not a side effect, and reads as
  routine (pilot weak-signal failures).
- **Example** (scaffold S):
  - Background: "The garden's elected board decides how the plots are laid
    out." Indifference X: "the board's decision".
  - Bad: "The coordinator knew the new layout would overturn the board's
    decision." (effect: "overturn the board's decision")
  - Good: "The coordinator knew the new layout would carry out the board's
    decision exactly." (effect: "carry out the board's decision")

### 4.8 Purity

**Definition.** Violating, or honoring, a taboo or something treated as
sacred, with no harm (§3.3).

- **In:** desecrating or honoring a sacred object, place or rite; breaking
  or keeping a food or contact taboo.
- **Out, disgust without violation:** gross but not taboo (a bad smell,
  spilled garbage). Something must be treated as sacred or forbidden.
- **Out, harm:** distress caused to worshippers or mourners, damage to the
  sacred object's owners, health risk. Do not name anyone's reaction.
- **Out, authority:** breaking a rule because a priest or council forbade
  it. Frame it as sacred in itself, not as an order.
- **Example** (purpose-written, no harm pair):
  - Background: "The stone at the top of the hill has been held sacred for
    centuries, and no one may step on it."
  - Action and goal: "The farmer cleared a new hillside path to shorten the
    walk to the fields." Indifference X: "the sacred stone".
  - Bad: "The farmer knew the new path would run straight over the sacred
    stone." (effect: "run the path over the sacred stone")
  - Good: "The farmer knew the new path would curve around the sacred stone
    and leave it untouched." (effect: "leave the sacred stone untouched")

## 5. Common mistakes (from the pilots)

Most pilot failures are covered by a definition's "Out" list (§4) or a
checklist item (§6). Three are easy to miss, so they are restated here.
Pilot failures were under the old one-sided screen, so these are the
authors' reading of the failed texts, not the reviewer's.

1. **Good version that is only "no violation".** "Kept the seating chart
   the same", "would respect the board's authority". It reads as neutral
   and is likely to miss the two-sided valence screen (good ≥ 7). The good
   side effect should actively uphold something (B5).
2. **Different backgrounds in bad and good.** Pilot fairness items set up an
   equal process for the bad version and a prior inequity for the good
   one. That is a difference beyond direction (B2).
3. **Foundation bleed.** Pacts and promises in loyalty items (fairness);
   favoritism in fairness items (loyalty); "tradition" in procedural items
   (authority) (A6, C5).

## 6. Review checklist

Each item is a yes/no question. Every "no" is a rejection or a fix. Checks
marked (code) are also run by `kmp.items.design_problems`; the rest are
review-only.

Which checks apply to Ngo's pairs:
- **Adapted Ngo pairs** (`nonmoral`, `moral`, `source = ngo`): A1, A9–A10,
  A13, R1–R4, B1, B8 and D. Not A2–A8 or B2–B7: Ngo's wording is kept
  ("the effect the plan would have"), and many pairs differ in more than
  the side effect (§7, decision K).
- **`ngo_verbatim` items:** A1, A10, A13, B9 and D. Exempt from R1–R4
  and B1, and from the matching code checks.

### A. Per item

- **A1.** `scenario` has exactly the template's clauses, in order (3 for
  nonmoral and ngo_verbatim, 4 for foundations), and no question line.
- **A2.** Clause 1 (nonmoral) or 2 (foundations) states a main action and
  an unrelated goal with "to ...".
- **A3.** The indifference clause reads exactly "The [role] did not care at
  all about the effect this would have on [X]." X is neutral, not the
  outcome.
- **A4.** The last clause states the side effect as foreseen ("knew ...
  would ..."), and the side effect is the last thing in the scenario
  **(proposed: so that "for this" in the blame and praise wordings points
  to it)**.
- **A5.** The side effect is not the goal and not a means to it.
- **A6.** The side effect fits the arm's definition (§4) and none of its
  "Out" cases.
- **A7.** Non-harm foundation items and prudential and procedural items
  name no damage to anyone's welfare (no injury, distress, loss of money
  or essentials), stated or strongly implied.
- **A8.** Foundations: the background clause states the norm (or, for
  harm, the fact) the side effect acts on, and says nothing about the
  outcome.
- **A9.** `agent` is the role noun as written mid-sentence ("the manager"),
  and the scenario uses that same noun for the agent throughout.
- **A10.** `effect` is a bare verb phrase that matches the side-effect
  clause in meaning, and reads correctly in "Did {agent} intentionally
  {effect}?" and "it would {effect}".
- **A11.** Plain words, short sentences, no jargon.
- **A12.** No graphic content beyond what the side effect requires.
- **A13.** `item_id`, `experiment`, `arm`, `sign` and `storyline_id` agree
  (the loader checks the ID; the reviewer checks the arm is right for the
  text). `source` is right.

### R. Role nouns, per item (2026-10-01 amendment)

- **R1.** No personal names anywhere in the item: agent or anyone else
  (review-only; code cannot detect names). For non-agent names in adapted
  Ngo pairs, see §7, decision L.
- **R2.** No gendered pronouns: he, she, him, her, his, hers, himself,
  herself (code).
- **R3.** The role noun is plain and not loaded: it carries no blame or
  praise of its own ("the CEO", "the politician" are out) and is
  gender-neutral ("the chair", not "the chairman").
- **R4.** No singular "they" for the agent where it reads awkwardly;
  repeat the role noun or restructure.

### B. Per pair (bad and good of one storyline and arm)

- **B1.** Same `agent` string in both versions (code).
- **B2.** Every clause except the side effect is word-for-word identical
  (background, action, goal, indifference with the same X).
- **B3.** The side effects differ only in direction: same affected party,
  same kind of outcome, opposite sign.
- **B4.** Similar magnitude: neither version is clearly bigger, longer
  lasting or reaching more people ("hurt the older member's knee" vs "ease
  the older member's knee pain", not vs "cure the older member").
- **B5.** The good version actively upholds or benefits; it is not just
  the absence of the bad outcome.
- **B6.** The good version upholds the same foundation (or domain) the bad
  version violates.
- **B7.** The two `effect` phrases are parallel in form ("drain the clerk's
  savings" / "grow the clerk's savings").
- **B8.** Adapted Ngo pair: compared with Ngo's original text, only names,
  pronouns, (where the two differed) the goal, and listed typo fixes have
  changed. The goal is the same in both versions. Nothing else differs
  from Ngo.
- **B9.** `ngo_verbatim` pair: both scenarios match Ngo's published text
  word for word, typos included.

### C. Per storyline

- **C1.** Nonmoral: storyline N's pairs (adapted moral, prudential,
  procedural) and its `ngo_verbatim` pair are numbered as Ngo pair N
  (items 2N−1, 2N).
- **C2.** The same role noun is used in both versions of every arm of the
  storyline (code checks within a pair only; across arms is review-only
  until a code check exists).
- **C3.** Nonmoral: the new pairs reuse the adapted Ngo pair's action and
  goal where plausible; otherwise the change is noted (§7, decision E).
- **C4.** Foundations, shared scaffold: one harm pair plus at least one
  foundation pair, all with the same role noun, action and goal, verbatim.
- **C5.** Foundations, shared scaffold: the action and goal are
  harm-neutral on their own.
- **C6.** Foundations: no two foundation pairs on one scaffold are near
  duplicates (a fairness and an authority version that both turn on the
  board's decision).
- **C7.** Purpose-written purity storylines are marked as such (mechanism
  per §7, decision A) and have no harm pair.

### D. Per file (before screening)

- **D1.** `kmp.items.load_items` loads the file and `design_problems`
  returns nothing (`ngo_verbatim`: nothing beyond its two exemptions).
- **D2.** Counts meet the drafting targets: nonmoral, a prudential and a
  procedural pair for all 40 storylines; ngo_verbatim, all 40 pairs;
  foundations, about 26 drafted storylines per foundation (20 target ×
  1.3) and 30–40 harm pairs (§3.3).
- **D3.** No role noun is reused across storylines within a file, so each
  storyline is easy to tell apart **(proposed)**.

## 7. Open decisions for the researcher

Recommendations are mine. None of these changes DESIGN.md until you decide.

**A. Marking purpose-written purity storylines.** §3.3 says they are
"flagged as such", but the item schema has no field for it, and nothing
enforces "shared scaffold ⇒ has a harm pair". A shared scaffold whose harm
pair fails screening also ends up without one.

- Option 1: new schema field `scaffold: shared | purpose` (foundations
  only). A design check requires a harm pair for `shared` at authoring.
  After screening and selection, the selection report lists `shared`
  storylines whose harm pair did not survive, rather than failing.
- Option 2: a reserved `storyline_id` range for purpose-written storylines
  (for example 901–999). No schema change, but the meaning lives in a
  convention.
- Option 3: no marker; analysis infers it from whether a harm pair exists.
  Loses the authoring intent and conflates it with screening losses.
- Analysis side, also to decide: whether storylines without a surviving
  harm pair enter the pooled harm-vs-non-harm contrast. With storyline as
  the cluster, they add non-harm data with no within-storyline harm
  comparison.
- **RESOLVED 2026-10-01: option 1 (recommendation accepted).** Checked at authoring and reported after
  selection. Primary pooled contrast on storylines with both a harm pair
  and a non-harm pair; a sensitivity analysis including the rest. Record
  this in the analysis plan.

**B. Ngo's pairs and "same agent". RESOLVED 2026-10-01.** Ngo's pairs are
minimally adapted to one shared role noun per storyline, with no gendered
pronouns, and meet the same-agent check. The verbatim originals are kept
as the separate `ngo_verbatim` set, exempt from the role-noun and
same-agent checks only (DESIGN.md amendments of 2026-10-01; §3.5 here).

**B2. Ngo's differing goals. RESOLVED 2026-10-01.** Where Ngo's two
versions have different goals ("buy a house" / "buy a car"), the adapted
pair uses one goal in both: the bad version's (§3.5).

**C. Ngo's typos.** Examples: item 10 "diverting the water for his town"
(the agent is a councilwoman); item 23 "would have rates of cancer"; item 40
"his new road" (the agent bought a trolley); item 53 "Philip" then
"Phillip"; item 17's question names "her neighbor" where the scenario says
"Susie-Ann". The list is not exhaustive. The adaptation removes the name
and pronoun ones (10, 53) as a side effect; the others remain.

- **RESOLVED 2026-10-01:** `ngo_verbatim` keeps every typo (it is word for word).
  The adapted Ngo pairs fix them, and each fix is listed in the stimuli
  file's notes. For `effect`, use Ngo's question phrase (with the role
  noun); where it disagrees with the scenario (item 17), decide case by
  case and log it.

**D. What "background norm" means for harm controls.** §3.3 gives every
foundations item a background norm, harm controls included, but harm has
no natural norm to state.

- **RESOLVED 2026-10-01 (recommendation accepted):** a neutral background fact that sets up who could be
  hurt or helped (§3.2 above). Do not state a moral rule ("one should not
  hurt others"), which would cue the answer.

**E. Which action and goal the nonmoral arms use.** The role noun is now
fixed per storyline (amendment). Still open: whether the prudential and
procedural pairs reuse the adapted Ngo pair's action and goal. Some
storylines (bombing, terrorism) have no plausible self-regarding or
procedural analogue; the pilot used fresh domains for those.

- **RESOLVED 2026-10-01 (recommendation accepted):** reuse the adapted Ngo action and goal where it reads
  naturally; otherwise keep the role noun, write a fresh action and goal in
  the same register, and note it.

**F. Two-sided valence vs "no one's welfare at stake".** The valence screen
asks how good or bad the side effect is "for those it affects" and needs
bad ≤ 3, good ≥ 7. Procedural, fairness and purity items are defined to
have no welfare effect. A flawless procedural item may rate near 5 and
fail; pushing it to pass invites the welfare stakes the definition rules
out.

- **RESOLVED 2026-10-01 (recommendation accepted):** author to the definitions, not to the valence
  threshold. If procedural or purity items fail valence in bulk, revisit
  the threshold against the real distribution, as §4 already allows, and
  record the change. Do not add welfare stakes to rescue them.

**G. Ngo moral pairs that fail screening.** All items are re-screened
(§3.2) and the originals are not rewritten, so a failing moral pair is
dropped. Its storyline then has nonmoral pairs but no moral pair.

- **RESOLVED 2026-10-01 (recommendation accepted):** drop it, list it by name in the selection report, and
  keep the storyline's passing nonmoral pairs. Handle the unbalanced
  storylines the same way as decision A in the analysis plan.

**H. Where foundations scaffolds come from.** DESIGN.md does not say
whether scaffolds reuse Ngo storylines (as the pilot did) or are new.

- **RESOLVED 2026-10-01 (recommendation accepted):** either is allowed. Prefer new scaffolds where Ngo's
  main action is harmful. Mark `source` honestly.

**I. Cross-foundation bleed is not screened.** The foundations pass rule
compares the intended foundation only with harm. A fairness item that also
rates high on authority passes.

- **RESOLVED 2026-10-01 (recommendation accepted):** keep it as a review check (A6, C6), not a screening
  rule, and report the full foundation profiles descriptively.

**J. Self-referring side effects repeat the role noun (new).** Without
pronouns, a prudential effect reads "Did the clerk intentionally drain the
clerk's savings?". It is clear but clumsy. Restructuring to an intransitive
phrase ("lose money") breaks the frame "it would {effect}", where "it" is
the action.

- **RESOLVED 2026-10-01 (recommendation accepted):** accept the repetition; it is grammatical and
  unambiguous. Alternatively, `protocol.py` could gain a reflexive form,
  but that is a protocol change, not an authoring one.

**K. Adapted Ngo pairs still differ in more than the side effect (new).**
The amendment says the goal alignment makes every adapted pair meet §3.1
"in full". But many Ngo pairs also differ in the action or its object
(gadget / invention; kiosk / new store; hunted / trapped; built a road /
bought a trolley; smacked the puppy / installed a fence, items 55–56) or in
the affected party (babies / toddlers; uncle / aunt; tennis player /
golfer). "Nothing else changes" leaves these in place, so those pairs meet
§3.1's agent and goal clauses but not "same main action" or "differ only in
direction".

- **RESOLVED 2026-10-01: option (1).** Adapted pairs equalise agent and
  goal only. Remaining differences in action, object or affected party
  stay, and the paper names them. B8 checks that nothing beyond names,
  pronouns, goal and listed typo fixes changed. (DESIGN.md's "in full" wording was corrected
  in commit 0bcc6ad.)

**L. Other people's names and gendered nouns in Ngo pairs (new).** Ngo
names non-agents (Susie-Ann / Billy-Bob, items 17–18; Curtis / Jackie,
items 29–30) and uses gendered relatives (uncle / aunt, mother). Gendered
pronouns referring to them ("make her extremely happy", item 20) fail the
code check, so they must change. The amendment covers the agent's names
and pronouns only.

- **RESOLVED 2026-10-01 (recommended default, not objected to):** replace
  non-agent names with roles ("the neighbor", "the roommate") and their
  pronouns with that role, as part of the name-and-pronoun adaptation.
  Gendered kinship nouns (uncle, aunt, mother) stay, since changing them
  changes the story.
