"""Loader + validation for configs/models.yaml, the model registry (master
spec §2).

``model_key`` convention: ``"{family}-pretrained"`` for the base checkpoint,
``"{family}-instruct"`` for the finetuned one (e.g. ``"llama-3.1-8b-instruct"``,
matching spec §3.5's example job record) -- use ``model_key_for()`` rather
than hand-formatting this string.
"""
from __future__ import annotations

import warnings
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict

Role = Literal["core", "extension", "extension-config-only", "debug"]
TuningStatus = Literal["pretrained", "finetuned"]
MechBackend = Literal["transformer_lens", "nnsight"]

_MODEL_KEY_SUFFIX = {"pretrained": "pretrained", "finetuned": "instruct"}


class RegistryConfigError(ValueError):
    """Raised for registry configuration errors that must hard-fail config
    load: a `role: core` family missing a checkpoint, or a reviewer model
    (Claude) appearing in the subject registry."""


class Family(BaseModel):
    """One model family: a pretrained/finetuned checkpoint pair sharing an
    architecture. ``pretrained``/``finetuned`` are optional at the schema
    level (so ``check_family_pairs`` has something meaningful to flag when
    one is genuinely absent) -- but every family actually shipped in
    configs/models.yaml lists both."""

    model_config = ConfigDict(extra="forbid")

    pretrained: str | None = None
    finetuned: str | None = None
    tl_name: str | None = None
    d_model: int
    n_layers: int
    role: Role
    sae: str | None = None
    # WO-5 requirement 1: pinned HF revision (branch/tag/commit) to load
    # both checkpoints at. Optional -- defaults to "main" so every
    # pre-existing configs/models.yaml entry (and every test fixture built
    # before WO-5) keeps validating unchanged. elicit_vllm.py records the
    # ACTUAL resolved commit hash per row in ResultRecord.model_revision,
    # not this string verbatim -- this field only pins which ref to load.
    revision: str = "main"
    # WO-6 requirement (task-7-brief.md): which mechanistic-interp backend
    # mech/backend.py uses for this family. Default "transformer_lens" (the
    # primary impl, spec §5.1); set "nnsight" per-family for models TL lacks
    # a HookedTransformer config for, or where nnsight's memory behaviour is
    # needed. Additive/optional -- like `revision` above, every pre-WO-6
    # configs/models.yaml entry and test fixture keeps validating unchanged.
    mech_backend: MechBackend = "transformer_lens"


def model_key_for(family: str, tuning_status: TuningStatus) -> str:
    """The `"{family}-{pretrained|instruct}"` model_key convention (spec
    §3.5's `"llama-3.1-8b-instruct"` example)."""
    return f"{family}-{_MODEL_KEY_SUFFIX[tuning_status]}"


def _iter_model_ids(family: Family):
    for model_id in (family.pretrained, family.finetuned, family.tl_name):
        if model_id:
            yield model_id


def check_reviewer_model_forbidden(registry: dict[str, Family]) -> None:
    """REVIEWER_MODEL_FORBIDDEN (DR §13 / common-context.md constraint 8):
    the curation reviewer model (Claude via API) must never appear as a
    subject in the registry. Hard error, any match, case-insensitive."""
    for family_name, family in registry.items():
        for model_id in _iter_model_ids(family):
            if "claude" in model_id.lower():
                raise RegistryConfigError(
                    f"configs/models.yaml family {family_name!r} references "
                    f"a Claude model id ({model_id!r}) -- the curation "
                    f"reviewer model must never appear as a subject "
                    f"(DR §13, common-context.md constraint 8)."
                )


def check_family_pairs(registry: dict[str, Family]) -> None:
    """A family missing either checkpoint can't answer RQ1's pretrained-vs-
    finetuned comparison. Hard error for `role: core` (promoted from the
    legacy script's warning-only behavior); warning for every other role,
    preserving that legacy behavior."""
    for family_name, family in registry.items():
        missing = [
            status for status, value in
            (("pretrained", family.pretrained), ("finetuned", family.finetuned))
            if not value
        ]
        if not missing:
            continue
        message = (
            f"family {family_name!r} (role={family.role}) is missing its "
            f"{missing} checkpoint(s) -- RQ1's pretrained-vs-finetuned "
            f"comparison cannot be answered for this family."
        )
        if family.role == "core":
            raise RegistryConfigError(message)
        warnings.warn(message, UserWarning, stacklevel=2)


def load_registry(path: str | Path) -> dict[str, Family]:
    """Loads and validates configs/models.yaml. Raises ``RegistryConfigError``
    if any `role: core` family is missing a checkpoint, or if a Claude model
    id appears anywhere in the file."""
    path = Path(path)
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    families_data = (data or {}).get("families", {})
    registry = {name: Family(**fields) for name, fields in families_data.items()}

    check_reviewer_model_forbidden(registry)
    check_family_pairs(registry)

    return registry
