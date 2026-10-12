# knobe_moral_probe: first look on Ngo's 80 vignettes

Decided 2026-10-12. Before anyone authors the ~550 extension items, run
Ngo's 40 pairs word for word (`stimuli/ngo_verbatim.csv`) on all 6 models
through the finished pipeline. If the models show no reliable Knobe
asymmetry on Ngo's own items, the nonmoral and foundations extensions (RQ2)
have nothing to extend, and we stop or rethink before spending the
authoring time.

It answers RQ1 on the verbatim text, gives a first read on RQ3 (instruct
vs pretrained), and runs the DESIGN §8 pilot gates (numbers, validity,
copying, anchor reversal, throughput).

**Caveat.** The verbatim items keep Ngo's names and pronouns, which change
with the sign (Bill harms, Robyn helps), so agent is confounded with sign.
The confound is not systematic: by the scenario's pronouns, the agent is
male in 21 bad and 19 good versions, so a gender bias can't make a sign
effect on its own. The name differs within the pair in 33 of 40
storylines, which adds noise and possible name cues (ethnicity, age) that
don't favor either sign. (Counted 2026-10-12 from `stimuli/ngo_verbatim.csv`:
he/his/him vs she/her per scenario; `agent` column bad vs good.) So a go
here is fair evidence of an effect. It can't say how much the role-noun
adaptation changes it; the verbatim-vs-adapted comparison does that later.
The main analysis uses the role-noun adapted items (DESIGN amendment
2026-10-01).

**Not needed:** screening (Ngo's items are human-validated; the reviewer
is for new items), an Anthropic API key, any authoring.

**Spending:** the only cost is cluster GPU time (step 3). Parker runs it
and decides on it; the agent never launches anything that costs money.

## Cluster notes (for whoever runs steps 2–3)

