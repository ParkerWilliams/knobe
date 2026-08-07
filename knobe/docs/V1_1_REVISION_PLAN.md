# v1.1 revision plan: moral/nonmoral labeling + RQ1a design

**Status:** proposal, not yet acted on. Companion to `DECISIONS_FOR_HUMANS.md`
(methodology-freeze decisions) and `data/curation/FLAGGED_VARIABLES_README.md`
(the diagnostic data this plan is built from). Nothing here should be
implemented by iterating against curation output until it "passes" — see
the method section below.

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
   contrast not reaching 80% power even at 480 families.
2. **Measurement:** `moral_relevance` — the independent reviewer rating used
   to define `valence_type` — misclassifies 57/420 variants (13.6%) relative
   to their intended category, concentrated in specific domains/subdomains
   and clustered by family (not random noise). This attenuates the
   interaction on top of (1).
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
2. **Fix both construction rules before rewriting any content.**
   - Generalize the existing document-readability-trap guardrail in
     `GENERATION_SYSTEM_PROMPT` (`src/knobe/constants.py`) — currently
     scoped to documents only — into: *for NMB/NMG, the outcome must be as
     dimensionally independent from the shared goal's real stakes as NEU is
     already required to be.*
   - Redefine `high_evocative_outcome` generation to target emotional
     vividness directly (or change the curation question to ask about
     concreteness/specificity, whichever direction is judged truer to the
     original RQ1c intent — this is an open decision, see below).
3. **Rewrite the ~30 flagged non-MB families against both rules in one
   pass**, using researcher judgment, not trial resubmission, preserving
   `family_id`/`set_id` so set membership for the Workstream A blocking
   model is restored rather than lost.
4. **Extend the evocativeness fix to MB and NEU separately, once the
   construct is redefined.** If only the non-MB families revised for
   `moral_relevance` get the new evocativeness treatment, evocativeness's
   effective manipulation strength would differ *by valence* purely as a
   revision-history artifact — a new confound for both RQ1a and RQ1c. MB/NEU
   don't need a `moral_relevance` edit, but do need the same evocativeness
   redefinition applied, as a lighter follow-up pass (no moral-category
   rewrite needed there, so this should be mechanical).
5. **Validate with a model that had no part in the diagnosis.** Run the
   revised batch through a model other than the primary reviewer (e.g.
   GPT-5/GPT-4-class) — not to pick whichever model agrees, but as a check
   that the fix generalizes past one judge's quirks. This doesn't conflict
   with the reviewer≠subject invariant (`curate.py:check_reviewer_not_subject`)
   since neither Sonnet nor GPT is a subject family (Gemma/Llama/Mistral);
   it's a second, independent check layered on top of the required one.
   - If Sonnet and GPT agree the revision reads as intended: proceed.
   - If they disagree: that disagreement is itself worth recording
     (judge-dependent ambiguity), not resolved by picking the model that
     gives the answer you want.
6. **No-peeking firewall.** Revise based on the curation diagnostics only.
   Do not consult v1.0's `sign_c:vt_c` or evocativeness×sign point estimates
   while deciding which families to rewrite or how. Record the revision
   decisions (this doc, updated) before re-running curation on the revised
   batch.
7. **Separately flagged, not part of this revision:** MG's much looser
   `moral_relevance` spread than MB's (stdev 2.31 vs 0.59) may reflect a
   reviewer-instrument asymmetry (harms read as unambiguously moral,
   equivalent benefits don't) rather than a stimulus defect. Worth a small
   calibration check (rate matched harm/benefit pairs of equal magnitude)
   independent of the family-by-family rewrite.

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
- **Bundle Workstream A and B into the same release.** Cutting a release
  for label cleanup alone, without the `set_id` structural fix, risks
  spending the full re-elicitation budget and still landing underpowered on
  RQ1a for reasons the labels don't touch — and vice versa, per "Why this
  exists" §3.
- **Timing is fine.** `prereg_frozen: false` in `configs/contrasts.yaml`
  means these are pre-freeze design decisions, not post-hoc changes to a
  locked analysis plan — same status as the existing `DECISIONS_FOR_HUMANS.md`
  items.

## Decisions needed before implementation (mirrors `DECISIONS_FOR_HUMANS.md` format)

- [ ] Confirm `set_id` as primary vs. sensitivity spec for RQ1a (Workstream A).
- [ ] Confirm the generalized NMB/NMG dimensional-independence guardrail
      wording (Workstream B, step 2) before rewriting flagged families.
- [ ] Confirm the evocativeness redefinition direction: rewrite
      `high_evocative_outcome` to target emotional vividness, or rewrite the
      curation question to ask about concreteness (Workstream B, step 2).
- [ ] Choose the independent validation model (Workstream B, step 5).
- [ ] Confirm v1.1 scope: A+B only (B now includes the former Workstream C)?
- [ ] Confirm v1.1 supersedes v1.0 vs. runs as a comparison release.
