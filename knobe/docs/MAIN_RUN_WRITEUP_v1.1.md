# Main Run Writeup — Release v1.1 (2026-08-09)

**Status:** published draft for researcher review. Raw per-response results are
local-only per the data agreement; every aggregate traces to the local
`results/v1.1/paper/` artifacts. Supersedes parts of the v1.0 writeup — see the
correction note there.

**Run:** 378,000 completions (420 variants × {intentionality, affect_salience
@ N=25; blame, praise @ N=50} × 6 checkpoints), frozen release v1.1
(manifest-guarded), fresh seeds. Zero manifest jobs incomplete. **Scoring is
uniform for the first time:** all six checkpoints EV-scored from forced-scoring
logprobs (spec §4.4), eliminating the v1.0 mixed-measurement caveat.

## The two headline changes from v1.0

**1. The "mistral reversal" was a measurement artifact — corrected here.**
A tokenizer bug (see Methods) made every Mistral logprob vector flat in v1.0;
with correct measurement, mistral's sign×tuning interaction is a clean **null**
(−0.011, Holm p=0.41), not a reversal. The revised cross-family story: the
finetuning-contingent Knobe asymmetry **replicates in gemma (+0.45, p<10⁻⁴) and
llama (+0.45, p<10⁻⁴) and is absent in mistral** — a magnitude dissociation
between families, no longer a directional one.

**2. RQ1a (moral vs nonmoral modulation) is now significant in all three
families under set-clustering** — gemma +0.092 (p=.0014), llama +0.629 (p≈0),
mistral +0.263 (p≈0) — with point estimates matching the family-RI primary
(the prereg's estimate-stability check passes: only SEs shrink). The v1.1
content fixes (24 families re-worked for dimensional independence; 22 clean)
plus the set_id blocking model turned v1.0's null into a consistent effect.
Promotion of set-clustering to primary remains a prereg decision to take
explicitly, not silently.

## Other results

- **Typicality×sign stays the most robust effect** — significant, same sign,
  all families (gemma −0.415, llama −0.177, mistral −0.195, all p<10⁻⁴).
  Mistral's corrected magnitude is roughly half its artifactual v1.0 value.
- **gemma/llama v1.0→v1.1 stability is excellent** on the untouched RQs
  (sign×tuning within ±0.03; typicality within ±0.03), supporting treating
  v1.1 as superseding v1.0 for those families too.
- **Affect-salience self-report (new):** collected cleanly for all six
  checkpoints. **Confound check (Phase 5.3): affect tracks sign** — bad
  scenarios are rated more emotionally striking than good in every family
  (gemma 5.89 vs 5.28; llama 3.52 vs 2.80; mistral 5.24 vs 4.76). Any
  affect×sign analysis must treat affect as sign-correlated, not an
  independent manipulated factor: use within-sign contrasts or residualized
  affect, per the observational-reframing note in the workflow docs.
- **Exclude-flagged sensitivity:** as configured it drops 88% of rows (the
  persisting vividness pair-flags dominate the flag set), so it compares
  "the 84 unflagged variants" rather than isolating the moral-bleed fix.
  Recommend re-running with a flag-class filter (exclude only
  moral-relevance/category flags) before reading anything into it.

## Methods notes

- **Mistral logprob correction.** The forced-scoring pass derived rating-token
  ids from standalone candidate encodings; Mistral's SentencePiece tokenizer
  maps a bare digit to a word-boundary piece whose id differs from the token
  realized in context after "Answer:", so every candidate lookup missed and
  logprobs_0_10 was silently flat (EV ≡ 5.0) for every Mistral row in v1.0 and
  the first v1.1 collection. Fixed (candidate ids from the in-context
  tokenization diff — exact for any tokenizer; regression-tested), and both
  Mistral checkpoints were re-elicited with the fixed runner (identical seeds,
  release hash-verified). llama/gemma tokenizations were never affected.
- Parse rates match v1.0 patterns (mistral-instruct 97.7% down to
  llama-pretrained 24.4%); all checkpoints EV-scored uniformly regardless.
- RQ1b blame/praise at N=50 (de-attenuation); the de-attenuated RQ1b fit is
  queued as follow-up analysis.
- All cross-domain generalization claims remain QUALIFIED under the
  preregistered domain-random-slope rule, as in v1.0.
- v1.1 known limitations carried in the release changelog: HC-NMB-01/HC-NMG-01
  goal-bleed (accepted, deferred to v1.2); reviewer-calibration pattern (4
  families where the production reviewer failed content ChatGPT passed);
  Type-1 MG instrument asymmetry (unchanged wording, separate cycle).

— Generated 2026-08-09 from `results/v1.1/paper/`; numbers trace to
`contrast_table.csv`, `set_sensitivity.csv`, `domain_slope_sensitivity.csv`.
