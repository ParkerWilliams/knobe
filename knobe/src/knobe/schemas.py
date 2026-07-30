"""Pydantic v2 models for every artifact in master spec §3, plus the shared
CSV/JSONL read/write helpers every stage uses to validate I/O at every
pipeline boundary (spec §3, common-context.md constraint 3).

Enum-like fields reuse the vocabularies defined in ``constants.py`` (never
redefine a competing copy of a taxonomy value here).

Design note on ``ResultRecord.parsed_rating`` (§3.6 vs §4.4): master spec
§3.6 literally types this field ``int|null``, but §4.4's logit-fallback
scoring computes a renormalized *expected value* over tokens "0".."10",
which is generally not an integer (see ``parsing.expected_rating_from_logprobs``).
Rounding that EV to the nearest int would silently discard the information
the fallback path exists to capture. This is flagged as an internal
inconsistency between two sections of the same spec document (not a
spec-vs-design-doc conflict) in the T0 report; the field is typed
``int | float | None`` here so both parse methods can populate it honestly.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import warnings
from pathlib import Path
from typing import IO, Literal, Sequence

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from knobe import constants

# ProbeRecord.construct (spec §3.9's own taxonomy-field name, and the
# directory-naming convention `<construct>__layer<l>.json`) shadows the
# deprecated BaseModel.construct() classmethod, which pydantic warns about
# on every import. Nothing in this codebase calls that deprecated
# classmethod, so the shadow is benign; narrowly silenced here (by exact
# message, not category-wide) so every downstream importer of this module
# doesn't see import-time warning noise for a field name we're keeping
# deliberately.
warnings.filterwarnings(
    "ignore",
    message=r'Field name "construct" in "ProbeRecord" shadows an attribute in parent "KnobeModel"',
    category=UserWarning,
)

# ---------------------------------------------------------------------------
# Shared vocab / helpers
# ---------------------------------------------------------------------------

Valence = Literal["MB", "MG", "NMB", "NMG", "NEU"]
Typicality = Literal["common", "uncommon"]
Evocativeness = Literal["low", "high"]
Sign = Literal["bad", "good", "na"]
QuestionType = Literal["intentionality", "blame", "praise"]
# "cancel" is reserved (unused by T0/WO-2) for WO-8's robustness-testing
# stub per the task-0 brief -- not yet a real render format.
PromptFormat = Literal["raw", "chat", "cancel"]
ParseMethod = Literal["regex", "logit_fallback"]
ScoringMethod = Literal["logits_0_10", "sampling"]
ProbeConstruct = Literal[
    "valence_moral",  # MB/MG vs NMB/NMG
    "sign",  # bad vs good
    "blame_rating",
    "severity",
    "vividness_evocativeness",
    "typicality_condition",
    "typicality_perception",
    "intentionality_rating",
]


def _blank_to_none(v):
    if isinstance(v, str) and v.strip() == "":
        return None
    return v


def _coerce_bool(v):
    if isinstance(v, bool):
        return v
    if v is None:
        return False
    if isinstance(v, str):
        s = v.strip().lower()
        if s in ("true", "1", "yes"):
            return True
        if s in ("false", "0", "no", ""):
            return False
    return v


def _coerce_optional_int_0_10(v):
    v = _blank_to_none(v)
    if v is None:
        return None
    return int(v)


def _check_nonmoral_subdomain(valence: str, nonmoral_subdomain: str) -> None:
    """Shared rule for FamilyRow and VignetteRow/CuratedRow (spec §3.1/§3.2):
    required iff valence is NMB/NMG (and must be one of the four canonical
    subdomains), must be empty for every other valence."""
    if valence in constants.NONMORAL_VALENCES:
        if not nonmoral_subdomain:
            raise ValueError(f"valence {valence} requires a nonmoral_subdomain")
        if nonmoral_subdomain not in constants.VALID_SUBDOMAINS:
            raise ValueError(
                f"nonmoral_subdomain {nonmoral_subdomain!r} not in "
                f"{sorted(constants.VALID_SUBDOMAINS)}"
            )
    else:
        if nonmoral_subdomain:
            raise ValueError(
                f"nonmoral_subdomain must be empty for valence {valence}, "
                f"got {nonmoral_subdomain!r}"
            )


class KnobeModel(BaseModel):
    """Base for all artifact models: unknown fields are a hard error, since
    schemas.py is the single enforcement point for every artifact's shape
    (common-context.md constraint 3)."""

    model_config = ConfigDict(extra="forbid")


class KnobeCSVModel(KnobeModel):
    """Base for row-oriented, CSV-backed artifacts. Subclasses may override
    ``csv_fieldnames()`` to pin an exact, legacy-compatible column order;
    the default is declaration order."""

    @classmethod
    def csv_fieldnames(cls) -> list[str]:
        return list(cls.model_fields.keys())


# ---------------------------------------------------------------------------
# §3.1 master_matrix.csv -- FamilyRow
# ---------------------------------------------------------------------------

_FAMILY_CSV_FIELDNAMES = [
    "family_id", "domain", "valence", "nonmoral_subdomain", "agent", "goal",
    "common_action", "uncommon_action", "affected_entity",
    "low_evocative_outcome", "high_evocative_outcome", "outcome_verb",
]


class FamilyRow(KnobeCSVModel):
    """One row of master_matrix.csv (spec §3.1): a hand/LLM-authored family,
    pre-assembly. The 12 canonical columns plus optional WO-1 provenance
    fields that are tolerated-absent on legacy CSVs (default to None/False
    when the column simply isn't in the input header)."""

    family_id: str
    domain: str
    valence: Valence
    nonmoral_subdomain: str = ""
    agent: str
    goal: str
    common_action: str
    uncommon_action: str
    affected_entity: str
    low_evocative_outcome: str
    high_evocative_outcome: str
    outcome_verb: str

    # WO-1 provenance, optional / tolerated-absent on legacy CSVs.
    generator_model: str | None = None
    ingest_date: str | None = None
    human_approved: bool = False

    @field_validator("generator_model", "ingest_date", mode="before")
    @classmethod
    def _optional_text_blank_to_none(cls, v):
        return _blank_to_none(v)

    @field_validator("human_approved", mode="before")
    @classmethod
    def _human_approved_coerce(cls, v):
        return _coerce_bool(v)

    @field_validator("family_id")
    @classmethod
    def _family_id_format(cls, v: str) -> str:
        if not re.fullmatch(constants.FAMILY_ID_RE, v):
            raise ValueError(f"family_id {v!r} does not match {constants.FAMILY_ID_RE!r}")
        return v

    @model_validator(mode="after")
    def _check_required_and_subdomain(self) -> "FamilyRow":
        for field in constants.REQUIRED_FIELDS:
            if field == "valence":
                continue  # already enum-validated
            if not getattr(self, field):
                raise ValueError(f"required field {field!r} is empty")
        _check_nonmoral_subdomain(self.valence, self.nonmoral_subdomain)
        return self

    @classmethod
    def csv_fieldnames(cls) -> list[str]:
        return _FAMILY_CSV_FIELDNAMES


# ---------------------------------------------------------------------------
# §3.2 vignettes.csv -- VignetteRow
# ---------------------------------------------------------------------------


class VignetteRow(KnobeCSVModel):
    """One row of vignettes.csv (spec §3.2): a fully-assembled variant. The
    same input must always produce a byte-identical row (assemble.py, WO-2)."""

    variant_id: str
    family_id: str
    domain: str
    valence: Valence
    nonmoral_subdomain: str = ""
    sign: Sign
    typicality: Typicality
    evocativeness: Evocativeness
    scenario: str
    q_intentionality: str
    q_blame: str
    q_praise: str

    @field_validator("family_id")
    @classmethod
    def _family_id_format(cls, v: str) -> str:
        if not re.fullmatch(constants.FAMILY_ID_RE, v):
            raise ValueError(f"family_id {v!r} does not match {constants.FAMILY_ID_RE!r}")
        return v

    @model_validator(mode="after")
    def _check_consistency(self) -> "VignetteRow":
        _check_nonmoral_subdomain(self.valence, self.nonmoral_subdomain)

        expected_letter = constants.VARIANT_LETTER[(self.typicality, self.evocativeness)]
        expected_variant_id = f"{self.family_id}-{expected_letter}"
        if self.variant_id != expected_variant_id:
            raise ValueError(
                f"variant_id {self.variant_id!r} disagrees with "
                f"(typicality={self.typicality!r}, evocativeness={self.evocativeness!r}); "
                f"expected {expected_variant_id!r}"
            )

        expected_sign = constants.SIGN_BY_VALENCE[self.valence]
        if self.sign != expected_sign:
            raise ValueError(
                f"sign {self.sign!r} disagrees with valence {self.valence!r}; "
                f"expected {expected_sign!r}"
            )
        return self

    @classmethod
    def csv_fieldnames(cls) -> list[str]:
        return list(constants.OUTPUT_FIELDNAMES)


# ---------------------------------------------------------------------------
# §3.3 curated.csv -- CuratedRow
# ---------------------------------------------------------------------------

_CURATION_RATING_FIELDS = list(constants.CURATION_QUESTIONS.keys())

_CURATED_CSV_FIELDNAMES = (
    list(constants.OUTPUT_FIELDNAMES)
    + [f for field in _CURATION_RATING_FIELDS for f in (field, f"{field}_raw")]
    + ["individual_flags", "pair_flag", "reviewer_model", "curation_date", "accepted"]
)


class CuratedRow(VignetteRow):
    """VignetteRow + the four curation-stage ratings (spec §3.3). Only rows
    with ``accepted == True`` enter a release."""

    moral_relevance: int | None = None
    moral_relevance_raw: str = ""
    severity: int | None = None
    severity_raw: str = ""
    vividness: int | None = None
    vividness_raw: str = ""
    typicality_perception: int | None = None
    typicality_perception_raw: str = ""

    individual_flags: str = ""
    pair_flag: str = ""
    reviewer_model: str
    curation_date: str
    accepted: bool = False

    @field_validator(
        "moral_relevance", "severity", "vividness", "typicality_perception", mode="before"
    )
    @classmethod
    def _rating_coerce(cls, v):
        return _coerce_optional_int_0_10(v)

    @field_validator("moral_relevance", "severity", "vividness", "typicality_perception")
    @classmethod
    def _rating_range(cls, v):
        if v is not None and not (0 <= v <= 10):
            raise ValueError(f"rating {v} out of range 0-10")
        return v

    @field_validator("accepted", mode="before")
    @classmethod
    def _accepted_coerce(cls, v):
        return _coerce_bool(v)

    @classmethod
    def csv_fieldnames(cls) -> list[str]:
        return list(_CURATED_CSV_FIELDNAMES)


# ---------------------------------------------------------------------------
# curate.py (WO-3) checkpoint + telemetry artifacts. Not enumerated by
# number in master spec §3 (that section stops at curated.csv, §3.3 --
# these two files are S3's internal working state, produced and consumed
# only by curate.py itself), but common-context.md constraint 3 ("every
# script... validates I/O against schemas.py") applies to every artifact a
# script reads or writes, not only the numbered ones -- so they get models
# here rather than being ad-hoc dicts written straight to disk.
# ---------------------------------------------------------------------------


class CurationRawResult(KnobeModel):
    """One line of ``curated_raw.jsonl`` -- the checkpoint unit for
    curate.py's resume mechanism (WO-3 §1): one independent completion for
    one (variant_id, curation question field) job. ``ok=False`` means the
    response didn't parse (parsing.parse_rating's never-coerce invariant);
    ``value`` is then None and ``raw`` holds the verbatim response for
    manual inspection -- never silently defaulted to a number."""

    variant_id: str
    field: str
    value: int | None = None
    ok: bool
    raw: str
    reviewer_model: str
    timestamp: float

    @field_validator("field")
    @classmethod
    def _field_known(cls, v: str) -> str:
        if v not in constants.CURATION_QUESTIONS:
            raise ValueError(
                f"field {v!r} is not one of constants.CURATION_QUESTIONS "
                f"{sorted(constants.CURATION_QUESTIONS)}"
            )
        return v


class CurationRunLogEntry(KnobeModel):
    """One line of ``curation_runlog.jsonl`` -- per-run cost/telemetry
    (WO-3 §7): appended once per ``knobe curate run`` invocation."""

    timestamp: float
    reviewer_model: str
    mock: bool
    n_jobs_total: int
    n_jobs_run: int
    n_jobs_skipped: int
    n_retries: int
    n_errors: int
    input_tokens: int | None = None
    output_tokens: int | None = None
    wall_time_sec: float


# ---------------------------------------------------------------------------
# §3.4 prompts.jsonl -- PromptRecord
# ---------------------------------------------------------------------------


class PromptRecord(KnobeModel):
    """One record per (variant x question x format) -- the ONLY text the
    H200 ever sends (spec §3.4).

    ``sha256`` is the sha256 hex digest of ``text`` (UTF-8) for "raw"/"cancel"
    formats. For "chat" format it is instead the sha256 of the *canonical*
    JSON serialization of ``messages`` (``json.dumps(messages, sort_keys=True,
    separators=(",", ":"))``) -- ``messages`` is the structured payload
    actually sent to a chat endpoint, so it, not ``text``, is what must be
    hashed for chat-format integrity checking. See ``sha256_for_text`` /
    ``sha256_for_messages`` below.
    """

    prompt_id: str
    variant_id: str
    question_type: QuestionType
    format: PromptFormat
    text: str
    messages: list[dict] | None = None
    sha256: str

    @field_validator("sha256")
    @classmethod
    def _sha256_shape(cls, v: str) -> str:
        if not re.fullmatch(r"[0-9a-f]{64}", v):
            raise ValueError(f"sha256 {v!r} is not a 64-char lowercase hex digest")
        return v

    @model_validator(mode="after")
    def _check_consistency(self) -> "PromptRecord":
        expected_prompt_id = f"{self.variant_id}::{self.question_type}::{self.format}"
        if self.prompt_id != expected_prompt_id:
            raise ValueError(
                f"prompt_id {self.prompt_id!r} != expected {expected_prompt_id!r}"
            )
        if self.format == "chat":
            if self.messages is None:
                raise ValueError('messages must be populated when format=="chat"')
        else:
            if self.messages is not None:
                raise ValueError(f'messages must be None when format={self.format!r}')
        return self


def sha256_for_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_for_messages(messages: list[dict]) -> str:
    canonical = json.dumps(messages, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# §3.5 jobs.jsonl -- JobRecord
# ---------------------------------------------------------------------------


class JobRecord(KnobeModel):
    """One completion to be sampled (spec §3.5). ``temperature``/``seed`` are
    always derived deterministically (sha256 of release_version, prompt_id,
    model_key, sample_idx) by jobs.py -- never generated at call time."""

    job_id: str
    prompt_id: str
    model_key: str
    sample_idx: int
    temperature: float
    seed: int

    @field_validator("sample_idx")
    @classmethod
    def _sample_idx_nonneg(cls, v: int) -> int:
        if v < 0:
            raise ValueError("sample_idx must be >= 0")
        return v


# ---------------------------------------------------------------------------
# §3.6 results.jsonl -- ResultRecord
# ---------------------------------------------------------------------------


class ResultRecord(KnobeModel):
    """One completed job (spec §3.6). Deliberately carries NO denormalized
    item fields (family_id/valence/typicality/... are joined in at analysis
    time via variant_id, per spec §3.6's file-hygiene rule)."""

    job_id: str
    prompt_id: str
    model_key: str
    sample_idx: int
    temperature: float
    seed: int

    raw_response: str
    parsed_rating: int | float | None = None
    parse_ok: bool
    parse_method: ParseMethod
    # -inf/NaN entries are stored as the finite JSON-safe sentinel -1e300 (an
    # impossible rating token scores -inf; JSON has no -inf) -- see
    # elicit_vllm._sanitize_logprobs_for_storage / _LOGPROB_NEG_INF_SENTINEL.
    logprobs_0_10: list[float] | None = None
    model_revision: str
    runner_version: str
    timestamp: float

    @field_validator("logprobs_0_10")
    @classmethod
    def _logprobs_length(cls, v):
        if v is not None and len(v) != 11:
            raise ValueError(f"logprobs_0_10 must have exactly 11 entries, got {len(v)}")
        return v


# ---------------------------------------------------------------------------
# power.py (WO-4) artifacts. Not one of spec §3's numbered artifacts (S4's
# own internal working state -- pilot variance decomposition + the
# simulation-grid checkpoint), but common-context.md constraint 3 ("every
# script... validates I/O against schemas.py") still applies.
# ---------------------------------------------------------------------------


class VarianceComponents(KnobeModel):
    """Output of ``power.estimate_variance_components`` (WO-4 §1): a
    per-subject-model, per-question variance decomposition from the pilot
    ``results.jsonl`` -- random-intercept-for-family variance plus
    response-level residual variance, and the resulting ICC. ``fallback_used``
    records whether the primary ``statsmodels`` mixedlm fit failed to
    converge and an OLS-with-cluster-robust-SEs fit was used instead (never
    silently dropped -- see ``power.py`` module docstring)."""

    model_key: str
    question: QuestionType
    var_family: float
    var_resid: float
    icc: float
    n_families: int
    n_items: int
    n_responses: int
    convergence_ok: bool
    fallback_used: bool = False

    @field_validator("var_family", "var_resid")
    @classmethod
    def _nonneg_variance(cls, v: float) -> float:
        if v < 0:
            raise ValueError(f"variance component must be >= 0, got {v}")
        return v


class PowerGridRow(KnobeModel):
    """One line of ``power_grid.jsonl`` (WO-4 §3): the simulation-based
    power estimate for one (contrast, item_count, n, sim_batch) grid point.
    ``n`` is the response-level N per item (per family or per family x
    condition-cell, contrast-dependent -- see power_sim.py). Resume is a
    skip on the (contrast, item_count, n, sim_batch) key already present in
    the file; ``--shard i/n`` shards over the list of such keys."""

    contrast: str
    item_count: int
    n: int
    sim_batch: int
    n_sims: int
    n_significant: int
    n_converged: int
    n_convergence_failures: int
    n_fallback_used: int
    power: float
    effect_size: float
    frac_clipped: float
    seed: int
    timestamp: float


# ---------------------------------------------------------------------------
# elicit_vllm.py (WO-5) checkpoint/telemetry artifact. Like
# CurationRawResult/CurationRunLogEntry above, this isn't one of spec §3's
# numbered artifacts (it's S5's own internal run telemetry, not a pipeline
# data contract), but common-context.md constraint 3 ("every script...
# validates I/O against schemas.py") still applies to every artifact a
# script writes.
# ---------------------------------------------------------------------------


class ElicitRunLogEntry(KnobeModel):
    """One line of ``elicit_runlog.jsonl`` -- per-invocation throughput/
    telemetry for ``knobe elicit`` (WO-5 §7), appended once per run."""

    timestamp: float
    engine: str
    release: str
    n_jobs_total: int
    n_jobs_done_before: int
    n_jobs_run: int
    wall_time_sec: float
    parse_rate_by_model_key: dict[str, float]


# ---------------------------------------------------------------------------
# §3.8 patch/<family>/layer_<l>.jsonl -- PatchRecord
# ---------------------------------------------------------------------------


class PatchInfo(KnobeModel):
    donor: str
    layers: list[int]
    positions: str = "all"


class PatchRecord(ResultRecord):
    """ResultRecord + the patch configuration that produced it (spec §3.8)."""

    patch: PatchInfo
    scoring: ScoringMethod


# ---------------------------------------------------------------------------
# §3.9 probes/<model_key>/<construct>__layer<l>.json -- ProbeRecord
# ---------------------------------------------------------------------------


class FamilySplit(KnobeModel):
    train: list[str]
    test: list[str]


class ProbeRecord(KnobeModel):
    model_key: str
    construct: ProbeConstruct
    layer: int
    weights_ref: str
    split: FamilySplit
    # Cross-validated score of the RAW probe (accuracy for classification, R²
    # for ridge), GroupKFold over scaffold groups on the train split.
    cv_score: float
    # Companion CV score of the RESIDUALIZED probe (ridge R² on the
    # confound-partialled target) -- the quantity RQ2 dissociation claims rest
    # on. Additive; defaults to cv_score's sibling being absent in pre-WO-7
    # records. NaN-safe stored as 0.0 when the residualized probe is degenerate.
    resid_cv_score: float = 0.0
    residualization_recipe: str
    # Additive WO-7 field: distinguishes a probe trained on a discrete design
    # *condition* label (classification) from one trained on a continuous
    # *rating* (ridge). Needed because §3.9's vividness_evocativeness construct
    # carries BOTH a low/high-evocativeness condition probe and a
    # curated-vividness rating probe under the one construct name; every other
    # construct has a single natural kind. Defaults to "condition" so pre-WO-7
    # ProbeRecords still validate. ``residualized`` flags the residualized
    # (confound-partialled) probe variant (WO-7 §3): RQ2 dissociation claims
    # use residualized probes, raw curves are descriptive.
    target_kind: Literal["condition", "rating"] = "condition"
    residualized: bool = False


# ---------------------------------------------------------------------------
# §3.10 data/release/vX.Y/manifest.json -- ReleaseManifest
# ---------------------------------------------------------------------------


class FileManifestEntry(KnobeModel):
    sha256: str
    rows: int


class LabeledCount(KnobeModel):
    """One (families, variants) tally pair -- the value type of
    ``ReleaseCounts.by_valence``/``by_domain`` (see below)."""

    families: int
    variants: int


class ReleaseCounts(KnobeModel):
    """Spec §3.10's ``counts`` object. ``families``/``variants`` are the
    release-wide totals (unchanged). ``by_valence``/``by_domain`` report
    BOTH levels, labeled, per key -- e.g.
    ``{"MB": {"families": 12, "variants": 48}, ...}`` -- per
    docs/DECISIONS_FOR_HUMANS.md item (d2) (researcher directive,
    2026-07-28): spec §3.10's own example doesn't disambiguate family- vs.
    variant-level grouping for these two fields, and a flat
    variant-only count (the pre-d2 shape: ``dict[str, int]``) silently
    discarded the family-level breakdown. No release directory exists yet
    under this shape, so there is no migration to an already-written
    manifest.json to worry about."""

    families: int
    variants: int
    by_valence: dict[str, LabeledCount]
    by_domain: dict[str, LabeledCount]


class ReleaseManifest(KnobeModel):
    release: str
    created: str
    git_commit: str
    files: dict[str, FileManifestEntry]
    counts: ReleaseCounts
    gates_passed: list[str]
    changelog: str


# ---------------------------------------------------------------------------
# analysis/ (WO-8) artifacts. Not one of spec §3's numbered artifacts (S8's
# own analysis working state -- the exclusions ledger + the Holm-corrected
# contrast table), but common-context.md constraint 3 ("every script...
# validates I/O against schemas.py") applies to every artifact a script
# writes, not only the numbered ones.
# ---------------------------------------------------------------------------


class ExclusionEntry(KnobeModel):
    """One reason-category of the analysis exclusions ledger (WO-8 §1): how
    many response rows were dropped for this reason, with a capped sample of
    the offending ids for inspection. Exclusions are NEVER silent -- the
    whole ledger is written to ``exclusions.json`` AND printed."""

    reason: str
    count: int
    examples: list[str] = []


class ExclusionsLedger(KnobeModel):
    """The analysis exclusions ledger (WO-8 §1), written to
    ``exclusions.json`` and printed. ``n_result_rows`` is the raw
    results.jsonl row count read; ``n_included`` is what survived into the
    analysis DataFrame; ``n_excluded`` = sum of every entry's count.
    ``n_job_rows``/``n_missing_results`` record the row-count validation
    against the jobs.jsonl manifest (spec §3.5): jobs with no completed
    result are themselves reported as an ``incomplete`` exclusion category,
    never silently ignored."""

    release: str
    n_result_rows: int
    n_included: int
    n_excluded: int
    n_job_rows: int | None = None
    n_missing_results: int = 0
    entries: list[ExclusionEntry] = []


class ContrastResultRecord(KnobeModel):
    """One row of the Holm-corrected contrast table (WO-8 §2/§5): the fitted
    estimate for one declared contrast on one subject model_family. ``method``
    records which estimator produced the point estimate/p-value (LMM primary,
    or the OLS-cluster-robust fallback when the mixed model didn't converge --
    never silently dropped). ``p_holm`` is the Holm-corrected p within the
    (model_family, rq) family. ``ci_low``/``ci_high`` are the seeded
    cluster-bootstrap percentile interval."""

    contrast: str
    rq: str
    model_family: str
    tuning_scope: str
    term: str
    estimate: float
    se: float | None = None
    p_value: float
    p_holm: float
    ci_low: float | None = None
    ci_high: float | None = None
    # Provenance of ci_low/ci_high: "cluster_bootstrap_ols" (seeded family-cluster
    # bootstrap, OLS refit per resample -- a robustness companion to the LMM Wald
    # p-value, NOT a second estimator of record) or "none" (n_boot==0).
    ci_method: str = "none"
    direction_expected: str
    direction_ok: bool
    n_obs: int
    n_groups: int
    method: str
    converged: bool
    fallback_used: bool


# ---------------------------------------------------------------------------
# CSV / JSONL helpers -- used by every stage to validate I/O at every
# pipeline boundary (common-context.md constraint 3).
# ---------------------------------------------------------------------------


def _csv_serialize_value(v) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return "True" if v else "False"
    return str(v)


def read_csv_validated(path: str | Path, model: type[KnobeModel]) -> list[KnobeModel]:
    """Reads a CSV file, validating every row against ``model``. Raises with
    the offending row number (1-indexed, header = row 1) on the first
    validation failure."""
    path = Path(path)
    rows: list[KnobeModel] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, raw in enumerate(reader, start=2):
            try:
                rows.append(model(**raw))
            except Exception as exc:  # pydantic.ValidationError or TypeError
                raise ValueError(f"{path}: row {i} failed validation against {model.__name__}: {exc}") from exc
    return rows


def write_csv_validated(
    rows: Sequence[KnobeModel], path: str | Path, model: type[KnobeModel]
) -> None:
    """Writes ``rows`` (already-validated model instances) to ``path`` as
    CSV, using ``model.csv_fieldnames()`` for column order."""
    path = Path(path)
    fieldnames = model.csv_fieldnames() if hasattr(model, "csv_fieldnames") else list(model.model_fields.keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            dumped = row.model_dump()
            writer.writerow({k: _csv_serialize_value(dumped.get(k)) for k in fieldnames})


def read_jsonl(path: str | Path, model: type[KnobeModel]) -> list[KnobeModel]:
    """Reads a JSONL file, validating every line against ``model``. Blank
    lines are skipped (tolerates a trailing newline)."""
    path = Path(path)
    rows: list[KnobeModel] = []
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(model.model_validate_json(line))
            except Exception as exc:
                raise ValueError(f"{path}: line {i} failed validation against {model.__name__}: {exc}") from exc
    return rows


def append_jsonl(row: KnobeModel, fh: IO[str]) -> None:
    """Appends one validated record as a single JSON line to an already-open
    file handle (append mode), flushing immediately so a crash mid-run loses
    at most the in-flight record -- the checkpoint/resume pattern every
    long-running script in this package uses (common-context.md constraint 3)."""
    fh.write(row.model_dump_json())
    fh.write("\n")
    fh.flush()


def write_jsonl(rows: Sequence[KnobeModel], path: str | Path) -> None:
    """Writes ``rows`` to ``path`` as JSONL, one record per line, in list
    order (write/truncate mode -- this is a batch write of an
    already-fully-computed sequence, e.g. render.py's prompts.jsonl or
    jobs.py's jobs.jsonl; both are precompute artifacts written whole, not
    incrementally, so this can't diverge from ``append_jsonl``'s one-line
    format). For incremental/checkpointed writes against an already-open,
    append-mode handle, use ``append_jsonl`` directly instead."""
    path = Path(path)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            append_jsonl(row, f)
