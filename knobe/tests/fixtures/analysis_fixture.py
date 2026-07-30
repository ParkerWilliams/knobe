"""Deterministic synthetic analysis fixtures for tests/test_analysis.py
(WO-8 acceptance: simulation recovery + Type-I + determinism). Pure functions
of their arguments -- same inputs always produce byte-identical
vignettes.csv/results.jsonl/curated.csv, never bare random/time-seeded
(common-context.md constraint 4).

``make_analysis_data`` plants KNOWN RQ1 effects (in the FINETUNED checkpoint
only): a bad>good sign gap that is larger for moral than nonmoral items (base +
1a), a typicality effect concentrated on positive items and an evocativeness
effect concentrated on negative items (1c dissociation), and a NEU
intentionality offset from the midpoint (1d). The pretrained checkpoint has no
effects, so the sign x tuning interaction is nonzero. ``make_null_tidy`` builds
a tiny effect-free tidy frame for the Type-I test.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from knobe import constants
from knobe.registry import model_key_for
from knobe.schemas import (
    CuratedRow, ResultRecord, VignetteRow, write_csv_validated, write_jsonl,
)

MU = 5.0
MORAL_GAP = 3.0        # bad-good intentionality gap, moral items, finetuned
NONMORAL_GAP = 1.0     # smaller gap for nonmoral items (1a: moral > nonmoral)
TYP_POS = 2.0          # typicality effect concentrated on GOOD items (1c)
EVOC_NEG = 2.0         # evocativeness effect concentrated on BAD items (1c)
NEU_OFFSET = 1.5       # NEU intentionality offset from midpoint (1d)
NOISE_SD = 0.8

_VALENCES = ["MB", "MG", "NMB", "NMG", "NEU"]
_DOMAINS = ["Environment", "Healthcare"]
FAMILY = "llama-3.1-8b"


def _clip_round(x: float) -> int:
    return int(round(min(10.0, max(0.0, x))))


def _mean_intentionality(valence: str, sign: str, tuning: str, typ_c: float, evoc_c: float) -> float:
    mean = MU
    if tuning != "finetuned":
        return mean
    s = 0.5 if sign == "bad" else (-0.5 if sign == "good" else 0.0)
    if valence in ("MB", "MG"):
        mean += MORAL_GAP * s
    elif valence in ("NMB", "NMG"):
        mean += NONMORAL_GAP * s
    if valence == "NEU":
        mean += NEU_OFFSET
    # 1c: typicality effect on GOOD items, evocativeness effect on BAD items.
    if sign == "good":
        mean += TYP_POS * typ_c
    if sign == "bad":
        mean += EVOC_NEG * evoc_c
    return mean


def make_analysis_data(
    out_dir: str | Path,
    *,
    n_families_per_valence: int = 6,
    n_samples: int = 6,
    seed: int = 11,
    family_name: str = FAMILY,
    include_chat: bool = False,
    n_domains: int = 2,
) -> dict[str, Path]:
    """Writes vignettes.csv, results.jsonl (both checkpoints) and curated.csv
    into ``out_dir`` with the planted effects above. Returns a dict of paths."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)

    vignette_rows: list[VignetteRow] = []
    curated_rows: list[CuratedRow] = []
    result_rows: list[ResultRecord] = []

    model_keys = {t: model_key_for(family_name, t) for t in ("pretrained", "finetuned")}
    domains = _DOMAINS if n_domains <= len(_DOMAINS) else [f"domain{d}" for d in range(n_domains)]
    domains = domains[:n_domains]

    counter = 0
    for valence in _VALENCES:
        sign = constants.SIGN_BY_VALENCE[valence]
        subdomain = "prudential" if valence in constants.NONMORAL_VALENCES else ""
        for _ in range(n_families_per_valence):
            domain = domains[counter % len(domains)]
            family_id = f"ENV-{valence}-{counter:02d}"
            counter += 1
            fam_int = float(rng.normal(0.0, 0.5))
            for (typicality, evocativeness), letter in constants.VARIANT_LETTER.items():
                variant_id = f"{family_id}-{letter}"
                typ_c = 0.5 if typicality == "uncommon" else -0.5
                evoc_c = 0.5 if evocativeness == "high" else -0.5
                vignette_rows.append(
                    VignetteRow(
                        variant_id=variant_id, family_id=family_id, domain=domain,
                        valence=valence, nonmoral_subdomain=subdomain, sign=sign,
                        typicality=typicality, evocativeness=evocativeness,
                        scenario=f"Synthetic scenario for {variant_id}.",
                        q_intentionality="Did they intentionally do it, 0 to 10?",
                        q_blame="How blameworthy, 0 to 10?",
                        q_praise="How praiseworthy, 0 to 10?",
                    )
                )
                curated_rows.append(
                    CuratedRow(
                        variant_id=variant_id, family_id=family_id, domain=domain,
                        valence=valence, nonmoral_subdomain=subdomain, sign=sign,
                        typicality=typicality, evocativeness=evocativeness,
                        scenario=f"Synthetic scenario for {variant_id}.",
                        q_intentionality="Did they intentionally do it, 0 to 10?",
                        q_blame="How blameworthy, 0 to 10?",
                        q_praise="How praiseworthy, 0 to 10?",
                        moral_relevance=8 if valence in ("MB", "MG") else 2,
                        severity=6 if sign == "bad" else 2,
                        vividness=_clip_round(5 + 3 * evoc_c),
                        typicality_perception=_clip_round(5 + 3 * typ_c),
                        reviewer_model="mock-reviewer", curation_date="2026-07-27",
                        accepted=True,
                    )
                )
                formats = ("raw", "chat") if include_chat else ("raw",)
                for tuning, model_key in model_keys.items():
                    for question in ("intentionality", "blame", "praise"):
                        for fmt in formats:
                            for sample_idx in range(n_samples):
                                if question == "intentionality":
                                    base = _mean_intentionality(valence, sign, tuning, typ_c, evoc_c)
                                elif question == "blame":
                                    base = MU + (2.0 if sign == "bad" else -1.0)
                                else:  # praise
                                    base = MU + (2.0 if sign == "good" else -1.0)
                                rating = _clip_round(base + fam_int + rng.normal(0.0, NOISE_SD))
                                prompt_id = f"{variant_id}::{question}::{fmt}"
                                result_rows.append(
                                    ResultRecord(
                                        job_id=f"{prompt_id}::{model_key}::{sample_idx}",
                                        prompt_id=prompt_id, model_key=model_key,
                                        sample_idx=sample_idx, temperature=1.0, seed=sample_idx,
                                        raw_response=str(rating), parsed_rating=rating,
                                        parse_ok=True, parse_method="regex", logprobs_0_10=None,
                                        model_revision="deadbeef", runner_version="test-fixture",
                                        timestamp=0.0,
                                    )
                                )

    paths = {
        "vignettes": out_dir / "vignettes.csv",
        "results": out_dir / "results.jsonl",
        "curated": out_dir / "curated.csv",
    }
    write_csv_validated(vignette_rows, paths["vignettes"], VignetteRow)
    write_csv_validated(curated_rows, paths["curated"], CuratedRow)
    write_jsonl(result_rows, paths["results"])
    return paths


