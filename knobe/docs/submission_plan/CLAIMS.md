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

**Confidence tiering — added 2026-09-13 after review.** The first version of
this doc presented all six claims at one level, which overstated two of them.
Today's gameplan work (§5 items 1, 2, 2a, 2b, 2c) consisted entirely of
**measurement** gates. Those settled which claims survive the scoring
question and are now closed. They did not touch the **stimulus** gates —
severity matching and curation selection — and those are exactly what the
arm-vs-arm claims depend on.

| tier | claims | status |
|---|---|---|
| **A — draftable now** | C1, C2, C4, C6 | Gates closed. Design does not rest on arm-vs-arm matching |
| **A− — draftable, one open confound** | C3 | Stakes rival reading tested and largely ruled out (`710b4c3`); curation attrition still uncharacterized |
| **B — underpowered** | C5 | One family, inherits attrition, needs G=48–75 for the other two |

**On severity, corrected.** An earlier version of this section said the
severity question was C3's biggest problem and that a ~400-call curation pass
was the highest-value remaining task. That was wrong on both counts. The main
run's severity confound was an authoring accident specific to *its* taxonomy
(MB written around genuine harm, NMB written to be low-stakes, nothing
enforcing parity); the pilots don't inherit that taxonomy. The version that
does transfer is a rival *interpretation* — that C3 tracks stakes rather than
moral domain — and the pilot already contained the discriminating comparison
in its prudential/procedural split. See C3.

Write Tier A and C3 now. Hold C5.

---

## The claims, in the order the paper should make them

### C1 (Tier A) — Logprob-EV scoring is question-dependent and can invert conclusions

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

### C2 (Tier A) — Instruction tuning increases the outcome-valence asymmetry

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
count. **Not Holm-corrected**: `tuning_contrast_wcb_parsed.csv` sits outside
`holm_correct_pilots.py`'s scope and its grouping is an open judgment call.
gemma's four cells (p≤.0005) survive Holm over all 12 trivially; llama's MF
harm cell (p=.0305) would not.
*Provenance:* `1bc6e12`. Table: `tuning_contrast_wcb_parsed.csv`.
*Note:* point 1's original "6/6" was six split-sample fits compared by eye.
This is the first actual test of the difference.

### C3 (Tier B) — Outcome moves blame far less in moral than nonmoral scenarios

**Rewritten 2026-09-14 after review. The previous version overstated this in
three ways; they are recorded below rather than deleted.**

**What is established.** The moral-vs-nonmoral × sign interaction is
significant in all three families for blame and two of three for praise.
Decomposed by sign, the domain gap is 3.7–4.4× larger in the good-outcome
cell than the bad one (5.4–8.4× for praise). Equivalently, stated as
within-domain sensitivity:

| | moral: good → bad | swing | nonmoral: good → bad | swing |
|---|---|---:|---|---:|
| blame, gemma | 7.10 → 8.92 | 1.81 | 2.09 → 7.71 | 5.62 |
| blame, llama | 6.92 → 8.53 | 1.61 | 2.66 → 7.39 | 4.73 |
| blame, mistral | 7.00 → 8.48 | 1.48 | 4.07 → 7.81 | 3.74 |

That is the finding: **within moral scenarios blame is relatively
insensitive to how the outcome turned out; within nonmoral scenarios it is
not.** Everything past that sentence is interpretation.

**What is not established — three live readings, none ruled out.**

1. *Indifference-tracking.* Blame follows the agent's stated mental state,
   which is held constant across sign by design, so it stays flat where the
   indifference is culpable.
2. *Content asymmetry.* Moral-good items contain reckless indifference about
   serious third-party consequences; nonmoral-good items contain indifference
   about a style guide or a seating chart. Blaming the first and not the
   second may simply be correct, in which case there is no bias here at all.
3. *Differential selection.* The moral-good cell lost **65% of its items to
   curation** (14/40 vs. 97.5% for moral-bad and 82.5–95% for all nonmoral
   cells), retaining those that scored highest on moral relevance. This
   predicts the pattern directly, and it is the cell the whole interaction
   rests on.

**Correction — the stakes test does less than previously claimed.** An
earlier version of this entry said a stakes reading was "largely ruled out"
by the prudential/procedural gradient (`710b4c3`). That test varies who bears
the consequence *among self-directed and conventional outcomes* — prudential
items are about the agent's own job security or retirement account. It never
varies third-party stakes, because by construction no arm has serious
third-party consequences without being moral. **Moral domain and
serious-third-party-consequence are confounded in this design and cannot be
separated by it.** The gradient result still stands on its own terms; it just
does not adjudicate what it was said to adjudicate.

**Two further corrections to the earlier entry.** It described this as "an
agent who brings about a good outcome being blamed more," which misreads what
is judged — the agent is being rated on conduct that includes professed
indifference, not on the good outcome. And it called the pattern "the most
direct support yet for the indifference-tracking reading," which asserts
reading 1 over readings 2 and 3 without evidence.

*Strength:* the pattern is solid and survives Holm; the explanation is open,
and the cell carrying it is the compromised one. **Tier B, not A−.**
*Provenance:* `0dc641b` (decomposition), `395a9ed` (attrition),
`710b4c3` (stakes gradient). Tables: `domain_gap_decomposition.csv`,
`selection_attrition.csv`, `stakes_gradient_check.csv`.

### C4 (Tier A) — Blame-vs-praise sensitivity is family-dependent

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
*Multiplicity:* survives. 17 of the 18 cells C3 and C4 rest on hold under
Holm on the parsed tables (`20e22e2`); the sole failure is mistral's praise
interaction, already ns at p=.0625.
*Provenance:* `244db46`, `20e22e2`. Tables: `blame_praise_swing.csv`,
`sign_wcb_holm_summary_parsed.csv`.

### C5 (Tier B) — In gemma, the asymmetry is not specific to morality or to harm

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

### C6 (Tier A) — Typicality runs opposite to the human pattern (v1.1 main run)

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

**Blocks C3 and C5 from Tier A — the severity pass.** ~400 reviewer calls
using the existing `curate_*_relevance.py` machinery plus a severity
question. Neither pilot has any severity data, so this is the difference
between "C3 is an indifference-tracking finding" and "C3 may be a severity
finding." It is the single highest-value remaining task and it is cheap.

**Also blocks C3 as written:** the four curation provenance files
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
