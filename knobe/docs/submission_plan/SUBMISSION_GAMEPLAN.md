# Submission Gameplan (2026-09-13)

**Status:** working plan, revised as claims clear or fail their gates. This
document answers "what do we submit, where, and in what order" — it does not
restate results. For the numbers themselves see
`docs/rq1_findings/RQ1_STATISTICAL_METHODS_v1.1.md` (main run) and
`docs/rq1_findings/ALIGNMENT_DISCUSSION_ngo_pilots.md` (both pilots); point
numbers below refer to that draft's numbering.

**Provenance for the audits this plan's rankings turn on:**
`analysis/ngo_extensions/measurement_selection_audit.py`, commit `395a9ed`
(`outputs/measurement_audit.csv`, `outputs/selection_attrition.csv`);
`analyze_sign_wcb.py --score parsed`, commit `6c73ab6`
(`outputs/sign_wcb*_parsed.csv`); `blame_praise_swing.py`, commit `244db46`
(`outputs/blame_praise_swing.csv`, `outputs/question_cell_means.csv`).

**2026-09-13 — §5 items 1, 2, 2a and 2b are done, and they changed the
paper.** The parsed-rating substitution flipped 14 of 30 q_intentionality
cells and 0 of 30 q_praise cells. Two consequences, in order of importance:

- **The blame/praise claims are untouched and are now the whole spine.**
  Every finetuned blame and praise cell holds under both scorings.
- **The pretrained→finetuned contrast survived and got stronger.** Now
  formally tested (`1bc6e12`) rather than read off six split-sample fits:
  8/12 cells significant and 11/12 positive under parsed, with gemma's
  interaction 2–4x larger than under EV. Promoted to Rank 2b.
- **The domain-generality claims shrank rather than improved.** An earlier pass
  of this note claimed the asymmetry is "domain-general in every family";
  that was wrong, and §5 item 2b is what caught it. Under parsed scoring
  **llama-finetuned shows no significant intentionality asymmetry in any arm
  of either pilot** (0/4 nonmoral, 1/6 MF), so there is no effect for a
  domain interaction to generalize across. Of the remaining two, only gemma's
  nulls are informative once equivalence-bounded; mistral's are underpowered.
  Domain-generality is a one-family result with a second family consistent
  but undetermined.

See `ALIGNMENT_DISCUSSION_ngo_pilots.md`'s correction note for what all this
supersedes in the draft, and `CLAIMS.md` for the current claim set — §2 of
this doc no longer duplicates it.

**Two priorities changed after the fact, both recorded rather than quietly
edited.** The finetuning contrast was the lowest-ranked claim this morning
and is now C2/Tier A, because it was never actually tested and survived
testing. The severity curation pass was briefly called the highest-value
remaining task and is now demoted (§5 item 8), because the concern was
imported from the main run's taxonomy and the discriminating data was already
in hand.

---

## 1. The framing decision

**The pilots are the paper. The main run is the methods backbone.**

The v1.1 main run's headline RQ1a comparison is confounded by a stimulus
manipulation failure that no amount of modeling fixes (MB exceeds NMB on
severity in 21 of 21 storylines, mean gap 5.42 —
`RQ1_MECHANISM_ANALYSIS_v1.1.md` §1). The pilots are built on Ngo's own
storylines, carry the genuinely novel multi-construct finding, and sidestep
that confound. The main run contributes the typicality reversal (RQ1c), the
wild-cluster-bootstrap machinery, and the measurement lesson.

There is currently no manuscript of any kind in this repo. The distance to a
submission is mostly writing, not analysis — which is why the worklist in §5
puts drafting in parallel with the one analysis task that gates everything.

---

## 2. Claim inventory → see `CLAIMS.md`

**Moved 2026-09-13.** This section used to carry a ranked claim inventory,
and `CLAIMS.md` now carries the same claims tiered by confidence. Two
overlapping ranking schemes is worse than one, so the inventory lives there
and this doc keeps only what it is uniquely for: the framing decision, the
evidence base (§3), venue targets (§4), the worklist (§5), and what is
deferred (§6–§7).

Mapping, for anyone reading this session's commit messages, which use the
old Rank names:

