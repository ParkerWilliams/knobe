# knobe_moral_probe: go / no-go and the full run

Written 2026-10-22 for Parker. Use this after the pilot (`docs/PILOT.md`).
It is written so you can decide and run without waiting on anyone:

- **GO:** you run the full run straight away. GPU time is your call.
- **NO-GO:** you push the checks and stop. The agent fixes the cause and
  updates this repo, and you re-run the pilot step it names.

The decision comes from a script, not a judgment call.

## 0. Already done before you start (agent and MM)

- The pilot ran (`docs/PILOT.md` steps 1–4) and its bundle is in
  `results_dist/`.
- MM applied review sheets 15–19, and the agent ran
  `../../.venv/bin/python -m tools.pilot_select --full`. That wrote
  `stimuli/full_run/{ngo_verbatim,nonmoral,foundations}.csv` (every
  approved pair that passed screening), committed and pushed.

If `stimuli/full_run/` isn't on the branch, stop: the full item set isn't
ready yet.

## 1. Pilot checks (CPU only, a few minutes)

You can run these on the cluster or anywhere with the repo installed. From
the study folder:

    tar -xzf ../../results_dist/results_knobe_moral_probe_pilot.tar.gz
    for e in nonmoral foundations; do for m in gemma llama_mistral; do
      ../../.venv/bin/python -m kmp.checks --stage pilot --results outputs/elicit/pilot_${e}_$m.jsonl --baseline outputs/elicit/pilot_${e}_${m}_noex.jsonl --items stimuli/pilot_run/$e.csv --out-dir outputs/checks/pilot_${e}_$m
    done; done

Each of the four exits 1 if anything blocks. That's expected; step 2 sorts
it out.

## 2. Go / no-go

    ../../.venv/bin/python -m tools.go_no_go outputs/checks/pilot_*

It prints **GO** or **NO-GO** and sorts every blocking line from the checks
into three groups:

| Group | What's in it | Effect |
|---|---|---|
| **STOP** | any reply cut off at the token budget, or no finish reason recorded (`cut_off`); missing rows (`coverage`); an instruct model under 90% numbers in any cell, except the next row's; an instruct model failing blame/praise validity or copying the worked examples | NO-GO |
| **allowed** | a pretrained model under 90% numbers (DESIGN.md §8: a finding for RQ3, not a blocker); Llama-3.1-8B-Instruct under 90% on intentionality or praise, but at 70% or more (its known refusals to rate harm) | GO |
| **findings** | pretrained models failing validity or copying | GO, reported |

### If GO

Go to step 3. First work out the time: `throughput.csv` in each pilot
checks folder gives rows per second for each model. The full run is about
**78,000 rows per model** (470,592 for all six if every survivor is
approved; `tools.pilot_select --full` prints the exact item counts). Time
per model is its rows ÷ its rows per second. As a guide: 20 rows/s is
about 6.5 h for all six models, and 8 rows/s is about 16 h. The time is
your call.

### If NO-GO

Commit and push the checks, so the agent can see the same files:

    git add outputs/checks/pilot_*
    git commit -m "[knobe_moral_probe] pilot checks: NO-GO"
    git push origin knobe_moral_probe

Then stop. Common causes and what happens next:

| STOP line | Likely cause | Fix (agent) | Then you |
|---|---|---|---|
| `cut_off: ... of replies stopped at the token budget` | a model writes long answers | raise the chat budget | re-run the pilot for that model only |
| `cut_off: ... not_recorded` | the engine didn't report finish reasons | fix the engine adapter | re-run the pilot self-check |
| `coverage: ...` | a job died part-way | none; re-running the same command resumes | re-run that pilot command, then steps 1–2 |
| `number_rate:` on Gemma or Mistral instruct | a prompt-format problem on that model | change the wording or format (a protocol change) | re-run the pilot |
| `validity:` or `example_copying:` on an instruct model | the model isn't reading the items, or is copying the worked examples | MM decides; possibly a protocol change | re-run the pilot |

## 3. The full run

Two jobs, as in the pilot. Gemma needs its attention backend. With the
worked examples only: the full run has no no-examples run (DESIGN.md
amendment 2026-10-01). From the study folder:

    # job 1, with VLLM_ATTENTION_BACKEND=TRITON_ATTN_VLLM_V1
    G=gemma-2-9b-pretrained,gemma-2-9b-instruct
    for e in ngo_verbatim nonmoral foundations; do
      ../../.venv/bin/python -m kmp.elicit --items stimuli/full_run/$e.csv --out outputs/elicit/full_${e}_gemma.jsonl --engine vllm --model-keys $G
    done

    # job 2, default backend
    LM=llama-3.1-8b-pretrained,llama-3.1-8b-instruct,mistral-7b-v0.1-pretrained,mistral-7b-v0.1-instruct
    for e in ngo_verbatim nonmoral foundations; do
      ../../.venv/bin/python -m kmp.elicit --items stimuli/full_run/$e.csv --out outputs/elicit/full_${e}_llama_mistral.jsonl --engine vllm --model-keys $LM
    done

Re-running a command resumes where it stopped. Results must survive a pod
restart (local disk or S3).

**Early check, about 5 minutes, after each job's first file
(`ngo_verbatim`):**

    ../../.venv/bin/python -m kmp.checks --stage full --results outputs/elicit/full_ngo_verbatim_gemma.jsonl --items stimuli/full_run/ngo_verbatim.csv --out-dir outputs/checks/full_ngo_verbatim_gemma

(Use `llama_mistral` in place of `gemma` for job 2.) Open `cut_off.csv`:
every chat row should say `pass`. **Stop rule:** if any says `fail` or
`not_recorded`, stop the job and push that `cut_off.csv`. It's the same fix
as in the NO-GO table, and the rows already written are kept. Otherwise let
the job run to the end.

## 4. Hand back

The results are about 52 MB compressed in all, so there's one bundle per
job (GitHub warns over 50 MB). The glob includes the `.starts.jsonl` and
`.finish.jsonl` sidecars, which the checks need:

    tar -czf ../../results_dist/results_knobe_moral_probe_full_gemma.tar.gz outputs/elicit/full_*_gemma.jsonl*
    tar -czf ../../results_dist/results_knobe_moral_probe_full_llama_mistral.tar.gz outputs/elicit/full_*_llama_mistral.jsonl*
    git add ../../results_dist/results_knobe_moral_probe_full_*.tar.gz outputs/elicit/full_*.manifest.json
    git commit -m "[knobe_moral_probe] full run: elicitation results (two bundles), manifests"
    git push origin knobe_moral_probe

That's the end of your part. The agent runs `kmp.checks --stage full` on
all six files, the analysis, and the log lines.

## Why these rules

- **Stops are things a full run can't recover from without a re-run:**
  answers cut off, missing data, instruct models whose answers can't be
  used. Each stop costs a pilot re-run, not a full one.
- **Allowed lines don't change what data gets collected.** How pretrained
  failures and Llama's refusals enter the analysis is decided afterwards,
  from the same rows. Holding the run for them gains nothing.
- **The 70% floor for Llama:** on OpenRouter its intentionality answers
  were 88% numbers (with the runner-0.4 reader) and refusals 14% on bad items
  (`ANALYSIS_LOG.md`, 2026-10-22). Anything well below that would be a new
  problem, not the known refusals, so it stops.
