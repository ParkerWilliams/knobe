# Docs index

Four subfolders, organized by what question each doc answers, not by date.
When adding a new doc, put it in the subfolder whose question it answers;
if none fit, that's a sign a new subfolder is needed rather than a reason
to drop it in the top level.

## `rq1_findings/` — what did RQ1 actually find, and how sure are we?

The results themselves, and the honest accounting of how much to trust them.

- **`RQ1_STATISTICAL_METHODS_v1.1.md`** — the methodology and full
  per-contrast result tables. The most-cited doc in the repo; start here
  for "what's the actual number for X."
- **`RQ1_MECHANISM_ANALYSIS_v1.1.md`** — the research interpretation layered
  on top of the methods doc: what the numbers mean for the Knobe-effect
  question.
- **`MAIN_RUN_WRITEUP_v1.0.md`** / **`MAIN_RUN_WRITEUP_v1.1.md`** — the
  release writeups in order. v1.0 contains a retracted measurement
  artifact (a Mistral tokenizer bug); v1.1 is the corrected version.
- **`OUTSTANDING_STATISTICAL_ANALYSIS.md`** — status checklist against the
  original 12-item technical review: what got fixed, what's still open.
- **`KNOBE_EFFECT_STATUS.md`** — the narrower question "is the classic
  effect present at all, and where," stripped of the full RQ1a-d
  decomposition.
- **`RAIMONDI_REPLICATION_GAPS.md`** — how this project's results compare
  to Raimondi et al. (arXiv:2510.12229), the paper this project extends,
  including where they don't line up and why.

## `severity_confound/` — the RQ1a severity/moral-status entanglement

One specific, still-partly-open problem: RQ1a's moral-vs-nonmoral
comparison is confounded with severity in this release's stimuli, and
whether that's fixable by better wording or needs new stimuli.

- **`SEVERITY_MORALIZATION_BACKGROUND.md`** — the psychology-literature
  case for why severity and moral status might not be separable at all,
  for this project's harm-based taxonomy specifically.
- **`SEVERITY_PILOT_PLAN.md`** — the two-phase plan to test that
  empirically (reworded curation question, then an escalated-severity
  stimulus pilot). See also `analysis/ngo_prudential_pilot/` for a
  differently-scoped attempt at the same underlying question, built
  directly on Raimondi's own stimuli instead of this project's taxonomy.

## `moral_foundations_extension/` — does the effect generalize beyond harm?

A distinct question from the severity confound above: even a clean
"moral-specific" finding only covers *harm-structured* moral content,
since that's all Ngo's/Raimondi's paradigm and this project's own "moral"
category ever test. This folder holds the plan to check whether the
asymmetry holds for moral wrongness grounded in loyalty, authority,
fairness, or purity instead of harm.

- **`MORAL_FOUNDATIONS_PILOT_PLAN.md`** — design doc (not yet built):
  vignette structure, storyline sourcing from Ngo's set, curation
  manipulation-check wording, and analysis plan.

## `v1_1_release_process/` — how the v1.1 release got built

Process docs from curating and freezing the v1.1 stimulus release, kept
for provenance rather than day-to-day reference now that the release is
frozen.

- **`DECISIONS_FOR_HUMANS.md`** — scientific/modeling judgment calls made
  by following the spec's letter, flagged for a second look.
- **`V1_1_REVISION_PLAN.md`** — the reasoning behind the v1.1 moral/nonmoral
  labeling and RQ1a design changes.
- **`NEXT_RUN_ACTION_ITEMS.md`** — the practical problem/fix punch list
  version of the revision plan.
- **`V1_1_CURATION_DECISION_TREES.md`** — branch-by-branch judgment calls
  for the curation-gate freeze decision.
- **`V1_1_WORKFLOW.md`** — the fine-grained execution plan tying the above
  together (who does what, in what order).

## `power_planning/`

- **`g1_power_report/`** — the pilot (G1) power simulation report and
  curves feeding the sample-size decisions for the v1.1 release.
