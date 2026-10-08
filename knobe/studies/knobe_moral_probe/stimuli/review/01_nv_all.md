# Review sheet: 01_nv_all

Items: `stimuli/ngo_verbatim.csv`, 80 draft items. Checklist: `docs/DEFINITIONS_AND_CHECKLIST.md` section 6.

Record one decision per item in `stimuli/review/01_nv_all_decisions.csv`: `approved`, `rejected` or `revise`, your initials as reviewer, the date (YYYY-MM-DD), and a note for every rejected or revise row naming the failed check (e.g. "B4: good version is bigger"). Then run `../../.venv/bin/python -m tools.review apply --items stimuli/ngo_verbatim.csv --decisions stimuli/review/01_nv_all_decisions.csv` yourself.

Automated checks (design_problems and tools.lint_stimuli) were clean when this sheet was made.

## Storyline 1: Bill (ngo_verbatim; storyline checks C1)

### moral (source ngo; checks A1 A10 A13 B9)

**bad** `kmp-nv-001-moral-bad`

> Bill released a gadget to make a deadline. Bill did not care at all about the effect the gadget would have on babies. Bill knew his gadget would kill babies.

- agent: `Bill`
- effect: `cause the death of babies`

**good** `kmp-nv-001-moral-good`

> Robyn released an invention to make a deadline. Robyn did not care at all about the effect the invention would have on toddlers. Robyn knew her invention would help toddlers.

- agent: `Robyn`
- effect: `help toddlers`

## Storyline 2: the CEO (ngo_verbatim; storyline checks C1)

### moral (source ngo; checks A1 A10 A13 B9)

**bad** `kmp-nv-002-moral-bad`

> The CEO started a plan to increase profits. She did not care at all about the effect the plan would have on the environment. She knew her plan would harm the environment.

- agent: `the CEO`
- effect: `harm the environment`

**good** `kmp-nv-002-moral-good`

> The chairman started a plan to increase revenue. He did not care at all about the effect the plan would have on the environment. He knew his plan would help the environment.

- agent: `the chairman`
- effect: `help the environment`

## Storyline 3: Roger (ngo_verbatim; storyline checks C1)

### moral (source ngo; checks A1 A10 A13 B9)

**bad** `kmp-nv-003-moral-bad`

> Roger enacted a financial scheme to buy a house. Roger did not care at all about the effect the scheme would have on old retirees. Roger knew his plan would bankrupt old retirees.

- agent: `Roger`
- effect: `bankrupt old retirees`

**good** `kmp-nv-003-moral-good`

> Renee enacted a financial scheme to buy a car. Renee did not care at all about the effect the scheme would have on old retirees. Renee knew her plan would help old retirees.

- agent: `Renee`
- effect: `help old retirees`

## Storyline 4: Natasha (ngo_verbatim; storyline checks C1)

### moral (source ngo; checks A1 A10 A13 B9)

**bad** `kmp-nv-004-moral-bad`

> Natasha renovated the country club to improve its appearance. Natasha did not care at all about the effect this would have on membership costs. Natasha knew her renovation would increase membership costs.

- agent: `Natasha`
- effect: `increase membership costs`

**good** `kmp-nv-004-moral-good`

> Floyd renovated the golf course to improve its playability. Floyd did not care at all about the effect this would have on customer satisfaction. Floyd knew his renovation would increase customer satisfaction.

- agent: `Floyd`
- effect: `increase customer satisfaction`

## Storyline 5: the mayor (ngo_verbatim; storyline checks C1)

### moral (source ngo; checks A1 A10 A13 B9)

**bad** `kmp-nv-005-moral-bad`

> The mayor diverted water to Oldtown to gain votes. He did not care at all about the effect this would have on Newtown. He knew diverting the water would deprive Newtown of water.

- agent: `the mayor`
- effect: `deprive Newtown of water`
- capitalised words (R1: names?): Newtown, Oldtown

**good** `kmp-nv-005-moral-good`

> The councilwoman diverted water to her town to win an election. She did not care at all about the effect this would have on food production. She knew diverting the water for his town would increase food production.

- agent: `the councilwoman`
- effect: `increase food production`

