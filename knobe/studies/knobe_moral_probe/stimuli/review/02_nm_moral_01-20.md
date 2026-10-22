# Review sheet: 02_nm_moral_01-20

Items: `stimuli/nonmoral.csv`, 40 draft items. Checklist: `docs/DEFINITIONS_AND_CHECKLIST.md` section 6.

Record one decision per item in `stimuli/review/02_nm_moral_01-20_decisions.csv`: `approved`, `rejected` or `revise`, your initials as reviewer, the date (YYYY-MM-DD), and a note for every rejected or revise row naming the failed check (e.g. "B4: good version is bigger"). Then run `../../.venv/bin/python -m tools.review apply --items stimuli/nonmoral.csv --decisions stimuli/review/02_nm_moral_01-20_decisions.csv` yourself.

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

## Storyline 4: the club owner (nonmoral; storyline checks C1 C2 C3)

### moral (source ngo; checks A1 A9 A10 A13 R1 R2 R3 R4 B1 B8)

**bad** `kmp-nm-004-moral-bad`

> The club owner renovated the country club to improve its appearance. The club owner did not care at all about the effect this would have on membership costs. The club owner knew the renovation would increase membership costs.

- agent: `the club owner`
- effect: `increase membership costs`
- Ngo's original: Natasha renovated the country club to improve its appearance. Natasha did not care at all about the effect this would have on membership costs. Natasha knew her renovation would increase membership costs.
- Ngo's effect: `increase membership costs`

**good** `kmp-nm-004-moral-good`

> The club owner renovated the golf course to improve its appearance. The club owner did not care at all about the effect this would have on customer satisfaction. The club owner knew the renovation would increase customer satisfaction.

- agent: `the club owner`
- effect: `increase customer satisfaction`
- Ngo's original: Floyd renovated the golf course to improve its playability. Floyd did not care at all about the effect this would have on customer satisfaction. Floyd knew his renovation would increase customer satisfaction.
- Ngo's effect: `increase customer satisfaction`
- log (goal, scenario): 'to improve its playability' -> 'to improve its appearance'. bad version's goal (B2)

## Storyline 5: the mayor (nonmoral; storyline checks C1 C2 C3)

### moral (source ngo; checks A1 A9 A10 A13 R1 R2 R3 R4 B1 B8)

**bad** `kmp-nm-005-moral-bad`

> The mayor diverted water to Oldtown to gain votes. The mayor did not care at all about the effect this would have on Newtown. The mayor knew diverting the water would deprive Newtown of water.

- agent: `the mayor`
- effect: `deprive Newtown of water`
- Ngo's original: The mayor diverted water to Oldtown to gain votes. He did not care at all about the effect this would have on Newtown. He knew diverting the water would deprive Newtown of water.
- Ngo's effect: `deprive Newtown of water`
- capitalised words (R1: names?): Newtown, Oldtown

**good** `kmp-nm-005-moral-good`

> The mayor diverted water to the mayor's town to gain votes. The mayor did not care at all about the effect this would have on food production. The mayor knew diverting the water for the mayor's town would increase food production.

- agent: `the mayor`
- effect: `increase food production`
- Ngo's original: The councilwoman diverted water to her town to win an election. She did not care at all about the effect this would have on food production. She knew diverting the water for his town would increase food production.
- Ngo's effect: `increase food production`
- log (goal, scenario): 'to win an election' -> 'to gain votes'. bad version's goal (B2)

## Storyline 6: the plant manager (nonmoral; storyline checks C1 C2 C3)

### moral (source ngo; checks A1 A9 A10 A13 R1 R2 R3 R4 B1 B8)

**bad** `kmp-nm-006-moral-bad`

> The plant manager enacted a plan to increase profits. The plant manager did not care at all about the effect the plan would have on flooding. The plant manager knew the plan would increase flooding.

- agent: `the plant manager`
- effect: `increase flooding`
- Ngo's original: The CEO enacted a plan to increase profits. She did not care at all about the effect the plan would have on flooding. She knew her plan would increase flooding.
- Ngo's effect: `increase flooding`

