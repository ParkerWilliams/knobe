# WO-6 — Activation caching and layer patching (H200)
**Stage:** S6. **Depends on:** WO-5 (scoring path + results for layer selection),
master spec §3.7–3.8, §5. **Blocks:** WO-7.

## Objective
Implement `mech/backend.py`, `mech/cache_acts.py`, `mech/patch.py`: reproduce
Raimondi's per-layer residual-stream analysis and pretrained→finetuned patching on
our decomposed stimulus set, storing everything needed for construct-level analysis.

## Part A — backend interface (`mech/backend.py`)
```python
class ResidualAccess(Protocol):
    def run_with_cache(prompt_ids, layers, positions) -> Acts      # fp16 out
    def run_patched(prompt_ids, donor: "ResidualAccess", layers,
                    positions="all", scoring="logits_0_10") -> Scores
```
- Primary impl: TransformerLens (`HookedTransformer.from_pretrained_no_processing`,
  explicit bf16 — never default fp32; document why `no_processing`: patching must
  operate on the same residual basis as the native model, no folded LayerNorm).
- Secondary impl: nnsight, same interface, activated per-model via config
  (`mech_backend: nnsight`) for models TL lacks or where memory demands it.
- Equivalence test between impls on the debug model: cached final-token residuals
  agree within fp16 tolerance; patched scores agree within a stated tolerance.

## Part B — activation caching (`mech/cache_acts.py`)
1. For every raw-format intentionality prompt in the release: cache residual stream
   at final prompt token, all layers (pre-0 … post-last), both checkpoints of each
   core family → `final_token_resid.safetensors` (spec §3.7) + row index.
2. Compute and store Raimondi's δ_l (per-layer mean activation contrast, bad vs good)
   AND the construct-level extensions: δ_l per {moral vs nonmoral valence, typicality
   condition, evocativeness condition, NEU vs valenced}, each computed on the
   controlled subsets the factorial design licenses (e.g. evocativeness contrast only
   within matched pairs).
3. Push caches + summary parquet to S3.

## Part C — patching (`mech/patch.py`)
1. **Layer sweep (replication):** for each core family, patch pretrained residuals
   into the finetuned model one layer at a time, all token positions, re-elicit
   intentionality via logit-distribution scoring (deterministic — the patched
   "re-elicitation" uses `logprobs_0_10` expected value, not stochastic sampling;
   record this as `scoring: "logits_0_10"`). Output per spec §3.8.
2. **Metrics per patched config:** full Δ_knobe plus every component gap in master
   spec §5.3, so RQ3's "which component did the patch suppress" table falls straight
   out. (Stochastic-sampling confirmation runs at the best layer(s) only, using
   WO-5's engine with a patched-model hook — budgeted, config-gated.)
3. **Multi-layer configs:** top-k critical layers jointly (k ∈ {1,2,3,5}), plus the
   Raimondi min-Δ_patch layer per model, config-driven.
4. **Capability check:** for each "successful" patch config, lm-eval-harness
   (ARC-Easy, HellaSwag, MMLU, TruthfulQA) on the patched model; store deltas.
5. Both models resident bf16 on one H200; assert same tokenizer + seq alignment
   between donor/recipient per prompt (hard error otherwise).

## Acceptance criteria
- Debug-model (gemma-2-2b) end-to-end: cache → δ_l plot → single-layer sweep →
  metrics table, on 40 items, < 30 min on one small GPU.
- Patching identity test: patching finetuned→finetuned (self) leaves logits unchanged
  within tolerance (catches hook/position bugs).
- δ_l on the trio qualitatively reproduces Raimondi's mid-to-late-layer concentration
  before any novel analysis is trusted (G3 gate input).
