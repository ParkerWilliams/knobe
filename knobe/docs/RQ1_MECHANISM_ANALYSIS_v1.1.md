# Teasing Apart the Knobe Effect in LLMs — Mechanism Analysis, Release v1.1 (revised 2026-08-10)

**Status:** exploratory research note, not a preregistered writeup. **This is
a full revision of the first pass**, after a small-cluster-robust
re-analysis (wild cluster bootstrap, a severity-covariate refit, and a
family-random-slope check — full methodology in
`docs/RQ1_STATISTICAL_METHODS_v1.1.md` §8–§11) showed that several of the
first pass's headline findings were artifacts of trusting asymptotic
standard errors at small cluster counts (as few as 21 family clusters) and a
random-intercept-only model that assumes every effect is constant across
families. Where a finding survived rigorous re-testing, it's kept, usually
with a smaller effect or narrower scope than first reported. Where it didn't
survive, that's stated plainly, not hedged into ambiguity. The RQ1a/RQ1b/RQ1c
contrasts are the frozen `configs/contrasts.yaml` fits (same numbers as
`docs/MAIN_RUN_WRITEUP_v1.1.md`); the valence-type-split sign effect, the
typicality/evocativeness gap tables, the severity/WCB/random-slope checks,
and the affect-decoupling analysis are exploratory follow-ups, not yet
pipeline artifacts.

**Motivating question:** the human Knobe literature treats intentionality
ascription as downstream of evaluation of a side effect — a "wag the dog"
result, since folk intuition treats intentionality as the more basic concept
feeding moral judgment, not the reverse. Four sub-questions decompose that
single finding into testable pieces this dataset's five-category taxonomy and
independent blame/praise/typicality/evocativeness manipulations make askable:
(1) is the evaluative effect driven by *any* negative valence or by *moral*
badness specifically; (2) does *blameworthiness* (graded) do more work than
mere good/bad valence; (3) does typicality *exacerbate* the asymmetry, as
reported in humans; (4) does affective response carry the same exacerbating
role in these models.

