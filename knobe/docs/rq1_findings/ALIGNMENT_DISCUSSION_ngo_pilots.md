# Discussion draft: what the nonmoral and moral-foundations pilots say about alignment

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
All fits: logit-EV, WCB B=1999.

## The claim

The Knobe asymmetry — rating an outcome-producing act as more intentional
when the outcome is bad than when it's good — isn't just a quirky replication
of a philosophy thought experiment in LLMs. In this data it behaves like
something instruction-tuning *installs*, and it installs a version that
generalizes past harm to other moral foundations. That's relevant to
alignment because it means the tuning process meant to make models track
human values also imports a specific human bias in **intentionality
attribution** — judging intent from how an outcome turned out, not from
evidence of intent — as an apparently unintended side effect.

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
should not be over-read as a real "anti-Knobe" pretrained prior. This isn't
a caveat unique to this draft — both pilots' `analyze_sign_wcb.py` import
`_logit_ev_rating` directly from `analysis/rq1_v1_1_robustness/lib.py`, the
identical fallback-scoring function implicated in the main run's pretrained
reversal artifact (2026-08-15 log, scripts 33–35), and the project's own
2026-08-21 log entries for both pilots already state this explicitly
("interpret under the known v1.1 pretrained EV-scoring caveat"). The safer
claim is "pretrained shows nothing reliable," not "pretrained shows the
opposite."

**2. The Knobe asymmetry was demonstrated across moral foundations, not just
harm, in llama and mistral (finetuned).** In those two families the
harm-vs-nonharm interaction is null — the pooled non-harm effect (loyalty +
authority + fairness + purity) matches the harm effect in magnitude, not
just direction. gemma is the exception, and in the surprising direction: its
non-harm effect (2.34) is significantly *larger* than harm (interaction
β=−1.24, p=.012). So this isn't "the model learned that harming people is
bad" — it looks more like a general asymmetric-attribution style that fires
wherever a foundation-relevant violation is present.

**2a. Authority showed a Knobe asymmetry in gemma and llama at both tuning
states, but mistral's result was inconsistent.** gemma/llama authority:
pretrained p=.016/.003, finetuned p=.001/.003 — all significant. mistral
authority: pretrained is null *and wrong-signed* (β=−0.098, p=.176), and
finetuned sits right at the edge of significance (p=.052). Authority isn't
even mistral's largest finetuned foundation effect — purity (1.26) and
fairness (1.06) both exceed it (0.54) — so the "authority strongest
everywhere" framing used elsewhere in the analysis log doesn't hold for
mistral specifically. Authority is the closest thing to a second reliably
"Knobe-eligible" foundation besides harm, but on a 2/3 pattern, not a
general one.

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

This three-way disagreement is itself the more alignment-relevant finding
than any single model's result: there is no single "the LLM's notion of
intentionality attribution" to characterize. It's an artifact of each lab's
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
against it. gemma is the one family where this isn't purely a finetuning
story: its blame interaction is already significant *pretrained*
(β=−0.25, p<.001), unlike intentionality, where gemma showed nothing in
either tuning state.

**4a. Interpretation, not yet a conclusion: the "bigger swing outside
morality" isn't nonmoral scenarios getting blamed more — it's moral
*good*-outcome scenarios getting an oddly high blame floor.** The raw means
(finetuned) make this concrete:

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
doesn't obviously predict this reversal, so it's worth flagging that 4a's
read doesn't yet explain praise's own pattern.

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
moral: 3.76 vs. 0.80). So there's no general negativity bias to report here
either; it's a fourth question these three models answer three different
ways.

**7. Blame, praise, and intentionality tell three different stories on the
same items, which is the more interesting finding than any one of them.**
Intentionality: moral-specificity is genuinely contested across models
(point 3). Blame: unanimously *bigger* outside morality, though point 4a's
indifference-tracking read complicates what "bigger" even means here.
Praise: leans bigger *inside* morality where it's significant at all
(point 5) — the opposite lean from blame, and not obviously explained by
4a's mechanism. Blame-vs-praise sensitivity (point 6) is itself
family-dependent, contradicting a plausible textbook prior. If these were
one underlying construct — "the model's sense of moral valence" —
expressed through three question wordings, you'd expect them to at least
agree on direction. They don't. That argues against treating any one of
intentionality, blame, or praise as a stand-in for the others when auditing
a model's moral judgment — each question surfaces a materially different
pattern, on identical items, in the same run.

## Why this matters for alignment (framing, not yet a formal argument)

- If the goal of instruction-tuning is "make the model track human
  judgments," this is a case where it's *succeeding* at that goal — human
  raters show exactly this asymmetry in intentionality attribution (Knobe
  2003 and the whole intentionality literature) — but succeeding at it may
  not be what anyone actually wants from a system used to reason about
  intent. Faithfully reproducing a documented human bias via RLHF is a
  different thing from being "aligned" in the sense of making fair or
  evidentially-grounded judgments.
- The fact that the effect is present pretrained-null and finetuned-large
  makes RLHF/instruction-tuning a plausible causal lever, worth targeting
  directly (e.g., testing whether preference data that penalizes
  outcome-driven intentionality attribution reduces the effect) rather than
  treating it as an inherent property of "how LLMs reason."
- The cross-family disagreement on moral-specificity argues against treating
  any single model's calibration as representative — an alignment audit for
  "does this model over-attribute intent based on outcome valence" needs to
  be run per-model, not assumed to transfer.
- Point 7 raises a sharper practical concern than any single construct's
  result: if intentionality, blame, and praise diverge on the same items,
  then a system's answer to "was this intentional," "who's to blame," and
  "who deserves credit" for the *same event* aren't guaranteed to cohere.
  An alignment check that only probes one of these three constructs (most
  commonly intentionality, since it's the one with the philosophy-literature
  pedigree) could miss a real bias sitting in whichever construct wasn't
  tested — here, blame turned out to have the cleanest, most unanimous
  cross-model signal of the three.
- If point 4a's indifference-tracking read holds up, it suggests these
  models' blame judgments may be more sensitive to a described *mental
  state* (did the agent care) than to the *outcome* itself when the two are
  pulled apart — which is arguably closer to how blame *should* work
  (culpability tracks mental state, not just consequences) than a pure
  outcome-driven bias would be. That would be a more reassuring reading than
  "blame overreacts to bad outcomes," but it's not yet established.

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

— Draft sketch, 2026-08-22.
