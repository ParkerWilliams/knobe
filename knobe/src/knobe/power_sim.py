"""Simulation engine for ``src/knobe/power.py`` (WO-4 §2): the
Westfall-Judd-Kenny-style crossed-random-effects DGP and the per-RQ1-
sub-question contrast simulators. Split out of ``power.py`` (whose
docstring explains why: this module is pure numpy/pandas/statsmodels
simulation code with no CLI/I/O surface, kept separate so ``power.py``
stays focused on orchestration -- see task-6-brief.md's "Code Organization"
note).

DGP (task-6-brief.md controller decision): for every contrast, response-
level ratings are generated as

    rating_ijk = mu + family_j + fixed_effect(condition) + eps_ijk

``family_j ~ N(0, var_family)``, one draw per family, shared by every
response nested in that family (the family side of Westfall/Judd/Kenny's
crossed random effects). ``eps_ijk ~ N(0, var_resid)``, one independent
draw per response. Both variance components come from
``power.estimate_variance_components`` fit on the pilot data.

There is deliberately no separate item-in-family (variant-level) random-
effect variance component: ``estimate_variance_components`` only estimates
two components (family, response-level residual) because the per-subject-
model mixedlm fit it uses has no crossed random effects for model x family
(statsmodels ``MixedLM`` limitation -- see ``power.py``'s module
docstring). Item-to-item variation within a family is therefore absorbed
into ``var_resid``; each contrast simulator documents which experimental
factors it represents as within-family fixed effects and which it
collapses over. This is a stated simplification, not an oversight.

Ratings are simulated on an unbounded (real-valued) analysis scale;
clipping to [0, 10] is NOT applied before fitting (task-6-brief.md:
"clipping applied for realism check only, primary sims run unclipped --
simpler and standard"). Each replicate instead records ``frac_clipped`` --
the fraction of its raw simulated response values that would have fallen
outside [0, 10] -- purely as a realism diagnostic surfaced in
``PowerGridRow``; it never affects the p-value or the power estimate.

Convergence-failure policy (never silently drop, task-6-brief.md): each
replicate first attempts a ``statsmodels`` mixedlm fit with a random
intercept for family. If it raises, fails to converge, or emits a
``ConvergenceWarning``, the replicate falls back to OLS with cluster-robust
SEs (clustered on family) to obtain a p-value -- the replicate always
contributes to the power denominator; convergence failures and fallback
usage are counted per grid point in ``PowerGridRow``.
"""
from __future__ import annotations

import hashlib
import warnings
from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.tools.sm_exceptions import ConvergenceWarning

# ---------------------------------------------------------------------------
# Seeding (task-6-brief.md controller decision, EXACT -- do not change
# without a version bump; see common-context.md constraint 4).
# ---------------------------------------------------------------------------


def derive_seed(seed: int, item_count: int, n: int, contrast: str, sim_idx: int) -> int:
    """One simulation replicate's RNG seed: sha256(seed, item_count, n,
    contrast, sim_idx) % 2**32. Every replicate of every grid point gets its
    own independently-derived seed -- reruns are exactly reproducible."""
    material = f"{seed}|{item_count}|{n}|{contrast}|{sim_idx}".encode("utf-8")
    digest = hashlib.sha256(material).hexdigest()
    return int(digest, 16) % (2**32)


@dataclass(frozen=True)
class SimParams:
    """Shared simulation inputs for every contrast (WO-4 §2)."""

    mu: float
    var_family: float
    var_resid: float
    effect_size: float
    alpha: float = 0.05


@dataclass(frozen=True)
class SimResult:
    p_value: float
    converged: bool
    fallback_used: bool
    frac_clipped: float


# ---------------------------------------------------------------------------
# Generic DGP + fit/test helpers
# ---------------------------------------------------------------------------


def simulate_intercept_only(
    rng: np.random.Generator,
    n_families: int,
    n_per_family: int,
    mu: float,
    var_family: float,
    var_resid: float,
    family_prefix: str = "F",
) -> pd.DataFrame:
    """Intercept-only DGP: one random family-intercept draw per family,
    ``n_per_family`` residual-noise responses per family. Used directly by
    the synthetic variance-recovery test and by the 1d (NEU offset)
    contrast."""
    sd_family = np.sqrt(var_family)
    sd_resid = np.sqrt(var_resid)
    family_effects = rng.normal(0.0, sd_family, size=n_families)
    rows = []
    for j in range(n_families):
        family_id = f"{family_prefix}{j:05d}"
        noise = rng.normal(0.0, sd_resid, size=n_per_family)
        for e in noise:
            rows.append({"family_id": family_id, "rating": mu + family_effects[j] + e})
    return pd.DataFrame(rows)


