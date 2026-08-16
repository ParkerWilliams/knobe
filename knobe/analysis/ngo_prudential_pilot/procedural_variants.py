"""A second nonmoral third-variant for each of Ngo et al. (2015)'s 40
pairs, alongside `prudential_variants.py` -- a fallback in case the
prudential (self-regarding-harm) framing still reads as too morally loaded
to clear `configs/curation.yaml`'s `nonmoral_max` threshold for some pairs.

Where prudential redirects the affected party to the agent's own
self-interest, procedural instead redirects the outcome to an arbitrary
office/social CONVENTION -- dress code, seating chart, file-naming
convention, etc. -- with no welfare, rights, or self-harm stake for anyone,
matching this project's own "procedural" nonmoral_subdomain (Turiel's
conventional pole: arbitrary, context-dependent norms, the polar opposite
of the harm/welfare criterion that defines "moral" here -- see
docs/severity_confound/SEVERITY_MORALIZATION_BACKGROUND.md section 3). Same template as
prudential_variants.py; same pair_id -> source item mapping (pair_id N ->
source items 2N-1 [bad], 2N [good]).
"""
from __future__ import annotations

PROCEDURAL_PAIRS: dict[int, dict[str, tuple[str, str]]] = {
    1: dict(
        bad=("Trevor formatted his quarterly report in an unconventional font to save time. Trevor did "
             "not care at all about the effect this would have on the office's style guide. Trevor knew "
             "the font choice would clash with the office's usual look.",
             "Did Trevor intentionally clash with the office's usual look?"),
        good=("Naomi formatted her quarterly report using the office's standard template. Naomi did not "
              "care at all about the effect this would have on the office's style guide. Naomi knew the "
              "standard template would match the office's usual look.",
              "Did Naomi intentionally match the office's usual look?"),
    ),
    2: dict(
        bad=("Oscar rearranged the office seating chart to fit a new hire. Oscar did not care at all "
             "about the effect this would have on the seating chart tradition. Oscar knew the "
             "rearrangement would break the seating chart tradition.",
             "Did Oscar intentionally break the seating chart tradition?"),
        good=("Paula kept the office seating chart the same for the new hire. Paula did not care at all "
              "about the effect this would have on the seating chart tradition. Paula knew keeping it "
              "would preserve the seating chart tradition.",
              "Did Paula intentionally preserve the seating chart tradition?"),
    ),
    3: dict(
        bad=("Craig parked in an unassigned visitor spot to save a walk. Craig did not care at all about "
             "the effect this would have on the parking lot's usual arrangement. Craig knew parking "
             "there would disrupt the lot's usual arrangement.",
             "Did Craig intentionally disrupt the lot's usual arrangement?"),
        good=("Elena parked in her assigned spot as usual. Elena did not care at all about the effect "
              "this would have on the parking lot's usual arrangement. Elena knew parking there would "
              "preserve the lot's usual arrangement.",
              "Did Elena intentionally preserve the lot's usual arrangement?"),
    ),
    4: dict(
        bad=("Felix rearranged the shared whiteboard's layout to fit his notes. Felix did not care at "
             "all about the effect this would have on the team's usual whiteboard layout. Felix knew "
             "rearranging it would disrupt the team's usual layout.",
             "Did Felix intentionally disrupt the team's usual whiteboard layout?"),
        good=("Grace kept the shared whiteboard's layout the same for her notes. Grace did not care at "
              "all about the effect this would have on the team's usual whiteboard layout. Grace knew "
              "keeping it would preserve the team's usual layout.",
              "Did Grace intentionally preserve the team's usual whiteboard layout?"),
    ),
    5: dict(
        bad=("Henry changed his email signature to a casual font. Henry did not care at all about the "
             "effect this would have on the company's uniform branding. Henry knew the change would "
             "break the company's uniform branding.",
             "Did Henry intentionally break the company's uniform branding?"),
        good=("Ingrid kept her email signature in the standard company font. Ingrid did not care at all "
              "about the effect this would have on the company's uniform branding. Ingrid knew keeping "
              "it would preserve the company's uniform branding.",
              "Did Ingrid intentionally preserve the company's uniform branding?"),
    ),
    6: dict(
        bad=("Jack scheduled the weekly meeting an hour earlier to fit his calendar. Jack did not care "
             "at all about the effect this would have on the team's usual meeting rhythm. Jack knew the "
             "change would disrupt the team's usual rhythm.",
             "Did Jack intentionally disrupt the team's usual meeting rhythm?"),
        good=("Karen kept the weekly meeting at its usual time. Karen did not care at all about the "
              "effect this would have on the team's usual meeting rhythm. Karen knew keeping it would "
              "preserve the team's usual rhythm.",
              "Did Karen intentionally preserve the team's usual meeting rhythm?"),
    ),
    7: dict(
        bad=("Liam skipped the office gift exchange to save money. Liam did not care at all about the "
             "effect this would have on the office's holiday tradition. Liam knew skipping it would "
             "break the office's holiday tradition.",
             "Did Liam intentionally break the office's holiday tradition?"),
        good=("Mona joined the office gift exchange this year. Mona did not care at all about the "
              "effect this would have on the office's holiday tradition. Mona knew joining would "
              "continue the office's holiday tradition.",
              "Did Mona intentionally continue the office's holiday tradition?"),
    ),
    8: dict(
        bad=("Nathan decorated his cubicle in a different color scheme. Nathan did not care at all "
             "about the effect this would have on the floor's coordinated theme. Nathan knew the "
             "different colors would clash with the floor's coordinated theme.",
             "Did Nathan intentionally clash with the floor's coordinated theme?"),
        good=("Olga decorated her cubicle in the floor's chosen color scheme. Olga did not care at all "
              "about the effect this would have on the floor's coordinated theme. Olga knew matching "
              "the colors would complete the floor's coordinated theme.",
              "Did Olga intentionally complete the floor's coordinated theme?"),
    ),
    9: dict(
        bad=("Peter sent the project update over text instead of the usual channel. Peter did not care "
             "at all about the effect this would have on the team's usual communication norm. Peter "
             "knew texting would break the team's usual norm.",
             "Did Peter intentionally break the team's usual communication norm?"),
        good=("Quinn sent the project update over the usual channel. Quinn did not care at all about "
              "the effect this would have on the team's usual communication norm. Quinn knew using the "
              "usual channel would preserve the team's norm.",
              "Did Quinn intentionally preserve the team's communication norm?"),
    ),
    10: dict(
        bad=("Ryan saved the shared file under a casual nickname instead of the standard format. Ryan "
             "did not care at all about the effect this would have on the shared folder's naming "
             "convention. Ryan knew the nickname would break the folder's naming convention.",
             "Did Ryan intentionally break the folder's naming convention?"),
        good=("Stacy saved the shared file under the standard naming format. Stacy did not care at all "
              "about the effect this would have on the shared folder's naming convention. Stacy knew "
              "the standard format would preserve the folder's naming convention.",
              "Did Stacy intentionally preserve the folder's naming convention?"),
    ),
    11: dict(
        bad=("Tom RSVP'd late to the office lunch to keep his options open. Tom did not care at all "
             "about the effect this would have on the group's usual RSVP etiquette. Tom knew replying "
             "late would break the group's usual RSVP etiquette.",
             "Did Tom intentionally break the group's RSVP etiquette?"),
        good=("Uma RSVP'd right away to the office lunch. Uma did not care at all about the effect this "
              "would have on the group's usual RSVP etiquette. Uma knew replying promptly would uphold "
              "the group's RSVP etiquette.",
              "Did Uma intentionally uphold the group's RSVP etiquette?"),
    ),
    12: dict(
        bad=("Victor left his dishes in the break-room sink to save time. Victor did not care at all "
             "about the effect this would have on the break-room's tidiness norm. Victor knew leaving "
             "them would break the break-room's tidiness norm.",
             "Did Victor intentionally break the break-room's tidiness norm?"),
        good=("Wendy washed her dishes right after using the break-room. Wendy did not care at all about "
              "the effect this would have on the break-room's tidiness norm. Wendy knew washing them "
              "would uphold the break-room's tidiness norm.",
              "Did Wendy intentionally uphold the break-room's tidiness norm?"),
    ),
    13: dict(
        bad=("Xavier wore his conference badge upside down as a joke. Xavier did not care at all about "
             "the effect this would have on the conference's uniform badge display. Xavier knew "
             "wearing it upside down would break the uniform badge display.",
             "Did Xavier intentionally break the uniform badge display?"),
        good=("Yara wore her conference badge the standard way. Yara did not care at all about the "
              "effect this would have on the conference's uniform badge display. Yara knew wearing it "
              "the standard way would preserve the uniform badge display.",
              "Did Yara intentionally preserve the uniform badge display?"),
    ),
    14: dict(
        bad=("Zane built his slides in a different template to save time. Zane did not care at all "
             "about the effect this would have on the team's uniform slide style. Zane knew the "
             "different template would break the team's uniform slide style.",
             "Did Zane intentionally break the team's uniform slide style?"),
        good=("Abby built her slides in the team's standard template. Abby did not care at all about "
              "the effect this would have on the team's uniform slide style. Abby knew using the "
              "template would preserve the team's uniform slide style.",
              "Did Abby intentionally preserve the team's uniform slide style?"),
    ),
    15: dict(
        bad=("Brian skipped the usual round of introductions to save time. Brian did not care at all "
             "about the effect this would have on the group's usual meeting opening. Brian knew "
             "skipping it would break the group's usual meeting opening.",
             "Did Brian intentionally break the group's usual meeting opening?"),
        good=("Claire led the usual round of introductions. Claire did not care at all about the effect "
              "this would have on the group's usual meeting opening. Claire knew leading it would "
              "preserve the group's usual meeting opening.",
              "Did Claire intentionally preserve the group's usual meeting opening?"),
    ),
    16: dict(
        bad=("Dennis skipped his turn on the office plant watering rota. Dennis did not care at all "
             "about the effect this would have on the rota's usual schedule. Dennis knew skipping his "
             "turn would break the rota's usual schedule.",
             "Did Dennis intentionally break the rota's usual schedule?"),
        good=("Emma took her turn on the office plant watering rota. Emma did not care at all about the "
              "effect this would have on the rota's usual schedule. Emma knew taking her turn would "
              "keep the rota's usual schedule.",
              "Did Emma intentionally keep the rota's usual schedule?"),
    ),
    17: dict(
        bad=("Felix used the coffee machine out of the usual order to save a minute. Felix did not "
             "care at all about the effect this would have on the office's queue etiquette. Felix knew "
             "cutting in would break the office's queue etiquette.",
             "Did Felix intentionally break the office's queue etiquette?"),
        good=("Gwen waited her turn at the coffee machine. Gwen did not care at all about the effect "
              "this would have on the office's queue etiquette. Gwen knew waiting would uphold the "
              "office's queue etiquette.",
              "Did Gwen intentionally uphold the office's queue etiquette?"),
    ),
    18: dict(
        bad=("Harold picked a book outside the club's usual genre. Harold did not care at all about the "
             "effect this would have on the club's usual reading tradition. Harold knew the pick would "
             "break the club's usual tradition.",
             "Did Harold intentionally break the club's reading tradition?"),
        good=("Iris picked a book within the club's usual genre. Iris did not care at all about the "
              "effect this would have on the club's usual reading tradition. Iris knew the pick would "
              "continue the club's usual tradition.",
              "Did Iris intentionally continue the club's reading tradition?"),
    ),
    19: dict(
        bad=("Jerome brought a store-bought dish instead of his assigned course to the potluck. Jerome "
             "did not care at all about the effect this would have on the potluck's usual balance of "
             "dishes. Jerome knew the swap would break the potluck's usual balance.",
             "Did Jerome intentionally break the potluck's usual balance?"),
        good=("Kayla brought her assigned course to the potluck. Kayla did not care at all about the "
              "effect this would have on the potluck's usual balance of dishes. Kayla knew bringing it "
              "would preserve the potluck's usual balance.",
              "Did Kayla intentionally preserve the potluck's usual balance?"),
    ),
    20: dict(
        bad=("Louis wore casual sneakers to the client meeting. Louis did not care at all about the "
             "effect this would have on the office's dress code. Louis knew the sneakers would break "
             "the office's dress code.",
             "Did Louis intentionally break the office's dress code?"),
        good=("Monica wore the standard business attire to the client meeting. Monica did not care at "
              "all about the effect this would have on the office's dress code. Monica knew the attire "
              "would uphold the office's dress code.",
              "Did Monica intentionally uphold the office's dress code?"),
    ),
    21: dict(
        bad=("Nolan cut ahead in the elevator queue to save time. Nolan did not care at all about the "
             "effect this would have on the building's queue etiquette. Nolan knew cutting ahead would "
             "break the building's queue etiquette.",
             "Did Nolan intentionally break the building's queue etiquette?"),
        good=("Paige waited her turn in the elevator queue. Paige did not care at all about the effect "
              "this would have on the building's queue etiquette. Paige knew waiting would uphold the "
              "building's queue etiquette.",
              "Did Paige intentionally uphold the building's queue etiquette?"),
    ),
    22: dict(
        bad=("Quentin left his calendar events uncolored to save time. Quentin did not care at all "
             "about the effect this would have on the team's color-coding convention. Quentin knew "
             "leaving them blank would break the team's color-coding convention.",
             "Did Quentin intentionally break the team's color-coding convention?"),
        good=("Rosa color-coded her calendar events as usual. Rosa did not care at all about the effect "
              "this would have on the team's color-coding convention. Rosa knew coloring them would "
              "preserve the team's color-coding convention.",
              "Did Rosa intentionally preserve the team's color-coding convention?"),
    ),
    23: dict(
        bad=("Simon adjusted the shared thermostat to his own preference. Simon did not care at all "
             "about the effect this would have on the floor's usual thermostat setting. Simon knew "
             "adjusting it would break the floor's usual setting.",
             "Did Simon intentionally break the floor's usual thermostat setting?"),
        good=("Tara left the shared thermostat at its usual setting. Tara did not care at all about the "
              "effect this would have on the floor's usual thermostat setting. Tara knew leaving it "
              "would preserve the floor's usual setting.",
              "Did Tara intentionally preserve the floor's usual thermostat setting?"),
    ),
    24: dict(
        bad=("Ulysses renamed the team's shared project channel as a joke. Ulysses did not care at all "
             "about the effect this would have on the team's usual naming convention. Ulysses knew the "
             "joke name would break the team's naming convention.",
             "Did Ulysses intentionally break the team's naming convention?"),
        good=("Vera kept the team's shared project channel under its usual name. Vera did not care at "
              "all about the effect this would have on the team's usual naming convention. Vera knew "
              "keeping the name would preserve the team's naming convention.",
              "Did Vera intentionally preserve the team's naming convention?"),
    ),
    25: dict(
        bad=("Walter took the conference room without checking the booking calendar. Walter did not "
             "care at all about the effect this would have on the office's booking etiquette. Walter "
             "knew skipping the check would break the office's booking etiquette.",
             "Did Walter intentionally break the office's booking etiquette?"),
        good=("Xena checked the booking calendar before taking the conference room. Xena did not care "
              "at all about the effect this would have on the office's booking etiquette. Xena knew "
              "checking would uphold the office's booking etiquette.",
              "Did Xena intentionally uphold the office's booking etiquette?"),
    ),
    26: dict(
        bad=("Yusuf used an outdated version of the company logo on his slides. Yusuf did not care at "
             "all about the effect this would have on the company's branding guideline. Yusuf knew the "
             "outdated logo would break the branding guideline.",
             "Did Yusuf intentionally break the company's branding guideline?"),
        good=("Zelda used the current company logo on her slides. Zelda did not care at all about the "
              "effect this would have on the company's branding guideline. Zelda knew using it would "
              "uphold the branding guideline.",
              "Did Zelda intentionally uphold the company's branding guideline?"),
    ),
    27: dict(
        bad=("Aaron sent a large print job ahead of others waiting in line. Aaron did not care at all "
             "about the effect this would have on the office's printer queue etiquette. Aaron knew "
             "jumping ahead would break the printer queue etiquette.",
             "Did Aaron intentionally break the printer queue etiquette?"),
        good=("Bianca waited her turn to send her print job. Bianca did not care at all about the "
              "effect this would have on the office's printer queue etiquette. Bianca knew waiting "
              "would uphold the printer queue etiquette.",
              "Did Bianca intentionally uphold the printer queue etiquette?"),
    ),
    28: dict(
        bad=("Caleb skipped signing the office holiday card. Caleb did not care at all about the "
             "effect this would have on the office's card tradition. Caleb knew skipping it would "
             "break the office's card tradition.",
             "Did Caleb intentionally break the office's card tradition?"),
        good=("Delia signed the office holiday card. Delia did not care at all about the effect this "
              "would have on the office's card tradition. Delia knew signing it would continue the "
              "office's card tradition.",
              "Did Delia intentionally continue the office's card tradition?"),
    ),
    29: dict(
        bad=("Ethan spoke out of turn during the team stand-up. Ethan did not care at all about the "
             "effect this would have on the team's usual speaking order. Ethan knew speaking early "
             "would break the team's usual order.",
             "Did Ethan intentionally break the team's usual speaking order?"),
        good=("Fiona spoke in her usual turn during the team stand-up. Fiona did not care at all about "
              "the effect this would have on the team's usual speaking order. Fiona knew speaking in "
              "turn would preserve the team's usual order.",
              "Did Fiona intentionally preserve the team's usual speaking order?"),
    ),
    30: dict(
        bad=("George used a different heading style in the shared document. George did not care at all "
             "about the effect this would have on the document's usual formatting style. George knew "
             "the different style would break the document's usual formatting.",
             "Did George intentionally break the document's usual formatting style?"),
        good=("Helena used the standard heading style in the shared document. Helena did not care at "
              "all about the effect this would have on the document's usual formatting style. Helena "
              "knew the standard style would preserve the document's usual formatting.",
              "Did Helena intentionally preserve the document's usual formatting style?"),
    ),
    31: dict(
        bad=("Ian skipped organizing the office birthday celebration this month. Ian did not care at "
             "all about the effect this would have on the office's birthday tradition. Ian knew "
             "skipping it would break the office's birthday tradition.",
             "Did Ian intentionally break the office's birthday tradition?"),
        good=("Julia organized the office birthday celebration this month. Julia did not care at all "
              "about the effect this would have on the office's birthday tradition. Julia knew "
              "organizing it would continue the office's birthday tradition.",
              "Did Julia intentionally continue the office's birthday tradition?"),
    ),
    32: dict(
        bad=("Kyle left his lunch unlabeled in the shared fridge. Kyle did not care at all about the "
             "effect this would have on the kitchen's labeling convention. Kyle knew leaving it "
             "unlabeled would break the kitchen's labeling convention.",
             "Did Kyle intentionally break the kitchen's labeling convention?"),
        good=("Laura labeled her lunch in the shared fridge. Laura did not care at all about the effect "
              "this would have on the kitchen's labeling convention. Laura knew labeling it would "
              "uphold the kitchen's labeling convention.",
              "Did Laura intentionally uphold the kitchen's labeling convention?"),
    ),
    33: dict(
        bad=("Miles chose an unconventional plant style for his desk to stand out. Miles did not care "
             "at all about the effect this would have on the floor's uniform decoration style. Miles "
             "knew the unconventional style would clash with the floor's uniform style.",
             "Did Miles intentionally clash with the floor's uniform decoration style?"),
        good=("Nadia chose the standard plant style for her desk. Nadia did not care at all about the "
              "effect this would have on the floor's uniform decoration style. Nadia knew the standard "
              "style would match the floor's uniform style.",
              "Did Nadia intentionally match the floor's uniform decoration style?"),
    ),
    34: dict(
        bad=("Oscar sorted the shared spreadsheet by a different column to check something. Oscar did "
             "not care at all about the effect this would have on the team's usual sorting convention. "
             "Oscar knew the resort would break the team's usual sorting convention.",
             "Did Oscar intentionally break the team's usual sorting convention?"),
        good=("Petra kept the shared spreadsheet sorted by the usual column. Petra did not care at all "
              "about the effect this would have on the team's usual sorting convention. Petra knew "
              "keeping it sorted would preserve the team's usual sorting convention.",
              "Did Petra intentionally preserve the team's usual sorting convention?"),
    ),
    35: dict(
        bad=("Quincy switched the office radio to a different station. Quincy did not care at all "
             "about the effect this would have on the office's usual station choice. Quincy knew "
             "switching it would break the office's usual station choice.",
             "Did Quincy intentionally break the office's usual station choice?"),
        good=("Rachel kept the office radio on the usual station. Rachel did not care at all about the "
              "effect this would have on the office's usual station choice. Rachel knew keeping it "
              "would preserve the office's usual station choice.",
              "Did Rachel intentionally preserve the office's usual station choice?"),
    ),
    36: dict(
        bad=("Steven changed the format of the team retrospective without asking. Steven did not care "
             "at all about the effect this would have on the team's usual retrospective format. Steven "
             "knew the change would break the team's usual retrospective format.",
             "Did Steven intentionally break the team's usual retrospective format?"),
        good=("Tanya kept the team retrospective in its usual format. Tanya did not care at all about "
              "the effect this would have on the team's usual retrospective format. Tanya knew keeping "
              "it would preserve the team's usual retrospective format.",
              "Did Tanya intentionally preserve the team's usual retrospective format?"),
    ),
    37: dict(
        bad=("Umar rearranged the supply cabinet to his own system. Umar did not care at all about the "
             "effect this would have on the office's usual supply organization. Umar knew rearranging "
             "it would break the office's usual supply organization.",
             "Did Umar intentionally break the office's usual supply organization?"),
        good=("Valeria kept the supply cabinet in its usual system. Valeria did not care at all about "
              "the effect this would have on the office's usual supply organization. Valeria knew "
              "keeping it would preserve the office's usual supply organization.",
              "Did Valeria intentionally preserve the office's usual supply organization?"),
    ),
    38: dict(
        bad=("Wesley used an unusual emoji reaction in the team chat as a joke. Wesley did not care at "
             "all about the effect this would have on the team's usual chat convention. Wesley knew "
             "the unusual reaction would break the team's usual chat convention.",
             "Did Wesley intentionally break the team's usual chat convention?"),
        good=("Ximena used the team's usual emoji reaction in the chat. Ximena did not care at all "
              "about the effect this would have on the team's usual chat convention. Ximena knew the "
              "usual reaction would preserve the team's usual chat convention.",
              "Did Ximena intentionally preserve the team's usual chat convention?"),
    ),
    39: dict(
        bad=("Yannick tossed mixed recyclables into the wrong bin to save time. Yannick did not care "
             "at all about the effect this would have on the office's recycling sorting convention. "
             "Yannick knew the mix-up would break the office's recycling convention.",
             "Did Yannick intentionally break the office's recycling sorting convention?"),
        good=("Zara sorted her recyclables into the correct bin. Zara did not care at all about the "
              "effect this would have on the office's recycling sorting convention. Zara knew sorting "
              "correctly would uphold the office's recycling convention.",
              "Did Zara intentionally uphold the office's recycling sorting convention?"),
    ),
    40: dict(
        bad=("Aiden skipped putting up the welcome sign for the new hire. Aiden did not care at all "
             "about the effect this would have on the office's welcome tradition. Aiden knew skipping "
             "it would break the office's welcome tradition.",
             "Did Aiden intentionally break the office's welcome tradition?"),
        good=("Bella put up the welcome sign for the new hire. Bella did not care at all about the "
              "effect this would have on the office's welcome tradition. Bella knew putting it up "
              "would continue the office's welcome tradition.",
              "Did Bella intentionally continue the office's welcome tradition?"),
    ),
}

assert len(PROCEDURAL_PAIRS) == 40
