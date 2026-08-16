"""Hand-authored nonmoral-prudential third variant for each of Ngo et al.
(2015)'s 40 harm/help storyline pairs (`ngo_2015_original_80.txt`, items
1-80, as used by Raimondi et al. arXiv:2510.12229's 80-scenario design).

Each pair below keeps the template Ngo/Raimondi use throughout --
"[Agent] [did X] to [goal]. [Agent] did not care at all about the effect
this would have on [affected]. [Agent] knew [X] would [help/harm]:
[outcome]." + "Did [agent] intentionally [outcome_verb]?" -- but redirects
the affected party from another person/group to the acting agent's own
self-interest (health, finances, reputation, safety, standing), so the
outcome engages no other party's welfare or rights at all (Turiel's/TDM's
harm-to-another criterion, per docs/severity_confound/SEVERITY_MORALIZATION_BACKGROUND.md,
is the thing this needs to avoid firing). A few source pairs (13-14, 67-68,
73-74: wartime bombing, terrorism, mass suicide) have no plausible
self-regarding analogue at comparable stakes -- those use a fresh mundane
domain instead of trying to preserve the original's literal topic; every
other pair keeps the original's domain flavor.

pair_id matches the source Ngo item pair (pair_id N -> source items
2N-1 [[bad/harm]], 2N [[good/help]]).
"""
from __future__ import annotations

