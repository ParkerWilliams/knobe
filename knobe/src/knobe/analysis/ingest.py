"""WO-8 §1: stream-join ``results.jsonl`` (possibly sharded across several
files) with the release ``vignettes.csv`` (variant metadata) and
``curated.csv`` (curation ratings) into ONE tidy, response-level analysis
DataFrame -- plus an exclusions ledger that is NEVER silent.

The join key is ``variant_id``, recovered from ``prompt_id`` by splitting on
``"::"`` (master spec §3.4/§3.6's convention: ``prompt_id ==
"{variant_id}::{question_type}::{format}"``). Denormalized item fields are
joined in HERE, at analysis time, not stored per result row (spec §3.6's
5M-row file-hygiene rule):

  * from the release vignette: ``family_id, valence, sign, typicality,
    evocativeness, domain, nonmoral_subdomain`` (+ derived ``valence_type``:
    moral / nonmoral / neutral);
  * from ``model_key`` via the registry: ``model_family`` and
    ``tuning_status`` (pretrained / finetuned);
  * from ``curated.csv`` (optional): ``moral_relevance, severity, vividness,
    typicality_perception`` (the curation-stage ratings, joined by
    variant_id -- used as continuous predictors in 1c secondary models).

Exclusions ledger (WO-8 §1, "never silent"): every response row that does
NOT enter the analysis DataFrame is accounted for by reason and counted --
parse failures, unknown/unreleased variants, variants not accepted into the
release, and ``format=="cancel"`` robustness-stub rows filtered out of the
primary analyses (spec-reserved format, WO-8 §4). Row counts are validated
against the ``jobs.jsonl`` manifest (spec §3.5): jobs with no completed
result are reported as an ``incomplete`` category. The whole ledger is
written to ``exclusions.json`` and printed.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence

import pandas as pd

from knobe.registry import Family, load_registry, model_key_for
from knobe.schemas import (
    CuratedRow,
    ExclusionEntry,
    ExclusionsLedger,
    JobRecord,
    ResultRecord,
    VignetteRow,
    read_csv_validated,
    read_jsonl,
)

# valence -> the analysis's three-way valence_type grouping. MB/MG are moral,
# NMB/NMG nonmoral, NEU neutral (the stakeless baseline handled by 1d).
VALENCE_TYPE = {
    "MB": "moral", "MG": "moral",
    "NMB": "nonmoral", "NMG": "nonmoral",
    "NEU": "neutral",
}

# Cap on how many offending ids each exclusion entry lists (the full count is
# always exact; the examples are a bounded sample for inspection).
_EXAMPLE_CAP = 20

# The columns of the analysis DataFrame, in a fixed order (byte-stable output).
ANALYSIS_COLUMNS = [
    "job_id", "prompt_id", "variant_id", "question_type", "format",
    "model_key", "model_family", "tuning_status",
    "family_id", "valence", "valence_type", "sign", "typicality",
    "evocativeness", "domain", "nonmoral_subdomain",
    "rating",
    "moral_relevance", "severity", "vividness", "typicality_perception",
]


def _default_registry_path() -> Path:
    return Path(__file__).resolve().parents[3] / "configs" / "models.yaml"


def build_model_key_index(registry: dict[str, Family]) -> dict[str, tuple[str, str]]:
    """Reverses ``registry.model_key_for``'s "{family}-{pretrained|instruct}"
    convention into ``model_key -> (model_family, tuning_status)`` for the
    denormalizing join (spec §3.6). Every (family, tuning_status) pair the
    registry can name is indexed, whether or not that checkpoint is actually
    present -- resolution of a missing checkpoint is WO-5's concern, not the
    analysis join's."""
    index: dict[str, tuple[str, str]] = {}
    for family_name in registry:
        for tuning_status in ("pretrained", "finetuned"):
            index[model_key_for(family_name, tuning_status)] = (family_name, tuning_status)
    return index


def _read_results(results_paths: Sequence[str | Path]) -> list[ResultRecord]:
    """Reads one or many results.jsonl shards (WO-8 §1: "possibly
    sharded/multiple files") into a single list, validating every row."""
    rows: list[ResultRecord] = []
    for path in results_paths:
        rows.extend(read_jsonl(path, ResultRecord))
    return rows


def _split_prompt_id(prompt_id: str) -> tuple[str, str, str] | None:
    parts = prompt_id.split("::")
    if len(parts) != 3:
        return None
    return parts[0], parts[1], parts[2]


