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

This study is new work. It reads none of the earlier outputs and changes
none of the earlier files.

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

Stimuli, code and outputs are added here as the implementation plan proceeds.
