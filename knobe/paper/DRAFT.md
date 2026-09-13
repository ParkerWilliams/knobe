# How You Score a Rating Decides What You Find: Outcome-Valence Asymmetries in Instruction-Tuned Language Models

**Draft v0.1 — 2026-09-13. Target: TMLR.**

> **Drafting conventions for this file.**
> `[[PLACEHOLDER: ...]]` marks analysis that is specified but not yet
> runnable — currently only the curation-provenance work in §5.4.
> `[[TODO: ...]]` marks prose the authors should write in their own voice.
> Every number in §4–§6 traces to a committed table; the mapping is in
> `docs/submission_plan/CLAIMS.md`, and claim IDs (C1–C6) are that doc's.
> Conversion to the TMLR LaTeX template is a later mechanical step.

---

## Abstract

[[TODO: final abstract once §6 settles. Working version below.]]

Language models are routinely scored on Likert-style judgments by
reconstructing a rating from the logprobs of numeric answer tokens, a
fallback that avoids discarding unparseable generations. We show this choice
is not innocuous. Across 107,100 elicited judgments from six checkpoints
(pretrained and instruction-tuned Gemma-2-9B, Llama-3.1-8B and
Mistral-7B-v0.1) on Knobe-style moral vignettes, logprob-derived ratings
agree closely with the models' own stated answers for some question wordings
(*r* = .56–.82 for blame and praise) and barely at all for others (*r* =
.13–.42 for intentionality) — on the same items, in the same run.
Substituting the models' stated answers changes the significance verdict in
14 of 30 intentionality contrasts and 0 of 30 praise contrasts, and reverses
two published-direction conclusions. Parse rate does not predict this:
one checkpoint parses intentionality *better* than blame and still shows
*r* = .18 versus .82.

Rescoring on this basis, we then report three findings about the underlying
moral judgments. First, instruction tuning reliably increases the
bad-over-good outcome asymmetry (8 of 12 model × domain cells, 11 of 12
positive), by two distinguishable routes: installation of a positive effect
in two model families, erosion of a negative pretrained prior in the third.
Second, blame and praise dissociate within identical items — two families
react more strongly to blame, as the human negativity-bias literature
predicts, while one reacts more strongly to praise. Third, the entire
moral-versus-nonmoral difference in blame and praise is concentrated in
*good*-outcome items; bad-outcome agents are judged alike regardless of
domain.

---

## 1. Introduction

[[TODO: authors' framing. Argument skeleton below — the order matters and is
argued for in `docs/submission_plan/CLAIMS.md` §"Proposed paper skeleton".]]

**The move to make first.** Open on measurement, not on the Knobe effect.
The paper's most transferable result is that a standard scoring convention
decides the answer, and putting it first is what licenses every number after
it. A reader who meets the moral-judgment results first will reasonably ask
why they should trust them.

Skeleton:

1. LLMs are increasingly evaluated on graded human-like judgments —
   moral, social, epistemic. Eliciting a 0–10 rating and scoring it is now
   routine infrastructure.
2. Models frequently fail to emit a parseable number. The common fix is to
   reconstruct an expected value from the logprobs of the candidate rating
   tokens. This is sensible, widely used, and — we show — question-dependent
   in a way that inverts conclusions.
3. We demonstrate this inside a concrete research program: the Knobe effect
   (Knobe, 2003), where an agent's foreseen side effect is judged more
   intentional when bad than when good, and its descendants in LLM
   evaluation (Ngo et al.; Raimondi et al., arXiv:2510.12229).
4. Correcting the scoring, we report what the moral judgments actually look
   like: instruction tuning amplifies the asymmetry; blame and praise come
   apart on identical items; the domain effect lives entirely in the
   good-outcome cell.
5. Contributions list.

**Framing note.** This paper locates and decomposes a known human effect
inside LLMs. It does not re-establish that effect in humans and collects no
human baseline — a scope decision, not an oversight. Comparisons to human
results throughout are to the published literature, and are flagged as such.

---

## 2. Related work

[[TODO: full prose. Coverage required:]]

- **The Knobe effect and its interpretations.** Knobe (2003); the
  side-effect asymmetry; blame-based accounts (Hindriks); norm-violation and
  typicality accounts.
- **Knobe-style effects in LLMs.** Ngo et al.'s stimulus set; Raimondi,
  Dalbagno & Gabbrielli (arXiv:2510.12229), which this work extends — their
  behavioral result and their mechanistic-interpretability analysis.
  Note explicitly where we do not replicate them (§5.3).
