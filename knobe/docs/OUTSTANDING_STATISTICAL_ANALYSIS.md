# Outstanding Statistical Analysis — Status Against the Original Review (2026-08-10, updated 2026-08-12)

**Status:** tracks the 12-item technical-audience review (Tier 1/2/3) given
earlier in this project against everything actually done since. Read this
alongside `docs/RQ1_STATISTICAL_METHODS_v1.1.md` (methodology + detailed
per-contrast tables) and `docs/RQ1_MECHANISM_ANALYSIS_v1.1.md` (research
interpretation) — this document's job is just the honest checklist: what
got fixed, what got partially addressed, what's still open, and what new
items the work itself surfaced.

**2026-08-12 closeout session:** items 2, 3, 4, 6, 8, 10, 11, and 12 were
all revisited (`analysis/rq1_v1_1_robustness/23-30`, branch
`outstanding-stats-closeout`, full trail in `results/ANALYSIS_LOG.md`). Two
of these (3 and 12-adjacent) surfaced results that change the picture rather
than just closing a checkbox — flagged inline below, not buried.

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

**2. RQ1b measurement-error correction — SIMEX DONE (2026-08-12); does not
resolve the disagreement; the joint/latent-variable half of the ask is
still open.** `28_rq1b_simex.py`: per-item measurement-error variance,
estimated directly from repeated `sample_idx` draws, is negligible
everywhere (1.5e-8 to 7.4e-8) — checked directly that `ev_rating` (the
logit-fallback EV score) is near-deterministic given the prompt across its
50 repeated samples per item, for every checkpoint. Consequence: SIMEX
correction via this channel does essentially nothing (attenuation -0.001%
to +0.01% in all 6 rq1b cells) — this is a real, checked finding, not a
skipped step. For the mistral-nonmoral disagreement specifically (family-FE
WCB p=.255 vs. family-random-slope p=.0021), a family-cluster bootstrap of
the whole SIMEX procedure gives simex_beta=-0.176 (unchanged), 95% CI
[-0.568, .054] (crosses 0), p≈.14 — **does not resolve it toward
significance; if anything leans toward the WCB's null reading.** Lesson:
whatever drives that disagreement isn't sampling-noise attenuation in
`pred_c` — the joint/structural latent-variable model (blame-mean and
intentionality as two indicators of a shared item effect) remains
unimplemented and is now the more promising remaining path if this
disagreement needs resolving; a from-scratch feasibility check (no `semopy`
installed, but pip-installable with no R dependency; a lower-friction
bivariate-mixed-model-with-shared-item-random-effect approximation is
buildable in `statsmodels` alone) is logged in `results/ANALYSIS_LOG.md`
2026-08-12 but not attempted.

**3. LMM-vs-ordinal sign disagreements — the literal fix is now DONE
(2026-08-12), and it complicates the story rather than closing it.** The
"convergent evidence means the ordinal model's disagreement is just its own
limitation" read below was the working theory as of 2026-08-10. A proper
mixed cumulative-link model (bambi/PyMC, `family="cumulative"`,
`(1|family_id)` random intercept, NUTS — pymc/bambi newly added as a
`bayes` extra in `pyproject.toml`, see that commit for a real dependency
snag and its fix) was fit for both flagged cells in
`29_rq1_ordinal_mixed_bambi.py`: mistral rq1_base `sign_c:tuning_c` (n=16800,
303s) and llama rq1c `typ_c:sign_c` (n=8400, 918s), both converged cleanly
(r_hat=1.0). **Both terms come back significant** (mistral mean=1.387, 94%
HDI [1.236, 1.539]; llama mean=1.302, HDI [1.037, 1.561]) — disagreeing with
the convergent-null evidence (WCB p=.918/.403, family-random-slope LMM
p≈.92/.39-.40) in *both* cells, not corroborating it.

**This isn't a clean resolution either way — an important caveat limits
what it means.** The bambi model has a family_id random *intercept* only,
not the random *slope* that the "family-random-slope LMM" pillar of the
convergent evidence actually relies on — and this document's own item 7
already established that omitting exactly that random slope causes 3-12x SE
inflation for these very terms. A random-slope refit
(`(1 + term | family_id)`) was attempted to close that gap properly, but a
2000-row calibration subsample alone ran past 5 minutes (vs. 44.5s for the
intercept-only version at the same N) — a clear signal the full fits would
run well past a 30-60 minute budget, so it was stopped rather than ground
through. **Open question, now sharper than before 2026-08-12, not
resolved:** does the ordinal-vs-LMM disagreement survive once random slopes
are properly added to the ordinal side, or is the disagreement just the
ordinal model repeating the same missing-random-slope mistake the LMM side
already had to fix? Don't cite the mistral/llama "null, corroborated by
convergent evidence" framing from the original review without this caveat
attached.

