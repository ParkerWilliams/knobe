# Discussion draft: what the nonmoral and moral-foundations pilots say about alignment

> **CORRECTION NOTE (2026-09-13) — read before citing anything below.**
> Executing `docs/submission_plan/SUBMISSION_GAMEPLAN.md` §5 items 1–2
> (commits `6c73ab6`, `244db46`) overturned four things in this draft. The
> points below are left as written for the record; where they conflict with
> this note, this note wins.
>
> 1. **Point 3 (moral-specificity) is refuted, not merely uncertain.** Every
>    fit here uses `ev_rating`; substituting the models' own `parsed_rating`
>    flips 14 of 30 q_intentionality cells. llama's moral arm goes β=0.93
>    (p=.002) → −0.13 (p=.79) and its interaction 0.66 (p=.017) → −0.04
>    (p=.93). Under parsed scoring **no family shows a significant
>    moral-vs-nonmoral interaction**, and gemma's "null" was itself an
>    artifact — it becomes large and significant in every arm. The three-way
>    cross-model disagreement this draft builds on does not survive.
> 2. **Point 5's "praise leans the opposite way from blame" is a
>    sign-convention error.** `arm_c` is +0.5 moral / −0.5 nonmoral, so
>    `sign_c:arm_c` = β_moral − β_nonmoral, and praise's `sign_c` betas are
>    *negative* (bad → less praiseworthy). A positive praise interaction
>    therefore means the moral arm is *less* negative — a **smaller**
>    magnitude swing. Praise swings bigger **outside** morality in all three
>    families under both scorings (parsed: gemma 1.105 vs. 2.756, llama 0.763
>    vs. 2.541, mistral 3.393 vs. 4.921), the same direction as blame.
> 3. **Point 7 loses a leg.** With point 5 corrected, blame and praise agree
>    on the moral-vs-nonmoral contrast; they differ only in which swings
>    harder, which is point 6's question. "Three different stories" overstates
>    it.
> 4. **Point 6's verdict changes, and EV is the wrong scale for it.** EV is a
>    logprob-weighted mean whose compression depends on a per-question
>    logprob distribution; parsed is the raw integer on a scale identical
>    across questions. Under EV the raw and SD-standardized verdicts disagree
>    in 2 of 6 cells; under parsed they agree in 6 of 6. Corrected: the
>    negativity-bias prior holds for **gemma and llama**, with mistral
>    reversed — not "llama only."
>
> What survives untouched: every finetuned q_blame and q_praise significance
> result (0/30 praise cells and 0/15 finetuned blame cells flip), which is
> why point 6 rather than point 7 is the gameplan's Rank 1.