- **Code:** `git@github.com:ParkerWilliams/knobe.git`, branch
  `knobe_moral_probe`. The project is the `knobe/` folder inside the clone;
  everything for this run is in `knobe/studies/knobe_moral_probe/` ("the
  study folder"), and it imports `knobe/src/knobe/` for the engine.
- **Environment:** the setup the repo README validated on the H200s:
  `vllm==0.10.1`, `huggingface_hub>=0.24.0` (declare them in the job
  config's `runtime_env.pip`), plus the repo installed with `.[stats]`.
  The cluster's HF identity already reaches the gated Llama and Gemma
  checkpoints.
- **Python:** the commands below write `.venv/bin/python` (local layout).
  In a cluster job, use the job environment's `python`, run from the same
  folders.
- **Gemma needs `VLLM_ATTENTION_BACKEND=TRITON_ATTN_VLLM_V1`.** Neither
  `kmp.elicit` nor `src/knobe` sets it, so the G1 pilot's split applies:
  one job for Gemma with that variable set (`--model-keys
  gemma-2-9b-pretrained,gemma-2-9b-instruct`), one for Llama and Mistral
  without it. Step 3b gives each job its own `--out` files.
- **Throughput:** the G1 pilot measured 8.4–11.6 rows/s per H200, but with
  11-candidate forced scoring, which `kmp.elicit` doesn't do. The 15–20
  rows/s assumed below is unconfirmed, and step 3a is what settles it. At
  8.4 rows/s the whole run is about 5.3 h.
- **Resume:** re-running the same command on the same `--out` resumes.
  Results need to survive a pod restart (local disk or S3, as in G1).
- **Hand back through the repo:** step 3c. One compressed bundle in
  `results_dist/` (the pilots' convention), the manifests, and the
  BOS-check output, pushed to this branch.

## Steps

### 1. (researcher) Approve the 80 items

Review `stimuli/review/01_nv_all.md` and fill in
`stimuli/review/01_nv_all_decisions.csv`. The known oddities (item 72
tablet vs music player, item 17, typos in 10, 23, 40, 46, 58) are Ngo's own
text. The verbatim set's job is to be word for word, so approving them as
written is consistent with check B9. Then, from the study folder:

    ../../.venv/bin/python -m tools.review apply --items stimuli/ngo_verbatim.csv --decisions stimuli/review/01_nv_all_decisions.csv

`kmp.elicit` refuses any item that isn't `approved`. If you reject an item,
tell the agent: elicit then needs a copy of the file without that pair.

### 2. (cluster) Double-BOS check

From the `knobe/` folder on the cluster (the project folder inside the clone, where `.venv` and `pyproject.toml` live):

    .venv/bin/python studies/knobe_moral_probe/tools/check_chat_bos.py 2>&1 | tee studies/knobe_moral_probe/outputs/bos_check.txt
    .venv/bin/python studies/knobe_moral_probe/tools/check_chat_bos.py --vllm 2>&1 | tee -a studies/knobe_moral_probe/outputs/bos_check.txt

If either reports a doubled BOS (exit 1 without the `tee`), stop and push
`bos_check.txt` before step 3.

### 3. (cluster) Elicitation

Size: 80 items × 168 samples = 13,440 rows per model per condition; 6
models × 2 conditions (with examples, `--no-examples`) = 161,280 rows. At
15–20 rows/s that's about **2.2–3 h of GPU**, or about 5.3 h at the G1 pilot's 8.4 rows/s. No API
cost.

**3a. Self-check (about 15–25 min, recommended).** Gemma-instruct alone,
with examples, in the Gemma job setup. It was the slowest model and the
worst at answering with a number in the earlier pilots, so it is the
worst case for both:

    ../../.venv/bin/python -m kmp.elicit --items stimuli/ngo_verbatim.csv --out outputs/elicit/nv_check_gemma.jsonl --engine vllm --model-keys gemma-2-9b-instruct
    ../../.venv/bin/python -m kmp.checks --stage full --results outputs/elicit/nv_check_gemma.jsonl --items stimuli/ngo_verbatim.csv --out-dir outputs/checks/nv_check_gemma

`outputs/checks/nv_check_gemma/throughput.csv` has the rows/s, and
`number_rates.csv` has the share of numeric answers per question and
wording. If any `passes` is False (under 90% numbers), the full run would
fail the gates: stop and send the agent the file and a few
`raw_response`s from the `.jsonl`. Otherwise go on to 3b.
The check file is not part of 3b's results.

**3b. Full first look.** Two jobs, split by family because of Gemma's
attention backend (cluster notes above). Each job runs its models with
examples and then with `--no-examples`, from the study folder:

    # job 1, with VLLM_ATTENTION_BACKEND=TRITON_ATTN_VLLM_V1
    ../../.venv/bin/python -m kmp.elicit --items stimuli/ngo_verbatim.csv --out outputs/elicit/ngo_verbatim_gemma.jsonl --engine vllm --model-keys gemma-2-9b-pretrained,gemma-2-9b-instruct
    ../../.venv/bin/python -m kmp.elicit --items stimuli/ngo_verbatim.csv --out outputs/elicit/ngo_verbatim_gemma_noex.jsonl --engine vllm --model-keys gemma-2-9b-pretrained,gemma-2-9b-instruct --no-examples

    # job 2, default backend
    ../../.venv/bin/python -m kmp.elicit --items stimuli/ngo_verbatim.csv --out outputs/elicit/ngo_verbatim_llama_mistral.jsonl --engine vllm --model-keys llama-3.1-8b-pretrained,llama-3.1-8b-instruct,mistral-7b-v0.1-pretrained,mistral-7b-v0.1-instruct
    ../../.venv/bin/python -m kmp.elicit --items stimuli/ngo_verbatim.csv --out outputs/elicit/ngo_verbatim_llama_mistral_noex.jsonl --engine vllm --model-keys llama-3.1-8b-pretrained,llama-3.1-8b-instruct,mistral-7b-v0.1-pretrained,mistral-7b-v0.1-instruct --no-examples

Re-running the same command resumes. Don't concatenate the files: each
one is checked against its own manifest.

**3c. Hand back through the repo.** The `.jsonl` files are gitignored
(repo CLAUDE.md §3), so they go in one compressed bundle in `results_dist/`,
like the pilots' results (about 5 MB on the fake engine). The manifests and
the BOS output are committed as they are. From the study folder:

    tar -czf ../../results_dist/results_knobe_moral_probe_first_look.tar.gz outputs/elicit/ngo_verbatim_*.jsonl
    git add ../../results_dist/results_knobe_moral_probe_first_look.tar.gz outputs/elicit/ngo_verbatim_*.manifest.json outputs/bos_check.txt
    git commit -m "[knobe_moral_probe] first look: elicitation results (bundle), manifests, BOS check"
    git push origin knobe_moral_probe

The glob also picks up the `.starts.jsonl` sidecars, which the throughput
check reads. On the other end, from the study folder:

    tar -xzf ../../results_dist/results_knobe_moral_probe_first_look.tar.gz

### 4. (local) Gates and the sign-effect table

`kmp.checks` once per job, from the study folder:

    ../../.venv/bin/python -m kmp.checks --results outputs/elicit/ngo_verbatim_gemma.jsonl --baseline outputs/elicit/ngo_verbatim_gemma_noex.jsonl --items stimuli/ngo_verbatim.csv --out-dir outputs/checks/ngo_verbatim_gemma
    ../../.venv/bin/python -m kmp.checks --results outputs/elicit/ngo_verbatim_llama_mistral.jsonl --baseline outputs/elicit/ngo_verbatim_llama_mistral_noex.jsonl --items stimuli/ngo_verbatim.csv --out-dir outputs/checks/ngo_verbatim_llama_mistral

Then the sign-effect table over both jobs, from the `knobe/` folder (about 1 min):

    .venv/bin/python studies/knobe_moral_probe/analysis/first_look.py --results studies/knobe_moral_probe/outputs/elicit/ngo_verbatim_gemma.jsonl studies/knobe_moral_probe/outputs/elicit/ngo_verbatim_llama_mistral.jsonl --items studies/knobe_moral_probe/stimuli/ngo_verbatim.csv --out studies/knobe_moral_probe/outputs/first_look/sign_effects.csv

Commit `outputs/checks/ngo_verbatim_*/`, `outputs/first_look/sign_effects.csv`
and the manifests, and add `ANALYSIS_LOG.md` lines for the run, the checks
and the first look. (This split was run end to end on the fake engine on
2026-10-12.)

## Go/no-go rule (confirmed by the researcher 2026-10-12, before any data)

Fixed before the data, because with 24 model × question cells some will
reach p < .05 by chance. A fake-engine run with random answers produced
p ≈ .03 in one cell.

- **Primary test:** the intentionality sign effect (`sign_c`, bad minus
  good) in the 3 instruct models, `p_wcb` Holm-adjusted across those 3.
- **Go** (author the extensions): at least 2 of the 3 instruct models show
  a positive effect with adjusted p < .05, and those models pass
  `kmp.checks`'s blocking gates (number rate, blame/praise validity,
  copying).
- **No-go** (stop or rethink): none do, or the instruct models fail the
  number-rate or validity gates.
- **Discuss:** exactly 1 of 3. Then look at blame and the effect sizes
  before deciding.
- **Reported, not part of the rule:** pretrained models and the
  `sign_c:tuning_c` interaction (RQ3), blame, praise, significance. The
  pretrained models may fail validity, which DESIGN §8 treats as a finding.

## After a go

Return to `AUTHORING_PLAN.md` at Task 9 (role-noun table). The verbatim
run doubles as Task 18's consistency set, but not as its screening:
screening still runs before the pilot of the new items.
