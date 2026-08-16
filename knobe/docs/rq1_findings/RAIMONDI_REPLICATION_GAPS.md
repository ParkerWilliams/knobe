# Where We Don't Replicate Raimondi et al., and Why It Matters (2026-08-15)

**Status:** synthesis of a same-day investigation
(`analysis/rq1_v1_1_robustness/31`–`35`, branch `rq1-base-sign-main-effect-wcb`,
full provenance in `results/ANALYSIS_LOG.md`) into how this project's RQ1_base
result compares to Raimondi, Dalbagno & Gabbrielli, *Analysing Moral Bias in
Finetuned LLMs through Mechanistic Interpretability* (arXiv:2510.12229), the
paper this project explicitly extends (`specs/00_PLAN.md` §1;
`specs/work_orders/WO8_analysis.md`: "RQ1 base: sign × tuning_status (the
Raimondi replication, now over decomposed items)"). Their reported numbers
below (Table 1, ΔKnobe = mean(negative) − mean(positive) intentionality
rating, 2×3 repeated-measures ANOVA, 80 moral-valence Ngo-derived scenarios,
283 completions/scenario) were pulled directly from the paper, not
reconstructed from this project's secondhand paraphrase of it.

## 1. The comparison, stage by stage

All rows below use this project's **moral-only** subset (matching the scope
of Raimondi's all-moral 80-scenario design) and, on the pretrained side, the
model's actual **parsed numeric rating**, not the pipeline's default
logit-fallback `ev_rating` score — see §2 for why that substitution is
load-bearing, not incidental.

| model | Raimondi pretrained (ΔKnobe) | Us, pretrained (β, WCB p) | Raimondi finetuned (ΔKnobe) | Us, finetuned (β, WCB p) |
|---|---|---|---|---|
| gemma | +0.51 | **+0.539, p=.001** — matches | +3.83 (sig. > pretrained, p<.001) | +0.368, p=.021 — same direction, smaller |
| llama | +0.24 | +0.016, p=.970 — inconclusive (n=871, 20.7% parse rate) | +1.60 (sig. > pretrained, p<.001) | **+0.658, p=.0005** — matches, largest effect in the study |
| mistral | +0.06 | +0.335, p=.120 — same direction, not significant | +1.67 (sig. > pretrained, p<.001) | **+0.062, p=.408 — null** |

Two of three families are broadly consistent with Raimondi at one or both
stages. **Two gaps are real enough to write up on their own:** llama's
pretrained status is unresolved rather than replicated, and **mistral does
not replicate the finetuned effect at all** — this is the one clean,
repeated non-replication in the set.

## 2. Gap 1 — llama pretrained is inconclusive, not confirmed either way

**What we found:** flat, null result (β=.016, p=.970) using parsed ratings,
but on only 871 rows (20.7% of the 4,200-row moral/pretrained/intentionality
sample actually produced a parseable numeric answer) — the lowest parse rate
of any cell in this comparison.

**Theory:** this is very likely a genuine measurement gap, not a genuine
behavioral finding either way. Llama-pretrained largely doesn't answer the
intentionality question in a parseable format at all; whatever the model's
underlying disposition is, this design doesn't have enough valid
observations to see it. This isn't a stimulus problem — it's an elicitation
problem (prompt format, lack of constrained decoding, or something about how
this checkpoint responds to the rendered prompt) that happens to bite
hardest here.

