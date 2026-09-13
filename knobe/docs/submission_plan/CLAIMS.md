# Claim Set for the Paper Draft (2026-09-13)

**Status:** the claim inventory to write from. `SUBMISSION_GAMEPLAN.md` is a
planning doc carrying its own revision history; this is the flattened,
current statement of what the paper asserts, each claim with the test behind
it, the scoring it depends on, the caveat that must ship with it, and the
commit it traces to.

**Scoring convention for the whole paper.** Every claim below is stated under
`parsed_rating` (the model's own numeric answer, parse_ok rows) unless marked
otherwise. EV scoring appears only as a robustness comparison and in the
measurement section. Rationale is C1.

**Scope.** All pilot claims are finetuned/instruct checkpoints unless the
claim is explicitly about tuning. Both pilots use Ngo-derived storylines;
the v1.1 main run contributes C6 and the inference machinery only.

---

## The claims, in the order the paper should make them

### C1 — Logprob-EV scoring is question-dependent and can invert conclusions

Reconstructing a 0–10 rating from first-token logprobs agrees with the
model's own stated answer for some question wordings and not others, on the
same items in the same run. Substituting the stated answer flips **14 of 30**
intentionality cells and **0 of 30** praise cells.

| question | ev/parsed agreement (finetuned) | cells flipping |
|---|---|---|
| q_praise | r = .56–.81 | 0/30 |
| q_blame | r = .66–.82 | 5/30 (all pretrained) |
| q_intentionality | r = **.146–.421** | 14/30 |

**The diagnostic is agreement, not parse rate.** gemma-instruct parses
intentionality *better* than blame (58.1% vs. 53.0%) and still lands at
r=.180 vs. .823. A parse-rate check would have passed this cell.

*Strength:* highest in the paper. Descriptive, no inference, same items,
same run, one variable differs.
*Caveat:* the mechanism — why a question that asks for a number yields a
usable logprob vector and one that invites a verdict does not — is proposed,
not tested.
*Provenance:* `395a9ed`, `6c73ab6`. Tables: `measurement_audit.csv`,
`sign_wcb*_parsed.csv`.

### C2 — Instruction tuning increases the outcome-valence asymmetry

Formal `sign_c × tuning_c` interaction per (pilot, family, arm):
**8 of 12 cells significant, 11 of 12 positive**, every family retaining at
least one significant cell. No negative interaction anywhere, under either
scoring.

gemma's interaction is **2–4× larger under parsed than under EV** (nonmoral
moral 0.11 → 2.32; MF harm 1.14 → 4.40) — the artifact was suppressing this
result, not producing it.

**Two mechanisms, not one.** gemma and mistral move from ≈0 pretrained to
large positive. llama moves from a significantly *negative* pretrained slope
to zero (nonmoral pooled −0.88 → −0.09): erosion of an anti-Knobe prior
rather than installation of a positive effect. The v1.1 main run reached the
same reading for llama independently (script 33), so two datasets agree.

*Strength:* high. Not an arm-vs-arm comparison, so neither the severity
confound nor the C-caveat attrition touches it.
*Caveat:* intentionality only — pretrained blame/praise parse at 25.5–29.9%,
too thin. Four cells are ns under parsed; report the cell table, not the
count.
*Provenance:* `1bc6e12`. Table: `tuning_contrast_wcb_parsed.csv`.
*Note:* point 1's original "6/6" was six split-sample fits compared by eye.
This is the first actual test of the difference.

### C3 — The moral/nonmoral difference lives entirely in the good-outcome cell

For **both** blame and praise, in **all three** families, the domain
difference is concentrated in good-outcome items; bad-outcome items barely
differ across domains.

| | moral good | nonmoral good | good gap | bad gap | ratio |
|---|---:|---:|---:|---:|---:|
| blame, gemma | 7.10 | 2.09 | **+5.02** | +1.21 | 4.2× |
| blame, llama | 6.92 | 2.66 | **+4.27** | +1.14 | 3.7× |
| blame, mistral | 7.00 | 4.07 | **+2.93** | +0.67 | 4.4× |
| praise, gemma | 1.27 | 3.15 | **−1.87** | −0.22 | 8.4× |
| praise, llama | 0.96 | 3.15 | **−2.18** | −0.41 | 5.4× |
| praise, mistral | 4.37 | 6.18 | **−1.80** | −0.28 | 6.5× |

An agent who brings about a *good* outcome while professing indifference is
blamed more and praised less when the domain is moral. Bad-outcome agents are
treated alike regardless of domain.

This is one phenomenon, not two diverging constructs: blame and praise point
the same way. It is also the most direct support yet for the
indifference-tracking reading (an agent indifferent to *others'* welfare
reads as culpable; one indifferent to *their own* interests does not).

*Strength:* high on the pattern, contested on the explanation.
*Caveat — mandatory, and it is severe:* the moral-good cell is the one that
lost **65% of its items to curation** (14/40 surviving vs. 97.5% for
moral-bad and 82.5–95% for all nonmoral cells). The surviving items were
selected for scoring highest on moral relevance. Differential selection
predicts exactly this pattern. **The effect is concentrated in the one cell
whose composition is compromised.** This must be stated in the same
paragraph as the result, not in a limitations section.
*Provenance:* `0dc641b` (decomposition), `395a9ed` (attrition). Tables:
`domain_gap_decomposition.csv`, `selection_attrition.csv`.

### C4 — Blame-vs-praise sensitivity is family-dependent

On identical items, comparing each family's blame swing against its own
praise swing: gemma and llama obey the human negativity-bias prior (blame
swings harder); **mistral inverts it** in both domains.

