# Working conventions for Claude Code on this project

This project runs a lot of exploratory statistical analysis (contrast fits,
bootstrap/permutation inference, sensitivity checks, power calculations)
against a frozen results release. Because these results feed a research
writeup, every number needs to be traceable back to the exact script, params,
and commit that produced it — not just handed back in chat. Follow these
conventions on every analysis task, without being asked each time.

## 1. Work directly on main; commits are the record

Single-contributor project — commit directly to `main` rather than opening a
new branch per analysis task. There's no review-before-merge step to protect,
so a branch's isolated diff isn't buying anything a good commit message
doesn't already give: section 2's incremental-commit discipline plus
section 5's analysis log are the audit trail. Each commit and the log line it
produces should be enough on their own to trace any number back to the exact
script, params, and commit that produced it — that's the same traceability
goal the old branch-per-task rule was serving, just without the branch
overhead.

(Earlier work in this repo used a branch-per-task convention — visible in the
commit history as merged branches. That's no longer the policy; don't create
new task branches going forward.)

## 2. Commit incrementally, not in one lump at the end

Commit at each meaningful step, not just once when the task is "done."
Meaningful steps generally look like: adding the core script, adding a
config/param file, adding a summary output table, fixing a bug found
mid-task. Write commit messages that describe what changed and why, and
reference the task spec file that motivated it when one exists, e.g.:

    "Add WCB refit for RQ1a null model, per rq1a_mde_task.md step 1"
    "Add MDE simulation grid over sign_c:vt_c effect sizes"
    "Fix: severity-adjusted spec was reusing baseline residual variance"

## 3. What to commit vs. what to gitignore

**Commit:**
- Analysis scripts and notebooks
- Config/parameter files (grid definitions, seed conventions, model specs)
- Summary output tables (contrast tables, diff CSVs, MDE result tables) —
  anything small enough to review directly and specific enough to be cited
  as a numbered result

**Do not commit (add to .gitignore instead):**
- Raw bootstrap/permutation replicate dumps (thousands of draws per contrast)
- Full simulation intermediate data
- Anything on the order of the full results_all.jsonl scale

These are regeneratable from the committed script + a documented random seed
— don't bloat the repo with data that exists to be reproduced, not stored.
If a task's seeding convention isn't already established, use
`sha256(base_seed, contrast, family, rep_idx)` (or the closest equivalent for
that task), matching the convention already used elsewhere in this codebase,
and note the convention used in the script's docstring.

## 4. Cost-check before expensive runs

Before launching any run involving nested loops of refits (bootstrap x grid
x families, simulation x bootstrap, etc.), estimate the cost of one inner
cell (one bootstrap draw, one simulation rep) and extrapolate to the full
job. Report that estimate and get explicit go-ahead before launching anything
expected to take more than a few minutes of wall-clock time. If the full run
looks too slow, propose a cheaper first pass (fewer draws/reps) to validate
the approach, then a final confirmation run at full precision — don't launch
the expensive version speculatively.

## 5. Analysis log

Append one line per completed analysis run to `results/ANALYSIS_LOG.md`
(create it if it doesn't exist), in this format:

    YYYY-MM-DD | script/command | key params | one-line outcome | commit hash

Example:

    2026-08-14 | wcb_inference.py | B=1999, cluster=set_id | RQ1a fails post-severity in all 3 families | a3f9c1e

This mirrors the provenance convention already used in
`RQ1_STATISTICAL_METHODS_v1.1.md` ("Generated ... from a fresh `knobe
analyze` run [exact command]") — the goal is that any number in a writeup can
be traced back to exactly how it was produced, months later, without asking.

## 6. End-of-session summary

At the end of every session (or before handing control back), list every
file created, modified, or deleted during the session — not just the ones
being presented as the final answer. Explicitly flag anything not yet
committed. Don't let intermediate scratch files go unmentioned just because
they weren't the headline deliverable.

## 7. Reuse existing pipeline code, don't reimplement

Before writing new statistical/analysis code, search the existing codebase
for machinery that already does the relevant fitting/resampling (e.g. the
existing wild cluster bootstrap implementation, the existing mixedlm fitting
helpers). If existing code is being reused, say so explicitly; if it's being
reimplemented instead of reused, state why (e.g. "the existing bootstrap
assumes X, which doesn't hold here, so I wrote a variant that...") rather
than silently duplicating logic. Reimplementing core inference machinery
without flagging it is a correctness risk — it's easy for two slightly
different bootstrap implementations to silently diverge.