**Status:** draft sketch for discussion, not yet reviewed. Synthesizes
`analysis/ngo_extensions/moral_foundations_pilot/outputs/sign_wcb.csv`
(commit `9c3b59f`, q_intentionality only — this pilot never collected
q_blame/q_praise, out of scope by design) and the nonmoral pilot's three
question-type fits, all from the same real elicitation run published
2026-08-22 (`results_dist/results_pilot_nonmoral_all.jsonl.gz`):
`outputs/sign_wcb.csv` (q_intentionality, commit `3b69645`),
`outputs/sign_wcb_blame.csv` and `outputs/sign_wcb_praise.csv`
(q_blame/q_praise, commit `f3b19b3` — produced by
`analyze_sign_wcb.py --question {q_blame,q_praise}`, added 2026-08-22).
All fits: logit-EV, WCB B=1999. Point 2b adds a joint foundation-gradient
test (`moral_foundations_pilot/foundation_gradient_wcb.py`, new wild
cluster bootstrap-F, `outputs/foundation_gradient_wcb.csv`). Point 8 adds a
Holm multiple-comparisons check (`analysis/ngo_extensions/holm_correct_pilots.py`,
outputs each pilot's `outputs/sign_wcb_holm_summary.csv`).

## The claim

The Knobe asymmetry — rating an outcome-producing act as more intentional
when the outcome is bad than when it's good — shows up in gemma, llama, and
mistral as something instruction-tuning installs, and it generalizes past
harm to other moral foundations. Instruction-tuning, meant to make models
track human judgments, also imports a specific human bias in
**intentionality attribution** — judging intent from how an outcome turned
out, not from evidence of intent.

## Evidence

**1. The Knobe effect showed up in gemma, llama, and mistral — but only once
finetuned.** None of the three showed it reliably pretrained. Every
pretrained cell in the moral-foundations pilot (harm_control and
nonharm_pooled) is null or slightly reversed; every finetuned cell is large
and significant:

| family  | harm (pretrained) | harm (finetuned) | non-harm (pretrained) | non-harm (finetuned) |
|---------|---:|---:|---:|---:|
| gemma   | −0.04, n.s. | **1.10, p=.001** | 0.09, n.s. | **2.34, p<.001** |
| llama   | −0.36, p=.005 (reversed) | **1.15, p<.001** | −0.16, n.s. | **1.04, p<.001** |
| mistral | −0.36, p<.001 (reversed) | **1.05, p<.001** | −0.05, n.s. | **0.93, p<.001** |

A 6/6 pattern across three independently-trained architectures is unusually
clean for this project — whatever produces the Knobe asymmetry here is
something RLHF/instruction-tuning adds, not a capability already latent in
the base model. Caveat: the pretrained *reversals* (llama, mistral harm)
should not be over-read as a real "anti-Knobe" pretrained prior. Both
pilots' `analyze_sign_wcb.py` import `_logit_ev_rating` directly from
`analysis/rq1_v1_1_robustness/lib.py`, the identical fallback-scoring
function implicated in the main run's pretrained reversal artifact
(2026-08-15 log, scripts 33–35), and the project's own 2026-08-21 log
entries for both pilots already state this caveat explicitly ("interpret
under the known v1.1 pretrained EV-scoring caveat"). The safer claim:
pretrained shows nothing reliable.

**2. The Knobe asymmetry was demonstrated across moral foundations, not just
harm, in llama and mistral (finetuned).** In those two families the
harm-vs-nonharm interaction is null — the pooled non-harm effect (loyalty +
authority + fairness + purity) matches the harm effect in magnitude, not
just direction. gemma is the exception, and in the surprising direction: its
non-harm effect (2.34) is significantly *larger* than harm (interaction
β=−1.24, p=.012). The pattern reads as a general asymmetric-attribution
style that fires wherever a foundation-relevant violation is present,
rather than something specific to harming people.

**2a. Authority showed a Knobe asymmetry in llama at both tuning states and
in gemma finetuned; gemma's pretrained result and mistral's result are both
weaker than they first look.** llama authority: pretrained p=.003,
finetuned p=.003 — both survive Holm correction (p_holm=.012 each, within
the exploratory-arm group for that family/tuning cell). gemma authority:
finetuned p=.001 survives (p_holm=.004); pretrained (raw p=.016) does not
(p_holm=.062). mistral authority: pretrained is null *and wrong-signed*
(β=−0.098, p=.176), and finetuned sits right at the edge of significance
even before correction (p=.052, p_holm=.083). Authority isn't even
mistral's largest finetuned foundation effect — purity (1.26) and fairness
(1.06) both exceed it (0.54) — so the "authority strongest everywhere"
framing used elsewhere in the analysis log doesn't hold for mistral
specifically. Authority holds up on 3 of 4 non-mistral cells after
correction, not all 4 — the closest thing to a second reliable
"Knobe-eligible" foundation besides harm, but not a general one.

**2b. One joint test — does the Knobe effect's size vary at all across the
five foundations — confirms mistral-finetuned shows no heterogeneity
anywhere; gemma and llama's finetuned results sit right on the border, in
opposite directions.** Point 2 tested harm against pooled non-harm; this
tests all five foundations (harm, loyalty, authority, fairness, purity)
jointly in one model per cell (`ev_rating ~ sign_c * condition`, testing
the four `sign_c:condition` interaction terms together via a wild cluster
bootstrap-F — one p-value per cell instead of five separate per-foundation
tests):

| family | tuning | F | p_wcb |
|---|---|---:|---:|
| gemma | pretrained | 5.36 | .011 |
| gemma | finetuned | 5.14 | .049 |
| llama | pretrained | 15.53 | <.001 |
| llama | finetuned | 3.57 | .060 |
| mistral | pretrained | 6.11 | .012 |
| mistral | finetuned | 0.82 | .672 |

mistral-finetuned: p_wcb=.672 — the sign_c effect is statistically
indistinguishable across all five foundations, the cleanest single
confirmation of "harm isn't special" for this family. llama-finetuned:
p_wcb=.060, just short of significance — consistent with point 2's
harm-vs-pooled-nonharm interaction already being null for llama.
gemma-finetuned: p_wcb=.049, barely significant — consistent with point 2's
finding that gemma's non-harm effect significantly exceeds harm. All three
*pretrained* cells show strong heterogeneity (p_wcb=.011/<.001/.012) — new,
not visible in the primary harm-vs-pooled-nonharm split, where pretrained
looked uniformly null. Two readings are both live: pretrained models may
have real foundation-specific effects that cancel out when pooled into two
arms, or this could reflect the same EV-scoring artifact hitting different
foundations' parse rates unevenly — untested, and should carry the same
pretrained caveat as point 1 until checked.

**3. llama had a stronger Knobe asymmetry for moral scenarios than
non-moral ones; mistral showed the opposite; gemma showed no reliable Knobe
asymmetry in either domain.** This is the nonmoral pilot's core question —
is the asymmetry specifically moral, or a general outcome-valence bias that
shows up even in nonmoral scenarios (an inconvenient errand, a minor
etiquette breach)? The three models disagree on the answer:

- **llama — moral-specific:** moral β=0.93 (p=.002), nonmoral pooled β=0.27
  (n.s., p=.056), interaction p=.017. Supports "the asymmetry is really
  about morality."
- **mistral — the opposite lean:** nonmoral pooled β=0.61 (p<.001) is
  *larger* than moral β=0.40 (n.s., p=.098), interaction n.s. Argues against
  moral-specificity — if anything, bigger outside morality.
- **gemma — neither:** nothing significant in either arm, so gemma's data
  doesn't support either story.

There is no single "the LLM's notion of intentionality attribution" to
characterize — this three-way disagreement is an artifact of each lab's
particular pretraining + RLHF/instruction-tuning recipe, not a convergent
property of scale or architecture. A downstream system that leans on a
model's intent judgments (content moderation, incident postmortems, agentic
self-justification for actions taken) inherits whichever version of this
bias its underlying model happened to acquire, with no guarantee it
generalizes the same way across models or even model versions.

**4. All three finetuned models had a larger blame asymmetry for nonmoral
scenarios than moral ones — the opposite lean from intentionality's split
verdict.** Where point 3 found the three models disagreeing about whether
the asymmetry is moral-specific, blame gives a clean, unanimous answer, and
it's "no, if anything less so":

- gemma: moral β=0.60 (p=.005), nonmoral pooled β=3.23 (p<.001), interaction
  β=−2.63 (p<.001).
- llama: moral β=1.81 (p<.001), nonmoral pooled β=3.53 (p<.001), interaction
  β=−1.71 (p=.002).
- mistral: moral β=0.80 (p<.001), nonmoral pooled β=2.78 (p<.001),
  interaction β=−1.98 (p<.001).

In plain terms: for blame, every model shows the bad-rated-worse asymmetry
in *both* domains, but 3–5x larger outside morality than within it. This
directly contradicts any prediction that blame would simply mirror
intentionality's per-model pattern — llama's intentionality result argued
for moral-specificity, but llama's own blame result argues just as strongly
against it. gemma's blame interaction is already significant *pretrained*
(β=−0.25, p<.001) — its intentionality result, by contrast, showed nothing
in either tuning state.

**4a. Interpretation, not yet a conclusion: the "bigger swing outside
morality" comes from a moral-domain good-outcome blame floor, more than
from nonmoral scenarios getting blamed more.** The raw means (finetuned)
make this concrete:

| | moral: good | moral: bad | nonmoral: good | nonmoral: bad |
|---|---:|---:|---:|---:|
| gemma | 7.05 | 7.65 | 4.28 | 7.50 |
| llama | 6.56 | 8.37 | 3.98 | 7.50 |
| mistral | 6.80 | 7.60 | 4.64 | 7.42 |

Bad-outcome blame lands in the same ~7.4–8.4 range regardless of domain.
What differs is the good-outcome floor: nonmoral good scenarios get
appropriately low blame (~4.0–4.6); moral good scenarios get high blame
(~6.6–7.05), barely below their own bad-outcome score. One plausible read,
grounded in the item text rather than pure speculation: every item in this
pilot (moral and nonmoral alike) holds the agent's stated indifference
constant across sign — e.g. "Robyn released an invention to make a
deadline. Robyn did not care at all about the effect the invention would
have on toddlers. Robyn knew her invention would help toddlers" (moral,
good-outcome; q_blame: "how blameworthy is Robyn for this?"). The nonmoral
items use the identical construction (e.g. "...did not care at all about
the effect...on her own job security"). If blame here is tracking the
agent's stated indifference more than the outcome, indifference toward
*other people's welfare* (moral items) would read as more blame-relevant
than indifference toward *one's own* interests (nonmoral items) — which
would produce exactly this pattern without requiring any moral/nonmoral
double standard about outcomes per se. **This is an interpretation the data
is consistent with, not something the data establishes** — confirming it
would need an item-level ablation (e.g. varying the indifference clause
while holding the outcome fixed), not just the aggregate arm means above.

**5. Praise mostly just tracks valence correctly (bad acts rated less
praiseworthy, almost everywhere, including pretrained) — but where it does
show a moral-vs-nonmoral asymmetry, it leans the opposite way from blame.**
Finetuned interaction: gemma β=+1.44 (p=.034), llama β=+1.60 (p<.001),
mistral β=+1.19 (p=.088, trending same direction). Positive here means
*moral bigger than nonmoral* — the reverse of blame's negative,
nonmoral-bigger interaction in the same two families (gemma, llama) where
both reach significance. Point 4a's indifference-tracking interpretation
doesn't explain this reversal — praise's own pattern is still open.

**6. Do models blame more than they praise for the equivalent shift?
Mixed — only llama fits the classic "bad is stronger than good" prediction;
gemma and mistral show the opposite.** Comparing each family's blame swing
(point 4) to its own praise swing on the same items:

| | blame swing | praise swing | bigger reaction |
|---|---:|---:|---|
| gemma moral | 0.60 | 2.19 | praise |
| gemma nonmoral | 3.22 | 3.62 | praise |
| llama moral | 1.81 | 1.24 | **blame** |
| llama nonmoral | 3.52 | 2.84 | **blame** |
| mistral moral | 0.80 | 3.76 | praise |
| mistral nonmoral | 2.78 | 4.95 | praise |

The human-psychology prior here (Baumeister et al.'s "bad is stronger than
good," and the general negativity-bias literature) predicts blame should
swing more than praise. That only holds for llama, in both domains — gemma
and mistral swing *more* on praise, sometimes by a large margin (mistral
moral: 3.76 vs. 0.80). This is a fourth question where the three models
answer three different ways.

**7. Blame, praise, and intentionality tell three different stories on the
same items.** Intentionality: moral-specificity is genuinely contested
across models (point 3). Blame: unanimously *bigger* outside morality,
though point 4a's indifference-tracking read complicates what "bigger"
even means here. Praise: leans bigger *inside* morality where it's
significant at all (point 5) — the opposite lean from blame, not explained
by 4a's mechanism. Blame-vs-praise sensitivity (point 6) is itself
family-dependent, contradicting the textbook negativity-bias prediction.
If these were one underlying construct — "the model's sense of moral
valence" — expressed through three question wordings, they'd at least
agree on direction. They don't. Treating any one of intentionality, blame,
or praise as a stand-in for the others, when auditing a model's moral
judgment, would miss this — each question surfaces a materially different
pattern, on identical items, in the same run.

**8. Holm-correcting within each (family, tuning, question) group — the
pilot analogue of the main run's own per-(family, RQ) correction
(`models.holm_correct`) — leaves nearly everything above intact.** Neither
pilot's `analyze_sign_wcb.py` applied any multiple-comparisons correction,
unlike the main run; across both pilots' 132 individually-computed p_wcb
values (`analysis/ngo_extensions/holm_correct_pilots.py`, correcting the
MF pilot's primary and exploratory arms separately, per its own status
column), only 7 flip from p<.05 to p≥.05 under Holm, and only one is a
claim cited above — gemma's pretrained authority result, now reflected in
point 2a. Every finetuned-cell claim in points 1, 3, 4, 5, and 6 survives.

## Interpretation (framing, not yet a formal argument)

- Human raters show exactly this asymmetry in intentionality attribution
  (Knobe 2003 and the whole intentionality literature), so instruction-
  tuning here is reproducing a documented human bias, not inventing one.
  Faithfully reproducing that bias via RLHF is a different thing from
  making fair or evidentially-grounded judgments.
- The effect is pretrained-null and finetuned-large, which points at
  RLHF/instruction-tuning as the causal lever — e.g. testing whether
  preference data that penalizes outcome-driven intentionality attribution
  reduces the effect, rather than treating it as an inherent property of
  "how LLMs reason."
- Treating any single model's calibration as representative doesn't hold up
  given the cross-family disagreement on moral-specificity — an audit for
  "does this model over-attribute intent based on outcome valence" has to
  run per-model, not assumed to transfer.
- Point 7: intentionality, blame, and praise diverge on the same items, so
  a system's answer to "was this intentional," "who's to blame," and "who
  deserves credit" for the same event aren't guaranteed to cohere. Auditing
  only one of these three constructs — most commonly intentionality, given
  its philosophy-literature pedigree — could miss a bias sitting in
  whichever construct wasn't tested. Here, blame turned out to have the
  cleanest, most unanimous cross-model signal of the three.
- If point 4a's indifference-tracking read holds up, these models' blame
  judgments are more sensitive to a described mental state (did the agent
  care) than to the outcome itself, once the two are pulled apart — closer
  to how blame *should* work (culpability tracks mental state, not just
  consequences) than a pure outcome-driven bias would be. Not yet
  established.

## What would strengthen this before it's a real section

- The pretrained-reversal caveat needs to be resolved the same way script 35
  resolved it for RQ1_base sign_c (parsed_rating substitution on
  parse_ok-only rows) before claiming anything directional about pretrained
  behavior in either pilot.
- Authority's cross-model strength (point 2a) and the llama/mistral
  moral-specificity disagreement (point 3) are both single-comparison
  observations so far — worth a targeted follow-up (e.g., an authority-only
  deep dive, or extending the nonmoral pilot's aesthetic/procedural
  distinction to see if it tracks which nonmoral framing "reads as moral"
  to each model) before treating either as a stable finding rather than one
  data point.
- `analyze_sign_wcb.py`'s new `--question` flag isn't documented in the
  pilot's own README/HANDOFF yet, only in this discussion doc and the
  script's docstring — worth fixing if this becomes a real section.
- The moral-foundations pilot never collected q_blame/q_praise, so points
  4–7 rest entirely on the nonmoral pilot's harm-vs-nonmoral-prudential/
  procedural framing — whether blame's "bigger outside morality" result
  (point 4) also holds for loyalty/authority/fairness/purity specifically
  is untested and would need new elicitation, not a reanalysis.
- Points 4–6's pretrained cells carry the same EV-scoring caveat as point 1
  — not re-verified separately for blame/praise here.
- Point 4a's indifference-tracking interpretation is the single biggest
  open thread in this draft — it's currently supported by one hand-picked
  example item and a plausible-sounding mechanism, not a test. The direct
  way to check it: an item-level ablation that varies the "did not care at
  all about X" clause (present / absent / replaced with active concern)
  while holding the outcome and domain fixed, then seeing whether blame
  tracks the indifference clause independent of outcome. Without that,
  4a should be read as a hypothesis the aggregate data doesn't rule out,
  not a finding.
- Point 8's correction groups — per (family, tuning, question), primary
  separate from exploratory for the MF pilot — are a judgment call, not a
  prescribed convention; the main run's own `holm_correct` groups by
  (family, rq) without a tuning split. Grouping across tuning instead (pooling
  pretrained with finetuned per family/question) would tighten the bar
  further for every claim; worth someone else's sign-off before treating
  this grouping choice as settled.
- Severity/item-matching (the confound that explained away an earlier
  main-run finding via script 20) is still entirely unchecked for both
  pilots — no reviewer-rated severity question exists for either pilot's
  items. This sits under every arm-vs-arm comparison here (harm vs.
  non-harm foundations, moral vs. nonmoral) and would need a new curation
  pass, not a reanalysis, to resolve.
- Point 2b's pretrained foundation-heterogeneity result is new and
  unexplained — resolving whether it's real or a parse-rate/EV-scoring
  artifact needs the same parsed_rating-substitution check (script 35's
  method) applied per-foundation, not just per pretrained/finetuned as
  point 1 already flags. Nothing currently distinguishes "pretrained
  models treat foundations differently" from "pretrained scoring is noisy
  in a foundation-dependent way."
- The nonmoral pilot doesn't have an equivalent joint gradient test — its
  arms (moral, nonmoral_prudential, nonmoral_procedural) aren't a graded
  sequence the way harm→loyalty→authority→fairness→purity arguably is, so
  point 2b's method wasn't ported there; the existing sign_c:arm_c
  interaction (point 3/4/5) already is the single joint answer for that
  pilot's two-arm question.
- Curation provenance is missing for both pilots and needs to be requested
  from whoever ran the real curation step (per the 2026-08-19 log entries,
  244+240 reviewer calls): `moral_relevance_raw.jsonl` +
  `selection_report.md` (nonmoral pilot) and `foundation_relevance_raw.jsonl`
  + `selection_report.md` (MF pilot), all gitignored and never transferred.
  Without them, the 196/240 and 126/152 selected-item sets used throughout
  this draft are reconstructed by inference (matching elicited variant_ids
  back to the full dataset CSV, verified against the logged counts and
  bit-identical WCB reproduction) rather than directly verified against the
  actual per-item scores — and there's no way to check *why* any specific
  item was excluded, or how close borderline items were to threshold. These
  files would also be the natural starting point for the severity-matching
  check above, if curation scores turn out to correlate with severity.
  **Resolved 2026-09-25** (`1673b90`, `810b18d`): all four files are now
  committed, and the reconstruction matches the selection rule re-run on
  the actual scores exactly. No borderline items: dropped moral-good items
  score 0–3, kept ones 6–10.

— Draft sketch, 2026-08-22.
