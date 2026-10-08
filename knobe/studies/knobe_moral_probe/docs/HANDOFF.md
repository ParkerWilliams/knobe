# knobe_moral_probe: handoff

Last updated 2026-10-08. Branch `knobe_moral_probe`. Read this first, then
the amendments at the top of `DESIGN.md`.

## Where the study is

| Stage | Status |
|---|---|
| Design (`DESIGN.md`) | Approved, with dated amendments at the top (they win over the body) |
| Pipeline (`kmp/`, 13-task `IMPLEMENTATION_PLAN.md`) | **Done.** Every task spec- and quality-reviewed, final whole-branch review fixed. 311 tests pass. The plan text is historical; module docstrings are current |
| Definitions and review checklist | **Approved by the researcher** 2026-10-01 (decisions A–U resolved) |
| Stimuli authoring (`AUTHORING_PLAN.md`, Tasks 0–22) | **In progress.** Tasks 0–6 done and reviewed (tools, `ngo_verbatim.csv`, README). Task 7 sheet made; waiting on the researcher |
| Screening | Not started. Reviewer pinned: `claude-sonnet-4-6` |
| Pilot | Not started |
| Full run | Not started |

## Next step

**Researcher:** review `stimuli/review/01_nv_all.md` (80 verbatim items),
fill in `stimuli/review/01_nv_all_decisions.csv` (`approved` / `rejected` /
`revise`, reviewer initials, date; a note is required for rejected and
revise), then run from the study folder:

    ../../.venv/bin/python -m tools.review apply --items stimuli/ngo_verbatim.csv --decisions stimuli/review/01_nv_all_decisions.csv

Then the agent resumes `AUTHORING_PLAN.md` at **Task 7 Step 4/5** (parser
fixes for any `revise`, lint, commit the decisions), then Task 8–9.

The tools changed from the plan's code after review (2026-10-08); the
module docstrings and tests are current:
- `review_record.read_decisions` strips cells, accepts an Excel BOM, and
  rejects bad decision values, an empty reviewer and wrong cell counts.
  `text_sha256` hashes a frozen field list.
- `review apply` only takes a `NN_<batch>_decisions.csv` inside the review
  dir, refuses duplicate rows, and refuses to write any status the whole
  review record doesn't back. `sheet` needs an `NN_` batch name and never
  overwrites.
- `lint_stimuli`: adapted Ngo pairs must have identical action sentences
  (one goal); pronoun changes in storyline 10 (pronouns that mean the uncle
  or aunt) need a log row; a log row licenses only its own span; B8 is
  skipped if the verbatim file differs from Ngo's source.

To restart in a new session: "Continue the knobe_moral_probe authoring plan
at Task 7, subagent-driven. Read docs/HANDOFF.md."

## Researcher gates ahead

1. **Task 7:** review the verbatim set (80 items). Points to look at, found
   in the Task 1 review (kept as written, per check B9):
   - item 72 (pair 36, good): the scenario is about a music player, but
     Ngo's question says "tablet"; item 71 says "computer" vs "tablet". The
     effect field feeds the question, so models will be asked about an
     object not in the story.
   - item 17: the effect "harm her neighbor's crops" vs "Susie-Ann's crops".
   - scenario typos: 10, 23, 40 ("his new road" in a trolley story), 46,
     58.
2. **Task 9:** the role-noun table for all 40 storylines (decisions O, P).
3. **Batches 02–07** (nonmoral, 40 items each) and **Task 14** (foundations
   scaffold roster), then **batches 08–14**.
4. **Task 16:** screening dry run and cost go-ahead (CLAUDE.md §4).
5. **Task 18:** first real screening run, ngo_verbatim only. It also confirms
   that Sonnet 4.6 accepts temperature 0 with thinking off.
6. **Task 20:** selection review, and a threshold revisit only if the real
   distribution calls for it (decision F).

## Before the pilot (not needed for authoring or screening)

- **Double-BOS check on the cluster** (Parker). Run
  `tools/check_chat_bos.py`, then the same with `--vllm`. knobe's
  `VllmEngine` renders chat templates as text and vLLM may add a second BOS;
  this could also affect the main run's instruct results.
- `anthropic` is not installed yet; authoring Task 17 adds it as a
  `screen` extra in `pyproject.toml`.
- **Pilot cost:** about 40 items × 6 models, with examples and with
  `--no-examples` (the copying baseline), about 77k rows, about 1–1.5 h at
  15–20 rows/s. Run `kmp.checks --stage pilot --baseline <noex results>`.
- **Full run:** about 85k rows per model, about 7–9.5 h for 6 models. The
  no-examples run is pilot-only; use `kmp.checks --stage full`.
- **Screening cost:** worst case about 6,200 calls, about $3.50.

## Decisions made 2026-10-01 (all recorded)

- Role nouns for every agent; no personal names, no gendered pronouns.
- Ngo pairs minimally adapted (names, pronouns, goal, listed typo fixes),
  plus `ngo_verbatim` as a word-for-word consistency set.
- `scaffold: shared | purpose` for foundations. The primary harm-vs-non-harm
  contrast uses only storylines with both pairs surviving; the rest go into
  a sensitivity analysis.
- Copying is measured against a no-examples run (`COPY_EXCESS_MAX` 0.10,
  proposed, revisit at the pilot). It blocks in the pilot only.
- Reviewer: `claude-sonnet-4-6`. Current-generation models reject
  temperature 0 and disabled thinking.
- DESIGN §9 Llama power numbers corrected from the committed script.
- Authoring decisions M–U (`DEFINITIONS_AND_CHECKLIST.md` §7).

## Conventions

Commit prefix `[knobe_moral_probe]`, no AI attribution trailer. Commit at
each step. The study keeps its own `ANALYSIS_LOG.md`. The branch and the
separate log are approved exceptions to the repo CLAUDE.md §1 and §5. Tests:
`.venv/bin/python -m pytest studies/knobe_moral_probe/tests -q`.
