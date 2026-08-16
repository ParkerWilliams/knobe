# From here to new results: who does what, in what order

Fine-grained execution plan. `V1_1_REVISION_PLAN.md` has the reasoning,
`NEXT_RUN_ACTION_ITEMS.md` has the problem/fix punch list,
`V1_1_CURATION_DECISION_TREES.md` has the branch-by-branch logic for the
Phase 2 gate — this is the "who does which step, in what order" view, with
the decisions folded in at the point they apply.

**[YOU]** = doable with no API key and no H200 access.
**[PARKER]** = needs his API key and/or H200 access, or a working local
`knobe` install (confirmed: you don't have one).

## Decisions already made (nothing left to resolve here)

- **`set_id`**: runs as a sensitivity fit (`--set-sensitivity`), not primary.
  Promotion to primary is a later decision, gated on the estimate-stability
  check against real data — not decided now.
- **Type-1 curation-question reword**: reverted. `constants.py`'s
  `moral_relevance` question is back to its original wording. The upcoming
  curation run tests only the Type-2 content fix — one variable, clean
  attribution. The reworded question (and its own validation protocol) is
  a separate, later cycle — see "Separate track" at the bottom.
- **Self-report question wording**: first-person, matched anchor labels:
  *"How emotionally striking do you find this scenario, on a scale from 0
  (not at all emotionally striking) to 10 (extremely emotionally striking)?"*
- **Self-report question ordering**: no concern, resolved — the pipeline
  elicits every question type as an independent, single-turn completion
  with the scenario re-embedded fresh each time (`render.py`); there is no
  shared context between question types for an order effect to act on,
  regardless of where the new question sits in the job manifest.

## Phase 1 — No API key needed, doable by you right now

1. **[YOU]** Say the word and I'll draft the self-report question code diff
   (the `QuestionType` literal in `schemas.py`/`jobs.py`, the new entry in
   `constants.MAIN_QUESTION_COLUMNS` with the wording above, the two
   `cli.py` `choices=(...)` tuples) as an unapplied, reviewable patch.
   Flagged as untested against Parker's real pipeline either way.
2. **[YOU]** Commit and push everything currently sitting uncommitted.
3. **[YOU]** Send Parker: `NEXT_RUN_ACTION_ITEMS.md`, `V1_1_REVISION_PLAN.md`,
   `V1_1_CURATION_DECISION_TREES.md`, this file, and point him at
   `data/authoring/v1.1_candidate/`.

## Phase 2 — Parker (local CLI steps first, then his API key for curation)

1. `knobe generate approve <24 family_ids> --matrix
   data/authoring/v1.1_candidate/ALL_DOMAINS_master_matrix_v1.1_candidate.csv`
   — pure local CSV flip, no API.
2. `knobe assemble
   data/authoring/v1.1_candidate/ALL_DOMAINS_master_matrix_v1.1_candidate.csv
   <out_prefix>` — produces `vignettes.csv` (S2), pure local, no API.
3. `knobe curate run <vignettes.csv> --reviewer-model <sonnet-string> --mock`
   — zero-cost dry run, catches invocation/schema errors before spending a
   real API call.
4. Run the real curation pass: `knobe curate run <vignettes.csv>
   --reviewer-model <sonnet-string> --out curated_v1.1.csv --raw
   curated_v1.1_raw.jsonl` — the whole 420-variant set (cheap, ~1,680 calls,
   minutes not hours; don't scope to just the 24, the reconciliation risk
   isn't worth the small savings). **First step needing his API key.**
5. **Work `curated_v1.1.csv` through `V1_1_CURATION_DECISION_TREES.md`
   Trees 1, 2, 4, and 5** (Tree 3 doesn't apply to this run — reverted).
   That gives, per family: clean pass / accept-as-limitation / one targeted
   revision — and an overall go/no-go on freezing.
6. `knobe curate review --curated curated_v1.1.csv --accept-unflagged` (or
   manual review for anything the trees routed to "targeted revision").

## Phase 3 — Parker, needs his dev environment (schema + job-spec, not yet H200)

Items 1-3 don't need to wait for Phase 2 to finish — job-generation work is
independent of whether the vignette content passed curation. Only item 4
(the freeze) needs Phase 2 fully resolved.

1. Review/merge the self-report question diff (if drafted in Phase 1) —
   test end-to-end against his real job-generation code. Check for
   hardcoded "3 questions per variant" assumptions elsewhere (job-count
   math, validation checks) before trusting it.
2. Confirm surprisal is feasible: does his elicitation setup retain
   logprobs already, or does that need enabling?
3. Decide + implement Workstream 3:
   - Unify scoring across checkpoints (prompt-format fix, or EV-score
     every checkpoint uniformly).
   - Increase response-level N for the RQ1b blame/praise elicitation only.
4. Re-freeze: `knobe assemble <matrix> <out_prefix> --release v1.1
   --curated curated_v1.1.csv --changelog "..." --gates-passed G0,G1,...`

## Phase 4 — Parker, needs H200

1. Kick off the full elicitation run against the frozen v1.1 release.
2. **Parallel, right now, doesn't need to wait for anything above**: run
   `knobe analyze --set-sensitivity` against v1.0's *existing* results.
   Costs nothing, tells you now whether `var_family` actually shrinks with
   `set_id` — an early read before spending any v1.1 compute.

## Phase 5 — Either of you, once v1.1 results land

1. `knobe analyze ... --set-sensitivity --exclude-flagged` on the new results.
2. Validity check: does `sign_c:vt_c`'s point estimate stay stable when
   `set_id` is added (only the SE should shrink)? If it moves, don't trust it.
3. Confound check: does self-reported affect correlate with `sign` itself?
   Check before trusting any affect×sign estimate.
4. De-attenuated RQ1b fit.
5. v1.0-vs-v1.1 stability check on the untouched RQs (base replication,
   Mistral reversal, typicality×sign) before treating v1.1 as superseding
   v1.0 outright.
6. Write up — state the RQ1c-evocativeness reframing (manipulated contrast
   → observational correlation) explicitly, not implied.

## Separate track — not on the critical path, no urgency

- **Type-1 curation-question reword** — its own validation cycle, whenever:
  test against the 11 target MG families + a clean-MB sample + a
  clean-nonmoral sample, per `V1_1_CURATION_DECISION_TREES.md` Tree 3.
  Adopt only if all three checks clear; otherwise document the MG
  reviewer-instrument asymmetry as an accepted limitation.
- **Item-within-family power resim** — needs Parker's pilot raw
  response-level data (not in this repo) plus new simulation-design code.
  Do before growing family count in a *future* release, not this one.