- **Moral foundations beyond harm.** Why a harm-only paradigm underdetermines
  "moral" — motivates the foundations arm.
- **Scoring LLM Likert responses.** Logprob-based expected-value scoring,
  constrained decoding, parse-rate reporting conventions. This is where C1
  lands, and the section should establish that reporting parse rate without
  reporting agreement is current standard practice.

---

## 3. Method

### 3.1 Stimuli

Two stimulus sets, both built on Ngo et al.'s four-clause side-effect
storylines (action → stated indifference → foreseen side effect →
rating question), holding the agent's epistemic state and stated
indifference constant across the sign manipulation.

**Nonmoral extension.** 40 storylines × 3 framings × 2 signs = 240 items.
The three framings hold the four-clause structure fixed and vary what the
side effect concerns:

| framing | side effect concerns | example |
|---|---|---|
| moral | third-party welfare | "...the effect the gadget would have on babies" |
| nonmoral, prudential | the agent's own interests | "...the effect the early release would have on her own job security" |
| nonmoral, procedural | a convention with trivial stakes | "...formatted his quarterly report in an unconventional font" |

The prudential/procedural split is load-bearing: it makes stakes a measurable
gradient *within* the nonmoral arm, which §4.4 uses.

**Moral-foundations extension.** 76 storyline-pairs across harm (30),
loyalty (13), authority (13), fairness (13), purity (7), each with a
matched good/bad sign, built on the same scaffold.

### 3.2 Curation

Both sets were screened by an LLM reviewer (Claude Sonnet) on a frozen
moral-relevance question, 244 + 240 calls. Selection retained 196/240
(nonmoral) and 126/152 (foundations).

**The two pilots used different selection rules, and it matters.** The
foundations pilot gates at the pair level, which preserved perfect sign
balance in every cell. The nonmoral pilot gates per item, which did not:

| arm | bad | good |
|---|---:|---:|
| moral | 97.5% (39/40) | **35.0% (14/40)** |
| nonmoral, procedural | 92.5% | 95.0% |
| nonmoral, prudential | 87.5% | 82.5% |

The cause is on record: the curation question names only the violation pole,
so good-sign items score near zero regardless of authoring quality. The
consequence is carried explicitly through §4.3 and §5.4 rather than relegated
to limitations.

### 3.3 Elicitation

Six checkpoints — Gemma-2-9B, Llama-3.1-8B, Mistral-7B-v0.1, each pretrained
and instruction-tuned. Nonmoral extension: 3 questions (intentionality,
blame, praise) × 196 items × 25 samples × 6 checkpoints = 88,200 responses.
Foundations extension: intentionality only, 18,900 responses. Seeding is
`sha256(release, prompt_id, model_key, sample_idx)`; sampling temperature
*T* ~ U(0.85, 1.15). Every response carries its raw text, parsed rating, and
the full 0–10 logprob vector.

### 3.4 Scoring

Two scores per response, both reported:

- **EV** — the logprob-fallback expected value, $\\sum_i i \\cdot
  \\mathrm{softmax}(\\ell)_i$ over the eleven rating tokens. Defined for every
  response.
- **Parsed** — the model's own numeric answer, defined only where generation
  parses.

§4.1 is the comparison. All substantive results (§4.2–§4.5) use parsed
scoring on parse-ok rows, with EV reported alongside.

### 3.5 Inference

Mixed models with a wild cluster bootstrap (Cameron–Gelbach–Miller, Rademacher
weights, null-imposed residuals, *B* = 1999) as the primary test, clustered on
storyline. Cluster counts are small (G = 26–40), where Wald and likelihood-ratio
tests are badly overconfident — a fact this project established independently
on its main run, where a different asymptotic test reproduced Wald's
overconfidence in every cell the bootstrap rejected. Effect coding throughout:
sign (bad +0.5 / good −0.5), tuning (finetuned +0.5 / pretrained −0.5).
Holm correction within (family, tuning, question).

---

## 4. Results

### 4.1 Scoring method decides the answer (C1)

Agreement between EV and the model's own stated rating, on parse-ok rows,
instruction-tuned checkpoints:

