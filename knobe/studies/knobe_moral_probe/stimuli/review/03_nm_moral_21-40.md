# Review sheet: 03_nm_moral_21-40

Items: `stimuli/nonmoral.csv`, 40 draft items. Checklist: `docs/DEFINITIONS_AND_CHECKLIST.md` section 6.

Record one decision per item in `stimuli/review/03_nm_moral_21-40_decisions.csv`: `approved`, `rejected` or `revise`, your initials as reviewer, the date (YYYY-MM-DD), and a note for every rejected or revise row naming the failed check (e.g. "B4: good version is bigger"). Then run `../../.venv/bin/python -m tools.review apply --items stimuli/nonmoral.csv --decisions stimuli/review/03_nm_moral_21-40_decisions.csv` yourself.

Automated checks (design_problems and tools.lint_stimuli) were clean when this sheet was made.

## Storyline 21: the hunter (nonmoral; storyline checks C1 C2 C3)

### moral (source ngo; checks A1 A9 A10 A13 R1 R2 R3 R4 B1 B8)

**bad** `kmp-nm-021-moral-bad`

> The hunter hunted animals to earn a living. The hunter did not care at all about the effect this would have on endangered reindeer. The hunter knew the hunting would cause the reindeer to become extinct.

- agent: `the hunter`
- effect: `cause the reindeer to become extinct`
- Ngo's original: Jerry hunted animals to earn a living. Jerry did not care at all about the effect this would have on endangered reindeer. Jerry knew his hunting would cause the reindeer to become extinct.
- Ngo's effect: `cause the reindeer to become extinct`

**good** `kmp-nm-021-moral-good`

> The hunter trapped animals to earn a living. The hunter did not care at all about the effect this would have on endangered monkeys. The hunter knew the trapping would save the monkeys from their predators.

- agent: `the hunter`
- effect: `save the monkeys from their predators`
- Ngo's original: Linda trapped animals to do research. Linda did not care at all about the effect this would have on endangered monkeys. Linda knew her trapping would save the monkeys from their predators.
- Ngo's effect: `save the monkeys from their predators`
- log (goal, scenario): 'to do research' -> 'to earn a living'. bad version's goal (B2)

## Storyline 22: the pregnant patient (nonmoral; storyline checks C1 C2 C3)

### moral (source ngo; checks A1 A9 A10 A13 R1 R2 R3 R4 B1 B8)

**bad** `kmp-nm-022-moral-bad`

> The pregnant patient decided to induce labor to reduce the pregnancy pains. The pregnant patient did not care at all about the effect this would have on the baby's health. The pregnant patient knew inducing labor would be bad for the baby's health.

