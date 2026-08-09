"""S2/WO-2 Part B: prompt rendering -> prompts.jsonl (master spec §3.4).

Renders every (variant x question x format) triple into a ``PromptRecord``.
This module invents no new wording of its own -- it only slots the
already-frozen ``scenario`` / ``q_*`` text from a validated
``VignetteRow`` into the frozen Raimondi prompt frame
(``constants.RAIMONDI_PROMPT_TEMPLATE``). ``prompts.jsonl`` is the ONLY
text the H200 will ever see (spec §3.4), so this module's two jobs are:
byte-stable, deterministically-ordered output, and never touching wording.

Formats:
  - "raw": the frozen frame text, used as a plain completion prompt.
  - "chat": the identical text wrapped as a single user message
    (``messages=[{"role": "user", "content": text}]``). Template
    application (e.g. a chat template's special tokens) happens on-device
    at load time in WO-5 -- the *text* frozen here is what's identical
    across raw/chat, only the transport shape differs. This is the
    robustness pass (spec §3.4's "chat (robustness pass)"), not the
    primary format.
  - "cancel" (``schemas.PromptFormat``'s third literal) is reserved for a
    later robustness-testing work order (WO-8) and is never emitted here.

Determinism (WO-2 acceptance criterion): rendering the same vignettes.csv
twice must produce byte-identical prompts.jsonl. Output ordering is fixed
independently of input row order: variant_id (sorted), then question in
intentionality/blame/praise order (``constants.MAIN_QUESTION_COLUMNS``'s
own key order -- not re-declared here), then format in raw/chat order.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Sequence

from knobe import constants
from knobe.schemas import (
    PromptRecord,
    VignetteRow,
    read_csv_validated,
    sha256_for_messages,
    sha256_for_text,
    write_jsonl,
)

# Format emission order (raw then chat) -- an engineering/output-ordering
# detail of this renderer, not a frozen scientific instrument, so it lives
# here rather than in constants.py. "cancel" is reserved (WO-8) and
# deliberately excluded from the default set.
RENDER_FORMATS: tuple[str, ...] = ("raw", "chat")
_KNOWN_FORMATS = frozenset(RENDER_FORMATS)

# Case-insensitive "banned word or any inflection at a word boundary"
# check, identical pattern to assemble.py's validate_family() banned-
# language scan.
_BANNED_WORD_RE = {w: re.compile(rf"\b{re.escape(w)}\w*\b") for w in constants.ALL_BANNED}


def render_prompt_text(scenario: str, question: str) -> str:
    """The one place the fixed Raimondi frame gets applied (spec §3.4)."""
    return constants.RAIMONDI_PROMPT_TEMPLATE.format(scenario=scenario, question=question)


def find_banned_words(text: str) -> list[str]:
    """Returns the sorted set of banned words (their canonical form from
    ``constants.ALL_BANNED``) found anywhere in ``text``, case-insensitive.
    Shared by the property tests; not used in the render path itself since
    banned-language enforcement is assemble.py's job (spec §3.1/§3.2) --
    this is a render-layer defense-in-depth check, not a re-implementation
    of that gate."""
    lowered = text.lower()
    return sorted(w for w, pattern in _BANNED_WORD_RE.items() if pattern.search(lowered))


def render_prompts_for_variant(
    row: VignetteRow, formats: Sequence[str] = RENDER_FORMATS
) -> list[PromptRecord]:
    """All prompt records for one variant, in question order
    (``constants.MAIN_QUESTION_COLUMNS``: intentionality, blame, praise)
    then format order (as given in ``formats``, default raw, chat)."""
    unknown = [f for f in formats if f not in _KNOWN_FORMATS]
    if unknown:
        raise ValueError(f"render.py only emits {sorted(_KNOWN_FORMATS)}, got unknown format(s): {unknown}")

    records: list[PromptRecord] = []
    # Column-backed questions first (legacy order), then the constant-worded
    # extra questions (v1.1 affect_salience) -- same per-question rendering.
    question_sources = [
        (question_type, getattr(row, column))
        for question_type, column in constants.MAIN_QUESTION_COLUMNS.items()
    ] + list(constants.EXTRA_QUESTION_TEXT.items())
    for question_type, question_text in question_sources:
        text = render_prompt_text(row.scenario, question_text)
        for fmt in formats:
            prompt_id = f"{row.variant_id}::{question_type}::{fmt}"
            if fmt == "raw":
                records.append(
                    PromptRecord(
                        prompt_id=prompt_id,
                        variant_id=row.variant_id,
                        question_type=question_type,
                        format="raw",
                        text=text,
                        messages=None,
                        sha256=sha256_for_text(text),
                    )
                )
            else:  # "chat"
                messages = [{"role": "user", "content": text}]
                records.append(
                    PromptRecord(
                        prompt_id=prompt_id,
                        variant_id=row.variant_id,
                        question_type=question_type,
                        format="chat",
                        text=text,
                        messages=messages,
                        sha256=sha256_for_messages(messages),
                    )
                )
    return records


def render_all(rows: list[VignetteRow], formats: Sequence[str] = RENDER_FORMATS) -> list[PromptRecord]:
    """Renders every row's prompts, in variant_id-sorted order regardless
    of the input list's own order -- output ordering must not depend on
    whatever order vignettes.csv happens to be in (WO-2 determinism
    acceptance criterion)."""
    records: list[PromptRecord] = []
    for row in sorted(rows, key=lambda r: r.variant_id):
        records.extend(render_prompts_for_variant(row, formats=formats))
    return records


def write_prompts_jsonl(records: list[PromptRecord], path: str | Path) -> None:
    write_jsonl(records, path)


# ---------------------------------------------------------------------------
# CLI-facing orchestration (called by knobe.cli's "render" subcommand)
# ---------------------------------------------------------------------------


def run(vignettes_path: str | Path, out_path: str | Path, *, formats: Sequence[str] = RENDER_FORMATS) -> int:
    rows = read_csv_validated(vignettes_path, VignetteRow)
    print(f"Loaded {len(rows)} vignette rows from {vignettes_path}")

    records = render_all(rows, formats=formats)
    write_prompts_jsonl(records, out_path)
    print(f"Wrote {len(records)} prompt records to {out_path}")
    return 0
