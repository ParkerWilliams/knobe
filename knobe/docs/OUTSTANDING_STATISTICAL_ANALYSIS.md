# Outstanding Statistical Analysis — Status Against the Original Review (2026-08-10)

**Status:** tracks the 12-item technical-audience review (Tier 1/2/3) given
earlier in this project against everything actually done since. Read this
alongside `docs/RQ1_STATISTICAL_METHODS_v1.1.md` (methodology + detailed
per-contrast tables) and `docs/RQ1_MECHANISM_ANALYSIS_v1.1.md` (research
interpretation) — this document's job is just the honest checklist: what
got fixed, what got partially addressed, what's still open, and what new
items the work itself surfaced.

## Tier 1

**1. Small-cluster-count inference — DONE.** Implemented a wild cluster
bootstrap (Cameron-Gelbach-Miller 2008, Rademacher weights, restricted
null-imposed residual DGP, B=1999) as the primary small-G-robust check,
used across every RQ1 contrast (`analysis/rq1_v1_1_robustness/01-09`,
`13-17`). This is what overturned RQ1a's headline and half of RQ1b's
family-specific claims. Randomization/permutation inference (the other
option suggested) wasn't implemented — WCB was judged sufficient and is the
more standard tool for this design; permutation inference remains a
reasonable independent cross-check if anyone wants a second opinion later,
but isn't currently a gap.

**2. RQ1b measurement-error correction — NOT DONE (a different, real bug
was found and fixed instead).** What got fixed: the bootstrap CI's *refit
engine* was biased (plain pooled OLS, when `pred_c` correlates 0.77–0.96
with family identity) — corrected via family fixed effects
(`_bootstrap_formula` in `models.py`, commit `8338f92`). **What's still
missing is the actual ask: a SIMEX correction or a joint/structural latent-
variable model treating blame-mean and intentionality as two indicators of
a shared item effect.** The EIV attenuation itself is still just
documented, not corrected for. This is arguably the single highest-value
remaining item — RQ1b's magnitudes are still a conservative floor with no
quantified correction, and the mistral-nonmoral disagreement between the
family-FE WCB (p=.255, not significant) and the family-random-slope model
(p=.0021, significant negative) is exactly the kind of ambiguity a proper
joint model would resolve instead of leaving as a coin flip between two
second-best estimators.

**3. LMM-vs-ordinal sign disagreements — PARTIALLY ADDRESSED, not resolved
as specified.** The two flagged disagreements (mistral's `sign_c:tuning_c`,
llama's `typ_c:sign_c`) now have *converging* independent evidence: the
family-random-slope LMM agrees with the family-clustered WCB on both cells
(mistral's null holds up, p=.92; llama's typ×sign is genuinely
non-significant, p≈.39-.40 by both methods) — which is real corroboration
that the ordinal model's disagreement is more likely its own limitation (no
random effects) than a sign of trouble in the LMM. But **no actual mixed
cumulative-link model was fit** (R's `ordinal::clmm` or a Bayesian ordinal
fit in `brms`/`rstanarm`, as specified) — the resolution here is
convergent-evidence-based, not a direct adjudication via the tool the
review recommended. If a technical reviewer wants the literal fix, it's
still open.

**4. Mistral NEU-typicality quasi-separation — NOT DONE.** Still documented
as a known-degenerate ordinal fit (estimate=13.3, `docs/RQ1_STATISTICAL_METHODS_v1.1.md`
§7.2); no penalized (Firth) or Bayesian-regularized ordinal refit was run.
The underlying LMM result for this cell is independently well-supported
(tight CI, and now also confirmed by WCB, `02_rq1d_wcb.py`: p_wcb=.000), so
this is lower-priority than it looked in isolation — but the literal ask is
still open.

**5. RQ1a severity confound needs a fitted model — DONE, and taken well
beyond the original ask.** Not just one severity-covariate refit: a
corrected (set-FE) severity-adjusted interaction fit (`04`, `13`, `14`), a
minimum-detectable-effect analysis showing all three families are
underpowered rather than confirmed-null post-adjustment (`15`), a
severity-adjusted version of the *direct* moral/nonmoral split test with a
genuine new finding (mistral's nonmoral reversal, `16`), a same-DF
label-vs-severity model comparison (`17`), a theory note connecting the
r=.885 severity/sign correlation to the moralization literature
(`docs/SEVERITY_MORALIZATION_BACKGROUND.md`), and a concrete stimulus-level
follow-up plan (`docs/SEVERITY_PILOT_PLAN.md`) rather than stopping at "does
it survive statistically." This went further than "fit one model" because
the first attempt at exactly that (item 5 as originally scoped) surfaced a
second instance of the same pooled-OLS bug found in item 2 — worth knowing
this Tier 1 item and Tier 1 item 2 turned out to share a root cause.

## Tier 2

**6. Bootstrap quality — PARTIALLY ADDRESSED, and the fix differs from what
was asked.** The WCB checks (item 1) use B=1999 (not the originally-flagged
`n_boot=200`) and a **wild bootstrap-t** rejection-rate p-value, not a
percentile interval — this sidesteps the percentile-vs-BCa skewness concern
entirely for every WCB-tested contrast, arguably more robust than bumping a
percentile bootstrap to BCa would have been. **What's unchanged: the
pipeline's own `_bootstrap_ci`** (used for the `ci_low`/`ci_high` columns in
`contrast_table.csv`) is still `n_boot=200`, still plain percentile, not
BCa — only its RQ1b-specific bias (wrong refit formula) was fixed, not its
resample count or interval method. If those CIs are ever going to be cited
as calibrated intervals (rather than the WCB p-values being the estimator
of record, which is the current guidance), this still needs doing.

