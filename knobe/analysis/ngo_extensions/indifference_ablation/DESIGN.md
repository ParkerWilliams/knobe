# Indifference-clause ablation — design (drafted 2026-09-25)

**Status (2026-09-28):** stimuli built and the elicitation code verified end-to-end
with the fake engine; the cluster run is staged. Nothing has been elicited yet.
Parker chose the §6 default scope (§7 items 1–4 decided); items 5–7 are open, and
**Mer's sign-off on the design is pending.** This is gameplan item 5 (`docs/submission_plan/SUBMISSION_GAMEPLAN.md`),
aimed at CLAIMS.md **claim 9**.

## 1. What it is for

Claim 9: blame is much less sensitive to outcome in moral scenarios than in nonmoral
ones, and the difference sits almost entirely in the good-outcome cell. Pilot blame
cell means (parsed, finetuned, `question_cell_means.csv`):

| | moral good | moral bad | nonmoral good | nonmoral bad | good-cell gap | bad-cell gap |
|---|---:|---:|---:|---:|---:|---:|
| gemma | 7.10 | 8.92 | 2.09 | 7.71 | 5.02 | 1.21 |
| llama | 6.92 | 8.53 | 2.66 | 7.39 | 4.27 | 1.14 |
| mistral | 7.00 | 8.48 | 4.07 | 7.81 | 2.93 | 0.67 |

There are three live readings: **(a)** blame tracks the stated indifference;
**(b)** the content asymmetry, where reckless indifference about serious third-party
consequences is blameworthy and indifference about a seating chart is not; and
**(c)** differential selection, since curation kept 14 of 40 moral-good items. Every
authored item states the indifference in one sentence. Varying that sentence while
holding outcome, domain, and question fixed tests whether the clause is what carries
the moral-good elevation.

## 2. Stimuli (`build_dataset.py` → `outputs/indifference_ablation_dataset.csv`)

All 240 authored items have the same shape: S1 is the action, S2 is
"*X did not care at all about the effect … would have on Y.*", and S3 is
"*X knew …*". The build checks this for every item: exactly three sentences, and the
clause appears exactly once, in S2. So the manipulation is fully mechanical and **no
per-item authoring is needed**.

| level | rule | moral-01-bad |
|---|---|---|
| `indifferent` | S2 verbatim (the original item) | …Bill did not care at all about the effect the gadget would have on babies. Bill knew… |
| `omitted` | S2 deleted | Bill released a gadget to make a deadline. Bill knew his gadget would kill babies. |
| `concerned` | "did not care at all about" → "cared a great deal about" | …Bill cared a great deal about the effect the gadget would have on babies. Bill knew… |

