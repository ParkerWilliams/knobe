# Mistral Chat-Template Check (spec, 2026-09-25)

**Status (2026-09-28):** the pipeline fix in §2 is committed and the run is
staged; not yet elicited. The §3 base run is approved; the §5 extensions
are not, and are best decided after the Raimondi authors reply (§1).

**What this gates.** `CLAIMS.md` claim 7 (Mistral does not replicate Raimondi
et al.'s finetuned effect) and `SUBMISSION_GAMEPLAN.md` §5 item 4. The claim
stays "unresolved rather than a finding" until the two cheap diagnostics in
`RAIMONDI_REPLICATION_GAPS.md` §4 are run: (1) weight/revision identity and
(2) chat-template handling. This doc records what (1) already settles from
local data and public sources, and specifies the one small elicitation (2)
still needs.

---

## 1. What is already settled without new data

**No chat-formatted data exists anywhere in the project.** `specs/00_PLAN.md`
§5 item 5 planned a chat-templated robustness pass for instruct models as a
secondary condition, and the pipeline implements it end to end
(`render.py` emits `format="chat"` prompts; `elicit_vllm` applies each
model's own template on-device). But every run config (`run_main_v1_1_core`,
`run_main_v1_1_bp`, the G1 pilot, v1.0, both Ngo pilots) set
`formats: [raw]`. Checked 2026-09-25: 0 chat rows in v1.0, v1.1, or the G1
pilot results. So the question cannot be answered from existing data.

**Revision identity (theory 1) is as settled as it can be from our side.**

| checkpoint | revision recorded in every v1.1 row |
|---|---|
| `mistralai/Mistral-7B-Instruct-v0.1` | `ec5deb64f2c6e6fa90c1abf74a91d5c93a9669ca` |
| `mistralai/Mistral-7B-v0.1` | `27d67f1b5f57dc0953326b2601d68371d40ea8da` |

`ec5deb6` is the Instruct-v0.1 repo's current head (2025-07-24, a README
edit). Per the public commit history, nothing after the December 2023
`safetensors` upload touches weights; later commits change the tokenizer
("Align tokenizer with mistral-common", 2024-07-03), the chat template
(2024-06-20), metadata, and the README. Raimondi et al. (arXiv:2510.12229)
appeared in October 2025, so any copy of Instruct-v0.1 they downloaded
carries the same files as ours.

**What the paper does not say.** It names the base models only
("Llama-3.1-8B, Mistral-7B-v0.1, and gemma-2-9b") and "finetuned versions of
each"; it gives no instruct checkpoint IDs, no revisions, no code link, and
says nothing about chat templates beyond "the prompt format was kept fixed
across all conditions" with a plain-text prompt ending in `Answer:` — which
is exactly our raw condition. Two consequences:

- The natural reading is that our raw run *already matches* their stated
  format, so a chat-template mismatch would have to come from something
  their pipeline did implicitly (e.g. a chat API applying the template).
- The finetuned Mistral checkpoint is genuinely ambiguous.
  `Mistral-7B-Instruct-v0.2` is a finetune of a *different* base and is
  what many tools resolve "Mistral-7B-Instruct" to. **The cheapest decisive
  step is to ask the authors** which instruct checkpoints they used and
  whether a chat template was applied; no compute can substitute for that
  answer.

## 2. A pipeline defect found while specifying the run

Every chat template in the trio writes the BOS token as text
(`<s>`, `<|begin_of_text|>`, `<bos>`), and vLLM's `generate()` on a text
prompt tokenizes with `add_special_tokens=True`, prepending BOS again.
Verified on the real Mistral tokenizer at `ec5deb6`: the unpatched chat path
yields token ids starting `[1, 1, ...]`. Raw-format results never pass
through this code and are unaffected; it would have corrupted the first
chat-format run.

Fix (`3f05c6d`): `render_chat_prompt()` in `src/knobe/elicit_vllm.py` strips the
template's textual BOS when the tokenizer adds its own, used by both engines,
with tests in `tests/test_elicit_chat_bos.py` (79/79 elicit tests pass with
it applied). The run additionally executes an on-node tokenizer-only
pre-flight that fails the job unless each checkpoint's chat prompt has
exactly one BOS and matches `apply_chat_template(tokenize=True)`; it passes
for Mistral locally (Llama and Gemma tokenizers are gated, so they are
checked on-node).