- agent: `the pregnant patient`
- effect: `worsen the baby's health`
- Ngo's original: Irene decided to induce labor to reduce her pregnancy pains. Irene did not care at all about the effect this would have on her baby's health. Irene knew inducing labor would be bad for her baby's health.
- Ngo's effect: `worsen her baby's health`

**good** `kmp-nm-022-moral-good`

> The pregnant patient decided to induce labor to reduce the pregnancy pains. The pregnant patient did not care at all about the effect this would have on the baby's health. The pregnant patient knew inducing labor would improve the baby's health.

- agent: `the pregnant patient`
- effect: `improve the health for the baby`
- Ngo's original: Holly decided to induce labor to get her pregnancy over with. Holly did not care at all about the effect this would have on her baby's health. Holly knew inducing labor would improve her baby's health.
- Ngo's effect: `improve the health for her baby`
- log (goal, scenario): 'to get her pregnancy over with' -> 'to reduce the pregnancy pains'. bad version's goal (B2)

## Storyline 23: the spectator (nonmoral; storyline checks C1 C2 C3)

### moral (source ngo; checks A1 A9 A10 A13 R1 R2 R3 R4 B1 B8)

**bad** `kmp-nm-023-moral-bad`

> The spectator screams during a tennis match to express excitement. The spectator did not care at all about the effect this would have on the tennis player. The spectator knew the yelling would cause the tennis player to lose.

- agent: `the spectator`
- effect: `cause the tennis player to lose`
- Ngo's original: Eugene screams during a tennis match to express his excitement. Eugene did not care at all about the effect this would have on the tennis player. Eugene knew his yelling would cause the tennis player to lose.
- Ngo's effect: `cause the tennis player to lose`

**good** `kmp-nm-023-moral-good`

> The spectator yells out during a golf tournament to express excitement. The spectator did not care at all about the effect the yelling would have on the golfer. The spectator knew the yelling would cause the golfer to win.

- agent: `the spectator`
- effect: `cause the golfer to win`
- Ngo's original: Margaret yells out during a golf tournament to express her excitement. Margaret did not care at all about the effect the yelling would have on the golfer. Margaret knew her yelling would cause golfer to win.
- Ngo's effect: `cause the golfer to win`
- log (typo, scenario): 'cause golfer to win' -> 'cause the golfer to win'. missing article (decision C, item 46)

## Storyline 24: the protester (nonmoral; storyline checks C1 C2 C3)

### moral (source ngo; checks A1 A9 A10 A13 R1 R2 R3 R4 B1 B8)

**bad** `kmp-nm-024-moral-bad`

> The protester protests in support of political prisoners to get on TV. The protester did not care at all about the effect the protests would have on the prisoners. The protester knew the protests would cause the execution of the political prisoners.

- agent: `the protester`
- effect: `cause the execution of the political prisoners`
- Ngo's original: Rebecca protests in support of political prisoners to get on TV. Rebecca did not care at all about the effect her protests would have on the prisoners. Rebecca knew her protests would cause the execution of the political prisoners.
- Ngo's effect: `cause the execution of the political prisoners`
- capitalised words (R1: names?): TV

**good** `kmp-nm-024-moral-good`

> The protester protests in support of the death row inmate to get on TV. The protester did not care at all about the effect this would have on the death row inmate. The protester knew the protests would cause the release of the death row inmate.

- agent: `the protester`
- effect: `cause the release of the death row inmate`
- Ngo's original: Sean protests in support of the death row inmate to get onto newspapers. Sean did not care at all about the effect this would have on the death row inmate. Sean knew his protests would cause the release of the death row inmate.
- Ngo's effect: `cause the release of the death row inmate`
- log (goal, scenario): 'to get onto newspapers' -> 'to get on TV'. bad version's goal (B2)
- capitalised words (R1: names?): TV

## Storyline 25: the blogger (nonmoral; storyline checks C1 C2 C3)

### moral (source ngo; checks A1 A9 A10 A13 R1 R2 R3 R4 B1 B8)

**bad** `kmp-nm-025-moral-bad`

> The blogger released the documents to gain publicity. The blogger did not care at all about the effect this would have on the friend's reputation. The blogger knew the documents would ruin the friend's reputation.

- agent: `the blogger`
- effect: `ruin the friend's reputation`
- Ngo's original: Curtis released the documents to gain publicity. Curtis did not care at all about the effect this would have on his friend's reputation. Curtis knew the documents would ruin his friend's reputation.
- Ngo's effect: `ruin his friend's reputation`

**good** `kmp-nm-025-moral-good`

> The blogger released the photos to gain publicity. The blogger did not care at all about the effect this would have on the boss's reputation. The blogger knew the photos would redeem the boss's reputation.

- agent: `the blogger`
- effect: `redeem the boss's reputation`
- Ngo's original: Lori released the photos to gain news coverage. Lori did not care at all about the effect this would have on her boss’s reputation. Lori knew the photos would redeem her boss’s reputation.
- Ngo's effect: `redeem her boss’s reputation`
- log (goal, scenario): 'to gain news coverage' -> 'to gain publicity'. bad version's goal (B2)

## Storyline 26: the school administrator (nonmoral; storyline checks C1 C2 C3)

### moral (source ngo; checks A1 A9 A10 A13 R1 R2 R3 R4 B1 B8)

**bad** `kmp-nm-026-moral-bad`

> The school administrator enacted the new lunch plan to cut costs. The school administrator did not care at all about the effect this would have on the health of school children. The school administrator knew the new lunch plan would harm the health of school children.