**good** `kmp-nm-006-moral-good`

> The plant manager enacted a plan to increase profits. The plant manager did not care at all about the effect the plan would have on flooding. The plant manager knew the plan would reduce flooding.

- agent: `the plant manager`
- effect: `reduce flooding`
- Ngo's original: The company owner enacted a plan to increase profits. He did not care at all about the effect the plan would have on flooding. He knew his plan would reduce flooding.
- Ngo's effect: `reduce flooding`

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

## Storyline 8: the university president (nonmoral; storyline checks C1 C2 C3)

### moral (source ngo; checks A1 A9 A10 A13 R1 R2 R3 R4 B1 B8)

**bad** `kmp-nm-008-moral-bad`

> The university president enacted a plan to increase business school funding. The university president did not care at all about the effect the plan would have on the medical school. The university president knew the plan would cut funding for the medical school.

- agent: `the university president`
- effect: `cut funding for the medical school`
- Ngo's original: The university president enacted a plan to increase business school funding. He did not care at all about the effect the plan would have on the medical school. He knew his plan would cut funding for the medical school.
- Ngo's effect: `cut funding for the medical school`

**good** `kmp-nm-008-moral-good`

> The university president enacted a plan to increase business school funding. The university president did not care at all about the effect the plan would have on the soccer team. The university president knew the plan would boost funding for the soccer team.

- agent: `the university president`
- effect: `boost funding for the soccer team`
- Ngo's original: The athletic director enacted a plan to increase basketball funding. She did not care at all about the effect the plan would have on the soccer team. She knew her plan would boost funding for the soccer team.
- Ngo's effect: `boost funding for the soccer team`
- log (goal, scenario): 'to increase basketball funding' -> 'to increase business school funding'. bad version's goal (B2)

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

## Storyline 10: the relative (nonmoral; storyline checks C1 C2 C3)

### moral (source ngo; checks A1 A9 A10 A13 R1 R2 R3 R4 B1 B8)

**bad** `kmp-nm-010-moral-bad`

> The relative placed an uncle in a nursing home to avoid being the caretaker. The relative did not care at all about the effect the placement would have on the uncle. The relative knew placing the uncle in a nursing home would make the uncle extremely unhappy.

- agent: `the relative`
- effect: `make the uncle unhappy`
- Ngo's original: Kate placed her uncle in a nursing home to avoid being his caretaker. Kate did not care at all about the effect the placement would have on her uncle. Kate knew placing him in a nursing home would make him extremely unhappy.
- Ngo's effect: `make her uncle unhappy`
- log (other_name, scenario): 'her uncle in' -> 'an uncle in'. kin noun with an article (review ruling 1)
- log (other_name, scenario): 'being his caretaker' -> 'being the caretaker'. his is the uncle; restructured so the goal matches the good version's (B2)
- log (other_name, scenario): 'on her uncle' -> 'on the uncle'. her is the agent; kin noun with an article (review ruling 1)
- log (other_name, scenario): 'placing him in' -> 'placing the uncle in'. him is the uncle
- log (other_name, scenario): 'make him extremely' -> 'make the uncle extremely'. him is the uncle
- log (other_name, effect): 'make her uncle' -> 'make the uncle'. kin noun with an article (review ruling 1)

**good** `kmp-nm-010-moral-good`

> The relative placed an aunt in a nursing home to avoid being the caretaker. The relative did not care at all about the effect the placement would have on the aunt. The relative knew placing the aunt in a nursing home would make the aunt extremely happy.

