# Review sheet: 15_nm_surv_moral

Items: `stimuli/nonmoral.csv`, 44 draft items. Checklist: `docs/DEFINITIONS_AND_CHECKLIST.md` section 6.

Record one decision per item in `stimuli/review/15_nm_surv_moral_decisions.csv`: `approved`, `rejected` or `revise`, your initials as reviewer, the date (YYYY-MM-DD), and a note for every rejected or revise row naming the failed check (e.g. "B4: good version is bigger"). Then run `../../.venv/bin/python -m tools.review apply --items stimuli/nonmoral.csv --decisions stimuli/review/15_nm_surv_moral_decisions.csv` yourself.

Automated checks (design_problems and tools.lint_stimuli) were clean when this sheet was made.

## Storyline 1: the engineer (nonmoral; storyline checks C1 C2 C3)

### moral (source ngo; checks A1 A9 A10 A13 R1 R2 R3 R4 B1 B8)

**bad** `kmp-nm-001-moral-bad`

> The engineer released a gadget to make a deadline. The engineer did not care at all about the effect the gadget would have on babies. The engineer knew the gadget would kill babies.

- agent: `the engineer`
- effect: `cause the death of babies`
- Ngo's original: Bill released a gadget to make a deadline. Bill did not care at all about the effect the gadget would have on babies. Bill knew his gadget would kill babies.
- Ngo's effect: `cause the death of babies`

**good** `kmp-nm-001-moral-good`

> The engineer released an invention to make a deadline. The engineer did not care at all about the effect the invention would have on toddlers. The engineer knew the invention would help toddlers.

- agent: `the engineer`
- effect: `help toddlers`
- Ngo's original: Robyn released an invention to make a deadline. Robyn did not care at all about the effect the invention would have on toddlers. Robyn knew her invention would help toddlers.
- Ngo's effect: `help toddlers`

## Storyline 2: the board chair (nonmoral; storyline checks C1 C2 C3)

### moral (source ngo; checks A1 A9 A10 A13 R1 R2 R3 R4 B1 B8)

**bad** `kmp-nm-002-moral-bad`

> The board chair started a plan to increase profits. The board chair did not care at all about the effect the plan would have on the environment. The board chair knew the plan would harm the environment.

- agent: `the board chair`
- effect: `harm the environment`
- Ngo's original: The CEO started a plan to increase profits. She did not care at all about the effect the plan would have on the environment. She knew her plan would harm the environment.
- Ngo's effect: `harm the environment`

**good** `kmp-nm-002-moral-good`

> The board chair started a plan to increase profits. The board chair did not care at all about the effect the plan would have on the environment. The board chair knew the plan would help the environment.

- agent: `the board chair`
- effect: `help the environment`
- Ngo's original: The chairman started a plan to increase revenue. He did not care at all about the effect the plan would have on the environment. He knew his plan would help the environment.
- Ngo's effect: `help the environment`
- log (goal, scenario): 'to increase revenue' -> 'to increase profits'. bad version's goal (B2)

## Storyline 3: the investor (nonmoral; storyline checks C1 C2 C3)

### moral (source ngo; checks A1 A9 A10 A13 R1 R2 R3 R4 B1 B8)

**bad** `kmp-nm-003-moral-bad`

> The investor enacted a financial scheme to buy a house. The investor did not care at all about the effect the scheme would have on old retirees. The investor knew the plan would bankrupt old retirees.

- agent: `the investor`
- effect: `bankrupt old retirees`
- Ngo's original: Roger enacted a financial scheme to buy a house. Roger did not care at all about the effect the scheme would have on old retirees. Roger knew his plan would bankrupt old retirees.
- Ngo's effect: `bankrupt old retirees`

**good** `kmp-nm-003-moral-good`

> The investor enacted a financial scheme to buy a house. The investor did not care at all about the effect the scheme would have on old retirees. The investor knew the plan would help old retirees.

- agent: `the investor`
- effect: `help old retirees`
- Ngo's original: Renee enacted a financial scheme to buy a car. Renee did not care at all about the effect the scheme would have on old retirees. Renee knew her plan would help old retirees.
- Ngo's effect: `help old retirees`
- log (goal, scenario): 'to buy a car' -> 'to buy a house'. bad version's goal (B2)

## Storyline 7: the bomber pilot (nonmoral; storyline checks C1 C2 C3)

### moral (source ngo; checks A1 A9 A10 A13 R1 R2 R3 R4 B1 B8)

**bad** `kmp-nm-007-moral-bad`

> The bomber pilot bombed a factory to reduce the enemy's steel production. The bomber pilot did not care at all about the effect the bombing would have on innocent civilians. The bomber pilot knew the bombing would kill innocent civilians.