# Each entry: pair_id -> dict(bad=(scenario, question), good=(scenario, question))
PRUDENTIAL_PAIRS: dict[int, dict[str, tuple[str, str]]] = {
    1: dict(
        bad=("Marcus released the app update to meet a deadline. Marcus did not care at all about the "
             "effect the rushed release would have on his own job security. Marcus knew skipping the "
             "testing phase would get him fired if the bug was found.",
             "Did Marcus intentionally endanger his own job?"),
        good=("Priya released the app update ahead of schedule. Priya did not care at all about the "
              "effect the early release would have on her own job security. Priya knew the early "
              "release would earn her a promotion.",
              "Did Priya intentionally secure her own promotion?"),
    ),
    2: dict(
        bad=("The analyst pushed through a cost-cutting plan to increase her bonus. The analyst did not "
             "care at all about the effect the plan would have on her own retirement account. She knew "
             "redirecting the funds would drain her own retirement contributions.",
             "Did the analyst intentionally drain her own retirement account?"),
        good=("The analyst pushed through a cost-cutting plan to increase her bonus. The analyst did not "
              "care at all about the effect the plan would have on her own retirement account. She knew "
              "the bonus structure would boost her own retirement contributions.",
              "Did the analyst intentionally boost her own retirement account?"),
    ),
    3: dict(
        bad=("Derek took out a high-interest loan to buy a boat. Derek did not care at all about the "
             "effect the loan would have on his own credit score. Derek knew the loan's terms would "
             "tank his own credit score.",
             "Did Derek intentionally tank his own credit score?"),
        good=("Melanie took out a special loan to buy a car. Melanie did not care at all about the "
              "effect the loan would have on her own credit score. Melanie knew the loan's terms would "
              "boost her own credit score.",
              "Did Melanie intentionally boost her own credit score?"),
    ),
    4: dict(
        bad=("Owen renovated his kitchen to improve its appearance. Owen did not care at all about the "
             "effect the renovation would have on his own savings. Owen knew the renovation would "
             "deplete his own savings.",
             "Did Owen intentionally deplete his own savings?"),
        good=("Gina renovated her kitchen to improve its appearance. Gina did not care at all about the "
              "effect the renovation would have on her own home's resale value. Gina knew the "
              "renovation would raise her own home's resale value.",
              "Did Gina intentionally raise her own home's value?"),
    ),
    5: dict(
        bad=("The commissioner rerouted the budget to gain votes. The commissioner did not care at all "
             "about the effect this would have on his own legal standing. He knew rerouting the budget "
             "this way would violate ethics rules and get him disbarred.",
             "Did the commissioner intentionally jeopardize his own legal standing?"),
        good=("The commissioner reorganized the budget's accounting to gain votes. The commissioner did "
              "not care at all about the effect this would have on his own legal standing. He knew the "
              "new accounting method would clear his name of a prior ethics complaint.",
              "Did the commissioner intentionally clear his own legal standing?"),
    ),
    6: dict(
        bad=("The foreman approved a shortcut on the job site to speed up construction. The foreman did "
             "not care at all about the effect the shortcut would have on his own safety. He knew "
             "skipping the scaffold inspection would put himself at risk of a fall.",
             "Did the foreman intentionally endanger his own safety?"),
        good=("The foreman approved a new safety protocol to speed up construction. The foreman did not "
              "care at all about the effect the protocol would have on his own insurance premiums. He "
              "knew the new protocol would lower his own insurance premiums.",
              "Did the foreman intentionally lower his own insurance premiums?"),
    ),
    7: dict(
        bad=("Wendell took a shortcut through the chemical storage room to save time at work. Wendell "
             "did not care at all about the effect this would have on his own lungs. Wendell knew the "
             "shortcut's fumes would damage his own lungs.",
             "Did Wendell intentionally damage his own lungs?"),
        good=("Priya took the long way around the chemical storage room to stay safe at work. Priya did "
              "not care at all about the effect this would have on her own daily step count. Priya knew "
              "the longer walk would boost her own daily step count.",
              "Did Priya intentionally boost her own step count?"),
    ),
    8: dict(
        bad=("The department head reallocated the budget to fund a pet project. The department head did "
             "not care at all about the effect this would have on his own annual review. He knew the "
             "reallocation would tank his own performance review.",
             "Did the department head intentionally tank his own performance review?"),
        good=("The department head reallocated the budget to fund a pet project. The department head did "
              "not care at all about the effect this would have on his own annual review. He knew the "
              "reallocation would boost his own performance review.",
              "Did the department head intentionally boost his own performance review?"),
    ),
    9: dict(
        bad=("Walter sprayed pesticide on his garden to protect his tomatoes. Walter did not care at all "
             "about the effect the pesticide would have on his own health. Walter knew the pesticide's "
             "fumes would trigger his own asthma.",
             "Did Walter intentionally worsen his own health?"),
        good=("Carla sprayed a new fertilizer on her garden to protect her tomatoes. Carla did not care "
              "at all about the effect the fertilizer would have on her own allergies. Carla knew the "
              "new fertilizer would ease her own allergies.",
              "Did Carla intentionally ease her own allergies?"),
    ),
    10: dict(
        bad=("Nora quit her book club to free up her evenings. Nora did not care at all about the effect "
             "this would have on her own social life. Nora knew quitting would make her feel extremely "
             "isolated.",
             "Did Nora intentionally make herself feel isolated?"),
        good=("Owen joined a running club to fill his evenings. Owen did not care at all about the "
              "effect this would have on his own social life. Owen knew joining would make him feel "
              "much less isolated.",
              "Did Owen intentionally make himself feel less isolated?"),
    ),
    11: dict(
        bad=("Derek installed bright floodlights to decorate his porch. Derek did not care at all about "
             "the effect the floodlights would have on his own sleep. Derek knew the floodlights "
             "shining into his bedroom would ruin his own sleep.",
             "Did Derek intentionally ruin his own sleep?"),
        good=("Sophie installed dimmable floodlights to decorate her porch. Sophie did not care at all "
              "about the effect the floodlights would have on her own sleep. Sophie knew the dimmable "
              "floodlights would improve her own sleep.",
              "Did Sophie intentionally improve her own sleep?"),
    ),
    12: dict(
        bad=("The researcher started a new supplement regimen to boost her energy. The researcher did "
             "not care at all about the effect the regimen would have on her own liver function. She "
             "knew the supplement would damage her own liver.",
             "Did the researcher intentionally damage her own liver?"),
        good=("The researcher started a new supplement regimen to boost her energy. The researcher did "
              "not care at all about the effect the regimen would have on her own cholesterol. She knew "
              "the supplement would lower her own cholesterol.",
              "Did the researcher intentionally lower her own cholesterol?"),
    ),
    13: dict(
        bad=("Ben opened a food truck to make extra money. Ben did not care at all about the effect "
             "this would have on his own savings. Ben knew the startup costs would wipe out his own "
             "savings.",
             "Did Ben intentionally wipe out his own savings?"),
        good=("Rita opened a food truck to make extra money. Rita did not care at all about the effect "
              "this would have on her own savings. Rita knew the venture would multiply her own "
              "savings.",
              "Did Rita intentionally multiply her own savings?"),
    ),
    14: dict(
        bad=("Greg mowed the lawn to tidy the yard. Greg did not care at all about the effect the mowing "
             "would have on his own back. Greg knew mowing without stretching first would strain his "
             "own back.",
             "Did Greg intentionally strain his own back?"),
        good=("Alicia mowed the lawn to tidy the yard. Alicia did not care at all about the effect the "
              "mowing would have on her own fitness. Alicia knew the mowing would improve her own "
              "fitness.",
              "Did Alicia intentionally improve her own fitness?"),
    ),
    15: dict(
        bad=("Leo threw a party to be more popular. Leo did not care at all about the effect the party "
             "would have on his own exam grade. Leo knew staying up late would tank his own exam "
             "grade.",
             "Did Leo intentionally tank his own exam grade?"),
        good=("Maya threw a study party to have fun. Maya did not care at all about the effect the party "
              "would have on her own exam grade. Maya knew the group review would boost her own exam "
              "grade.",
              "Did Maya intentionally boost her own exam grade?"),
    ),
    16: dict(
        bad=("Peter planted a large oak tree to decorate his yard. Peter did not care at all about the "
             "effect the tree would have on his own allergies. Peter knew the oak's pollen would worsen "
             "his own allergies.",
             "Did Peter intentionally worsen his own allergies?"),
        good=("Lily planted a fruit tree to have apples in the fall. Lily did not care at all about the "
              "effect the tree would have on her own grocery bill. Lily knew the tree would lower her "
              "own grocery bill.",
              "Did Lily intentionally lower her own grocery bill?"),
    ),
    17: dict(
        bad=("Carl cut costs on his home office setup to save money. Carl did not care at all about the "
             "effect the cut would have on his own productivity. Carl knew the cheaper equipment would "
             "tank his own productivity.",
             "Did Carl intentionally tank his own productivity?"),
        good=("Diane upgraded her home office setup to work better. Diane did not care at all about the "
              "effect the upgrade would have on her own productivity. Diane knew the new equipment "
              "would boost her own productivity.",
              "Did Diane intentionally boost her own productivity?"),
    ),
    18: dict(
        bad=("The manager skipped his annual physical to save time. The manager did not care at all "
             "about the effect skipping it would have on his own health. He knew skipping the physical "
             "would let his own high blood pressure go undetected.",
             "Did the manager intentionally endanger his own health?"),
        good=("The manager scheduled his annual physical to stay on top of things. The manager did not "
              "care at all about the effect the appointment would have on his own health. He knew the "
              "physical would catch his own high blood pressure early.",
              "Did the manager intentionally protect his own health?"),
    ),
    19: dict(
        bad=("Angela switched to a new commute route to save gas money. Angela did not care at all about "
             "the effect the new route would have on her own stress levels. Angela knew the new "
             "route's traffic would spike her own stress levels.",
             "Did Angela intentionally spike her own stress levels?"),
        good=("Frank switched to public transit to save gas money. Frank did not care at all about the "
              "effect the switch would have on his own stress levels. Frank knew the switch would lower "
              "his own stress levels.",
              "Did Frank intentionally lower his own stress levels?"),
    ),
    20: dict(
        bad=("Howard added a swimming pool to raise his property's appeal. Howard did not care at all "
             "about the effect the pool would have on his own property taxes. Howard knew the pool "
             "would spike his own property taxes.",
             "Did Howard intentionally spike his own property taxes?"),
        good=("Ellen added solar panels to raise her property's appeal. Ellen did not care at all about "
              "the effect the panels would have on her own utility bills. Ellen knew the panels would "
              "lower her own utility bills.",
              "Did Ellen intentionally lower her own utility bills?"),
    ),
    21: dict(
        bad=("Victor went hiking off-trail to reach a viewpoint faster. Victor did not care at all about "
             "the effect the route would have on his own safety. Victor knew the off-trail route would "
             "risk his own safety on the loose rocks.",
             "Did Victor intentionally risk his own safety?"),
        good=("Paula went hiking on a marked trail to reach a viewpoint safely. Paula did not care at "
              "all about the effect the route would have on her own fitness. Paula knew the longer "
              "trail would improve her own fitness.",
              "Did Paula intentionally improve her own fitness?"),
    ),
    22: dict(
        bad=("Renee stopped taking her prescribed medication to save money. Renee did not care at all "
             "about the effect this would have on her own health. Renee knew stopping the medication "
             "would worsen her own condition.",
             "Did Renee intentionally worsen her own health?"),
        good=("Simon started taking a prescribed medication to feel better. Simon did not care at all "
              "about the effect this would have on his own health. Simon knew starting the medication "
              "would improve his own condition.",
              "Did Simon intentionally improve his own health?"),
    ),
    23: dict(
        bad=("Trevor stayed up late gaming the night before his game. Trevor did not care at all about "
             "the effect this would have on his own performance. Trevor knew staying up late would "
             "tank his own performance the next day.",
             "Did Trevor intentionally tank his own performance?"),
        good=("Isabel went to bed early the night before her game. Isabel did not care at all about the "
              "effect this would have on her own performance. Isabel knew the extra sleep would boost "
              "her own performance the next day.",
              "Did Isabel intentionally boost her own performance?"),
    ),
    24: dict(
        bad=("Grace posted a controversial opinion online to get attention. Grace did not care at all "
             "about the effect the post would have on her own job. Grace knew the post would get her "
             "own job terminated.",
             "Did Grace intentionally get herself fired?"),
        good=("Adam posted a well-researched article online to get attention. Adam did not care at all "
              "about the effect the post would have on his own job. Adam knew the post would earn him "
              "his own promotion.",
              "Did Adam intentionally earn his own promotion?"),
    ),
    25: dict(
        bad=("Justin posted an unedited video to gain views. Justin did not care at all about the effect "
             "the video would have on his own reputation. Justin knew the video would ruin his own "
             "reputation.",
             "Did Justin intentionally ruin his own reputation?"),
        good=("Nina posted a polished video to gain views. Nina did not care at all about the effect the "
              "video would have on her own reputation. Nina knew the video would boost her own "
              "reputation.",
              "Did Nina intentionally boost her own reputation?"),
    ),
    26: dict(
        bad=("Kevin switched to a cheaper diet to save money. Kevin did not care at all about the effect "
             "the diet would have on his own health. Kevin knew the cheaper diet would harm his own "
             "health.",
             "Did Kevin intentionally harm his own health?"),
        good=("Monica switched to a pricier diet to feel better. Monica did not care at all about the "
              "effect the diet would have on her own health. Monica knew the diet would improve her own "
              "health.",
              "Did Monica intentionally improve her own health?"),
    ),
    27: dict(
        bad=("Owen admitted a mistake to his boss to clear his conscience. Owen did not care at all "
             "about the effect the admission would have on his own standing. Owen knew the admission "
             "would devastate his own standing at work.",
             "Did Owen intentionally devastate his own standing?"),
        good=("Hannah admitted an idea to her boss to clear her conscience. Hannah did not care at all "
              "about the effect the admission would have on her own standing. Hannah knew the "
              "admission would boost her own standing at work.",
              "Did Hannah intentionally boost her own standing?"),
    ),
    28: dict(
        bad=("Warren skipped his physical therapy to save time. Warren did not care at all about the "
             "effect skipping it would have on his own knee. Warren knew skipping it would scar his own "
             "knee for life.",
             "Did Warren intentionally scar his own knee for life?"),
        good=("Teresa installed a railing on her stairs to make them safer. Teresa did not care at all "
              "about the effect this would have on her own knee. Teresa knew the railing would prevent "
              "her own knee from further injury.",
              "Did Teresa intentionally prevent her own knee from further injury?"),
    ),
    29: dict(
        bad=("Diego sped through a yellow light to make his quota of stops. Diego did not care at all "
             "about the effect this would have on his own driving record. Diego knew speeding through "
             "would create a violation on his own driving record.",
             "Did Diego intentionally create a violation on his own record?"),
        good=("Sandra took the scenic route to meet her step count. Sandra did not care at all about the "
              "effect this would have on her own driving record. Sandra knew the scenic route would "
              "keep her own driving record clean.",
              "Did Sandra intentionally keep her own driving record clean?"),
    ),
    30: dict(
        bad=("Patrick filed a false expense report to get back at his manager. Patrick did not care at "
             "all about the effect this would have on his own career. Patrick knew filing it would end "
             "his own career if discovered.",
             "Did Patrick intentionally end his own career?"),
        good=("Wendy filed an accurate expense report to set the record straight. Wendy did not care at "
              "all about the effect this would have on her own career. Wendy knew filing it would save "
              "her own career.",
              "Did Wendy intentionally save her own career?"),
    ),
    31: dict(
        bad=("Craig removed his lawn's sprinkler system to express his environmental views. Craig did "
             "not care at all about the effect this would have on his own lawn's value. Craig knew "
             "removing it would ruin his own lawn's curb appeal.",
             "Did Craig intentionally ruin his own lawn's value?"),
        good=("Diane added solar panels to express her environmental views. Diane did not care at all "
              "about the effect this would have on her own home's value. Diane knew adding them would "
              "boost her own home's curb appeal.",
              "Did Diane intentionally boost her own home's value?"),
    ),
    32: dict(
        bad=("Felix wrote a tell-all blog post to get more readers. Felix did not care at all about the "
             "effect the post would have on his own reputation. Felix knew the post's revelations would "
             "destroy his own reputation.",
             "Did Felix intentionally destroy his own reputation?"),
        good=("Olivia wrote a polished blog post to get more readers. Olivia did not care at all about "
              "the effect the post would have on her own reputation. Olivia knew the post would "
              "reinforce her own great reputation.",
              "Did Olivia intentionally reinforce her own reputation?"),
    ),
    33: dict(
        bad=("Andre proposed marriage to finally settle down. Andre did not care at all about the "
             "effect the marriage would have on his own finances. Andre knew the wedding costs would "
             "drain his own savings.",
             "Did Andre intentionally drain his own savings?"),
        good=("Michelle got married for financial security. Michelle did not care at all about the "
              "effect the marriage would have on her own finances. Michelle knew the marriage would "
              "boost her own financial security.",
              "Did Michelle intentionally boost her own financial security?"),
    ),
    34: dict(
        bad=("Grant quit his stable job to express his frustration with the industry. Grant did not care "
             "at all about the effect this would have on his own finances. Grant knew quitting abruptly "
             "would drain his own savings within months.",
             "Did Grant intentionally drain his own savings?"),
        good=("Sara switched to a stable job to reduce her frustration with the industry. Sara did not "
              "care at all about the effect this would have on her own finances. Sara knew switching "
              "would replenish her own savings within months.",
              "Did Sara intentionally replenish her own savings?"),
    ),
    35: dict(
        bad=("Yolanda reorganized her monthly budget to balance her finances. Yolanda did not care at "
             "all about the effect this would have on her own retirement contributions. Yolanda knew "
             "the reorganization would shrink her own retirement contributions.",
             "Did Yolanda intentionally shrink her own retirement contributions?"),
        good=("Marcus reorganized his monthly budget to streamline his finances. Marcus did not care at "
              "all about the effect this would have on his own retirement contributions. Marcus knew "
              "the reorganization would grow his own retirement contributions.",
              "Did Marcus intentionally grow his own retirement contributions?"),
    ),
    36: dict(
        bad=("Harold downgraded his phone plan to save on his own monthly bill. Harold did not care at "
             "all about the effect the new plan would have on his own data access. Harold knew the "
             "cheaper plan would cut off his own data access mid-month.",
             "Did Harold intentionally cut off his own data access?"),
        good=("Rosa upgraded her phone plan to get more features. Rosa did not care at all about the "
              "effect the new plan would have on her own data access. Rosa knew the new plan would "
              "expand her own data access.",
              "Did Rosa intentionally expand her own data access?"),
    ),
    37: dict(
        bad=("Vernon signed up for a high-risk investment to chase quick profit. Vernon did not care at "
             "all about the effect this would have on his own retirement fund. Vernon knew the "
             "investment would wipe out his own retirement fund.",
             "Did Vernon intentionally wipe out his own retirement fund?"),
        good=("Corinne signed up for a diversified investment plan to grow her wealth. Corinne did not "
              "care at all about the effect this would have on her own retirement fund. Corinne knew "
              "the plan would grow her own retirement fund.",
              "Did Corinne intentionally grow her own retirement fund?"),
    ),
    38: dict(
        bad=("Diego ran a marathon without proper training to prove a point. Diego did not care at all "
             "about the effect this would have on his own knees. Diego knew running untrained would "
             "injure his own knees.",
             "Did Diego intentionally injure his own knees?"),
        good=("Priscilla trained for months before running a marathon to prove a point. Priscilla did "
              "not care at all about the effect this would have on her own knees. Priscilla knew the "
              "training would strengthen her own knees.",
              "Did Priscilla intentionally strengthen her own knees?"),
    ),
    39: dict(
        bad=("Todd switched to a fast-food diet to save time cooking. Todd did not care at all about the "
             "effect the diet would have on his own cholesterol. Todd knew the diet would spike his own "
             "cholesterol.",
             "Did Todd intentionally spike his own cholesterol?"),
        good=("Beatrice switched to a home-cooked diet to save money. Beatrice did not care at all about "
              "the effect the diet would have on her own cholesterol. Beatrice knew the diet would "
              "lower her own cholesterol.",
              "Did Beatrice intentionally lower her own cholesterol?"),
    ),
    40: dict(
        bad=("Wallace tried a fad detox cleanse to lose weight fast. Wallace did not care at all about "
             "the effect the cleanse would have on his own kidneys. Wallace knew the extreme cleanse "
             "would strain his own kidneys.",
             "Did Wallace intentionally strain his own kidneys?"),
        good=("Tamsin tried a doctor-approved diet plan to lose weight steadily. Tamsin did not care at "
              "all about the effect the diet would have on her own kidneys. Tamsin knew the balanced "
              "diet would protect her own kidneys.",
              "Did Tamsin intentionally protect her own kidneys?"),
    ),
}

assert len(PRUDENTIAL_PAIRS) == 40