**Significance:** low-stakes for the "did we replicate" question specifically
(Raimondi's own llama-pretrained delta, +0.24, is itself the second-smallest
of their three — a modest effect that this project's parse-rate problem
simply can't resolve one way or the other). Higher-stakes as a general
warning: any other pretrained-arm claim in this release that hasn't been
cross-checked against `parsed_rating` (see §3) carries the same risk of
either a spurious result (as gemma's was) or a null that's actually just
underpowered (as llama's may be).

## 3. Gap 0 (the one that isn't really a gap) — gemma's "reversal" was a scoring artifact

Not a Raimondi discrepancy at all once diagnosed, but worth recording here
because it's the reason the pretrained-rating methodology in §1 uses
`parsed_rating` instead of this pipeline's default `ev_rating`. The
logit-fallback EV score (`analysis/rq1_v1_1_robustness/lib.py::_logit_ev_rating`)
initially showed gemma-pretrained with a *significant reversal*
(β=−.172, p=.000, moral-only) — the opposite of Raimondi's +0.51. Checking
`ev_rating` against the model's actual parsed answer (reusing the method
`26_ev_scoring_validation.py` already established for RQ1c, item 11) found
the two are essentially uncorrelated on this cell (r≈0.007) — gemma-pretrained
mostly doesn't produce a parseable number (43.5% failure rate), and the
logit-fallback reconstruction from first-token logprobs was measuring
something other than the model's judgment. Substituting `parsed_rating`
flips the sign and lands almost exactly on Raimondi's own number
(+0.539 vs. +0.51).

**Significance:** this is the most important finding of the whole
investigation, not a footnote. It means **the pipeline's default scoring
method can silently manufacture a significant, wrong-direction effect on
low-parse-rate pretrained checkpoints**, and it did so here undetected until
this specific cell was cross-checked. Item 11 previously validated
`ev_rating` against `parsed_rating` only for RQ1c's typicality×sign term. No
other pretrained-arm result in this release has had the same cross-check.
This should be treated as an open action item: **any claim resting on
`ev_rating` for a pretrained checkpoint is unverified until spot-checked
against `parsed_rating` the way this cell was**, not just the ones this
investigation happened to touch.

## 4. Gap 2 — mistral does not replicate the finetuned effect (the real divergence)

**What we found:** null, twice over. Moral-only finetuned `sign_c`: β=.062,
WCB p=.408 (small-cluster-robust test) *and* asymptotic Wald p=.366 (the
less conservative test) — both agree on no effect. This isn't a
power/rigor artifact: mistral-instruct has the **highest parse rate in the
entire release (98.2%)**, so this isn't a repeat of the gemma/llama
measurement problem above.

**Why this one is credible as a real divergence, not noise:** this project
has an unusually well-documented history of mistral being the source of
real anomalies rather than normal model heterogeneity:
- v1.0's original run reported a significant mistral *reversal*
  (Holm p=.002) that was later retracted as a tokenizer bug — every Mistral
  `logprobs_0_10` vector was flat (`EV ≡ 5.0`), a measurement failure, not a
  behavior.
- After the fix, v1.1 found mistral's sign×tuning interaction is a clean
  null, not a reversal — already a divergence from "Raimondi found a large
  effect in all three models," documented before this session started.
- RQ1b's mistral-nonmoral cell has an independent, still-unresolved
  disagreement between estimators (family-FE WCB p=.255 vs. random-slope
  p=.0021) that SIMEX ruled out measurement-error as the explanation for
  (`docs/rq1_findings/OUTSTANDING_STATISTICAL_ANALYSIS.md` item 2).
- This session's nonmoral-subdomain breakdown found mistral trending in the
  *reversed* direction (good > bad) across pooled nonmoral, aesthetic, and
  procedural subdomains alike — never significant, but a consistent pattern
  recurring across three independent slices.

**Theories, roughly in order of how checkable they are:**
1. **Model/weights mismatch.** Different exact revision, quantization, or
   download of `mistralai/Mistral-7B-v0.1`/`-Instruct-v0.1` than Raimondi
   used. Cheaply checkable: compare weight hashes / revision tags against
   whatever Raimondi's repo or appendix specifies, if available.
2. **Prompting/decoding mismatch.** Raimondi sampled at
   T~U(0.85, 1.15); chat template application and system-prompt wording are
   also both explicitly flagged as project-specific choices
   (`specs/00_PLAN.md` §"Chat template policy"). A mismatch here specifically
   for mistral (not gemma/llama) would need to interact with something
   mistral-specific — plausible, given mistral's chat template has
   historically been a common source of subtle handling bugs across
   tooling, but not yet checked.
3. **Genuine model difference.** Mistral-7B-v0.1-Instruct may simply not
   have acquired the same finetuning-induced bias Raimondi's copy did —
   e.g., if Raimondi's instruct checkpoint or its exact release differs, or
   if the specific instruction-tuning data diverged in a way that happens to
   affect this bias. This is the least checkable theory from our side alone
   and the one that would be most interesting if true.
4. **Stimulus-content difference.** Our moral vignettes are this project's
   own LLM-drafted, human-curated taxonomy, not Ngo's original human-written
   80 items — even restricted to "moral" scope, the items themselves differ.
   Weakest of the four theories, because gemma and llama both replicate on
   the same stimulus set — if content were the dominant driver, it should
   have suppressed their effects too.

**Significance:** this is the one place in this whole comparison where "we
built a different, if related, experiment" isn't a sufficient explanation on
its own — gemma and llama's success on the *same* stimuli, elicitation
pipeline, and test standard rules out most shared-infrastructure
explanations, which is exactly why mistral is worth isolating rather than
folded into a general "our design differs from theirs" story. It also means
**any RQ1 claim resting on mistral's presence of a classic Knobe-style
bias should be treated as unsupported, now on three independent lines of
evidence** (this comparison, the RQ1b-nonmoral disagreement, and the
nonmoral-subdomain reversal trend) — not a single fragile result.

## 5. What this changes about the RQ1_base "replication" claim

The honest summary is no longer a single verdict — it's per-family:

- **Gemma**: replicates at both stages once scoring is corrected. The
  strongest, cleanest case for "this project reproduces Raimondi."
- **Llama**: replicates at the finetuned stage (β=.658, the largest effect
  in the study); pretrained stage is unresolved, not contradictory.
- **Mistral**: does not replicate at the finetuned stage, on two independent
  tests, with no measurement-artifact explanation available on the
  pretrained-scoring axis that resolved gemma's discrepancy. This is a real
  finding, worth reporting as such rather than smoothing over as "one of
  three didn't work."

## 6. Open follow-ups this investigation surfaced

- **Audit every pretrained-arm `ev_rating` claim in this release against
  `parsed_rating`** the way this session did for one cell (§3) — item 11
  only ever validated this for RQ1c, and gemma's reversal shows the failure
  mode is real, not hypothetical.
- **Resolve llama-pretrained's parse-rate problem** if the pretrained arm of
  RQ1_base is going into a writeup — either accept it as an honest gap or
  investigate a constrained-decoding fix to raise the parseable-response
  rate.
- **Investigate the mistral divergence directly**, in the order listed in
  §4: check weights/revision first (cheapest), then chat-template/decoding
  parameters, before concluding it's a genuine cross-model behavioral
  difference.