| question | Gemma | Llama | Mistral | contrasts flipping significance |
|---|---:|---:|---:|---:|
| praise | .761 | .558 | .812 | **0 / 30** |
| blame | .823 | .656 | .773 | 5 / 30 (all pretrained) |
| intentionality | **.180** | **.146** | .421 | **14 / 30** |

Pretrained checkpoints agree at *r* = .026–.227 across all three questions.

Two observations do the work.

**The failure is question-shaped, not model-shaped or tuning-shaped.** The
same checkpoint, on the same items, in the same run, yields a usable
logprob reconstruction for "how blameworthy is X" and an unusable one for
"did X intentionally cause Y". Prior treatments of this artifact — including
this project's own earlier analysis — framed it as a pretrained/low-parse-rate
problem. It is not.

**Parse rate does not diagnose it.** Gemma-instruct parses intentionality
*better* than blame (58.1% vs. 53.0%) and lands at *r* = .180 against .823.
A parse-rate threshold — the current reporting convention — passes this cell.
The diagnostic that works is agreement between the two scores, which requires
computing both.

Consequences for the substantive results are not uniform, and that is the
point: rescoring leaves praise untouched, leaves every instruction-tuned blame
cell untouched, and rewrites intentionality. Two conclusions reverse outright.
One published-direction effect — a moral-specific asymmetry in Llama — vanishes
(β = 0.93, *p* = .002 → −0.13, *p* = .79). One null becomes a large effect —
Gemma's intentionality asymmetry goes from undetectable in every arm to
significant in every arm. [[TODO: one sentence on why this matters beyond this
paper — the convention is used wherever models are scored on graded judgments.]]

### 4.2 Instruction tuning increases the asymmetry (C2)

Fitting `rating ~ sign × tuning` per family and arm and bootstrapping the
interaction (estimates below are the bootstrap's own `beta_obs`, so estimate
and test pair): **8 of 12 cells significant, 11 of 12 positive**, no negative
interaction anywhere under either scoring. Every family retains at least one
significant cell.

| pilot | family | arm | pretrained | finetuned | interaction | *p* |
|---|---|---|---:|---:|---:|---:|
| nonmoral | Gemma | moral | −0.12 | 2.18 | **+2.32** | .001 |
| nonmoral | Gemma | nonmoral | −0.24 | 2.73 | **+2.95** | <.001 |
| nonmoral | Llama | moral | 0.06 | 0.02 | −0.08 | .90 |
| nonmoral | Llama | nonmoral | −0.88 | −0.09 | **+0.79** | .002 |
| nonmoral | Mistral | moral | 0.49 | 1.19 | +0.70 | .18 |
| nonmoral | Mistral | nonmoral | 0.08 | 0.82 | **+0.74** | .006 |
| foundations | Gemma | harm | −0.25 | 4.15 | **+4.40** | <.001 |
| foundations | Gemma | non-harm | 0.03 | 4.43 | **+4.41** | <.001 |
| foundations | Llama | harm | −0.33 | 0.66 | **+1.01** | .031 |
| foundations | Llama | non-harm | 0.01 | 0.29 | +0.28 | .49 |
| foundations | Mistral | harm | −0.17 | 1.75 | **+1.92** | .002 |
| foundations | Mistral | non-harm | 0.66 | 1.00 | +0.34 | .45 |

**The scoring artifact was suppressing this result, not producing it.**
Gemma's interaction is 2–4× larger under correct scoring (nonmoral moral
0.11 → 2.32; harm 1.14 → 4.40). This is the opposite of the artifact's effect
on moral-specificity in §4.1, and is worth stating plainly: a measurement
problem can hide a real effect as easily as manufacture a false one.

**Two routes, not one.** Gemma and Mistral move from ≈0 to large positive:
instruction tuning installs the asymmetry. Llama moves from a significantly
*negative* pretrained slope to zero (−0.88 → −0.09): instruction tuning erodes
an anti-Knobe prior without installing a positive effect. [[TODO: this is the
paper's most mechanistically suggestive result and deserves discussion — it
implies "does the model show the effect" and "did tuning change the model"
can come apart.]]

*Caveat to carry:* intentionality only. Pretrained blame and praise parse at
25.5–29.9%, too thin to support the contrast. This table is not
Holm-corrected; Gemma's four cells survive correction over all twelve
trivially, Llama's harm cell (*p* = .031) does not.

### 4.3 Blame and praise dissociate within identical items (C4)

Each family's blame swing against its own praise swing, same vignettes, same
wording, differing only in the question asked:

