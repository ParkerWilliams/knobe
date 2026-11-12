# Jev as the subject, asked natively (2026-11-12)

> **Protocol status.** These results were made at commit 983ef56, under the question wordings from before Mer's 2026-10-22 amendments:
> - Intentionality w1 was Ngo's bare "Did X intentionally …?" (now w1a, which adds "0 (definitely not) to 10 (definitely yes)").
> - `fnd_fairness` had its old wording.
>
> All other cells are unchanged. A rerun under the current wordings was blocked on 2026-11-12: the OpenRouter key had hit its $100 total limit (HTTP 403). The merged code refuses to analyze these answers, because their recorded request hashes no longer match the current questions. To rerun, raise the key limit, set the old `outputs/elicit/jev_native_*.jsonl` files aside with their manifests, then run the commands under Reproduce.

**Question (Parker, 2026-11-12):** is the Knobe effect present in Jev itself, with no LLM output and no wrapper?
Each moral-bias question is posed as Jev's own multiple-choice ("scantron") question.

**Answer:** yes. Jev rates a bad foreseen side effect as far more intentional and blameworthy than a good one, and gives almost no praise for the good one. That is the original asymmetry, in Ngo's 80 items and in both pilot sets. The asymmetry is just as large for prudential and procedural side effects as for moral ones, so for Jev it is not specific to moral content.

## What Jev was asked

Code: `kmp/jev_native.py` (the question sheet), `tools/jev_native.py` (elicit / analyze / compare), tests in `tests/test_jev_native.py`.

The cells are the same as the chat models': every item × question × wording from `protocol.subject_qkeys` × `protocol.QUESTIONS`, with the wordings unchanged. Each call carries one question:

```json
{"model": "typesafe/jev-1.14",
 "state": {"scenario": "Bill released a gadget to make a deadline. Bill did not care at all about the effect the gadget would have on babies. Bill knew his gadget would kill babies."},
 "questions": {"rating": {"type": "choice",
   "instructions": "How blameworthy is Bill for this, on a scale from 0 (not at all) to 10 (extremely)?",
   "criteria": {"0": "0 (not at all)", "1": "1", "2": "2", "...": "...", "9": "9", "10": "10 (extremely)"}}}}
```

- **State.** Jev gets the scenario only. There is no instruction line, no "Scenario: / Question: / Answer:" frame and no worked examples.
- **Bubbles.** There are eleven bubbles, 0–10. A number the wording anchors carries the wording's own words, and the others are bare numbers. Intentionality w1 ("Did X intentionally …?") has no anchors, so it gets eleven bare bubbles, just as the chat models got a bare 0–10 question. There is no "none" option.
- **Calls.** There is one call per question, with sample 0 only. Jev never sees a question's other wordings.
- **Readouts.** Each answer gives the top bubble (ties go to the lower number) and the expected value (EV) over 0–10. Reversed wordings are recoded 10 − x through `kmp.frame.join_items`, the same coding the chat models get.
- **Analysis.** It reuses `analysis/first_look.sign_effects`, `analysis/arm_effects.arm_effects` and the `kmp.checks` tables on Jev's answers directly. There is no reply text, `kmp.answer` or `ResultRecord` in between. The fits are a wild cluster bootstrap, B = 1999, clustered by storyline, with first_look's seeds. p-values are unadjusted.

**The wrapped run is not this test.** The 2026-10-22 run (`tools/jev_subject.py`, tables `jevsubj_*`) gave Jev the chat models' whole prompt as its state, and one meta-question ("answer the question at the end of `prompt`") over the options "The answer is 0." … "The answer is 10.". It then sent the pick back through the chat-reply pipeline. It is kept only as a contrast.

## Run

typesafe/jev-1.14 resolved to -20261014 for every answer. Sheet spec `jev_native.SPEC`. Each row and the manifest carry the hash of every request.

| set | questions | answered | cost |
|---|---|---|---|
| Ngo verbatim (80 items) | 1,040 | 1,040 | $0.022 |
| pilot nonmoral (240) | 3,120 | 3,120 | $0.067 |
| pilot foundations (152) | 1,764 | 1,764 | $0.039 |

There were 0 errors and 0 answers with no probability on any bubble.

## Results

In the tables below, β is the bad-minus-good coefficient (`sign_c`) and p is the wild-bootstrap p-value. "Normal wordings" leaves out the reversed wording (see the reversed-wording note below the tables). The tables are in `outputs/first_look/jevnat_<set>[_ev][_normal]_sign_effects.csv`.

**Ngo's 80 items, intentionality**

| reader | wordings | bad | good | β | p | pairs bad > good |
|---|---|---|---|---|---|---|
| top bubble | all 3 | 9.89 | 0.92 | +8.98 | < .001 | — |
| top bubble | normal | 9.84 | 0.75 | +9.09 | < .001 | 39 / 40 (1 level, 0 below) |
| EV | all 3 | 7.84 | 2.69 | +5.15 | < .001 | — |
| EV | normal | 7.72 | 2.48 | +5.24 | < .001 | — |