def ingest(
    results_paths: Sequence[str | Path],
    vignettes_path: str | Path,
    *,
    curated_path: str | Path | None = None,
    jobs_path: str | Path | None = None,
    registry_path: str | Path | None = None,
    release: str = "unknown",
) -> tuple[pd.DataFrame, ExclusionsLedger]:
    """Joins results + release vignettes (+ optional curated ratings) into a
    tidy response-level DataFrame (``ANALYSIS_COLUMNS``), returning it with
    the exclusions ledger. Rows are dropped -- and counted, never silently --
    for: ``cancel``-format robustness rows (spec-reserved, WO-8 §4);
    unknown/unreleased variants; variants not accepted into the release
    (when ``curated_path`` given); unresolvable model_keys; and parse
    failures (``parse_ok`` false or ``parsed_rating`` null). Jobs in
    ``jobs_path`` with no result are reported as an ``incomplete`` category
    (spec §3.5 row-count validation)."""
    registry = load_registry(registry_path or _default_registry_path())
    key_index = build_model_key_index(registry)

    vignettes = read_csv_validated(vignettes_path, VignetteRow)
    vign_by_id = {v.variant_id: v for v in vignettes}

    curated_by_id: dict[str, CuratedRow] = {}
    accepted_ids: set[str] | None = None
    if curated_path is not None:
        curated = read_csv_validated(curated_path, CuratedRow)
        curated_by_id = {c.variant_id: c for c in curated}
        # Only accepted==True rows enter a release (spec §3.3); items present
        # in curated but not accepted are an explicit exclusion category.
        accepted_ids = {c.variant_id for c in curated if c.accepted}

    results = _read_results(results_paths)

    excl: dict[str, list[str]] = {}

    def _drop(reason: str, ident: str) -> None:
        excl.setdefault(reason, []).append(ident)

    rows: list[dict] = []
    for r in results:
        split = _split_prompt_id(r.prompt_id)
        if split is None:
            _drop("malformed_prompt_id", r.job_id)
            continue
        variant_id, question_type, prompt_format = split

        if prompt_format == "cancel":
            # Lindauer-Southwood cancelling-statement robustness stub: the
            # schema reserves format=="cancel" so the later follow-up reuses
            # this whole pipeline; it is filtered out of the PRIMARY analyses
            # here with a logged note (WO-8 §4), never silently.
            _drop("cancel_format_filtered", r.job_id)
            continue

        key = key_index.get(r.model_key)
        if key is None:
            _drop("unknown_model_key", r.job_id)
            continue
        model_family, tuning_status = key

        vignette = vign_by_id.get(variant_id)
        if vignette is None:
            _drop("unknown_variant", r.job_id)
            continue

        if accepted_ids is not None and variant_id not in accepted_ids:
            _drop("variant_not_accepted", r.job_id)
            continue

        if not r.parse_ok or r.parsed_rating is None:
            _drop("parse_failure", r.job_id)
            continue

        curated_row = curated_by_id.get(variant_id)
        rows.append(
            {
                "job_id": r.job_id,
                "prompt_id": r.prompt_id,
                "variant_id": variant_id,
                "question_type": question_type,
                "format": prompt_format,
                "model_key": r.model_key,
                "model_family": model_family,
                "tuning_status": tuning_status,
                "family_id": vignette.family_id,
                "valence": vignette.valence,
                "valence_type": VALENCE_TYPE[vignette.valence],
                "sign": vignette.sign,
                "typicality": vignette.typicality,
                "evocativeness": vignette.evocativeness,
                "domain": vignette.domain,
                "nonmoral_subdomain": vignette.nonmoral_subdomain,
                "rating": float(r.parsed_rating),
                "moral_relevance": curated_row.moral_relevance if curated_row else None,
                "severity": curated_row.severity if curated_row else None,
                "vividness": curated_row.vividness if curated_row else None,
                "typicality_perception": (
                    curated_row.typicality_perception if curated_row else None
                ),
            }
        )

    df = pd.DataFrame(rows, columns=ANALYSIS_COLUMNS)

    entries = [
        ExclusionEntry(reason=reason, count=len(ids), examples=sorted(ids)[:_EXAMPLE_CAP])
        for reason, ids in sorted(excl.items())
    ]
    n_excluded = sum(e.count for e in entries)

    # Row-count validation against the jobs.jsonl manifest (spec §3.5). Missing
    # results are INCOMPLETE WORK, tracked SEPARATELY (n_missing_results) -- they
    # are jobs with no result row at all, NOT result-row exclusions, so folding
    # them into n_excluded would break the reconciliation n_included + n_excluded
    # == n_result_rows (reviewer minor).
    n_job_rows: int | None = None
    n_missing_results = 0
    if jobs_path is not None:
        jobs = read_jsonl(jobs_path, JobRecord)
        n_job_rows = len(jobs)
        result_job_ids = {r.job_id for r in results}
        n_missing_results = sum(1 for j in jobs if j.job_id not in result_job_ids)
    ledger = ExclusionsLedger(
        release=release,
        n_result_rows=len(results),
        n_included=len(df),
        n_excluded=n_excluded,
        n_job_rows=n_job_rows,
        n_missing_results=n_missing_results,
        entries=entries,
    )
    return df, ledger


def write_exclusions(ledger: ExclusionsLedger, out_path: str | Path) -> None:
    """Writes ``exclusions.json`` (validated) AND prints a human summary --
    exclusions are never silent (WO-8 §1)."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(ledger.model_dump_json(indent=2), encoding="utf-8")
    print_exclusions(ledger, out_path)


def print_exclusions(ledger: ExclusionsLedger, out_path: str | Path | None = None) -> None:
    dest = f" (written to {out_path})" if out_path is not None else ""
    print(
        f"[analysis] exclusions ledger for release {ledger.release!r}{dest}: "
        f"of {ledger.n_result_rows} result rows read, {ledger.n_included} included and "
        f"{ledger.n_excluded} excluded.",
        file=sys.stderr,
    )
    for entry in ledger.entries:
        example = f" e.g. {entry.examples[0]}" if entry.examples else ""
        print(f"[analysis]   - {entry.reason}: {entry.count}{example}", file=sys.stderr)
    if ledger.n_job_rows is not None:
        # Missing manifest jobs are incomplete WORK, reported as a SEPARATE
        # sentence -- not folded into the result-row exclusion count above.
        print(
            f"[analysis]   manifest: {ledger.n_missing_results} of {ledger.n_job_rows} job(s) "
            f"have no completed result (incomplete work, tracked separately).",
            file=sys.stderr,
        )
