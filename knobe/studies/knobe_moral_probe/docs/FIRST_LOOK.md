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

**Spending:** nothing in this plan costs money except cluster GPU time
(step 3), which needs the researcher's go-ahead first.

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

From the repo root on the cluster:

    .venv/bin/python studies/knobe_moral_probe/tools/check_chat_bos.py
    .venv/bin/python studies/knobe_moral_probe/tools/check_chat_bos.py --vllm

Exit 1 means some model gets BOS twice. Stop and report it before step 3.

### 3. (cluster) Elicitation. **STOP: researcher go-ahead first**

Size: 80 items × 168 samples = 13,440 rows per model per condition; 6
models × 2 conditions (with examples, `--no-examples`) = 161,280 rows. At
the pilots' measured 15–20 rows/s that's about **2.2–3 h of GPU**. No API
cost.

**3a. Validation pass (about 12–15 min).** One model, with examples. This
checks throughput and the number rate before the long run:

    ../../.venv/bin/python -m kmp.elicit --items stimuli/ngo_verbatim.csv --out outputs/elicit/nv_check_mistral.jsonl --engine vllm --model-keys mistral-7b-v0.1-instruct

Report the rows/s and the share of numeric answers. Go on only if they're
close to the estimate.

**3b. Full first look**, from the study folder:

    ../../.venv/bin/python -m kmp.elicit --items stimuli/ngo_verbatim.csv --out outputs/elicit/ngo_verbatim.jsonl --engine vllm
    ../../.venv/bin/python -m kmp.elicit --items stimuli/ngo_verbatim.csv --out outputs/elicit/ngo_verbatim_noex.jsonl --engine vllm --no-examples

Re-running the same command resumes. Bring back both `.jsonl` files and
both `.manifest.json` files. The `.jsonl` files are gitignored; the
manifests are committed.

### 4. (local) Gates and the sign-effect table

From the study folder:

    ../../.venv/bin/python -m kmp.checks --results outputs/elicit/ngo_verbatim.jsonl --baseline outputs/elicit/ngo_verbatim_noex.jsonl --items stimuli/ngo_verbatim.csv --out-dir outputs/checks/ngo_verbatim

From the repo root (about 1 min):

    .venv/bin/python studies/knobe_moral_probe/analysis/first_look.py --results studies/knobe_moral_probe/outputs/elicit/ngo_verbatim.jsonl --items studies/knobe_moral_probe/stimuli/ngo_verbatim.csv --out studies/knobe_moral_probe/outputs/first_look/sign_effects.csv

Commit `outputs/checks/ngo_verbatim/`, `outputs/first_look/sign_effects.csv`
and the manifests, and add `ANALYSIS_LOG.md` lines for the run, the checks
and the first look.

## Go/no-go rule (proposed; the researcher confirms it before the data)

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