- agent: `the bomber pilot`
- effect: `kill innocent civilians`
- Ngo's original: The airplane bomber bombed a factory to reduce enemy’s steel production. He did not care at all about the effect the bombing would have on innocent civilians. He knew his bombing would kill innocent civilians.
- Ngo's effect: `kill innocent civilians`
- log (typo, scenario): "to reduce enemy's steel production" -> "to reduce the enemy's steel production". missing article (decision C)

**good** `kmp-nm-007-moral-good`

> The bomber pilot bombed a facility to reduce the enemy's steel production. The bomber pilot did not care at all about the effect the bombing would have on the townsfolk. The bomber pilot knew the bombing would liberate the townsfolk.

- agent: `the bomber pilot`
- effect: `liberate the townsfolk`
- Ngo's original: The bomber pilot bombed a facility to reduce the enemy’s iron production. She did not care at all about the effect the bombing would have on the townsfolk. She knew her bombing would liberate the townsfolk.
- Ngo's effect: `liberate the townsfolk`
- log (goal, scenario): "to reduce the enemy's iron production" -> "to reduce the enemy's steel production". bad version's goal (B2), with the bad version's article fix

## Storyline 9: the grower (nonmoral; storyline checks C1 C2 C3)

### moral (source ngo; checks A1 A9 A10 A13 R1 R2 R3 R4 B1 B8)

**bad** `kmp-nm-009-moral-bad`

> The grower spread weed killer to protect the grower's crops. The grower did not care at all about the effect this would have on the neighbor's crops. The grower knew the pesticide would harm the neighbor's crops.

- agent: `the grower`
- effect: `harm the neighbor's crops`
- Ngo's original: Jenny spread weed killer to protect her crops. Jenny did not care at all about the effect this would have on Susie-Ann’s crops. Jenny knew her pesticide would harm Susie-Ann's crops.
- Ngo's effect: `harm her neighbor's crops`
- log (other_name, scenario): "Susie-Ann's crops" -> "the neighbor's crops". non-agent name to role (decision L); the effect already says neighbor (MM 2026-10-12)

**good** `kmp-nm-009-moral-good`

> The grower spread anti-fungals to protect the grower's crops. The grower did not care at all about the effect this would have on the neighbor's crops. The grower knew the anti-fungals would protect the neighbor's crops.

- agent: `the grower`
- effect: `protect the neighbor's crops`
- Ngo's original: Stanley spread anti-fungals to protect his crops. Stanley did not care at all about the effect this would have on Billy-Bob’s crops. Stanley knew his anti-fungals would protect Billy-Bob’s crops.
- Ngo's effect: `protect Billy-Bob’s crops`
- log (other_name, scenario): "Billy-Bob's crops" -> "the neighbor's crops". non-agent name to role (decision L)
- log (other_name, effect): "Billy-Bob's crops" -> "the neighbor's crops". non-agent name to role (decision L)

## Storyline 13: the merchant (nonmoral; storyline checks C1 C2 C3)

### moral (source ngo; checks A1 A9 A10 A13 R1 R2 R3 R4 B1 B8)

**bad** `kmp-nm-013-moral-bad`

> The merchant opened a kiosk to make more money. The merchant did not care at all about the effect the kiosk would have on nearby vendors. The merchant knew the kiosk would harm nearby vendors.

- agent: `the merchant`
- effect: `harm nearby vendors`
- Ngo's original: Joe opened a kiosk to make more money. Joe did not care at all about the effect the kiosk would have on nearby vendors. Joe knew his kiosk would harm nearby vendors.
- Ngo's effect: `harm nearby vendors`

**good** `kmp-nm-013-moral-good`

> The merchant opened a new store to make more money. The merchant did not care at all about the effect the store would have on other businesses. The merchant knew the store would help other businesses.

- agent: `the merchant`
- effect: `help other businesses`
- Ngo's original: Helen opened a new store to increase revenue. Helen did not care at all about the effect the store would have on other businesses. Helen knew her store would help other businesses.
- Ngo's effect: `help other businesses`
- log (goal, scenario): 'to increase revenue' -> 'to make more money'. bad version's goal (B2)

## Storyline 15: the student (nonmoral; storyline checks C1 C2 C3)

### moral (source ngo; checks A1 A9 A10 A13 R1 R2 R3 R4 B1 B8)

**bad** `kmp-nm-015-moral-bad`

> The student threw a party to be more popular. The student did not care at all about the effect this would have on the roommate. The student knew the party would make the roommate fail the morning's exam.