def _frac_out_of_range(values) -> float:
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return 0.0
    return float(np.mean((arr < 0.0) | (arr > 10.0)))


def _fit_and_test(df: pd.DataFrame, formula: str, groups_col: str, test_term: str) -> tuple[float, bool, bool]:
    """Fits ``formula`` as a mixedlm with random intercept for
    ``groups_col``; falls back to OLS with cluster-robust SEs (clustered on
    ``groups_col``) if the mixedlm fit raises, fails to converge, or emits
    a ConvergenceWarning. Returns (p_value_for_test_term, mixedlm_converged,
    fallback_used). Warnings from either fit are captured locally (never
    left to propagate as bare warnings -- this repo's pytest config turns
    warnings into hard errors) and used as an additional non-convergence
    signal for the mixedlm attempt."""
    converged = False
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            md = smf.mixedlm(formula, data=df, groups=df[groups_col])
            mdf = md.fit()
        had_convergence_warning = any(issubclass(w.category, ConvergenceWarning) for w in caught)
        converged = bool(getattr(mdf, "converged", False)) and not had_convergence_warning
        if converged and test_term in mdf.pvalues.index:
            p = float(mdf.pvalues[test_term])
            if np.isfinite(p):
                return p, True, False
        converged = False  # any path reaching here needs the OLS fallback below
    except Exception:
        converged = False

    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        ols = smf.ols(formula, data=df).fit(cov_type="cluster", cov_kwds={"groups": df[groups_col]})
    p = float(ols.pvalues[test_term])
    if not np.isfinite(p):
        p = 1.0  # degenerate fit: conservative "not significant", never dropped
    return p, converged, True


# ---------------------------------------------------------------------------
# Contrast simulators (WO-4 §2 / task-6-brief.md's RQ1 sub-question list).
# Each takes (rng, item_count, n, params) and returns one SimResult for one
# simulation replicate. ``item_count`` is a PER-CELL item target (DR §16's
# "per-cell item target" framing); ``n`` is the response-level N per item
# (or per within-family condition-cell, where noted).
# ---------------------------------------------------------------------------


def simulate_1a(rng: np.random.Generator, item_count: int, n: int, params: SimParams) -> SimResult:
    """1a: valence-type (moral/nonmoral) x sign (bad/good) interaction --
    the MB/MG/NMB/NMG asymmetry-of-asymmetries. ``item_count`` families per
    valence x sign cell (4 cells total); families are between-subject on
    this contrast (typicality/evocativeness collapsed -- not this
    contrast's estimand). Cell means are set so the bad-vs-good gap is
    ``effect_size`` within "moral" and 0 within "nonmoral", i.e. the
    interaction contrast itself equals ``effect_size``."""
    cell_means = {
        ("moral", "bad"): params.mu + params.effect_size / 2,
        ("moral", "good"): params.mu - params.effect_size / 2,
        ("nonmoral", "bad"): params.mu,
        ("nonmoral", "good"): params.mu,
    }
    sd_family = np.sqrt(params.var_family)
    sd_resid = np.sqrt(params.var_resid)
    rows = []
    raw_values: list[float] = []
    fam_idx = 0
    for (vt, sg), cell_mu in cell_means.items():
        for _ in range(item_count):
            family_id = f"1a_{fam_idx:05d}"
            fam_idx += 1
            fam_eff = rng.normal(0.0, sd_family)
            values = cell_mu + fam_eff + rng.normal(0.0, sd_resid, size=n)
            raw_values.extend(values.tolist())
            vt_code = 0.5 if vt == "moral" else -0.5
            sg_code = 0.5 if sg == "bad" else -0.5
            for v in values:
                rows.append({"family_id": family_id, "rating": v, "vt": vt_code, "sg": sg_code})
    df = pd.DataFrame(rows)
    p, converged, fallback = _fit_and_test(df, "rating ~ vt*sg", "family_id", "vt:sg")
    return SimResult(p, converged, fallback, _frac_out_of_range(raw_values))


