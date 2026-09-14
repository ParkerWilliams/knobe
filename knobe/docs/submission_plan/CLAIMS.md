# Claim Inventory (2026-09-14)

**What this is.** An inventory of the claims our experiments support, ordered
by how well they're supported. Not a paper plan — no venue framing, no
section ordering, no pre-commitment to which subset becomes a paper. Those
decisions live in `SUBMISSION_GAMEPLAN.md` and should follow from this rather
than shape it.

**Conventions.** Every claim separates *what is established* from *what is
interpretation*, and names its provenance (script, commit, table). Unless
stated otherwise, claims are about instruction-tuned checkpoints and use
`parsed_rating` scoring on parse-ok rows — see claim 1 for why that choice is
not neutral.

**Sources.** v1.1 main run (378,000 completions, decomposed factorial);
nonmoral extension (88,200 responses, three question types); moral-foundations
extension (18,900 responses, intentionality). Three families — Gemma-2-9B,
Llama-3.1-8B, Mistral-7B-v0.1 — pretrained and instruction-tuned.

---

## Which experiment each claim rests on

| | claim | source |
|---:|---|---|
| 1 | logprob-EV scoring is question-dependent | both extensions |
| 2 | instruction tuning increases the asymmetry | both extensions |
| 3 | the three questions dissociate | **nonmoral only** |
| 4 | blame-vs-praise sensitivity differs by family | **nonmoral only** |
| 5 | asymptotic inference is overconfident at these G | **main run only** |
| 6 | typicality runs opposite to humans | **main run only** |
| 7 | Mistral doesn't replicate Raimondi | **main run only** |
| 8 | not privileged for harm or morality, in Gemma | both extensions |
| 9 | blame is outcome-insensitive in moral scenarios | **nonmoral only** |
| 10 | LLM curation causes differential attrition | both extensions |
| 11 | v1.1's moral/nonmoral comparison is confounded | **main run only** |

**The landscape.** The Ngo extensions carry seven of eleven claims, including
every strongly-supported substantive one. The main run's four unique
contributions are one real behavioural result (6, typicality), one
methodological result (5, inference), one unresolved non-replication (7), and
one negative design finding (11) — and 11 is the reason the main run's own
headline comparison is not reported at all.

So an extensions-only account loses the typicality reversal and the inference
argument, and keeps everything else. That is a defensible scope, and 5 and 11
can still be cited as method precedent without making the main run a
first-class source.

---

## Strongly supported

### 1. Logprob-EV scoring is question-dependent, and parse rate does not diagnose it

When a model does not emit a parseable number, the standard fallback
reconstructs an expected value from the logprobs of the eleven rating tokens.
That reconstruction tracks the model's own stated answer well for some
question wordings and poorly for others, on the same items in the same run:

| question | Gemma | Llama | Mistral | contrasts flipping significance |
|---|---:|---:|---:|---:|
| praise | .761 | .558 | .812 | 0 / 30 |
| blame | .823 | .656 | .773 | 5 / 30 (all pretrained) |
| intentionality | **.180** | **.146** | .421 | **14 / 30** |

Pretrained checkpoints sit at .026–.227 across all three questions.

Two things make this more than a local nuisance. **Parse rate does not detect
it** — Gemma parses intentionality *better* than blame (58.1% vs. 53.0%) and
still lands at .180 against .823, so the sanity check in common use passes
the broken cell. And **the artifact distorts in both directions**: it
manufactured a significant wrong-direction pretrained effect (the earlier
"anti-Knobe" finding, retracted), and it suppressed a real one (Gemma's
tuning contrast, 0.11 → 2.32 once corrected).

*Established:* the agreement figures, the flip counts, the parse-rate
dissociation.
*Interpretation:* that this is about whether a question invites a number
versus a verdict. Plausible, untested.
*Source:* **both Ngo extensions** (the question axis exists only there). The
artifact was first caught in the main run, on one cell.
*Provenance:* `395a9ed`, `6c73ab6` — `measurement_audit.csv`,
`sign_wcb*_parsed.csv`.

### 2. Instruction tuning increases the outcome-valence asymmetry