- agent: `the school administrator`
- effect: `harm the health of the school children`
- Ngo's original: Clara enacted the new lunch plan to cut costs. Clara did not care at all about the effect this would have on the health of school children. Clara knew her new lunch plan would harm the health of school children.
- Ngo's effect: `harm the health of the school children`

**good** `kmp-nm-026-moral-good`

> The school administrator enacted the health plan to cut costs. The school administrator did not care at all about the effect this would have on the health of army recruits. The school administrator knew the new plan would improve the health of army recruits.

- agent: `the school administrator`
- effect: `improve the health of army recruits`
- Ngo's original: Martin enacted the health plan to cut costs. Martin did not care at all about the effect this would have on the health of army recruits. Martin knew his new plan would improve the health of army recruits.
- Ngo's effect: `improve the health of army recruits`

## Storyline 27: the adult child (nonmoral; storyline checks C1 C2 C3)

### moral (source ngo; checks A1 A9 A10 A13 R1 R2 R3 R4 B1 B8)

**bad** `kmp-nm-027-moral-bad`

> The adult child told the mother the adult child's views to make a point. The adult child did not care at all about the effect this would have on the mother. The adult child knew the views would devastate the mother.

- agent: `the adult child`
- effect: `devastate the mother`
- Ngo's original: Philip told his mother his views to make a point. Phillip did not care at all about the effect this would have on his mother. Phillip knew his views would devastate his mother.
- Ngo's effect: `devastate his mother`
- log (typo, scenario): 'Phillip' -> 'The adult child'. Ngo spells the agent Philip and Phillip (decision C, item 53)

**good** `kmp-nm-027-moral-good`

> The adult child told the mother the adult child's opinions to make a point. The adult child did not care at all about the effect this would have on the mother. The adult child knew the opinions would make the mother happy.

- agent: `the adult child`
- effect: `make the mother happy`
- Ngo's original: Alice told her mother her opinions to make a point. Alice did not care at all about the effect this would have on her mother. Alice knew her opinions would make her mother happy.
- Ngo's effect: `make her mother happy`

## Storyline 28: the dog owner (nonmoral; storyline checks C1 C2 C3)

### moral (source ngo; checks A1 A9 A10 A13 R1 R2 R3 R4 B1 B8)

**bad** `kmp-nm-028-moral-bad`

> The dog owner smacked the puppy to relieve anger. The dog owner did not care at all about the effect this would have on the puppy. The dog owner knew the smacking would scar the puppy for life.

- agent: `the dog owner`
- effect: `scar the puppy for life`
- Ngo's original: Diane smacked her puppy to relieve her anger. Diane did not care at all about the effect this would have on her puppy. Diane knew the smacking would scar the puppy for life.
- Ngo's effect: `scar the puppy for life`

**good** `kmp-nm-028-moral-good`

> The dog owner installed a fence around the yard to relieve anger. The dog owner did not care at all about the effect this would have on the dog. The dog owner knew the fence would prevent the dog from running into traffic.

- agent: `the dog owner`
- effect: `prevent the dog from running into traffic`
- Ngo's original: Josh installed a fence around his yard to improve its looks. Josh did not care at all about the effect this would have on his dog. Josh knew the fence would prevent the dog from running into traffic.
- Ngo's effect: `prevent the dog from running into traffic`
- log (goal, scenario): 'to improve its looks' -> 'to relieve anger'. bad version's goal (B2), its pronoun dropped as in the bad version

## Storyline 29: the cop (nonmoral; storyline checks C1 C2 C3)

### moral (source ngo; checks A1 A9 A10 A13 R1 R2 R3 R4 B1 B8)

**bad** `kmp-nm-029-moral-bad`

> The cop pulled over the car to meet the monthly quota. The cop did not care at all about the effect this would have on traffic. The cop knew pulling over the car would create a traffic hazard on the busy road.

- agent: `the cop`
- effect: `create a traffic hazard on the busy road`
- Ngo's original: The cop pulled over the car to meet his monthly quota. He did not care at all about the effect this would have on traffic. He knew pulling over the car would create a traffic hazard on the busy road.
- Ngo's effect: `create a traffic hazard on the busy road`