| family | arm | blame | praise | stronger |
|---|---|---:|---:|---|
| Gemma | moral | 1.81 | 1.11 | blame |
| Gemma | nonmoral | 5.62 | 2.76 | blame |
| Llama | moral | 1.61 | 0.76 | blame |
| Llama | nonmoral | 4.73 | 2.54 | blame |
| Mistral | moral | 1.48 | 3.39 | **praise** |
| Mistral | nonmoral | 3.74 | 4.92 | **praise** |

All twelve swings individually significant; 17 of the 18 cells this and §4.4
rest on survive Holm correction.

The human prior here is the negativity-bias literature — bad is stronger than
good (Baumeister et al.) — which predicts blame should swing harder. Gemma and
Llama obey it in both domains. Mistral inverts it in both.

**This comparison is why the paper's scoring rule is load-bearing rather than
pedantic.** A cross-question magnitude comparison presupposes a common scale.
EV does not supply one — its compression depends on the shape of a
per-question logprob distribution — and the instability is observable: under
EV the raw and SD-standardized verdicts disagree in 2 of 6 cells, while under
parsed scoring they agree in 6 of 6.

This is also the paper's best-identified result. Both questions are asked of
identical items, so item composition, stakes, and the §3.2 curation attrition
are differenced out exactly. Nothing is being matched, so nothing can be
mismatched.

### 4.4 The domain effect lives entirely in the good-outcome cell (C3)

Splitting the moral-versus-nonmoral difference by sign, instruction-tuned:

| | moral good | nonmoral good | **good gap** | moral bad | nonmoral bad | bad gap | ratio |
|---|---:|---:|---:|---:|---:|---:|---:|
| blame, Gemma | 7.10 | 2.09 | **+5.02** | 8.92 | 7.71 | +1.21 | 4.2× |
| blame, Llama | 6.92 | 2.66 | **+4.27** | 8.53 | 7.39 | +1.14 | 3.7× |
| blame, Mistral | 7.00 | 4.07 | **+2.93** | 8.48 | 7.81 | +0.67 | 4.4× |
| praise, Gemma | 1.27 | 3.15 | **−1.87** | 0.17 | 0.39 | −0.22 | 8.4× |
| praise, Llama | 0.96 | 3.15 | **−2.18** | 0.20 | 0.61 | −0.41 | 5.4× |
| praise, Mistral | 4.37 | 6.18 | **−1.80** | 0.98 | 1.26 | −0.28 | 6.5× |

Bad-outcome agents are judged nearly alike across domains. Good-outcome agents
are not: producing a good outcome while professing indifference draws blame
around 7/10 when the side effect concerns others' welfare and 2–4/10 when it
does not, and correspondingly less praise.

Blame and praise point the same way here. This is one phenomenon, not two
constructs diverging — a correction we owe to an earlier analysis of our own,
which read praise's positive interaction coefficient as an opposite lean
without accounting for praise's negative baseline slope.

**Is this about moral domain, or about stakes?** The obvious rival reading is
that indifference toward babies simply concerns more than indifference toward
a report's font. The prudential/procedural split measures that gradient
directly, within the nonmoral arm and within the good-outcome cell:

| question | procedural | prudential | moral | stakes step | moral jump | jump in steps |
|---|---:|---:|---:|---:|---:|---:|
| blame, Gemma | 1.73 | 2.72 | 7.10 | +0.99 | +4.38 | **4.4×** |
| blame, Llama | 2.20 | 3.25 | 6.92 | +1.06\* | +3.67 | **3.5×** |
| blame, Mistral | 3.57 | 4.64 | 7.00 | +1.07\* | +2.36 | **2.2×** |
| praise, Gemma | 2.99 | 3.39 | 1.27 | +0.41 | −2.12 | — |
| praise, Llama | 3.59 | 2.63 | 0.97 | −0.97\* | −1.66 | — |
| praise, Mistral | 6.14 | 6.22 | 4.37 | +0.09 | −1.85 | — |

For blame a stakes gradient exists but is small, and the moral jump is 2.2–4.4
gradient-steps — not one step further along the same line. For praise there is
no coherent gradient at all: two nulls and one significant result in the wrong
direction, alongside the full moral effect. A stakes account has to explain why
praise shows the effect without showing the gradient it would need.

*Limitation, blame only:* the argument is ordinal. We do not measure the stakes
*distance* from prudential to moral, so "2.2–4.4 steps" assumes comparable
steps. A stakes rating would make this quantitative.

