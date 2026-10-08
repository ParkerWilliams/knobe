# knobe_moral_probe: task checklist

Last updated 2026-10-08. Task numbers are `AUTHORING_PLAN.md`'s. **(you)**
marks a step only the researcher can do; **STOP** is a gate where the agent
waits for you. `HANDOFF.md` has the detail.

## Done

- [x] Design (`DESIGN.md`) approved, with dated amendments
- [x] Pipeline (`kmp/`, 13 tasks), reviewed
- [x] Definitions and review checklist approved (decisions A–U)
- [x] Task 0: sign-off on the checklist and decisions M–S, U
- [x] Task 1: Ngo source parser (`tools/ngo_source.py`)
- [x] Task 2: review record (`tools/review_record.py`)
- [x] Task 3: `stimuli/ngo_verbatim.csv` generated (80 items) and logged
- [x] Task 4: stimulus lint (`tools/lint_stimuli.py`)
- [x] Task 5: review sheets and decisions (`tools/review.py`)
- [x] Task 6: README

## Stimuli authoring

- [ ] Task 7: review batch 01, the verbatim set (80 items)
  - [x] Sheet `stimuli/review/01_nv_all.md` made and committed
  - [ ] **(you)** Fill in `01_nv_all_decisions.csv` and run `tools.review apply`. Look at item 72 (tablet vs music player), item 17 (neighbor vs Susie-Ann), and the typos in 10, 23, 40, 46, 58
  - [ ] Parser fixes for any `revise`, then re-sheet as the next batch number (**STOP** again)
  - [ ] Lint clean, commit your decisions
- [ ] Task 8: method for adding draft items (no commit of its own)
- [ ] Task 9: `stimuli/NOTES.md`, `nonmoral_log.csv`, role-noun table for all 40 storylines
  - [ ] **STOP (you):** approve the role-noun table (decisions O, P)
- [ ] Task 10: batches 02–03, adapted Ngo moral pairs (2 × 40 items). **STOP (you):** review
- [ ] Task 11: batches 04–05, prudential pairs (2 × 40). **STOP (you):** review
- [ ] Task 12: batches 06–07, procedural pairs (2 × 40). **STOP (you):** review
- [ ] Task 13: nonmoral completeness check (D2)
- [ ] Task 14: foundations scaffold roster. **STOP (you):** approve
- [ ] Task 15: batches 08–14, foundations items. **STOP (you):** review each

## Screening

- [ ] Task 16: screening dry run and cost estimate. **STOP (you):** cost go-ahead
- [ ] Task 17: install `anthropic` (as a `screen` extra) and confirm the `claude-sonnet-4-6` pin
- [ ] Task 18: first real screening run, ngo_verbatim only (also confirms temperature 0 with thinking off)
- [ ] Task 19: screen nonmoral and foundations
- [ ] Task 20: selection review; revisit thresholds only if the real distribution calls for it. **STOP (you)**
- [ ] Task 21: revisit round (only if Task 20 asks for rewrites)
- [ ] Task 22: close out

## Before the pilot

- [ ] **(you, on the cluster)** Run `tools/check_chat_bos.py`, then with `--vllm`; report both
- [ ] Pilot cost estimate including the `--no-examples` run, for all 6 models. **STOP (you):** go-ahead
- [ ] Pilot: about 40 items × 6 models, with and without examples; `kmp.checks --stage pilot --baseline <noex results>`
- [ ] Revisit `COPY_EXCESS_MAX` (0.10 proposed) on the pilot results

## Full run

- [ ] Cost estimate (about 85k rows per model, about 7–9.5 h for 6 models). **STOP (you):** go-ahead
- [ ] Full run; `kmp.checks --stage full`
- [ ] Analysis, including the sensitivity fit without the loaded-role storylines (decision P)