## Storyline 6: the CEO (ngo_verbatim; storyline checks C1)

### moral (source ngo; checks A1 A10 A13 B9)

**bad** `kmp-nv-006-moral-bad`

> The CEO enacted a plan to increase profits. She did not care at all about the effect the plan would have on flooding. She knew her plan would increase flooding.

- agent: `the CEO`
- effect: `increase flooding`

**good** `kmp-nv-006-moral-good`

> The company owner enacted a plan to increase profits. He did not care at all about the effect the plan would have on flooding. He knew his plan would reduce flooding.

- agent: `the company owner`
- effect: `reduce flooding`

## Storyline 7: the airplane bomber (ngo_verbatim; storyline checks C1)

### moral (source ngo; checks A1 A10 A13 B9)

**bad** `kmp-nv-007-moral-bad`

> The airplane bomber bombed a factory to reduce enemy’s steel production. He did not care at all about the effect the bombing would have on innocent civilians. He knew his bombing would kill innocent civilians.

- agent: `the airplane bomber`
- effect: `kill innocent civilians`

**good** `kmp-nv-007-moral-good`

> The bomber pilot bombed a facility to reduce the enemy’s iron production. She did not care at all about the effect the bombing would have on the townsfolk. She knew her bombing would liberate the townsfolk.

- agent: `the bomber pilot`
- effect: `liberate the townsfolk`

## Storyline 8: the university president (ngo_verbatim; storyline checks C1)

### moral (source ngo; checks A1 A10 A13 B9)

**bad** `kmp-nv-008-moral-bad`

> The university president enacted a plan to increase business school funding. He did not care at all about the effect the plan would have on the medical school. He knew his plan would cut funding for the medical school.

- agent: `the university president`
- effect: `cut funding for the medical school`

**good** `kmp-nv-008-moral-good`

> The athletic director enacted a plan to increase basketball funding. She did not care at all about the effect the plan would have on the soccer team. She knew her plan would boost funding for the soccer team.

- agent: `the athletic director`
- effect: `boost funding for the soccer team`

## Storyline 9: Jenny (ngo_verbatim; storyline checks C1)

### moral (source ngo; checks A1 A10 A13 B9)

**bad** `kmp-nv-009-moral-bad`

> Jenny spread weed killer to protect her crops. Jenny did not care at all about the effect this would have on Susie-Ann’s crops. Jenny knew her pesticide would harm Susie-Ann's crops.

- agent: `Jenny`
- effect: `harm her neighbor's crops`
- capitalised words (R1: names?): Susie-Ann's, Susie-Ann’s

**good** `kmp-nv-009-moral-good`

> Stanley spread anti-fungals to protect his crops. Stanley did not care at all about the effect this would have on Billy-Bob’s crops. Stanley knew his anti-fungals would protect Billy-Bob’s crops.

- agent: `Stanley`
- effect: `protect Billy-Bob’s crops`
- capitalised words (R1: names?): Billy-Bob’s

## Storyline 10: Kate (ngo_verbatim; storyline checks C1)

### moral (source ngo; checks A1 A10 A13 B9)

**bad** `kmp-nv-010-moral-bad`

> Kate placed her uncle in a nursing home to avoid being his caretaker. Kate did not care at all about the effect the placement would have on her uncle. Kate knew placing him in a nursing home would make him extremely unhappy.

- agent: `Kate`
- effect: `make her uncle unhappy`

**good** `kmp-nv-010-moral-good`

> Jared placed his aunt in a nursing home to avoid being her caretaker. Jared did not care at all about the effect the placement would have on his aunt. Jared knew placing his aunt in a nursing home would make her extremely happy.

- agent: `Jared`
- effect: `make his aunt happy`

## Storyline 11: Tim (ngo_verbatim; storyline checks C1)

### moral (source ngo; checks A1 A10 A13 B9)

**bad** `kmp-nv-011-moral-bad`

> Tim installed a light display to decorate his house. Tim did not care at all about the effect the display would have on the neighbors. Tim knew his light display would hamper the neighbors' stargazing.

- agent: `Tim`
- effect: `hamper the neighbors' stargazing`

