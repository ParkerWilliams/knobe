# Knobe Moral Probe: Status and Next Steps

As of 2026-11-19 · Mer McFadden (drafted with Claude). Also kept as a Claude doc:
https://claude.ai/artifact/Hk6KKApUsPfc1eMggywNAh

## Summary

**What we're looking for.** In people, a foreseen side effect is judged more intentional when it is bad than when it is good: the Knobe effect, as measured in Ngo et al. (2015). We ask whether language models show this asymmetry. If they do, we ask whether it is specific to moral content, or a general response to any bad outcome (prudential, procedural, non-harm moral). We also ask whether fine-tuning introduces or strengthens it.

**What we've found.** So far the evidence comes only from stand-ins: three OpenRouter instruct models and Jev, TypeSafe's decision model. None of the study's six models has been run.

- **The asymmetry is there.** All four stand-ins rate bad side effects as more intentional on Ngo's pairs (p ≤ .001). Blame follows the same pattern.
- **It does not look moral-specific.** Prudential and procedural side effects show the asymmetry too. The moral arm's gap is larger in only 2 of 4 stand-ins, and in one of those because of a reversal on prudential items. The blame gap is actually smaller for moral items in all three chat models.
- **Two measurement problems.** Every model misreads at least some of the reversed-anchor wordings, which dilutes pooled blame and praise. Praise effects are small and near the floor.
- **There is no evidence yet on fine-tuning.** Pretrained checkpoints aren't available as stand-ins.

**What that suggests we pursue.**

1. **Run the pilot on the study's own models.** It is the only route to RQ3 and the only test of whether the stand-in pattern holds. It is waiting on cluster access, last reported on 2026-10-22 as blocked by an AWS SSO login.
2. **Treat "general, not moral" as the leading hypothesis.** Write it into the analysis plan with predictions before the full run, as DESIGN §10 requires. Settle the reversed-wording treatment in the same step.
3. **Plan a mechanistic follow-on around the same question.** Is there one internal "bad outcome" signal that drives intentionality for every kind of bad side effect? Cross-arm probes and steering can test that, using mech code the repo already has (last section). It starts once the pilot confirms the effect, and only after the forward-pass readout is checked against behavior.

## Research questions

There is stand-in evidence for RQ1, RQ2 and RQ4, and none for RQ3 or RQ5. The questions are from `docs/DESIGN.md` §1. The test for each is from §10: wild cluster bootstrap, clustered by storyline, B = 1999, Holm within family × tuning × question.

| RQ | Question | Test | Evidence so far | Status |
| --- | --- | --- | --- | --- |
| 1 | Do models show Ngo's bad-vs-good asymmetry in intentionality? | Sign effect on Ngo's pairs (final set: 19 adapted, plus 30 verbatim as a consistency check) | Yes in all 4 stand-ins: Gemma-3-4B +1.20, Llama-3.1-8B +0.69, Mistral-Nemo +2.37, Jev +8.95 (all p ≤ .001) | Supported on stand-ins |
| 2a | Does it extend to nonmoral outcomes (prudential, procedural)? | Sign effect per arm; moral vs rest interaction | Yes: the asymmetry appears in nonmoral arms too. Moral vs rest is larger for Gemma +1.37 (driven by a prudential reversal) and Mistral-Nemo +0.75; null for Llama −0.13 and Jev +0.12 (EV) | Mixed |
| 2b | Does it extend to non-harm moral foundations? | Sign effect per foundation; harm vs rest pooled | Yes, broadly. Harm vs rest is not significant in any chat stand-in (Gemma +0.85, p = .051); Jev's is smaller in harm (EV −1.73, p = .004) | Mixed, small cells (7–13 storylines) |
| 3 | Does fine-tuning introduce or strengthen it? | Tuning interaction, pretrained vs instruct | None: OpenRouter serves no pretrained checkpoints | Needs the pilot |
| 4 | Do intentionality, blame and praise follow the same pattern? | Sign effect per question | Blame follows in every model. Praise goes the right way but is small and near floor. Blame's moral vs rest gap is negative in all 3 chat stand-ins (−0.54 to −0.74) | Partly; praise is weak |
| 5 | Does it track the model's own sense of significance, harm, morality? | Sign effect moderated by the model's own ratings | Not yet analyzed | Needs the full run |

## What we have so far

We have six completed pieces of work. None of them uses the study's own models, and the pilot runs used the August pilot vignettes rather than the final stimuli.