- agent: `the student`
- effect: `make the roommate fail the morning's exam`
- Ngo's original: Jacob threw a party to be more popular. Jacob did not care at all about the effect this would have on his roommate, Curtis. Jacob knew his party would make Curtis fail the morning's exam.
- Ngo's effect: `make Curtis fail the morning's exam`
- log (other_name, scenario): 'his roommate, Curtis' -> 'the roommate'. non-agent name to role (decision L)
- log (other_name, scenario): 'make Curtis fail' -> 'make the roommate fail'. non-agent name to role (decision L)
- log (other_name, effect): 'make Curtis fail' -> 'make the roommate fail'. non-agent name to role (decision L)

**good** `kmp-nm-015-moral-good`

> The student threw a party to be more popular. The student did not care at all about the effect this would have on the roommate. The student knew the party would help the roommate make new friends.

- agent: `the student`
- effect: `help the roommate make new friends`
- Ngo's original: Rachel threw a party to have fun. Rachel did not care at all about the effect this would have on her roommate, Jackie. Rachel knew her party would help Jackie make new friends.
- Ngo's effect: `help Jackie make new friends`
- log (goal, scenario): 'to have fun' -> 'to be more popular'. bad version's goal (B2)
- log (other_name, scenario): 'her roommate, Jackie' -> 'the roommate'. non-agent name to role (decision L)
- log (other_name, scenario): 'help Jackie make' -> 'help the roommate make'. non-agent name to role (decision L)
- log (other_name, effect): 'help Jackie make' -> 'help the roommate make'. non-agent name to role (decision L)

## Storyline 16: the gardener (nonmoral; storyline checks C1 C2 C3)

### moral (source ngo; checks A1 A9 A10 A13 R1 R2 R3 R4 B1 B8)

**bad** `kmp-nm-016-moral-bad`

> The gardener planted a tree to decorate the gardener's yard. The gardener did not care at all about the effect the tree would have on the neighbor. The gardener knew the tree would make the neighbor unhappy.

- agent: `the gardener`
- effect: `make the neighbor unhappy`
- Ngo's original: Russell planted a tree to decorate his yard. Russell did not care at all about the effect the tree would have on his neighbor. Russell knew his tree would make his neighbor unhappy.
- Ngo's effect: `make his neighbor unhappy`

**good** `kmp-nm-016-moral-good`

> The gardener planted a tree to decorate the gardener's yard. The gardener did not care at all about the effect the tree would have on the neighbor. The gardener knew the tree would make the neighbor happy.

- agent: `the gardener`
- effect: `make the neighbor happy`
- Ngo's original: Vicky planted a tree to have fruit in the fall. Vicky did not care at all about the effect the tree would have on her neighbor. Vicky knew her tree would make her neighbor happy.
- Ngo's effect: `make her neighbor happy`
- log (goal, scenario): 'to have fruit in the fall' -> "to decorate the gardener's yard". bad version's goal (B2)

## Storyline 18: the surgeon general (nonmoral; storyline checks C1 C2 C3)

### moral (source ngo; checks A1 A9 A10 A13 R1 R2 R3 R4 B1 B8)

**bad** `kmp-nm-018-moral-bad`

> The surgeon general implemented the policy to keep the position. The surgeon general did not care at all about the effect the policy would have on rates of influenza. The surgeon general knew the policy would increase rates of influenza.

- agent: `the surgeon general`
- effect: `increase rates of influenza`
- Ngo's original: The Surgeon General implemented the policy to keep his position. He did not care at all about the effect the policy would have on rates of influenza. He knew his policy would increase rates of influenza.
- Ngo's effect: `increase rates of influenza`

**good** `kmp-nm-018-moral-good`

> The surgeon general implemented the policy to keep the position. The surgeon general did not care at all about the effect the policy would have on rates of deaths. The surgeon general knew the policy would decrease deaths.

- agent: `the surgeon general`
- effect: `decrease deaths`
- Ngo's original: The Defense Secretary implemented the policy to remain politically popular. She did not care at all about the effect the policy would have on rates of deaths. She knew her policy would decrease deaths.
- Ngo's effect: `decrease deaths`
- log (goal, scenario): 'to remain politically popular' -> 'to keep the position'. bad version's goal (B2)

## Storyline 19: the employer (nonmoral; storyline checks C1 C2 C3)

### moral (source ngo; checks A1 A9 A10 A13 R1 R2 R3 R4 B1 B8)

**bad** `kmp-nm-019-moral-bad`

> The employer enacted the plan to increase earnings. The employer did not care at all about the effect the plan would have on the employer's employees. The employer knew the plan would make employees unhappy.

- agent: `the employer`
- effect: `make employees unhappy`
- Ngo's original: Carolyn enacted the plan to increase earnings. Carolyn did not care at all about the effect the plan would have on her employees. Carolyn knew her plan would make employees unhappy.
- Ngo's effect: `make employees unhappy`

**good** `kmp-nm-019-moral-good`

> The employer enacted the plan to increase earnings. The employer did not care at all about the effect the plan would have on the employer's employees. The employer knew the plan would make employees happy.

- agent: `the employer`
- effect: `make employees happy`
- Ngo's original: Christopher enacted the plan to increase earnings. Christopher did not care at all about the effect the plan would have on his employees. Christopher knew his plan would make employees happy.
- Ngo's effect: `make employees happy`

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