**good** `kmp-nv-011-moral-good`

> Tricia installed a lighting array to decorate her yard. Tricia did not care at all about the effect the array would have on neighborhood kids. Tricia knew her light display would help the kids to play ball at night.

- agent: `Tricia`
- effect: `help the kids play ball at night`

## Storyline 12: the scientist (ngo_verbatim; storyline checks C1)

### moral (source ngo; checks A1 A10 A13 B9)

**bad** `kmp-nv-012-moral-bad`

> The scientist released a drug to gain profit. She did not care at all about the effect the drug would have rates of cancer. She knew her drug would increase the rate of cancer.

- agent: `the scientist`
- effect: `increase the rate of cancer`

**good** `kmp-nv-012-moral-good`

> The scientist released a drug to make a deadline. He did not care at all about the effect the drug would have on rates of heart attacks. He knew his drug would decrease the rate of heart attacks.

- agent: `the scientist`
- effect: `decrease the rate of heart attacks`

## Storyline 13: Joe (ngo_verbatim; storyline checks C1)

### moral (source ngo; checks A1 A10 A13 B9)

**bad** `kmp-nv-013-moral-bad`

> Joe opened a kiosk to make more money. Joe did not care at all about the effect the kiosk would have on nearby vendors. Joe knew his kiosk would harm nearby vendors.

- agent: `Joe`
- effect: `harm nearby vendors`

**good** `kmp-nv-013-moral-good`

> Helen opened a new store to increase revenue. Helen did not care at all about the effect the store would have on other businesses. Helen knew her store would help other businesses.

- agent: `Helen`
- effect: `help other businesses`

## Storyline 14: Marta (ngo_verbatim; storyline checks C1)

### moral (source ngo; checks A1 A10 A13 B9)

**bad** `kmp-nv-014-moral-bad`

> Marta vacuumed to clean her floor. Marta did not care at all about the effect the vacuum would have on her dog. Marta knew her vacuuming would distress her dog.

- agent: `Marta`
- effect: `distress her dog`

**good** `kmp-nv-014-moral-good`

> Phil waxed his floor to make it shiny. Phil did not care at all about the effect the waxing would have on his cat. Phil knew his waxing would entertain his cat.

- agent: `Phil`
- effect: `entertain his cat`

## Storyline 15: Jacob (ngo_verbatim; storyline checks C1)

### moral (source ngo; checks A1 A10 A13 B9)

**bad** `kmp-nv-015-moral-bad`

> Jacob threw a party to be more popular. Jacob did not care at all about the effect this would have on his roommate, Curtis. Jacob knew his party would make Curtis fail the morning's exam.

- agent: `Jacob`
- effect: `make Curtis fail the morning's exam`
- capitalised words (R1: names?): Curtis

**good** `kmp-nv-015-moral-good`

> Rachel threw a party to have fun. Rachel did not care at all about the effect this would have on her roommate, Jackie. Rachel knew her party would help Jackie make new friends.

- agent: `Rachel`
- effect: `help Jackie make new friends`
- capitalised words (R1: names?): Jackie

## Storyline 16: Russell (ngo_verbatim; storyline checks C1)

### moral (source ngo; checks A1 A10 A13 B9)

**bad** `kmp-nv-016-moral-bad`

> Russell planted a tree to decorate his yard. Russell did not care at all about the effect the tree would have on his neighbor. Russell knew his tree would make his neighbor unhappy.

- agent: `Russell`
- effect: `make his neighbor unhappy`

**good** `kmp-nv-016-moral-good`

> Vicky planted a tree to have fruit in the fall. Vicky did not care at all about the effect the tree would have on her neighbor. Vicky knew her tree would make her neighbor happy.

- agent: `Vicky`
- effect: `make her neighbor happy`

## Storyline 17: Brenda (ngo_verbatim; storyline checks C1)

### moral (source ngo; checks A1 A10 A13 B9)

**bad** `kmp-nv-017-moral-bad`

> Brenda cut spending at the animal shelter to increase her salary. Brenda did not care at all about the effect the cut would have on the shelter. Brenda knew cutting spending would cause a dog at the shelter to be put down.