- agent: `the relative`
- effect: `make the aunt happy`
- Ngo's original: Jared placed his aunt in a nursing home to avoid being her caretaker. Jared did not care at all about the effect the placement would have on his aunt. Jared knew placing his aunt in a nursing home would make her extremely happy.
- Ngo's effect: `make his aunt happy`
- log (other_name, scenario): 'his aunt in a nursing home to' -> 'an aunt in a nursing home to'. kin noun with an article (review ruling 1)
- log (other_name, scenario): 'being her caretaker' -> 'being the caretaker'. her is the aunt; restructured so the goal matches the bad version's (B2)
- log (other_name, scenario): 'on his aunt' -> 'on the aunt'. his is the agent; kin noun with an article (review ruling 1)
- log (other_name, scenario): 'placing his aunt' -> 'placing the aunt'. his is the agent; kin noun with an article (review ruling 1)
- log (other_name, scenario): 'make her extremely' -> 'make the aunt extremely'. her is the aunt
- log (other_name, effect): 'make his aunt' -> 'make the aunt'. kin noun with an article (review ruling 1)

## Storyline 11: the homeowner (nonmoral; storyline checks C1 C2 C3)

### moral (source ngo; checks A1 A9 A10 A13 R1 R2 R3 R4 B1 B8)

**bad** `kmp-nm-011-moral-bad`

> The homeowner installed a light display to decorate the homeowner's house. The homeowner did not care at all about the effect the display would have on the neighbors. The homeowner knew the light display would hamper the neighbors' stargazing.

- agent: `the homeowner`
- effect: `hamper the neighbors' stargazing`
- Ngo's original: Tim installed a light display to decorate his house. Tim did not care at all about the effect the display would have on the neighbors. Tim knew his light display would hamper the neighbors' stargazing.
- Ngo's effect: `hamper the neighbors' stargazing`

**good** `kmp-nm-011-moral-good`

> The homeowner installed a lighting array to decorate the homeowner's house. The homeowner did not care at all about the effect the array would have on neighborhood kids. The homeowner knew the light display would help the kids to play ball at night.

- agent: `the homeowner`
- effect: `help the kids play ball at night`
- Ngo's original: Tricia installed a lighting array to decorate her yard. Tricia did not care at all about the effect the array would have on neighborhood kids. Tricia knew her light display would help the kids to play ball at night.
- Ngo's effect: `help the kids play ball at night`
- log (goal, scenario): 'to decorate her yard' -> "to decorate the homeowner's house". bad version's goal (B2)

## Storyline 12: the scientist (nonmoral; storyline checks C1 C2 C3)

### moral (source ngo; checks A1 A9 A10 A13 R1 R2 R3 R4 B1 B8)

**bad** `kmp-nm-012-moral-bad`

> The scientist released a drug to gain profit. The scientist did not care at all about the effect the drug would have on rates of cancer. The scientist knew the drug would increase the rate of cancer.

- agent: `the scientist`
- effect: `increase the rate of cancer`
- Ngo's original: The scientist released a drug to gain profit. She did not care at all about the effect the drug would have rates of cancer. She knew her drug would increase the rate of cancer.
- Ngo's effect: `increase the rate of cancer`
- log (typo, scenario): 'would have rates of cancer' -> 'would have on rates of cancer'. missing 'on' (decision C, item 23)

**good** `kmp-nm-012-moral-good`

> The scientist released a drug to gain profit. The scientist did not care at all about the effect the drug would have on rates of heart attacks. The scientist knew the drug would decrease the rate of heart attacks.

- agent: `the scientist`
- effect: `decrease the rate of heart attacks`
- Ngo's original: The scientist released a drug to make a deadline. He did not care at all about the effect the drug would have on rates of heart attacks. He knew his drug would decrease the rate of heart attacks.
- Ngo's effect: `decrease the rate of heart attacks`
- log (goal, scenario): 'to make a deadline' -> 'to gain profit'. bad version's goal (B2)

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

## Storyline 14: the tenant (nonmoral; storyline checks C1 C2 C3)

### moral (source ngo; checks A1 A9 A10 A13 R1 R2 R3 R4 B1 B8)

**bad** `kmp-nm-014-moral-bad`

> The tenant vacuumed to clean the floor. The tenant did not care at all about the effect the vacuum would have on the tenant's dog. The tenant knew the vacuuming would distress the tenant's dog.

- agent: `the tenant`
- effect: `distress the tenant's dog`
- Ngo's original: Marta vacuumed to clean her floor. Marta did not care at all about the effect the vacuum would have on her dog. Marta knew her vacuuming would distress her dog.
- Ngo's effect: `distress her dog`

