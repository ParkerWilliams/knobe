# Jev as the subject, asked natively (2026-11-12)

> **Protocol status.** These results use the current question wordings, including Mer's 2026-10-22 amendments:
> - Intentionality w1 is w1a: Ngo's "Did X intentionally …?" plus "0 (definitely not) to 10 (definitely yes)".
> - `fnd_fairness` names both poles.
>
> The run was made on 2026-11-12, after merging Mer's work (02140a8). It replaces the first native run (983ef56), which used the older wordings. That run's answers are kept locally as `outputs/elicit/jev_native_<set>_pre1022.jsonl`, and their manifests are committed beside them. The 5,426 questions asked word for word in both runs are the test-retest check below.

A short shareable version with verbatims (scenarios, questions and Jev's answers) is [`JEV_NATIVE_REPORT.html`](JEV_NATIVE_REPORT.html), written by `tools/jev_native_report.py`.

**Question (Parker, 2026-11-12):** is the Knobe effect present in Jev itself, with no LLM output and no wrapper?
Each moral-bias question is posed as Jev's own multiple-choice ("scantron") question.

**Answer:** yes. Jev rates a bad foreseen side effect as far more intentional and blameworthy than a good one, and gives almost no praise for the good one. That is the original asymmetry. It shows in Ngo's 80 items and in both pilot sets. The asymmetry is just as large for prudential and procedural side effects as for moral ones, so for Jev it is not specific to moral content.

## What Jev was asked

Code: `kmp/jev_native.py` (the question sheet), `tools/jev_native.py` (elicit / analyze / compare / retest), tests in `tests/test_jev_native.py`.

The cells are the same as the chat models': every item × question × wording from `protocol.subject_qkeys` × `protocol.QUESTIONS`, with the wordings unchanged. Each call carries one question:

```json
{"model": "typesafe/jev-1.14",
 "state": {"scenario": "Bill released a gadget to make a deadline. Bill did not care at all about the effect the gadget would have on babies. Bill knew his gadget would kill babies."},
 "questions": {"rating": {"type": "choice",
   "instructions": "How blameworthy is Bill for this, on a scale from 0 (not at all) to 10 (extremely)?",
   "criteria": {"0": "0 (not at all)", "1": "1", "2": "2", "...": "...", "9": "9", "10": "10 (extremely)"}}}}
```

- **State.** Jev gets the scenario only. There is no instruction line, no "Scenario: / Question: / Answer:" frame and no worked examples.
- **Bubbles.** There are eleven bubbles, 0–10. A number the wording anchors carries the wording's own words, and the others are bare numbers. Since the amendment every wording has anchors; intentionality w1a's are "0 (definitely not)" and "10 (definitely yes)". There is no "none" option.
- **Calls.** There is one call per question, with sample 0 only. Jev never sees a question's other wordings.
- **Readouts.** Each answer gives the top bubble (ties go to the lower number) and the expected value (EV) over 0–10. Reversed wordings are recoded 10 − x through `kmp.frame.join_items`, the same coding the chat models get.
- **Analysis.** It reuses `analysis/first_look.sign_effects`, `analysis/arm_effects.arm_effects` and the `kmp.checks` tables on Jev's answers directly. There is no reply text, `kmp.answer` or `ResultRecord` in between. The fits are a wild cluster bootstrap, B = 1999, clustered by storyline, with first_look's seeds. p-values are unadjusted.

**The wrapped run is not this test.** The 2026-10-22 run (`tools/jev_subject.py`, tables `jevsubj_*`) gave Jev the chat models' whole prompt as its state, plus one meta-question ("answer the question at the end of `prompt`") over the options "The answer is 0." … "The answer is 10.". It then sent the pick back through the chat-reply pipeline. It is kept only as a contrast.

## Run

typesafe/jev-1.14 resolved to -20261014 for every answer. Sheet spec `jev_native.SPEC`. Each row and the manifest carry the hash of every request.

| set | questions | answered | cost |
|---|---|---|---|
| Ngo verbatim (80 items) | 1,040 | 1,040 | $0.022 |
| pilot nonmoral (240) | 3,120 | 3,120 | $0.067 |
| pilot foundations (152) | 1,764 | 1,764 | $0.039 |

There were 0 errors and 0 answers with no probability on any bubble.

## Results

In the tables below, β is the bad-minus-good coefficient (`sign_c`) and p is the wild-bootstrap p-value. "Normal wordings" leaves out the reversed wording (see the reversed-wording note below the tables). The tables are in `outputs/first_look/jevnat_<set>[_ev][_normal]_sign_effects.csv`, and the pair counts are in `outputs/checks/jevnat_<set>/pair_direction.csv`.

**Ngo's 80 items, intentionality**

| reader | wordings | bad | good | β | p | pairs bad > good |
|---|---|---|---|---|---|---|
| top bubble | all 3 | 9.88 | 0.93 | +8.95 | < .001 | — |
| top bubble | normal | 9.83 | 1.03 | +8.80 | < .001 | 37 / 40 (1 level, 2 below) |
| EV | all 3 | 8.03 | 2.67 | +5.35 | < .001 | — |
| EV | normal | 7.95 | 2.47 | +5.49 | < .001 | — |

**Ngo's 80 items, blame and praise (normal wordings, top bubble):**
- Blame: bad 9.55 vs good 0.98, β +8.58, with 39 / 40 pairs bad > good and 1 level.
- Praise: good 0.56 vs bad 0.00, β −0.56. 22 pairs are level at 0, and in 18 the good side effect gets more praise.
- With EV: blame +6.56, praise −2.13.

**Pilot sets, intentionality (normal wordings, top bubble), storylines with bad > good:**
- nonmoral: moral 37/40, prudential 32/40, procedural 30/40. No prudential or procedural storyline goes the other way.
- foundations: harm 25/30, authority 13/13, fairness 9/13, loyalty 12/13, purity 6/7.

**Arm contrast** (`arm_effects`, all wordings). Positive means a larger bad-vs-good gap in the moral or harm arm.

| set | contrast | reader | β | p |
|---|---|---|---|---|
| nonmoral | intentionality, moral vs rest | top bubble | +1.26 | .073 |
| nonmoral | intentionality, moral vs rest | EV | +0.12 | .73 |
| foundations | intentionality, harm vs rest | top bubble | −0.68 | .52 |
| foundations | intentionality, harm vs rest | EV | −1.73 | .004 (smaller in harm) |

So for Jev the asymmetry is not specific to moral content.

**Reversed wordings** (`checks/jevnat_<set>/anchor_agreement.csv`, `wording_means.csv`):
- **Intentionality.** Jev follows the reversed sheet: normal vs reversed r = .92–.99.
- **Blame.** Jev follows it only partly: r = .32–.54, mean difference −3.3 to −5.5.
- **Praise.** Jev reads it backwards. It takes "0 (extremely praiseworthy)" as "none": r = −.22 to −.40, mean difference +6.8 to +8.2.

This is why the pooled praise "validity" check fails in all three sets (`praise_good_minus_bad` < 0), and why the pooled blame and praise effects are diluted. On the normal wordings the direction is right everywhere. On the native sheet blame w3r is read better than in the wrapped run (Ngo bad − good after recode: wrapped −8.9, native +2.6).

**Native vs wrapped**, Ngo intentionality: β +8.73 → +8.95 (EV +5.65 → +5.35). The headline effect does not depend on the wrapper. Pooled blame moves the most (+2.86 → +6.58), entirely through the reversed wording. Side-by-side tables: `outputs/first_look/jevnat_vs_wrapped_*`. The wrapped run predates the amendments, so its intentionality w1 is the old bare wording.

## What the amendments changed

These are wording means, bad − good, comparing the first native run with this one (`checks/jevnat_<set>[_ev]/wording_means.csv`).

| question | reader | Ngo | nonmoral | foundations |
|---|---|---|---|---|
| intentionality w1 → w1a | top bubble | 9.50 → 8.65 | 8.62 → 7.49 | 8.55 → 7.93 |
| intentionality w1 → w1a | EV | 4.44 → 5.09 | 4.38 → 4.81 | 5.08 → 5.81 |
| `fnd_fairness` (fairness arm) | top bubble | — | — | 2.31 → 0.00 |

- **w1a.** The anchors shift Jev's answers in a consistent direction, but which way the gap moves depends on the readout.
  - Top bubble, good versions: some move up off 0. Every good-version top bubble that changed went up, 28 of 28 across the three sets. On the unchanged wordings, changes go both ways.
  - Top bubble overall: the gap narrows by 0.6–1.1.
  - EV, bad versions: they gain about +0.56 in every set, as mass moves onto "10 (definitely yes)". So the EV gap widens by 0.4–0.7.
  - Unchanged wordings move by at most 0.16 in EV.
  - Pooled intentionality barely moves (Ngo top bubble +8.98 → +8.95). That is because w2 and w3r, asked word for word, happened to move the other way by 0.3–0.5 on the top bubble.
- **`fnd_fairness`.** The question now asks about "fair or unfair treatment". Jev gives both versions of every fairness item a 10, where before the good versions averaged 7.69. That is what the amendment was for: the check now asks about the domain, not the direction.
- **Everything else** was asked word for word both times, so any change there is run-to-run variation. For example, Ngo normal-wording blame went from +8.45 to +8.58, praise from −0.59 to −0.56, and significance from +1.68 to +1.75.

## Test-retest: Jev is not deterministic

5,426 questions were asked word for word in both native runs, with the same request hash and the same -20261014 snapshot. Tables: `outputs/checks/jevnat_retest_<set>.csv`, from `tools/jev_native.py retest`.

| set | questions | top bubble repeats | top moves ≥ 3 | EV r | mean \|EV change\| | max | identical probabilities |
|---|---|---|---|---|---|---|---|
| Ngo | 960 | 92.5% | 2.0% | .996 | 0.18 | 2.11 | 14% |
| nonmoral | 2,880 | 92.3% | 2.1% | .996 | 0.18 | 2.37 | 9% |
| foundations | 1,586 | 91.9% | 2.5% | .995 | 0.20 | 1.82 | 8% |

- **Answers vary between calls.** The same request comes back with different probabilities most of the time. About one top bubble in thirteen changes, usually to a neighbouring bubble when two are close.
- **The EV is stable.** r ≈ .995 across runs, so the EV is the steadier readout per question.
- **Per question:** praise's top bubble repeats least (r .82–.83), and significance has the most near-ties (81–83% repeat).
- **What it means for the effects:** on blame, praise and significance, which were asked word for word in both runs, β moved by up to 0.24 on the top bubble and by at most 0.07 on the EV. That is small beside the intentionality and blame effects. It is not small beside the effects near zero, though. Ngo's pooled praise on the top bubble went from +0.35 (p .063) to +0.58 (p .003) between the two runs, so a top-bubble p-value near .05 should not be read as settled. The EV is the readout to quote for small effects.

## Caveats

- **One call per question.** Jev's probabilities stand in for the spread of samples, so the top bubble snaps to the scale ends. EV is the closer analog of a chat model's mean, and it is also the more repeatable readout (above).
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
../../.venv/bin/python tools/jev_native.py retest --first outputs/elicit/jev_native_ngo_verbatim_pre1022.jsonl --second outputs/elicit/jev_native_ngo_verbatim.jsonl --out outputs/checks/jevnat_retest_ngo_verbatim.csv
```

The other two comparisons (EV and wording means) are the same `compare` call:
- on `jevnat_ngo_verbatim_ev_sign_effects.csv` vs `jevsubj_ev_ngo_verbatim_sign_effects.csv`;
- on `checks/jevnat_ngo_verbatim/wording_means.csv` vs `checks/jev_subject_ngo_verbatim/wording_means.csv`, written to `first_look/jevnat_vs_wrapped_ngo_verbatim_wording_means.csv`.

`retest` is run the same way for the two pilot sets.

The answers themselves (`outputs/elicit/jev_native_*.jsonl`) are local and gitignored, as are all the elicit files. Their manifests are committed.

A fresh `elicit` is a new draw, so its top bubbles will differ from these in about 8% of questions (see Test-retest).