**7. Family random slopes — the ANALYSIS is done; the PROMOTION isn't.**
`08_family_random_slopes.py` confirms 3–12x SE inflation vs.
random-intercept-only in every cell tested, and independently reproduces
the WCB p-values to within ~.02 — strong convergent evidence this
misspecification is real and pervasive. **This has not been made a
standard, always-reported pipeline sensitivity fit** (parallel to
`--domain-slope-sensitivity`, which already exists in `models.py` for
domain) — it's still a one-off script outside `knobe analyze`. That
promotion (a real `models.py`/`report.py` change, plus tests) is still
open, and is probably the highest-leverage *pipeline* change on this whole
list given how pervasive the effect is.

**8. Likelihood-ratio tests alongside Wald — NOT DONE.** No LRT
comparisons were run anywhere in this session. Still fully open.

**9. Multiplicity across the whole exploratory session — NOT ADDRESSED, and
the exposure grew.** Holm-within-(family,RQ) still only covers the nine
preregistered contrasts. Everything from the mechanism-doc exploration
(the valence-split test, the typicality/evocativeness gap tables, the
affect-decoupling regressions) *and* everything from today's severity work
(scripts 13–17, all discovered by looking at what the data showed first) is
outside that correction. The originally-recommended fix — preregister these
specific hypotheses and test them on a genuine v1.2 holdout — has not
happened and could not have happened yet (there is no v1.2 data). This is
now a longer list of uncorrected exploratory findings than when the review
was written, not a shorter one. Worth being explicit about with anyone
reading the mechanism doc: it is a garden-of-forking-paths document, stated
as such, not a confirmatory one.

**10. Effect sizes / variance decomposition (ICC) — NOT DONE as specified,
partially served by a different tool.** No ICC or variance-partition
coefficient was computed for any primary LMM. The minimum-detectable-effect
work (`09`, `15`) answers an adjacent but distinct question — "is a null
result underpowered or real" — for several contrasts, which is part of what
ICC/effect-size reporting is for, but doesn't give the general
"how much of the variance is family vs. residual" decomposition the review
asked for. Still open as literally specified.

## Tier 3

**11. Validate the uniform logit-fallback EV-scoring decision — NOT DONE.**
No agreement check between the softmax-EV score and the parsed rating was
run for high-parse-rate checkpoints (e.g. mistral-instruct, 97.7% parse
rate). Still fully open.

**12. Differential non-response by parse rate — NOT DONE.** No check of
whether parse failure correlates with experimental condition (e.g.
atypical/NEU scenarios producing more unparseable hedging) was run for any
checkpoint, including the very-low-parse-rate ones (llama-pretrained,
24.4%) that anchor the tuning contrasts. Still fully open.

## New items this session's work surfaced (not on the original list)

- **A general audit habit, not a one-off fix, is needed for the pooled-OLS-
  vs-continuous-covariate bug.** It was found and fixed independently three
  times (RQ1b's `pred_c`, RQ1a's `severity_c` in two different model
  specs) before a systematic audit of every `wild_cluster_bootstrap` call
  was actually run (README.md's audit note — done, nothing else found as of
  2026-08-10, but this should be standard practice for any future WCB
  script, not a retrospective check).
- **Resolve the mistral RQ1b-nonmoral disagreement** between the family-FE
  WCB and the family-random-slope model (§13 item 1 above and
  `docs/RQ1_STATISTICAL_METHODS_v1.1.md` §10.2) — this is the same
  underlying ask as Tier 1 item 2 (a proper joint/EIV model would settle
  both at once).
- **The escalated-severity pilot** (`docs/SEVERITY_PILOT_PLAN.md`) is a
  stimulus-design-level attempt at what Tier 1 item 5 and Tier 2 item 9
  can't reach statistically — if severity and moral status turn out to be
  genuinely inseparable in this taxonomy (the moralization-literature
  prediction), that's a finding about the *design*, not something more
  compute or a better model can fix.

## Priority read, if picking up this list fresh

Highest leverage, in order: **(2/new-item)** the RQ1b joint EIV/latent model
— it resolves an existing named disagreement, not just a hypothetical
concern; **(7)** promoting random slopes into the pipeline — the effect is
large and pervasive, and it's currently invisible to anyone who only runs
`knobe analyze`; **(9)** stating the multiplicity exposure explicitly
wherever the mechanism doc is cited externally, since it can't be fixed
without new data; **(11/12)** are cheap, mechanical checks worth doing
before anyone leans on the pretrained-checkpoint contrasts specifically.