| Date | Work | What it gave us | Limits |
| --- | --- | --- | --- |
| 2026-11-12 to 11-16 | Jev native (`docs/JEV_NATIVE.md`, report HTML) | Jev rated the scenarios itself on 5,924 questions. Large asymmetry, not moral-specific. Test-retest: top pick repeats 92%, EV r = .995 | Not an LLM in the study; top pick snaps to scale ends; one call per question |
| 2026-10-22 | Stimuli finished (`stimuli/full_run/`) | 236 pairs after screening and four review rounds; loyalty 17 pairs (target 20, above floor). Pilot items picked: 44 | Not yet answered by any model |
| 2026-10-22 | Jev wrapped run | Jev answering the chat models' full prompt; kept as a contrast | Superseded by the native run |
| 2026-10-21 | Jev as a second reader of chat replies | Agrees with the regex reader on 99.93% of readable answers; no effect changes sign or crosses .05 | Cross-check only; regex stays the reader of record |
| 2026-10-14 | First look v2 on stand-ins (`docs/OPENROUTER_PRELIMINARY.md`) | 262,944 answers; Knobe pattern in all 3 models; go/no-go = go (2 of 3) | Instruct only; 2 of 3 models are not the study's; Llama fails the 90% number gate |
| 2026-10-13 | First look v1 | Same models; superseded by v2 after the answer-format fix | Answers cut off at 10 tokens |

## What we are on track to conclude

If the study models behave like the stand-ins, the most likely headline is this: LLMs show the Knobe asymmetry, but it is a general bad-vs-good asymmetry rather than a moral one. That is a hypothesis for the analysis plan, not a result.

**Likely to hold up**

- **RQ1.** The asymmetry is present. Every model tested shows it on Ngo's pairs, at p ≤ .001, under both readers.
- **RQ4, blame.** Blame tracks intentionality in direction in every model.

**Leaning, but not settled**

- **RQ2, not moral-specific.** Nonmoral arms show the asymmetry too. Moral vs rest is significant in only 2 of 4 stand-ins, and in Gemma it comes from a prudential reversal.
- **RQ4, blame is smaller in the moral arm.** The blame gap is smaller for moral than nonmoral items in all 3 chat stand-ins. This matches August pilot claim 9 and may become a finding in its own right.

**Cannot conclude yet**

- **RQ3 (fine-tuning).** There is no pretrained data. If pretrained models fail the validity gate (DESIGN §8, check 2), RQ3 is reported as not measurable under this protocol.
- **RQ5 (self-perception).** Not analyzed.
- **Individual foundations.** Fairness, loyalty and purity had 7–13 storylines in the pilot sets. The final set has 17–26 pairs per foundation, and comparisons between foundations are descriptive only (§11).
- **Praise.** Effects are small and near the floor. Jev reads the reversed praise wording backwards, and the chat stand-ins misread reversed wordings too (r −.38 to −.92). The pooled praise estimate is not trustworthy until the reversed-wording question is settled.

## Open decisions for Mer

The first two should be settled before the full run, because they change what the primary analysis is.

| Decision | Why it matters | Options | Recommendation |
| --- | --- | --- | --- |
| How to treat reversed-anchor wordings | Every model tested misreads at least some reversed wordings, which dilutes pooled blame and praise | (a) Normal wordings primary, pooled as sensitivity; (b) keep pooled primary, normal as sensitivity; (c) decide after the pilot's anchor check | (a) or (c), recorded as a DESIGN amendment |
| Analysis plan with predictions | DESIGN §10 requires it committed before the full run; none exists yet | Write it now from the stand-in evidence, or after the pilot | Draft now and finalize after the pilot, before the full run starts |
| Jev's role in the writeup | Jev's results are clean but Jev is not a language model under study | Comparison point, appendix, or out of scope | Appendix or comparison point; re-run or quote EV only before citing the moral-vs-rest null |
| Nonmoral experiment's moral arm size | Final set has 19 moral pairs against 33–34 prudential and procedural | Accept, or author and screen more moral pairs | Accept unless the pilot shows the moral-vs-rest contrast is underpowered |

Done 2026-11-19: the review record. The decision CSVs in `stimulus_reviews_completed_2026-10-22/` were already in `stimuli/review/`. Mer's two review summaries were added there in 53d4c16, so the local folder is now a duplicate.

## Next steps

The critical path is the cluster pilot. Everything except steps 1 and 2 waits on it.

