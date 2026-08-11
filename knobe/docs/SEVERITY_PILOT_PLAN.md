# Escalated-Severity Nonmoral Pilot — Plan of Action (drafted 2026-08-10, for execution starting 2026-08-11)

**Goal:** find out whether nonmoral-bad (NMB) severity can be raised toward
moral-bad (MB) levels (~7/10) while staying reviewer-classified nonmoral, or
whether it hits a moralization ceiling — and if there's a ceiling, locate it
empirically rather than assume a number. This is the direct empirical
follow-up to `docs/SEVERITY_MORALIZATION_BACKGROUND.md`'s prediction
(procedural/aesthetic moralize fast; prudential is the best candidate to
resist it) and to `RQ1_MECHANISM_ANALYSIS_v1.1.md` §1 / script `17`'s
finding that the categorical moral/nonmoral label still out-predicts raw
continuous severity on overall model fit (AIC), even though severity and
the label are highly correlated (r=.885 within moral items) — i.e., the
label may be carrying information a severity score alone doesn't, which is
exactly what a clean severity-matched design would let you test properly.

## Why this is worth doing before spending more compute on RQ1a

The severity-adjusted RQ1a interaction is underpowered by a lot at current
sample sizes (`docs/RQ1_STATISTICAL_METHODS_v1.1.md` §11.2: gemma/mistral
would need a ~20x larger release to resolve it under the existing
confounded design). A severity-matched design doesn't just need less new
data than a brute-force N increase — it needs **zero** new subject-model
elicitation to test the *stimulus-design* question (does the confound
survive better vignette-writing), because the curation reviewer step is the
only thing that needs to run for this pilot. Only if the pilot succeeds
(finds severity-matched nonmoral content that survives moral-relevance
review) does it justify a real elicitation run.

## Scope: small, curation-only, cheap

1. **3–5 pilot families**, prudential subdomain only for the first pass
   (per the moralization background note, prudential is the best-motivated
   candidate: no other party's welfare/rights is engaged, so Turiel's/TDM's
   harm-to-another criterion is least likely to fire). Reuse existing
   domains already in the release (pick from `ACAD`, `FIN`, `WORK` — domains
   where a purely self-directed prudential disaster is easy to write
   plausibly) rather than inventing new ones.