| old name | now | what happened |
|---|---|---|
| Rank 1 (blame-vs-praise) | **C4**, Tier A | Verdict corrected to gemma+llama vs. mistral; `parsed` established as the primary scale |
| Rank 2 (foundation gradient) | **C5**, Tier B | Narrowed to gemma once equivalence-bounded |
| Rank 2b (finetuning) | **C2**, Tier A | Promoted; formally tested for the first time |
| Rank 3 (domain-general) | folded into **C5** | — |
| Rank 4 (construct divergence) | folded into **C3**/**C4** | Point 5's sign-convention error removed one leg |
| old Rank 4 (moral-specificity) | **refuted** | Does not appear in the paper |
| old Rank 5 (finetuning) | → Rank 2b → **C2** | — |
| — | **C1** (measurement) | New; now leads the paper |
| — | **C3** (good-cell localization) | New; Tier A− after the stakes test |


## 3. The two audit findings that set these rankings

Both from `measurement_selection_audit.py` (commit `395a9ed`).

### 3.1 The EV-scoring artifact is question-shaped, not just tuning-shaped

`r(ev_rating, parsed_rating)` on parse_ok rows, nonmoral pilot:

| model | q_blame | q_intentionality | q_praise |
|---|---:|---:|---:|
| gemma-2-9b-instruct | **.823** | **.180** | **.761** |
| llama-3.1-8b-instruct | **.656** | **.146** | **.558** |
| mistral-7b-v0.1-instruct | **.773** | **.421** | **.812** |
| gemma-2-9b-pretrained | .178 | .098 | .227 |
| llama-3.1-8b-pretrained | .026 | .138 | .176 |
| mistral-7b-v0.1-pretrained | .039 | .070 | .074 |

MF pilot (q_intentionality only): gemma-instruct .523, llama-instruct .130,
mistral-instruct .530; all three pretrained .059–.094.

The main run only ever framed this artifact as a pretrained/finetuned split,
because it had no reason to look at the question axis. The pilots collect
three question types on identical items, which makes that axis checkable for
the first time. Two consequences:

- Blame and praise ask for a number and get one. Those cells are the
  best-measured in the project, which is what makes Rank 1 safe.
- Finetuned intentionality is measured at or below the pretrained cells where
  the artifact struck. Every intentionality-based claim — Ranks 2, 3, 4, 5 —
  inherits that.

Not a parse-rate story: gemma-instruct parses intentionality *better* than
blame (58.1% vs. 53.0%) and still lands at .180. The forced-scoring vector
fails to track the intentionality answer even when the model gives one.

### 3.2 The nonmoral pilot lost 65% of its moral-good cell to curation

Both pilots authored balanced designs. Post-curation survival, nonmoral
pilot:

| arm | bad | good |
|---|---:|---:|
| moral | **97.5%** (39/40) | **35.0%** (14/40) |
| nonmoral_procedural | 92.5% | 95.0% |
| nonmoral_prudential | 87.5% | 82.5% |

The MF pilot, which switched to pair-level gating mid-curation for exactly
this reason (2026-08-19 log), came out perfectly balanced in every cell
(30/30, 10/10, 9/9, 8/8, 6/6).

Cause is on record: the curation questions "name only the violation pole, so
good-sign items score near zero... regardless of authoring quality"
(2026-08-19 log). The nonmoral pilot kept per-item selection; the MF pilot
did not.

Consequence: every moral-arm coefficient in the nonmoral pilot compares 39
bad items against 14 items selected for scoring highest on moral loadedness.
**This is a third candidate explanation for point 4a's elevated moral-good
blame floor** (6.56–7.05 vs. nonmoral-good 3.98–4.64), alongside severity and
indifference-tracking, and it is the most mechanical of the three. 4a cannot
be cut from the writeup — cutting it removes the acknowledgment, not the
problem.

---

## 4. Venue: TMLR (decided 2026-09-13)

**Decided, not a shortlist.** Drafting targets TMLR.

Reasons, in order of weight:

1. **No human baseline, by explicit scope call.** `V1_1_REVISION_PLAN.md`:
   "This project's aim is to locate and decompose a known human effect inside
   LLMs, not to re-establish the human effect on a new stimulus set." C3, C4
   and C6 are all framed against *published* human results, on modified Ngo
   items rather than the originals. At CogSci or Cognition that is a
   first-round objection; at TMLR it is unremarkable.
2. **C1 leads naturally.** The strongest contribution is a measurement
   finding about how LLM Likert responses are scored — an ML/NLP audience
   question.
3. **Cross-model heterogeneity reads as a finding**, not as an inconclusive
   result. TMLR reviews on whether claims match evidence rather than on
   novelty or a unified story, which is exactly this project's shape.
4. **No deadline pressure**, so the provenance files and any v2 elicitation
   can land mid-review rather than gating submission.
5. The mechanistic arm (§6) extends naturally in the same venue later.

Not chosen: *ACL via ARR (same shape, but needs a tighter single story and
risks heterogeneity reading as inconclusive); AIES/FAccT (a good fit for a
C4-led audit framing, worth revisiting for a second paper); CogSci (blocked
by reason 1).

**Drafting decisions that follow:** C1 leads. C3 is drafted now with its
attrition confound stated in-line and explicit placeholders for the analysis
the curation provenance files will enable — the files are being chased in
parallel, so this is a fill-in rather than a rewrite. Manuscript starts in
markdown at `paper/DRAFT.md`; conversion to the TMLR LaTeX template is a
later mechanical step.

## 5. Worklist, in order

### Closed 2026-09-13

All seven were measurement or inference gates. Between them they settled
which claims survive scoring, which survive multiplicity, and which of C3's
rival readings survives test.

| item | commit | what it decided |
|---|---|---|
| Parsed-rating substitution, both pilots, all cells | `6c73ab6` | 14/30 intentionality flip, 0/30 praise. Refuted moral-specificity; produced C1 |
| Praise scale-comparability | `244db46` | `parsed` is the primary scale for cross-question magnitude; C4's verdict corrected |
| Foundation-gradient F under parsed | `70f1a34` | Two of three pretrained heterogeneity results were artifact |
| Equivalence bounds | `03b8f1b` | C5 narrows to gemma; caught a domain-generality overstatement |
| `required_sets()` | `0dc641b` | mistral needs G=75 / G=48 — reachable, not hopeless |
| Formal `sign_c × tuning_c` | `1bc6e12` | C2: 8/12 significant, 11/12 positive. The test point 1 never ran |
| Holm on the parsed tables | `20e22e2` | 17/132 flip; 17 of C3/C4's 18 load-bearing cells survive |
| Stakes gradient (prudential vs procedural) | `710b4c3` | C3's stakes rival reading ruled out for praise, constrained for blame |

### Do next

1. **Draft C1 → C2 → C4 → C3.** That is the whole empirical spine and every
   gate on it is closed. C1 leads: it converts the paper's biggest liability
   into its headline contribution and licenses every number after it.

2. **Recover the four curation provenance files** (`moral_relevance_raw.jsonl`
   + `selection_report.md` per pilot). Now C3's *only* remaining open
   confound, and the sole thing standing between C3 and Tier A. They are the
   only way to compare the 26 dropped moral-good items against the 14 that
   survived. Blocked on a person, so send the request before drafting rather
   than after.

3. **Holm-correct the tuning contrast.** `tuning_contrast_wcb_parsed.csv`
   sits outside `holm_correct_pilots.py`'s scope and is the one C2 table with
   no multiplicity correction. The grouping is a judgment call this repo has
   flagged as needing sign-off, which is why it was left rather than guessed.
   gemma's cells survive any correction; llama's MF harm cell (p=.0305) does
   not.

### Do in parallel

4. **Mistral revision / chat-template check** — gates only the Raimondi
   comparison, but it is an afternoon and it turns "we don't replicate" into
   either a methodological explanation or a real finding.

5. **Point 4a indifference-clause ablation** — vary "did not care at all
   about X" (present / absent / active concern) holding outcome and domain
   fixed. **Upgraded by `710b4c3`:** with the stakes reading largely ruled
   out, indifference-tracking is now the leading explanation for C3 rather
   than one of three, so an ablation would confirm a live hypothesis instead
   of adjudicating a three-way tie. Small elicitation on existing items.

6. **q_blame / q_praise for the MF pilot** — re-elicitation on already-curated
   items. Would extend C4 (the strongest claim) across foundations and merge
   the two pilots into one result rather than two.

### Parallel track — human replication (new 2026-09-13)

Decided today, scoped and costed in `docs/human_study/PROTOCOL.md`. Two arms
as one study: blame on the 240 authored nonmoral items (a direct human test
of C3), and intentionality on the 152 authored foundation items (standalone —
whether the Knobe effect extends past harm has never been tested in humans).
~131 participants, ~$540 plus an ~$80 pilot.

**Does not gate the TMLR submission.** Paper one is model-only and its
framing is sound without human data. This is paper two, and it makes paper
one stronger if it lands during review.

Two payoffs beyond the obvious one:

- Running the **authored** sets rather than the post-curation subsets means
  human ratings on the 26 dropped moral-good items. That substitutes for the
  missing curation provenance files and converts C3's last open confound from
  a person-dependent gate into one we control.
- The foundations arm is a moral-psychology contribution independent of any
  LLM result, which opens venues the model-only work cannot reach.

**Blocking step, and it is irreversible if skipped:** an IRB determination.
IRBs cannot approve research retroactively, and the project's affiliation
status is genuinely unclear (side project, external collaborator), so the
determination request goes out before anything else in this track. Everything
else — instrument build, block generator, pilot design — proceeds in
parallel; only collection waits.

### Before submission, not before drafting

7. **Multiplicity exposure.** Partly addressed — the parsed tables are now
   Holm-corrected (`20e22e2`) and C3/C4 survive. What remains is that C2–C4
   are still exploratory: the clean fix is a preregistered confirmatory run on
   fresh items, and the ICC analysis (design effects 6–160×) says more
   clusters, not more samples, is what buys power.

### Demoted

8. ~~**Severity curation pass over both pilots**~~ — **demoted 2026-09-13,
   was "do if bandwidth allows."** The reasoning that put it here was
   imported from the main run, where severity was an authoring accident
   specific to *that* taxonomy (MB written around genuine harm, NMB written
   low-stakes, nothing enforcing parity). The pilots don't inherit that
   taxonomy. The version that does transfer is a rival *interpretation* of
   C3 — stakes rather than moral domain — and `710b4c3` tested it with data
   already collected: no stakes gradient for praise at all, and for blame a
   gradient 2.2–4.4× smaller than the moral jump it would have to explain.
   What a stakes rating would now add is turning C3's blame argument from
   ordinal to quantitative. Worth doing eventually; not a gate, and not the
   highest-value task it was briefly called.


## 6. Deliberately deferred

- **The mechanistic arm.** `src/knobe/mech/` is ~145 KB of built, tested code
  — activation caching, pretrained→finetuned layer patching, per-layer probes,
  RQ2–RQ4 decomposition — that has never been run on real data (no `acts/`,
  `patch/`, or `mech_report/` anywhere under `results/`). It is the novelty
  ceiling, since Raimondi's paper is itself a mech-interp paper. It is also
  the wrong next step: `pytest -m gpu` has never run against real backends,
  the nnsight slice-0 patch path is flagged as shaky, and the lm-eval
  capability check is still a stub raising `NotImplementedError`. Paper two,
  or after the behavioral paper is submitted.
- **Random-slope ordinal refit** (`OUTSTANDING` item 3). Compute-bound.
  "Ordinal and LMM disagree here" is a respectable limitation to report.
- **RQ1b joint latent-variable model.** SIMEX already ruled out the
  measurement-error explanation; this resolves one cell of one contrast in
  the run that is becoming the backbone rather than the headline.
- **Both severity pilot phases** (`SEVERITY_PILOT_PLAN.md`). That plan was
  scoped to the v1.1 main run's taxonomy, where severity was a genuine
  stimulus-design failure. It does not transfer to the Ngo extensions, which
  are this project's focus now — see §5 item 8. Phase 0's reworded-question
  check remains relevant to RQ1a specifically, and RQ1a is not going in the
  paper.
- **Promoting random slopes into the pipeline** (`OUTSTANDING` item 7).
  Highest-leverage *pipeline* change on the list, and irrelevant to this
  submission.

---

## 7. Open provenance gaps

- The four curation files in item 5. Until they arrive, the 196/240 and
  126/152 selected-item sets are reconstructed by inference — verified against
  logged counts and bit-identical WCB reproduction, but not against the actual
  per-item scores, and with no way to check why any specific item was
  excluded.
- `analyze_sign_wcb.py`'s `--question` flag is documented only in the script
  docstring and `ALIGNMENT_DISCUSSION_ngo_pilots.md`, not in either pilot's
  README or HANDOFF.