A second observation: after `[/INST]` the forced-scoring candidate `"7"`
tokenizes as a word-internal `7`, whereas the model's natural continuation
is `▁` then `7`. So logprob-EV scoring is not meaningful in chat format —
the same class of boundary problem as the retracted v1.0 Mistral result.
**`parsed_rating` is the only score of record for this check**, which is
also the scale the Raimondi comparison already uses (§2 of the gaps doc).

## 3. Design

| | |
|---|---|
| items | release v1.1, MB + MG variants only (168 variants, 42 families) — Raimondi's all-moral scope, the same subset as the existing finetuned comparison |
| question | intentionality only (Raimondi's only question) |
| format | chat: the frozen raw text, unchanged, as one user message; each model's own template applied on-device |
| checkpoints | the three instruct models; Gemma and Llama are the controls (both replicate Raimondi in raw format) |
| revisions | pinned to the exact commits v1.1 recorded, so raw vs. chat compares one set of weights and tokenizer files |
| N | 25 per (variant, checkpoint), matching v1.1 intentionality |
| seeds | the frozen `derive_temperature_and_seed(release, prompt_id, model_key, sample_idx)` rule; chat `prompt_id`s end `::chat`, so draws are independent of the raw run's |
| temperature | U(0.85, 1.15), the same rule as every run |
| max_tokens | 10, unchanged from raw, for comparability (hard-coded in `run_elicit`) |
| rows | 168 × 1 × 3 × 25 = **12,600** |

Run config, committed here as the canonical copy:

```yaml
release: v1.1
models:
  - llama-3.1-8b-instruct
  - mistral-7b-v0.1-instruct
  - gemma-2-9b-instruct
formats:
  - chat
n_samples: 25
questions:
  - intentionality
```

(`jobs build` expands this over all 420 variants; the staging step keeps
the 168 MB/MG ones and asserts the 4,200-per-checkpoint count.)

**Cost.** Two single-GPU jobs (Gemma needs its own attention backend, the
same split as the main run). At the main run's observed throughput (≈11.6
rows/s Llama/Mistral, ≈8.4 Gemma), elicitation is ≈12 min + ≈8 min; with
model loads and environment setup, **under 1 GPU-hour total**. Results stay
local, like every other raw result, until explicitly published.

## 4. Analysis plan (reuse, no new inference machinery)

Stack the new chat rows with the v1.1 raw rows for the same 168 variants and
checkpoints; `parse_ok` rows only; `parsed_rating` throughout.
`analysis/rq1_v1_1_robustness/lib.py`'s `wild_cluster_bootstrap` (B=1999,
cluster = `family_id`, G = 42), with the same `sign_c` coding as
`05_valence_split_wcb.py`.

1. **Chat-only replication, per family:** `parsed_rating ~ sign_c`. The
   Raimondi test re-run in chat format.
2. **Format moderation, per family:** `parsed_rating ~ sign_c * format_c`
   (raw −0.5 / chat +0.5); the WCB on `sign_c:format_c` is the test.
3. **Parse rate per (checkpoint, format).** Reported first, because a
   chat-format parse collapse at `max_tokens=10` would be a finding about
   the instrument, not the model.

Holm within this contrast family (3 checkpoints × 2 tests). One log line per
run in `results/ANALYSIS_LOG.md`.

**Interpretation, stated before the data:**

- *Mistral chat significant and positive, format interaction significant,
  controls stable:* Mistral's null is format-specific, and claim 7 becomes
  a methodological explanation, contingent on the authors confirming they
  (or their tooling) applied a template.
- *Mistral chat null as well:* format is ruled out as the explanation.
  What remains is checkpoint identity (§1), which only the authors can
  settle; claim 7 stays "unresolved", now with one of two diagnostics
  closed.
- *Controls move under chat:* the template changes the asymmetry
  generally, which is a finding about the elicitation format in its own
  right and belongs with claim 1.

## 5. Optional extensions (not in the base run; decisions for the authors)

- **All 420 variants in chat format** (31,500 rows, ≈1.5 GPU-hours): turns
  this into the full chat robustness pass `specs/00_PLAN.md` planned for
  all of RQ1, rather than only the Raimondi check.
- **A `Mistral-7B-Instruct-v0.2` raw-format arm** on the same 168 variants
  (4,200 rows): tests the checkpoint-identity reading directly. Needs a new
  registry entry in `configs/models.yaml`. Best decided after the authors
  reply.
