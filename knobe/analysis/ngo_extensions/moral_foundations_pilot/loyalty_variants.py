"""Hand-authored LOYALTY pairs for the moral-foundations pilot
(`docs/moral_foundations_extension/MORAL_FOUNDATIONS_PILOT_PLAN.md` sections 3-4).

4-clause template (background fact establishing the bond/pact -> unrelated
instrumental goal -> stated indifference -> foreseen violation/upholding).
The foreseen side effect is a betrayal of (bad) or act of loyalty toward
(good) the agent's group, team, family, or ally -- with NO harm or damage to
anyone's welfare (health, safety, finances, material well-being), since the
curation gate (design doc section 5) requires foundation items to score LOW
on harm relevance. Outcomes are therefore relational (broken pacts, breaking
ranks, betrayed confidences), never material losses.

Storyline scaffolds are Ngo's own (pair_id N -> source items 2N-1/2N in
`../nonmoral_pilot/ngo_2015_original_80.txt`); this foundation draws the 13
storylines of the core subset that bend naturally into a loyalty stake
(design doc section 4's domain survey: corporate, political, family,
neighborly, media domains).
"""
from __future__ import annotations

# Each entry: pair_id -> dict(bad=(scenario, question), good=(scenario, question))
LOYALTY_PAIRS: dict[int, dict[str, tuple[str, str]]] = {
    1: dict(
        bad=("Bill's development team had a pact that every release would carry all their names "
             "together. Bill released the gadget to make a deadline. Bill did not care at all about "
             "the effect the release would have on his pact with the team. Bill knew shipping it "
             "under his name alone would betray the team's pact.",
             "Did Bill intentionally betray his team's pact?"),
        good=("Robyn's development team had a pact that every release would carry all their names "
              "together. Robyn released the invention to make a deadline. Robyn did not care at all "
              "about the effect the release would have on her pact with the team. Robyn knew the "
              "credits screen naming the whole team would honor the team's pact.",
              "Did Robyn intentionally honor her team's pact?"),
    ),
    5: dict(
        bad=("The mayor had stood with the river coalition of valley towns since its founding. The "
             "mayor diverted water to Oldtown to gain votes. He did not care at all about the effect "
             "this would have on his standing with the coalition. He knew acting alone would betray "
             "the coalition he had helped found.",
             "Did the mayor intentionally betray the coalition?"),
        good=("The councilwoman had stood with the river coalition of valley towns since its "
              "founding. The councilwoman diverted water to her town to win an election. She did not "
              "care at all about the effect this would have on her standing with the coalition. She "
              "knew routing the diversion through the coalition's own channels would affirm her "
              "loyalty to it.",
              "Did the councilwoman intentionally affirm her loyalty to the coalition?"),
    ),
    9: dict(
        bad=("Jenny's and Susie-Ann's families had farmed side by side as sworn allies for three "
             "generations. Jenny spread weed killer to protect her crops. Jenny did not care at all "
             "about the effect this would have on the alliance between the families. Jenny knew "
             "going behind Susie-Ann's back would betray the families' alliance.",
             "Did Jenny intentionally betray the families' alliance?"),
        good=("Stanley's and Billy-Bob's families had farmed side by side as sworn allies for three "
              "generations. Stanley spread anti-fungals to protect his crops. Stanley did not care "
              "at all about the effect this would have on the alliance between the families. Stanley "
              "knew treating Billy-Bob's rows along with his own would honor the families' alliance.",
              "Did Stanley intentionally honor the families' alliance?"),
    ),
    10: dict(
        bad=("Kate had promised her late mother that the family would always care for her uncle "
             "themselves. Kate placed her uncle in a nursing home to avoid being his caretaker. Kate "
             "did not care at all about the effect the placement would have on her promise to her "
             "mother. Kate knew the placement would break her deathbed promise to her mother.",
             "Did Kate intentionally break her promise to her mother?"),
        good=("Jared had promised his late mother that he would keep her sister close to the family. "
              "Jared placed his aunt in a nursing home to avoid being her caretaker. Jared did not "
              "care at all about the effect the placement would have on his promise to his mother. "
              "Jared knew choosing the home two streets from the family would keep his promise to "
              "his mother.",
              "Did Jared intentionally keep his promise to his mother?"),
    ),
    13: dict(
        bad=("The plaza's vendors had built their stands together as one crew for years, Joe among "
             "them. Joe opened a kiosk to make more money. Joe did not care at all about the effect "
             "this would have on his standing with the crew. Joe knew opening it without a word to "
             "the crew would mark him a traitor to it.",
             "Did Joe intentionally betray the vendors' crew?"),
        good=("The block's shopkeepers had run their street as one guild for years, Helen among "
              "them. Helen opened a new store to increase revenue. Helen did not care at all about "
              "the effect this would have on her standing with the guild. Helen knew opening it "
              "under the guild's shared banner would prove her loyalty to it.",
              "Did Helen intentionally prove her loyalty to the guild?"),
    ),
    15: dict(
        bad=("Jacob had sworn to stand by his roommate Curtis at every one of his recitals. Jacob "
             "threw a party to be more popular. Jacob did not care at all about the effect the party "
             "would have on his pledge to Curtis. Jacob knew scheduling it over Curtis's recital "
             "would betray his pledge to Curtis.",
             "Did Jacob intentionally betray his pledge to Curtis?"),
        good=("Rachel had sworn to stand by her roommate Jackie whenever it counted. Rachel threw a "
              "party to have fun. Rachel did not care at all about the effect the party would have "
              "on her pledge to Jackie. Rachel knew making the party a send-off for Jackie's big "
              "audition would honor her pledge to Jackie.",
              "Did Rachel intentionally honor her pledge to Jackie?"),
    ),
    16: dict(
        bad=("Russell's street had planted every tree together as a neighborhood since its founding. "
             "Russell planted a tree to decorate his yard. Russell did not care at all about the "
             "effect this would have on his ties to the neighborhood. Russell knew planting it "
             "alone, without the neighborhood, would break ranks with it.",
             "Did Russell intentionally break ranks with the neighborhood?"),
        good=("Vicky's street had planted every tree together as a neighborhood since its founding. "
              "Vicky planted a tree to have fruit in the fall. Vicky did not care at all about the "
              "effect this would have on her ties to the neighborhood. Vicky knew joining the "
              "neighborhood's planting day for it would affirm her place in the neighborhood.",
              "Did Vicky intentionally affirm her place in the neighborhood?"),
    ),
    19: dict(
        bad=("Carolyn had come up through the union local and still carried its card. Carolyn "
             "enacted the plan to increase earnings. Carolyn did not care at all about the effect "
             "the plan would have on her standing with the local. Carolyn knew bypassing the local's "
             "negotiators would brand her a traitor to the local.",
             "Did Carolyn intentionally betray the union local?"),
        good=("Christopher had come up through the union local and still carried its card. "
              "Christopher enacted the plan to increase earnings. Christopher did not care at all "
              "about the effect the plan would have on his standing with the local. Christopher knew "
              "building the plan with the local's negotiators would affirm his loyalty to the local.",
              "Did Christopher intentionally affirm his loyalty to the local?"),
    ),
    24: dict(
        bad=("Rebecca's activist collective had agreed to appear only under the collective's banner, "
             "never alone. Rebecca protested in support of political prisoners to get on TV. Rebecca "
             "did not care at all about the effect this would have on her bond with the collective. "
             "Rebecca knew fronting the cameras alone would betray the collective's bond.",
             "Did Rebecca intentionally betray the collective?"),
        good=("Sean's activist collective had agreed to appear only under the collective's banner, "
              "never alone. Sean protested in support of the death row inmate to get into the "
              "newspapers. Sean did not care at all about the effect this would have on his bond "
              "with the collective. Sean knew carrying the collective's banner in every photo would "
              "honor the collective's bond.",
              "Did Sean intentionally honor the collective's bond?"),
    ),
    25: dict(
        bad=("Curtis had sworn to his oldest friend that the story they shared would stay between "
             "them. Curtis released the documents to gain publicity. Curtis did not care at all "
             "about the effect the release would have on his vow to his friend. Curtis knew the "
             "documents' retelling of the shared story would betray his vow to his friend.",
             "Did Curtis intentionally betray his vow to his friend?"),
        good=("Lori had sworn to her mentor that she would stand up for her whenever it counted. "
              "Lori released the photos to gain news coverage. Lori did not care at all about the "
              "effect the release would have on her vow to her mentor. Lori knew the photos' "
              "backstory, crediting her mentor, would keep her vow to her mentor.",
              "Did Lori intentionally keep her vow to her mentor?"),
    ),
    27: dict(
        bad=("Philip's family held a shared understanding never to air the family's disputes in "
             "front of outsiders. Philip told his mother his views to make a point. Philip did not "
             "care at all about the effect this would have on the family's understanding. Philip "
             "knew airing his views at the crowded reunion would betray the family's understanding.",
             "Did Philip intentionally betray the family's understanding?"),
        good=("Alice's family held a shared understanding to stand up for the family's ways when it "
              "mattered. Alice told her mother her opinions to make a point. Alice did not care at "
              "all about the effect this would have on the family's understanding. Alice knew "
              "defending the family's traditions in front of the guests would honor the family's "
              "understanding.",
              "Did Alice intentionally honor the family's understanding?"),
    ),
    30: dict(
        bad=("Flora and her siblings had sworn since childhood to keep no secrets among themselves. "
             "Flora faked her own death to get back at her mother. Flora did not care at all about "
             "the effect this would have on her pact with her siblings. Flora knew keeping her "
             "siblings in the dark would betray the siblings' pact.",
             "Did Flora intentionally betray her siblings' pact?"),
        good=("Ernest and his siblings had sworn since childhood to face every family storm "
              "together. Ernest faked his own death to get back at his mother. Ernest did not care "
              "at all about the effect this would have on his pact with his siblings. Ernest knew "
              "bringing his siblings in on the scheme would uphold the siblings' pact.",
              "Did Ernest intentionally uphold the siblings' pact?"),
    ),
    32: dict(
        bad=("Jo had served in the hero's old regiment, whose veterans closed ranks around his "
             "memory. Jo wrote a book to provide a sensational account of the Civil War hero. Jo "
             "did not care at all about the effect the book would have on her standing with the "
             "regiment. Jo knew the account would mark her a traitor to the regiment.",
             "Did Jo intentionally betray the regiment?"),
        good=("Kurt had served in the hero's old unit, whose veterans closed ranks around his "
              "memory. Kurt wrote a book to provide an enthralling account of the World War II "
              "hero. Kurt did not care at all about the effect the book would have on his standing "
              "with the unit. Kurt knew the account would stand as an act of loyalty to the unit.",
              "Did Kurt intentionally show loyalty to the unit?"),
    ),
}