2. **3 severity rungs per family**, escalating from the current ceiling: the
   existing max NMB severity in the release is 4 (`data/curation/curated_v1.1.csv`,
   `nonmoral_subdomain == "prudential"` currently has only 4 items, severity
   capped at 2 — barely explored). Target rungs: ~4 (matches current
   procedural ceiling, a sanity baseline), ~6, ~8-9 (approaching MB's ~7
   average). Keep the *low_evocative_outcome*/*high_evocative_outcome*
   distinction and all other `GENERATION_SYSTEM_PROMPT` slot rules
   unchanged — only the outcome's stated magnitude changes across rungs.
3. **Curation only, not elicitation.** Run each rung through
   `knobe curate run --mock` first (free, catches schema/invocation errors),
   then the real reviewer pass (`knobe curate run --reviewer-model
   <sonnet-string>`) — cheap, the full 420-variant v1.1 pass was "~1,680
   calls, minutes not hours" per `docs/V1_1_WORKFLOW.md`; a 3-5 family x
   3-rung pilot (roughly 12-20 variants x 4 curation questions) is a rounding
   error on that.
4. **Track `moral_relevance` and `severity` together per rung**, not just
   whether the item got flagged. The `check_category_manipulation` threshold
   (`moral_relevance <= 4` for NMB, per `configs/curation.yaml`) is a hard
   cutoff, but the *slope* of moral_relevance vs. severity across rungs is
   the actually informative number — even sub-threshold movement tells you
   how close to the ceiling you are.

## Method: write, curate, read the slope, stop or escalate

For each pilot family:

1. Write the baseline (current-ceiling, ~severity 4) NMB/NMG pair, following
   every existing `GENERATION_SYSTEM_PROMPT` slot rule (dimensional
   independence, no banned words, etc.) — this is a sanity check that the
   pilot's authoring matches production quality before escalating.
2. Write two escalated rungs (~6, ~8-9) of the *same* storyline — same
   agent/goal/actions, only the outcome's stated magnitude changes. Do NOT
   change `affected_entity` to someone else's welfare partway through
   escalation — that would confound "more severe" with "more clearly
   affects another party," which is a different manipulation
   (`GENERATION_SYSTEM_PROMPT`'s own dimensional-independence rule already
   warns about this exact failure mode for the unrelated moral-bleed fix).
3. Run all rungs (baseline + escalated, all pilot families) through curation
   together as one batch — cheaper and lets `BATCH_QA_PROMPT_TEMPLATE`-style
   cross-checking catch drift across rungs.
4. Plot/tabulate `moral_relevance` against `severity` per family, across
   rungs. Three possible shapes, each with a different next step:
   - **Flat** (moral_relevance stays ≤4 even at rung 3): severity and moral
     status ARE separable in this taxonomy, at least for prudential content.
     → Proceed to a real elicitation pilot on these items (do subject models
     show the same intentionality asymmetry for severity-matched nonmoral
     items as for moral ones?).
   - **Rising, crosses threshold before rung 3**: locates the empirical
     ceiling. → Report the ceiling severity value; that number is itself a
     finding (how much harm-independent-of-party a nonmoral outcome can
     carry before an independent judge calls it moral) worth writing up
     against the moralization literature, win or lose for the original
     RQ1a goal.
   - **Rising from rung 1** (even the baseline "current ceiling" item is
     borderline): would suggest the *existing* NMB severity=4 ceiling in the
     release is already near the moralization boundary, which raises the
     interesting possibility that ALL subdomains (not just
     procedural/aesthetic) are structurally capped, not just the ones
     already documented as concentrated in `FLAGGED_VARIABLES_README.md`.
5. **Independent-judge check before trusting any "flat" result**: per
   `docs/V1_1_REVISION_PLAN.md` Workstream B's precedent (the 24 revised
   NMB/NMG families were cross-checked against ChatGPT, not just the
   production Sonnet reviewer, specifically to rule out one judge's
   idiosyncrasies), run any rung that reads "flat" through a second model
   (same manual-conversation protocol used before) before concluding
   severity and moral status are separable here. A single-reviewer "flat"
   result is not sufficient given how consequential this finding would be.

## Optional extension, only if the curation-only pilot succeeds

If (and only if) some rung/family combination produces genuinely
severity-matched, reviewer-confirmed-nonmoral content: elicit
`moral_relevance`-equivalent self-report from the three subject models
(gemma/llama/mistral, both checkpoints) on those specific items, piggybacking
on the `affect_salience` precedent from v1.1 (new question type, no schema
work needed beyond what already exists). This tests the genuinely novel
question from the original conversation: do the *subject* models moralize
high-severity nonmoral content even when the human-modeled reviewer
doesn't? A "yes" here would be a new finding in its own right, independent
of whatever RQ1a's fate ends up being.

## What this plan deliberately does NOT do yet

- Does not touch the full v1.1 release or `data/authoring/ALL_DOMAINS_master_matrix.csv`
  — pilot items are pilot-only files (e.g.
  `data/authoring/severity_pilot/pilot_matrix.csv`), never merged into the
  frozen release per `data/release/README.md`'s append-only rule.
- Does not commit to a specific severity-target number in advance — the
  point of the pilot is to *find* the ceiling empirically, not assume one
  from the background note's theoretical prediction.
- Does not run any new subject-model elicitation unless the curation-only
  phase actually succeeds — avoids spending H200/API budget on a design
  that might not clear curation.

## Rough time/cost estimate

Writing 3-5 families x 3 rungs (12-20 variants): an afternoon of careful
authoring (this is the part most likely to need iteration — getting a
prudential disaster to read as severity-9 without smuggling in
another-party harm is a real writing challenge, not a mechanical task).
Curation pass: minutes, trivial API cost. Second-reviewer cross-check on any
flat result: an hour of manual ChatGPT-conversation labor, matching the
Workstream B precedent. Total: plausible as a single day's work, matching
the "probably for tomorrow" framing this plan was scoped for.