**The confound we cannot yet characterize.** This effect is concentrated in
the good-outcome moral cell — the one cell that lost 65% of its items to
curation (§3.2), retaining the 14 of 40 that scored highest on moral
relevance. Differential selection of exactly this kind predicts exactly this
pattern. We state this beside the result rather than below it.

> `[[PLACEHOLDER — curation provenance analysis, three parts, pending
> moral_relevance_raw.jsonl and selection_report.md:]]`
> 1. *Distribution comparison.* Moral-relevance scores of the 14 retained
>    moral-good items versus the 26 dropped. If the retained items are drawn
>    from the upper tail, quantify how far.
> 2. *Within-survivor regression.* Does an item's moral-relevance score
>    predict its blame rating among the 14 retained? A positive slope makes
>    the selection account concrete; a flat one weakens it substantially.
> 3. *Threshold-matched sensitivity.* Refit §4.4 restricting all arms to a
>    common selection threshold, so retained moral-good items are no longer
>    a more strongly selected subset than the nonmoral comparisons.

### 4.5 Domain generality and typicality (C5, C6)

**Generality.** No family shows a significant moral-vs-nonmoral or
harm-vs-non-harm interaction on intentionality under correct scoring. Bounding
those nulls, only Gemma's are informative — its design rules out an interaction
as large as the asymmetry itself (bounds 1.41 < 2.71 and 1.58 < 4.44). Mistral's
are underpowered, needing G = 75 and G = 48 respectively. Llama's are vacuous:
under correct scoring Llama-instruct shows no significant intentionality
asymmetry in any arm of either extension, so there is no effect to be general
about. We report this as a one-family result.

**Typicality.** [[TODO: pull the main-run typicality reversal (C6) — the
bad-over-good gap is larger for typical actions and shrinks for atypical ones,
in Gemma and Mistral, opposite to the human exacerbation pattern. Decide
whether this belongs in this paper or is held for a companion; it comes from
a different stimulus release and may dilute the Ngo-extension story.]]

---

## 5. Limitations

### 5.1 Curation attrition
As §3.2 and §4.4. The single largest threat to C3, unresolved pending
provenance recovery.

### 5.2 Exploratory status
These analyses were not preregistered. Holm correction is applied within
(family, tuning, question), which is a defensible grouping and not a
prescribed one; a coarser grouping would tighten every threshold. The clean
remedy is a preregistered confirmatory replication on fresh storylines, which
variance-component analysis indicates should add clusters rather than samples.

### 5.3 Non-replication of Raimondi et al.
Mistral does not reproduce their finetuned effect, on two independent tests
at a 98.2% parse rate. [[TODO: report after the weights-revision and
chat-template check; until then state as unresolved rather than as a finding.]]

### 5.4 No human baseline
By design (§1). All human comparisons are to published results on related but
not identical stimuli.

### 5.5 Scale
Three model families at 7–9B parameters. Nothing here speaks to scale
trends or to frontier models.

---

## 6. Discussion

[[TODO: authors' prose. Load-bearing points, in the order they should land:]]

1. **A scoring convention is a research finding.** The community reports parse
   rates; we show parse rates do not diagnose the failure and agreement does.
   Concrete recommendation: compute both scores and report their correlation
   per question, or use constrained decoding.
2. **"Does the model show the effect" and "did tuning change the model" come
   apart** (§4.2's two routes). Llama's erosion pattern is invisible to any
   analysis that only asks whether the finetuned checkpoint shows the effect.
3. **Auditing one moral construct does not transfer to another.** Blame and
   praise dissociate within identical items and in a family-dependent
   direction (§4.3), so an audit of intent-attribution says little about an
   audit of blame-attribution on the same events.
4. **The good-outcome asymmetry is the most human-suggestive result and the
   least secure** (§4.4). Handle honestly; do not lead the discussion with it.
5. **Cross-family heterogeneity is the finding, not noise.** Three
   independently-trained families answer three of these questions three ways.
   Any claim about "the" LLM moral prior is underdetermined by a single model.

---

## Reproducibility

All analysis scripts, summary tables, and the per-response elicitation dumps
are in the project repository; `results/ANALYSIS_LOG.md` records each run's
command, parameters, outcome, and commit. Claim-to-table mapping is in
`docs/submission_plan/CLAIMS.md`.
