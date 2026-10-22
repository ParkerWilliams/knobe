# knobe_moral_probe: pilot runbook

Written 2026-10-22. The pilot is DESIGN.md §8's gate before the full run:
44 screened, approved items on all six study models, with and without the
worked examples. It is also the first data from the study's own models (the
first look ran on OpenRouter stand-ins), so it covers RQ3 (pretrained vs
instruct) for the first time.

**Spending:** cluster GPU time only, about 1.2–3 h (estimate below). Parker
runs it and decides on it. Nothing here calls a paid API.

## 0. Before Parker starts (MM and the agent)

These must be done and pushed first. Step 1 refuses otherwise.

1. **MM:** review the survivor sheets (`stimuli/review/15`–`19`) and run
   `tools.review apply` on each. The pilot needs at least 4 approved,
   screened pairs in each nonmoral arm and 2 in each foundations arm.
2. **MM:** decide the intentionality w1 wording (see "Open decision"
   below). It changes the prompt text, so it has to come before the pilot.
3. **Agent:** pick the pilot items, commit, push:

       ../../.venv/bin/python -m tools.pilot_select

   `tools.pilot_select` takes approved pairs that passed screening, ranked
   by sha256 of a fixed seed and the pair (reproducible, not hand-picked),
   and writes `stimuli/pilot_run/{nonmoral,foundations}.csv`. Don't run
   `tools.lint_stimuli` on these files. Its authoring rule that every shared
   foundations storyline keep its harm pair doesn't apply to a sample, and
   §8's gates don't use within-storyline contrasts. `kmp.elicit` runs the
   design check that applies to a selected set (`stage="selected"`, clean
   on a simulated pick 2026-10-22).

## Cluster notes (unchanged from FIRST_LOOK.md)

- Code: `git@github.com:ParkerWilliams/knobe.git`, branch
  `knobe_moral_probe`. Run everything from the study folder
  `knobe/studies/knobe_moral_probe/`. The commands write
  `../../.venv/bin/python`; in a cluster job, use the job's `python`.
- Environment: `vllm==0.10.1`, `huggingface_hub>=0.24.0`, the repo installed
  with `.[stats]`.
- **Gemma needs `VLLM_ATTENTION_BACKEND=TRITON_ATTN_VLLM_V1`**, so Gemma
  runs as its own job, and Llama and Mistral run as another without it.
- Re-running a command on the same `--out` resumes.

## 1. Double-BOS check (a few minutes)

From the `knobe/` folder:

    .venv/bin/python studies/knobe_moral_probe/tools/check_chat_bos.py 2>&1 | tee studies/knobe_moral_probe/outputs/bos_check.txt
    .venv/bin/python studies/knobe_moral_probe/tools/check_chat_bos.py --vllm 2>&1 | tee -a studies/knobe_moral_probe/outputs/bos_check.txt

**Stop rule:** if either reports a doubled BOS, stop and push `bos_check.txt`.

## 2. Self-check (about 10–20 min): Gemma-instruct, nonmoral, with examples

In the Gemma job setup. This is the first study model on the cluster and
the first run with the 512-token chat budget, so check it before spending
the rest:

    ../../.venv/bin/python -m kmp.elicit --items stimuli/pilot_run/nonmoral.csv --out outputs/elicit/pilot_check_gemma.jsonl --engine vllm --model-keys gemma-2-9b-instruct
    ../../.venv/bin/python -m kmp.checks --results outputs/elicit/pilot_check_gemma.jsonl --items stimuli/pilot_run/nonmoral.csv --out-dir outputs/checks/pilot_check_gemma

The checks exit 1 here because there's no no-examples baseline yet. That's
expected. Read three files in `outputs/checks/pilot_check_gemma/`:

- `cut_off.csv`: every row `pass`. **Stop rule:** if any row is `fail` or
  `not_recorded`, stop and send the agent the file plus a few
  `raw_response`s whose line in
  `outputs/elicit/pilot_check_gemma.jsonl.finish.jsonl` says `"length"`.
  `fail` means replies hit the 512-token budget; `not_recorded` means the
  engine didn't report finish reasons.
- `number_rates.csv`: share of numeric answers. **Stop rule:** if most
  cells are below 0.90, stop and send the file and a few `raw_response`s.
  A cell or two below 0.90 isn't a stop (see "Expected" below).
- `throughput.csv`: rows per second. With it, step 3's time is rows ÷ rate.

The check file is not part of the pilot's results.

## 3. The pilot (about 1.2–3 h GPU in all)

