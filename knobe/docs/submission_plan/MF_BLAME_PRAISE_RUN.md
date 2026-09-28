# MF pilot blame/praise: is it worth running, and what else to change (2026-09-28)

Decision memo for `SUBMISSION_GAMEPLAN.md` §5 item 6. The code is staged
(`a5e12a6`, `df5d8e6`); nothing has been elicited. Claim numbers refer to
`CLAIMS.md`.

## 1. Do the intentionality results earn the run?

**The bar the design doc set.** `MORAL_FOUNDATIONS_PILOT_PLAN.md` §2 scoped
blame/praise out because they answer a mechanism question (*why* the
asymmetry happens), which "isn't earned" until the pilot shows the asymmetry
exists outside harm at all. "Revisit if results are suggestive enough."

**Whether it's met.** For instruction-tuned Gemma and Mistral, yes, clearly.
For Llama, no. From `sign_wcb_parsed.csv` (parsed scoring, WCB B=1999,
cluster=pair_id; Holm from `sign_wcb_holm_summary_parsed.csv`):

| finetuned | harm (G=30) | non-harm pooled (G=26) | harm vs non-harm (G=34) |
|---|---|---|---|
| Gemma | **4.13** (p<.001) | **4.44** (p<.001) | −0.30 (p=.70) |
| Mistral | **1.75** (p<.001) | **1.00** (p=.010; Holm .020) | 0.75 (p=.07) |
| Llama | 0.66 (p=.10) | 0.29 (p=.39) | 0.37 (p=.44) |

For Gemma the non-harm effect is as large as the harm effect. Pretrained
checkpoints show nothing that survives correction except scattered Mistral
cells. The 2026-08-21 log entry reported the asymmetry generalizing "in all
three instruct models." That was under logit-EV scoring. Under parsed
scoring, Llama drops out (consistent with claim 8), so the decision should
rest on the table above, not on that entry.

**The bar is also not really the reason to run it.** Meeting the design
doc's condition says blame/praise is *allowed*. What makes it *worth it* is
that three claims currently rest on a single dataset, and this run is the
only cheap way to test all three on a second one:

| claim | status now | what the MF blame/praise run tests |
|---|---|---|
| 3: the three questions dissociate | nonmoral only | The MF pilot already has the intentionality half: no harm vs non-harm interaction in any tuned family. Claim 3 predicts blame *does* show a domain interaction on the same items. Same within-item, cross-question identification as the original, so item composition is differenced out. |
| 4: blame vs praise sensitivity differs by family | nonmoral only | Whether Mistral's praise > blame inversion, the most interpretable part of claim 4, recurs on 126 independently authored items. |
| 9: blame is outcome-insensitive in moral scenarios | nonmoral only, 3 rival readings | Reading (c), differential selection, can't arise here: MF used pair-level gating, so every cell kept bad/good balance (`selection_attrition.csv`). If moral-good blame is again insensitive to outcome, (c) is ruled out as the whole story. |

**What each outcome would mean.** Any result is informative:

- *Replicates:* claims 3 and 4 become two-dataset results. Claim 9 loses its
  selection rival, which is the upgrade the gameplan's item 2 was trying to
  reach by other means.
- *Fails to replicate:* the claims are specific to the nonmoral stimulus set,
  and the paper has to say so. Better learned before submission than from a
  reviewer.

**Limits on what it can show.**
- Per-foundation blame/praise will be exploratory only: G=6–10 storylines per
  foundation. The testable contrast is harm vs pooled non-harm (G=34).
- Llama contributes to claim 4 only. It has no intentionality asymmetry here
  to explain.
- Pretrained cells contribute nothing (see 2a).
- The design limit in claim 9 carries over. MF non-harm violations still mostly
  fall on third parties, so the run doesn't separate moral domain from who
  bears the consequence.

**Verdict: run it.** The strongest reason is replicating claims 3, 4 and 9.
Extending intentionality past harm is the weaker one.

## 2. What to change for the run, and what not to

**Governing constraint.** The run's value is almost entirely *comparative*:
blame/praise vs the MF intentionality rows already collected (claim 3
analogue), and vs the nonmoral pilot's blame/praise (claims 4, 9). Anything
that changes the primary measurement relative to those two datasets destroys
the comparison the run exists to make. So the primary pass stays exactly as
it is, and any improvements go in as separately labeled additions.