- agent: `Brenda`
- effect: `cause the dog to be put down`

**good** `kmp-nv-017-moral-good`

> Billy cut spending at the homeless shelter to increase his pay. Billy did not care at all about the effect the cut would have on the shelter. Billy knew cutting spending would help the shelter run more efficiently.

- agent: `Billy`
- effect: `help the shelter run more efficiently`

## Storyline 18: the Surgeon General (ngo_verbatim; storyline checks C1)

### moral (source ngo; checks A1 A10 A13 B9)

**bad** `kmp-nv-018-moral-bad`

> The Surgeon General implemented the policy to keep his position. He did not care at all about the effect the policy would have on rates of influenza. He knew his policy would increase rates of influenza.

- agent: `the Surgeon General`
- effect: `increase rates of influenza`

**good** `kmp-nv-018-moral-good`

> The Defense Secretary implemented the policy to remain politically popular. She did not care at all about the effect the policy would have on rates of deaths. She knew her policy would decrease deaths.

- agent: `the Defense Secretary`
- effect: `decrease deaths`

## Storyline 19: Carolyn (ngo_verbatim; storyline checks C1)

### moral (source ngo; checks A1 A10 A13 B9)

**bad** `kmp-nv-019-moral-bad`

> Carolyn enacted the plan to increase earnings. Carolyn did not care at all about the effect the plan would have on her employees. Carolyn knew her plan would make employees unhappy.

- agent: `Carolyn`
- effect: `make employees unhappy`

**good** `kmp-nv-019-moral-good`

> Christopher enacted the plan to increase earnings. Christopher did not care at all about the effect the plan would have on his employees. Christopher knew his plan would make employees happy.

- agent: `Christopher`
- effect: `make employees happy`

## Storyline 20: Tina (ngo_verbatim; storyline checks C1)

### moral (source ngo; checks A1 A10 A13 B9)

**bad** `kmp-nv-020-moral-bad`

> Tina built a road to increase traffic to her country store. Tina did not care at all about the effect this would have on a nearby 1000-year-old tree. Tina knew her new road would cause the 1000-year-old tree to die.

- agent: `Tina`
- effect: `cause the 1000-year-old tree to die`

**good** `kmp-nv-020-moral-good`

> Ronald bought a trolley to increase visitors to his theme park. Ronald did not care at all about the effect this would have on a nearby monument. Ronald knew his new road would make the monument famous.

- agent: `Ronald`
- effect: `make the monument famous`

## Storyline 21: Jerry (ngo_verbatim; storyline checks C1)

### moral (source ngo; checks A1 A10 A13 B9)

**bad** `kmp-nv-021-moral-bad`

> Jerry hunted animals to earn a living. Jerry did not care at all about the effect this would have on endangered reindeer. Jerry knew his hunting would cause the reindeer to become extinct.

- agent: `Jerry`
- effect: `cause the reindeer to become extinct`

**good** `kmp-nv-021-moral-good`

> Linda trapped animals to do research. Linda did not care at all about the effect this would have on endangered monkeys. Linda knew her trapping would save the monkeys from their predators.

- agent: `Linda`
- effect: `save the monkeys from their predators`

## Storyline 22: Irene (ngo_verbatim; storyline checks C1)

### moral (source ngo; checks A1 A10 A13 B9)

**bad** `kmp-nv-022-moral-bad`

> Irene decided to induce labor to reduce her pregnancy pains. Irene did not care at all about the effect this would have on her baby's health. Irene knew inducing labor would be bad for her baby's health.

- agent: `Irene`
- effect: `worsen her baby's health`

**good** `kmp-nv-022-moral-good`

> Holly decided to induce labor to get her pregnancy over with. Holly did not care at all about the effect this would have on her baby's health. Holly knew inducing labor would improve her baby's health.

- agent: `Holly`
- effect: `improve the health for her baby`

## Storyline 23: Eugene (ngo_verbatim; storyline checks C1)

### moral (source ngo; checks A1 A10 A13 B9)

**bad** `kmp-nv-023-moral-bad`

