"""Deterministic synthetic pilot fixture generator for tests/test_power.py
(task-6-brief.md acceptance criterion: "bundled pilot fixture (generate a
small synthetic results.jsonl+vignettes.csv in tests/fixtures via a
committed deterministic script or conftest factory)").

This is the committed deterministic script; ``make_pilot_fixture`` is
called at test time (not import time) to materialize the pair of files
into a caller-supplied directory (typically pytest's ``tmp_path``) --
same inputs always produce byte-identical vignettes.csv/results.jsonl, so
this stays a pure function of its arguments, never bare ``random``/time-
seeded (common-context.md constraint 4).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from knobe import constants
from knobe.schemas import ResultRecord, VignetteRow, write_csv_validated, write_jsonl

DOMAIN = "Environment"
MODEL_KEY = "toy-model-instruct"

_VALENCES = ["MB", "MG", "NMB", "NMG", "NEU"]
# Stylized per-valence intentionality means for a "well-behaved" pilot
# subject model: MB rated more intentional than MG (the base Knobe
# asymmetry), a smaller NMB/NMG gap, NEU near the 0-10 scale's midpoint.
_VALENCE_MEANS = {"MB": 7.5, "MG": 3.5, "NMB": 6.0, "NMG": 5.0, "NEU": 5.0}


def make_pilot_fixture(
    out_dir: str | Path,
    *,
    n_families_per_valence: int = 3,
    n_samples: int = 3,
    seed: int = 7,
    model_key: str = MODEL_KEY,
) -> tuple[Path, Path]:
    """Writes ``vignettes.csv`` + ``results.jsonl`` into ``out_dir``.
    Returns (results_path, vignettes_path). Every family gets all 4
    variants (spec §3.2); every variant gets all 3 questions
    (intentionality/blame/praise, spec §4.2) x ``n_samples`` independent
    completions, all ``parse_ok=True`` (regex parse)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)

    vignette_rows: list[VignetteRow] = []
    result_rows: list[ResultRecord] = []

    family_counter = 0
    for valence in _VALENCES:
        sign = constants.SIGN_BY_VALENCE[valence]
        nonmoral_subdomain = "prudential" if valence in constants.NONMORAL_VALENCES else ""
        for _ in range(n_families_per_valence):
            family_id = f"ENV-{valence}-{family_counter:02d}"
            family_counter += 1
            base_mean = _VALENCE_MEANS[valence]
            for (typicality, evocativeness), letter in constants.VARIANT_LETTER.items():
                variant_id = f"{family_id}-{letter}"
                vignette_rows.append(
                    VignetteRow(
                        variant_id=variant_id, family_id=family_id, domain=DOMAIN,
                        valence=valence, nonmoral_subdomain=nonmoral_subdomain, sign=sign,
                        typicality=typicality, evocativeness=evocativeness,
                        scenario=f"Synthetic pilot scenario for {variant_id}.",
                        q_intentionality="Did they intentionally do it, on a scale from 0 to 10?",
                        q_blame="How blameworthy are they, on a scale from 0 to 10?",
                        q_praise="How praiseworthy are they, on a scale from 0 to 10?",
                    )
                )
                for question in ("intentionality", "blame", "praise"):
                    for sample_idx in range(n_samples):
                        prompt_id = f"{variant_id}::{question}::raw"
                        raw_rating = base_mean + rng.normal(0.0, 1.0)
                        rating = int(round(min(10.0, max(0.0, raw_rating))))
                        result_rows.append(
                            ResultRecord(
                                job_id=f"{prompt_id}::{model_key}::{sample_idx}",
                                prompt_id=prompt_id, model_key=model_key, sample_idx=sample_idx,
                                temperature=1.0, seed=sample_idx,
                                raw_response=str(rating), parsed_rating=rating,
                                parse_ok=True, parse_method="regex", logprobs_0_10=None,
                                model_revision="deadbeef", runner_version="test-fixture",
                                timestamp=0.0,
                            )
                        )

    results_path = out_dir / "results.jsonl"
    vignettes_path = out_dir / "vignettes.csv"
    write_jsonl(result_rows, results_path)
    write_csv_validated(vignette_rows, vignettes_path, VignetteRow)
    return results_path, vignettes_path
