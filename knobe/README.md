# knobe

Research codebase for a decomposed Knobe-effect study in LLMs, extending
Raimondi et al. (arXiv:2510.12229). It generates a balanced factorial vignette
set, elicits intentionality/blame/praise ratings from subject models, and runs
both a behavioral analysis (mixed models + planned contrasts) and a
mechanistic-interpretability analysis (activation caching, δ_l contrasts,
pretrained→finetuned layer patching, per-layer probes).

`specs/01_MASTER_SPEC.md` (in the sibling `specs/` repo) is the authoritative
architecture and data-contract reference. `src/knobe/constants.py` is the
single source of truth for the taxonomy, banned-word lists, question wording,
and template text — never duplicate or hand-edit those values elsewhere.

Research docs (results, methodology, process history) live under `docs/`,
organized by subfolder — see [`docs/README.md`](docs/README.md) for the index.

## Pipeline stage map

Each stage reads and writes JSONL/CSV/parquet artifacts validated against
`schemas.py` at every boundary. Stages are resumable (append + skip-completed)
and, where long-running, shardable.

| Stage | Module | CLI subcommand | Input → Output |
|-------|--------|----------------|----------------|
| S1 generation | `generate.py`, `tracking.py` | `knobe generate next-prompt / ingest / approve / status / qa` | authoring prompts → `data/authoring/…_master_matrix.csv` |
| S2 assemble | `assemble.py` | `knobe assemble` | master_matrix.csv → `vignettes.csv` (+ release freeze under `data/release/vX.Y/`) |
| S2 render | `render.py` | `knobe render` | `vignettes.csv` → `prompts.jsonl` (the only text the H200 sends) |
| S2 jobs | `jobs.py` | `knobe jobs build / diff` | `prompts.jsonl` × run config → `jobs.jsonl`; diff → remaining work |
| S3 curation | `curate.py` | `knobe curate run / review` | `vignettes.csv` → `curated.csv` (+ raw checkpoint, distribution reports) |
| S4 power | `power.py`, `power_sim.py` | `knobe power estimate / simulate / report / run` | pilot `results.jsonl` → `variance_components.jsonl` → `power_grid.jsonl` → `power_report/` |
| S5 elicitation | `elicit_vllm.py` | `knobe elicit` | `jobs.jsonl` + `prompts.jsonl` → `results.jsonl` |
| S6a activation cache | `mech/cache_acts.py` | `knobe mech cache` | `prompts.jsonl` + `vignettes.csv` → `acts/<model_key>/final_token_resid.safetensors` + `index.json`, `delta_l.parquet` + `.png` |
| S6b layer patching | `mech/patch.py` | `knobe mech patch` | pretrained→finetuned → `patch/<family>/layer_<tag>.jsonl` + `patch_metrics.parquet` |
| S7a probes | `mech/probes.py` | `knobe mech probes` | activation cache + tables → `probes/<model_key>/<construct>__<kind>__layer<l>.json` + `.npz`, and RQ2 report `mech_report/rq2_*` (curves/CIs/dissociation/subspace + `rq2_localization.png`) |
| S7b decompose | `mech/decompose.py` | `knobe mech decompose` | `patch_metrics.parquet` + probes → RQ3/RQ4 report |
| S8 analysis | `analysis/` | `knobe analyze` | `results.jsonl` (+ vignettes/curated) → `paper/` (numbers + figures) |

## Setup

```
uv venv --python 3.13
uv pip install -e ".[dev,stats]"
.venv/bin/python -m pytest
```

`pytest` passes on a laptop with no GPU/heavy deps: torch/vllm/transformer_lens/
nnsight/lm-eval/boto3 are all optional extras behind guarded imports.

### Extras map

| Extra | Pulls in | Needed for |
|-------|----------|------------|
| `dev` | pytest, safetensors, pyarrow, matplotlib | the test suite + artifact round-trips |
| `stats` | statsmodels, scipy, scikit-learn, matplotlib | S4 power, S8 analysis, S7 probes/decompose |
| `hf` | torch, transformers, safetensors | `--engine hf` CPU-friendly elicitation |
| `vllm` | vllm | `--engine vllm` (the real H200 S5 backend) |
| `mech` | transformer_lens, nnsight, safetensors, pyarrow, matplotlib, scikit-learn, statsmodels | S6/S7 real backends (`--backend tl|nnsight`) + probes/decompose |
| `aws` | boto3 | `S3Storage` (durable off-node result sync) |
| `sae` | sae-lens | Gemma Scope SAE decomposition stub |
| `eval` | lm-eval | S6 capability check (post-patch ARC/HellaSwag/MMLU/TruthfulQA) |

