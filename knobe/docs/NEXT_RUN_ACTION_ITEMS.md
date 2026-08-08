# Next run: what's wrong and what to fix

Practical version of `V1_1_REVISION_PLAN.md` — problem + action item, no
discussion. Full reasoning and supporting data are in that doc and in
`data/curation/FLAGGED_VARIABLES_README.md` if you want it; this is just the
punch list.

## Do this, in this order

**Don't run the full elicitation job yet — it's not ready, and running now
risks a costly redo** (any content change after the fact invalidates the
manifest hash, forcing a full re-run of the 189k-completion job). What's
actually left before it's worth kicking off:

1. Approve the 24 already-drafted, already-validated content revisions —
   one local command, no API: `knobe generate approve <family_ids> --matrix
   data/authoring/v1.1_candidate/ALL_DOMAINS_master_matrix_v1.1_candidate.csv`
   (family_id list and validation results in that same directory). No
   further review needed — content's been drafted, human-reviewed, and
   independently cross-model validated (§1a below).
2. Apply that matrix to the real pipeline and re-run S1/S2 assembly (mechanical).
3. Re-run real S3 curation on the revised batch (needs your API access) —
   confirms the fix on the pipeline's own terms, not just the ChatGPT
   cross-check. If it disagrees with ChatGPT on any family, resolve that
   before moving on.
4. Decide the self-report question's name/wording and implement it (§2
   below has the exact touchpoints — it's a contained schema change, not a
   redesign) — do this *before* the freeze, since it changes the job manifest.
5. Re-freeze the v1.1 manifest, then run elicitation.

Everything below this point is reference for *why*, plus the few items that
are still genuinely open decisions rather than instructions.

**Sizing note up front:** items 1 and 2 each split into (a) a quick rule/prompt
edit, and (b) actually producing revised content — generate → human review →
re-curate. (b) is its own multi-step process, not a same-session adjustment,
and shouldn't be rushed (rushing it reintroduces the exact failure mode
flagged below — editing-and-resubmitting until a check passes). If tonight's
run needs to happen before (b) is done, run the pipeline/engineering fixes
(items 3-5) on the existing v1.0 vignette set and treat the content rewrite
as a separate follow-up before the next freeze, rather than compressing it
into this session.

## Before writing/regenerating any vignettes

### 1. Moral/nonmoral category bleed — 57/420 variants (13.6%), but it's two different problems

Pulled full context on all 31 flagged families. They split cleanly into two
groups that need opposite treatment — don't apply one fix to both.

