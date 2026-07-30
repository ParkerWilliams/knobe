# Project Plan: Decomposed Knobe-Effect Study in LLMs
**Status:** working plan, 2026-07-27. Companion to `01_MASTER_SPEC.md` and `work_orders/`.

## 1. What we are building, in one paragraph

Raimondi et al. (arXiv:2510.12229) showed the Knobe effect in three finetuned LLMs
(Llama-3.1-8B, Mistral-7B-v0.1, Gemma-2-9B), localized it to mid-to-late residual-stream
layers, and eliminated it by patching pretrained activations into those layers — all
operationalized as a single negative-vs-positive contrast over 80 Ngo-derived scenarios.
This project rebuilds the stimulus base as a decomposed, factorial design (5 outcome
categories × typicality × evocativeness × 10 domains, 250 families → ~1000 vignettes)
and re-runs all three of their stages asking, at each stage, *which component* of the
asymmetry is present, localized, or patched — plus a new probe-alignment stage (RQ4).

## 2. The pipeline and where each stage runs

```
 LOCAL / API (laptop + Claude API)                      H200 (open-weight models)
 ─────────────────────────────────                      ─────────────────────────
 S1 Generate family sets  (LLM-drafted, human-curated)
 S2 Assemble variants     (deterministic, existing code)
 S3 Curate               (reviewer model ≠ subject models)
 S4 Pilot + power sim    (Westfall-style simulation)
        │
        ▼
   FROZEN DATASET RELEASE  ──── manifest.json + sha256 ────►
                                                        S5 Behavioral elicitation (vLLM)
                                                        S6 Activation caching + layer patching
                                                        S7 Probe training + patch decomposition
        ◄──── results.jsonl, per-layer final-token ─────
              residuals (~300MB/model), patch results
 S8 Statistical analysis + figures (local)
```

The handoff boundary is deliberately a **frozen, hashed dataset release** in one
direction and **flat result artifacts** in the other. Nothing on the H200 ever edits
stimuli; nothing local ever touches model weights. This keeps the expensive side
stateless and re-runnable, and it means a coding agent working on either side needs
only the data contracts in the master spec, never the other side's code.

### What is genuinely local precompute
- All stimulus generation and curation (Claude API — cheap: ~1,000 variants × 4
  curation questions ≈ 4k calls, one-time).
- **Prompt rendering.** Every prompt string the H200 will ever send — including
  chat-template application decisions — is precomputed locally into `prompts.jsonl`.
  The H200 job is then a pure "read prompt, sample completion, write row" loop. This
  removes an entire class of silent divergence (template drift between behavioral and
  mechanistic stages).
- The full job manifest (every `(variant_id, question, model, sample_idx)` tuple with
  its derived seed), so the H200 side does no combinatorics, only execution.
- Power simulation, all statistics, all figures.
- Probe *training* can be local too: we ship back per-layer final-token residuals
  (≈ n_items × n_layers × d_model fp16 ≈ 260–330MB per model), and probes are ridge/
  logistic regressions on those. Only probe-based *interventions* need the GPU.

### What must be on the H200
- Behavioral elicitation of the six subject checkpoints (vLLM offline batch).
  Scale check: 1,000 variants × 3 questions × 100 samples × 6 checkpoints ≈ 1.8M
  short completions — a few GPU-hours total at vLLM throughput; even Raimondi's
  N=283 scheme (≈5.1M) is well within one day on one H200.
- Activation caching, per-layer patching runs (two models resident at once),
  patched re-elicitation, and benchmark sanity checks (lm-eval-harness).

**Critical consistency rule:** behavioral and mechanistic stages must use the *same
weights, same tokenizer, same rendered prompts* — i.e., run behavioral elicitation on
our own H200s from HF checkpoints, not through a hosted API. A hosted provider's
serving stack (quantization, template, sampler) would make S5 results incomparable
with S6/S7 internals. This is why the pluggable-provider design in
`elicit_main_experiment.py` gets narrowed to vLLM-on-HF-checkpoints for subjects
(the pluggable interface survives for the curation/reviewer side, which is API-based).

## 3. Subject models

**Core (replication set — run these first):** Raimondi's exact trio, base + instruct:

| family | pretrained | finetuned | d_model | layers | bf16 |
|---|---|---|---|---|---|
| llama-3.1-8b | meta-llama/Llama-3.1-8B | …-8B-Instruct | 4096 | 32 | ~16GB |
| mistral-7b-v0.1 | mistralai/Mistral-7B-v0.1 | …-7B-Instruct-v0.1 | 4096 | 32 | ~14GB |
| gemma-2-9b | google/gemma-2-9b | google/gemma-2-9b-it | 3584 | 42 | ~18GB |

All six fit on one H200 (141GB) simultaneously if needed; patching (one base+instruct
pair resident) is comfortable even in fp32.

**Extension menu (what else easily fits one H200)** — constraint: must have a *public
base + instruct pair* (this excludes many popular models), and ideally TransformerLens
support. In rough order of scientific value per GPU-hour:

1. **OLMo-2-7B / 13B (AI2)** — base+instruct with *fully open training data*, so
   finetuning-contingency claims ("the asymmetry is induced by finetuning") can in
   principle be traced to the tuning corpus. Best value-add.
2. **Qwen2.5-7B / 14B / 32B** — clean base+instruct pairs, strong models; 32B is the
   largest that stays comfortable for mechanistic work on a single H200 in bf16
   (~64GB × 2 models resident ≈ 128GB — tight but workable; 14B is the safe pick).
3. **Gemma-2-2B / 27B** — Raimondi's own ablation sizes; 2B is nearly free to run and
   good for pipeline debugging; 27B gives a size axis inside a family they already used.
   Bonus: **Gemma Scope** pretrained SAEs exist for Gemma-2 (2B/9B fully, 27B partially),
   which upgrades RQ4 from hand-trained linear probes to a much stronger
   feature-level analysis at zero training cost.