## CLI quickstart — zero-GPU G0 rehearsal

Every stage runs GPU-free with deterministic fakes, so the whole plumbing can
be button-pressed on a laptop before the H200 arrives:

```
# S2: assemble + render + build jobs (fast, deterministic batch transforms)
knobe assemble data/authoring/ALL_DOMAINS_master_matrix.csv build/vignettes
knobe render build/vignettes.csv --out build/prompts.jsonl
knobe jobs build --config configs/run_example.yaml --prompts build/prompts.jsonl --out build/jobs.jsonl

# S5: elicit against the deterministic fake engine (no GPU, no downloads).
# --skip-manifest-check because a fresh checkout has no frozen release manifest.
knobe elicit --jobs build/jobs.jsonl --prompts build/prompts.jsonl \
    --run-config configs/run_example.yaml --engine fake --out build/results.jsonl \
    --skip-manifest-check

# S8: analyze
knobe analyze --results build/results.jsonl --vignettes build/vignettes.csv --out-dir build/paper
```

Resume idiom — `jobs diff` reports the set-difference of `jobs.jsonl` vs
`results.jsonl` by `job_id`, so a killed run restarts against only the
remainder:

```
knobe jobs diff --jobs build/jobs.jsonl --results build/results.jsonl --out build/remaining.jsonl
knobe elicit --jobs build/remaining.jsonl --prompts build/prompts.jsonl \
    --run-config configs/run_example.yaml --engine fake --out build/results.jsonl \
    --skip-manifest-check
```

## Study results (compressed)

The per-response study results for both releases ship as gzipped JSONL in
`results_dist/` (one row per variant x question x model x sample; raw
response text, parsed rating, forced-scoring logprobs, seed/temperature/
revision). The analysis pipeline expects them under `results/<release>/`
(gitignored). To unpack into the right place, from this directory:

```
mkdir -p results/v1.0 results/v1.1
gunzip -c results_dist/results_v1.0_all.jsonl.gz > results/v1.0/results_all.jsonl
gunzip -c results_dist/results_v1.1_all.jsonl.gz > results/v1.1/results_all.jsonl
```

The two Ngo-extension pilots' per-response results (see
`analysis/ngo_extensions/`) ship the same way, published 2026-08-22:
`results_pilot_nonmoral_all.jsonl.gz` (88,200 rows) and
`results_pilot_moral_foundations_all.jsonl.gz` (18,900 rows). Their
analysis scripts read them from each pilot's `outputs/` directory
(gitignored):

```
gunzip -c results_dist/results_pilot_nonmoral_all.jsonl.gz \
    > analysis/ngo_extensions/nonmoral_pilot/outputs/elicit_results.jsonl
gunzip -c results_dist/results_pilot_moral_foundations_all.jsonl.gz \
    > analysis/ngo_extensions/moral_foundations_pilot/outputs/elicit_results.jsonl
```

v1.0 caveat: all Mistral `logprobs_0_10` vectors in the v1.0 file are flat
(the retracted measurement artifact -- see `docs/rq1_findings/MAIN_RUN_WRITEUP_v1.0.md`);
v1.1 contains the corrected re-elicitation. Analysis commands and fallback
lists are documented in the writeups.

## Result custody: everything comes home

Standing process (2026-07-29): **every cluster artifact is harvested to the
local `results/<release>/` directory promptly after its job completes**, via
the `knobe_fetch` log-relay job (in the local-only cluster folder -- gzip+base64
through job logs, sha256-verified; any S3 key set or byte range via the config
`fetch` block).
S3 is the durable copy; local is the working copy; cluster logs rotate, so
harvest is part of finishing a job, not an afterthought. Sizing: fine to
tens of MB per job (the whole pilot was 12 MB of logs); S6 activation caches
(~300 MB fp16, incompressible) need byte-range slicing across several relay
jobs -- or real S3 read access, which supersedes the relay when it lands.

## H200 arrival checklist

1. **Run the GPU suite first:** `pytest -m gpu`. These tests are deselected by
   default (see `pyproject.toml addopts`) and only exercise the real backends.
   The two shakiest items to verify by hand:
   - **nnsight slice-0 input-proxy patch** — patching the pre-block-0 residual
     (the embedding slice) goes through nnsight's input proxy, a different code
     path than the block-output slices; the gpu test asserts TL/nnsight
     equivalence across all slices including 0.
   - **lm-eval capability stub** — `mech/patch.run_capability_check` returns
     canned deltas under FakeBackend and raises `NotImplementedError` on the
     real path. Wire it into `lm_eval.simple_evaluate` and keep the gpu test a
     strict `xfail` until the real harness is connected.