**1a. Type 2 (20 families) — NMB/NMG/NEU reading too moral (score too high).**
**Problem:** the shared goal for a family-set is sometimes itself
moral-stakes (e.g. "restructure nurse staffing ratios to reduce labor
costs"), so the NMB/NMG sibling reads as moral even though its outcome
(decor, cover design, odor) was meant to be a nonmoral side-channel. Often
made worse because the *affected entity* is the same stakes-bearing
population as the real harm (patients, residents, borrowers) even when the
described outcome itself is cosmetic.
**Action — ready to run, drafted AND independently validated, not just a
rule to apply by hand:**
- Revised content for all 24 families (19 originally flagged + 5 caught in
  a sibling-consistency review pass) is drafted:
  `data/authoring/v1.1_candidate/moral_relevance_type2_patch.csv` (the diff)
  and `data/authoring/v1.1_candidate/ALL_DOMAINS_master_matrix_v1.1_candidate.csv`
  (the patch already applied — ran clean, 105 rows preserved;
  `human_approved` correctly reset to `False` on every patched row, since
  the old approval was for the old text, pending Parker's actual review).
  `agent`/`goal`/`common_action`/`uncommon_action` are untouched in every
  case — only `affected_entity`/`outcome_verb`/`low_evocative_outcome`/
  `high_evocative_outcome` changed, and the fix strategy throughout is
  moving the outcome off the domain's real-stakes population onto an
  internal/back-office one (staff, internal tooling) instead.
- **Independently validated, not just self-assessed**: all 24 revised
  families run through ChatGPT (browser, manual, fresh conversation per
  family, exact `CURATION_PROMPT_TEMPLATE` format) — scores ranged 0-3
  (mean 1.62), all well under the ≤4 nonmoral threshold, zero disagreements.
  Raw scores: `data/authoring/v1.1_candidate/chatgpt_validation_results.csv`.
  This satisfies the cross-model validation step (Workstream B step 6 in
  `V1_1_REVISION_PLAN.md`) without needing API access.
- `FOOD-NEU-02` was **not** auto-patched — only one of its four variants was
  flagged (mr=6, just over the mr≤4 threshold), and the family's existing
  concept already matches the ideal NEU template closely (internal
  file-naming format). Recommend a light reword of just that one variant's
  text and a re-check, not a structural rewrite — this one may be reviewer
  noise rather than a real construction problem.
- Run S1/S2 assembly on the candidate matrix, then S3 curation, to get
  fresh scenario text and moral_relevance ratings for these 20 families
  before deciding they're fixed.
- Same guardrail generalization is worth making in `GENERATION_SYSTEM_PROMPT`
  (`src/knobe/constants.py`) for future generation, independent of this
  patch: NMB/NMG outcomes should be as dimensionally independent from the
  shared goal's stakes as NEU already has to be.

**1b. Type 1 (11 families) — MG reading too *nonmoral* (score too low).**
Families: `ANIM-MG-02`, `ENV-MG-01/02/03`, `FIN-MG-01/02`, `HC-MG-01`,
`PRIV-MG-01`, `PS-MG-01/02`, `WORK-MG-02`.
**Problem — different from 1a, do NOT rewrite this content.** These
describe unambiguous moral goods (reducing patient complications from
understaffing, reducing choking/fire risk, reducing loan default, improving
water quality) — direct positive mirrors of harms that would score 8-9 if
flipped to bad. MB's own scores are tight and clean (mean 8.9, stdev 0.59);
MG's are loose (mean 6.47, stdev 2.31) on comparably-staked content. That
pattern points at the **reviewer instrument** under-recognizing benefit
framing as "moral" relative to harm framing, not bad vignette content.
Rewriting these to sound more "obviously moral" would just optimize the
text for the judge — the exact failure mode being avoided elsewhere in this
doc.
**Sharpest evidence for this being an instrument problem, not a content
problem:** `PS-MB-02-D` and `PS-MG-02` are the same storyline (identical
agent, identical "did not care at all" framing, identical setup) differing
only in outcome sign — fire risk increased vs. decreased. `PS-MB-02-D`
scored 10; `PS-MG-02` scored 2. Same content shape, same author, opposite
scores purely from valence.

**Decided: not part of this release.** A reworded question was drafted and
briefly landed in code, but was reverted — `src/knobe/constants.py`'s
`moral_relevance` question is back to its original wording, so the
upcoming curation run tests only the Type-2 content fix, one variable at a
time. Reasoning: fixing two things in one curation pass would confound
attribution if anything looked off, and the reworded question's own
validation protocol (below) had never actually been run.

Candidate wording, parked for its own separate cycle:
> "Is this scenario about a moral matter -- including producing a moral benefit, preventing harm, or protecting someone's wellbeing/rights -- or is it purely a matter of practicality/aesthetics/etiquette with no bearing on anyone's welfare? (0=purely practical/aesthetic/etiquette, 10=purely moral, weighing benefits and harms equally)"

**When this gets picked up — Parker, requires API access:** re-run
curation with the reworded question against (a) these 11 flagged families
— should move to ≥6, (b) a random sample of already-clean MB families —
should stay ≥6, not regress, (c) a random sample of already-clean
NMB/NMG/NEU families — should stay ≤4, not falsely inflate. If (b) or (c)
breaks, don't adopt it — treat Type 1 as a documented instrument
limitation instead (same as v1.0 already did for evocativeness), not
something to force-fix. Decision trees for this check:
`V1_1_CURATION_DECISION_TREES.md` Tree 3.

**After curation runs on the revised batch — decision rule:**
- Family clears its threshold: use the revised version in v1.1.
- Family still fails after this one rewrite pass: don't iterate again
  immediately (that's the pass-chasing trap). Flag it back for a second
  look, and don't let a handful of stragglers block the rest of the release
  — document as a residual limitation, same as v1.0 did.

### 2. Evocativeness manipulation doesn't register — 173/210 pairs (82%), 36 reversed
**Problem:** construct mismatch, not a wording problem. `high_evocative_outcome`
was written for concreteness/specificity; the curation question measures
emotional vividness. Two things we tried that do **not** fix it: an
external emotion-word lexicon (doesn't reflect what the subject models find
salient) and personal-report framing ("residents said..." vs. "a survey
found...") — tested directly against the data, no effect on the gap (0.51
vs. 0.45 mean gap with/without it).
**Quick part (do tonight):** decide the operationalization —
- **Option A:** add a self-report affect-salience question to elicitation
  ("how emotionally striking is this scenario, 0-10?"), asked of the
  subject models themselves, per variant. Requires adding a field to the
  elicitation job spec before the run.
- **Option B:** use token-level surprisal/perplexity of the subject model
  on the scenario text (needs logprobs retained) as a model-native vividness
  proxy — no new elicitation question needed, just retain logprobs you may
  already be computing.
**Not-quick part (separate task, own timeline):**
- Whichever option is chosen, produce revised `high_evocative_outcome` text
  (or a redefined curation question) dataset-wide — MB/NEU too, not just the
  ~30 families from item 1 — otherwise evocativeness's strength differs by
  valence for no reason other than revision history. Same generate → review
  → re-curate cycle as item 1.
- List of current failures: `data/curation/vividness_gap_flagged.csv`.

## Pipeline fixes (independent of vignette content — can happen in parallel)

### 3. Curation flags exist but aren't used by the analysis code
**Problem:** `ingest.py` only filters on `accepted` (True/False). It never
looks at `individual_flags`/`pair_flag`. Since `accepted=True` for all 420
v1.0 variants, every flagged item — including the 57 in item 1 and the 173
in item 2 — was fed into RQ1a/RQ1c exactly like a clean item. This is why
RQ1a came back null/inconsistent and RQ1c-evocativeness came back
incoherent.
**Action:** once items 1 and 2 are rewritten, re-run curation on the
revised batch so `accepted`/flags reflect the new content, then re-freeze
before elicitation. (This item is resolved by fixing 1 and 2, not by
separate code — flagging it so it's clear *why* 1 and 2 matter, not just
that they're cosmetic.)

### 4. Inconsistent scoring method across checkpoints
**Problem:** 5 of 6 checkpoints fall back to EV-over-logprobs because
free-text parse rate is under 95% (as low as 25% for llama-pretrained);
mistral-instruct alone uses parsed ratings (98%). Any cross-model
comparison — including the Mistral reversal — is currently comparing models
measured two different ways.
**Action:** fix the elicitation prompt format to raise parse rates
uniformly, or make an explicit decision to EV-score every checkpoint the
same way. Do this before trusting any cross-model claim in a writeup.

### 5. RQ1b (blame/praise) predictor is noisy
**Problem:** item-level blame/praise means used as the regressor are noisy
point estimates (errors-in-variables), attenuating the slope. Same root
cause as the mistral-log — measurement noise, not effect absence.
**Action:** increase response-level N specifically for the blame/praise
elicitation (more completions per existing item, not more families). No
new stimuli needed.

## Analysis-side fixes (run after results come back — don't block the elicitation run)

### 6. RQ1a needs a blocking model, not just a label fix
**Problem:** `sign` and `valence_type` are both fixed per family — the
interaction is a fully between-family contrast that eats the entire
`var_family` variance component as noise (58% of total variance for
gemma-instruct). Power sim shows this doesn't reach 80% even at 480
families. Label cleanup (item 1) reduces bias but does not fix this.
**Action:** add `set_id` (strip the valence token off `family_id` — e.g.
`ENV-MB-01` and `ENV-MG-01` share `set_id=ENV-01`) as a random effect
alongside `family` in the RQ1a fit. The five valence-siblings share a
storyline by construction; this recovers that matching. Check after
implementing: the `sign×valence_type` point estimate should not move when
`set_id` is added — only its SE should shrink. If the estimate moves,
`set_id` is absorbing the effect, not de-noising it.

### 7. Power targets are currently optimistic
**Problem:** the G1 power simulation only models family + residual
variance, no item-within-family term, and says so itself.
**Action:** re-run the power sim with an item-level variance term added
before setting any new family-count target. Do this before deciding
whether/how much to grow past 105 families.

## Already fixed — no action needed
- `vignettes_curated.json` had `accepted="False"` hardcoded for all 420
  rows (export bug, unrelated to any real decision). Fixed by
  cross-referencing `curated.csv`. No exporter script exists in the tracked
  codebase — if this file ever gets regenerated from scratch, check the
  same bug doesn't recur.
- The "36 reversed pairs" (writeup) vs. "27/51 families" (independent
  recompute) numbers are reconciled — pair-level vs. family-level counting
  of the same data, not a discrepancy.
- Confirmed: flagged vignettes were **not** silently excluded from v1.0 —
  all 420 variants, flagged or not, are in the frozen release and in the
  analyzed results (188,381/189,000 rows). This was a documented, dated
  decision (2026-08-04), not an accident.

## Do not do yet
- Don't grow family count past 105 until item 7's resim and item 6's fix
  have actually been tried.
- No human-baseline arm — out of scope by design, not a resource tradeoff.
- Mistral reversal investigation, domain-random-slope handling, more model
  families/sizes, CLMM/proper ordinal mixed model, chat-format robustness,
  formal preregistration — all real, all separate from this run, don't fold
  into it.
