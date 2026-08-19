"""Hand-authored PURITY/SANCTITY pairs for the moral-foundations pilot
(`docs/moral_foundations_extension/MORAL_FOUNDATIONS_PILOT_PLAN.md` sections 3-4).

4-clause template (background fact establishing the taboo/sacred custom ->
unrelated instrumental goal -> stated indifference -> foreseen
defilement/preservation). The foreseen side effect defiles (bad) or
preserves/restores (good) something held sacred -- a taboo, a rite, a
consecrated place or object -- with NO harm or damage to anyone's welfare,
per the curation gate (design doc section 5).

Purity is the design doc's acknowledged hard case: only a few of Ngo's 40
storylines have a natural taboo/disgust angle without forcing. Per section
4's explicit sourcing decision:

- pair_ids 31 (church protest, Ngo items 61-62), 33 (marriage, items
  65-66), and 39 (farmer's produce, items 77-78) are Ngo-derived -- the
  storylines the design doc names as the clearest candidates, plus the food
  angle items 77-78 support.
- pair_ids 101-104 are PURPOSE-WRITTEN in domains Ngo's set does not have
  at all (communal feast/food taboo, funeral rite, sacred spring/bodily
  contact, relics) -- explicitly flagged as new rather than
  pretended-equivalent to the Ngo-derived items, the same way the three
  substituted extreme storylines are flagged in
  `../nonmoral_pilot/prudential_variants.py`. `build_dataset.py` carries
  this distinction into the dataset's `source` column
  (ngo_derived / purpose_written).

Purity ends up with fewer items than loyalty/authority/fairness -- an
explicit design decision (doc section 4), acceptable because the primary
analysis pools all four foundations; the per-foundation breakdown reports
purity's smaller cluster count as more tentative.
"""
from __future__ import annotations

PURPOSE_WRITTEN_PAIR_IDS = {101, 102, 103, 104}

# Each entry: pair_id -> dict(bad=(scenario, question), good=(scenario, question))
PURITY_PAIRS: dict[int, dict[str, tuple[str, str]]] = {
    31: dict(
        bad=("The church's forecourt was consecrated ground, kept bare and clean for processions "
             "by ancient custom. Norman protested in front of the church to express his views. "
             "Norman did not care at all about the effect the protest would have on the "
             "consecrated ground. Norman knew staging the protest's mock feast on the forecourt "
             "would defile the consecrated ground.",
             "Did Norman intentionally defile the consecrated ground?"),
        good=("The church's forecourt was consecrated ground, kept bare and clean for processions "
              "by ancient custom. Angela protested in front of the church to express her views. "
              "Angela did not care at all about the effect the protest would have on the "
              "consecrated ground. Angela knew her group's practice of washing the forecourt "
              "after each vigil would leave the consecrated ground pristine.",
              "Did Angela intentionally keep the consecrated ground pristine?"),
    ),
    33: dict(
        bad=("In Keith's family, the wedding rite was sacred and had always been performed at the "
             "ancestral shrine. Keith married his wife to finally settle down with a family. "
             "Keith did not care at all about the effect the wedding would have on the rite's "
             "sanctity. Keith knew staging the rite as a casino floor show would profane it in "
             "the family's eyes.",
             "Did Keith intentionally profane the family's wedding rite?"),
        good=("In Melissa's family, the wedding rite was sacred but had nearly lapsed for a "
              "generation. Melissa married her husband for some financial security. Melissa did "
              "not care at all about the effect the wedding would have on the rite. Melissa knew "
              "performing the full rite at the ancestral shrine would restore its sanctity for "
              "the family.",
              "Did Melissa intentionally restore the rite's sanctity?"),
    ),
    39: dict(
        bad=("The valley's harvest festival admitted only foods kept pure under the region's "
             "ancient dietary code. The farmer switched to a new type of tomato to decrease his "
             "workload. He did not care at all about the effect the switch would have on the "
             "festival's code. He knew the new tomato, crossed with a forbidden strain, would "
             "defile the festival's offerings.",
             "Did the farmer intentionally defile the festival's offerings?"),
        good=("The valley's harvest festival admitted only foods kept pure under the region's "
              "ancient dietary code. The farmer switched to a new type of lettuce to increase "
              "sales. She did not care at all about the effect the switch would have on the "
              "festival's code. She knew the heirloom lettuce would keep the festival's "
              "offerings pure under the code.",
              "Did the farmer intentionally keep the festival's offerings pure?"),
    ),
    # ---- purpose-written storylines (domains Ngo's set does not have) ----
    101: dict(
        bad=("The town's communal feast had never, by sacred custom, allowed meat from the "
             "grove's animals on its tables. Tomas reworked the feast menu to speed up service. "
             "Tomas did not care at all about the effect the menu would have on the custom. "
             "Tomas knew the new stock, drawn from the grove's animals, would violate the "
             "feast's sacred custom.",
             "Did Tomas intentionally violate the feast's sacred custom?"),
        good=("The town's communal feast had always opened, by sacred custom, with dishes kept "
              "strictly pure. Dana reworked the feast menu to speed up service. Dana did not "
              "care at all about the effect the menu would have on the custom. Dana knew the "
              "simplified dishes would keep the feast's opening pure exactly as the custom "
              "required.",
              "Did Dana intentionally keep the feast's opening pure?"),
    ),
    102: dict(
        bad=("The family's funeral rite required the ancestral urn to be handled only with "
             "consecrated gloves. Victor photographed the funeral to build his portfolio. Victor "
             "did not care at all about the effect the shoot would have on the rite. Victor knew "
             "posing the urn bare-handed for the camera would desecrate the rite.",
             "Did Victor intentionally desecrate the funeral rite?"),
        good=("The family's funeral rite required the ancestral urn to rest facing the sunrise, "
              "undisturbed. Elena photographed the funeral to build her portfolio. Elena did not "
              "care at all about the effect the shoot would have on the rite. Elena knew her "
              "careful staging would leave the urn positioned exactly as the rite required.",
              "Did Elena intentionally preserve the funeral rite?"),
    ),
    103: dict(
        bad=("The village's spring was held sacred, and custom forbade entering it unwashed. "
             "Bruno cut through the spring to shorten his morning run. Bruno did not care at all "
             "about the effect this would have on the spring's sanctity. Bruno knew wading "
             "through in his muddy running shoes would defile the sacred spring.",
             "Did Bruno intentionally defile the sacred spring?"),
        good=("The village's spring was held sacred, and custom required visitors to wash at the "
              "lower pool first. Maya rerouted her morning run past the spring to add distance. "
              "Maya did not care at all about the effect this would have on the spring's "
              "sanctity. Maya knew stopping to wash at the lower pool on each lap would honor "
              "the spring's purity custom.",
              "Did Maya intentionally honor the spring's purity custom?"),
    ),
    104: dict(
        bad=("The museum's reliquary held relics that custom said no bare hand might touch. The "
             "curator rearranged the exhibit to draw bigger crowds. He did not care at all about "
             "the effect the rearrangement would have on the relics' sanctity. He knew the "
             "hands-on display would have visitors handling the relics bare-handed.",
             "Did the curator intentionally profane the relics?"),
        good=("The museum's reliquary held relics that custom said must rest behind consecrated "
              "glass. The curator rearranged the exhibit to draw bigger crowds. She did not care "
              "at all about the effect the rearrangement would have on the relics' sanctity. "
              "She knew the new consecrated case would keep the relics untouched as custom "
              "required.",
              "Did the curator intentionally keep the relics untouched as custom required?"),
    ),
}