Omission is safe because every S3 pronoun refers back to S1 or to the agent, never to
S2 (all 240 checked). Exceptions:
- Two Ngo originals carry source typos in S2: moral-12-bad ("would have rates of
  cancer") and moral-29-good ("the effect would have on the road"). They are kept
  verbatim at `indifferent` and `concerned` so the minimal pair stays exact, and they
  disappear at `omitted`.

The question columns are the pilot's own. None of them mention the clause.
`pilot_selected` marks the 196 curated items, derived from the published
`results_dist` archive, the same way `measurement_selection_audit.py` does it.

The result is 720 rows: 40 per (arm × sign × level) cell.

## 3. Elicitation (`elicit.py`)

- `elicit.py` is a thin wrapper that imports `../nonmoral_pilot/elicit.py` by path. It
  rebinds five module globals (dataset, output path, release string, runner version,
  question list) and calls the pilot's `main()`. The pilot script stays
  byte-identical, so the published pilot rows still match the code their
  `runner_version` names.
- The prompt frame, raw-completion format, and logprob capture are unchanged.
- Seeding uses the pilot's rule with the new release
  `ngo_extensions_indifference_ablation_v1`. The `indifferent` level therefore
  re-elicits the pilot's exact prompts on fresh seeds, which gives a built-in
  test-retest.
- Verified with the fake engine: the seeds match the new release, resume skips
  completed jobs, and the staged cluster bundle passes a smoke test.
- Defaults: the three instruct models, N = 25, and all three questions.

## 4. Analysis plan

- **Score:** `parsed_rating` on parse-ok rows (claim 1). EV is reported only for
  comparison.
- **Scope:** finetuned models, fit per family × question (blame and praise are
  primary).
- **Inference:** `wild_cluster_bootstrap` from `analysis/rq1_v1_1_robustness/lib.py`,
  B = 1999, cluster = `pair_id`, seed 28.
  - G = 40, and every storyline spans all arms, signs, and levels.
- **Coding:**
  - `sign_c` and `arm_c` as in the pilot.
  - `clause_c`: indifferent +0.5 / omitted −0.5.
  - `concern_c`: omitted +0.5 / concerned −0.5.

| id | fit (subset) | term | question it answers |
|---|---|---|---|
| P0 | `~ sign_c*arm_c` (indifferent, curated 196) | `sign_c:arm_c` | Does claim 9 replicate on fresh seeds? This gates everything below. |
| **P1** | `~ arm_c*clause_c` (good sign) | `arm_c:clause_c` | How much of the good-cell domain gap the clause carries |
| P2 | `~ sign_c*arm_c*clause_c` (all) | 3-way | Whether claim 9's full interaction depends on the clause |
| P3 | `~ clause_c` per good arm (moral / prudential / procedural) | `clause_c` | Where the clause matters: third-party vs self vs convention |
| **P4** | `~ selected_c` (indifferent, moral-good, 40 items) | `selected_c` | Reading (c): the 26 curation-dropped items vs the 14 kept. Also re-estimate P1 on the curated subset vs the authored set. |
| P5 | P1 and P3 with `concern_c` | — | Dose-response (secondary) |

- **Multiplicity:** Holm within (family, question) over P1–P4. P5 is exploratory.
- **Also report:** the parse rate per cell. The pilot's moral-good blame cells parse
  poorly for gemma (136 of 350 rows), and differential parse by level would confound
  the fits.

## 5. Predicted patterns

| outcome | P1 | P3 moral-good | P3 nonmoral-good | P4 |
|---|---|---|---|---|
| **The clause carries it** — (a), or (b) as stated | large, + | blame drops a lot at `omitted` (toward the ~0.7–1.2 bad-cell gap) | small drop | — |
| **Content or stakes alone carry it** — a variant of (b) that doesn't need indifference | ≈ 0 | moral-good blame stays ≈ 7 at `omitted` | ≈ 0 | — |
| **(c) selection** | — | — | — | Dropped items blamed less; the authored-40 good-cell gap is much smaller than the curated-14 gap |

The curation scores make (c) plausible on its face. Dropped moral-good items scored
0–3 on moral relevance and kept ones scored 6–10, with nothing in between. One
dropped item, moral-09-good, never got a parseable score.

**Limit: (a) and (b) are not separable with model data.** Both say the model blames
indifference about third-party consequences. Whether that is a bias or correct
judgment is a normative question that needs the human benchmark (PROTOCOL.md arm A).
P3 gives partial leverage: a clause effect confined to the moral arm leans toward (b),
and one present in every arm leans toward (a).

## 6. Cost (CLAUDE.md §4)

720 stimuli × 3 questions × 25 samples comes to 54,000 rows per model. Throughput was
measured from the 2026-08-19 pilot run's row timestamps: about 20 rows/s for
llama/mistral and about 15.5 for gemma.

| configuration | rows | wall (two jobs, in parallel) | GPU-h |
|---|---:|---:|---:|
| **default:** instruct ×3, 3 questions, authored 240, 3 levels | 162,000 | ~1.8 h | ~3.0 |
| blame + praise only | 108,000 | ~1.3 h | ~2.1 |
| drop `concerned` | 108,000 | ~1.3 h | ~2.1 |
| + pretrained (all 6) | 324,000 | ~3.5 h | ~6 |

## 7. Decisions for Parker and Mer

**Decided 2026-09-28 (Parker):** items 1–4 as recommended below: authored 240,
keep `concerned` with the "cared a great deal about" wording, include
intentionality, instruct models only. That is the §6 default: 162,000 rows,
~3 GPU-hours. Item 5's hand-read of the 80 moral `concerned` items was done the
same day: all read grammatically apart from the two inherited source typos
(§2), and the good-outcome reading noted in item 2 is visible as expected.
Items 6–7 are open.

1. **Item set:** authored 240 (recommended — the only way to test (c), and it matches
   human-study arm A) or curated 196 (−18% cost, loses P4).
2. **The `concerned` level:** keep it or not, and its wording. "cared a great deal
   about" is the minimal antonym. Note that it changes more than attitude: with a bad
   outcome it reads as reluctant harm, and with a good outcome as implying the benefit
   was valued, close to intended. `omitted` is the clean contrast; `concerned` costs a
   third of the run for a secondary test.
3. **Questions:** include intentionality (recommended, +50%, parsed-only per claim 1)
   or blame + praise only.
4. **Models:** instruct only (recommended — claim 9 is instruct-only, and pretrained
   blame/praise parse at 25.5–29.9%) or all 6.
5. **Validity check:** no curation gate (gating reintroduces (c)). Instead, a hand
   read of the 80 moral `concerned` items (about 15 minutes). An optional
   manipulation-check question ("how much did X care…") would separate "the model
   ignored the clause" from "registered it but didn't use it."
6. **Lock the analysis first:** commit the P0–P5 script before harvest (recommended,
   given the gameplan's multiplicity concern).
7. **Human-study linkage:** add the `omitted` level to PROTOCOL arm A?