| family | arm | blame | praise | bigger |
|---|---|---:|---:|---|
| gemma | moral / nonmoral | 1.81 / 5.62 | 1.11 / 2.76 | blame |
| llama | moral / nonmoral | 1.61 / 4.73 | 0.76 / 2.54 | blame |
| mistral | moral / nonmoral | 1.48 / 3.74 | 3.39 / 4.92 | **praise** |

All twelve swings individually significant. Raw and SD-standardized verdicts
agree in 6/6 cells under parsed (they disagree in 2/6 under EV, which is the
empirical reason C1's scoring rule is load-bearing rather than pedantic).

*Strength:* highest of the substantive claims. Within-item, so item
composition, severity, and the C3 attrition are all differenced out exactly.
Best-measured cells in the project.
*Caveat:* cross-question magnitude comparison presumes both questions use the
0–10 scale comparably; parsed scoring makes that assumption as weak as it can
be made, but it is not zero.
*Provenance:* `244db46`. Table: `blame_praise_swing.csv`.

### C5 — In gemma, the asymmetry is not specific to morality or to harm

No family shows a significant moral-vs-nonmoral or harm-vs-non-harm
interaction under parsed scoring. Equivalence-bounding says only gemma's
nulls are informative:

| family | moral vs nonmoral | harm vs non-harm |
|---|---|---|
| gemma | bound 1.41 < benchmark 2.71 ✓ | bound 1.58 < 4.44 ✓ |
| mistral | 0.95 vs 0.81 — underpowered (needs G=75) | 1.45 vs 1.00 — underpowered (needs G=48) |
| llama | benchmark ≈ 0 — no asymmetry to generalize | benchmark ≈ 0 |

*Strength:* moderate, one family.
*Caveat:* still an arm-vs-arm comparison, so it inherits C3's attrition and
the unchecked severity matching — though a confound would have to
*manufacture* a null here, which is a harder story than manufacturing a
difference. Gemma also shows joint five-foundation heterogeneity (p=.043)
even with its harm-vs-pooled-non-harm null, so the claim is "not privileged
for harm," not "uniform across foundations."
*Provenance:* `03b8f1b`, `70f1a34`. Tables: `equivalence_bounds.csv`,
`foundation_gradient_wcb_parsed.csv`.

### C6 — Typicality runs opposite to the human pattern (v1.1 main run)

The bad>good intentionality gap is *larger* for typical actions and shrinks
or reverses for atypical ones, in gemma and mistral — the reverse of the
human exacerbation result. Survives WCB, an independent family-random-slope
model, and parsed-rating substitution. Absent in llama by three independent
checks.

*Strength:* high; the most robust main-run result.
*Caveat:* `typ_c` main effect and interaction decompose differently by family
(gemma interaction-only, llama main-effect-only, mistral both).
*Provenance:* pre-existing. `RQ1_MECHANISM_ANALYSIS_v1.1.md` §3.

---

## What the paper does not claim

Stated explicitly because earlier drafts did claim several of these.

| Not claimed | Why |
|---|---|
| The asymmetry is moral-specific | Refuted. llama's interaction 0.66 (p=.017) → −0.04 (p=.93) under parsed; no family significant |
| llama shows the largest asymmetry in the study | Artifact. 0/4 nonmoral and 1/6 MF cells significant under parsed; it had the project's worst agreement (r=.146/.130) |
| Blame and praise lean opposite ways on domain | Sign-convention error. Praise's betas are negative, so its positive interaction means a *smaller* moral swing. Both swing bigger outside morality |
| Pretrained models show foundation-specific effects | Artifact. gemma .011 → .295, llama <.001 → .233; only mistral survives |
| Intentionality, blame and praise tell three different stories | Overstated. Blame and praise agree in direction (C3); they differ in magnitude (C4) |
| RQ1a moral-vs-nonmoral (main run) | Stimulus manipulation failure — MB exceeds NMB on severity in 21/21 storylines |
| Any pretrained blame/praise result | 25.5–29.9% parse rates |

---

## Proposed paper skeleton

1. **Intro** — the Knobe asymmetry, Ngo/Raimondi, what a decomposed design buys.
2. **Measurement (C1)** — lead with it. It licenses every later number and is
   the most transferable contribution.
3. **Instruction tuning (C2)** — the asymmetry is installed/amplified, with
   two mechanisms across families.
4. **Where the domain effect lives (C3, C4)** — the good-cell localization
   and the blame/praise sensitivity split. The empirical core.
5. **Generality (C5, C6)** — domain-generality in gemma; the typicality
   reversal.
6. **Limitations** — C3's attrition, unchecked severity, multiplicity,
   mistral/Raimondi non-replication.

C1 first is the important structural choice: it converts the paper's biggest
liability (results that change under rescoring) into its headline
contribution, and it is why the reader should believe C2–C6.

---

## Gates still open

Ranked by whether they block drafting.

**Blocks C3 as written:** the four curation provenance files
(`moral_relevance_raw.jsonl`, `selection_report.md` per pilot). They are the
only way to compare the 26 dropped moral-good items against the 14 that
survived. Without them C3 ships with an unresolvable confound rather than a
characterized one.

**Blocks nothing, strengthens C3/C5:** a severity curation pass over both
pilots (~400 reviewer calls).

**Blocks the Raimondi comparison only:** the mistral weights-revision and
chat-template check.

**Before submission, not before drafting:** multiplicity exposure
(`OUTSTANDING_STATISTICAL_ANALYSIS.md` item 9), and the preregistered
confirmatory run that would convert C2–C4 from exploratory to confirmed.