4. Llama-3.2-1B/3B — cheap size axis within Llama family (Raimondi's ablation used 1B).
5. **Not recommended as subjects:** Llama-3.1-70B (bf16 weights ≈ 140GB — doesn't fit
   one H200 for mechanistic work; fp8 serving works for behavior only, which breaks the
   consistency rule), and any instruct-only release (no base = no patch donor).

**Recommendation encoded in the spec:** trio first (replication), then OLMo-2-7B and
Gemma-2-2B as the first extensions, others config-only.

## 4. Interpretability stack

- **TransformerLens** as the standard for activation caching, per-layer residual
  patching, and hook-based interventions. Supports all core families. Caveat for
  agents: TL defaults to fp32 — load in bf16/fp16 explicitly for 27B-class models.
- **nnsight** as the designated escalation path if a model lacks TL support or memory
  becomes tight (it wraps native HF modules; no weight duplication or upcasting).
  The spec's patching module is written against a thin internal interface
  (`get_resid(layer, pos)`, `set_resid(...)`) so the backend is swappable.
- **SAELens + Gemma Scope** as an optional RQ4 upgrade for the Gemma-2 family:
  project patch-induced activation deltas into a pretrained SAE feature basis and ask
  which named features move, instead of (or alongside) our own probe directions.
- **lm-eval-harness** for the post-patch capability checks (ARC-E, HellaSwag, MMLU,
  TruthfulQA — mirroring Raimondi).
- vLLM strictly for throughput sampling (S5); it exposes no internals and is never
  used for S6/S7.

## 5. Design decisions surfaced while reading the current materials
These need explicit resolution; the spec currently encodes the recommendation.

1. **NEU × evocativeness contradiction.** Design-rationale §7 says neutral families
   yield 2 variants (no evocativeness crossing); generation-spec2 §1 and
   `assemble_vignettes.py` give NEU the full 4 variants, and the current matrix's 21
   NEU families all carry low/high renderings. **Recommendation: keep 4-variant NEU**
   — "does concreteness alone move intentionality when nothing is at stake?" is a
   clean RQ1d sub-test and the marginal cost is zero — and amend the design rationale.
   (Resolve before freezing v1.)
2. **Nonmoral subdomain imbalance.** Current matrix: aesthetic 24, procedural 16,
   prudential 2, **etiquette 0**. The remaining ~145 families to be generated must be
   steered (the tracking-log recommendation mechanism already exists) or subdomain
   cannot be used even as a covariate. Work order 1 makes the balance target a hard
   acceptance criterion, not a soft aim.
3. **Response-level N.** Raimondi's 283 samples/item matched Ngo's human N — a
   sentimental constant, not a power calculation. With ~13× their item count, item-level
   N is our power driver (per design-rationale §16). Spec: pilot at N=25, then set main
   N from the variance decomposition (expected landing zone 50–100), with
   T ~ U(0.85, 1.15) retained for comparability.
4. **Both-tails elicitation cost is fine.** Asking blame *and* praise of every item
   (per spec2 §3) triples calls vs Raimondi but is what makes RQ1b answerable; at vLLM
   costs this is a non-issue. No change.
5. **Chat template policy.** Raimondi queried both base and instruct models with the
   same plain-text format ending in "Answer:". Primary condition replicates that
   (raw completion for both), with a chat-templated robustness pass for instruct
   models logged as a secondary condition. Precomputed locally either way (see §2).
6. **Curation reviewer.** Must not be a subject family (already enforced in code).
   Claude (API) as reviewer is compatible with all listed subjects.

## 6. Stage gates (design-rationale §15, made operational)

- **G0 pipeline dry run** (local, existing code + Gemma-2-2B on any GPU or even CPU):
  20 Ngo-style items end-to-end through S2→S5→S8 plumbing. Validates parsing, seeding,
  resume logic. *Gate: zero unparsed responses after prompt fixes; resume produces
  byte-identical results.jsonl.*
- **G1 behavioral pilot** (H200): full trio on the ~420 already-assembled variants,
  N=25. *Gate: base Knobe contrast (MB vs MG) reproduces in ≥2/3 instruct models;
  variance components estimated; power sim sets final N and any item-count increase.*
- **G2 dataset freeze:** all 250 families curated, pair-checks passed, balance targets
  met → `release/v1.0` hashed and archived. After this, stimuli are immutable;
  any fix is v1.1 with a changelog.
- **G3 mechanistic go/no-go:** only constructs with a real behavioral footprint in G1+S5
  (per RQ1) proceed to per-construct localization/patching — RQ2–4 are defined over
  RQ1's survivors.

## 7. Sequencing for the two of you + coding agents

1. Resolve §5 items 1–2 (one conversation).
2. Hand **WO-1/WO-2** to a coding agent now (generation tooling upgrades + assembly
   hardening) — pure local work, no compute dependency.
3. In parallel, hand **WO-5/WO-6 scaffolding** to a second agent: everything through
   G0 runs on any machine with a small GPU (Gemma-2-2B / Llama-3.2-1B are the debug
   models precisely so H200 access is not on the critical path).
4. Generation sprint to 250 families (human-in-the-loop per spec2 §10 cadence) while
   agents build; curation (WO-3) runs as families land.
5. G1 pilot on H200 → power sim (WO-4) → freeze v1.0 (G2).
6. Main S5 run, then S6/S7 per work orders; S8 analysis is spec'd from day one so the
   results schema is guaranteed to feed it.

## 8. Risks worth naming

- **Base-model parseability.** Pretrained checkpoints answer "Answer:" prompts noisily;
  Raimondi coped, but our parse-rate must be measured per checkpoint in G0/G1, with
  first-token-logit fallback scoring (constrain to tokens "0"–"10") available if free
  generation parses <95%. The fallback also gives cleaner per-item score distributions
  for the mechanistic stages.
- **Cross-model patching validity.** Patching pretrained→finetuned assumes aligned
  tokenization (true within family) and layer-wise correspondence (assumed, as in
  Raimondi). We inherit this assumption; note it in limitations.
- **Construct correlation in the wild.** Even with the factorial design, curation
  ratings (severity, vividness, typicality-perception) will correlate across items;
  RQ2/RQ4 analyses must use partial correlations / residualized probes, not raw ones —
  this is written into WO-7.
- **Drift between spec and design docs.** The master spec cites design-rationale
  section numbers rather than restating rules wherever possible; the taxonomy tables
  and banned-word list live in exactly one place in the repo (`constants.py`),
  imported everywhere else — same single-source-of-truth discipline the existing
  code already follows.
