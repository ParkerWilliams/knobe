# Severity De-Mystification and Escalated-Severity Pilot — Plan of Action (drafted 2026-08-10, updated 2026-08-10; execution starting 2026-08-11)

**Two phases, in order.** Phase 0 asks whether the severity/moral
entanglement (r=.885 within moral items) is partly a **measurement
artifact** — the curation question conflates two things — before assuming
it's a fact about the stimuli. Phase 1 (the original plan, now demoted to
second because it's more expensive) is the escalated-severity nonmoral
vignette pilot, which only makes full sense once Phase 0's answer is known.
Phase 0 is cheaper, faster, and needs zero new vignette authoring — it
should run first, and could change how much of Phase 1 is even necessary.

## Phase 0: is "severity" measuring one thing or two?

**The trigger.** The curation severity question reads: *"How severe or
significant is this outcome, on a scale from 0 to 10?"* (`CURATION_QUESTIONS`,
`constants.py`). That disjunction is worth taking seriously as a validity
problem in its own right, independent of anything about the stimuli:
"severe" naturally reads as *magnitude of material consequence* (cost,
scale, harm), while "significant" naturally reads closer to *how much this
matters/how important it is* — a term that, in ordinary usage, leans on the
same intuition that makes something read as a moral issue in the first
place ("that's a significant issue" ≈ "that's a moral issue"). Two readings
of why the question is worded this way, both worth stating rather than
picking one:

1. **Benign**: "significant" may just be there as valence-symmetric cover,
   since "severe" sounds odd applied to a *good* outcome — i.e., it's
   solving the good/bad wording-symmetry problem, not smuggling in moral
   weight.
2. **Leaky**: regardless of why it was added, "significant" is close enough
   to "morally/socially important" that a reviewer answering this question
   could be rating "how much does this matter" rather than "how large is
   the material consequence" — which would mean part of the r=.885
   correlation is an artifact of the instrument, not a fact about the
   underlying scenarios.

**If reading 2 has real weight, this is good news, not bad news** — it
means part of RQ1a's difficulty might be fixable by a cleaner *question*,
which is far cheaper than a cleaner *stimulus set* (Phase 1).

### The test: reword the question, re-run curation on the EXISTING 420 variants — no new vignettes needed

1. **Candidate reworded question (magnitude-only, valence-symmetric,
   explicitly excludes "significant"):**
   > "Setting aside whether this outcome is good or bad, how large is its
   > practical impact — in cost, scale, or people/systems affected — on a
   > scale from 0 (negligible) to 10 (massive)?"
