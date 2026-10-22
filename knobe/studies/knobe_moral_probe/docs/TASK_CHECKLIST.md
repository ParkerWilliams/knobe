# knobe_moral_probe: task checklist

Last updated 2026-10-22. Task numbers are `AUTHORING_PLAN.md`'s. **(you)**
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

## First look on Ngo's 80 (`FIRST_LOOK.md`), before any more authoring

- [x] `analysis/first_look.py` (sign-effect fits), tested on the fake engine
- [x] **(you)** Sheet 01: all 80 approved by MM 2026-10-12 (Codex pre-review), applied
- [x] **(you)** Confirm the go/no-go rule in `FIRST_LOOK.md` (2 of 3 instruct, confirmed 2026-10-12)
- [x] (Parker, OpenRouter, instead of the cluster) stand-in instruct models, v2 answer format: rule gives "go" (`HANDOFF.md` 2026-10-22)
- [x] **STOP (you):** go, accepted on the stand-ins 2026-10-22
- [ ] **(cluster)** `tools/check_chat_bos.py`, then with `--vllm`; first look on the 6 study models (now before the pilot; runbook needs the 256-token chat budget in its cost)
- [ ] Llama-3.1-8B-Instruct number rate: fix and test on OpenRouter before the full run

## Stimuli authoring (after a go)

- [ ] Task 7: review batch 01, the verbatim set (80 items)
  - [x] Sheet `stimuli/review/01_nv_all.md` made and committed
  - [ ] **(you)** Fill in `01_nv_all_decisions.csv` and run `tools.review apply`. Look at item 72 (tablet vs music player), item 17 (neighbor vs Susie-Ann), and the typos in 10, 23, 40, 46, 58
  - [ ] Parser fixes for any `revise`, then re-sheet as the next batch number (**STOP** again)
  - [ ] Lint clean, commit your decisions
- [ ] Task 8: method for adding draft items (no commit of its own)
- [ ] Task 9: `stimuli/NOTES.md`, `nonmoral_log.csv`, role-noun table for all 40 storylines (drafted 2026-10-22)
  - [ ] **STOP (you):** approve the role-noun table (decisions O, P)
- [ ] Task 10: batches 02–03, adapted Ngo moral pairs (2 × 40 items). **STOP (you):** review
  - Fix in the adapted items (MM, 2026-10-12): pair 9 bad, the effect names the person the scenario names, not "her neighbor"; pair 36 good, the effect says music player, not tablet. Kept as written in `ngo_verbatim`
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

## Screening (done 2026-10-22, screen first; MM)

- [x] OpenRouter route + `--allow-draft`; reply line; ~$2.30 in all (`ANALYSIS_LOG.md`)
- [x] Procedural valence limits, balanced fairness question, purity and fairness rewrites (DESIGN amendment 2026-10-22)
- [ ] **(you)** Review survivor sheets 15-19 (452 items) and `tools.review apply` each

## Before the pilot (`docs/PILOT.md`)

- [x] No cut-off reasoning: chat budget 512, finish reasons recorded, `cut_off` gate
- [x] Llama intentionality wording test (w1a/w1b fix the format misses; refusals remain)
- [x] **(you)** Intentionality w1 wording: w1a (MM 2026-10-22), applied
- [ ] Agent: `tools.pilot_select` once sheets 15-19 are applied, commit, push
- [ ] **(Parker, cluster)** `docs/PILOT.md` steps 1-4 (about 1.2-3 h GPU)
- [ ] Agent: gates (step 5), log, report; **STOP (you):** refusals and any gate failures

## Full run (`docs/FULL_RUN.md`)

- [ ] Agent: `tools.pilot_select --full` once sheets 15-19 are applied, commit, push
- [ ] **(Parker)** Pilot checks, then `tools.go_no_go` (GO: run; NO-GO: push the checks and stop)
- [ ] **(Parker, cluster)** Full run, 2 jobs x 3 sets (about 470k rows); early cut-off check; two bundles back
- [ ] Agent: `kmp.checks --stage full`; analysis, including the sensitivity fits (loaded roles, decision P; strict procedural limits; storylines without a harm pair, decision A)
- [ ] **(you)** How Llama's refusals enter the analysis