# ---------------------------------------------------------------------------
# Null (effect-free) tidy frame for the Type-I test -- bypasses ingest so the
# per-sim cost is a single mixedlm fit (keeps 200 sims fast; WO-8 acceptance).
# ---------------------------------------------------------------------------


def make_domain_variance_tidy(seed: int = 3, *, n_domains: int = 6, n_fam_per_domain: int = 6, n_resp: int = 4) -> pd.DataFrame:
    """A tidy frame with REAL domain-level variance entangled with the sign
    contrast: each domain carries the sign as a whole (alternating bad/good) plus
    a domain-level random intercept, so the sign effect is a BETWEEN-domain
    contrast. A family-RI fit (many small independent clusters) then reports a
    much smaller SE for sign than a domain-clustered fit that correctly accounts
    for the between-domain confounding -- the reviewer's construction proving the
    domain-sensitivity fit is genuinely domain-aware, NOT the inert vc_formula.
    Columns: family_id, domain, rating, sign_c."""
    rng = np.random.default_rng(seed)
    rows = []
    fam = 0
    for d in range(n_domains):
        domain = f"D{d}"
        domain_int = rng.normal(0.0, 1.5)
        sign_c = 0.5 if d % 2 == 0 else -0.5  # sign carried at the domain level
        for _ in range(n_fam_per_domain):
            fam_id = f"F{fam:04d}"
            fam += 1
            fam_int = rng.normal(0.0, 0.4)
            for _ in range(n_resp):
                rating = MU + domain_int + fam_int + 1.0 * sign_c + rng.normal(0.0, 0.8)
                rows.append({"family_id": fam_id, "domain": domain, "rating": float(rating), "sign_c": sign_c})
    return pd.DataFrame(rows)