**Ngo's 80 items, blame and praise (normal wordings, top bubble):**
- Blame: bad 9.50 vs good 1.05, β +8.45, with 39 / 40 pairs bad > good.
- Praise: good 0.59 vs bad 0.00, β −0.59. 21 pairs are level at 0 and in 19 the good side effect gets more praise.
- With EV: blame +6.52, praise −2.18.

**Pilot sets, intentionality (normal wordings, top bubble), storylines with bad > good:**
- nonmoral: moral 38/40, prudential 33/40, procedural 36/40.
- foundations: harm 27/30, authority 13/13, fairness 9/13, loyalty 12/13, purity 7/7.

**Arm contrast** (`arm_effects`, all wordings). Positive means a larger bad-vs-good gap in the moral or harm arm.

| set | contrast | reader | β | p |
|---|---|---|---|---|
| nonmoral | intentionality, moral vs rest | top bubble | +1.13 | .064 |
| nonmoral | intentionality, moral vs rest | EV | +0.10 | .78 |
| foundations | intentionality, harm vs rest | top bubble | −0.17 | .87 |
| foundations | intentionality, harm vs rest | EV | −1.68 | .005 (smaller in harm) |

So for Jev the asymmetry is not specific to moral content.

**Reversed wordings** (`checks/jevnat_<set>/anchor_agreement.csv`, `wording_means.csv`):
- **Intentionality.** Jev follows the reversed sheet: normal vs reversed r = .85–.95.
- **Blame.** Jev follows it only partly: r = .25–.49, mean difference −3.2 to −5.4.
- **Praise.** Jev reads it backwards. It takes "0 (extremely praiseworthy)" as "none": r = −.21 to −.44, mean difference +6.8 to +8.3.

This is why the pooled praise "validity" check fails (`praise_good_minus_bad` < 0) and the pooled blame and praise effects are diluted. On the normal wordings the direction is right everywhere. On the native sheet blame w3r is read better than in the wrapped run (Ngo bad − good after recode: wrapped −8.9, native +2.5).

**Native vs wrapped**, Ngo intentionality: β +8.73 → +8.98 (EV +5.65 → +5.15). The headline effect does not depend on the wrapper. Pooled blame moves the most (+2.86 → +6.48), entirely through the reversed wording. Side-by-side tables: `outputs/first_look/jevnat_vs_wrapped_*`.

## Caveats

- **One call per question.** Jev's probabilities stand in for the spread of samples, so the top bubble snaps to the scale ends. EV is the closer analog of a chat model's mean.
- **Pilot items** were run as written (`--allow-draft`), as in the OpenRouter runs.
- **Reversed wordings.** Pooled tables include the reversed wordings; the "normal" tables are the sensitivity check. The arm contrasts above are pooled.
- **No inference across models** (Jev vs the chat models) is drawn here.

## Reproduce (from the study folder; elicit needs OPENROUTER_API_KEY)

```
../../.venv/bin/python tools/jev_native.py elicit --items stimuli/ngo_verbatim.csv --out outputs/elicit/jev_native_ngo_verbatim.jsonl
../../.venv/bin/python tools/jev_native.py elicit --items stimuli/pilot/pilot_nonmoral.csv --allow-draft --out outputs/elicit/jev_native_pilot_nonmoral.jsonl
../../.venv/bin/python tools/jev_native.py elicit --items stimuli/pilot/pilot_foundations.csv --allow-draft --out outputs/elicit/jev_native_pilot_foundations.jsonl
../../.venv/bin/python tools/jev_native.py analyze --items stimuli/ngo_verbatim.csv --results outputs/elicit/jev_native_ngo_verbatim.jsonl --name jevnat_ngo_verbatim
../../.venv/bin/python tools/jev_native.py analyze --items stimuli/pilot/pilot_nonmoral.csv --results outputs/elicit/jev_native_pilot_nonmoral.jsonl --name jevnat_pilot_nonmoral --experiment nonmoral
../../.venv/bin/python tools/jev_native.py analyze --items stimuli/pilot/pilot_foundations.csv --results outputs/elicit/jev_native_pilot_foundations.jsonl --name jevnat_pilot_foundations --experiment foundations
../../.venv/bin/python tools/jev_native.py compare --native outputs/first_look/jevnat_ngo_verbatim_sign_effects.csv --wrapped outputs/first_look/jevsubj_ngo_verbatim_sign_effects.csv --out outputs/first_look/jevnat_vs_wrapped_ngo_verbatim_sign_effects.csv
```

The other two comparisons (EV and wording means) are the same `compare` call on `jevnat_ngo_verbatim_ev_sign_effects.csv` vs `jevsubj_ev_ngo_verbatim_sign_effects.csv`, and on `checks/jevnat_ngo_verbatim/wording_means.csv` vs `checks/jev_subject_ngo_verbatim/wording_means.csv`. The answers themselves (`outputs/elicit/jev_native_*.jsonl`) are local and gitignored, as are all the elicit files; their manifests are committed.
