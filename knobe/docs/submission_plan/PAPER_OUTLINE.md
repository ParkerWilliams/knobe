# Paper outline (2026-09-28)

Target: TMLR. Scope per `SUBMISSION_GAMEPLAN.md` §1 "Paper scope". Claim
numbers are `CLAIMS.md`'s. Supersedes `paper/DRAFT.md`'s structure.

**Venue shape.** TMLR reviews on two questions: are the claims supported by
accurate, convincing and clear evidence, and would some of its audience be
interested. It doesn't review on novelty or a single unified story. So the
paper's job is to state each claim at exactly the strength its evidence
supports, and make the evidence easy to check.

**Format rules** (from TMLR's submission page, 2026-09-28):
- **Length:** any length, but it must be justified by the content, and
  unusually long main texts (appendices not counted) delay review. The ~11
  pages budgeted below is a target, not a limit.
- **Form:** a PDF built from the TMLR LaTeX stylefile and template.
  Appendices go after the references.
- **Reviewers aren't required to read the appendix or supplementary
  material.** So anything a claim rests on must be in the main text. The
  appendix is for backup, not for load-bearing evidence. This matters most
  for claim 5: the main text has to say, in a sentence or two with a number,
  why the bootstrap and not Wald tests, not just point to Appendix A.
- **Supplementary material:** up to 100MB, PDF or ZIP, anonymized. Code and
  data are encouraged. `results_dist/` is 31MB, so the full published data
  fits. Anonymizing means a ZIP without `.git` (commit authors) and without
  identifying strings. As of today, 5 tracked files contain names or local
  paths: `data/authoring/v1.1_candidate/apply_patch.py` and four docs under
  `docs/severity_confound/` and `docs/v1_1_release_process/`. The GitHub
  repo can't be linked during review.
- **Not on that page, check separately:** whether a broader impact
  statement is required.

**Through-line.** Measuring an outcome-valence asymmetry in LLMs depends on
three choices the literature treats as incidental: how the rating is scored,
which question is asked, and which checkpoint is tested. Each choice changes
the answer. The paper shows how much, then reports what survives careful
measurement.

**Working title.** Keep `DRAFT.md`'s C1-led title as a candidate: *How You
Score a Rating Decides What You Find: Outcome-Valence Asymmetries in
Instruction-Tuned Language Models.* Alternative that covers the question
axis too: *The Knobe Effect in LLMs Depends on What You Ask and How You Score
It.*

---

## Abstract (~200 words)

One sentence each: the effect and why LLM audits study it; the design (Ngo's
40 storylines extended with nonmoral and moral-foundation variants, 3
question types, 3 families, pretrained and instruct); the measurement result
(claim 1); tuning (2); dissociation (3) and family differences (4); the
curation finding (10); one line on scope (no human data on these items).

## 1. Introduction (~1 page)

- Knobe effect in humans; LLM replications use Likert elicitation;
  Raimondi et al. (arXiv:2510.12229) report the effect in finetuned models.
- The gap: those studies fix one question, one scoring rule, one checkpoint.
- Contributions, as a numbered list:
  1. Scoring is question-dependent, and parse rate doesn't diagnose it (claim 1).
  2. Instruction tuning increases the asymmetry, by two different routes (claim 2).
  3. Intentionality, blame and praise dissociate on identical items (claim 3),
     and blame-vs-praise sensitivity differs by family (claim 4).
  4. Methods: LLM-reviewer curation with a valence-asymmetric screening question
     silently destroys design balance (claim 10).

## 2. Related work (~0.75 page)

- Knobe effect and its human literature: Knobe 2003; Ngo et al. 2015;
  blame-first accounts (Hindriks); typicality.
- LLMs and moral / cognitive-bias evaluation; Raimondi et al.
- Eliciting ratings from LLMs: parsed answers vs logprob expected values.
- LLMs as stimulus reviewers or judges.

## 3. Design (~2 pages)

| § | content | source |
|---|---|---|
| 3.1 Stimuli | Ngo's 40 harm/help pairs. **Nonmoral extension**: each storyline also in a prudential and a procedural framing, 240 items. **Foundations extension**: harm control + loyalty, authority, fairness, purity, 152 items. The template, including the indifference clause. Figure 1: design schematic with one worked storyline across arms | `nonmoral_pilot/README.md`, `MORAL_FOUNDATIONS_PILOT_PLAN.md` |
| 3.2 Curation | LLM reviewer, thresholds, the two selection rules (per-item vs pair-level). Factual here; the finding is §6 | `configs/curation.yaml`, `selection_report.md` ×2 |
| 3.3 Models, elicitation | Gemma-2-9B, Llama-3.1-8B, Mistral-7B-v0.1, pretrained + instruct; frozen Raimondi frame, raw completion; N=25; sampled temperature; three independent single-turn questions | `elicit.py` ×2, `constants.py` |
| 3.4 Scoring | Parsed rating vs logprob-EV fallback; parsed primary, and why (forward-ref §4) | `parsing.py` |
| 3.5 Inference | Sign effect per arm and cell; wild cluster bootstrap, cluster = storyline, B=1999; Holm within (family, tuning, question); equivalence bounds for nulls. Why the bootstrap: one or two sentences with a number stated here (claim 5), full comparison in Appendix A | `lib.py`, `holm_correct_pilots.py`, `equivalence_bounds.py` |

## 4. Measurement: scoring decides what you find (~1.5 pages) — claim 1

- Table: EV-vs-parsed agreement by question × family (praise .56–.81, blame
  .66–.82, intentionality .15–.42).
- Flip counts: 14/30 intentionality contrasts change significance, 0/30 praise.
- Parse rate doesn't detect it: Gemma parses intentionality better than blame
  and still agrees at .18.
- Both directions of distortion: a retracted wrong-direction pretrained
  effect; Gemma's tuning contrast suppressed (0.11 → 2.32).
- Short practical recommendation for anyone eliciting LLM ratings.
- Figure 2: agreement by question, one panel per family.

## 5. What survives careful measurement (~3 pages)

Ordered intentionality first, then across questions, then blame/praise, so
each section sets up the next.

| § | claim | key evidence | figure / table |
|---|---|---|---|
| 5.1 Instruction tuning increases the asymmetry | 2 | `sign × tuning`: 8/12 significant, 11/12 positive; two routes (Gemma/Mistral installed, Llama's reversed prior eroded) | Fig 3: pretrained vs instruct slopes per family |
| 5.2 Not privileged for harm or morality, in Gemma | 8 | No moral/nonmoral or harm/non-harm interaction in any family; only Gemma's nulls are informative once equivalence-bounded; joint heterogeneity p=.043 caveat | table: bounds vs effect size |
| 5.3 The questions dissociate | 3 | Same items: intentionality shows no domain interaction, blame shows a large one in every family, praise in two. Within-item identification | Fig 4: interaction by question × family |
| 5.4 Blame vs praise differ by family | 4 | Swing comparison; Gemma/Llama blame > praise, Mistral inverted; parsed as the common scale | table: swings |
| 5.5 An open pattern: blame in moral scenarios | 9 | Moral-good blame stays high; three readings (indifference-tracking, content asymmetry, differential selection), none ruled out; the third-party design limit | table: cell means |

State in-line: claims 3, 4 and 9 come from the nonmoral extension only, and
are exploratory in the multiplicity sense.

## 6. A methodological finding: curation attrition (~0.75 page) — claim 10

- Nonmoral: moral-good survives 35% vs 82–98% elsewhere, because the screening
  question names only the violation pole.
- Foundations: pair-level gating keeps every cell balanced.
- Same reviewer, same week, two rules. Generalization: anyone screening
  stimuli with an LLM on a valence-asymmetric question hits this silently.
- Table: survival by arm × sign, both extensions.

## 7. Additional finding: typicality in a separate stimulus set (~0.5 page) — claim 6

- Main run, finetuned checkpoints, the project's own crossed typicality
  factor. Gemma and Mistral: the bad > good gap is larger for typical actions,
  the reverse of the pattern reported in the human literature; Llama absent.
- In the same paragraph: separate stimulus set, small effects, family-specific
  decomposition, no human ratings on these items.
- One sentence pointing to Appendix B for why the main run's own headline
  comparison isn't reported.

## 8. Discussion and limitations (~1.25 pages)

- What "the asymmetry" means for an LLM depends on question, family and
  checkpoint. Audits of one question don't license claims about another.
- Limitations, stated plainly:
  - no human data on these items
  - three 7–9B families
  - raw-completion prompting of instruct models, and the answer loss that
    comes with it (Gemma ~45%)
  - small storyline counts (G=6–40) and exploratory status
  - single-dataset support for claims 3 and 4
  - claim 9's third-party design limit

## 9. Conclusion (~0.25 page)

## Broader impact statement

LLM moral-judgment audits as evidence for deployment decisions; the risk
that a scoring choice produces or erases a bias finding.

## Appendices

- **A.** Asymptotic inference is overconfident at these cluster counts (claim 5): Wald/LRT vs bootstrap.
- **B.** The main run and why its moral/nonmoral comparison isn't reported (claim 11): severity confound, 21/21 storylines.
- **C.** Full result tables, both scorings, Holm columns.
- **D.** Stimulus examples, every arm.
- **E.** Curation prompts, thresholds, selection reports; the parse-failure exclusions from `verify_curation_provenance.py`.
- **F.** Parse-failure breakdown (`parse_failure_breakdown.csv`).
- **G.** Reproducibility: seeds, model revisions, commands, commit per table.

---

## Where pending work lands

| step (from the 2026-09-28 assessment) | changes |
|---|---|
| Failure rates by sign/arm (no GPU) | §8 limitation wording; Appendix F. If failures are lopsided, §4 and §5 need a selection caveat |
| Holm on the tuning table (needs grouping sign-off) | §5.1: Llama's harm cell may not survive |
| Chat-format diagnostic (GPU) | §8 limitation becomes a robustness result, or §4 gains a finding |
| MF blame/praise (GPU) | §5.3–5.5 move from one dataset to two; claim 9's selection reading addressed |
| Mistral revision check | Claim 7 enters §7 or Appendix B, or stays out |

Nothing in this table blocks drafting §1–§4 and §6–§7 now.