def simulate_1b(rng: np.random.Generator, item_count: int, n: int, params: SimParams) -> SimResult:
    """1b: blame/praise slope difference -- within "bad" items,
    intentionality ~ blame; within "good" items, intentionality ~ praise;
    test whether the two slopes differ (DR's blame/praise dissociation,
    Hindriks et al. 2016). Modeled as a single predictor column ``x``
    (standardized, mean 0 / sd 1 -- standing in for "blame" on bad-valence
    rows and "praise" on good-valence rows, since each row only ever has
    one of the two ratings) interacting with a bad/good dummy: the ``x:sg``
    coefficient is exactly the slope-difference test. ``effect_size`` is
    the target slope difference; ``base_slope`` is an arbitrary but fixed
    average slope. Documented simplification: only intentionality's
    variance components are estimated from the pilot (WO-4 §1), so the
    blame/praise predictor itself is simulated on a generic standardized
    scale rather than from its own pilot-estimated variance -- the
    slope-difference effect size is independently configurable in
    power.yaml precisely because its units don't literally match the other
    contrasts' rating-point mean-difference default."""
    base_slope = 0.5
    slope_bad = base_slope + params.effect_size / 2
    slope_good = base_slope - params.effect_size / 2
    sd_family = np.sqrt(params.var_family)
    sd_resid = np.sqrt(params.var_resid)
    rows = []
    raw_values: list[float] = []
    fam_idx = 0
    for sign, slope in (("bad", slope_bad), ("good", slope_good)):
        for _ in range(item_count):
            family_id = f"1b_{fam_idx:05d}"
            fam_idx += 1
            fam_eff = rng.normal(0.0, sd_family)
            x = rng.normal(0.0, 1.0, size=n)
            values = params.mu + fam_eff + slope * x + rng.normal(0.0, sd_resid, size=n)
            raw_values.extend(values.tolist())
            sg_code = 0.5 if sign == "bad" else -0.5
            for xv, v in zip(x, values):
                rows.append({"family_id": family_id, "rating": v, "x": xv, "sg": sg_code})
    df = pd.DataFrame(rows)
    p, converged, fallback = _fit_and_test(df, "rating ~ x*sg", "family_id", "x:sg")
    return SimResult(p, converged, fallback, _frac_out_of_range(raw_values))


def _simulate_sign_by_within_factor(
    rng: np.random.Generator, item_count: int, n: int, params: SimParams, family_prefix: str
) -> SimResult:
    """Shared DGP for 1c's two sub-contrasts: a within-family 2-level
    factor (typicality OR evocativeness -- the caller picks which, the
    OTHER factor is collapsed/not represented, a documented simplification)
    crossed with sign (bad/good), which IS between-family (family_id
    determines valence, hence sign). ``item_count`` families per sign level
    (2 cells); each family contributes both levels of the within factor,
    ``n`` responses per (family, level). Level effects make the
    within-factor gap equal ``effect_size`` under "bad" and 0 under "good"
    -- the sign x within-factor interaction contrast equals ``effect_size``."""
    level_effect = {
        ("bad", 1): params.effect_size / 2,
        ("bad", 0): -params.effect_size / 2,
        ("good", 1): 0.0,
        ("good", 0): 0.0,
    }
    sd_family = np.sqrt(params.var_family)
    sd_resid = np.sqrt(params.var_resid)
    rows = []
    raw_values: list[float] = []
    fam_idx = 0
    for sign in ("bad", "good"):
        for _ in range(item_count):
            family_id = f"{family_prefix}_{fam_idx:05d}"
            fam_idx += 1
            fam_eff = rng.normal(0.0, sd_family)
            sg_code = 0.5 if sign == "bad" else -0.5
            for level in (0, 1):
                values = (
                    params.mu + fam_eff + level_effect[(sign, level)]
                    + rng.normal(0.0, sd_resid, size=n)
                )
                raw_values.extend(values.tolist())
                lv_code = 0.5 if level == 1 else -0.5
                for v in values:
                    rows.append({"family_id": family_id, "rating": v, "sg": sg_code, "lv": lv_code})
    df = pd.DataFrame(rows)
    p, converged, fallback = _fit_and_test(df, "rating ~ sg*lv", "family_id", "sg:lv")
    return SimResult(p, converged, fallback, _frac_out_of_range(raw_values))


def simulate_1c_typicality(rng: np.random.Generator, item_count: int, n: int, params: SimParams) -> SimResult:
    """1c (typicality half): typicality (common/uncommon) x sign interaction,
    evocativeness collapsed. See ``_simulate_sign_by_within_factor``."""
    return _simulate_sign_by_within_factor(rng, item_count, n, params, "1c_typ")


def simulate_1c_evocativeness(rng: np.random.Generator, item_count: int, n: int, params: SimParams) -> SimResult:
    """1c (evocativeness half): evocativeness (low/high) x sign interaction,
    typicality collapsed. See ``_simulate_sign_by_within_factor``."""
    return _simulate_sign_by_within_factor(rng, item_count, n, params, "1c_evoc")


