# Final run plan: closing the paper's open gaps (2026-09-28)

One GPU session, plus a few no-GPU tasks, that closes every gap between the
paper's claims and its evidence that a TMLR reviewer is likely to raise.
Scope per `SUBMISSION_GAMEPLAN.md` §1; structure per `PAPER_OUTLINE.md`.
Supersedes the run sections of `MF_BLAME_PRAISE_RUN.md`, whose 5,670-row
chat diagnostic is replaced by arm B below; its reasoning still stands.

## What the run has to close

| gap | claims affected | closed by |
|---|---|---|
| Instruct models only ever prompted raw; Gemma loses ~45% of answers, lopsided by sign (good items 10–27pp more), and the EV-based selection check can't clear intentionality (`parse_failure_by_cell.py`, `bdcca65`) | 1, 2, 8 (Gemma intentionality) | arm B |
| Claims 3 and 4 rest on one item set, and are exploratory | 3, 4 | arm A, preregistered |
| Claim 9's selection reading (c) can't be ruled out in the nonmoral pilot | 9 | arm A (MF used balanced pair-level selection) |
| Tuning table has no multiplicity correction | 2 | no-GPU task 3 |
| Mistral non-replication unresolved | 7 (out unless checked) | no-GPU task 4 |

## The run: two arms, instruct checkpoints only

Pretrained checkpoints are excluded from both arms. No claim uses pretrained
blame/praise, and a chat template doesn't apply to a base model.

### Arm A: MF blame/praise, raw format (primary protocol)

- MF's 126 selected items × q_blame, q_praise × 3 instruct models × N=25 =
  **18,900 rows**.
- Protocol identical to the MF intentionality run and the nonmoral
  blame/praise run: `RAIMONDI_PROMPT_TEMPLATE`, raw completion,
  `MAX_TOKENS=10`, unchanged `RELEASE` and seeding. Code already staged
  (`a5e12a6`); invocation:
  `elicit.py --engine vllm --n-samples 25 --questions q_blame,q_praise --model-keys <3 instruct keys>`.
- Appends to `moral_foundations_pilot/outputs/elicit_results.jsonl`. This is
  safe because `load_frame` filters by question (`df5d8e6`).

**Why this is a confirmatory test, not just more data.** These items have
never been asked blame or praise questions, so predictions committed before
the run (below) make this a genuine out-of-sample test of claims 3 and 4.
That's the "preregistered confirmatory run on fresh items" that
`SUBMISSION_GAMEPLAN.md` §5 item 7 names as the clean fix for their
exploratory status. **Caveat to state in the paper:** it tests
*generalization* (harm vs non-harm foundations), not *replication* of the
same contrast (moral vs nonmoral).

### Arm B: chat-format robustness pass, both pilots, all questions

- Same items, questions and N as each pilot's raw run, instruct models only:
  - nonmoral: 196 × 3 questions × 3 models × 25 = 44,100 rows
  - MF: 126 × 3 questions × 3 models × 25 = 28,350 rows
  - **total 72,450 rows**
- Identical frame text, sent as one user message with no system prompt (the
  production `render.py` "chat" shape), with each model's own chat template
  applied by `VllmEngine`. `MAX_TOKENS=10`, pending the smoke test (step 2
  below).
- N=25 rather than a small diagnostic N. It's cheap, and it means chat
  estimates are exactly as precise as raw ones. So if the formats disagree,
  the paper can report both at full strength instead of treating chat as a
  weaker check.

### Size and time

Throughput in the 2026-08-19/21 runs was 15–20 rows/s per model (Gemma
slowest), measured from row timestamps.

| | rows per model | time per model |
|---|---:|---:|
| arm A | 6,300 | ~6 min |
| arm B | 24,150 | ~25 min (chat templates add prompt tokens, so allow ~30) |
| **total** | **30,450** | **~35 min** |

That's ~91,350 rows in all, about 1.75 GPU-hours run sequentially, or well
under an hour with one job per model as the cluster runner already does.
Model loading is on top of that. Per CLAUDE.md §4, the smoke test (step 2)
confirms these numbers before launch.

## Engineering before launch (no GPU)

1. **Add `--format raw|chat` to both pilots' `elicit.py`.**
   - Reuse `VllmEngine`'s existing `messages` path; no new engine code.
     *(2026-09-28, Parker: that path sent every chat prompt with two BOS
     tokens — the templates write BOS as text and vLLM prepends another.
     Fixed in `3f05c6d` with tests; arm B needs that commit.)*
   - Chat prompt_ids get the production suffix, `{variant}::{question}::chat`
     (the 3-part convention `src/knobe/power.py` and `src/knobe/analysis/ingest.py`
     already parse). Their seeds therefore derive independently, and job_ids
     can't collide with raw.
   - Chat rows go to a **separate file**, `elicit_results_chat.jsonl`.
     `load_frame` filters by question but not by format, so mixing them into
     one file would silently pool them (the `df5d8e6` failure mode).
   - Bump `RUNNER_VERSION` in both.
