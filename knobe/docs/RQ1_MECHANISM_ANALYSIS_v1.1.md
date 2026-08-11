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
fails once properly tested (wild cluster bootstrap; the asymptotic set-cluster
Wald fit that first looked like it rescued all three families, p=.0014/.0000/.0000,
is unreliable at only 21 clusters). Baseline WCB survives for llama/mistral
(p=.0045/.001) but not gemma (p=.640); with severity added as a covariate,
none survive (p=.655/.222/.564) — full numbers and the set-FE bootstrap-bias
correction behind them in `docs/RQ1_STATISTICAL_METHODS_v1.1.md` §9.
**The full trail this section summarizes — the label-vs-severity AIC
comparison, the direct dose-response test and the equivalence-CI correction
to how its null was first read, and why the item distribution itself rules
out a higher-order fix — is preserved in full in that doc's §9.1–9.3, not
just this shorter version.**

**The direct manipulation check this warranted from the start, and didn't
get at norming time: are moral and nonmoral items actually matched on
severity within the same storyline?** The curation severity-match check
only ever compares *within* a family across the low/high-evocativeness
swap — it was never checked *across* valence categories. Pulling the
within-storyline (same `set_id`) pairs directly:

| pair | mean severity gap | sets matched (within 1.0 point) |
|---|---|---|
| MB vs. NMB (**bad**) | **5.42** | **0 of 21** |
| MG vs. NMG (**good**) | 1.00 | 11 of 20 |

**Bad pairs are catastrophically unmatched — MB exceeds NMB by 3.5 to 7.0
points in every single one of 21 storylines, with zero exceptions. Good
pairs are reasonably close.** This is the actual finding, and it's a
stimulus-design fact, not a statistical artifact: **RQ1a's item set has a
severity confound baked into the moral-bad/nonmoral-bad comparison
specifically — the exact pairing the wag-the-dog asymmetry lives in — and
no regression term fixes a manipulation that was never matched in the first
place.** MB was authored around "genuine harm" with no severity target
relative to NMB; NMB was authored to be dimensionally independent and
low-stakes. Nothing enforced parity between them.

This also explains why every statistical attempt to *model* the confound
away struggled the same way: severity correlates with sign at **r=.885
within moral items** (barely separable from the sign label itself) vs. only
**r=.473 within nonmoral items**, and at the item level, family-mean
severity occupies almost completely disjoint ranges by valence — MB
5.7–9.0, everything else 0.0–4.5, with **1 family out of 105** in the
4–5.5 gap between them. A direct severity×sign dose-response test at full
power (`19_severity_dose_response.py`, same clustering/subset as
`rq1c_typicality_x_sign`) found no significant effect in any family
(p=.544/.698/.364) — but its own confidence intervals are wide enough to
contain an effect as large as typicality's clean, significant one in every
family, so that null is **uninformative, not disconfirming**: with severity
occupying two disjoint clusters rather than a real continuum, no
functional form (linear or otherwise) can be fit to it with precision. The
same logic applies to the AIC comparison in `17_severity_vs_label.py`
(label beats severity on overall fit) — plausibly reflects the categorical
encoding being a cleaner version of nearly the same two-cluster signal, not
independent evidence morality "beats" severity as a driver.

**Bottom line: this is a manipulation failure to fix by re-norming and
re-matching the stimuli (`docs/SEVERITY_PILOT_PLAN.md`, scoped specifically
to nonmoral-*bad* content — the good pairs don't need it), not something
more modeling on the existing v1.1 data can resolve.** Until nonmoral-bad
severity is deliberately raised into the 5–7 range and re-checked against
moral_relevance, RQ1a's moral-vs-severity question should be reported as a
design limitation, not a statistically-adjudicated finding in either
direction. (Full matched-pair table: `docs/RQ1_STATISTICAL_METHODS_v1.1.md`
§9.4.)

**What still stands on its own:** the direct split-sample test (fit the
sign effect separately within moral-only and nonmoral-only items, not as a
pooled interaction) survives WCB for gemma and llama (nonmoral badness alone
produces no reliable shift; moral badness does) — but given the severity
finding above, this should be read as "moral-*and*-severe badness produces
the effect, nonmoral-and-mild badness doesn't," not yet as evidence morality
per se (independent of severity) is the active ingredient. That
decomposition is exactly what the pilot is for.

**One separate, standalone finding worth keeping despite the consolidation
above**: unlike the moral-vs-nonmoral comparison, severity *within* the
nonmoral category (NMB 0.3–3.0 vs. NMG 0.0–1.8) actually overlaps
substantially rather than forming disjoint clusters, so it isn't subject to
the same identification problem. Severity-adjusting the nonmoral-only split
test there (`16_valence_split_severity_covariate.py`) found mistral flips to
a strongly significant *negative* effect (p_wcb=.000, 0/1999 draws
exceeded it) — once severity is held constant, mistral rates bad nonmoral
outcomes as *less* intentional than same-severity good ones, a relationship
severity was suppressing in the raw data. This is real and independent of
everything above; worth its own follow-up.

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

**Not a severity story in disguise.** Given RQ1a's severity confound
(§1), the natural next question is whether typicality itself correlates
with severity — uncommon actions do read as slightly more severe than
common ones, consistently across every valence category (`curated_v1.1.csv`:
MB 6.6→7.5, MG 1.8→2.0, NMB 1.6→1.7, NMG 0.7→1.1), but the correlation is
weak (r=.07–.15, vs. RQ1a's r=.885 within moral items) and typicality is a
factorially-crossed, balanced design factor here, not a family-constant
category like sign/valence-type. Controlling for severity leaves
`typ_c:sign_c` **unchanged to 6 decimal places** in all three families
(`18_rq1c_typicality_severity_covariate.py`) — the opposite result from
RQ1a, where severity ate nearly the entire signal. This finding doesn't
ride on severity at all.

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
- ~~Is RQ1a's moral/nonmoral comparison actually severity-matched?~~ — done
  (§1 above): checked directly, within-storyline, bad pairs only (MB vs.
  NMB) — catastrophically unmatched (mean gap 5.42, 0/21 sets within 1.0
  point); good pairs (MG vs. NMG) are reasonably close (mean gap 1.00,
  11/20 matched). This is the decisive finding: a stimulus-design
  manipulation failure specific to the bad-valence pairs, not a statistical
  power problem — motivates the pilot below directly, scoped to
  nonmoral-*bad* content specifically (nonmoral-good doesn't need it).
- **Active next step**: `docs/SEVERITY_PILOT_PLAN.md` — draft and curate
  (not yet elicit) severity-escalated prudential-subdomain nonmoral-**bad**
  pilot items specifically, to find out whether nonmoral-bad severity can
  be raised into MB's 5-7 range while staying reviewer-classified nonmoral.
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