**good** `kmp-nm-029-moral-good`

> The cop pulled over the truck to meet the monthly quota. The cop did not care at all about the effect this would have on the road. The cop knew pulling over the truck would make the road safer.

- agent: `the cop`
- effect: `make the road safer`
- Ngo's original: The cop pulled over the truck to meet her monthly quota. She did not care at all about the effect would have on the road. She knew pulling over the truck would make the road safer.
- Ngo's effect: `make the road safer`
- log (typo, scenario): 'the effect would have' -> 'the effect this would have'. missing 'this' (decision C, item 58)

## Storyline 30: the policyholder (nonmoral; storyline checks C1 C2 C3)

### moral (source ngo; checks A1 A9 A10 A13 R1 R2 R3 R4 B1 B8)

**bad** `kmp-nm-030-moral-bad`

> The policyholder faked the policyholder's own death to get back at the policyholder's mother. The policyholder did not care at all about the effect this would have on the rest of the family. The policyholder knew faking the death would devastate the rest of the family.

- agent: `the policyholder`
- effect: `devastate the rest of the family`
- Ngo's original: Flora faked her own death to get back at her mother. Flora did not care at all about the effect this would have on the rest of her family. Flora knew faking her death would devastate the rest of her family.
- Ngo's effect: `devastate the rest of her family`

**good** `kmp-nm-030-moral-good`

> The policyholder faked the policyholder's own death to get back at the policyholder's mother. The policyholder did not care at all about the effect this would have on the rest of the family. The policyholder knew the scheme would benefit the family with life insurance payments.

- agent: `the policyholder`
- effect: `benefit the family with life insurance payments`
- Ngo's original: Ernest faked his own death to get back at his mother. Ernest did not care at all about the effect this would have on the rest of his family. Ernest knew his scheme would benefit the family with life insurance payments.
- Ngo's effect: `benefit the family with life insurance payments`

## Storyline 31: the resident (nonmoral; storyline checks C1 C2 C3)

### moral (source ngo; checks A1 A9 A10 A13 R1 R2 R3 R4 B1 B8)

**bad** `kmp-nm-031-moral-bad`

> The resident protested in front of the church to express the resident's views. The resident did not care at all about the effect the protests would have on the church. The resident knew the messages would offend the church.

- agent: `the resident`
- effect: `offend the church`
- Ngo's original: Norman protested in front of the church to express his views. Norman did not care at all about the effect the protests would have on the church. Norman knew his messages would offend the church.
- Ngo's effect: `offend the church`

**good** `kmp-nm-031-moral-good`

> The resident protested in front of the church to express the resident's views. The resident did not care at all about the effect the protests would have on the church. The resident knew the messages would earn the church good publicity.

- agent: `the resident`
- effect: `earn the church good publicity`
- Ngo's original: Angela protested in front of the church to express her views. Angela did not care at all about the effect the protests would have on the church. Angela knew her messages would earn the church good publicity.
- Ngo's effect: `earn the church good publicity`

## Storyline 32: the author (nonmoral; storyline checks C1 C2 C3)

### moral (source ngo; checks A1 A9 A10 A13 R1 R2 R3 R4 B1 B8)

**bad** `kmp-nm-032-moral-bad`

> The author wrote a book to provide a sensational account of the Civil War hero. The author did not care at all about the effect the book would have on the hero's reputation. The author knew the book would severely destroy the hero's reputation.