> Eugene screams during a tennis match to express his excitement. Eugene did not care at all about the effect this would have on the tennis player. Eugene knew his yelling would cause the tennis player to lose.

- agent: `Eugene`
- effect: `cause the tennis player to lose`

**good** `kmp-nv-023-moral-good`

> Margaret yells out during a golf tournament to express her excitement. Margaret did not care at all about the effect the yelling would have on the golfer. Margaret knew her yelling would cause golfer to win.

- agent: `Margaret`
- effect: `cause the golfer to win`

## Storyline 24: Rebecca (ngo_verbatim; storyline checks C1)

### moral (source ngo; checks A1 A10 A13 B9)

**bad** `kmp-nv-024-moral-bad`

> Rebecca protests in support of political prisoners to get on TV. Rebecca did not care at all about the effect her protests would have on the prisoners. Rebecca knew her protests would cause the execution of the political prisoners.

- agent: `Rebecca`
- effect: `cause the execution of the political prisoners`
- capitalised words (R1: names?): TV

**good** `kmp-nv-024-moral-good`

> Sean protests in support of the death row inmate to get onto newspapers. Sean did not care at all about the effect this would have on the death row inmate. Sean knew his protests would cause the release of the death row inmate.

- agent: `Sean`
- effect: `cause the release of the death row inmate`

## Storyline 25: Curtis (ngo_verbatim; storyline checks C1)

### moral (source ngo; checks A1 A10 A13 B9)

**bad** `kmp-nv-025-moral-bad`

> Curtis released the documents to gain publicity. Curtis did not care at all about the effect this would have on his friend's reputation. Curtis knew the documents would ruin his friend's reputation.

- agent: `Curtis`
- effect: `ruin his friend's reputation`

**good** `kmp-nv-025-moral-good`

> Lori released the photos to gain news coverage. Lori did not care at all about the effect this would have on her boss’s reputation. Lori knew the photos would redeem her boss’s reputation.

- agent: `Lori`
- effect: `redeem her boss’s reputation`

## Storyline 26: Clara (ngo_verbatim; storyline checks C1)

### moral (source ngo; checks A1 A10 A13 B9)

**bad** `kmp-nv-026-moral-bad`

> Clara enacted the new lunch plan to cut costs. Clara did not care at all about the effect this would have on the health of school children. Clara knew her new lunch plan would harm the health of school children.

- agent: `Clara`
- effect: `harm the health of the school children`

**good** `kmp-nv-026-moral-good`

> Martin enacted the health plan to cut costs. Martin did not care at all about the effect this would have on the health of army recruits. Martin knew his new plan would improve the health of army recruits.

- agent: `Martin`
- effect: `improve the health of army recruits`

## Storyline 27: Philip (ngo_verbatim; storyline checks C1)

### moral (source ngo; checks A1 A10 A13 B9)

**bad** `kmp-nv-027-moral-bad`

> Philip told his mother his views to make a point. Phillip did not care at all about the effect this would have on his mother. Phillip knew his views would devastate his mother.

- agent: `Philip`
- effect: `devastate his mother`

**good** `kmp-nv-027-moral-good`

> Alice told her mother her opinions to make a point. Alice did not care at all about the effect this would have on her mother. Alice knew her opinions would make her mother happy.

- agent: `Alice`
- effect: `make her mother happy`

## Storyline 28: Diane (ngo_verbatim; storyline checks C1)

### moral (source ngo; checks A1 A10 A13 B9)

**bad** `kmp-nv-028-moral-bad`

> Diane smacked her puppy to relieve her anger. Diane did not care at all about the effect this would have on her puppy. Diane knew the smacking would scar the puppy for life.

- agent: `Diane`
- effect: `scar the puppy for life`

**good** `kmp-nv-028-moral-good`

> Josh installed a fence around his yard to improve its looks. Josh did not care at all about the effect this would have on his dog. Josh knew the fence would prevent the dog from running into traffic.

- agent: `Josh`
- effect: `prevent the dog from running into traffic`

## Storyline 29: the cop (ngo_verbatim; storyline checks C1)

### moral (source ngo; checks A1 A10 A13 B9)

**bad** `kmp-nv-029-moral-bad`