Two jobs, each running both experiments with and without the worked
examples. That's 8 output files. Each `--out` is its own file; don't
concatenate them.

    # job 1, with VLLM_ATTENTION_BACKEND=TRITON_ATTN_VLLM_V1
    G=gemma-2-9b-pretrained,gemma-2-9b-instruct
    for e in nonmoral foundations; do
      ../../.venv/bin/python -m kmp.elicit --items stimuli/pilot_run/$e.csv --out outputs/elicit/pilot_${e}_gemma.jsonl --engine vllm --model-keys $G
      ../../.venv/bin/python -m kmp.elicit --items stimuli/pilot_run/$e.csv --out outputs/elicit/pilot_${e}_gemma_noex.jsonl --engine vllm --model-keys $G --no-examples
    done

    # job 2, default backend
    LM=llama-3.1-8b-pretrained,llama-3.1-8b-instruct,mistral-7b-v0.1-pretrained,mistral-7b-v0.1-instruct
    for e in nonmoral foundations; do
      ../../.venv/bin/python -m kmp.elicit --items stimuli/pilot_run/$e.csv --out outputs/elicit/pilot_${e}_llama_mistral.jsonl --engine vllm --model-keys $LM
      ../../.venv/bin/python -m kmp.elicit --items stimuli/pilot_run/$e.csv --out outputs/elicit/pilot_${e}_llama_mistral_noex.jsonl --engine vllm --model-keys $LM --no-examples
    done

**Size:** per model and condition, 24 nonmoral items × 168 samples + 20
foundations items × 144 = 6,912 rows. Over 6 models × 2 conditions that's
82,944 rows. At 8–20 rows/s that's 1.2–2.9 h. Step 2's throughput
replaces the guess. Chat replies stop at the end of each answer: Llama's
mean on OpenRouter was 68 tokens, the 95th percentile 146. So the 512
budget mainly costs time on unusually long replies.

## 4. Hand back through the repo

The `.jsonl` files are gitignored, so they go in one bundle together with
their `.starts.jsonl` and `.finish.jsonl` sidecars (the glob picks those
up). The checks need both. From the study folder:

    tar -czf ../../results_dist/results_knobe_moral_probe_pilot.tar.gz outputs/elicit/pilot_*.jsonl
    git add ../../results_dist/results_knobe_moral_probe_pilot.tar.gz outputs/elicit/pilot_*.manifest.json outputs/bos_check.txt
    git commit -m "[knobe_moral_probe] pilot: elicitation results (bundle), manifests, BOS check"
    git push origin knobe_moral_probe

## 5. Local (agent): gates

    tar -xzf ../../results_dist/results_knobe_moral_probe_pilot.tar.gz
    for e in nonmoral foundations; do for m in gemma llama_mistral; do
      ../../.venv/bin/python -m kmp.checks --stage pilot --results outputs/elicit/pilot_${e}_$m.jsonl --baseline outputs/elicit/pilot_${e}_${m}_noex.jsonl --items stimuli/pilot_run/$e.csv --out-dir outputs/checks/pilot_${e}_$m
    done; done

Then commit `outputs/checks/pilot_*`, add `ANALYSIS_LOG.md` lines, and
report to MM against DESIGN.md §8 (numbers, pretrained validity, example
check, anchor reversal, throughput, and the cut-off gate).

## Expected, not a stop

- **Llama-3.1-8B-Instruct refuses to rate some harmful acts.** On
  OpenRouter it refused intentionality on 14–16% of bad items and 5–7% of
  good items under every wording (`ANALYSIS_LOG.md`, 2026-10-22), and it
  refuses praise for harm as well (2026-10-13). Its number-rate cells for
  those questions will likely sit below 0.90 and block in `kmp.checks`.
  That's a decision for MM after the pilot (how refusals enter the
  analysis), not a reason to stop the run.
- **Pretrained models may fail validity** (§8 check 2). A finding, not a
  blocker.

## Open decision (MM, before step 0.3): intentionality w1 wording

w1 is Ngo's yes/no question, "Did {agent} intentionally {effect}?". On
Llama-3.1-8B-Instruct, appending a scale fixes the format misses
(`outputs/first_look/intentionality_wording_test.csv`):

| wording | appended text | numeric | format misses (bad / good) | bad − good |
|---|---|---|---|---|
| w1 | — | 53% | 39% / 34% | 1.7 |
| w1a | "Answer on a scale from 0 (definitely not) to 10 (definitely yes)." | 84% | 4% / 7% | 3.9 |
| w1b | "Answer with a number from 0 (no) to 10 (yes)." | 86% | 5% / 3% | 3.9 |

Both keep Ngo's question word for word. Recommendation: **w1a**. It's
closer to the other wordings' anchored scales, and its number rate is more
even across bad and good (83% / 86% vs w1b's 80% / 92%), which matters for
selection bias. Either one is a protocol change (a DESIGN amendment), and
it changes the prompt text for every model.

## Full run, afterwards (for planning)

About 440k rows (DESIGN.md §9), with no no-examples run. At the pilot's
measured rate that's 440,000 ÷ (rows/s) seconds: about 6 h at 20 rows/s,
15 h at 8 rows/s. The full-run runbook follows the same steps, with the
selected items in place of `stimuli/pilot_run/`.
