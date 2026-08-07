# v1.1 revision plan: moral/nonmoral labeling + RQ1a design

**Status:** Workstream 0 done. A/B/C are proposals, not yet acted on.
Companion to `DECISIONS_FOR_HUMANS.md` (methodology-freeze decisions) and
`data/curation/FLAGGED_VARIABLES_README.md` (the diagnostic data this plan
is built from). Nothing here should be implemented by iterating against
curation output until it "passes" — see the method section below.
**Explicitly out of scope:** a human-baseline arm on these stimuli. This
project is about locating and decomposing a known human effect inside LLMs,
not re-establishing the human effect itself; see "Out of scope" section.

## Workstream 0 — immediate data-integrity fixes (done, no dependencies)

1. **`vignettes_curated.json` `accepted`-field bug — fixed.** All 420
   records had the literal string `"accepted": "False"`, while `curated.csv`
   (the authoritative source, and the one the analysis pipeline reads) has
   `True` for all 420, consistent with the documented release-changelog
   decision (2026-08-04: "all 420 variants accepted... rather than
   resolved"). Uniform-across-all-rows wrongness is the signature of a
   hardcoded/stale default in whatever ad hoc script produced this export
   (that script isn't in the tracked codebase — `git log` shows the JSON
   was added as a data file only, commit `bdf9258`, no exporter committed
   alongside it). Fixed by cross-referencing `curated.csv` by `variant_id`
   and correcting only the `accepted` field (now a proper JSON boolean, not
   a string) — every other field left untouched. Flag to Parker as a
   concrete pipeline bug in that export path, in case it gets regenerated
   from source later and the same bug recurs.
2. **Reversed vividness-pair count — reconciled, not a data discrepancy.**
   The main-run writeup's "36 pairs reversed" and an independent
   recomputation's "27 families" (51 including zero-gap ties) both check out
   against `curated.csv` — they're counting different units. The writeup
   counts at the **pair level** (out of 210 total `(family, typicality)`
   pairs — the exact unit `check_pairs` operates on): 36 pairs have a
   strictly negative vividness gap. The family-level number averages a
   family's (up to two) typicality-conditioned pair gaps and checks the
   sign of the mean: 27 families have a strictly negative mean gap, 51 have
   a non-positive one. Both are reproducible from the same source data;
   pick whichever unit is relevant per use (pair-level for anything mirroring
   `check_pairs`'s own logic, family-level for anything keyed on `family_id`)
   and state which one is being used.

## Why this exists

RQ1a (`sign_c * vt_c`, "is the Knobe asymmetry moral-specific?") came back
null and inconsistent in the v1.0 main run (Holm p>.10 across all three
model families). Three causes were identified, and they are **not fully
separable from each other**:

1. **Structural:** `sign` and `valence_type` are both fixed properties of a
   family (a family is entirely MB, MG, NMB, NMG, or NEU — never more than
   one), so the interaction is a fully between-family contrast that has to
   absorb the entire `var_family` component as noise (58% of total variance
   for gemma-instruct per the G1 pilot). The power simulation shows this
   contrast not reaching 80% power even at 480 families — and that
   simulation's own variance decomposition (family + residual only, no
   item-within-family term) is flagged by the power report itself as
   "systematically optimistic," so the true picture may be worse.
2. **Measurement:** `moral_relevance` — the independent reviewer rating used
   to define `valence_type` — misclassifies 57/420 variants (13.6%) relative
   to their intended category, concentrated in specific domains/subdomains
   and clustered by family (not random noise). This attenuates the
   interaction on top of (1), and also attenuates RQ1b (see Workstream B),
   which subsets its data by the same `valence_type` variable.
3. **Set-completeness:** the natural fix for (1) is to model the shared
   storyline structure (`set_id`, five valence-siblings per set) as a
   blocking variable instead of relying on `family` alone (Workstream A
   below). That fix only works if enough sets have clean, present data
   across MB/MG/NMB/NMG. Checked directly against the current data: **only
   7 of 21 sets** have all four valences clean by the `moral_relevance`
   check. Clean-family rates per valence are uneven — MB 21/21, NEU 20/21,
   NMG 13/21, MG 10/21, NMB 10/21. So (2) and (3) collide: cleaning up
   `moral_relevance` by *excluding* flagged variants would collapse the
   blocking design from 21 usable sets to 7, trading one power problem for
   another. Labels have to be fixed by **rewriting in place** (same
   `family_id`/`set_id`), not by dropping items.

There's a fourth wrinkle compounding this: of the 63 non-MB families
(MG/NMB/NMG — exactly where `moral_relevance` concentrates), **zero are
clean on both `moral_relevance` and the vividness/evocativeness gap check
simultaneously**, and 97% of the moral_relevance-flagged non-MB families
also fail the vividness-gap check. This is substantially the *same* ~30
families needing both fixes, not two disjoint problems — see Workstream B
below, which merges what was previously planned as two separate passes.

Bottom line: growing family count isn't worth funding until Workstreams A
and B both land, and B needs to be one combined content pass, not two
sequential ones.

## Workstream A — analysis fix (no new data collection)

Add `set_id` (recoverable from `family_id` by stripping the valence token —
`ENV-MB-01` and `ENV-MG-01` share `set_id = ENV-01`) as a random effect
alongside `family` in the RQ1a fit, nested or crossed as convergence allows.
The five valence-siblings in a set share one storyline (agent/goal/actions)
by construction (`GENERATION_SYSTEM_PROMPT`), so this recovers a genuine
matched-block design that the current family-only clustering discards. This
is a **within-set, between-valence** design, not a coverage lever like
domain — it targets the RQ1a contrast specifically and should be tried
before any new family generation is funded. Its payoff is capped by
Workstream B — see "Why this exists" §3 above.

**Before trusting the result:** confirm `set_id` isn't absorbing part of the
`sign_c:vt_c` fixed effect itself. Since `set_id` is defined by stripping
exactly the token that also drives `valence_type`, there's a real risk of
collinearity between the new random effect and the fixed effect it's meant
to de-noise. Check the fixed-effect point estimate is stable (not moving
suspiciously) once `set_id` is added — only its standard error should
shrink. This is also diagnostic either way: if `var_family` shrinks
substantially once `set_id` is added, that's real power gained cheaply and
evidence the residual was storyline-flavor variance. If it doesn't shrink,
that's evidence the leftover noise is construction-quality noise (Workstream
B's problem) rather than storyline flavor — informative for how urgently
the vignette-revision work is needed versus optional.

**Prerequisite, not yet done:** re-run the G1 power simulation with an
item-within-family variance term added (currently absent — see "Why this
exists" §1) before committing to any v1.1/v2 family-count target. Otherwise
the target itself may be wrong regardless of what `set_id` buys you.

**Open decision:** does `set_id` go in as the primary spec for RQ1a, or as
a declared sensitivity analysis alongside the existing domain-slope
sensitivity machinery in `configs/contrasts.yaml`? Recommend: primary,
given it's the natural design-implied structure, not an ad hoc check — but
confirm before implementing, same as the other primary-model decisions in
`DECISIONS_FOR_HUMANS.md` §(b).

## Workstream B — combined revision pass: moral-category labels + evocativeness, together, on the same non-MB families

Originally scoped as two separate workstreams (label fix now, evocativeness
redesign later). Merging them because they hit the same items: the ~30
non-MB families that need a `moral_relevance` fix essentially all also need
an evocativeness fix, and rewriting the same family's text twice in two
uncoordinated passes risks inconsistent edits and wastes a curation cycle.

**The failure mode to avoid:** hand-editing a flagged vignette and
resubmitting it to the same reviewer model until its score crosses
threshold, for either variable. That optimizes for one judge's surface
reaction, not construct validity, and risks introducing a new
wording-explicitness confound correlated with valence_type or evocativeness.

**The method to use instead:**

1. **Diagnose at the rule level, for both variables, before writing anything.**
   - `moral_relevance` (source: `moral_relevance_flagged.csv` +
     `FLAGGED_VARIABLES_README.md`): shared goals that touch a domain's real
     stakes (patient staffing ratios, loan fee structures, emissions
     equipment) leak moral weight into a nominally-nonmoral outcome,
     concentrated in `procedural`/`aesthetic` subdomains and in
     Healthcare/Finance/Environment/Data Privacy/Product Safety.
   - `vividness`/evocativeness (source: `vividness_gap_flagged.csv`): not
     concentrated — near-universal (82% of pairs, including a meaningful
     share of MB) — because `high_evocative_outcome` was written to be more
     *concrete/specific*, while the curation question asks about *emotional
     vividness*. A construct mismatch, not a per-item defect.
2. **Fix the moral-category construction rule.** Generalize the existing
   document-readability-trap guardrail in `GENERATION_SYSTEM_PROMPT`
   (`src/knobe/constants.py`) — currently scoped to documents only — into:
   *for NMB/NMG, the outcome must be as dimensionally independent from the
   shared goal's real stakes as NEU is already required to be.*
3. **Re-ground the evocativeness construct in the model, not in an external
   judge.** The original human finding this design traces to (Ngo) is that
   *strong emotional reactions in the individual* amplify the asymmetry —
   the construct is affective salience *as experienced by the subject*, not
   "vivid wording" as an external property. An external lexicon (e.g. NRC)
   doesn't fix this: it encodes what human lexicographers tagged as
   emotionally loaded, which has no guaranteed relationship to what's
   salient to the models actually being tested, and doesn't solve the
   reviewer-model-convergence problem, it just moves it to a different
   fixed proxy. Two candidate operationalizations that are grounded in the
   subject models themselves instead:
   - **Direct self-report from subject models**: add an affect-salience
     question ("how emotionally striking is this scenario, 0-10?") to the
     elicitation set per subject model per variant. Lets affect salience
     vary *by model* — a model-specific difference here is itself an
     etiology-relevant finding, not just noise.
   - **Surprisal/perplexity as a model-native signal**: token-level
     surprisal of the subject model on the scenario text, computed from
     retained logprobs. No judge, no subjective rating, directly measures
     how strongly the text registers to the model's own predictive
     distribution — closer to a mechanistic measure and ties into the
     planned S6/S7 activation-level work.
   - **Ruled out, tested and didn't hold up:** personal-report framing
     ("residents said/reported..." vs. "a survey found...") was checked
     directly against `curated.csv` as a candidate wording-level lever.
     It correlates with *less* severity drift (0.51 vs. 0.92 mean diff) as
     hoped, but does **not** meaningfully raise the vividness gap (0.51 vs.
     0.45 mean gap, ~18% vs. 17% pass rate at the ≥2 threshold — no real
     difference). Don't rely on this framing trick; it doesn't move the
     variable that matters.
   This is an open decision (see below), not resolved here — pick one
   operationalization (or both, as complementary evidence) before rewriting
   any content.
4. **Rewrite the ~30 flagged non-MB families against the moral-category rule
   and the chosen affect-salience construct in one pass**, using researcher
   judgment, not trial resubmission, preserving `family_id`/`set_id` so set
   membership for the Workstream A blocking model is restored rather than
   lost.
5. **Extend the evocativeness fix to MB and NEU separately, once the
   construct is redefined.** If only the non-MB families revised for
   `moral_relevance` get the new evocativeness treatment, evocativeness's
   effective manipulation strength would differ *by valence* purely as a
   revision-history artifact — a new confound for both RQ1a and RQ1c. MB/NEU
   don't need a `moral_relevance` edit, but do need the same evocativeness
   redefinition applied, as a lighter follow-up pass (no moral-category
   rewrite needed there, so this should be mechanical).
6. **Validate with a model that had no part in the diagnosis.** Run the
   revised batch through a model other than the primary reviewer (e.g.
   GPT-5/GPT-4-class) — not to pick whichever model agrees, but as a check
   that the moral-category fix generalizes past one judge's quirks. (This
   check is for the `moral_relevance` fix specifically; the affect-salience
   construct in step 3 is deliberately designed to not need this kind of
   external judge validation at all.) Doesn't conflict with the
   reviewer≠subject invariant (`curate.py:check_reviewer_not_subject`) since
   neither Sonnet nor GPT is a subject family (Gemma/Llama/Mistral).
   - If Sonnet and GPT agree the revision reads as intended: proceed.
   - If they disagree: that disagreement is itself worth recording
     (judge-dependent ambiguity), not resolved by picking the model that
     gives the answer you want.
7. **No-peeking firewall.** Revise based on the curation diagnostics only.
   Do not consult v1.0's `sign_c:vt_c` or evocativeness×sign point estimates
   while deciding which families to rewrite or how. Record the revision
   decisions (this doc, updated) before re-running curation on the revised
   batch.
8. **Separately flagged, not part of this revision:** MG's much looser
   `moral_relevance` spread than MB's (stdev 2.31 vs 0.59) may reflect a
   reviewer-instrument asymmetry (harms read as unambiguously moral,
   equivalent benefits don't) rather than a stimulus defect. Worth a small
   calibration check (rate matched harm/benefit pairs of equal magnitude)
   independent of the family-by-family rewrite.

## Workstream C — measurement fixes independent of vignette content

These don't touch stimuli, so they can proceed on their own timeline, but
should be bundled into the same v1.1 release since it already requires
full re-elicitation (see costs below).

1. **Unify scoring method across checkpoints.** 5 of 6 checkpoints fall
   back to EV-over-logprobs because free-text parse rate is below 95%
   (as low as 25% for llama-pretrained); mistral-instruct alone uses parsed
   ratings (98% parse rate). This is a live confound for any *between-model*
   claim, including the Mistral reversal — currently the cleanest-measured
   checkpoint by construction is also the one that reverses. Needs a
   prompt-format fix to raise parse rates uniformly, or a decision to
   EV-score every checkpoint the same way, before leaning on cross-model
   comparisons in a writeup.
2. **Increase response-level N for the RQ1b blame/praise elicitation** (more
   completions per existing item, not more families). RQ1b's item-level
   blame/praise means are used as predictors and are noisy point estimates
   (the writeup's own errors-in-variables caveat: "slope magnitudes are
   attenuated, signs interpretable"). Different fix from RQ1a's
   between-family bottleneck — this is per-item measurement noise used as a
   regressor, which more responses per item directly shrinks. Cheap (no new
   stimuli), and de-attenuates a direct etiology question (is the asymmetry
   mediated by responsibility attribution specifically).

## Cutting v1.1: what it actually costs

- **Re-elicitation, not just re-generation, is the expensive part.** Any
  content change moves the release manifest hash; elicitation refuses to
  run against a stale hash (`data/release/v1.0` sha256 guard). The
  family-random-intercept model needs the full pooled dataset for
  comparable variance estimates, so this means redoing the full
  189,000-completion, two-H200-job run — not just the ~30 revised families.
- **Comparability burden.** v1.0's other findings (gemma/llama replication,
  the Mistral reversal, the typicality×sign effect) are a published draft.
  v1.1 either supersedes v1.0 outright or owes a v1.0-vs-v1.1 stability
  check on the untouched RQs.
- **Bundle Workstreams A, B, and C into the same release.** Cutting a
  release for label cleanup alone, without the `set_id` structural fix,
  risks spending the full re-elicitation budget and still landing
  underpowered on RQ1a for reasons the labels don't touch — and vice versa,
  per "Why this exists" §3. Workstream C is free to bundle in since the
  re-elicitation cost is already being paid.
- **Timing is fine.** `prereg_frozen: false` in `configs/contrasts.yaml`
  means these are pre-freeze design decisions, not post-hoc changes to a
  locked analysis plan — same status as the existing `DECISIONS_FOR_HUMANS.md`
  items.

## Out of scope for v1.1 (tracked here so nothing gets lost, not being worked on now)

- **Human baseline on these stimuli — explicitly excluded.** This project's
  aim is to locate and decompose a known human effect inside LLMs, not to
  re-establish the human effect on a new stimulus set. Not a cost/tradeoff
  call, a scope call — leave it out.
- **Adversarial scrutiny of the Mistral reversal.** Independent of
  everything above — it doesn't need RQ1a or evocativeness fixed to be real
  or interesting, and is arguably the study's actual headline finding.
  Per-domain breakdown, per-question split, direct inspection of
  mistral-instruct's raw completions (easiest checkpoint to read directly,
  98% parse rate). Don't let this get deprioritized behind the
  secondary-contrast repair work above.
- **Domain-random-slope QUALIFICATION.** Every headline contrast — including
  the two solid ones (base replication, typicality×sign) — is marked
  QUALIFIED for large across-domain variance. Distinct from `var_family` and
  the evocativeness construct problem, and not obviously fixed by anything
  in this plan. Needs its own choice: add domains for a real cross-domain
  generalization claim, or frame publication claims as domain-specific.
- **CLMM / proper mixed-effects ordinal model.** The LMM-primary choice was
  an engineering constraint (`statsmodels.OrderedModel` has no random
  effects), not a preference. Worth doing once (R's `ordinal::clmm`, or a
  Bayesian ordinal mixed model) but a rigor fix, not a power booster —
  shouldn't block v1.1.
- **More model families/sizes**, to test whether the Mistral reversal is
  model-specific or scale-dependent.
- **Alignment-method variation** (SFT vs. DPO vs. RLHF, not just
  tuned-vs-not).
- **Chat-format robustness** (`--chat-comparison`, already planned but not
  run).
- **Real preregistration** (OSF or similar) of the RQ1a `set_id` model, the
  evocativeness redefinition, and the v1.1 family-count target.

## Decisions needed before implementation (mirrors `DECISIONS_FOR_HUMANS.md` format)

- [ ] Confirm `set_id` as primary vs. sensitivity spec for RQ1a (Workstream A).
- [ ] Run the item-within-family power resim before setting any v1.1/v2
      family-count target (Workstream A).
- [ ] Confirm the generalized NMB/NMG dimensional-independence guardrail
      wording (Workstream B, step 2) before rewriting flagged families.
- [ ] Choose the affect-salience operationalization for evocativeness:
      subject-model self-report, surprisal-based, or both (Workstream B,
      step 3).
- [ ] Choose the independent validation model for the moral-category fix
      (Workstream B, step 6).
- [ ] Confirm v1.1 scope: A+B+C bundled in one release?
- [ ] Confirm v1.1 supersedes v1.0 vs. runs as a comparison release.