def make_domain_slope_tidy(
    seed: int = 5, *, heterogeneous: bool, n_domains: int = 10,
    n_fam_per_domain: int = 4, n_resp: int = 6, slope_sd: float = 1.5,
) -> pd.DataFrame:
    """A tidy frame for the domain-RANDOM-SLOPE sensitivity test. The sign
    effect's slope varies BY DOMAIN when ``heterogeneous`` (drawn ~ N(1.0,
    slope_sd) per domain -- real cross-domain effect heterogeneity), or is
    constant 1.0 across domains when homogeneous. ``sign_c`` is balanced within
    each family (so the slope is estimable within every domain). Columns:
    family_id, domain, rating, sign_c."""
    rng = np.random.default_rng(seed)
    rows = []
    fam = 0
    for d in range(n_domains):
        domain = f"D{d}"
        domain_int = rng.normal(0.0, 1.0)
        domain_slope = 1.0 + (rng.normal(0.0, slope_sd) if heterogeneous else 0.0)
        for _ in range(n_fam_per_domain):
            fam_id = f"F{fam:04d}"
            fam += 1
            fam_int = rng.normal(0.0, 0.3)
            for k in range(n_resp):
                sign_c = 0.5 if k % 2 == 0 else -0.5  # balanced within family
                rating = MU + domain_int + fam_int + domain_slope * sign_c + rng.normal(0.0, 0.8)
                rows.append({"family_id": fam_id, "domain": domain, "rating": float(rating), "sign_c": sign_c})
    return pd.DataFrame(rows)


def _sim_seed(base_seed: int, sim_idx: int) -> int:
    return int(hashlib.sha256(f"{base_seed}|{sim_idx}".encode()).hexdigest(), 16) % (2**32)


def make_null_tidy(base_seed: int, sim_idx: int, *, n_fam_per_cell: int = 10, n_resp: int = 3) -> pd.DataFrame:
    """A tiny effect-free response-level frame for a valence-type x sign design
    (the rq1a primary contrast): families crossed over moral/nonmoral x bad/good,
    all cell means equal (null). Only family intercept + response noise vary."""
    rng = np.random.default_rng(_sim_seed(base_seed, sim_idx))
    rows = []
    fam = 0
    for vt in ("moral", "nonmoral"):
        for sign in ("bad", "good"):
            for _ in range(n_fam_per_cell):
                fam_id = f"F{fam:04d}"
                fam += 1
                fam_int = rng.normal(0.0, 0.7)
                sign_c = 0.5 if sign == "bad" else -0.5
                vt_c = 0.5 if vt == "moral" else -0.5
                for r in MU + fam_int + rng.normal(0.0, 1.0, size=n_resp):
                    rows.append({"family_id": fam_id, "rating": float(r), "sign_c": sign_c, "vt_c": vt_c})
    return pd.DataFrame(rows)
