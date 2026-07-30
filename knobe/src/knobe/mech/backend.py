"""S6: the mechanistic-interpretability access layer (master spec §3.7-3.8,
§5; WO-6 Part A).

``ResidualAccess`` is the ONE interface every mech script (cache_acts.py,
patch.py, and later probes.py/decompose.py) talks to. No script imports
TransformerLens or nnsight directly -- spec §5.1: "Backend via
mech/backend.py's ResidualAccess interface only ... No script imports TL
directly." torch never leaks across this boundary either: every method
takes/returns plain Python + numpy, so the orchestration layer, and this
whole repo's default (GPU-free) test suite, never import torch.

Three implementations:
  - ``TLBackend`` (guarded ``transformer_lens`` import): the primary impl.
  - ``NnsightBackend`` (guarded ``nnsight`` import): selected per-family via
    the registry ``mech_backend: nnsight`` field, for models TL lacks a
    ``HookedTransformer`` config for.
  - ``FakeBackend`` (pure numpy, deterministic): the test vehicle. Unlike a
    dumb stub it implements REAL patching semantics over a tiny linear fake
    "model" -- run_patched genuinely replaces the recipient's residual at
    the named layer(s) with the donor's and recomputes the downstream
    forward -- so the self-patch identity test and the planted-signal
    cache->sweep->metrics loop are meaningful, not tautological.

Layer-index convention (canonical across cache_acts.py, patch.py, and the
δ_l / patch tables) -- pick one, use it EVERYWHERE:
  A residual cache is ``n_layers + 1`` "slices" stacked on axis 1. Slice
  ``s`` (an int in ``0..n_layers``) is:
    * ``s == 0``          -> resid_pre.0   (pre-block-0, the embedding).
    * ``s`` in 1..n_layers -> resid_post.(s-1) (output of block s-1).
  "layer ``s``" means slice ``s`` for BOTH δ_l and patching: patching
  "layer s" replaces slice ``s`` at every token position with the donor's
  slice ``s`` and continues the forward pass. In TransformerLens hook
  terms that is ``blocks.0.hook_resid_pre`` for s==0 and
  ``blocks.(s-1).hook_resid_post`` for s>=1 (see ``TLBackend``).
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Callable, Literal, Protocol, Sequence, runtime_checkable

import numpy as np

Positions = Literal["final", "all"]

# ---------------------------------------------------------------------------
# The residual-cache container returned across the backend boundary.
# ---------------------------------------------------------------------------


@dataclass
class Acts:
    """A residual-stream cache, numpy at the boundary (spec §3.7). ``resid``
    is ``float16`` shaped ``[n_prompts, len(layers), d_model]`` -- the
    residual stream at the FINAL prompt token when ``positions == "final"``
    (the "Answer:" position; the only thing shipped back to local per
    §3.7). ``layers`` gives the slice index (see the module docstring's
    convention) for each column of axis 1, so a subset cache still records
    which slices it holds. ``prompt_index[i]`` is the position of row ``i``
    in the caller's original ``prompts`` list (identity unless the backend
    reorders)."""

    resid: np.ndarray  # float16 [n_prompts, len(layers), d_model]
    prompt_index: list[int]
    layers: list[int]
    positions: str
    model_key: str

    def __post_init__(self) -> None:
        if self.resid.ndim != 3:
            raise ValueError(f"Acts.resid must be 3-D [n_prompts, n_slices, d_model]; got {self.resid.shape}")
        n, n_slices, _ = self.resid.shape
        if len(self.prompt_index) != n:
            raise ValueError(f"prompt_index length {len(self.prompt_index)} != n_prompts {n}")
        if len(self.layers) != n_slices:
            raise ValueError(f"layers length {len(self.layers)} != resid axis-1 {n_slices}")


class TokenizerMismatchError(RuntimeError):
    """Raised when a patch's donor and recipient don't tokenize a prompt
    identically (spec §5.5 / WO-6 Part C.6). Patching splices the donor's
    residual at token position *p* into the recipient at the same position
    *p*; if the two models' tokenizers disagree on sequence length (or
    tokenization) for a prompt, position *p* doesn't denote the same thing
    in both, so the patch is meaningless -- a hard error, never a silent
    misalignment."""


def _assert_patchable(recipient: "ResidualAccess", donor: "ResidualAccess", prompts: Sequence[str]) -> None:
    """The two cross-cutting patch preconditions, in ONE place for all three
    backends: (1) donor and recipient are the SAME backend implementation --
    the pretrained/finetuned checkpoints of one family share a backend
    (registry ``mech_backend``); (2) they tokenize every prompt identically,
    so a token position denotes the same thing in both (spec §5.5). Either
    failure is a hard error, never a silent misalignment."""
    if type(donor) is not type(recipient):
        raise TypeError(
            f"{type(recipient).__name__}.run_patched requires a same-implementation donor "
            f"(got {type(donor).__name__}); donor/recipient are the pretrained/finetuned "
            f"checkpoints of one family and share a backend."
        )
    for p in prompts:
        n_r, n_d = recipient.n_tokens(p), donor.n_tokens(p)
        if n_r != n_d:
            raise TokenizerMismatchError(
                f"donor/recipient tokenization mismatch for prompt {p!r}: recipient "
                f"{recipient.model_key!r} has {n_r} tokens, donor {donor.model_key!r} has "
                f"{n_d} (spec §5.5 -- patching requires identical tokenization)."
            )


@runtime_checkable
class ResidualAccess(Protocol):
    """The interface every mech script uses (spec §5.1). Implementations:
    ``TLBackend`` / ``NnsightBackend`` (real, GPU) and ``FakeBackend``
    (numpy). A patch's ``donor`` must be the SAME implementation class as
    the recipient (both TL, or both fake) -- donor and recipient are the
    pretrained/finetuned checkpoints of ONE family, which share a backend
    (registry ``mech_backend``)."""

    n_layers: int
    d_model: int
    model_key: str

    def run_with_cache(
        self,
        prompts: Sequence[str],
        layers: Sequence[int] | None = None,
        positions: Positions = "final",
    ) -> Acts: ...

    def logits_0_10(self, prompts: Sequence[str]) -> np.ndarray:
        """Log-probabilities over the eleven rating tokens "0".."10" at the
        answer position: ``[n_prompts, 11]`` (rows are log-softmax
        normalised over just those 11 tokens). patch.py turns these into an
        expected-value rating via ``parsing.expected_rating_from_logprobs``
        (scoring == "logits_0_10", deterministic -- no sampling)."""
        ...

    def run_patched(
        self,
        prompts: Sequence[str],
        donor: "ResidualAccess",
        layers: Sequence[int],
        positions: str = "all",
        scoring: str = "logits_0_10",
    ) -> np.ndarray:
        """Replace the recipient's residual stream at ``layers`` (all token
        positions) with ``donor``'s activations from the SAME prompt, then
        continue the forward pass; return the patched ``logits_0_10``
        ``[n_prompts, 11]`` (spec §5.2). Hard-errors on tokenizer mismatch
        (``TokenizerMismatchError``)."""
        ...

    def run_patched_with_cache(
        self,
        prompts: Sequence[str],
        donor: "ResidualAccess",
        layers: Sequence[int],
        positions: Positions = "final",
    ) -> Acts:
        """Like ``run_patched`` but returns the patched RESIDUAL cache (an
        ``Acts``) instead of the rating logits -- the downstream final-token
        residuals AFTER splicing ``donor``'s activations at ``layers``. RQ4
        (decompose.py) sources Δh = ``run_patched_with_cache`` −
        ``run_with_cache`` from this (WO-7): the patch-induced activation
        shift at every downstream layer, without persisting a second large
        patched-acts cache (patch.py's on-disk contract stays unchanged).
        Hard-errors on tokenizer mismatch (``TokenizerMismatchError``)."""
        ...

    def n_tokens(self, prompt: str) -> int:
        """Token count for ``prompt`` under this model's tokenizer -- used
        by ``run_patched`` to assert donor/recipient sequence alignment
        (spec §5.5)."""
        ...


# ---------------------------------------------------------------------------
# Deterministic hashing helpers for FakeBackend (no bare RNG -- every value
# is a pure function of a string key, so runs reproduce byte-for-byte;
# common-context.md constraint 4).
# ---------------------------------------------------------------------------


def _hash_floats(key: str, n: int) -> np.ndarray:
    """``n`` deterministic, ~standard-normal floats from sha256(key). Uses a
    counter-mode digest stream so length is unbounded and independent of
    ``n``'s value elsewhere."""
    out = np.empty(n, dtype=np.float64)
    filled = 0
    counter = 0
    while filled < n:
        digest = hashlib.sha256(f"{key}|{counter}".encode("utf-8")).digest()
        # Four 8-byte chunks per digest -> four uniforms in [0,1), each
        # mapped to a zero-mean, unit-variance value by centering and
        # scaling by sqrt(12) (Var(U[0,1]) = 1/12). Not a true Gaussian, but
        # for a deterministic FAKE model all that matters is that the values
        # are zero-mean, unit-variance, and reproducible -- not their exact
        # marginal shape.
        vals = np.frombuffer(digest, dtype=np.uint64).astype(np.float64) / 2**64  # 4 uniforms in [0,1)
        take = min(4, n - filled)
        out[filled : filled + take] = (vals[:take] - 0.5) * np.sqrt(12.0)
        filled += take
        counter += 1
    return out


def _unit_vector(key: str, d: int) -> np.ndarray:
    v = _hash_floats(key, d)
    norm = np.linalg.norm(v)
    return v / norm if norm > 0 else v


# label_fn: prompt text -> (content_key, sign). ``sign`` in {-1, 0, +1}
# (bad = +1, good = -1, neutral/unknown = 0). ``content_key`` strips the
# sign so a matched bad/good pair shares a residual "base" -- the basis for
# the deterministic planted-signal contrast.
LabelFn = Callable[[str], "tuple[str, int]"]


def _default_label(prompt: str) -> "tuple[str, int]":
    return prompt, 0


@dataclass
class PlantedSignal:
    """A known per-layer bad/good contrast injected into a FakeBackend's
    forward pass (WO-6: "supports a constructed 'planted signal' mode where
    the test can inject a known per-layer contrast"). The signal is a fixed
    vector (aligned with the model's readout direction, so it moves the
    rating) added into slice ``layer`` with coefficient ``+magnitude`` for
    bad prompts and ``-magnitude`` for good ones. Because the forward pass
    carries residuals downstream with decay, the signal is strongest
    exactly at ``layer`` (δ_l peaks there) and the ONLY layer whose patch
    removes it at the source is ``layer`` itself -- which is what makes the
    end-to-end planted-signal acceptance test genuinely discriminate."""

    layer: int
    magnitude: float = 1.0


# ---------------------------------------------------------------------------
# FakeBackend -- deterministic numpy "model" with REAL patching semantics.
# ---------------------------------------------------------------------------


class FakeBackend:
    """A GPU-free ``ResidualAccess`` whose residual stream is a genuine
    (if tiny + linear) forward pass, so patching is a real intervention.

    Forward pass (per prompt, per residual slice ``s`` = 0..n_layers):

        resid[0]   = base(content, 0)
        resid[s+1] = decay * resid[s] + base(content, s+1) + signal(s+1)

    ``base(content, s)`` is a deterministic hash vector for (model_key,
    content_key, slice), projected ORTHOGONAL to the readout direction --
    so it varies the residual per item and per layer but contributes
    exactly zero to the read-out rating (keeping the rating a clean
    function of the planted signal alone). ``signal(s)`` is nonzero only at
    the planted layer and only when ``sign != 0``: ``sign * magnitude *
    readout_dir``.

    Read-out: ``feature = Σ_s resid[s]·readout_dir`` (a scalar summed over
    ALL slices, so a patch that removes the signal from a downstream subset
    of slices changes the rating by exactly the removed portion -- the
    property the planted-signal test relies on). ``rating_center =
    clip(5 + gain*feature, 0, 10)``; ``logits_0_10`` is a peaked
    distribution centred there.

    Determinism: every number is a pure function of string keys -- identical
    inputs reproduce byte-for-byte across processes.
    """

    def __init__(
        self,
        model_key: str,
        n_layers: int,
        d_model: int,
        *,
        label_fn: LabelFn | None = None,
        planted: PlantedSignal | None = None,
        decay: float = 0.5,
        gain: float = 1.3,
        sharpness: float = 0.7,
        base_scale: float = 0.1,
        tokens_fn: Callable[[str], int] | None = None,
    ):
        if n_layers < 1:
            raise ValueError("n_layers must be >= 1")
        if planted is not None and not (0 <= planted.layer <= n_layers):
            raise ValueError(f"planted.layer {planted.layer} out of range 0..{n_layers}")
        self.model_key = model_key
        self.n_layers = n_layers
        self.d_model = d_model
        self._label = label_fn or _default_label
        self.planted = planted
        self.decay = decay
        self.gain = gain
        self.sharpness = sharpness
        self.base_scale = base_scale
        self._tokens_fn = tokens_fn or (lambda p: len(p.split()))
        # Readout direction is per-model (salted by model_key). The planted
        # signal aligns with THIS model's readout, since patched forwards
        # always read out through the recipient.
        self._readout_dir = _unit_vector(f"{model_key}|readout", d_model)

    # -- forward pass -------------------------------------------------------

    def _base(self, content_key: str, slice_idx: int) -> np.ndarray:
        raw = _hash_floats(f"{self.model_key}|base|{content_key}|{slice_idx}", self.d_model)
        # Project out the readout direction so base contributes nothing to
        # the rating (see class docstring).
        raw = raw - np.dot(raw, self._readout_dir) * self._readout_dir
        return raw * self.base_scale

    def _forward(self, prompt: str, patch: "dict[int, np.ndarray] | None" = None) -> np.ndarray:
        """Full residual stack ``[n_layers+1, d_model]`` (float64). ``patch``
        maps a slice index -> donor residual to splice in AFTER that slice
        is computed, then continue (real patching semantics)."""
        content_key, sign = self._label(prompt)
        resid = np.zeros((self.n_layers + 1, self.d_model), dtype=np.float64)
        resid[0] = self._base(content_key, 0)
        if self.planted is not None and self.planted.layer == 0 and sign != 0:
            resid[0] = resid[0] + sign * self.planted.magnitude * self._readout_dir
        if patch is not None and 0 in patch:
            resid[0] = patch[0]
        for s in range(1, self.n_layers + 1):
            new = self.decay * resid[s - 1] + self._base(content_key, s)
            if self.planted is not None and self.planted.layer == s and sign != 0:
                new = new + sign * self.planted.magnitude * self._readout_dir
            resid[s] = new
            if patch is not None and s in patch:
                # Replace resid_post at this layer for "all positions", then
                # continue -- the spec §5.2 procedure.
                resid[s] = patch[s]
        return resid

    def _readout_logprobs(self, resid_stack: np.ndarray) -> np.ndarray:
        feature = float(np.sum(resid_stack @ self._readout_dir))
        center = 5.0 + self.gain * feature
        center = min(10.0, max(0.0, center))
        idx = np.arange(11, dtype=np.float64)
        logits = -self.sharpness * (idx - center) ** 2
        logits -= logits.max()
        logsumexp = np.log(np.sum(np.exp(logits)))
        return logits - logsumexp

    # -- ResidualAccess interface ------------------------------------------

    def n_tokens(self, prompt: str) -> int:
        return self._tokens_fn(prompt)

    def run_with_cache(
        self,
        prompts: Sequence[str],
        layers: Sequence[int] | None = None,
        positions: Positions = "final",
    ) -> Acts:
        prompts = list(prompts)
        want = list(range(self.n_layers + 1)) if layers is None else list(layers)
        for s in want:
            if not (0 <= s <= self.n_layers):
                raise ValueError(f"layer {s} out of range 0..{self.n_layers}")
        stacks = [self._forward(p) for p in prompts]  # each [n_layers+1, d_model]
        # FakeBackend has no token axis: "final" and "all" return the same
        # per-prompt residual (a single conceptual position). Real backends
        # distinguish them; here it keeps patching (which needs donor
        # residuals for "all" positions) and caching (final token) uniform.
        resid = np.stack([st[want] for st in stacks], axis=0).astype(np.float16)
        return Acts(
            resid=resid,
            prompt_index=list(range(len(prompts))),
            layers=want,
            positions=positions,
            model_key=self.model_key,
        )

    def logits_0_10(self, prompts: Sequence[str]) -> np.ndarray:
        return np.stack([self._readout_logprobs(self._forward(p)) for p in prompts], axis=0)

    def run_patched(
        self,
        prompts: Sequence[str],
        donor: "ResidualAccess",
        layers: Sequence[int],
        positions: str = "all",
        scoring: str = "logits_0_10",
    ) -> np.ndarray:
        prompts = list(prompts)
        _assert_patchable(self, donor, prompts)
        patch_layers = list(layers)
        for s in patch_layers:
            if not (0 <= s <= self.n_layers):
                raise ValueError(f"patch layer {s} out of range 0..{self.n_layers}")
        out = np.empty((len(prompts), 11), dtype=np.float64)
        for i, p in enumerate(prompts):
            # Donor residuals at full compute precision (spec §5.2 -- real
            # backends keep bf16 on-GPU; the fp16 in Acts is only the
            # ON-DISK cache dtype §3.7, never the patch-time precision). Using
            # donor._forward directly rather than the fp16 run_with_cache is
            # what makes the self-patch (donor is recipient) identity EXACT.
            donor_stack = donor._forward(p)  # [n_layers+1, d_model] float64
            patch = {s: donor_stack[s] for s in patch_layers}
            patched_stack = self._forward(p, patch=patch)
            out[i] = self._readout_logprobs(patched_stack)
        return out

    def run_patched_with_cache(
        self,
        prompts: Sequence[str],
        donor: "ResidualAccess",
        layers: Sequence[int],
        positions: Positions = "final",
    ) -> Acts:
        prompts = list(prompts)
        _assert_patchable(self, donor, prompts)
        patch_layers = list(layers)
        for s in patch_layers:
            if not (0 <= s <= self.n_layers):
                raise ValueError(f"patch layer {s} out of range 0..{self.n_layers}")
        want = list(range(self.n_layers + 1))
        stacks = []
        for p in prompts:
            donor_stack = donor._forward(p)  # full-precision donor residuals
            patch = {s: donor_stack[s] for s in patch_layers}
            stacks.append(self._forward(p, patch=patch)[want])
        resid = np.stack(stacks, axis=0).astype(np.float16)
        return Acts(resid, list(range(len(prompts))), want, positions, self.model_key)


# ---------------------------------------------------------------------------
# Guarded real-backend imports (never required at test time; deselected-by
# -default gpu tests exercise them on the H200 -- common-context.md
# constraint 7).
# ---------------------------------------------------------------------------

try:
    import torch
except ImportError:  # pragma: no cover -- exercised whenever the 'mech'/'hf' extra isn't installed
    torch = None

try:
    from transformer_lens import HookedTransformer
except ImportError:  # pragma: no cover -- same
    HookedTransformer = None

try:
    import nnsight  # noqa: F401
except ImportError:  # pragma: no cover -- same
    nnsight = None


def _resid_hook_name(slice_idx: int) -> str:
    """The TransformerLens hook name for a canonical slice index (see the
    module docstring's convention): slice 0 -> the block-0 resid_pre
    (embedding); slice s>=1 -> block (s-1)'s resid_post."""
    if slice_idx == 0:
        return "blocks.0.hook_resid_pre"
    return f"blocks.{slice_idx - 1}.hook_resid_post"


class TLBackend:
    """TransformerLens-backed ``ResidualAccess`` (spec §5.1's primary impl).

    NOT exercised by this repo's default suite -- ``transformer_lens`` is a
    heavy GPU extra deliberately not installed here (common-context.md
    constraint 7); the ``@pytest.mark.gpu`` tests in tests/test_mech_gpu.py
    exercise it on the H200. The code below is written to a careful reading
    of the TL API but its exact behaviour (hook names, cache keys, the
    from_pretrained_no_processing dtype path) is what those gpu tests must
    confirm.

    Two load choices are deliberate and MUST NOT be "cleaned up":

    * ``from_pretrained_no_processing`` (NOT ``from_pretrained``): patching
      must operate on the SAME residual basis as the native model. The
      processed loader folds LayerNorm into adjacent weights and centres /
      re-scales the residual writing weights; a pretrained activation cached
      under that transformed basis is not interchangeable with the
      finetuned model's residual, so splicing one into the other would be
      comparing apples to a rotated, re-centred pear. ``no_processing``
      keeps the raw residual stream so donor and recipient share a basis.
    * explicit ``dtype=torch.bfloat16``: TransformerLens defaults to fp32,
      which for a 27B-class model (and even the 9B core models here, with
      two checkpoints resident at once, spec §5.2) OOMs a single H200.
      bf16 is the run's compute dtype; fp16 is only the on-disk cache dtype
      (§3.7).
    """

    def __init__(self, model_key: str, model_name: str, n_layers: int, d_model: int, revision: str = "main"):
        if HookedTransformer is None:
            raise RuntimeError(
                "transformer_lens is required for TLBackend -- install the 'mech' extra "
                "(`uv pip install -e '.[mech]'`) or use FakeBackend."
            )
        self.model_key = model_key
        self.n_layers = n_layers
        self.d_model = d_model
        self._model = HookedTransformer.from_pretrained_no_processing(
            model_name, dtype=torch.bfloat16, revision=revision,
        )
        self._model.eval()
        self._tokenizer = self._model.tokenizer
        self._rating_token_ids = _rating_token_ids(self._tokenizer)

    def n_tokens(self, prompt: str) -> int:
        return len(self._tokenizer.encode(prompt))

    def _cache_names(self, layers: Sequence[int] | None) -> list[int]:
        return list(range(self.n_layers + 1)) if layers is None else list(layers)

    def run_with_cache(
        self,
        prompts: Sequence[str],
        layers: Sequence[int] | None = None,
        positions: Positions = "final",
    ) -> Acts:  # pragma: no cover -- gpu-only
        prompts = list(prompts)
        want = self._cache_names(layers)
        names = {_resid_hook_name(s) for s in want}
        rows = []
        with torch.no_grad():
            for prompt in prompts:
                tokens = self._model.to_tokens(prompt)
                _, cache = self._model.run_with_cache(
                    tokens, names_filter=lambda n: n in names,
                )
                # Final prompt token = the "Answer:" position (§3.7).
                pos = -1 if positions == "final" else slice(None)
                slices = [cache[_resid_hook_name(s)][0, pos].float().cpu().numpy() for s in want]
                rows.append(np.stack(slices, axis=0))
        resid = np.stack(rows, axis=0).astype(np.float16)
        return Acts(resid, list(range(len(prompts))), want, positions, self.model_key)

    def logits_0_10(self, prompts: Sequence[str]) -> np.ndarray:  # pragma: no cover -- gpu-only
        out = np.empty((len(prompts), 11), dtype=np.float64)
        with torch.no_grad():
            for i, prompt in enumerate(prompts):
                tokens = self._model.to_tokens(prompt)
                logits = self._model(tokens)[0, -1]  # final-position next-token logits
                out[i] = _rating_logprobs_from_logits(logits, self._rating_token_ids)
        return out

    def run_patched(
        self,
        prompts: Sequence[str],
        donor: "ResidualAccess",
        layers: Sequence[int],
        positions: str = "all",
        scoring: str = "logits_0_10",
    ) -> np.ndarray:  # pragma: no cover -- gpu-only
        prompts = list(prompts)
        _assert_patchable(self, donor, prompts)
        patch_layers = list(layers)
        out = np.empty((len(prompts), 11), dtype=np.float64)
        with torch.no_grad():
            for i, prompt in enumerate(prompts):
                tokens = self._model.to_tokens(prompt)
                donor_tokens = donor._model.to_tokens(prompt)
                names = {_resid_hook_name(s) for s in patch_layers}
                _, donor_cache = donor._model.run_with_cache(
                    donor_tokens, names_filter=lambda n: n in names,
                )

                def _hook(activation, hook, _cache=donor_cache):
                    # Replace resid at this layer for ALL positions with the
                    # donor's cached activation (spec §5.2).
                    return _cache[hook.name].to(activation.dtype)

                fwd_hooks = [(_resid_hook_name(s), _hook) for s in patch_layers]
                logits = self._model.run_with_hooks(tokens, fwd_hooks=fwd_hooks)[0, -1]
                out[i] = _rating_logprobs_from_logits(logits, self._rating_token_ids)
        return out

    def run_patched_with_cache(
        self,
        prompts: Sequence[str],
        donor: "ResidualAccess",
        layers: Sequence[int],
        positions: Positions = "final",
    ) -> Acts:  # pragma: no cover -- gpu-only
        prompts = list(prompts)
        _assert_patchable(self, donor, prompts)
        patch_layers = list(layers)
        want = list(range(self.n_layers + 1))
        cache_names = {_resid_hook_name(s) for s in want}
        patch_names = {_resid_hook_name(s) for s in patch_layers}
        rows = []
        with torch.no_grad():
            for prompt in prompts:
                tokens = self._model.to_tokens(prompt)
                donor_tokens = donor._model.to_tokens(prompt)
                _, donor_cache = donor._model.run_with_cache(
                    donor_tokens, names_filter=lambda n: n in patch_names,
                )

                def _hook(activation, hook, _cache=donor_cache):
                    return _cache[hook.name].to(activation.dtype)

                fwd_hooks = [(_resid_hook_name(s), _hook) for s in patch_layers]
                _, patched_cache = self._model.run_with_cache(
                    tokens, fwd_hooks=fwd_hooks, names_filter=lambda n: n in cache_names,
                )
                pos = -1 if positions == "final" else slice(None)
                slices = [patched_cache[_resid_hook_name(s)][0, pos].float().cpu().numpy() for s in want]
                rows.append(np.stack(slices, axis=0))
        resid = np.stack(rows, axis=0).astype(np.float16)
        return Acts(resid, list(range(len(prompts))), want, positions, self.model_key)


class NnsightBackend:
    """nnsight-backed ``ResidualAccess`` (spec §5.1's fallback; selected via
    registry ``mech_backend: nnsight``). Same semantics as ``TLBackend`` via
    ``model.trace`` -- inside a trace, the residual output of a decoder
    layer is read (``.output[0].save()``) for caching and assigned
    (``layer.output[0][:] = donor_resid``) for patching, all positions.

    NOT exercised by the default suite (guarded ``nnsight`` import); the
    gpu-marked equivalence test (tests/test_mech_gpu.py) confirms it agrees
    with ``TLBackend`` on the debug model within fp16 tolerance. The exact
    module path to the residual stream (``model.model.layers[l]`` for a
    Llama-style model vs other architectures) is what that test pins down;
    written here to the common HF-decoder layout with a docstring flag that
    per-architecture adjustment may be needed.
    """

    def __init__(self, model_key: str, model_name: str, n_layers: int, d_model: int, revision: str = "main"):
        if nnsight is None:
            raise RuntimeError(
                "nnsight is required for NnsightBackend -- install the 'mech' extra "
                "(`uv pip install -e '.[mech]'`) or use FakeBackend."
            )
        from nnsight import LanguageModel

        self.model_key = model_key
        self.n_layers = n_layers
        self.d_model = d_model
        self._model = LanguageModel(model_name, revision=revision, dispatch=True, torch_dtype=torch.bfloat16)
        self._tokenizer = self._model.tokenizer
        self._rating_token_ids = _rating_token_ids(self._tokenizer)

    def n_tokens(self, prompt: str) -> int:
        return len(self._tokenizer.encode(prompt))

    def _layer_module(self, block_idx: int):  # pragma: no cover -- gpu-only
        # Common HF-decoder layout; per-architecture override point.
        return self._model.model.layers[block_idx]

    def _resid_proxy(self, slice_idx: int):  # pragma: no cover -- gpu-only
        # slice 0 = input to block 0 (embedding); slice s>=1 = output of
        # block s-1 -- mirrors _resid_hook_name's convention.
        if slice_idx == 0:
            return self._layer_module(0).input[0][0]
        return self._layer_module(slice_idx - 1).output[0]

    def run_with_cache(
        self,
        prompts: Sequence[str],
        layers: Sequence[int] | None = None,
        positions: Positions = "final",
    ) -> Acts:  # pragma: no cover -- gpu-only
        prompts = list(prompts)
        want = list(range(self.n_layers + 1)) if layers is None else list(layers)
        rows = []
        for prompt in prompts:
            with self._model.trace(prompt):
                saved = {s: self._resid_proxy(s).save() for s in want}
            pos = -1 if positions == "final" else slice(None)
            slices = [saved[s].value[0, pos].float().cpu().numpy() for s in want]
            rows.append(np.stack(slices, axis=0))
        resid = np.stack(rows, axis=0).astype(np.float16)
        return Acts(resid, list(range(len(prompts))), want, positions, self.model_key)

    def logits_0_10(self, prompts: Sequence[str]) -> np.ndarray:  # pragma: no cover -- gpu-only
        out = np.empty((len(prompts), 11), dtype=np.float64)
        for i, prompt in enumerate(prompts):
            with self._model.trace(prompt):
                logits = self._model.lm_head.output[0, -1].save()
            out[i] = _rating_logprobs_from_logits(logits.value, self._rating_token_ids)
        return out

    def run_patched(
        self,
        prompts: Sequence[str],
        donor: "ResidualAccess",
        layers: Sequence[int],
        positions: str = "all",
        scoring: str = "logits_0_10",
    ) -> np.ndarray:  # pragma: no cover -- gpu-only
        prompts = list(prompts)
        _assert_patchable(self, donor, prompts)
        patch_layers = list(layers)
        out = np.empty((len(prompts), 11), dtype=np.float64)
        for i, prompt in enumerate(prompts):
            with donor._model.trace(prompt):
                donor_resid = {s: donor._resid_proxy(s).save() for s in patch_layers}
            with self._model.trace(prompt):
                for s in patch_layers:
                    proxy = self._resid_proxy(s)
                    proxy[:] = donor_resid[s].value.to(proxy.dtype)
                logits = self._model.lm_head.output[0, -1].save()
            out[i] = _rating_logprobs_from_logits(logits.value, self._rating_token_ids)
        return out

    def run_patched_with_cache(
        self,
        prompts: Sequence[str],
        donor: "ResidualAccess",
        layers: Sequence[int],
        positions: Positions = "final",
    ) -> Acts:  # pragma: no cover -- gpu-only
        prompts = list(prompts)
        _assert_patchable(self, donor, prompts)
        patch_layers = list(layers)
        want = list(range(self.n_layers + 1))
        rows = []
        for prompt in prompts:
            with donor._model.trace(prompt):
                donor_resid = {s: donor._resid_proxy(s).save() for s in patch_layers}
            with self._model.trace(prompt):
                for s in patch_layers:
                    proxy = self._resid_proxy(s)
                    proxy[:] = donor_resid[s].value.to(proxy.dtype)
                saved = {s: self._resid_proxy(s).save() for s in want}
            pos = -1 if positions == "final" else slice(None)
            slices = [saved[s].value[0, pos].float().cpu().numpy() for s in want]
            rows.append(np.stack(slices, axis=0))
        resid = np.stack(rows, axis=0).astype(np.float16)
        return Acts(resid, list(range(len(prompts))), want, positions, self.model_key)


# ---------------------------------------------------------------------------
# Shared real-backend logit helpers (torch-touching; only ever called from
# the gpu-only paths above).
# ---------------------------------------------------------------------------


def _rating_token_ids(tokenizer) -> list[int]:  # pragma: no cover -- gpu-only
    """Single-token ids for "0".."10". Where a rating is multi-token for a
    tokenizer (commonly "10"), its id is recorded as -1 and its logprob
    handled as a two-token continuation by the caller -- but for the debug
    models used in the gpu smoke tests all eleven are single tokens; this is
    flagged for the gpu tests to confirm per tokenizer (cf. elicit_vllm.py's
    _log_tokenization_shape)."""
    ids = []
    for i in range(11):
        enc = tokenizer.encode(str(i), add_special_tokens=False)
        ids.append(enc[0] if len(enc) == 1 else -1)
    return ids


def _rating_logprobs_from_logits(logits, rating_token_ids: Sequence[int]) -> np.ndarray:  # pragma: no cover -- gpu-only
    """Log-softmax over the full vocab, then gather the 11 rating tokens and
    renormalise over just those (matching FakeBackend.logits_0_10's
    semantics and parsing.expected_rating_from_logprobs' renormalisation)."""
    log_probs = torch.log_softmax(logits.float(), dim=-1)
    gathered = np.array(
        [log_probs[tid].item() if tid >= 0 else -np.inf for tid in rating_token_ids],
        dtype=np.float64,
    )
    m = np.max(gathered)
    logsumexp = m + np.log(np.sum(np.exp(gathered - m)))
    return gathered - logsumexp


# ---------------------------------------------------------------------------
# Backend construction from the registry (used by cache_acts.py / patch.py).
# ---------------------------------------------------------------------------

BACKENDS = {"transformer_lens": TLBackend, "nnsight": NnsightBackend}
