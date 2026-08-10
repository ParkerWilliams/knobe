"""S5: the H200 behavioral elicitation runner (master spec §3.6, §4;
WO-5). Pure execution of a precomputed job manifest -- no combinatorics, no
prompt construction, no randomness beyond the manifest's own per-job
seed/temperature (those come from ``jobs.jsonl``, built by ``jobs.py``, and
are NEVER re-derived here).

Architecture (task-5-brief.md, binding):
  - ``GenerationEngine`` protocol, three implementations: ``VllmEngine``
    (real H200 backend, guarded ``vllm`` import), ``HfEngine`` (guarded
    torch/transformers CPU fallback for the debug path), ``FakeEngine``
    (deterministic sha256-based -- the vehicle for every test in this
    module, and also a real ``--engine fake`` option so the whole plumbing
    -- checkpoint/resume, manifest guard, sharding, storage sync,
    throughput reporting -- can be rehearsed end-to-end offline, per WO-5's
    "Debug path (G0)").
  - ``knobe.storage``'s ``StorageBackend`` for the durability loop: push
    the results shard to storage every ``checkpoint_every`` rows and at
    exit (atexit + SIGTERM/SIGINT), and restore on start from whichever of
    (local file, storage copy) has more rows.
  - Model loading with pinned ``model_revision`` (``registry.Family.revision``,
    default "main"); one model resident at a time; jobs are grouped by
    (model_key, format) so a model is loaded at most once per invocation.
  - Manifest guard (spec §3.10): refuses to run unless the run config's
    release hash-matches ``data/release/<release>/manifest.json``, unless
    ``--skip-manifest-check`` is passed (prominently logged when it is).

Never imports ``knobe.storage`` the other way around (storage.py is
standalone), and never touches ``torch``/``vllm`` at import time (both are
guarded, per common-context.md constraint 7) -- this whole module, and
every test that exercises it, works on a laptop with neither installed.
"""
from __future__ import annotations

import atexit
import hashlib
import json
import math
import os
import signal
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Literal, Protocol, Sequence

from knobe.jobs import diff_jobs, load_run_config
from knobe.parsing import ParsedRating, parse_with_fallback
from knobe.registry import Family, load_registry, model_key_for
from knobe.schemas import (
    ElicitRunLogEntry,
    JobRecord,
    PromptRecord,
    ReleaseManifest,
    ResultRecord,
    append_jsonl,
    read_jsonl,
    write_jsonl,
)
from knobe.storage import NullStorage, StorageBackend, load_storage_config

RUNNER_VERSION = "elicit_vllm-0.1"

DEFAULT_CHECKPOINT_EVERY = 10_000
DEFAULT_BATCH_SIZE = 32
DEFAULT_REPORT_EVERY_BATCHES = 10
PARSE_RATE_THRESHOLD = 0.95


# ---------------------------------------------------------------------------
# Engine abstraction (task-5-brief.md architecture decision)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EngineRequest:
    """One completion to fire. Exactly one of ``text``/``messages`` must be
    set -- ``text`` for a "raw" plain-completion job, ``messages`` for a
    "chat" job (the model's own chat template is applied on-device by the
    engine, at generate() time, not here -- see PromptRecord's docstring:
    the frozen text is identical across raw/chat, only the transport shape
    differs)."""

    job_id: str
    prompt_id: str
    temperature: float
    seed: int
    max_tokens: int = 10
    text: str | None = None
    messages: list[dict] | None = None
    want_first_token_logprobs: bool = True

    def __post_init__(self) -> None:
        if (self.text is None) == (self.messages is None):
            raise ValueError(
                f"EngineRequest {self.job_id!r} must set exactly one of text/messages "
                f"(got text={self.text!r}, messages={self.messages!r})"
            )


@dataclass(frozen=True)
class EngineResponse:
    """One completion's result. ``logprobs_0_10`` is None only when
    ``want_first_token_logprobs`` was False on the request; otherwise it's
    always exactly 11 floats (indices 0..10 = logprob of the model
    assigning that first-generated-token/token-sequence to rating i) --
    see ``ResultRecord.logprobs_0_10`` and WO-5 requirement 3's two-token
    "10" handling, implemented per-engine below (``FakeEngine``'s
    ``_split_token_logprobs`` has the fully-documented reference version)."""

    job_id: str
    raw_response: str
    logprobs_0_10: list[float] | None


class GenerationEngine(Protocol):
    def load(
        self,
        model_id: str,
        *,
        revision: str = "main",
        dtype: str = "bfloat16",
        gpu_memory_utilization: float = 0.9,
    ) -> str:
        """Loads ``model_id`` at ``revision``. Returns the ACTUAL resolved
        revision (commit hash) to record per output row -- not necessarily
        ``revision`` verbatim (e.g. "main" resolves to whatever commit was
        HEAD at load time)."""
        ...

    def generate(self, batch: Sequence[EngineRequest]) -> list[EngineResponse]:
        """Runs one batch of independent completions against the
        currently-loaded model. Returns responses in an order that need
        not match ``batch`` -- callers must key results by ``job_id``."""
        ...


# ---------------------------------------------------------------------------
# FakeEngine -- deterministic, no real model. The test vehicle for this
# whole module, and a real `--engine fake` G0 rehearsal option.
# ---------------------------------------------------------------------------


def _log_softmax(logits: Sequence[float]) -> list[float]:
    m = max(logits)
    exps = [math.exp(logit - m) for logit in logits]
    total = sum(exps)
    return [logit - m - math.log(total) for logit in logits]


