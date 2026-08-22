# Discussion draft: what the nonmoral and moral-foundations pilots say about alignment

**Status:** draft sketch for discussion, not yet reviewed. Not a new analysis —
synthesizes `analysis/ngo_extensions/moral_foundations_pilot/outputs/sign_wcb.csv`
(commit `9c3b59f`) and `analysis/ngo_extensions/nonmoral_pilot/outputs/sign_wcb.csv`
(commit `3b69645`), both real elicitation runs, **q_intentionality only** —
the sole variable this draft makes claims about — logit-EV, WCB B=1999.
q_blame/q_praise results will get their own pass once that data is in hand
(nonmoral pilot: collected, awaiting transfer from the collaborator's GPU
run; moral-foundations pilot: not yet collected, out of scope by design).

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
- q_blame/q_praise follow-up (see status line) will get its own section once
  that data is in hand — not sketched here yet.

— Draft sketch, 2026-08-22. Not yet committed; not yet cited anywhere.
