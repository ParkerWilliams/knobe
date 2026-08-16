# Decomposed Knobe-Effect Study in LLMs — Main Run Writeup (Release v1.0)

> **CORRECTION (2026-08-09):** a tokenizer bug made every Mistral
> logprobs_0_10 vector flat (EV ≡ 5.0) in this run, so all EV-scored Mistral
> results below — in particular the "mistral reversal" (rq1_base_sign_x_tuning
> −0.14, presented as this run's most consequential new datum) — rested on a
> constant pretrained baseline and are **retracted as measurement artifacts**.
> With corrected measurement (release v1.1, re-elicited Mistral checkpoints),
> mistral's sign×tuning interaction is a null, not a reversal. gemma and llama
> results were unaffected and replicate in v1.1. See
> `MAIN_RUN_WRITEUP_v1.1.md` (Methods) for the full mechanism.


**Status:** published draft for researcher review. Raw per-response results remain
local-only per the data agreement; every aggregate below traces to the local
`results/v1.0/paper/` artifacts.
**Run:** 2026-08-05, two single-H200 cluster jobs (gemma; llama/mistral). **Data:** 189,000
completions (420 variants × 3 questions × N=25 × 6 checkpoints), release v1.0
(manifest-hash-guarded), fresh seeds derived from the release string. **Analysis:**
`results/v1.0/paper/` (S8, WO-8), logit-fallback (EV over first-token logprobs, spec §4.4)
for the five checkpoints whose regex parse rate fell below 95%. 188,381 rows analyzed
(99.7%); zero manifest jobs incomplete.

## One-paragraph summary

Extending Raimondi et al. (arXiv:2510.12229) with a decomposed factorial vignette set
(105 families × 4 variants, 10 domains, 5 outcome categories × typicality ×
evocativeness), we replicate the finetuning-contingent Knobe-style asymmetry in two of
three model families — and find a significant *reversal* in the third. The
sign×tuning interaction (the study's core contrast) is strong and positive in
gemma-2-9b (+0.47, p≈0) and llama-3.1-8b (+0.47, p≈0): instruct-tuned models rate
harmful side-effects as more intentional than helpful ones, while their pretrained
bases do not. Mistral-7B-v0.1 shows a smaller but significant interaction in the
*opposite* direction (−0.14, Holm p=0.002), upgraded from a pilot null by the full-N
run. The most robust effect in the study is not the classic contrast at all but the
typicality×sign interaction, significant with the same sign in all three families
(−0.19 to −0.44, all p<10⁻⁶): atypical actions amplify the intentionality asymmetry.
The evocativeness manipulation produced incoherent effects across families and carries
a documented manipulation-check failure; we treat RQ1c-evocativeness as uninterpretable
in v1.0.

## Findings by research question

### RQ1 base: the Knobe asymmetry and its finetuning contingency

| family | sign (instruct only) | sign × tuning | reading |
|---|---|---|---|
| gemma-2-9b | +0.34 (Holm p=.017) | **+0.47 (p<10⁻⁴)** | replicates |
| llama-3.1-8b | +0.35 (p=.088, ns) | **+0.47 (p<10⁻⁴)** | replicates (interaction-driven) |
| mistral-7b-v0.1 | −0.14 (ns) | **−0.14 (p=.002)** | significant reversal |

The interaction contrasts survive the domain-cluster sensitivity refit (all three
families, same signs, p≤.002 with domain as the clustering unit). The
domain-random-slope sensitivity, however, marks **every** headline generalization
contrast QUALIFIED under the preregistered rule (CI ratios 2.8–7.9 or non-negligible
slope variance): effects vary substantially across the 10 domains, and cross-domain
generalization claims should be phrased accordingly.

Mistral's reversal is the single most consequential new datum. In the pilot it was a
null; at main-run power it is a directional dissociation between model families
trained on different corpora/procedures. Before any writeup claims "the Knobe effect
in LLMs," this needs adversarial scrutiny (per-domain breakdown, per-question split,
inspection of mistral-instruct's raw completions — its 98% parse rate makes it the
cleanest-measured checkpoint in the study).

### RQ1a: moral vs nonmoral valence-type modulation

Not significant in any family in the primary fit (estimates +0.05 to +0.62, all Holm
p>.10). Domain-cluster refit finds llama/mistral significant, but the slope
sensitivity marks all three QUALIFIED with large slope variance — read as
domain-heterogeneous at best, not a stable effect.

### RQ1b: decomposition by moral status

Directionally positive for moral items in gemma and llama (both p<10⁻⁴; mistral ns).
The nonmoral analogue is significant in llama (+2.64) and weakly in gemma; llama shows
a large asymmetry for BOTH moral and nonmoral items — consistent with a general
negativity asymmetry rather than a specifically moral one in that family. (Note the
1b errors-in-variables caveat in summary.md: slope magnitudes are attenuated,
signs interpretable.)

### RQ1c: typicality and evocativeness

**Typicality×sign is the strongest, most consistent effect in the study**: −0.44
(gemma), −0.19 (llama), −0.43 (mistral), all p<10⁻⁶, same sign, and it survives both
sensitivity refits in all families (though still domain-QUALIFIED for magnitude).
Uncommon actions sharpen the asymmetry.

**Evocativeness×sign is incoherent** — negative in gemma (−0.07), null in llama,
positive in mistral (+0.28) — and sits under a documented manipulation-check failure:
at curation, the reviewer model rated the intended vividness gap at median 0 (mean
0.47 vs required ≥2; 300/420 pairs flagged; 36 pairs *reversed*). The high-evocativeness
variants operationalize concreteness/specificity; the curation instrument measures
emotional evocativeness. Until the construct is re-operationalized (v1.1), RQ1c-evocativeness
results should not be interpreted.

### RQ1d: neutral-baseline structure

Large, uniformly significant neutral-offset effects (+1.55 to +2.65, all p<10⁻⁶) and
typicality-within-neutral effects that *disagree in sign across families* (gemma
−0.38; llama +0.60; mistral +0.67). The neutral baseline is doing real work and its
family-specific structure deserves a look before RQ2+ builds on it.

## Methods notes a reviewer will ask about

- **Scoring.** Five of six checkpoints parse below the 95% threshold (llama-pretrained
  25%, mistral-pretrained 29%, gemma-instruct 44%, gemma-pretrained 64%, llama-instruct
  77%); per spec §4.4 those checkpoints are EV-scored from the stored, renormalized
  first-token logprob distribution over "0"–"10" — uniform within checkpoint, no
  re-elicitation. Mistral-instruct (98%) uses parsed ratings. 619 rows (0.3%) excluded
  as parse failures (all mistral-instruct, which does not use fallback).
- **Primary model.** LMM with family random intercept (`lmm-familyRI`); the spec's
  CLMM-primary/LMM-sensitivity ordering is inverted with documentation (statsmodels
  OrderedModel lacks random effects). Ordinal fixed-effects sensitivity in
  `ordinal_sensitivity.csv`. Holm correction within (family × RQ). Seeded
  family-cluster bootstrap CIs.
- **Dataset deviations (release changelog, decision 2026-08-04):** frozen at 105
  families (below the 250-family plan target — power report shows contrast 1a
  underpowered at this size; 1c/1d adequately powered); all 420 variants accepted
  with curation flags preserved as documented limitations rather than resolved.
- **Provenance.** Stimuli frozen in `data/release/v1.0` (sha256 manifest; elicitation
  refuses on hash mismatch). Results harvested via the log relay with per-file sha256
  verification; `jobs diff` confirms 0 of 189,000 manifest jobs without a result.
  Elicitation engine: vLLM 0.10.1, bf16, one H200 per job; gemma under
  VLLM_ATTENTION_BACKEND=TRITON_ATTN_VLLM_V1.

## Limitations (carry into any manuscript)

1. 105/250 families; contrast 1a underpowered by design of this interim run.
2. Evocativeness manipulation failed its manipulation check; RQ1c-evocativeness
   uninterpretable pending v1.1 revision (construct: concreteness vs emotional
   evocativeness).
3. All cross-domain generalization QUALIFIED under the preregistered domain-slope rule.
4. EV-scoring (not free-response parsing) for 5/6 checkpoints; parse-rate differences
   across checkpoints are themselves a family-level behavioral difference worth noting.
5. Mistral reversal unexplained; treat as a finding to probe, not noise.
6. Reviewer-model dependence: curation ratings from a single reviewer (claude-sonnet-5,
   thinking disabled); no human rater agreement data in v1.0.

## What's next (not started, gated on human decisions)

- **G3 go/no-go (S6/S7):** constructs with a real behavioral footprint — the base
  asymmetry (gemma/llama) and typicality — are the natural candidates for activation
  caching, per-layer patching, and probes; mistral's reversal makes it the most
  interesting patching target (does patching pretrained activations *restore* the
  standard direction?).
- **v1.1 dataset revision:** evocativeness re-operationalization + the 145-family
  completion sprint; etiquette subdomain rebalance.
- **Analysis follow-ups:** per-domain forest plots for the mistral reversal;
  chat-format robustness (`--chat-comparison`); blame/praise-specific splits.

— Generated 2026-08-06 from `results/v1.0/paper/` artifacts; every number above is
traceable to `contrast_table.csv`, `domain_sensitivity.csv`,
`domain_slope_sensitivity.csv`, or `summary.md` in that directory.