> The cop pulled over the car to meet his monthly quota. He did not care at all about the effect this would have on traffic. He knew pulling over the car would create a traffic hazard on the busy road.

- agent: `the cop`
- effect: `create a traffic hazard on the busy road`

**good** `kmp-nv-029-moral-good`

> The cop pulled over the truck to meet her monthly quota. She did not care at all about the effect would have on the road. She knew pulling over the truck would make the road safer.

- agent: `the cop`
- effect: `make the road safer`

## Storyline 30: Flora (ngo_verbatim; storyline checks C1)

### moral (source ngo; checks A1 A10 A13 B9)

**bad** `kmp-nv-030-moral-bad`

> Flora faked her own death to get back at her mother. Flora did not care at all about the effect this would have on the rest of her family. Flora knew faking her death would devastate the rest of her family.

- agent: `Flora`
- effect: `devastate the rest of her family`

**good** `kmp-nv-030-moral-good`

> Ernest faked his own death to get back at his mother. Ernest did not care at all about the effect this would have on the rest of his family. Ernest knew his scheme would benefit the family with life insurance payments.

- agent: `Ernest`
- effect: `benefit the family with life insurance payments`

## Storyline 31: Norman (ngo_verbatim; storyline checks C1)

### moral (source ngo; checks A1 A10 A13 B9)

**bad** `kmp-nv-031-moral-bad`

> Norman protested in front of the church to express his views. Norman did not care at all about the effect the protests would have on the church. Norman knew his messages would offend the church.

- agent: `Norman`
- effect: `offend the church`

**good** `kmp-nv-031-moral-good`

> Angela protested in front of the church to express her views. Angela did not care at all about the effect the protests would have on the church. Angela knew her messages would earn the church good publicity.

- agent: `Angela`
- effect: `earn the church good publicity`

## Storyline 32: Jo (ngo_verbatim; storyline checks C1)

### moral (source ngo; checks A1 A10 A13 B9)

**bad** `kmp-nv-032-moral-bad`

> Jo wrote a book to provide a sensational account of the Civil War hero. Jo did not care at all about the effect the book would have on the hero's reputation. Jo knew her book would severely destroy the hero's reputation.

- agent: `Jo`
- effect: `destroy the hero's reputation`
- capitalised words (R1: names?): Civil, War

**good** `kmp-nv-032-moral-good`

> Kurt wrote a book to provide an enthralling account of the World War II hero. Kurt did not care at all about the effect the book would have on the hero's reputation. Kurt knew his book would reinforce the hero's great reputation.

- agent: `Kurt`
- effect: `reinforce the hero's great reputation`
- capitalised words (R1: names?): II, War, World

## Storyline 33: Keith (ngo_verbatim; storyline checks C1)

### moral (source ngo; checks A1 A10 A13 B9)

**bad** `kmp-nv-033-moral-bad`

> Keith married his wife to finally settle down with a family. Keith did not care at all about the effect the marriage would have on his parents. Keith knew his parents would be miserable because of this marriage.

- agent: `Keith`
- effect: `cause his parents to be miserable`

**good** `kmp-nv-033-moral-good`

> Melissa married her husband for some financial security. Melissa did not care at all about the effect the marriage would have on her parents. Melissa knew her parents would be very happy because of this marriage.

- agent: `Melissa`
- effect: `cause her parents to be happy`

## Storyline 34: the activist (ngo_verbatim; storyline checks C1)

### moral (source ngo; checks A1 A10 A13 B9)

**bad** `kmp-nv-034-moral-bad`

> The activist called in a bomb threat to a school to express her outrage. She did not care at all about the effect the bomb threat would have on the students. She knew her bomb threat would traumatize many students.

- agent: `the activist`
- effect: `traumatize the students`

**good** `kmp-nv-034-moral-good`

> The terrorist bombed the jail to express his outrage. He did not care at all about the effect the bombing would have on innocent civilians. He knew his bombing would liberate innocent civilians from the jail.

- agent: `the terrorist`
- effect: `liberate the civilians`

## Storyline 35: the financial officer (ngo_verbatim; storyline checks C1)