**4. Mistral NEU-typicality quasi-separation — DONE (2026-08-12), cleanly
resolved.** `30_mistral_neu_typicality_bayes.py`: a Bayesian-regularized
ordinal fit (bambi/PyMC, same setup as item 3, weakly-informative default
priors — no Firth-for-ordinal package exists in Python, checked) on the
small mistral NEU/finetuned subset (n=2100, G=21). Fast (28s), converged
cleanly (r_hat=1.0). Diagnosed the original degeneracy directly along the
way: this subset's rounded ratings collapse to only 2 categories, so the
"ordinal" model here is really binary logistic, and `typ_c` apparently
near-perfectly separates the two categories — the classic MLE-to-infinity
failure mode. The regularized posterior is finite and well-behaved: mean=6.0,
94% HDI [4.52, 7.67], excludes 0 with real (not degenerate) uncertainty, and
**corroborates rather than contradicts** the existing LMM+WCB result for
this cell (p_wcb=.000). Unlike item 3, this one is a clean win: no open
thread left.

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

**6. Bootstrap quality — the BCa comparison is now DONE (2026-08-12); the
pipeline itself is still deliberately unchanged.** `27_bootstrap_ci_bca_comparison.py`
compares the pipeline's own `_bootstrap_ci` (reused as-is, not
reimplemented, n_boot=200, percentile) against a jackknife-BCa extension
(n_boot=499 — cost-checked down from an initial n_boot=1999 attempt that
was killed after 6.5 min with no checkpointing) across all 21 primary
cells. **Result: BCa changes the zero-exclusion conclusion in exactly 1 of
21 cells** — gemma's evocativeness×sign, which is also the single most
marginal cell in the whole release already (WCB p=.030). All other 20
cells agree regardless of method. Deliberately not promoted to the pipeline
default: `contrast_table.csv`'s `ci_low`/`ci_high` are already cited in
prior docs, and swapping the method would retroactively change what those
numbers mean. WCB p-values remain the estimator of record; this just
confirms the percentile-vs-BCa choice barely matters in practice.

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

**8. Likelihood-ratio tests alongside Wald — DONE (2026-08-12).**
`24_lrt_vs_wald.py`: ML-fit LRT (df=1) computed alongside the existing
Wald/WCB p-values for every primary contrast already WCB-tested in scripts
01/02/03/07. LRT never disagrees with WCB in a way that would overturn a
conclusion — but more usefully, it never *rescues* anything WCB already
rejected either: it reproduces Wald's exact overconfidence pattern in every
cell WCB flagged (rq1a-gemma, rq1b-gemma both domains, rq1b-mistral-nonmoral,
rq1c-llama typicality and evocativeness, rq1c-mistral-evocativeness). Useful
negative result: confirms the small-cluster problem isn't a WCB-specific
artifact — a different asymptotic test shares Wald's overconfidence in
exactly the same cells, reinforcing that WCB's correction is doing real
work rather than being an idiosyncratic property of that one method.

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

**10. Effect sizes / variance decomposition (ICC) — DONE (2026-08-12).**
`23_icc_variance_decomposition.py`: REML random-intercept-only fits at each
contrast's existing WCB grouping column, per family, reporting ICC and the
implied design effect. ICC ranges widely (0.02-0.88 across contrasts) and
design effects are large almost everywhere (6-160x) — within-family
replicate sampling has strongly diminishing returns relative to adding new
families. This is now the concrete input for right-sizing the next
data-collection increment (the ~145 planned-but-ungenerated families) —
more families, not more samples per family, is what buys power in most of
this design.

## Tier 3