**good** `kmp-nm-014-moral-good`

> The tenant waxed the floor to clean the floor. The tenant did not care at all about the effect the waxing would have on the tenant's cat. The tenant knew the waxing would entertain the tenant's cat.

- agent: `the tenant`
- effect: `entertain the tenant's cat`
- Ngo's original: Phil waxed his floor to make it shiny. Phil did not care at all about the effect the waxing would have on his cat. Phil knew his waxing would entertain his cat.
- Ngo's effect: `entertain his cat`
- log (goal, scenario): 'to make it shiny' -> 'to clean the floor'. bad version's goal (B2)

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

## Storyline 17: the shelter director (nonmoral; storyline checks C1 C2 C3)

### moral (source ngo; checks A1 A9 A10 A13 R1 R2 R3 R4 B1 B8)

**bad** `kmp-nm-017-moral-bad`

> The shelter director cut spending at the animal shelter to increase the shelter director's salary. The shelter director did not care at all about the effect the cut would have on the shelter. The shelter director knew cutting spending would cause a dog at the shelter to be put down.

- agent: `the shelter director`
- effect: `cause the dog to be put down`
- Ngo's original: Brenda cut spending at the animal shelter to increase her salary. Brenda did not care at all about the effect the cut would have on the shelter. Brenda knew cutting spending would cause a dog at the shelter to be put down.
- Ngo's effect: `cause the dog to be put down`

**good** `kmp-nm-017-moral-good`

> The shelter director cut spending at the homeless shelter to increase the shelter director's salary. The shelter director did not care at all about the effect the cut would have on the shelter. The shelter director knew cutting spending would help the shelter run more efficiently.

- agent: `the shelter director`
- effect: `help the shelter run more efficiently`
- Ngo's original: Billy cut spending at the homeless shelter to increase his pay. Billy did not care at all about the effect the cut would have on the shelter. Billy knew cutting spending would help the shelter run more efficiently.
- Ngo's effect: `help the shelter run more efficiently`
- log (goal, scenario): 'to increase his pay' -> "to increase the shelter director's salary". bad version's goal (B2)

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

## Storyline 20: the store owner (nonmoral; storyline checks C1 C2 C3)

### moral (source ngo; checks A1 A9 A10 A13 R1 R2 R3 R4 B1 B8)

**bad** `kmp-nm-020-moral-bad`

> The store owner built a road to increase traffic to the country store. The store owner did not care at all about the effect this would have on a nearby 1000-year-old tree. The store owner knew the new road would cause the 1000-year-old tree to die.

- agent: `the store owner`
- effect: `cause the 1000-year-old tree to die`
- Ngo's original: Tina built a road to increase traffic to her country store. Tina did not care at all about the effect this would have on a nearby 1000-year-old tree. Tina knew her new road would cause the 1000-year-old tree to die.
- Ngo's effect: `cause the 1000-year-old tree to die`

**good** `kmp-nm-020-moral-good`

> The store owner bought a trolley to increase traffic to the country store. The store owner did not care at all about the effect this would have on a nearby monument. The store owner knew the new trolley would make the monument famous.

- agent: `the store owner`
- effect: `make the monument famous`
- Ngo's original: Ronald bought a trolley to increase visitors to his theme park. Ronald did not care at all about the effect this would have on a nearby monument. Ronald knew his new road would make the monument famous.
- Ngo's effect: `make the monument famous`
- log (goal, scenario): 'to increase visitors to his theme park' -> 'to increase traffic to the country store'. bad version's goal (B2)
- log (typo, scenario): 'his new road' -> 'the new trolley'. the good version buys a trolley, not a road (decision C, item 40)