### 2a. Change: drop the pretrained checkpoints

Run `--model-keys` with the three instruct keys only: 126 × 2 × 3 × 25 =
**18,900 rows** instead of 37,800. There is no pretrained blame/praise claim
anywhere in the project. Llama and Mistral pretrained parse blame/praise at
25–30%. Gemma pretrained parses at 63–65%, but its EV-vs-parsed agreement
is r = .18–.23. `CLAIMS.md` already lists "any pretrained blame/praise
result" under *what we do not claim*.

### 2b. Keep fixed

| setting | value | why fixed |
|---|---|---|
| prompt frame | `RAIMONDI_PROMPT_TEMPLATE`, raw completion | identical to MF intentionality and nonmoral blame/praise |
| question wording | frozen `constants.QUESTIONS` | same; reused not rewritten (`a5e12a6`) |
| N | 25 | the nonmoral pilot's blame/praise used 25. The main run used 50 for blame/praise, but power here is limited by the number of storylines (G), not samples per item, so 50 buys little |
| `MAX_TOKENS` | 10 | changing it changes which rows parse, relative to both comparison datasets. Most failures aren't truncation (blank output, fill-in blanks), but some are: Gemma-instruct opens with "**Explanation:**" in 7–12% of rows and hits the limit before giving a number (2c). Test a longer limit in the diagnostic pass, not the primary one |
| `RELEASE`, seeding | unchanged | keeps published rows' seeds; new prompt_ids get their own (verified 0 collisions) |
| item set | the 126 selected | re-curating would change the items relative to the intentionality rows |
| scoring | decided at analysis time; parsed primary | per claim 1, and the logprobs are captured either way |

### 2c. Consider adding: a chat-format diagnostic pass

This is the one change I think is worth discussing. It affects every pilot
result, not just this run.

**The problem.** Every pilot and main-run elicitation sends instruct models a
raw completion prompt, no chat template (`nonmoral_pilot/elicit.py` docstring;
every `configs/run_main_*.yaml` lists `formats: [raw]`). The spec designates
chat format as a robustness pass, and it has **never been run anywhere in
the project**. The parse failures look like what instruct models do on
untemplated input. Examples from the nonmoral pilot's finetuned rows:

Parse-failure breakdown, instruct models, both pilots pooled, as % of all
rows (`analysis/ngo_extensions/parse_failure_breakdown.py`, on `results_dist/`):

| model | question | failed | blank output | fill-in blank | starts explaining, cut off | other |
|---|---|---:|---:|---:|---:|---:|
| Gemma | blame | 47.0% | 19.7% | 11.1% | 6.9% | 9.3% |
| Gemma | praise | 45.7% | 16.9% | 7.6% | 9.3% | 11.9% |
| Gemma | intentionality | 43.4% | 4.7% | 16.1% | 11.8% | 10.8% |
| Llama | blame | 22.7% | 0.0% | 15.5% | 0.1% | 7.1% |
| Llama | praise | 20.6% | 0.0% | 16.0% | 0.0% | 4.4% |
| Llama | intentionality | 29.8% | 0.0% | 26.2% | 0.0% | 3.5% |
| Mistral | all three | 1.1–1.8% | — | — | — | — |

- **Blank output** (Gemma only): `' \n'`, `'  \n\n'`. A line break, then the
  model stops. Not truncation.
- **Fill-in blank:** `' _______'`, `' __\n\n**Explanation:**…'`. The model
  reads "Answer:" as a worksheet blank to leave for the reader.
- **Starts explaining, cut off** (mostly Gemma): `'\n\n\n**Explanation:**\n\nThe
  scenario clearly states that'`. The only truncation-shaped failure: the
  10-token limit runs out before a number.
- **Other:** instruction echoes (`'Please remember to justify your answer
  briefly.'`), yes/no verdicts (Llama, intentionality only), refusals
  (`'I cannot provide a numerical answer'`), and noise.

The first two are what untemplated instruct models typically do. The third
is a max-token effect. None is random with respect to item or question:
Gemma's blank rate is 3.5–4× higher for blame/praise than for intentionality.

Parse failures are systematic, not random: claim 1 shows the fallback score
doesn't recover them. So "Gemma drops ~45% of its answers" is a selection
concern a reviewer can raise against every Gemma cell. It also bears on
claim 7, where Mistral chat-template handling is an open hypothesis.

