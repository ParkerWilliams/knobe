"""Rating parsers shared by curation, main-experiment elicitation, and any
patched re-elicitation (master spec §4.4).

Two parsing strategies:
  - ``parse_rating``: regex first-integer-0..10, ported byte-identically
    from the legacy curate_vignettes.py / elicit_main_experiment.py
    ``parse_rating`` functions.
  - ``expected_rating_from_logprobs`` / ``parse_with_fallback``: the
    logit-fallback scoring path used only for checkpoints whose regex
    parse rate falls below the spec's 95% threshold in G0/G1 -- a
    renormalized expected value over the token logprobs for "0".."10" at
    the answer position.

An unparseable response NEVER silently coerces to a number: ``parse_rating``
returns ``(None, False, raw)`` and ``parse_with_fallback`` only falls back to
a numeric expected value when logit fallback is both available (logprobs
supplied) and configured for that checkpoint (``threshold_ok is False``).
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Literal, Sequence

# Matches a bare "0".."10" at a word boundary -- identical pattern to the
# legacy curate_vignettes.py / elicit_main_experiment.py parse_rating().
_RATING_RE = re.compile(r"\b(10|[0-9])\b")


def parse_rating(raw_text: str) -> tuple[int | None, bool, str]:
    """Extracts the first integer 0-10 from a model's response.

    Returns ``(value, ok, raw)``. ``ok=False`` means the response didn't
    parse cleanly -- never silently coerce a bad parse to a default number.
    """
    match = _RATING_RE.search(raw_text)
    if match:
        return int(match.group(1)), True, raw_text
    return None, False, raw_text


def expected_rating_from_logprobs(logprobs_0_10: Sequence[float]) -> float:
    """Renormalized expected value over tokens "0".."10" at the answer
    position (spec §4.4's logit-fallback scoring).

    ``logprobs_0_10`` must have exactly 11 entries, index *i* being the log
    probability of token "i" (``-inf`` / very negative for effectively-zero
    mass is fine). Probabilities are renormalized over just these 11 tokens
    (they need not sum to 1 over the full vocabulary) before taking the
    expectation E[rating] = sum_i i * p_i.
    """
    if len(logprobs_0_10) != 11:
        raise ValueError(
            f"expected_rating_from_logprobs requires exactly 11 logprobs "
            f"(one per token '0'..'10'), got {len(logprobs_0_10)}"
        )
    max_lp = max(logprobs_0_10)
    if max_lp == float("-inf"):
        raise ValueError("all logprobs are -inf; cannot compute an expected value")
    # Softmax-style renormalization, shifted by the max for numerical
    # stability (log-sum-exp trick).
    weights = [math.exp(lp - max_lp) for lp in logprobs_0_10]
    total = sum(weights)
    probs = [w / total for w in weights]
    return sum(i * p for i, p in enumerate(probs))


ParseMethod = Literal["regex", "logit_fallback"]


@dataclass(frozen=True)
class ParsedRating:
    """Result of parse_with_fallback: what to store in ResultRecord's
    parsed_rating / parse_ok / parse_method fields."""

    parsed_rating: float | int | None
    parse_ok: bool
    parse_method: ParseMethod
    raw: str


def parse_with_fallback(
    raw: str,
    logprobs_0_10: Sequence[float] | None,
    threshold_ok: bool,
) -> ParsedRating:
    """Implements spec §4.4: regex first; logit fallback only when the
    checkpoint is configured for it (``threshold_ok is False``, i.e. this
    checkpoint's measured regex parse rate fell below the 95% gate) AND
    logprobs are actually available for this response.

    ``threshold_ok=True`` means the checkpoint's regex parse rate is
    healthy -- fallback must NOT kick in even if logprobs happen to be
    present and this particular response failed to parse; that failure is
    recorded as an honest miss (``parse_ok=False``), not papered over.
    """
    value, ok, raw_out = parse_rating(raw)
    if ok:
        return ParsedRating(parsed_rating=value, parse_ok=True, parse_method="regex", raw=raw_out)

    if not threshold_ok and logprobs_0_10 is not None:
        ev = expected_rating_from_logprobs(logprobs_0_10)
        return ParsedRating(parsed_rating=ev, parse_ok=True, parse_method="logit_fallback", raw=raw_out)

    return ParsedRating(parsed_rating=None, parse_ok=False, parse_method="regex", raw=raw_out)