2. **Smoke test:** fake engine for both arms (job counts, 0 collisions
   against the published archives), then a real N=2 chat pass per model.
   Two decisions come from it:
   - **Parse rate under chat.** If Gemma is still below ~90%, check whether
     it's truncation. If so, raise chat `MAX_TOKENS` to 32 before the full
     run and record why. Raw arms stay at 10 regardless.
   - **Throughput,** to confirm the time estimate.
3. **Regenerate `mf_pilot_dataset_selected.csv`** (`curate_foundation_relevance.py
   --select`). The local copy lacks `q_blame`/`q_praise`, and arm A exits
   without them.
4. **Fix `verify_curation_provenance.py`'s** cell-by-cell check to compare
   shared columns. It currently fails on column differences although the item
   sets match. *(Done 2026-09-28 — see the commit that adds this note.)*
5. **Add a `fmt` argument to both `load_frame`s** (default raw, reads the
   matching file), so every existing caller's frame is unchanged.
6. **Commit the analysis plan (next section) before any real row exists.**

## Analysis plan, to commit before the run

**Scoring and inference:**
- Parsed rating is primary, EV reported alongside.
- WCB B=1999, cluster=pair_id.
- Holm within (family, tuning, question, format), extending
  `holm_correct_pilots.py`'s grouping by the format axis.

**Arm A:**

| test | prediction, committed now |
|---|---|
| A1 (claim 3 generalization): q_blame `sign_c:arm_c`, harm vs non-harm pooled, per instruct family | non-zero, in the direction of the nonmoral result: a smaller blame outcome swing in the harm arm. Fix `arm_c`'s coding in the plan |
| A2 (claim 4): blame swing vs praise swing per family, parsed scale (`blame_praise_swing.py` method) | Gemma and Llama blame > praise; Mistral praise > blame |
| A3 (claim 9 analogue): good-outcome blame, harm vs non-harm (`domain_gap_decomposition` method) | moral-core good items keep a high blame floor, as in the nonmoral pilot |
| exploratory | per-foundation cells; q_praise interactions |

**Arm B, per (pilot, family, question):**

| test | what it decides |
|---|---|
| B1: parse rate and its sign lopsidedness under chat (`parse_failure_by_cell.py`, format axis added) | whether chat removes the Gemma selection concern |
| B2: every claim's key contrast re-estimated under chat, reported next to raw | whether the claims hold under the other format |

**B2 decision rule, fixed in advance:**
- **Same direction and same significance verdict under both formats →** the
  claim holds as stated, and the paper adds one robustness sentence.
- **Otherwise →** report both formats, and extend claim 1 to name prompt
  format as a third measurement choice alongside scoring and question type.

## How each outcome lands in the paper

Every outcome is writable. The run can't leave the paper worse off than
now, only change which sentences it contains.

| outcome | paper change |
|---|---|
| A1–A3 confirmed | claims 3 and 4 become "confirmed on independent items, preregistered"; claim 9 loses reading (c); §5.3–5.5 cite both pilots |
| A1–A3 not confirmed | claims 3 and 4 scoped to the nonmoral item set, with the MF result reported as a failed generalization. An informative finding in its own right |
| B: chat fixes parse, estimates agree | Gemma's intentionality selection concern is closed; claims 1, 2 and 8 hold under either format; §8 limitation becomes a robustness result |
| B: chat fixes parse, estimates move | claim 1 gains a third axis (format), and the moved claims are reported under both formats. Arguably makes §4 the paper's strongest section |
| B: chat doesn't fix parse | the selection concern stays and is stated for Gemma's intentionality cells; Mistral (98% parse under raw) carries those claims |

## No-GPU tasks in the same week

1. Fix `verify_curation_provenance.py` (engineering step 4).
2. Commit the analysis plan (engineering step 6).
3. **Holm on the tuning table:** you and Parker agree on the grouping, then
   run it (gameplan §5 item 3).
4. **Mistral revision check:** compare the recorded `model_revision` hashes
   against Raimondi's. If it resolves claim 7 either way, it goes in §7 or
   Appendix B; if not, claim 7 stays out.
5. After the run: republish both pilots' `results_dist/` archives, add
   log lines, and update `PROTOCOL.md` §8 item 5 (the human study's
   foundations blame/praise reasoning reverses).

## Deliberately not in this run

- **Indifference-clause ablation.** It's the test that would *explain* claim
  9, but it needs new stimuli and a design pass. Claim 9 is written as
  "pattern established, explanation open", which is honest without it. A
  paper-two item.
- **Pretrained anything,** more model families, or larger N. None changes a
  claim's status: power is limited by storyline count, not samples.
- **Human study.** Needs an IRB determination; a separate paper.