def _pseudo_logit(material: str, token: str) -> float:
    """A deterministic, hash-derived stand-in for a real model's raw logit
    for ``token`` given ``material`` -- never real randomness, just
    sha256(material, token) mapped into [0, 1)."""
    digest = hashlib.sha256(f"{material}|tok={token}".encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") / 2**32


def _request_material(req: EngineRequest) -> str:
    if req.messages is not None:
        payload = json.dumps(req.messages, sort_keys=True, separators=(",", ":"))
    else:
        payload = req.text or ""
    return f"{payload}|seed={req.seed}"


def _rating_from_material(material: str) -> int:
    digest = hashlib.sha256(material.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % 11


class FakeEngine:
    """Deterministic engine: response text and logprobs are pure functions
    of sha256(prompt-or-messages, seed) -- no real model, no randomness
    beyond that hash, so identical (prompt, seed) always produces identical
    output, across runs and process restarts (WO-5 acceptance criterion:
    "re-run reproduces identical raw_response strings").

    ``token_mode`` simulates two distinct real-tokenizer shapes (WO-5
    requirement 3 -- "verify per-tokenizer that 0-10 are single tokens;
    where '10' is multi-token, implement the two-token continuation
    handling"):

      - "single" (default): every one of "0".."10" is its own single
        token for this (fake) tokenizer, so the first-generated-token
        distribution alone gives P(token) for all 11 ratings directly.
      - "split": "10" is NOT a single token here -- it's the two tokens
        "1" then "0" (a common real-BPE-tokenizer shape: single digits get
        their own token, but a run of two digits does not). P("10") is
        then the JOINT P(t0="1") * P(t1="0" | t0="1"): the first factor
        comes from the SAME position-0 distribution used for ratings 0-9
        (token "1" is shared between response "1" and the first token of
        response "10"); the second factor requires a genuinely SEPARATE,
        second scored call with "1" forced as the already-generated first
        token
        (``_split_token_logprobs`` below, via a distinct hash namespace so
        it's provably independent of position-0's distribution) -- this is
        the "probe P('1') then P('0'|'1') via a second scored call" real
        engines must do. Both branches are exercised in
        tests/test_elicit.py (``TestFakeEngineLogprobs``).
    """

    def __init__(self, token_mode: Literal["single", "split"] = "single"):
        if token_mode not in ("single", "split"):
            raise ValueError(f"token_mode must be 'single' or 'split', got {token_mode!r}")
        self.token_mode = token_mode
        self.load_calls: list[tuple[str, str]] = []  # (model_id, revision) -- test introspection
        self.generate_calls: list[list[EngineRequest]] = []  # test introspection

    def load(
        self,
        model_id: str,
        *,
        revision: str = "main",
        dtype: str = "bfloat16",
        gpu_memory_utilization: float = 0.9,
    ) -> str:
        self.load_calls.append((model_id, revision))
        return "fake"

    def generate(self, batch: Sequence[EngineRequest]) -> list[EngineResponse]:
        self.generate_calls.append(list(batch))
        # Test-only slowdown hook (never read outside a deliberately-set
        # test env var): makes the real-SIGKILL G0 gate test
        # (tests/test_elicit.py's TestCLIRealSigkillResume) deterministic
        # rather than racing an otherwise-near-instant FakeEngine against
        # `os.kill` timing. No effect whatsoever unless
        # KNOBE_FAKE_ENGINE_SLEEP_MS is explicitly set in the environment.
        sleep_ms = os.environ.get("KNOBE_FAKE_ENGINE_SLEEP_MS")
        if sleep_ms:
            time.sleep(int(sleep_ms) / 1000.0)
        return [self._generate_one(req) for req in batch]

    def _generate_one(self, req: EngineRequest) -> EngineResponse:
        material = _request_material(req)
        rating = _rating_from_material(material)

        if not req.want_first_token_logprobs:
            return EngineResponse(job_id=req.job_id, raw_response=str(rating), logprobs_0_10=None)

        if self.token_mode == "single":
            logprobs_0_10 = self._single_token_logprobs(material, rating)
        else:
            logprobs_0_10 = self._split_token_logprobs(material, rating)

        return EngineResponse(job_id=req.job_id, raw_response=str(rating), logprobs_0_10=logprobs_0_10)

    @staticmethod
    def _single_token_logprobs(material: str, rating: int) -> list[float]:
        """Single-token tokenizer: "0".."10" are 11 distinct tokens, so one
        position-0 distribution gives every entry directly."""
        tokens = [str(i) for i in range(11)]
        logits = [_pseudo_logit(material, t) for t in tokens]
        logits[rating] += 8.0  # bias so `rating` is the argmax -- deterministic, still varies by material
        return _log_softmax(logits)

    @staticmethod
    def _split_token_logprobs(material: str, rating: int) -> list[float]:
        """Split-token tokenizer: position 0 only has single-char tokens
        "0".."9" -- ratings 0-9 read straight off it (single-token
        responses); rating 10 needs the joint P("1")*P("0"|"1") described
        in the class docstring."""
        digit_tokens = [str(i) for i in range(10)]
        logits0 = [_pseudo_logit(material, t) for t in digit_tokens]
        if rating == 10:
            logits0[1] += 8.0  # "10" starts with the "1" token
        else:
            logits0[rating] += 8.0
        logprobs0 = _log_softmax(logits0)

        # Second scored call: forces t0="1" (a distinct hash namespace, so
        # this is genuinely independent of logprobs0, not derived from it).
        cont_material = f"{material}|forced_t0=1"
        cont_tokens = [str(i) for i in range(10)]
        logits1 = [_pseudo_logit(cont_material, t) for t in cont_tokens]
        if rating == 10:
            logits1[0] += 8.0  # continuation "0" -> "10"
        logprobs1 = _log_softmax(logits1)

        logprobs_0_10 = list(logprobs0)  # indices 0..9
        logprobs_0_10.append(logprobs0[1] + logprobs1[0])  # index 10: joint, log-space sum
        return logprobs_0_10


# ---------------------------------------------------------------------------
# Guarded real-engine imports (never required at test time)
# ---------------------------------------------------------------------------

try:
    import torch
except ImportError:  # pragma: no cover -- exercised whenever the 'hf' extra isn't installed
    torch = None

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
except ImportError:  # pragma: no cover -- same as above
    AutoModelForCausalLM = None
    AutoTokenizer = None

try:
    from vllm import LLM, SamplingParams
except ImportError:  # pragma: no cover -- exercised whenever the 'vllm' extra isn't installed
    LLM = None
    SamplingParams = None


def _resolve_hf_revision(model_id: str, revision: str) -> str:
    """Best-effort resolution of `revision` (which may be a branch/tag,
    e.g. the default "main") to the actual commit hash, for
    ResultRecord.model_revision. Falls back to `revision` itself (still
    honest -- just less precise) if huggingface_hub isn't available or the
    lookup fails for any reason (offline, private repo, etc.) -- this must
    never be fatal, since it's a provenance nicety, not a correctness
    requirement."""
    try:
        from huggingface_hub import HfApi

        info = HfApi().model_info(model_id, revision=revision)
        return info.sha or revision
    except Exception:
        return revision


RATING_TOKENS: tuple[str, ...] = tuple(str(i) for i in range(11))  # "0".."10"



def candidate_tail_ids(tokenizer, prompt: str, forced: str) -> list[int]:
    """Token ids the tokenizer ACTUALLY realizes for the candidate span of
    ``forced`` (= ``prompt + candidate_text``), computed as the tail of
    ``encode(forced)`` past its longest common prefix with
    ``encode(prompt)``. Exact for any tokenizer, including SentencePiece
    families whose standalone ``encode(candidate)`` differs from the
    in-context tokenization (the Mistral flat-logprobs bug, 2026-08-09).
    Special tokens included, matching what vLLM scores in prompt_logprobs."""
    base = tokenizer.encode(prompt, add_special_tokens=True)
    full = tokenizer.encode(forced, add_special_tokens=True)
    lcp = 0
    for a, b in zip(base, full):
        if a != b:
            break
        lcp += 1
    return full[lcp:]


class VllmEngine:
    """Real vLLM-backed engine (guarded import; WO-5's H200 production
    backend). NOT exercised by this repo's test suite -- vllm is a heavy
    GPU extra, deliberately not installed here per common-context.md
    constraint 7 -- but structurally complete: per-request
    ``SamplingParams(temperature, seed, max_tokens)`` for the actual sampled
    response, and the model's own chat template for "chat"-format jobs
    (``tokenizer.apply_chat_template``).

    ``logprobs_0_10`` is computed via EXACT forced-continuation scoring
    (``_score_candidates_batch``), not by reading candidates off a free
    generation call's top-K logprobs. An earlier version requested
    ``logprobs=20`` on the free-generation call and read "0".."10" off
    whatever fell in that top-20 -- for a high-entropy response (exactly
    the kind logit-fallback scoring exists to rescue) a rating token can
    easily fall OUTSIDE the top-20, silently landing as -inf and biasing
    the renormalized expected value, or -- if EVERY one of the 11 fell
    outside -- crashing ``expected_rating_from_logprobs`` mid-run (see the
    defensive guard around that call in ``run_elicit``, which remains as a
    second line of defense; this class's job is to not need it in the
    first place). Fixed here: score each of the 11 candidate strings
    DIRECTLY via ``prompt_logprobs`` teacher-forcing (the same mechanism
    ``FakeEngine._split_token_logprobs`` conceptually models), which
    vLLM always reports honestly for the literal token(s) realized at a
    forced position, regardless of top-K rank -- exact, not truncated,
    whether a candidate is one token or several for a given tokenizer, so
    there's no longer any need to special-case a "10"-is-multi-token
    branch; one uniform mechanism handles every candidate.

    Cost: this trades throughput for correctness -- one free-generation
    call (for the actual sampled ``raw_response`` text) PLUS up to 11
    additional forced-scoring calls per batch (one per rating candidate),
    each itself a real vLLM ``generate()`` invocation with
    ``max_tokens=1`` (prompt-scoring only; vLLM >=0.10 rejects 0). That's up to 12x the vLLM calls of the naive
    top-K-read approach for a batch that wants logprobs on every request --
    a real, deliberate throughput cost for exactness on the field the
    logit-fallback path depends on. A future optimization could skip the
    forced-scoring pass for jobs whose free-generation top-K already
    covers all 11 candidates (informational only -- see
    ``_log_tokenization_shape``), but that's not implemented here.
    """

    def __init__(self) -> None:
        if LLM is None:
            raise RuntimeError(
                "vllm is required for VllmEngine -- install the 'vllm' extra "
                "(`uv pip install -e '.[vllm]'`) or use --engine hf/fake."
            )
        self._llm = None
        self._tokenizer = None

    def load(
        self,
        model_id: str,
        *,
        revision: str = "main",
        dtype: str = "bfloat16",
        gpu_memory_utilization: float = 0.9,
    ) -> str:
        self._llm = LLM(
            model=model_id, revision=revision, dtype=dtype,
            gpu_memory_utilization=gpu_memory_utilization,
        )
        self._tokenizer = self._llm.get_tokenizer()
        self._log_tokenization_shape()
        return _resolve_hf_revision(model_id, revision)

    def _log_tokenization_shape(self) -> None:
        """WO-5 requirement 3: verify (and log) per-tokenizer whether
        "0".."10" are single tokens. Purely informational/diagnostic now
        that ``_score_candidates_batch`` scores every candidate exactly
        regardless of its token count -- correctness no longer depends on
        this, but it's still worth knowing (e.g. an unexpectedly
        many-token "10" would be a red flag about the tokenizer)."""
        shape = {}
        for tok in RATING_TOKENS:
            ids = self._tokenizer.encode(tok, add_special_tokens=False)
            shape[tok] = len(ids)
        multi = {tok: n for tok, n in shape.items() if n != 1}
        print(
            f"[elicit] tokenization shape for rating tokens: {shape} "
            f"(multi-token: {multi or 'none'})",
            file=sys.stderr,
        )

    def _prompt_text(self, req: EngineRequest) -> str:
        if req.messages is not None:
            return self._tokenizer.apply_chat_template(
                req.messages, tokenize=False, add_generation_prompt=True,
            )
        return req.text  # type: ignore[return-value]

    def generate(self, batch: Sequence[EngineRequest]) -> list[EngineResponse]:
        prompts = [self._prompt_text(req) for req in batch]
        sampling_params = [
            SamplingParams(temperature=req.temperature, seed=req.seed, max_tokens=req.max_tokens)
            for req in batch
        ]
        outputs = self._llm.generate(prompts, sampling_params)
        texts = [out.outputs[0].text for out in outputs]

        logprobs_by_idx: list[list[float] | None] = [None] * len(batch)
        idxs_wanting_logprobs = [i for i, req in enumerate(batch) if req.want_first_token_logprobs]
        if idxs_wanting_logprobs:
            scoring_prompts = [prompts[i] for i in idxs_wanting_logprobs]
            # One forced-scoring pass per candidate token (see class
            # docstring for the cost this trades off).
            per_candidate: list[list[float | None]] = [
                self._score_candidates_batch(scoring_prompts, tok) for tok in RATING_TOKENS
            ]
            for row, i in enumerate(idxs_wanting_logprobs):
                logprobs_by_idx[i] = [
                    per_candidate[cand_idx][row] if per_candidate[cand_idx][row] is not None else float("-inf")
                    for cand_idx in range(11)
                ]

        return [
            EngineResponse(job_id=req.job_id, raw_response=text, logprobs_0_10=logprobs_by_idx[i])
            for i, (req, text) in enumerate(zip(batch, texts))
        ]

    def _score_candidates_batch(self, prompts: list[str], candidate_text: str) -> list[float | None]:
        """Exact log P(candidate_text | prompt) for every prompt in
        ``prompts``, via vLLM's ``prompt_logprobs`` teacher-forcing:
        appends ``candidate_text`` to each prompt as part of the PROMPT
        (``max_tokens=1`` -- vLLM >=0.10 rejects 0; the one generated
        token is discarded, so this is still a pure scoring pass) and
        reads off, for each token position the
        candidate spans, the logprob of the actual token realized there --
        vLLM always includes that value even when it falls outside
        whatever top-K was requested, since it's the literal token
        realized at that position, not a sampled/ranked candidate. Summing
        log-space probabilities across the candidate's token span gives
        the EXACT joint probability of the whole candidate continuation
        (one position for a single-token candidate, two for a two-token
        one like a multi-token "10" -- one mechanism, no special-casing).

        Boundary-assumption caveat (documented, not fixed here): this
        assumes ``tokenizer(prompt + candidate_text)`` tokenizes the tail
        exactly as ``tokenizer(prompt) + tokenizer(candidate_text)`` --
        i.e. string concatenation doesn't cause the tokenizer to merge
        characters across the prompt/candidate boundary differently than
        it would independently. True for essentially every prompt in this
        dataset (they end in "Answer:" with no trailing space before the
        model's own continuation), but not a universally guaranteed BPE
        property; see the equivalent caveat in ``HfEngine``'s forced call.
        """
        # Candidate token ids must be derived IN CONTEXT, per prompt: a
        # standalone encode(candidate) is WRONG for SentencePiece-family
        # tokenizers (Mistral), which map a bare "7" to a word-boundary
        # piece ("_7") while the token actually realized after "Answer:"
        # in the forced prompt is the boundary-free "7" -- a different id.
        # That mismatch made every candidate lookup miss and silently
        # produced flat logprobs_0_10 for every Mistral row in the v1.0
        # and v1.1 main runs (EV constant 5.0; found 2026-08-09). The
        # in-context diff below is exact for ANY tokenizer: whatever ids
        # the forced prompt actually tokenizes to past the shared prefix
        # ARE the candidate span, by construction.
        forced_prompts = [p + candidate_text for p in prompts]
        # max_tokens=1 (not 0): vLLM >=0.10 rejects max_tokens=0 outright
        # ("max_tokens must be at least 1", G1 pilot run-19 lesson). We only
        # read PROMPT logprobs; the single generated token is discarded, so
        # this stays a pure scoring pass at the cost of one wasted token.
        sp = SamplingParams(max_tokens=1, prompt_logprobs=1, temperature=0.0)
        outputs = self._llm.generate(forced_prompts, sp)

        results: list[float | None] = []
        for prompt, forced, out in zip(prompts, forced_prompts, outputs):
            tail_ids = candidate_tail_ids(self._tokenizer, prompt, forced)
            plps = out.prompt_logprobs
            if not tail_ids or not plps or len(plps) < len(tail_ids):
                results.append(None)
                continue
            tail = plps[-len(tail_ids):]
            total = 0.0
            ok = True
            for pos, token_id in zip(tail, tail_ids):
                if pos is None or token_id not in pos:
                    ok = False
                    break
                total += pos[token_id].logprob
            results.append(total if ok else None)
        return results


class HfEngine:
    """Slow CPU-friendly fallback (guarded torch/transformers import;
    ``--engine hf``). Generates one request at a time (no batching) --
    adequate for the G0 debug path (gemma-2-2b/llama-3.2-1b on a laptop or
    single small GPU), not intended for the real H200 run. NOT exercised
    by this repo's test suite (same reasoning as VllmEngine)."""

    def __init__(self) -> None:
        if torch is None or AutoModelForCausalLM is None:
            raise RuntimeError(
                "torch/transformers are required for HfEngine -- install the 'hf' extra "
                "(`uv pip install -e '.[hf]'`) or use --engine fake."
            )
        self._model = None
        self._tokenizer = None
        self._single_token_ok: dict[int, bool] = {}
        self._token_id_for: dict[int, int] = {}

    def load(
        self,
        model_id: str,
        *,
        revision: str = "main",
        dtype: str = "bfloat16",
        gpu_memory_utilization: float = 0.9,
    ) -> str:
        torch_dtype = getattr(torch, dtype, None) or torch.bfloat16
        self._tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision)
        self._model = AutoModelForCausalLM.from_pretrained(model_id, revision=revision, torch_dtype=torch_dtype)
        self._model.eval()
        self._single_token_ok.clear()
        self._token_id_for.clear()
        for i in range(11):
            ids = self._tokenizer.encode(str(i), add_special_tokens=False)
            self._single_token_ok[i] = len(ids) == 1
            if len(ids) == 1:
                self._token_id_for[i] = ids[0]
        return _resolve_hf_revision(model_id, revision)

    def _prompt_text(self, req: EngineRequest) -> str:
        if req.messages is not None:
            return self._tokenizer.apply_chat_template(
                req.messages, tokenize=False, add_generation_prompt=True,
            )
        return req.text  # type: ignore[return-value]

    def generate(self, batch: Sequence[EngineRequest]) -> list[EngineResponse]:
        return [self._generate_one(req) for req in batch]

    def _generate_one(self, req: EngineRequest) -> EngineResponse:
        prompt = self._prompt_text(req)
        inputs = self._tokenizer(prompt, return_tensors="pt")
        if req.temperature > 0:
            torch.manual_seed(req.seed)
        with torch.no_grad():
            out = self._model.generate(
                **inputs,
                max_new_tokens=req.max_tokens,
                do_sample=req.temperature > 0,
                temperature=max(req.temperature, 1e-5),
                output_scores=True,
                return_dict_in_generate=True,
            )
        new_tokens = out.sequences[0][inputs["input_ids"].shape[1] :]
        text = self._tokenizer.decode(new_tokens, skip_special_tokens=True)

        logprobs_0_10 = None
        if req.want_first_token_logprobs and out.scores:
            logprobs_0_10 = self._extract_logprobs_0_10(prompt, out.scores[0][0])
        return EngineResponse(job_id=req.job_id, raw_response=text, logprobs_0_10=logprobs_0_10)

    def _extract_logprobs_0_10(self, prompt: str, pos0_logits) -> list[float]:
        log_probs = torch.log_softmax(pos0_logits.float(), dim=-1)
        out = [float("-inf")] * 11
        for i in range(11):
            if self._single_token_ok.get(i):
                out[i] = log_probs[self._token_id_for[i]].item()

        if not self._single_token_ok.get(10, True):
            one_ids = self._tokenizer.encode("1", add_special_tokens=False)
            if len(one_ids) == 1:
                lp_one = log_probs[one_ids[0]].item()
                # Second scored call: force "1" as the generated first
                # token, score the next position for "0". Boundary-
                # assumption caveat: this assumes tokenizer(prompt + "1")
                # re-tokenizes with "1" as its own trailing token rather
                # than merging across the prompt/"1" boundary -- true for
                # this dataset's prompts (end in "Answer:", no trailing
                # space) but not a universal BPE guarantee.
                forced = prompt + self._tokenizer.decode(one_ids)
                inputs2 = self._tokenizer(forced, return_tensors="pt")
                with torch.no_grad():
                    logits2 = self._model(**inputs2).logits[0, -1]
                log_probs2 = torch.log_softmax(logits2.float(), dim=-1)
                zero_ids = self._tokenizer.encode("0", add_special_tokens=False)
                if len(zero_ids) == 1:
                    out[10] = lp_one + log_probs2[zero_ids[0]].item()
        return out


ENGINES: dict[str, type] = {"vllm": VllmEngine, "hf": HfEngine, "fake": FakeEngine}


def build_engine(name: str) -> GenerationEngine:
    if name not in ENGINES:
        raise ValueError(f"unknown --engine {name!r}; choose one of {sorted(ENGINES)}")
    return ENGINES[name]()


# ---------------------------------------------------------------------------
# Model resolution (jobs.jsonl model_key -> configs/models.yaml checkpoint)
# ---------------------------------------------------------------------------


def resolve_model_id(model_key: str, registry: dict[str, Family]) -> tuple[str, str, str]:
    """Reverses ``registry.model_key_for``'s "{family}-{pretrained|instruct}"
    convention to find the HF checkpoint id + pinned revision for a
    ``jobs.jsonl`` ``model_key``. Returns ``(model_id, family_name,
    revision)``."""
    for family_name, family in registry.items():
        for tuning_status in ("pretrained", "finetuned"):
            if model_key_for(family_name, tuning_status) == model_key:
                model_id = family.pretrained if tuning_status == "pretrained" else family.finetuned
                if not model_id:
                    raise ValueError(
                        f"model_key {model_key!r} resolves to family {family_name!r} "
                        f"({tuning_status}), but configs/models.yaml has no {tuning_status} "
                        f"checkpoint for that family."
                    )
                return model_id, family_name, family.revision
    raise ValueError(
        f"model_key {model_key!r} does not match any family in configs/models.yaml "
        f"(expected '{{family}}-pretrained' or '{{family}}-instruct')."
    )


# ---------------------------------------------------------------------------
# Manifest guard (spec §3.10; WO-5 requirement 6)
# ---------------------------------------------------------------------------


class ManifestGuardError(RuntimeError):
    """Raised when a release's on-disk files don't hash-match
    manifest.json -- refuses to run rather than risk elicitation against
    silently-mutated prompts/vignettes."""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_release_root() -> Path:
    return _repo_root() / "data" / "release"


def default_registry_path() -> Path:
    return _repo_root() / "configs" / "models.yaml"


def verify_release_manifest(release: str, release_root: str | Path | None = None) -> None:
    """Verifies ``data/release/<release>/manifest.json`` hashes over its
    listed files (spec §3.10) -- raises ``ManifestGuardError`` (never a
    bare exception) on any mismatch, missing manifest, or missing file, so
    a caller can print+refuse cleanly. Does nothing (no return value) on
    success."""
    release_root = Path(release_root) if release_root is not None else default_release_root()
    release_dir = release_root / release
    manifest_path = release_dir / "manifest.json"
    if not manifest_path.exists():
        raise ManifestGuardError(
            f"manifest guard: {manifest_path} does not exist -- cannot verify release "
            f"{release!r} before running (spec §3.10). Pass --skip-manifest-check only "
            f"for a throwaway G0 toy run."
        )
    manifest = ReleaseManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
    if manifest.release != release:
        raise ManifestGuardError(
            f"manifest guard: {manifest_path} declares release {manifest.release!r}, "
            f"expected {release!r} (from the run config)."
        )

    errors: list[str] = []
    for filename, entry in manifest.files.items():
        file_path = release_dir / filename
        if not file_path.exists():
            errors.append(f"{filename}: missing at {file_path}")
            continue
        actual_sha = hashlib.sha256(file_path.read_bytes()).hexdigest()
        if actual_sha != entry.sha256:
            errors.append(f"{filename}: sha256 mismatch (manifest={entry.sha256}, actual={actual_sha})")
    if errors:
        raise ManifestGuardError(
            f"manifest guard FAILED for release {release!r} -- refusing to run "
            f"(spec §3.10): " + "; ".join(errors)
        )


# ---------------------------------------------------------------------------
# Sharding (WO-5 requirement 5)
# ---------------------------------------------------------------------------


def shard_jobs(jobs_list: Sequence[JobRecord], shard: tuple[int, int] | None) -> list[JobRecord]:
    """``--shard i/n``: deterministic assignment over the manifest's own
    (job_id) order, ``job_index % n == i``. ``CUDA_VISIBLE_DEVICES`` is
    respected implicitly -- this function has no GPU awareness at all, it
    just partitions the job list; the caller launches one process per GPU,
    each with a different ``i`` and its own ``CUDA_VISIBLE_DEVICES``."""
    if shard is None:
        return list(jobs_list)
    i, n = shard
    if not (0 <= i < n):
        raise ValueError(f"--shard index must satisfy 0 <= i < n; got {shard}")
    return [j for idx, j in enumerate(jobs_list) if idx % n == i]


# ---------------------------------------------------------------------------
# Durability loop (task-5-brief.md architecture): storage restore-on-start
# + periodic/crash-time push.
# ---------------------------------------------------------------------------


def _count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    with open(path, encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def read_results_tolerating_torn_tail(path: str | Path) -> list[ResultRecord]:
    """Reads ``results.jsonl`` for resume, tolerating a missing/empty file
    (nothing done yet, per ``jobs.read_results_tolerant``'s precedent) AND
    a TORN trailing line -- e.g. a SIGKILL that landed after
    ``append_jsonl``'s ``write()`` calls but before/during its ``flush()``,
    or mid-syscall, leaving a partial/invalid JSON fragment as the file's
    last line with no completing newline.

    Only the LAST line is ever treated this leniently: every other line
    failing to parse is still a hard error (real corruption, not a benign
    crash artifact, must stay loud). A torn trailing line just means that
    one row's completion was never durably recorded -- dropping it is
    always safe, since the corresponding job simply gets redone on resume
    (re-running a job is never wrong, only occasionally redundant).

    When a torn tail IS found, the file is also REPAIRED (rewritten to
    contain only the successfully-parsed rows) before returning, so a
    subsequent append starts from a clean, whole-lines-only state -- the
    torn bytes must not linger and get silently glued onto the next
    appended row (which would corrupt both records when re-read later)."""
    path = Path(path)
    if not path.exists() or path.stat().st_size == 0:
        return []

    # Split on "\n" ONLY -- str.splitlines() also splits on U+2028/U+0085
    # etc., and pydantic writes non-ASCII raw, so a completion containing a
    # unicode line separator INSIDE a (legal-JSON) string would be shredded
    # into two invalid fragments and misread as mid-file corruption
    # (main-run job 42, 2026-08-05: llama-instruct row at line 31850).
    lines = [line for line in path.read_text(encoding="utf-8").split("\n") if line.strip()]
    if not lines:
        return []

    results: list[ResultRecord] = []
    torn = False
    for i, line in enumerate(lines):
        is_last = i == len(lines) - 1
        try:
            results.append(ResultRecord.model_validate_json(line))
        except Exception as exc:
            if not is_last:
                raise ValueError(
                    f"{path}: line {i + 1} failed validation against ResultRecord and is NOT "
                    f"the trailing line -- real corruption, not a benign crash artifact: {exc}"
                ) from exc
            torn = True
            print(
                f"WARNING: {path}: trailing line looks torn (crash mid-write, e.g. SIGKILL) -- "
                f"dropping it and repairing the file; the corresponding job will be redone.",
                file=sys.stderr,
            )

    if torn:
        write_jsonl(results, path)
    return results


def restore_completed_results(out_path: str | Path, storage: StorageBackend, remote_key: str) -> None:
    """Ensures ``out_path`` on disk holds whichever of (local file already
    there, storage-backed copy) is more complete. "Fresher" for an
    append-only checkpoint file means MORE ROWS: a brand-new ephemeral node
    with no local state restores entirely from storage; a node resuming its
    own prior run keeps its local file if it's already ahead of the last
    push (e.g. crashed between a checkpoint push and the next one)."""
    out_path = Path(out_path)
    local_n = _count_lines(out_path)
    if not storage.exists(remote_key):
        return
    candidate_path = out_path.with_name(out_path.name + ".remote_candidate")
    storage.pull(remote_key, candidate_path)
    remote_n = _count_lines(candidate_path)
    if remote_n > local_n:
        candidate_path.replace(out_path)
    else:
        candidate_path.unlink(missing_ok=True)


# Tracks the atexit callback most recently registered by
# install_durability_handlers, if any -- module-level so repeated calls
# within one long-lived process (a real CLI process only ever calls this
# once, but a whole pytest SESSION importing/exercising this module many
# times over does not) REPLACE the previous registration instead of
# accumulating one atexit callback per call forever. An unbounded pile of
# stale callbacks -- each referencing a since-deleted tmp_path's out_path/
# storage from an earlier test -- would otherwise fire at interpreter
# exit, printing a "crash-time storage push failed" warning per leftover
# callback (pure noise, but noise that pollutes what should be pristine
# test output).
_installed_atexit_push: Callable[[], None] | None = None


def install_durability_handlers(out_path: str | Path, storage: StorageBackend, remote_key: str) -> Callable[[], None]:
    """Registers atexit + SIGTERM/SIGINT handlers that push ``out_path``'s
    current (already-flushed) contents to storage before the process dies.
    SIGKILL (kill -9) is uncatchable by definition -- it is the per-row
    append+flush discipline in ``run_elicit``'s write loop, not this
    handler, that protects against an ungraceful SIGKILL death (a crash
    loses at most the one in-flight row, never corrupts the file, and a
    restart resumes via the normal set-difference).

    Returns an ``uninstall()`` callable that removes both the atexit
    callback and restores whatever SIGTERM/SIGINT handlers were previously
    installed. A real CLI invocation never needs to call it (the process
    exiting makes the registration moot either way); it exists primarily
    so callers that install these handlers repeatedly within one process
    -- this module's own test suite -- can clean up after themselves
    deterministically instead of relying solely on the replace-not-
    accumulate behavior above."""
    global _installed_atexit_push
    out_path = Path(out_path)

    def _push(*_ignored) -> None:
        try:
            if out_path.exists():
                storage.push(out_path, remote_key)
        except Exception as exc:  # best-effort: never let a durability push crash exit handling
            print(f"WARNING: crash-time storage push failed: {exc}", file=sys.stderr)

    if _installed_atexit_push is not None:
        atexit.unregister(_installed_atexit_push)
    atexit.register(_push)
    _installed_atexit_push = _push

    old_term_handler = signal.getsignal(signal.SIGTERM)
    old_int_handler = signal.getsignal(signal.SIGINT)

    def _signal_handler(signum, _frame):
        _push()
        sys.exit(128 + signum)

    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)

    def uninstall() -> None:
        global _installed_atexit_push
        if _installed_atexit_push is _push:
            atexit.unregister(_push)
            _installed_atexit_push = None
        signal.signal(signal.SIGTERM, old_term_handler)
        signal.signal(signal.SIGINT, old_int_handler)

    return uninstall


# ---------------------------------------------------------------------------
# Defensive parsing wrapper (reviewer-critical fix): a live multi-hour run
# must never crash mid-write over one degenerate row.
# ---------------------------------------------------------------------------


def _safe_parse_with_fallback(raw: str, logprobs_0_10: Sequence[float] | None, threshold_ok: bool) -> ParsedRating:
    """Wraps ``parsing.parse_with_fallback`` so a degenerate
    ``logprobs_0_10`` distribution can never crash the write loop.

    ``parsing.expected_rating_from_logprobs`` (the logit-fallback EV
    computation) raises ``ValueError`` when every one of the 11
    rating-token logprobs is ``-inf`` -- e.g. a response so far off-
    distribution that none of "0".."10" scored above the engine's
    numerical floor anywhere near the answer position. That must never
    propagate out of a single job's parsing and abort a run that may be
    hours into a multi-thousand-row H200 job: this call site catches it
    and degrades to the SAME honest-miss outcome ``parse_with_fallback``
    already returns for an unparseable response with no usable fallback
    (``parse_ok=False``, ``parse_method="regex"``, ``parsed_rating=None``)
    -- the row is still written, just without a rating, exactly like any
    other unparseable response. Never silently coerced to a number."""
    try:
        return parse_with_fallback(raw, logprobs_0_10, threshold_ok)
    except ValueError:
        return ParsedRating(parsed_rating=None, parse_ok=False, parse_method="regex", raw=raw)


# A finite, JSON-round-trip-safe stand-in for -inf/+inf/NaN in a stored
# ResultRecord.logprobs_0_10 -- discovered while adding the degenerate-
# distribution guard above: pydantic's model_dump_json() silently
# serializes any non-finite float as JSON `null`, and ResultRecord.
# logprobs_0_10 is typed `list[float] | None` (spec §3.6, frozen -- NOT
# `list[float | None]`), so a `null` entry FAILS re-validation on the very
# next read of that same file. Left unsanitized, writing one genuinely
# degenerate row (a real, expected output -- FakeEngine's tests construct
# them deliberately, and VllmEngine's exact forced-scoring can legitimately
# score an impossible candidate as -inf) would silently corrupt itself and
# crash every subsequent resume attempt against that file, which is
# exactly the class of "crashes a live H200 run" failure this whole fix is
# about. -1e300 is chosen purely to be (a) finite/JSON-safe and (b) far
# enough below any real logprob that exp(sentinel - max_lp) still
# underflows to exactly 0.0 in float64 -- i.e. numerically inert for
# parsing.expected_rating_from_logprobs's softmax renormalization.
_LOGPROB_NEG_INF_SENTINEL = -1e300


def _sanitize_logprobs_for_storage(logprobs_0_10: list[float] | None) -> list[float] | None:
    """Clamps any non-finite entry (-inf, +inf, NaN) to a finite sentinel
    before it's ever written to disk (see ``_LOGPROB_NEG_INF_SENTINEL``'s
    comment for why). Must be called with the engine's RAW response --
    ``_safe_parse_with_fallback`` above is deliberately given the
    UNSANITIZED logprobs (before this function runs), so its degenerate-
    distribution detection still sees a real, literal -inf and triggers
    correctly; only the value that ends up ON DISK is sanitized."""
    if logprobs_0_10 is None:
        return None
    out = []
    for lp in logprobs_0_10:
        if lp != lp or lp == float("-inf"):  # `lp != lp` is the NaN check
            out.append(_LOGPROB_NEG_INF_SENTINEL)
        elif lp == float("inf"):  # pragma: no cover -- +inf is never a real logprob; defensive only
            out.append(-_LOGPROB_NEG_INF_SENTINEL)
        else:
            out.append(lp)
    return out


# ---------------------------------------------------------------------------
# Throughput reporting (WO-5 requirement 7)
# ---------------------------------------------------------------------------


def _print_throughput_report(
    n_done: int, n_total: int, start_time: float, parse_stats: dict[str, list[int]],
) -> None:
    elapsed = time.perf_counter() - start_time
    rate = n_done / elapsed if elapsed > 0 else 0.0
    remaining = max(n_total - n_done, 0)
    eta_sec = remaining / rate if rate > 0 else float("inf")
    parse_bits = " ".join(
        f"{mk}={ok}/{tot}({ok / tot:.0%})" for mk, (ok, tot) in sorted(parse_stats.items()) if tot
    )
    print(
        f"[elicit] {n_done}/{n_total} rows done, {rate:.1f} rows/sec, "
        f"ETA {eta_sec:.0f}s -- parse-rate: {parse_bits}",
        file=sys.stderr,
    )


def _print_final_report(n_done: int, elapsed: float, parse_stats: dict[str, list[int]]) -> dict[str, float]:
    """Prints the end-of-run per-checkpoint parse-rate summary + the
    prominent logit-fallback instruction for any checkpoint under the 95%
    threshold. Returns {model_key: parse_rate} for the runlog entry."""
    rate = n_done / elapsed if elapsed > 0 else 0.0
    print(f"[elicit] DONE: {n_done} rows in {elapsed:.1f}s ({rate:.1f} rows/sec)", file=sys.stderr)

    parse_rate_by_model_key: dict[str, float] = {}
    for model_key, (ok, tot) in sorted(parse_stats.items()):
        if tot == 0:
            continue
        checkpoint_rate = ok / tot
        parse_rate_by_model_key[model_key] = checkpoint_rate
        print(f"[elicit] checkpoint {model_key!r}: parse_rate={checkpoint_rate:.1%} ({ok}/{tot})", file=sys.stderr)
        if checkpoint_rate < PARSE_RATE_THRESHOLD:
            print(
                f"WARNING: checkpoint {model_key!r} parse rate {checkpoint_rate:.1%} is below "
                f"the {PARSE_RATE_THRESHOLD:.0%} threshold (spec §4.4) -- rerun with "
                f"`--logit-fallback {model_key}`, or add {model_key!r} to the run config's "
                f"`logit_fallback_checkpoints` list (the config key to set), to enable "
                f"expected-value scoring from logprobs for this checkpoint.",
                file=sys.stderr,
            )
    return parse_rate_by_model_key


# ---------------------------------------------------------------------------
# The runner
# ---------------------------------------------------------------------------


def run_elicit(
    *,
    jobs_path: str | Path,
    prompts_path: str | Path,
    run_config_path: str | Path,
    out_path: str | Path = "results.jsonl",
    engine_name: str = "fake",
    engine: GenerationEngine | None = None,
    shard: tuple[int, int] | None = None,
    limit: int | None = None,
    storage: StorageBackend | None = None,
    storage_config_path: str | Path | None = None,
    checkpoint_every: int = DEFAULT_CHECKPOINT_EVERY,
    batch_size: int = DEFAULT_BATCH_SIZE,
    report_every_batches: int = DEFAULT_REPORT_EVERY_BATCHES,
    skip_manifest_check: bool = False,
    release_root: str | Path | None = None,
    registry_path: str | Path | None = None,
    logit_fallback_checkpoints: Sequence[str] = (),
    dtype: str = "bfloat16",
    gpu_memory_utilization: float = 0.9,
    runlog_path: str | Path | None = None,
    remote_key: str | None = None,
    install_signal_handlers: bool = True,
) -> int:
    """Full orchestration: manifest guard -> storage restore -> resume
    set-difference -> shard/limit -> group by (model_key, format) -> one
    model resident at a time -> generate + parse + append + checkpoint ->
    throughput report. Returns a process exit code (0 success, 1 a
    checked/expected refusal, e.g. the manifest guard)."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    run_config = load_run_config(run_config_path)
    release = run_config.release

    if skip_manifest_check:
        print(
            f"WARNING: --skip-manifest-check passed -- SKIPPING the release manifest hash "
            f"guard for release {release!r} (spec §3.10). Only use this for a throwaway G0 "
            f"toy run, never a real dataset run.",
            file=sys.stderr,
        )
    else:
        try:
            verify_release_manifest(release, release_root)
        except ManifestGuardError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1

    if storage is None:
        storage = load_storage_config(storage_config_path) if storage_config_path else NullStorage()

    remote_key = remote_key or f"results/{release}/{out_path.name}"
    restore_completed_results(out_path, storage, remote_key)

    if install_signal_handlers:
        install_durability_handlers(out_path, storage, remote_key)

    all_jobs = read_jsonl(jobs_path, JobRecord)
    sharded_jobs = shard_jobs(all_jobs, shard)

    existing_results = read_results_tolerating_torn_tail(out_path)
    remaining, diff_report = diff_jobs(sharded_jobs, existing_results)
    if limit is not None:
        remaining = remaining[:limit]

    print(
        f"[elicit] shard_total={len(sharded_jobs)} already_done={diff_report.done} "
        f"remaining(after --limit)={len(remaining)}",
        file=sys.stderr,
    )

    prompts_by_id = {p.prompt_id: p for p in read_jsonl(prompts_path, PromptRecord)}
    registry = load_registry(registry_path or default_registry_path())

    if engine is None:
        engine = build_engine(engine_name)

    groups: dict[tuple[str, str], list[JobRecord]] = defaultdict(list)
    for job in remaining:
        prompt = prompts_by_id.get(job.prompt_id)
        if prompt is None:
            raise ValueError(
                f"job {job.job_id!r} references prompt_id {job.prompt_id!r}, not found in {prompts_path}"
            )
        groups[(job.model_key, prompt.format)].append(job)

    # Union of the CLI's --logit-fallback flag and the run config's own
    # `logit_fallback_checkpoints` list -- either can name a checkpoint,
    # so the decision can live durably in version control (the run
    # config) or be set ad hoc for one invocation (the CLI flag).
    logit_fallback_set = set(logit_fallback_checkpoints) | set(run_config.logit_fallback_checkpoints)
    parse_stats: dict[str, list[int]] = defaultdict(lambda: [0, 0])

    n_rows_since_checkpoint = 0
    n_rows_total = 0
    n_batches = 0
    n_jobs_total_this_run = len(remaining)
    start_time = time.perf_counter()
    current_model_key: str | None = None
    current_revision: str | None = None

    with open(out_path, "a", encoding="utf-8") as fh:
        for group_key in sorted(groups):
            model_key, fmt = group_key
            group_jobs = groups[group_key]

            if model_key != current_model_key:
                model_id, _family_name, pinned_revision = resolve_model_id(model_key, registry)
                current_revision = engine.load(
                    model_id, revision=pinned_revision, dtype=dtype,
                    gpu_memory_utilization=gpu_memory_utilization,
                )
                current_model_key = model_key
                print(
                    f"[elicit] loaded model_key={model_key} model_id={model_id} "
                    f"revision={current_revision}",
                    file=sys.stderr,
                )

            threshold_ok = model_key not in logit_fallback_set

            for batch_start in range(0, len(group_jobs), batch_size):
                batch_jobs = group_jobs[batch_start : batch_start + batch_size]
                requests = [
                    EngineRequest(
                        job_id=job.job_id,
                        prompt_id=job.prompt_id,
                        temperature=job.temperature,
                        seed=job.seed,
                        max_tokens=10,
                        text=prompts_by_id[job.prompt_id].text if fmt != "chat" else None,
                        messages=prompts_by_id[job.prompt_id].messages if fmt == "chat" else None,
                        want_first_token_logprobs=True,
                    )
                    for job in batch_jobs
                ]
                responses_by_id = {r.job_id: r for r in engine.generate(requests)}

                for job in batch_jobs:
                    resp = responses_by_id[job.job_id]
                    # Degenerate-distribution detection must see the RAW
                    # (possibly literally -inf) logprobs; only the value
                    # written to disk gets sanitized -- see both functions'
                    # docstrings.
                    parsed = _safe_parse_with_fallback(resp.raw_response, resp.logprobs_0_10, threshold_ok)
                    result = ResultRecord(
                        job_id=job.job_id,
                        prompt_id=job.prompt_id,
                        model_key=job.model_key,
                        sample_idx=job.sample_idx,
                        temperature=job.temperature,
                        seed=job.seed,
                        raw_response=resp.raw_response,
                        parsed_rating=parsed.parsed_rating,
                        parse_ok=parsed.parse_ok,
                        parse_method=parsed.parse_method,
                        logprobs_0_10=_sanitize_logprobs_for_storage(resp.logprobs_0_10),
                        model_revision=current_revision,
                        runner_version=RUNNER_VERSION,
                        timestamp=time.time(),
                    )
                    append_jsonl(result, fh)
                    n_rows_since_checkpoint += 1
                    n_rows_total += 1
                    parse_stats[model_key][1] += 1
                    if parsed.parse_ok:
                        parse_stats[model_key][0] += 1

                n_batches += 1
                if n_rows_since_checkpoint >= checkpoint_every:
                    storage.push(out_path, remote_key)
                    n_rows_since_checkpoint = 0
                if n_batches % report_every_batches == 0:
                    _print_throughput_report(n_rows_total, n_jobs_total_this_run, start_time, parse_stats)

    # Final push regardless of checkpoint interval, so a normal
    # (non-crash) completion also lands the final shard in storage.
    storage.push(out_path, remote_key)

    elapsed = time.perf_counter() - start_time
    parse_rate_by_model_key = _print_final_report(n_rows_total, elapsed, parse_stats)

    if runlog_path is not None:
        runlog_path = Path(runlog_path)
        runlog_path.parent.mkdir(parents=True, exist_ok=True)
        entry = ElicitRunLogEntry(
            timestamp=time.time(),
            engine=engine_name,
            release=release,
            n_jobs_total=n_jobs_total_this_run,
            n_jobs_done_before=diff_report.done,
            n_jobs_run=n_rows_total,
            wall_time_sec=elapsed,
            parse_rate_by_model_key=parse_rate_by_model_key,
        )
        with open(runlog_path, "a", encoding="utf-8") as f:
            append_jsonl(entry, f)

    return 0


# ---------------------------------------------------------------------------
# CLI-facing orchestration (called by knobe.cli's "elicit" subcommand)
# ---------------------------------------------------------------------------


def run(
    *,
    jobs_path: str | Path,
    prompts_path: str | Path,
    run_config_path: str | Path,
    out_path: str | Path = "results.jsonl",
    engine_name: str = "vllm",
    shard: tuple[int, int] | None = None,
    limit: int | None = None,
    storage_config_path: str | Path | None = None,
    checkpoint_every: int = DEFAULT_CHECKPOINT_EVERY,
    batch_size: int = DEFAULT_BATCH_SIZE,
    report_every_batches: int = DEFAULT_REPORT_EVERY_BATCHES,
    skip_manifest_check: bool = False,
    release_root: str | Path | None = None,
    registry_path: str | Path | None = None,
    logit_fallback_checkpoints: Sequence[str] = (),
    dtype: str = "bfloat16",
    gpu_memory_utilization: float = 0.9,
    runlog_path: str | Path | None = None,
) -> int:
    """``knobe elicit``'s CLI entry point: fills in the runlog default path
    (alongside ``--out``, matching ``curate.run``'s convention) and
    delegates to ``run_elicit``."""
    runlog_path = runlog_path if runlog_path is not None else Path(out_path).parent / "elicit_runlog.jsonl"
    return run_elicit(
        jobs_path=jobs_path,
        prompts_path=prompts_path,
        run_config_path=run_config_path,
        out_path=out_path,
        engine_name=engine_name,
        shard=shard,
        limit=limit,
        storage_config_path=storage_config_path,
        checkpoint_every=checkpoint_every,
        batch_size=batch_size,
        report_every_batches=report_every_batches,
        skip_manifest_check=skip_manifest_check,
        release_root=release_root,
        registry_path=registry_path,
        logit_fallback_checkpoints=logit_fallback_checkpoints,
        dtype=dtype,
        gpu_memory_utilization=gpu_memory_utilization,
        runlog_path=runlog_path,
    )