- agent: `the author`
- effect: `destroy the hero's reputation`
- Ngo's original: Jo wrote a book to provide a sensational account of the Civil War hero. Jo did not care at all about the effect the book would have on the hero's reputation. Jo knew her book would severely destroy the hero's reputation.
- Ngo's effect: `destroy the hero's reputation`
- capitalised words (R1: names?): Civil, War

**good** `kmp-nm-032-moral-good`

> The author wrote a book to provide a sensational account of the Civil War hero. The author did not care at all about the effect the book would have on the hero's reputation. The author knew the book would reinforce the hero's great reputation.

- agent: `the author`
- effect: `reinforce the hero's great reputation`
- Ngo's original: Kurt wrote a book to provide an enthralling account of the World War II hero. Kurt did not care at all about the effect the book would have on the hero's reputation. Kurt knew his book would reinforce the hero's great reputation.
- Ngo's effect: `reinforce the hero's great reputation`
- log (goal, scenario): 'to provide an enthralling account of the World War II hero' -> 'to provide a sensational account of the Civil War hero'. bad version's goal (B2); the hero is part of the goal, so the good version's hero is now the Civil War hero too
- capitalised words (R1: names?): Civil, War

## Storyline 33: the newlywed (nonmoral; storyline checks C1 C2 C3)

### moral (source ngo; checks A1 A9 A10 A13 R1 R2 R3 R4 B1 B8)

**bad** `kmp-nm-033-moral-bad`

> The newlywed married their wife to finally settle down with a family. The newlywed did not care at all about the effect the marriage would have on their parents. The newlywed knew their parents would be miserable because of this marriage.

- agent: `the newlywed`
- effect: `cause their parents to be miserable`
- Ngo's original: Keith married his wife to finally settle down with a family. Keith did not care at all about the effect the marriage would have on his parents. Keith knew his parents would be miserable because of this marriage.
- Ngo's effect: `cause his parents to be miserable`
- log (pronoun, scenario): 'married his wife' -> 'married their wife'. singular their (review ruling 4)
- log (pronoun, scenario): 'on his parents' -> 'on their parents'. singular their (review ruling 4)
- log (pronoun, scenario): 'knew his parents' -> 'knew their parents'. singular their (review ruling 4)
- log (pronoun, effect): 'cause his parents' -> 'cause their parents'. singular their (review ruling 4)

**good** `kmp-nm-033-moral-good`

> The newlywed married their husband to finally settle down with a family. The newlywed did not care at all about the effect the marriage would have on their parents. The newlywed knew their parents would be very happy because of this marriage.

- agent: `the newlywed`
- effect: `cause their parents to be happy`
- Ngo's original: Melissa married her husband for some financial security. Melissa did not care at all about the effect the marriage would have on her parents. Melissa knew her parents would be very happy because of this marriage.
- Ngo's effect: `cause her parents to be happy`
- log (pronoun, scenario): 'married her husband' -> 'married their husband'. singular their (review ruling 4)
- log (goal, scenario): 'for some financial security' -> 'to finally settle down with a family'. bad version's goal (B2)
- log (pronoun, scenario): 'on her parents' -> 'on their parents'. singular their (review ruling 4)
- log (pronoun, scenario): 'knew her parents' -> 'knew their parents'. singular their (review ruling 4)
- log (pronoun, effect): 'cause her parents' -> 'cause their parents'. singular their (review ruling 4)

## Storyline 34: the activist (nonmoral; storyline checks C1 C2 C3)

### moral (source ngo; checks A1 A9 A10 A13 R1 R2 R3 R4 B1 B8)

**bad** `kmp-nm-034-moral-bad`

> The activist called in a bomb threat to a school to express outrage. The activist did not care at all about the effect the bomb threat would have on the students. The activist knew the bomb threat would traumatize many students.

- agent: `the activist`
- effect: `traumatize the students`
- Ngo's original: The activist called in a bomb threat to a school to express her outrage. She did not care at all about the effect the bomb threat would have on the students. She knew her bomb threat would traumatize many students.
- Ngo's effect: `traumatize the students`

**good** `kmp-nm-034-moral-good`

> The activist bombed the jail to express outrage. The activist did not care at all about the effect the bombing would have on innocent civilians. The activist knew the bombing would liberate innocent civilians from the jail.

- agent: `the activist`
- effect: `liberate the civilians`
- Ngo's original: The terrorist bombed the jail to express his outrage. He did not care at all about the effect the bombing would have on innocent civilians. He knew his bombing would liberate innocent civilians from the jail.
- Ngo's effect: `liberate the civilians`

## Storyline 35: the financial officer (nonmoral; storyline checks C1 C2 C3)

### moral (source ngo; checks A1 A9 A10 A13 R1 R2 R3 R4 B1 B8)

**bad** `kmp-nm-035-moral-bad`

> The financial officer reorganized funding to balance the budget. The financial officer did not care at all about the effect this would have on education. The financial officer knew the new system would harm education.

- agent: `the financial officer`
- effect: `harm education`
- Ngo's original: The financial officer reorganized funding to balance the budget. He did not care at all about the effect this would have on education. He knew his new system would harm education.
- Ngo's effect: `harm education`

**good** `kmp-nm-035-moral-good`

> The financial officer reorganized funding to balance the budget. The financial officer did not care at all about the effect this would have on marketing. The financial officer knew the new system would help marketing.

- agent: `the financial officer`
- effect: `help marketing`
- Ngo's original: The treasurer reorganized funding to streamline costs. She did not care at all about the effect this would have on marketing. She knew her new system would help marketing.
- Ngo's effect: `help marketing`
- log (goal, scenario): 'to streamline costs' -> 'to balance the budget'. bad version's goal (B2)

## Storyline 36: the product designer (nonmoral; storyline checks C1 C2 C3)

### moral (source ngo; checks A1 A9 A10 A13 R1 R2 R3 R4 B1 B8)

**bad** `kmp-nm-036-moral-bad`

> The product designer revised the tablet computer to increase sales. The product designer did not care at all about the effect the revision would have on the deaf. The product designer knew the revision would make the computer inaccessible for the deaf.

- agent: `the product designer`
- effect: `make the tablet inaccessible for the deaf`
- Ngo's original: The CEO revised the tablet computer to increase sales. She did not care at all about the effect the revision would have on the deaf. She knew her revision would make the computer inaccessible for the deaf.
- Ngo's effect: `make the tablet inaccessible for the deaf`

**good** `kmp-nm-036-moral-good`

> The product designer revised the music player to increase sales. The product designer did not care at all about the effect the revision would have on the blind. The product designer knew the revision would make the music player accessible for the blind.

- agent: `the product designer`
- effect: `make the music player accessible for the blind`
- Ngo's original: The CEO revised the music player to increase sales. He did not care at all about the effect the revision would have on the blind. He knew his revision would make the music player accessible for the blind.
- Ngo's effect: `make the tablet accessible for the blind`
- log (effect, effect): 'make the tablet accessible' -> 'make the music player accessible'. the scenario is about a music player (MM 2026-10-12, item 72)

## Storyline 37: the cult leader (nonmoral; storyline checks C1 C2 C3)

### moral (source ngo; checks A1 A9 A10 A13 R1 R2 R3 R4 B1 B8)

**bad** `kmp-nm-037-moral-bad`

> The cult leader wrote a declaration to keep the cult leader's influence. The cult leader did not care at all about the effect the declaration would have on the followers. The cult leader knew the decree would cause the followers to commit mass suicide.

- agent: `the cult leader`
- effect: `cause the followers to commit mass suicide`
- Ngo's original: The cult leader wrote a declaration to keep his influence. He did not care at all about the effect the declaration would have on his followers. He knew his decree would cause his followers to commit mass suicide.
- Ngo's effect: `cause his followers to commit mass suicide`

**good** `kmp-nm-037-moral-good`

> The cult leader made a new policy to keep the cult leader's influence. The cult leader did not care at all about the effect the policy would have on current followers. The cult leader knew the decree would prevent mass suicides from happening.

- agent: `the cult leader`
- effect: `prevent mass suicides from happening`
- Ngo's original: The cult leader made a new policy to recruit more members. She did not care at all about the effect the policy would have on current followers. She knew her decree would prevent mass suicides from happening.
- Ngo's effect: `prevent mass suicides from happening`
- log (goal, scenario): 'to recruit more members' -> "to keep the cult leader's influence". bad version's goal (B2)

## Storyline 38: the candidate (nonmoral; storyline checks C1 C2 C3)

### moral (source ngo; checks A1 A9 A10 A13 R1 R2 R3 R4 B1 B8)

**bad** `kmp-nm-038-moral-bad`

> The candidate ran for President to get a book deal. The candidate did not care at all about the effect the candidacy would have on education. The candidate knew the candidacy would harm education.

- agent: `the candidate`
- effect: `harm education`
- Ngo's original: The candidate ran for President to get a book deal. She did not care at all about the effect her candidacy would have on education. She knew her candidacy would harm education.
- Ngo's effect: `harm education`
- capitalised words (R1: names?): President

**good** `kmp-nm-038-moral-good`

> The candidate ran for President to get a book deal. The candidate did not care at all about the effect the candidacy would have on businesses. The candidate knew the candidacy would help businesses.

- agent: `the candidate`
- effect: `help the businesses`
- Ngo's original: The candidate ran for President to get a nice tour bus. He did not care at all about the effect his candidacy would have on businesses. He knew his candidacy would help businesses.
- Ngo's effect: `help the businesses`
- log (goal, scenario): 'to get a nice tour bus' -> 'to get a book deal'. bad version's goal (B2)
- capitalised words (R1: names?): President

## Storyline 39: the farmer (nonmoral; storyline checks C1 C2 C3)

### moral (source ngo; checks A1 A9 A10 A13 R1 R2 R3 R4 B1 B8)

**bad** `kmp-nm-039-moral-bad`

> The farmer switched to a new type of tomato to decrease the farmer's workload. The farmer did not care at all about the effect the tomato would have on the farmer's customers. The farmer knew the new tomato would make many people sick.

- agent: `the farmer`
- effect: `cause people to be sick`
- Ngo's original: The farmer switched to a new type of tomato to decrease his workload. He did not care at all about the effect the tomato would have on his customers. He knew his new tomato would make many people sick.
- Ngo's effect: `cause people to be sick`

**good** `kmp-nm-039-moral-good`

> The farmer switched to a new type of lettuce to decrease the farmer's workload. The farmer did not care at all about the effect the lettuce would have on the farmer's customers. The farmer knew the new lettuce would be healthy for many customers.

- agent: `the farmer`
- effect: `improve the health of the farmer's customers`
- Ngo's original: The farmer switched to a new type of lettuce to increase sales. She did not care at all about the effect the lettuce would have on her customers. She knew her new lettuce would be healthy for many customers.
- Ngo's effect: `improve the health of her customers`
- log (goal, scenario): 'to increase sales' -> "to decrease the farmer's workload". bad version's goal (B2)