2. **Cluster bootstrap (landed 2026-07-28)** — the cluster is Ray-on-Kubernetes;
   a local-only (gitignored) cluster folder holds the platform wrapper and
   connection details. There is no ssh/kubectl step for normal job
   operations: submit through the wrapper against the cluster's Ray Dashboard.
   H200 worker groups are uw2-only; `group:h200-stt` (1 GPU/pod) fits knobe's
   single-GPU stages. Run `scripts/cluster_connect.sh` (local-only, gitignored)
   for the full runbook and `scripts/cluster_connect.sh check` for a
   connectivity test.

   **Required job title:** every knobe submission uses
   `JOB_NAME="Quality ai bias test"` (researcher directive, 2026-07-28):

   ```
   cd <cluster-folder>/jobs
   export USER_EMAIL="$(git config user.email)"
   make submit CONFIG=<job_type>/<config>.json JOB_NAME="Quality ai bias test" REGION=uw2
   ```

   Never put tokens/credentials in job configs or `runtime_env.env_vars` —
   the dashboard renders them publicly and the submitter rejects them; use
   cluster-mounted Kubernetes secrets (see the wrapper's README).

   **G0 probe findings (2026-07-28, jobs "Quality ai bias test" 1–4):**
   - `group:h200-stt` worker = NVIDIA H200, 139.8 GB VRAM, torch
     2.7.1+cu126, CUDA 12.6, Python 3.10.
   - The cluster's HF identity can access **all 11 registry
     checkpoints**, including gated meta-llama/* and google/gemma-*.
   - **Working env (validated end-to-end, run 7):** `pip: ["vllm==0.10.1",
     "huggingface_hub>=0.24.0"]` — vLLM 0.10.1 stays on the node's torch
     2.7.1/cu126 and tolerates the base image's transformers 4.54.1.
     Two dead ends, documented: newest vLLM ships CUDA-13 wheels
     (`libcudart.so.13` missing on this CUDA-12.6 node), and vLLM 0.9.x
     collides with transformers ≥4.54 over the `aimv2` model type — which
     cannot be fixed by pinning transformers, because **pip pins for
     transformers do NOT shadow the base image's copy**
     (`/home/ray/anaconda3/.../transformers`, verified via probe): match
     vLLM to the image's transformers, not vice versa.
   - Generation smoke (Llama-3.2-1B, bf16, seeded T=1.0, max_tokens=10,
     logprobs=20): loaded in 24.5s, returned a parseable rating
     completion with 20 first-token logprobs — the exact elicit_vllm.py
     mechanics confirmed on the H200.

   **G1 pilot lessons (runs 8–27; `knobe_g1` under the wrapper's jobs folder
   is the reference implementation):**
   - Attention backends are per-architecture on this stack: Llama/Mistral
     run on the default backend; **Gemma-2 requires
     `VLLM_ATTENTION_BACKEND=TRITON_ATTN_VLLM_V1`** (default FlashAttention
     lacks tanh softcapping; FlashInfer trips an sm_scale assertion on
     Gemma's custom attention scale; FlexAttention lacks sliding window).
     Hence the pilot runs as two jobs split by family.
   - The platform wrapper passes `--config /tmp/training_config.json` — a
     node-global path that races between concurrently starting jobs. Read
     the per-job `TRAINING_CONFIG` env var instead (knobe_g1/g1_pilot.py).
   - A stopped job's vLLM EngineCore survives as an orphan holding ~130 GiB
     on the pod; new jobs on that pod die with "Free memory on device
     12/139.8 GiB". g1_pilot.py reaps such zombies pre-flight (guarded:
     only orphaned vllm/knobe processes) and retries elicit up to 3× —
     safe because resume restores completed rows from local/S3.
   - `knobe elicit --batch-size 256 --checkpoint-every 2000` (defaults 32 /
     10000) — batching amortizes the 11-candidate forced-scoring passes,
     3.2× throughput; observed ≈11.6 rows/s (Llama-8B, default backend)
     and ≈8.4 rows/s (Gemma-9B, Triton) per H200.
   - Pilot parse rates: llama-3.1-8b-instruct ≈66%, gemma-2-9b-instruct
     ≈41% — both below the 95% threshold, so those checkpoints use
     logit-fallback (EV over logprobs_0_10) in analysis, per spec §4.4.
     Every row carries the exact logprobs, so no re-run is needed.
   - Wrapper CLI quirk: a config-level `runtime_env` block SUPPRESSES the
     job-type `pyproject.toml` deps — declare pip deps in the config's
     `runtime_env.pip` list.
   - The wrapper's `make submit` doesn't quote `JOB_NAME`; submit via
     `cli/shared_cluster_cli.py submit ... --name "Quality ai bias test"`
     directly (same wrapper). Cluster requires unique job ids — repeat
     runs append a run counter to the required title.
3. **Storage** — `configs/storage.yaml` selects the `StorageBackend`
   (`null` / `local` / `s3`). The real bucket name lives in the local-only
   `configs/storage.yaml` (IRSA-authenticated on-cluster, no keys anywhere).
   Pass `--storage configs/storage.yaml` to any H200 stage to enable durable
   off-node sync.

### Local ↔ remote storage key layout (documented once)

Local output lives under `results/<release>/…`. The storage backend mirrors it
under these remote keys:

| Artifact | Local path | Remote key |
|----------|-----------|------------|
| elicitation results | `results/<release>/results.jsonl` | `results/<release>/<results-filename>` |
| activation cache | `results/<release>/acts/<model_key>/…` | `acts/<release>/<model_key>/…` |
| **sharded** cache | `…/acts/<model_key>/shard_i_of_n/…` | `acts/<release>/<model_key>/shard_i_of_n/…` |
| patch results | `results/<release>/patch/<family>/…` | `patch/<release>/<family>/…` |

Sharded activation caches carry the `shard_i_of_n` segment in the remote key
too, so concurrent shards never clobber each other in the bucket. Combine them
into the single top-level cache the probes loader expects with:

```
knobe mech cache --release vX.Y --model-key <k> --prompts … --vignettes … --merge-shards
```

which validates the shard set is complete (all `0..n-1` present) and disjoint
(no duplicate prompt_id) before writing `final_token_resid.safetensors` +
`index.json`. To then compute full-set δ_l after a sharded cache run, run the
ordinary unsharded `knobe mech cache` (no `--shard`): it safely reuses the
merged top-level cache and aligns δ_l to the cache's on-disk row order.

**Patch-sweep parallelism:** parallelize `knobe mech patch` by `--layers`
(each config writes a distinct `layer_<tag>.jsonl`), NOT by `--shard`. Every
shard of a `--shard` patch run writes the same `layer_<tag>.jsonl` paths and
pushes to the same shard-less remote keys, so concurrent `--shard` runs against
one output dir clobber each other; `--shard` is for single-process prompt
subsetting only (a startup warning fires if it is combined with `--storage`).

## Conventions and invariants

- **Frozen instruments** — question wording, template text, taxonomy
  definitions, and banned-word lists live ONLY in `src/knobe/constants.py` and
  are never edited (master spec §7). Everything imports from there.
- **`data/release/` is append-only** — once a `vX.Y/` release and its
  `manifest.json` are written, nothing inside may be edited or deleted; cut a
  new release instead. Downstream artifacts record the release they were
  computed from, and H200 jobs refuse to run on a manifest-hash mismatch.
- **Determinism / seeding** — no bare `random`/time-seeded RNG. All randomness
  derives from the spec §3.5 rule (sha256 of release_version, prompt_id,
  model_key, sample_idx) or an explicit `--seed`.
- **`--limit` / `--shard` policy** — long-running stages (curate, elicit, power
  simulate, mech cache/patch) accept `--limit N` and `--shard i/n`. Fast
  deterministic batch transforms (assemble, render, jobs build) intentionally
  do **not**: they process the whole set atomically, and sharding a pure
  transform would only invite drift between partial outputs.
- **Reviewer ≠ subject** — the curation reviewer model (Claude API) must never
  appear as a subject in `configs/models.yaml` (checked automatically).

## Makefile targets

| Target | Runs |
|--------|------|
| `make check` | the full default pytest suite |
| `make check-woN` | the tests for work order N (`check-wo0`, `wo1`, `wo2a`, `wo2bc`, `wo3`, `wo4`, `wo5`, `wo6`, `wo7`, `wo8`) |
| `make paper` | regenerate every number + figure into `results/<release>/paper/` (override `RELEASE`/`RESULTS`/… on the command line) |

`gpu`- and `slow`-marked tests are deselected by default; run them explicitly
with `pytest -m gpu` / `pytest -m slow`.

## Known caveats / deferred work

Several scientific and modeling choices in this implementation follow the spec
but warrant a researcher sign-off before pre-registration freeze and before any
RQ claims. They are catalogued, with context and implementation pointers, in
[`docs/v1_1_release_process/DECISIONS_FOR_HUMANS.md`](docs/v1_1_release_process/DECISIONS_FOR_HUMANS.md).
