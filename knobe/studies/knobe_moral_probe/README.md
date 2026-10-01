# knobe_moral_probe

Do language models show the Knobe effect, rating a foreseen bad side effect
as more intentional than a good one? Does the effect extend beyond harm and
help, and does fine-tuning introduce or strengthen it? Asked on Ngo et al.'s
(2015) paired scenarios, plus a nonmoral extension and a moral-foundations
extension. Research questions and full design: `docs/DESIGN.md`.

Started 2026-09-28. Everything belonging to this study lives in this folder
and carries its name:

| where the name appears | form |
|---|---|
| folder | `studies/knobe_moral_probe/` |
| git branch | `knobe_moral_probe` |
| commit messages | prefixed `[knobe_moral_probe]` |
| release string (seeds) | `knobe_moral_probe` |
| item IDs | prefixed `kmp-` |
| `RUNNER_VERSION` | starts with `knobe_moral_probe` |
| analysis log | `ANALYSIS_LOG.md` in this folder |

## Relation to earlier work in this repo

This study is new work. It changes none of the earlier files, and reads
none of their outputs except one: `analysis/power_basis.py`, the
design-stage power check, reads the MF pilot's committed
`sign_wcb_parsed.csv`.

- **Ngo-extension pilots**
  (`analysis/ngo_extensions/nonmoral_pilot/`, `moral_foundations_pilot/`,
  2026-08 to 2026-09-25). Their findings motivated this study's design: how
  models were prompted, how answers were scored, and how items were
  screened. They stay as the pilot record. Some pilot scenarios are reused
  here as drafts, re-screened under this study's rules, and get `kmp-` IDs.
- **v1.0 / v1.1 main run** (`data/release/`, `results_dist/results_v1*`).
  Separate stimuli and taxonomy; not used here.
- **Pilot-era planning docs** (`docs/submission_plan/`). Written before this
  study. `FINAL_RUN_PLAN.md` and `MF_BLAME_PRAISE_RUN.md` are superseded by
  `docs/DESIGN.md`.

Library code in `src/knobe/` (engine, model registry, seeding, result
format) is imported, not copied.

## Contents

| path | what |
|---|---|
| `docs/DESIGN.md` | research questions, stimuli, screening, instrument, prompt format, code, gates, scale, analysis |
| `docs/REFERENCES.md` | what each cited work is cited for |
| `references.bib` | BibTeX, from official publisher records |
| `ANALYSIS_LOG.md` | one line per completed run of this study |
| `docs/IMPLEMENTATION_PLAN.md` | the pipeline build plan |
| `kmp/` | pipeline: items, protocol, prompts, screen (pass rule, pair selection), screen_run (reviewer runner and CLI), elicit, frame, checks |
| `tests/` | `.venv/bin/python -m pytest studies/knobe_moral_probe/tests -q` from the repo root |
| `tools/check_chat_bos.py` | pre-pilot check for a doubled BOS on instruct chat prompts |
| `analysis/power_basis.py` | DESIGN.md §9 power table → `outputs/power_basis.csv` |
| `stimuli/` | one items file per experiment: `nonmoral.csv`, `foundations.csv`, `ngo_verbatim.csv` |

## Commands

From this folder; `../../.venv/bin/python -m kmp.<module> --help` for all
flags. `<experiment>` is `nonmoral`, `foundations` or `ngo_verbatim`. An
items file can't mix experiments, so each step runs once per experiment.

**Before the pilot,** on the cluster, from the repo root: check whether
knobe's `VllmEngine` feeds instruct chat prompts a doubled BOS. Run the
tokenizer mode, then `--vllm` (GPU), and report both results before any
real elicitation. Exit 1 means some model gets BOS twice.

    .venv/bin/python studies/knobe_moral_probe/tools/check_chat_bos.py
    .venv/bin/python studies/knobe_moral_probe/tools/check_chat_bos.py --vllm

**Screening** (`kmp.screen`, which runs `kmp.screen_run`'s CLI). Start with
`--dry-run`: it prints the call count and a token estimate and asks nothing
(CLAUDE.md §4). A real run needs `protocol.REVIEWER_MODEL` pinned to an
exact dated model ID (not `-latest`) and the `anthropic` package installed
in `.venv`. `--mock` is a deterministic fake reviewer for testing. Re-run
the same command to resume.

    ../../.venv/bin/python -m kmp.screen --items stimuli/<experiment>.csv --out-dir outputs/screening/<experiment> --dry-run
    ../../.venv/bin/python -m kmp.screen --items stimuli/<experiment>.csv --out-dir outputs/screening/<experiment> --reviewer-model <pinned id>

**Elicitation.** One `--out` per experiment × model set; a second run on the
same `--out` is refused. Each `--out` gets a run manifest,
`<out>.manifest.json`, which is committable provenance; the `.lock` and
`.starts.jsonl` sidecars and any `.manifest.json.*.tmp` left by an
interrupted manifest write are gitignored, like the results. `--engine` is
required (`vllm` on the cluster; `fake` only for tests). Every model is
run twice: with the worked examples, and with `--no-examples` into its own
`--out`. The copying check needs the no-examples run as its baseline. This
roughly doubles pilot elicitation, so count it in the cost estimate.

    ../../.venv/bin/python -m kmp.elicit --items outputs/screening/<experiment>/selected_items.csv --out outputs/elicit/<experiment>.jsonl --engine vllm --model-keys <keys>
    ../../.venv/bin/python -m kmp.elicit --items outputs/screening/<experiment>/selected_items.csv --out outputs/elicit/<experiment>_noex.jsonl --engine vllm --model-keys <keys> --no-examples

**Checks** (DESIGN.md §8 and its amendments). `--baseline` is the
no-examples results file.

    ../../.venv/bin/python -m kmp.checks --results outputs/elicit/<experiment>.jsonl --baseline outputs/elicit/<experiment>_noex.jsonl --items outputs/screening/<experiment>/selected_items.csv --out-dir outputs/checks/<experiment>

Exit 0: nothing blocks. Exit 1: a blocking gate (an uncaught error, such as
an unreadable results file, also exits 1; read stderr). Exit 2: the inputs were
refused before anything was written (a missing or mismatched manifest, a
baseline that isn't a no-examples run of the same models and prompts).
Blocking: coverage gaps, any cell below the number-rate minimum, and, for
instruct models, a failed or missing validity check or example copying
above `protocol.COPY_EXCESS_MAX` (missing baseline counts). Reported as
findings only: the same validity and copying problems for pretrained
models, anchor agreement, the example effect and throughput. The tables and
`provenance.json` (inputs and hashes, git state, thresholds, manifests,
gate summary) go to `--out-dir`; they are small summary tables and are
committed (repo CLAUDE.md §3). A run on `--engine fake` prints a WARNING and
records `fake_engine: true` in `provenance.json`; it can legitimately exit 1,
since random answers can fail the instruct validity checks.