Fitting `rating ~ sign × tuning` per family and arm and bootstrapping the
interaction: **8 of 12 cells significant, 11 of 12 positive**, no negative
interaction anywhere under either scoring, every family retaining at least
one significant cell.

Two mechanisms, not one. Gemma and Mistral move from ≈0 pretrained to large
positive — tuning installs the asymmetry. Llama moves from a significantly
*negative* pretrained slope to zero (−0.88 → −0.09) — tuning erodes a
reversed prior without installing a positive effect. The v1.1 main run
reached the same reading for Llama independently, so two datasets agree.

This matters partly because "does the model show the effect" and "did tuning
change the model" come apart: Llama's shift is invisible to any analysis that
only tests the tuned checkpoint.

*Established:* the interaction table.
*Caveats:* intentionality only — pretrained blame and praise parse at
25.5–29.9%. Not Holm-corrected (this table sits outside the correction
script's scope); Gemma's four cells survive correction over all twelve
trivially, Llama's harm cell (p = .031) does not.
*Source:* **both Ngo extensions**; the main run reaches the same reading for
Llama independently.
*Provenance:* `1bc6e12` — `tuning_contrast_wcb_parsed.csv`.

### 3. The three questions dissociate on identical items

Under correct scoring, the moral-vs-nonmoral interaction is **absent for
intentionality in every family** and **large for blame in every family**:

| question | Gemma | Llama | Mistral |
|---|---|---|---|
| intentionality | −0.52 (p=.349) | −0.04 (p=.934) | +0.29 (p=.488) |
| blame | **−3.81 (p<.001)** | **−3.13 (p<.001)** | **−2.26 (p=.003)** |
| praise | **+1.65 (p=.010)** | **+1.78 (p<.001)** | +1.53 (p=.063) |

This is the best-identified substantive result in the set, for a structural
reason: it is a within-item comparison *across questions*. The same
vignettes, the same run, differing only in what was asked — so item
composition, stakes, and the curation attrition in claim 10 are all
differenced out exactly. It survives the confound that claim 9's magnitude
does not.

The practical reading: asking a model whether an act was intentional and
asking who is to blame for it are not interchangeable probes of the same
underlying judgment, and an audit of one says little about the other.

*Established:* the dissociation, and its immunity to item-composition
confounds.
*Interpretation:* anything about *why* the constructs come apart.
*Source:* **nonmoral extension only** — the only dataset with three question
types on the same items.
*Provenance:* `6c73ab6` — `sign_wcb{,_blame,_praise}_parsed.csv`.

### 4. Blame-vs-praise sensitivity differs by family

Each family's blame swing against its own praise swing, same vignettes:

| family | arm | blame | praise | stronger |
|---|---|---:|---:|---|
| Gemma | moral / nonmoral | 1.81 / 5.62 | 1.11 / 2.76 | blame |
| Llama | moral / nonmoral | 1.61 / 4.73 | 0.76 / 2.54 | blame |
| Mistral | moral / nonmoral | 1.48 / 3.74 | 3.39 / 4.92 | **praise** |

All twelve swings individually significant; 17 of the 18 cells claims 3, 4
and 9 rest on survive Holm correction. Raw and SD-standardized verdicts agree
in 6/6 cells under parsed scoring and disagree in 2/6 under EV — which is the
empirical reason claim 1's scoring rule is load-bearing rather than
pedantic, since EV's compression depends on a per-question logprob
distribution and so supplies no common scale for a cross-question magnitude
comparison.

Also within-item, so the same identification argument as claim 3 applies.

*Established:* the swing comparison.
*Interpretation:* reading Mistral's inversion against the human
negativity-bias literature. We have no human data on these items; the prior
is general, not stimulus-matched.
*Source:* **nonmoral extension only.**
*Provenance:* `244db46` — `blame_praise_swing.csv`.

### 5. Asymptotic inference is badly overconfident at these cluster counts

At G = 21–84, Wald tests substantially overstate significance, and a
likelihood-ratio test reproduces the same overconfidence in exactly the cells
the wild cluster bootstrap rejects. This is why the bootstrap is the
estimator of record throughout, and it overturned several first-pass findings
in the main run.

*Established:* the cell-by-cell agreement between Wald and LRT overconfidence.
*Source:* **v1.1 main run only.**
*Provenance:* pre-existing — `rq1_v1_1_robustness/08`, `24`;
`OUTSTANDING_STATISTICAL_ANALYSIS.md` items 7–8.

---

## Moderately supported

### 6. Typicality runs opposite to the human exacerbation pattern

In Gemma and Mistral, the bad-over-good intentionality gap is *larger* for
typical actions and shrinks or reverses for atypical ones — the reverse of
the human finding that atypicality exacerbates the asymmetry. Survives the
bootstrap, an independent family-random-slope model, and parsed-rating
substitution. Absent in Llama by three independent checks.

*Caveat:* the main effect and interaction decompose differently by family
(Gemma interaction-only, Llama main-effect-only, Mistral both), so "the same
effect in 2 of 3 families" understates the heterogeneity.
*Source:* **v1.1 main run only.**
*Provenance:* pre-existing — `RQ1_MECHANISM_ANALYSIS_v1.1.md` §3.

### 7. Mistral does not replicate Raimondi et al.'s finetuned effect

Null on two independent tests at a 98.2% parse rate, so not a measurement
gap. Gemma and Llama replicate on the same stimuli and pipeline, which rules
out most shared-infrastructure explanations.

*Open:* the cheap diagnostics — weight revision tag and chat-template
handling — have not been run. Until they are, this is unresolved rather than
a finding about the model.
*Source:* **v1.1 main run only** (moral-only subset, matched to Raimondi's scope).
*Provenance:* pre-existing — `RAIMONDI_REPLICATION_GAPS.md` §4.

### 8. In Gemma, the asymmetry is not privileged for harm or for morality

No family shows a significant moral-vs-nonmoral or harm-vs-non-harm
interaction on intentionality under correct scoring. Equivalence-bounding
shows only Gemma's nulls are informative — its design rules out an
interaction as large as the asymmetry itself (1.41 < 2.71; 1.58 < 4.44).
Mistral's are underpowered (needs G = 75 and 48). Llama's are vacuous: it
shows no significant intentionality asymmetry in any arm of either extension
under correct scoring, so there is nothing to be general about.

*Caveat:* Gemma still shows joint heterogeneity across the five foundations
(p = .043) despite its harm-vs-pooled-non-harm null, so "not privileged for
harm" is the claim, not "uniform across foundations."
*Source:* **both Ngo extensions** — moral-vs-nonmoral from one, harm-vs-non-harm
from the other.
*Provenance:* `03b8f1b`, `70f1a34` — `equivalence_bounds.csv`,
`foundation_gradient_wcb_parsed.csv`.

---

## Pattern solid, explanation open

### 9. Blame is far less outcome-sensitive in moral than nonmoral scenarios

| | moral: good → bad | swing | nonmoral: good → bad | swing |
|---|---|---:|---|---:|
| Gemma | 7.10 → 8.92 | 1.81 | 2.09 → 7.71 | 5.62 |
| Llama | 6.92 → 8.53 | 1.61 | 2.66 → 7.39 | 4.73 |
| Mistral | 7.00 → 8.48 | 1.48 | 4.07 → 7.81 | 3.74 |

Equivalently: the domain gap is 3.7–4.4× larger in the good-outcome cell than
the bad one for blame, 5.4–8.4× for praise.

**Three live readings, none ruled out.** (a) *Indifference-tracking* — blame
follows the agent's stated mental state, held constant across sign by design.
(b) *Content asymmetry* — moral-good items contain reckless indifference
about serious third-party consequences while nonmoral-good items concern a
style guide or a seating chart, so blaming the first and not the second may
simply be correct, in which case there is no bias here. (c) *Differential
selection* — the moral-good cell lost 65% of its items to curation (claim 10)
and retained the most morally loaded, which predicts this pattern directly.

**A design limit worth stating explicitly.** The three arms differ in *who
bears the consequence*: third parties (moral), the agent themselves
(prudential), a convention (procedural). So moral domain and
serious-third-party-consequence are confounded by construction, and no
contrast in this design separates them. The prudential/procedural stakes
gradient (`710b4c3`) varies stakes among self-directed and conventional
outcomes only; it does not adjudicate this.

*Established:* the pattern, and that it survives Holm.
*Not established:* the explanation, and whether this is a defect at all.
*Source:* **nonmoral extension only.**
*Provenance:* `0dc641b`, `395a9ed`, `710b4c3` —
`domain_gap_decomposition.csv`, `selection_attrition.csv`,
`stakes_gradient_check.csv`.

---

## Findings about method, not about models

### 10. LLM-reviewer curation with a valence-asymmetric question causes severe differential attrition

Both extensions authored balanced designs and screened them with an LLM
reviewer. The nonmoral extension's question named only the violation pole, so
good-sign items scored near zero regardless of authoring quality:

| arm | bad | good |
|---|---:|---:|
| moral | 97.5% (39/40) | **35.0% (14/40)** |
| nonmoral, procedural | 92.5% | 95.0% |
| nonmoral, prudential | 87.5% | 82.5% |

The foundations extension hit the same problem and switched to pair-level
gating mid-curation, which preserved perfect balance in every cell. That
contrast — same team, same reviewer, same week, two selection rules, one
catastrophic imbalance — is a clean demonstration.

This is generalizable and, as far as we know, undiscussed: anyone screening
stimuli with an LLM reviewer on a valence-asymmetric question will hit it,
and the failure is silent unless per-cell survival is inspected.

*Source:* **both Ngo extensions** — the contrast between their two selection
rules is the finding.
*Provenance:* `395a9ed` — `selection_attrition.csv`.

### 11. The main run's moral/nonmoral comparison is confounded by stimulus design

Moral-bad items exceed nonmoral-bad on reviewer-rated severity in **21 of 21**
storylines, mean gap 5.42 points. Severity correlates with sign at r = .885
within moral items, and family-mean severity occupies nearly disjoint ranges
by valence. No regression term fixes a manipulation that was never matched;
this is a design finding, not a statistical one, and it is why that
comparison is not reported as a result.

*Source:* **v1.1 main run only.**
*Provenance:* pre-existing — `RQ1_MECHANISM_ANALYSIS_v1.1.md` §1.

---

## What we do not claim

Recorded because earlier drafts asserted several of these.

| not claimed | why |
|---|---|
| The asymmetry is moral-specific | Refuted. Llama's interaction 0.66 (p=.017) → −0.04 (p=.93) under correct scoring; no family significant |
| Llama shows the largest asymmetry in the study | Artifact. 0/4 nonmoral and 1/6 foundation cells significant under parsed; it had the project's worst score agreement |
| Blame and praise lean opposite ways on domain | Sign-convention error. Praise's betas are negative, so its positive interaction means a *smaller* moral swing. Both swing bigger outside morality |
| Pretrained models show foundation-specific effects | Artifact. Gemma .011 → .295, Llama <.001 → .233; only Mistral survives |
| Intentionality, blame and praise tell three different stories | Overstated. Blame and praise agree in direction; they differ in magnitude (claim 4) |
| Models are "biased" in claim 9 | Reading (b) says the behavior may be correct. Unresolved |
| Models are less susceptible to moral luck than people | No human data exists. Asserted in discussion, withdrawn |
| Any pretrained blame/praise result | 25.5–29.9% parse rates |
| The v1.1 moral-vs-nonmoral comparison | Claim 11 |

---

## Mapping to the older C-numbers

`paper/DRAFT.md` still references the previous `C1`–`C6` scheme:

| old | new |
|---|---|
| C1 measurement | 1 |
| C2 instruction tuning | 2 |
| C3 good-outcome localization | 9 (rewritten and downgraded) |
| C4 blame-vs-praise | 4 |
| C5 domain generality | 8 |
| C6 typicality | 6 |

Claims 3, 5, 7, 10 and 11 had no C-number. The draft's cross-references need
a pass.