All numbers below use the finetuned/instruct checkpoint unless noted,
EV-scored uniformly from forced-scoring logprobs (spec §4.4). "Survives WCB"
means the effect cleared a wild cluster bootstrap test (Cameron-Gelbach-Miller,
1999 resamples, clustered on the actual experimental unit — family or
storyline-set, whichever the contrast's design calls for) at α=.05; this is a
properly-sized test at the cluster counts this dataset has (21–84), unlike
the primary model's own Wald p-value.

---

## 1. Any negative evaluation, or moral badness specifically?

**What survives:** testing the sign effect (bad vs. good) separately within
the moral-only and nonmoral-only subsets, in gemma and llama specifically:

| family | moral-only: bad−good | WCB p | nonmoral-only: bad−good | WCB p |
|---|---|---|---|---|
| gemma | +0.368 | **.021** | +0.276 | .436 |
| llama | +0.658 | **.0005** | +0.028 | .918 |
| mistral | +0.062 | .408 | −0.201 | .060 |

**For gemma and llama, this specific test holds up: purely nonmoral badness
does not move intentionality ratings, while moral badness does, robustly.**
This is the cleanest surviving evidence that the base "wag the dog" effect
(evaluation of a side effect shifting the intentionality call) is at least
partly moral-specific rather than a generic negativity response, in these
two families. Mistral shows neither effect reliably (moral p=.41; nonmoral
trends negative but doesn't clear WCB, p=.06).

**What does NOT survive:** the formal test of moral-specificity —
`rq1a_sign_x_valence_type`, the interaction that directly asks "is the
bad>good gap *bigger* for moral than nonmoral items" in one pooled model —
fails once properly tested. Under the primary family-clustered model it was
underpowered (gemma p=.80, llama p=.09, mistral p=.03); refitting on
`set_id` clustering (the matched five-valence-sibling structure) initially
looked like it rescued all three (p=.0014/.0000/.0000), but that used the
same asymptotic Wald approach that's unreliable at only 21 clusters. Redone
as a wild cluster bootstrap:

| family | baseline WCB p (no severity, severity-complete subsample) | +severity-covariate WCB p |
|---|---|---|
| gemma | .640 | .655 |
| llama | **.0045** | .222 |
| mistral | **.001** | .564 (point estimate flips sign negative) |

(One family, WORK-MG-02, has no curation severity record and is dropped from
both columns here for an apples-to-apples comparison; the standalone
full-84-family baseline WCB — no severity model in play — gives very
slightly different numbers with the identical qualitative pattern: gemma
.512, llama .003, mistral <.0001. See
`analysis/rq1_v1_1_robustness/03_rq1a_baseline_wcb.py` vs.
`04_rq1a_severity_covariate.py`. The +severity numbers here are also
corrected from an earlier pass: `severity_c` is a continuous, family-level
covariate, so a plain-pooled-OLS bootstrap refit is biased for the same
reason RQ1b's was — a set-fixed-effects refit fixes it, per
`docs/RQ1_STATISTICAL_METHODS_v1.1.md` §9.)

Adding reviewer-rated severity as a covariate (MB averages 7.0/10 severity,
NMB averages 1.6 — moral and nonmoral items are not intensity-matched in this
stimulus set) kills the interaction in all three families, including the two
that survived the baseline small-G test — and by a wider margin than the
first-pass (biased) numbers suggested. **The formal "moral-specific
interaction" claim does not survive small-cluster-robust inference once
intensity is controlled for, in any family.**

**Underpowered, not null.** A minimum-detectable-effect calculation
(`docs/RQ1_STATISTICAL_METHODS_v1.1.md` §11.2) resolves which of these two
this actually is: every severity-adjusted observed effect sits well under
what this design could reliably detect at G=21 — mistral's (−0.062) is a
fifth of its own MDE (0.312); even llama's much larger estimate (1.646) is
only about half its MDE (3.117). **The honest statement is "RQ1a is
uninterpretable post-severity-control at this cluster count for all three
families," not "the moral-specific effect disappeared."** How much more data
would fix this differs sharply by family: llama would need roughly 3x the
current 21 sets (to 70) to have a shot at confirming its point estimate;
gemma and mistral would need a ~20x larger release (400+ sets), because
their point estimates are small enough relative to their SEs that the
arithmetic doesn't converge on anything feasible — itself suggestive that
gemma's and mistral's severity-adjusted effects are mostly noise, while
llama's might be a real, just under-sampled, effect. Full derivation:
`docs/RQ1_STATISTICAL_METHODS_v1.1.md` §9.

**Why this confound may not be fixable by more data alone.** Reviewer-rated
severity correlates with sign at **r=.885 within moral items** and only
**r=.473 within nonmoral items** (`16_valence_split_severity_covariate.py`)
— severity is close to a proxy for sign specifically within the moral
category. `docs/SEVERITY_MORALIZATION_BACKGROUND.md` connects this to why:
this project's own taxonomy defines "moral" as harm/welfare-affecting
(`constants.py`'s `GENERATION_SYSTEM_PROMPT` explicitly excludes
purity/loyalty/authority content), which is the same criterion Turiel's
moral/conventional distinction and Gray & Schein's Theory of Dyadic
Morality use to define moral cognition itself — on those accounts, severity
isn't sitting on top of an independent moral dimension, it's close to
*constitutive* of it, at least for this harm-based slice of morality. Rozin's
moralization research adds the mechanism: rising perceived consequences are
what pull a nonmoral matter across the moral/conventional line in the first
place, which predicts that hand-writing "severity-matched nonmoral" content
will fight the same moral-bleed problem `data/curation/FLAGGED_VARIABLES_README.md`
already documents (20-26% of nonmoral items in high-real-stakes domains get
reviewer-judged moral anyway).

**Re-running the severity-adjusted direct split (rather than the pooled
interaction) within each valence type gives a more textured, partly
unanticipated picture** (`16_valence_split_severity_covariate.py`,
`family_id`-clustered, G=42 — no OLS-vs-GLS divergence here, checked and
confirmed clean, unlike the set_id-clustered pooled models above):

| family | moral-only, +severity | nonmoral-only, +severity |
|---|---|---|
| gemma | fails (p=.543; severity ate the signal, as expected given r=.885) | not significant, but sign flips negative (p=.22) |
| llama | fails at α=.05 but closer (p=.134); point estimate grows to 2.22 | not significant (p=.57) |
| mistral | stays null (p=.72, was already null) | **flips to strongly significant negative** (p_wcb=.000, 0/1999 draws exceeded it) |

Mistral's nonmoral result is a genuine, unanticipated finding, not noise:
once severity is held constant, mistral rates *bad* nonmoral outcomes as
*less* intentional than same-severity good ones — severity was suppressing
this relationship in the raw (unadjusted) data. Worth investigating on its
own terms in a future pass, independent of the RQ1a moral-specificity
question.

**Does severity alone predict the sign asymmetry as well as the categorical
moral/nonmoral label?** (`17_severity_vs_label.py`, three same-DF models —
label-alone, severity-alone, combined — compared via AIC and set-FE WCB.)
**AIC decisively favors the categorical label over continuous severity as a
predictor of intentionality overall, in all three families** (gemma: label
AIC 16776 vs. severity AIC 17423; llama: 24664 vs. 24769; mistral: 3232 vs.
5212 — an overwhelming margin for mistral specifically). That's evidence
*against* the strong "severity does all the work" reading: the categorical
label carries predictive information a raw severity score doesn't fully
capture. **Caveat this needs before leaning on it**: AIC compares overall
model fit (main effect + interaction together), not specifically the
sign-dependent asymmetry term — the label's advantage could be a general
moral-vs-nonmoral level difference in ratings unrelated to the Knobe
asymmetry per se, not evidence the label specifically drives the
asymmetry. Consistent with that caveat: in the combined model, **neither
the label's nor severity's own interaction with sign survives in any
family** — both wash out together (gemma: p=.71/.97; llama: p=.54/.20;
mistral: p=.45/.52), which the moralization-literature reading predicts
directly (if severity and moral status are close to the same underlying
signal for this harm-based taxonomy, a model can't cleanly credit either
one once both are in the same equation — that's what near-collinearity
looks like, not a null result for both). This is exactly the ambiguity
`docs/SEVERITY_PILOT_PLAN.md`'s escalated-severity pilot is designed to
resolve empirically, by trying to break the collinearity at the stimulus
level rather than the statistical level.

**Reconciling the two results:** a split-sample test (fit the sign effect
twice, once per subset) and a pooled-interaction test (fit one model with an
interaction term) are related but not identical questions, especially at
different cluster granularities (family-clustered, G=42, for the split; set-
clustered, G=21, for the interaction) and the split test hasn't itself been
severity-adjusted yet. Read this as: **gemma and llama show a real,
moral-specific sign effect (nonmoral badness alone does nothing), but the
formal claim that this asymmetry is statistically *larger* for moral than
nonmoral items — as opposed to nonmoral simply being null and moral being
present — isn't yet established at a defensible standard, and what evidence
there was is largely explained by the severity confound.** That's a more
qualified but more honest version of the original headline.

---

## 2. Blameworthiness, or mere valence?

The Hindriks-asymmetry contrast (RQ1b) regresses intentionality on an item's
*graded* blame mean (bad items) or praise mean (good items), crossed with a
bad/good indicator.

| family | moral: LMM estimate | WCB p | nonmoral: LMM estimate | WCB p |
|---|---|---|---|---|
| gemma | +0.222 | **.698 (fails)** | +0.443 | **.337 (fails)** |
| llama | +2.683 | **<.0001 (survives)** | +1.947 | **.0005 (survives)** |
| mistral | +1.301 | **<.0001 (survives)** | −0.164 | **.255 (unresolved, see below)** |

**Gemma shows no reliable Hindriks effect at all, in either domain, once
properly tested — a materially different conclusion than the first pass's
"blameworthiness matters in all three families."** Llama's effect is the
most robust of the three: it survives in both moral and nonmoral items,
supporting a graded, blame-driven (not merely valence-driven) mechanism that
isn't moral-specific. Mistral's moral-item effect is real and robust;
its nonmoral effect — reported in the first pass as a clean "reversal" and
treated as key evidence mistral is qualitatively different — **does not
survive a properly-specified small-cluster test and should be treated as
unresolved, not confirmed in either direction** (a family-random-slope check
gives it a significant negative estimate while the more defensible
family-fixed-effects wild bootstrap does not; see
`docs/RQ1_STATISTICAL_METHODS_v1.1.md` §10.2). Don't cite "mistral reverses
the Hindriks asymmetry for nonmoral items" as an established finding.

**A methodological note worth keeping, not just a caveat.** Diagnosing why
the initial wild-cluster-bootstrap pass gave nonsensical, sign-flipped
results for RQ1b surfaced a real bug: the pipeline's own reported confidence
intervals for RQ1b were computed with a biased refit procedure (plain pooled
OLS, when the predictor is strongly correlated with family identity — a
textbook random-effects endogeneity problem). This has now been fixed in
`src/knobe/analysis/models.py` (family fixed effects added to the RQ1b
bootstrap specifically), confirmed against the real data (all 6 RQ1b CIs now
bracket their point estimates, versus 3 of 6 failing to before), and covered
by two new regression tests. The original LMM point estimates in the table
above were never wrong — only the bootstrap CI around them was — but this is
a good example of how a "just add a robustness check" instinct can uncover an
actual defect rather than just reassurance.

**Caveat — errors-in-variables (unchanged from the first pass).** An item's
blame/praise mean is a finite-sample estimate (blame and intentionality are
independent completions; there is no response-level pairing, DR §12), which
attenuates every slope toward zero. Where an effect survives WCB, its
direction and cross-domain generality are trustworthy; its magnitude is a
conservative floor.

---

## 3. Does typicality exacerbate the bias, as in humans?

Descriptive bad-good intentionality gap, split by typicality condition:

| family | gap, common/typical | gap, uncommon/atypical | typ×sign WCB p |
|---|---|---|---|
| gemma | 0.53 | 0.11 | **<.001 (survives)** |
| llama | 0.43 | 0.25 | **.403 (fails)** |
| mistral | 0.03 | −0.17 | **<.001 (survives)** |

**Gemma and mistral robustly show the asymmetry running backwards from the
human exacerbation pattern** — the bad>good intentionality gap is *larger*
for ordinary/typical actions and *shrinks or reverses* for atypical ones, the
opposite of what "atypicality exacerbates the bias" would predict. This
survives both the wild cluster bootstrap and an independent family-random-slope
model (which gives nearly identical p-values via completely different
machinery — strong convergent evidence it's real). **Llama's version of this
effect does not survive** — a conclusion now reached three independent ways:
the ordinal-sensitivity check flips its sign, the wild cluster bootstrap
gives p=.40, and the family-random-slope model gives p=.39. Llama's
typicality×sign result should be treated as genuinely absent, not merely
uncertain.

**Revised conclusion: in the two families where this effect is real (gemma,
mistral), typicality does not exacerbate the wag-the-dog bias — it runs the
opposite direction, dampening rather than amplifying the evaluation-driven
asymmetry for atypical actions.** In llama there's no reliable typicality×sign
effect of either kind. The claim that this was "the single most robust effect
in the entire release" (first-pass framing) should be narrowed to "robust in
2 of 3 families" — still the strongest surviving effect after RQ1d, but not
universal.

---

## 4. Does affective response carry the same exacerbating role?

**The evocativeness manipulation still does not move self-reported affect**
(unchanged from the first pass — this analysis wasn't re-run through WCB
since it's a simple mean-difference, not a clustered regression, but the
effect sizes were already near-zero and directionally backwards):

| family | affect, high-evocative | affect, low-evocative | gap (high−low) |
|---|---|---|---|
| gemma | 5.34 | 5.49 | −0.15 |
| llama | 2.91 | 3.12 | −0.21 |
| mistral | 4.94 | 5.05 | −0.11 |

**The evocativeness×sign interaction itself is now much weaker evidence than
first reported.** Wild-cluster-bootstrapping the same three coefficients that
looked significant under the primary model:

| family | evoc×sign LMM p | evoc×sign WCB p |
|---|---|---|
| gemma | 5×10⁻³² | **.030 (barely survives)** |
| llama | .0044 | **.374 (fails)** |
| mistral | 3×10⁻¹⁵ | **.170 (fails)** |

Only gemma clears a properly-sized test, and only marginally. Combined with
the construct-validity problem above (the manipulation doesn't produce a
self-reported affect gap in any family), there is now very little support
for "evocative presentation drives intentionality ascription on negative
items" as a real mechanism in this data — not just an unmeasured one.

**The within-scenario affect-decoupling finding is unchanged, but flagged as
not yet re-tested at the same rigor.** Using each model's own self-reported
affect on the four variants within a family (not the assigned label),
demeaned within `family_id × sign`:

| family, sign | affect→intentionality slope, pretrained | shift under instruction-tuning | p (Wald, not yet WCB'd) |
|---|---|---|---|
| gemma, bad | +0.50 | −0.77 | .0004 |
| llama, bad | +0.94 | −1.02 | .036 |
| mistral, bad | +0.36 | −0.34 | .0002 |

Given how many of this document's Wald-significant findings did not survive
small-cluster-robust re-testing, **this result should now be read as a lead,
not a finding** — it hasn't yet been put through the same wild-cluster-
bootstrap or random-slope check as everything else here, and given the
pattern established above, there's a real chance its p-values are similarly
overconfident. The qualitative story (pretrained models show a within-family
affect-intentionality link; instruction-tuned models don't) may still hold,
but shouldn't be asserted with the same confidence as the RQ1d or gemma/mistral
RQ1c results until it clears the same bar.

**Caveats (unchanged):** small within-family N (4 variants × ~21 families per
sign), and affect tracks sign itself in every family (bad scenarios
universally rated more emotionally striking — gemma 5.89 vs 5.28, llama 3.52
vs 2.80, mistral 5.24 vs 4.76), so any affect×sign claim needs the
within-sign framing used here, not a naive pooled affect×sign term.

---

## Overall shape of the answer (revised)

After small-cluster-robust re-testing, the picture is more conservative and
more family-specific than the first pass suggested, but the taxonomy is
still doing real work — none of these four questions would be askable
without it, and what survives is genuinely informative:

- **Moral-specificity (§1):** real and robust in gemma and llama as a direct
  split-sample effect (nonmoral badness alone does nothing; moral badness
  does); the stronger, formal "moral bigger than nonmoral" interaction claim
  does not survive severity adjustment in any family.
- **Blameworthiness (§2):** real and robust in llama (both moral and
  nonmoral) and in mistral (moral only); **not established in gemma at all**;
  mistral's nonmoral "reversal" is unresolved, not confirmed.
- **Typicality (§3):** real, robust, and running opposite to the human
  exacerbation pattern in gemma and mistral; absent in llama.
- **Affect (§4):** the evocativeness-manipulation route to this question is
  now weakly supported at best (gemma only, marginally) and independently
  has a construct-validity problem; the within-family self-report-affect
  decoupling result is a promising lead that hasn't yet been tested to the
  same standard as the rest of this document.

**Mistral is not a consistent "odd one out"** the way the first pass framed
it — it's null on the RQ1a interaction and the sign×tuning base contrast
(though the sign×tuning null itself has one unresolved ordinal-model
disagreement), robust on RQ1b-moral, and unresolved on RQ1b-nonmoral. That's
a genuinely mixed profile, not a clean "mistral never acquired the bias"
story. **Gemma is the family whose profile shifted the most under
re-analysis**: it lost its entire RQ1b (blameworthiness) result and most of
its RQ1a support, while keeping its RQ1c typicality result as the strongest
surviving finding for that family. **Llama is the most consistent across the
four questions except typicality**, where it uniquely fails all three
independent checks.

None of the four "carries over from humans" cleanly, and the specific way
each one fails or partially holds differs by family — which is itself the
finding: a plain "LLMs show the Knobe bias" verdict would have hidden all of
this heterogeneity, both the substantive kind (moral-specificity, typicality
direction) and the purely statistical kind (which effects survive properly-
sized inference) that this taxonomy and this re-analysis made visible.

## What changed from the first pass, in one table

| claim | first pass | revised |
|---|---|---|
| RQ1a moral-specific interaction | "significant in all 3 families" | fails severity-adjusted WCB in all 3 |
| RQ1a direct split (moral vs nonmoral alone) | not separately WCB-tested | survives for gemma, llama |
| RQ1b gemma (both) | "significant" | fails WCB, both domains |
| RQ1b llama (both) | "significant" | survives WCB, both domains |
| RQ1b mistral moral | "significant" | survives WCB |
| RQ1b mistral nonmoral ("reversal") | reported as a clean finding | unresolved, not confirmed |
| RQ1c typicality×sign, gemma/mistral | "most robust effect in the release" | confirmed, narrowed to 2/3 families |
| RQ1c typicality×sign, llama | flagged uncertain (ordinal sign-flip) | confirmed absent (3 independent checks agree) |
| RQ1c evocativeness×sign | "significant in all 3, small" | survives only in gemma, marginally |
| RQ1d (offset, typicality-within-NEU) | robust | unchanged — the one set of findings small-cluster-robust testing didn't touch |
| Affect-decoupling (§4) | reported as a finding | downgraded to a lead pending the same rigor |

## Open follow-ups

- Resolve the mistral RQ1b-nonmoral disagreement with a joint/latent-variable
  model rather than choosing between two second-best estimators.
- Wild-cluster-bootstrap and random-slope-test the affect-decoupling result
  (§4) before citing it with the same confidence as the rest of this
  document.
- ~~Severity-adjust the direct moral/nonmoral split test~~ — done (§1
  above): moral-only loses significance for gemma, doesn't reach it for
  llama (p=.134, but a growing point estimate); nonmoral-only produces an
  unanticipated significant reversal for mistral, worth its own follow-up.
- **Active next step**: `docs/SEVERITY_PILOT_PLAN.md` — draft and curate
  (not yet elicit) severity-escalated prudential-subdomain nonmoral pilot
  items, to test empirically whether severity and moral status are
  separable in this taxonomy at all, per
  `docs/SEVERITY_MORALIZATION_BACKGROUND.md`'s prediction.
- Resolve the RQ1_base mistral sign×tuning ordinal-vs-LMM/WCB disagreement
  (both LMM and WCB agree on a clean null; only the ordinal check, which
  can't model random effects, disagrees).
- Domain-random-slope sensitivity fits for the cross-domain generalization
  claims underlying §1 and §3, given how much family-level heterogeneity the
  random-slope check surfaced.
- ~~Minimum-detectable-effect for the severity-adjusted RQ1a model~~ — done
  (§1 above, `docs/RQ1_STATISTICAL_METHODS_v1.1.md` §11.2): all three
  families are underpowered, not confirmed-null. Doing this surfaced a
  second case of the pooled-OLS bias (fixed via set fixed effects, same fix
  family as RQ1b's) — ~~worth a systematic check of every other WCB script~~
  now checked: every other `wild_cluster_bootstrap` call in
  `analysis/rq1_v1_1_robustness/` uses only balanced ±0.5 factors or a bare
  intercept; `pred_c` (RQ1b) and `severity_c` (RQ1a) were the only two
  continuous, cluster-correlated covariates, and both are fixed now.
- Three numbers in §1 (the severity-by-valence table) and elsewhere in this
  session are still not backed by a committed script — recorded as "Known
  gaps" in `results/ANALYSIS_LOG.md` rather than silently left untraced.

— Analysis run 2026-08-10 against `results/v1.1/results_all.jsonl` (378,000
rows), `data/release/v1.1/vignettes.csv`, and `data/curation/curated_v1.1.csv`
(severity). Full statistical methodology, diagnostics, and the code fix are
in `docs/RQ1_STATISTICAL_METHODS_v1.1.md` §8–§13. Preregistered contrast
numbers trace to `results/v1.1/paper/contrast_table.csv` (regenerated after
the RQ1b bootstrap fix), `set_sensitivity.csv`, `ordinal_sensitivity.csv`.
Wild-cluster-bootstrap, severity, RE/OLS/FE, and random-slope numbers are
not yet `knobe analyze` pipeline artifacts, but are fully reproducible from
the committed scripts in `analysis/rq1_v1_1_robustness/` (see that
directory's README.md and `docs/RQ1_STATISTICAL_METHODS_v1.1.md` §8–§13 for
which script produces which table).