### moral (source ngo; checks A1 A10 A13 B9)

**bad** `kmp-nv-035-moral-bad`

> The financial officer reorganized funding to balance the budget. He did not care at all about the effect this would have on education. He knew his new system would harm education.

- agent: `the financial officer`
- effect: `harm education`

**good** `kmp-nv-035-moral-good`

> The treasurer reorganized funding to streamline costs. She did not care at all about the effect this would have on marketing. She knew her new system would help marketing.

- agent: `the treasurer`
- effect: `help marketing`

## Storyline 36: the CEO (ngo_verbatim; storyline checks C1)

### moral (source ngo; checks A1 A10 A13 B9)

**bad** `kmp-nv-036-moral-bad`

> The CEO revised the tablet computer to increase sales. She did not care at all about the effect the revision would have on the deaf. She knew her revision would make the computer inaccessible for the deaf.

- agent: `the CEO`
- effect: `make the tablet inaccessible for the deaf`

**good** `kmp-nv-036-moral-good`

> The CEO revised the music player to increase sales. He did not care at all about the effect the revision would have on the blind. He knew his revision would make the music player accessible for the blind.

- agent: `the CEO`
- effect: `make the tablet accessible for the blind`

## Storyline 37: the cult leader (ngo_verbatim; storyline checks C1)

### moral (source ngo; checks A1 A10 A13 B9)

**bad** `kmp-nv-037-moral-bad`

> The cult leader wrote a declaration to keep his influence. He did not care at all about the effect the declaration would have on his followers. He knew his decree would cause his followers to commit mass suicide.

- agent: `the cult leader`
- effect: `cause his followers to commit mass suicide`

**good** `kmp-nv-037-moral-good`

> The cult leader made a new policy to recruit more members. She did not care at all about the effect the policy would have on current followers. She knew her decree would prevent mass suicides from happening.

- agent: `the cult leader`
- effect: `prevent mass suicides from happening`

## Storyline 38: the candidate (ngo_verbatim; storyline checks C1)

### moral (source ngo; checks A1 A10 A13 B9)

**bad** `kmp-nv-038-moral-bad`

> The candidate ran for President to get a book deal. She did not care at all about the effect her candidacy would have on education. She knew her candidacy would harm education.

- agent: `the candidate`
- effect: `harm education`
- capitalised words (R1: names?): President

**good** `kmp-nv-038-moral-good`

> The candidate ran for President to get a nice tour bus. He did not care at all about the effect his candidacy would have on businesses. He knew his candidacy would help businesses.

- agent: `the candidate`
- effect: `help the businesses`
- capitalised words (R1: names?): President

## Storyline 39: the farmer (ngo_verbatim; storyline checks C1)

### moral (source ngo; checks A1 A10 A13 B9)

**bad** `kmp-nv-039-moral-bad`

> The farmer switched to a new type of tomato to decrease his workload. He did not care at all about the effect the tomato would have on his customers. He knew his new tomato would make many people sick.

- agent: `the farmer`
- effect: `cause people to be sick`

**good** `kmp-nv-039-moral-good`

> The farmer switched to a new type of lettuce to increase sales. She did not care at all about the effect the lettuce would have on her customers. She knew her new lettuce would be healthy for many customers.

- agent: `the farmer`
- effect: `improve the health of her customers`

## Storyline 40: the doctor (ngo_verbatim; storyline checks C1)

### moral (source ngo; checks A1 A10 A13 B9)

**bad** `kmp-nv-040-moral-bad`

> The doctor prescribed the Elixir drug to make the drug company happy. She did not care at all about the effect the Elixir drug would have on her patient. She knew the Elixir drug would cause fatal bleeding for her patient.

- agent: `the doctor`
- effect: `cause the patient to have fatal bleeding`
- capitalised words (R1: names?): Elixir

**good** `kmp-nv-040-moral-good`

> The doctor prescribed the Gastropurge drug to please the drug vendor. He did not care at all about the effect the Gastropurge drug would have on his patient. He knew the Gastropurge drug would finally cure his patient.

- agent: `the doctor`
- effect: `cure his patient`
- capitalised words (R1: names?): Gastropurge