**The option.** A small diagnostic, run separately from the primary pass:

- finetuned only, all three questions, MF items, N=5: 126 × 3 × 3 × 5 =
  **5,670 rows**
- identical frame text, sent as one user message (the production
  `render.py` "chat" shape)
- optionally a third arm: raw format with a longer `MAX_TOKENS` (e.g. 64),
  which isolates the truncated-explanation failures from the templating
  ones. Same size again

This answers two questions. Does templating (or a longer limit) fix Gemma's
and Llama's parse rates? And do the parsed sign effects move when it does? If they don't
move, that's one sentence in the paper that closes a reviewer objection. If
they do, we need to know before submission.

**Cost and risks.**
- *New code:* the pilot `elicit.py` only sends `text`, so this needs the
  `messages` path. That path exists in `elicit_vllm.VllmEngine` and
  production `render.py`; it's plumbing, not new machinery.
- *Pooling risk:* chat rows **must go to a separate output file** (e.g.
  `elicit_results_chat.jsonl`). `load_frame` filters by question, not by
  format, so rows in the same file would be silently pooled into every
  table. That's the same failure `df5d8e6` just fixed for questions.
- *Scope:* doing this properly for the paper means both pilots. Running the
  MF diagnostic first tells us whether that's needed.

**Recommendation:** add it to the same GPU session if the plumbing can be
done and fake-engine verified beforehand. Don't hold the primary blame/praise
run for it.

### 2d. Considered, not recommended for this run

- **Indifference-clause ablation (gameplan item 5).** It's now the leading test
  for claim 9, but it needs new stimuli (clause present / absent / active
  concern) and its own design pass. Bundling it would delay item 6 behind
  authoring. Better run separately.
- **Mistral revision check (item 4).** No run change needed: every row
  already records `model_revision`, so the check compares recorded hashes
  against Raimondi's and needs no GPU.
- **Re-curating the 3 MF pairs dropped on reviewer parse failures**
  (loyalty-19, loyalty-30, purity-39). This would change the item set
  relative to the intentionality rows. Report it as a limitation instead.

### 2e. Change: write the analysis plan before the run

Given this project's retractions (the "anti-Knobe" finding, moral
specificity, the praise sign-convention error), commit the analysis plan
before any blame/praise row exists. Proposed contents:

1. **Primary (claim 3 analogue):** `sign_c:arm_c`, harm vs non-harm pooled,
   q_blame, per tuned family. Claim 3 predicts it is non-zero, in the
   direction of the nonmoral pilot's result: a smaller blame outcome swing in
   the harm (moral-core) arm. The sign of `arm_c`'s coding must be fixed in
   the plan, not read off afterwards.
2. **Primary (claim 4 replication):** blame swing vs praise swing per family
   via `blame_praise_swing.py`'s method. Prediction: Gemma and Llama blame >
   praise, Mistral praise > blame.
3. **Secondary (claim 9 analogue):** good-outcome blame in harm vs non-harm,
   by sign (the `domain_gap_decomposition` method).
4. **Exploratory:** per-foundation cells; q_praise interactions.
5. **Scoring and multiplicity:** parsed primary, EV reported alongside. Holm
   within (family, tuning, question), matching `holm_correct_pilots.py`.

## 3. Before launching

1. Regenerate `mf_pilot_dataset_selected.csv` (`curate_foundation_relevance.py
   --select`). The local copy predates the q_blame/q_praise columns, and
   `elicit.py` exits without them.
2. `verify_curation_provenance.py` currently fails its cell-by-cell check on
   this machine: missing `q_blame`/`q_praise` (MF) and `moral_relevance`
   (nonmoral) columns in the local selected CSVs. The item sets match
   exactly. Fix the check to compare shared columns before relying on it
   again.
3. Fake-engine run with the instruct keys only; confirm 18,900 jobs and 0
   job_id collisions.
4. Per CLAUDE.md §4, estimate GPU time from the 2026-08-19 run's timestamps
   before launching. At 18,900 rows it should be well under an hour; the
   nonmoral README puts the whole 1.8M-completion main run at "a few
   GPU-hours".
5. After the run: republish `results_dist/results_pilot_moral_foundations_all.jsonl.gz`
   with the new rows, and update `PROTOCOL.md` §8 item 5. Its reasoning
   for leaving foundations blame/praise out of the human study reverses.