## Storyline 40: the doctor (nonmoral; storyline checks C1 C2 C3)

### moral (source ngo; checks A1 A9 A10 A13 R1 R2 R3 R4 B1 B8)

**bad** `kmp-nm-040-moral-bad`

> The doctor prescribed the Elixir drug to make the drug company happy. The doctor did not care at all about the effect the Elixir drug would have on the patient. The doctor knew the Elixir drug would cause fatal bleeding for the patient.

- agent: `the doctor`
- effect: `cause the patient to have fatal bleeding`
- Ngo's original: The doctor prescribed the Elixir drug to make the drug company happy. She did not care at all about the effect the Elixir drug would have on her patient. She knew the Elixir drug would cause fatal bleeding for her patient.
- Ngo's effect: `cause the patient to have fatal bleeding`
- capitalised words (R1: names?): Elixir

**good** `kmp-nm-040-moral-good`

> The doctor prescribed the Gastropurge drug to make the drug company happy. The doctor did not care at all about the effect the Gastropurge drug would have on the patient. The doctor knew the Gastropurge drug would finally cure the patient.

- agent: `the doctor`
- effect: `cure the patient`
- Ngo's original: The doctor prescribed the Gastropurge drug to please the drug vendor. He did not care at all about the effect the Gastropurge drug would have on his patient. He knew the Gastropurge drug would finally cure his patient.
- Ngo's effect: `cure his patient`
- log (goal, scenario): 'to please the drug vendor' -> 'to make the drug company happy'. bad version's goal (B2)
- capitalised words (R1: names?): Gastropurge