1. **Mer:** settle the reversed-wording treatment and the other open decisions above.
2. **Mer, with Claude:** draft the analysis plan with predictions, including the hypothesis that the asymmetry is general rather than moral.
3. **Parker:** confirm cluster access, then run `docs/PILOT.md` steps 1–5 on all six study models, with and without worked examples. Cost: about 1.2–3 h of GPU time; this is Parker's call.
4. **Claude:** run the pilot checks and `tools/go_no_go.py`, then log and report. This is the first evidence on RQ3 and on pretrained validity.
5. **Parker:** on GO, run the full set (`docs/FULL_RUN.md`, 432,288 rows). On NO-GO, follow that doc's fix-and-rerun path.
6. **Mer:** finalize and commit the analysis plan before the full run's data are analyzed.
7. **Claude:** run the full-run checks and the primary fits for RQ1–RQ4. Then the sensitivity fits: normal wordings only, EV reader, and option C refusal bounds.
8. **Claude:** run the RQ5 moderation analysis, which is the one analysis not yet built.
9. **Mer:** decide which results go in the writeup, including whether Jev appears, and whether to start the mechanistic follow-on (see its own order of steps below).

One question for Parker: has the AWS SSO login that blocked cluster jobs on 2026-10-22 been resolved?

## Mechanistic follow-on

The study is well placed for interpretability work. Its stimuli are minimal pairs (same storyline, only the side effect's sign changes), and its models are open-weight 7–9B pairs. A tested mech pipeline already exists in `src/knobe/mech/`: activation caching, per-layer bad−good contrasts, pretrained→instruct layer patching, and linear probes with storyline-level splits. It is about 3,750 lines and has never run on real data. `docs/submission_plan/SUBMISSION_GAMEPLAN.md` §6 deferred it to "paper two, or after the behavioral paper." Raimondi et al. (2026), the paper this study extends, is itself a mech-interp paper, so this is the natural second paper.

**The one real blocker is the readout.** The mech code scores a forward pass by the expected value over the tokens "0"–"10" at the answer position. This study rejected that readout for behavior because, for instruct models, it often disagrees with the written answer (Wang et al. 2024; CLAIMS.md claim 1). Before any mechanistic result can be tied to the behavioral effect, the forward-pass readout has to reproduce the behavioral sign effect, per model and question, on the study's own prompts.

**Candidate analyses**

| Question | Method | Ties to | Code |
| --- | --- | --- | --- |
| Where in the network does the side effect's sign enter the intentionality judgment? | Per-layer bad−good residual contrast on the minimal pairs | RQ1 | Reuse `cache_acts.py` (δ_l) |
| Is there one shared "bad outcome" direction, or a separate moral one? | Train a sign probe on moral items, test on prudential, procedural and non-harm foundations; compare per-arm directions | RQ2, the headline | Reuse `probes.py`; new cross-arm transfer split |
| Does that direction cause the asymmetry? | Steer: add the bad−good direction to good items, ablate it on bad items, measure the change in intentionality | RQ1, RQ2 | New: steering is not in `backend.py` |
| Where does fine-tuning add or amplify it? | Pretrained→instruct layer patching (Raimondi's method) on the clean stimuli | RQ3 | Reuse `patch.py`; needs pretrained models to pass the validity gate |
| Do intentionality and blame read the same direction? | Probe and steering overlap across questions | RQ4 | Reuse `probes.py` / `decompose.py` |
| Which features carry badness? | Sparse autoencoder features on the contrast (Gemma Scope for Gemma-2-9B, already wired in config) | Exploratory | Reuse `decompose.py --sae gemma-scope` |

If the behavioral result stays "general, not moral", the cross-arm probe-transfer and steering tests are the strongest follow-on. They would say whether the model uses one valence signal for every kind of bad outcome, which behavior alone cannot show.

**Order, once the pilot has confirmed the effect on the study models**

1. **Parker:** run `pytest -m gpu` on the cluster; it has never run against the real backends. Known weak spots: nnsight slice-0 patching, and the lm-eval capability check, which is still a stub.
2. **Claude:** write the adapter from kmp items and prompts to the mech pipeline's inputs. Its schemas are the older protocol's (VignetteRow, valence families).
3. **Parker:** run the readout validation (one forward pass per prompt) and the activation cache. Rough estimate: about 7,000 prompts per model and about 2 GB of fp16 residuals per model, so minutes of GPU. To be confirmed by timing one model first.
4. **Claude:** run the contrasts and cross-arm probes on the cache. This is CPU only.
5. **Mer:** decide on steering and patching, which are the more expensive GPU steps, from what steps 3–4 show.