def simulate_1d(rng: np.random.Generator, item_count: int, n: int, params: SimParams) -> SimResult:
    """1d: NEU offset vs. scale midpoint (5). ``item_count`` NEU families
    (sign is "na" for NEU -- a single between-family cell, no sign/typ/evoc
    crossing), ``n`` responses per family. Tests whether the family-level
    mean rating differs from 5 (a one-sample-style Wald test on the
    intercept of the mean-5-centered outcome)."""
    df = simulate_intercept_only(
        rng, item_count, n, params.mu + params.effect_size, params.var_family, params.var_resid,
        family_prefix="1d_",
    )
    raw_values = df["rating"].tolist()
    df = df.assign(rating_centered=df["rating"] - params.mu)
    p, converged, fallback = _fit_and_test(df, "rating_centered ~ 1", "family_id", "Intercept")
    return SimResult(p, converged, fallback, _frac_out_of_range(raw_values))


ContrastFn = Callable[[np.random.Generator, int, int, SimParams], SimResult]

CONTRASTS: dict[str, ContrastFn] = {
    "1a": simulate_1a,
    "1b": simulate_1b,
    "1c_typicality": simulate_1c_typicality,
    "1c_evocativeness": simulate_1c_evocativeness,
    "1d": simulate_1d,
}

# Machine-readable per-contrast family multiplier: total families simulated
# at one (contrast, item_count) grid point is item_count * FAMILY_MULTIPLIER
# [contrast] -- MUST match each simulator's actual family-generation loop
# (a reviewer flagged that power_report.md itself needs to surface this,
# not just the docstrings, so 1a's and 1d's tables can't be misread as
# equal-family designs):
#   1a (simulate_1a): 4 cells (moral/nonmoral x bad/good), item_count
#     families per cell -> 4 * item_count.
#   1b (simulate_1b): 2 cells (bad/good), item_count families per cell
#     -> 2 * item_count.
#   1c_typicality / 1c_evocativeness (_simulate_sign_by_within_factor):
#     2 cells (bad/good), item_count families per cell -> 2 * item_count
#     (the within-family factor doesn't add families, just responses).
#   1d (simulate_1d): 1 cell (NEU only), item_count families -> item_count.
FAMILY_MULTIPLIER: dict[str, int] = {
    "1a": 4,
    "1b": 2,
    "1c_typicality": 2,
    "1c_evocativeness": 2,
    "1d": 1,
}


# ---------------------------------------------------------------------------
# Grid-point aggregation: run n_sims replicates, aggregate to one row's
# worth of counts.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GridPointStats:
    n_sims: int
    n_significant: int
    n_converged: int
    n_convergence_failures: int
    n_fallback_used: int
    power: float
    frac_clipped: float


def run_grid_point(
    contrast: str,
    item_count: int,
    n: int,
    params: SimParams,
    seed: int,
    n_sims: int,
    sim_idx_start: int = 0,
) -> GridPointStats:
    """Runs ``n_sims`` independent simulation replicates for one
    (contrast, item_count, n) grid point and aggregates them. Each
    replicate's seed is independently derived (``derive_seed``) from
    ``sim_idx_start + i`` for ``i in range(n_sims)`` -- ``sim_idx_start``
    lets a grid point be split across multiple checkpointed batches without
    reusing a replicate's seed."""
    if contrast not in CONTRASTS:
        raise ValueError(f"unknown contrast {contrast!r}; known contrasts: {sorted(CONTRASTS)}")
    sim_fn = CONTRASTS[contrast]

    n_significant = 0
    n_converged = 0
    n_fallback = 0
    frac_clipped_values: list[float] = []
    for i in range(n_sims):
        sim_idx = sim_idx_start + i
        derived_seed = derive_seed(seed, item_count, n, contrast, sim_idx)
        rng = np.random.default_rng(derived_seed)
        result = sim_fn(rng, item_count, n, params)
        if result.p_value < params.alpha:
            n_significant += 1
        if result.converged:
            n_converged += 1
        if result.fallback_used:
            n_fallback += 1
        frac_clipped_values.append(result.frac_clipped)

    power = n_significant / n_sims if n_sims else 0.0
    frac_clipped = float(np.mean(frac_clipped_values)) if frac_clipped_values else 0.0
    return GridPointStats(
        n_sims=n_sims,
        n_significant=n_significant,
        n_converged=n_converged,
        n_convergence_failures=n_sims - n_converged,
        n_fallback_used=n_fallback,
        power=power,
        frac_clipped=frac_clipped,
    )