**11. Validate the uniform logit-fallback EV-scoring decision — DONE
(2026-08-12).** `26_ev_scoring_validation.py`: `ev_rating` (logit-fallback)
vs. `parsed_rating` agreement is only moderate even on the best-parsed
checkpoints (corr .44-.50 for the three instruct models) and near-zero for
all three pretrained checkpoints (.05-.07) — the two scores are genuinely
not interchangeable response-by-response. But re-testing RQ1c's
`typ_c:sign_c` (finetuned-only, the release's strongest result) on
parse_ok-only rows with `parsed_rating` substituted gives the **identical
significance pattern** in all three families (effect sizes roughly double
under parsed-only, but which families are significant doesn't change).
Reassuring for the headline result; `rq1_base`'s tuning contrast couldn't be
tested this way since it structurally requires the low-parse-rate
pretrained side.

**12. Differential non-response by parse rate — DONE (2026-08-12).**
`25_parse_rate_condition_check.py`: logistic regression of `parse_ok` on
typicality/sign/valence-type (+domain control), per checkpoint, on
intentionality rows. **Typicality shows no effect on parse rate anywhere**
(all p>.13) — directly protects RQ1c/RQ1d, the release's strongest surviving
results, since they rest on typicality. Valence-type (moral vs. nonmoral)
*does* predict parse rate in 3 of 6 checkpoints (mistral-pretrained
p=2.7e-7, gemma-instruct p=4.4e-4, llama-instruct p=3.9e-3) — flagged as a
possible differential-nonresponse confound for RQ1a/RQ1b specifically, not
chased further this session.

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
  both at once). **Update 2026-08-12: SIMEX (the other half of item 2) does
  not settle it** — see item 2 above. The joint/latent-variable model is
  now the only unattempted lever left for this specific disagreement.
- **The escalated-severity pilot** (`docs/SEVERITY_PILOT_PLAN.md`) is a
  stimulus-design-level attempt at what Tier 1 item 5 and Tier 2 item 9
  can't reach statistically — if severity and moral status turn out to be
  genuinely inseparable in this taxonomy (the moralization-literature
  prediction), that's a finding about the *design*, not something more
  compute or a better model can fix.
- **New, 2026-08-12: the item-3 ordinal-vs-LMM disagreement is now more
  open than before, not resolved.** A proper mixed cumulative-link model
  disagreed with the LMM/WCB convergent-null evidence in *both* flagged
  cells, reversing the "just the ordinal model's own limitation" read from
  2026-08-10 — but only a random-*intercept* version was fit; the
  random-*slope* version needed for a fair comparison against the
  family-random-slope LMM was cost-prohibitive at full data size (a 2000-row
  calibration subsample alone ran past 5 minutes). Whoever picks this up
  next should either budget real compute time for a full random-slope
  bambi/PyMC run (try a non-centered parameterization first — it's the
  standard fix for the slow/poorly-mixing geometry random-slope models tend
  to hit) or treat "ordinal vs. LMM as response-distribution choices
  disagree here" as a standalone limitation to report rather than resolve.
- **pymc/bambi are now available project-wide** (`pyproject.toml`'s `bayes`
  extra, `uv pip install -e ".[bayes]"`) for any future Bayesian mixed-model
  work — with a documented dependency snag (pymc's `arviz` dependency breaks
  on import against this project's matplotlib; fixed with a 2-line compat
  shim, `analysis/rq1_v1_1_robustness/_bayes_compat.py`, import it before
  `pymc`/`bambi`, not a matplotlib downgrade — that broke 26 existing tests).
- **New, 2026-08-12: valence-type (not typicality) predicts parse rate in
  3/6 checkpoints** (item 12) — typicality itself is clean, so RQ1c/RQ1d
  aren't threatened, but this is an unexamined possible differential-
  nonresponse confound specifically for RQ1a/RQ1b, which do turn on
  moral/nonmoral valence.

## Priority read, if picking up this list fresh

Highest leverage, in order: **(new, item 3)** the random-slope ordinal
refit for mistral's `sign_c:tuning_c` and llama's `typ_c:sign_c` — this is
now the sharpest open question on the list, since the 2026-08-12 fit
actively contradicts the convergent-null evidence rather than just leaving
it unconfirmed, and the only thing standing between "resolved" and "still
open" is compute budget for a properly-specified model; **(2/new-item)**
the RQ1b joint EIV/latent model — SIMEX (tried) ruled out one candidate
explanation for the mistral-nonmoral disagreement, this is the remaining
one; **(7)** promoting random slopes into the pipeline — the effect is
large and pervasive, and it's currently invisible to anyone who only runs
`knobe analyze` (also now directly relevant to the item-3 random-slope
question above); **(9)** stating the multiplicity exposure explicitly
wherever the mechanism doc is cited externally, since it can't be fixed
without new data. Items 6, 8, 10, 11, and 12 are now closed — see above for
what each one found (most were confirmatory/protective of existing results;
none overturned a conclusion).