2. Run this against the same 420 v1.1 `scenario` texts already in
   `data/release/v1.1/vignettes.csv` — a single new curation question, not
   the full four-question battery, so ~420 reviewer calls, not ~1,680
   (`docs/v1_1_release_process/V1_1_WORKFLOW.md`'s full-pass cost estimate was "minutes not
   hours" for 4x this many calls).
3. **Do not edit `constants.py`'s `CURATION_QUESTIONS`.** That's a frozen
   instrument (master spec §7, restated in `knobe/README.md`'s "Conventions
   and invariants") — question wording changes go through the project's own
   established reword-validation track (`docs/v1_1_release_process/V1_1_WORKFLOW.md`'s "Type-1
   curation-question reword": test on a subsample, validate, adopt only if
   it clears checks, as a new versioned question, never a silent in-place
   edit). This experiment is exploratory and writes to its own output file,
   never touching `curated_v1.1.csv` or the frozen release.
4. **Compare, per family and pooled:**
   - `corr(new_magnitude_score, sign)` within moral items — does it drop
     well below .885? Within nonmoral items — does it move at all from .473?
   - `corr(new_magnitude_score, original_severity_score)` — convergent
     validity: if these are highly correlated (say r>.9), the original
     question was mostly already measuring magnitude, and the "significant"
     framing wasn't doing much independent work (points back toward Phase
     1's stimulus-level story being the dominant explanation). If they
     diverge substantially, that's direct evidence the original score was
     conflating two things.
   - Refit the RQ1a severity-adjusted interaction (`14_rq1a_severity_set_fe_wcb.py`'s
     spec) substituting the new magnitude score for `severity_c`. Does the
     SE shrink meaningfully (i.e., does the collinearity problem
     documented in `docs/rq1_findings/RQ1_STATISTICAL_METHODS_v1.1.md` §11.2 ease)? Does
     the interaction become resolvable at G=21, or still not?
5. **Three possible outcomes, each with a clear next step:**
   - **Correlation drops substantially, RQ1a's SE shrinks**: the original
     severity measure was partly a wording artifact. Adopt the reworded
     question for future analysis (through the proper reword-validation
     track, not silently), and RQ1a may become resolvable without any new
     vignette writing at all — Phase 1 becomes lower priority, not
     abandoned (a stimulus-level confound could still exist underneath a
     now-cleaner measurement).
   - **Correlation barely moves**: the entanglement is a fact about the
     stimuli, not the instrument — proceed straight to Phase 1 with more
     confidence it's the right lever to pull.
   - **Correlation drops somewhat but not enough to resolve RQ1a's power
     problem**: both explanations have some truth to them — report both,
     and Phase 1 is still worth doing but the expectation for how much it
     alone can fix should be tempered.

**Cost/logistics**: no new authoring, ~420 reviewer calls (cheap), needs
`ANTHROPIC_API_KEY` access this environment doesn't have — same "needs
Parker's API key" split as every other curation-reviewer step in this
project's existing workflow docs. A ready-to-run script skeleton is at
`analysis/severity_wording_check/run_reworded_severity.py` — reuses
`curate.AnthropicReviewer` and `constants.CURATION_PROMPT_TEMPLATE`'s shape
without touching the frozen `CURATION_QUESTIONS` dict, writes to its own
output file. Analysis script (correlation comparison + RQ1a refit) is
`analysis/severity_wording_check/analyze_reworded_severity.py`, runnable as
soon as the reviewer-call output exists.

## Phase 1: Escalated-Severity Nonmoral Pilot

### Why this is worth doing before spending more compute on RQ1a

The severity-adjusted RQ1a interaction is underpowered by a lot at current
sample sizes (`docs/rq1_findings/RQ1_STATISTICAL_METHODS_v1.1.md` §11.2: gemma/mistral
would need a ~20x larger release to resolve it under the existing
confounded design). A severity-matched design doesn't just need less new
data than a brute-force N increase — it needs **zero** new subject-model
elicitation to test the *stimulus-design* question (does the confound
survive better vignette-writing), because the curation reviewer step is the
only thing that needs to run for this pilot. Only if the pilot succeeds
(finds severity-matched nonmoral content that survives moral-relevance
review) does it justify a real elicitation run.

### Scope: small, curation-only, cheap

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
   calls, minutes not hours" per `docs/v1_1_release_process/V1_1_WORKFLOW.md`; a 3-5 family x
   3-rung pilot (roughly 12-20 variants x 4 curation questions) is a rounding
   error on that.
4. **Track `moral_relevance` and `severity` together per rung**, not just
   whether the item got flagged. The `check_category_manipulation` threshold
   (`moral_relevance <= 4` for NMB, per `configs/curation.yaml`) is a hard
   cutoff, but the *slope* of moral_relevance vs. severity across rungs is
   the actually informative number — even sub-threshold movement tells you
   how close to the ceiling you are.

### Method: write, curate, read the slope, stop or escalate

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
   `docs/v1_1_release_process/V1_1_REVISION_PLAN.md` Workstream B's precedent (the 24 revised
   NMB/NMG families were cross-checked against ChatGPT, not just the
   production Sonnet reviewer, specifically to rule out one judge's
   idiosyncrasies), run any rung that reads "flat" through a second model
   (same manual-conversation protocol used before) before concluding
   severity and moral status are separable here. A single-reviewer "flat"
   result is not sufficient given how consequential this finding would be.

### Optional extension, only if the curation-only pilot succeeds

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

### What this plan deliberately does NOT do yet

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

### Rough time/cost estimate

Writing 3-5 families x 3 rungs (12-20 variants): an afternoon of careful
authoring (this is the part most likely to need iteration — getting a
prudential disaster to read as severity-9 without smuggling in
another-party harm is a real writing challenge, not a mechanical task).
Curation pass: minutes, trivial API cost. Second-reviewer cross-check on any
flat result: an hour of manual ChatGPT-conversation labor, matching the
Workstream B precedent. Total: plausible as a single day's work, matching
the "probably for tomorrow" framing this plan was scoped for.
