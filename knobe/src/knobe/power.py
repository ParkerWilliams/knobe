"""WO-4: pilot variance decomposition + Westfall-Judd-Kenny-style
simulation-based power determination (DR §16).

Two artifacts feed off a pilot ``results.jsonl``/``vignettes.csv``:
  1. ``estimate_variance_components`` -- fits a per-subject-model,
     per-question mixed model (random intercept for family, response-level
     residual variance) and reports the ICC.
  2. The simulation grid (``power_sim.py``) -- given those variance
     components and an assumed effect size, simulates the planned RQ1
     contrasts over an (item_count x response-N) grid, >= 1000 replicates
     per point by default, and estimates power as the fraction of
     replicates whose planned-contrast p-value clears alpha.

Both write append-only, resumable JSONL checkpoints (``schemas.py``'s
``VarianceComponents``/``PowerGridRow``) and a markdown + PNG decision
report (``generate_report``) that is this work order's gate artifact for
G2 (WO4_pilot_power.md §3).

Controller decision -- statsmodels, not rpy2/lme4 (task-6-brief.md): this
package already depends on statsmodels/scipy/matplotlib/pandas/numpy for
S8's analysis pipeline (master spec §6), and ``statsmodels.formula.api.
mixedlm`` is adequate for the variance-component estimation this work
order actually needs -- a single random intercept for family, plus
response-level residual variance. Bridging to R's lme4 via rpy2 would add
a second language runtime + an R installation as a hard dependency of a
laptop-run pipeline stage, for a model class statsmodels already
implements. The real limitation this buys: statsmodels' ``MixedLM`` has no
support for CROSSED random effects (e.g. family x model simultaneously,
the fully general Westfall/Judd/Kenny structure). WO-4 §1 sidesteps this by
fitting one model PER SUBJECT MODEL (exactly WO4_pilot_power.md's own
phrasing) rather than one model with model as a second random-effects
factor -- so the crossed-effects limitation never actually binds here. The
simulation stage (power_sim.py) documents the same simplification for its
own DGP (no separate item-in-family variance component).

Code organization (task-6-brief.md): this module ("power.py") stays
"public API + CLI/IO orchestration" -- pilot join, variance-component
estimation, config loading, grid orchestration/checkpointing/resume, and
report generation. The pure simulation math (DGP + per-contrast
simulators, no I/O) lives in ``power_sim.py``, split out because it grew
past what's comfortable in one file and has a genuinely different
concern (numpy/pandas/statsmodels math vs. file/CLI orchestration).
"""
from __future__ import annotations

import sys
import time
import warnings
from pathlib import Path
from typing import Sequence

import pandas as pd
import statsmodels.formula.api as smf
from pydantic import Field
from statsmodels.tools.sm_exceptions import ConvergenceWarning

from knobe.power_sim import CONTRASTS, FAMILY_MULTIPLIER, SimParams, run_grid_point
from knobe.schemas import (
    KnobeModel,
    PowerGridRow,
    QuestionType,
    ResultRecord,
    VarianceComponents,
    VignetteRow,
    append_jsonl,
    read_csv_validated,
    read_jsonl,
)

DEFAULT_THRESHOLDS = (0.8, 0.9)


# ---------------------------------------------------------------------------
# Pilot join + variance-component estimation (WO-4 §1)
# ---------------------------------------------------------------------------


def _join_pilot(
    results: Sequence[ResultRecord],
    vignettes: Sequence[VignetteRow],
    *,
    question: str,
    model_key: str,
    fmt: str = "raw",
) -> pd.DataFrame:
    """Joins ``results`` to ``vignettes`` via ``variant_id`` recovered by
    splitting ``prompt_id`` on ``"::"`` (spec §3.4/§3.6's join key), filtered
    to one ``question_type``, one prompt ``fmt`` (default "raw", the
    primary format -- "chat" is a robustness-pass duplicate, spec §3.4),
    one ``model_key``, and only rows that parsed (``parse_ok`` and a
    non-null ``parsed_rating``). Returns a tidy DataFrame with one row per
    response: family_id, variant_id, rating, valence, sign, typicality,
    evocativeness."""
    vign_by_id = {v.variant_id: v for v in vignettes}
    rows = []
    for r in results:
        parts = r.prompt_id.split("::")
        if len(parts) != 3:
            continue
        variant_id, question_type, prompt_format = parts
        if question_type != question or prompt_format != fmt:
            continue
        if r.model_key != model_key:
            continue
        if not r.parse_ok or r.parsed_rating is None:
            continue
        vignette = vign_by_id.get(variant_id)
        if vignette is None:
            continue
        rows.append(
            {
                "family_id": vignette.family_id,
                "variant_id": variant_id,
                "rating": float(r.parsed_rating),
                "valence": vignette.valence,
                "sign": vignette.sign,
                "typicality": vignette.typicality,
                "evocativeness": vignette.evocativeness,
            }
        )
    return pd.DataFrame(rows)


def _moment_variance_components(df: pd.DataFrame, group_col: str, value_col: str) -> tuple[float, float]:
    """Method-of-moments (one-way random-effects ANOVA) variance-component
    estimator -- the fallback used when the mixedlm fit itself fails or
    doesn't converge (never silently drop the estimate, task-6-brief.md).
    Standard unbalanced-design formula (Searle, Casella & McCulloch,
    *Variance Components*, 1992, ch. 3): var_resid = within-group MS;
    var_family = max(0, (between-group MS - within-group MS) / n0), with
    n0 the usual unbalanced-design correction."""
    counts = df.groupby(group_col)[value_col].count()
    n_total = int(counts.sum())
    k = len(counts)
    grand_mean = float(df[value_col].mean())
    group_means = df.groupby(group_col)[value_col].mean()

    ss_between = float((counts * (group_means - grand_mean) ** 2).sum())
    ss_within = 0.0
    for group_id, mean_value in group_means.items():
        group_values = df.loc[df[group_col] == group_id, value_col]
        ss_within += float(((group_values - mean_value) ** 2).sum())

    df_between = k - 1
    df_within = n_total - k
    msb = ss_between / df_between if df_between > 0 else 0.0
    msw = ss_within / df_within if df_within > 0 else 0.0
    n0 = (n_total - float((counts**2).sum()) / n_total) / df_between if df_between > 0 else float(counts.mean())

    var_resid = max(msw, 1e-9)
    var_family = max(0.0, (msb - msw) / n0) if n0 > 0 else 0.0
    return var_family, var_resid


def estimate_variance_components(
    results: Sequence[ResultRecord],
    vignettes: Sequence[VignetteRow],
    *,
    question: QuestionType = "intentionality",
    model_key: str,
) -> VarianceComponents:
    """WO-4 §1: fits ``rating ~ 1`` with a random intercept for family
    (mixedlm) on the pilot's ``question``/``model_key`` subset, reporting
    ``var_family`` (random-intercept variance), ``var_resid`` (response-
    level residual variance), and ``icc = var_family / (var_family +
    var_resid)``. Falls back to a method-of-moments ANOVA estimator
    (``_moment_variance_components``) if the mixedlm fit raises, fails to
    converge, or emits a ConvergenceWarning -- never silently dropped;
    ``fallback_used``/``convergence_ok`` record which path was taken."""
    df = _join_pilot(results, vignettes, question=question, model_key=model_key)
    if df.empty:
        raise ValueError(
            f"no pilot rows for model_key={model_key!r} question={question!r} "
            f"(format='raw', parse_ok=True) -- nothing to fit"
        )

    n_families = int(df["family_id"].nunique())
    n_items = int(df["variant_id"].nunique())
    n_responses = int(len(df))

    convergence_ok = False
    var_family: float | None = None
    var_resid: float | None = None
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            md = smf.mixedlm("rating ~ 1", data=df, groups=df["family_id"])
            mdf = md.fit()
        had_convergence_warning = any(issubclass(w.category, ConvergenceWarning) for w in caught)
        convergence_ok = bool(getattr(mdf, "converged", False)) and not had_convergence_warning
        if convergence_ok:
            var_family = float(mdf.cov_re.iloc[0, 0])
            var_resid = float(mdf.scale)
    except Exception:
        convergence_ok = False

    fallback_used = False
    if var_family is None or var_resid is None or var_family < 0 or var_resid <= 0:
        fallback_used = True
        var_family, var_resid = _moment_variance_components(df, "family_id", "rating")

    icc = var_family / (var_family + var_resid) if (var_family + var_resid) > 0 else 0.0

    return VarianceComponents(
        model_key=model_key,
        question=question,
        var_family=var_family,
        var_resid=var_resid,
        icc=icc,
        n_families=n_families,
        n_items=n_items,
        n_responses=n_responses,
        convergence_ok=convergence_ok,
        fallback_used=fallback_used,
    )


def pilot_mb_mg_gap(
    results: Sequence[ResultRecord],
    vignettes: Sequence[VignetteRow],
    *,
    question: QuestionType = "intentionality",
    model_key: str,
) -> float:
    """MB mean minus MG mean, on the pilot's ``question``/``model_key``
    subset (signed -- MB is expected to elicit higher intentionality than
    MG for a well-behaved model, but the sign isn't assumed)."""
    df = _join_pilot(results, vignettes, question=question, model_key=model_key)
    mb = df.loc[df["valence"] == "MB", "rating"]
    mg = df.loc[df["valence"] == "MG", "rating"]
    if mb.empty or mg.empty:
        raise ValueError(
            "pilot data must contain both MB and MG rows for this model_key/question "
            "to compute the default effect size (WO-4 §2)"
        )
    return float(mb.mean() - mg.mean())


def default_effect_size(
    results: Sequence[ResultRecord],
    vignettes: Sequence[VignetteRow],
    *,
    question: QuestionType = "intentionality",
    model_key: str,
) -> float:
    """WO-4 §2's stated default: half the pilot's observed |MB-MG| gap."""
    return abs(pilot_mb_mg_gap(results, vignettes, question=question, model_key=model_key)) / 2.0


# ---------------------------------------------------------------------------
# configs/power.yaml
# ---------------------------------------------------------------------------


class PilotSection(KnobeModel):
    question: QuestionType = "intentionality"


class PowerConfig(KnobeModel):
    """``configs/power.yaml``'s schema. See that file's own comments for
    what each field means -- ``effect_sizes[contrast] is None`` means
    "derive from the pilot at simulate-time" (WO-4 §2's stated default)."""

    seed: int
    n_sims: int
    item_counts: list[int]
    response_ns: list[int]
    mu: float = 5.0
    alpha: float = 0.05
    contrasts: list[str]
    effect_sizes: dict[str, float | None] = Field(default_factory=dict)
    pilot: PilotSection = Field(default_factory=PilotSection)


def load_power_config(path: str | Path) -> PowerConfig:
    import yaml

    path = Path(path)
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return PowerConfig(**(data or {}))


# ---------------------------------------------------------------------------
# Simulation grid: checkpointing + resume + shard (WO-4 §3)
# ---------------------------------------------------------------------------


def build_grid_points(contrasts: Sequence[str], item_counts: Sequence[int], response_ns: Sequence[int]) -> list[tuple[str, int, int]]:
    """Deterministic grid-point order: contrast outer, then item_count,
    then response N -- so ``--shard``/resume behave identically across
    runs given the same config."""
    unknown = [c for c in contrasts if c not in CONTRASTS]
    if unknown:
        raise ValueError(f"unknown contrast(s) {unknown}; known contrasts: {sorted(CONTRASTS)}")
    return [(c, ic, n) for c in contrasts for ic in item_counts for n in response_ns]


def _read_existing_grid_keys(path: str | Path) -> set[tuple[str, int, int, int]]:
    path = Path(path)
    if not path.exists() or path.stat().st_size == 0:
        return set()
    rows = read_jsonl(path, PowerGridRow)
    return {(r.contrast, r.item_count, r.n, r.sim_batch) for r in rows}


def simulate_grid(
    *,
    variance_components: VarianceComponents,
    config: PowerConfig,
    out_path: str | Path,
    pilot_default_effect_size: float | None = None,
    seed: int | None = None,
    item_counts: Sequence[int] | None = None,
    response_ns: Sequence[int] | None = None,
    n_sims: int | None = None,
    contrasts: Sequence[str] | None = None,
    shard: tuple[int, int] | None = None,
    limit: int | None = None,
) -> tuple[int, int]:
    """Runs (or resumes) the simulation grid, appending one ``PowerGridRow``
    per newly-completed (contrast, item_count, n) point to ``out_path``.
    Points already present in ``out_path`` are skipped (resume). Returns
    (n_run, n_skipped)."""
    seed = config.seed if seed is None else seed
    item_counts = list(item_counts) if item_counts is not None else list(config.item_counts)
    response_ns = list(response_ns) if response_ns is not None else list(config.response_ns)
    n_sims = config.n_sims if n_sims is None else n_sims
    contrast_list = list(contrasts) if contrasts is not None else list(config.contrasts)

    grid_points = build_grid_points(contrast_list, item_counts, response_ns)
    if shard is not None:
        i, n_shards = shard
        if not (0 <= i < n_shards):
            raise ValueError(f"--shard index must satisfy 0 <= i < n; got {shard}")
        grid_points = [gp for idx, gp in enumerate(grid_points) if idx % n_shards == i]
    if limit is not None:
        grid_points = grid_points[:limit]

    done_keys = _read_existing_grid_keys(out_path)

    n_run = 0
    n_skipped = 0
    out_path = Path(out_path)
    with open(out_path, "a", encoding="utf-8") as fh:
        for contrast, item_count, n in grid_points:
            sim_batch = 0
            key = (contrast, item_count, n, sim_batch)
            if key in done_keys:
                n_skipped += 1
                continue

            configured_es = config.effect_sizes.get(contrast)
            if configured_es is not None:
                effect_size = configured_es
            elif pilot_default_effect_size is not None:
                effect_size = pilot_default_effect_size
            else:
                raise ValueError(
                    f"contrast {contrast!r} has effect_sizes: null in the config and no "
                    f"pilot_default_effect_size was supplied -- pass --pilot-results/"
                    f"--pilot-vignettes so the default (half the pilot MB-MG gap) can be derived."
                )

            params = SimParams(
                mu=config.mu,
                var_family=variance_components.var_family,
                var_resid=variance_components.var_resid,
                effect_size=effect_size,
                alpha=config.alpha,
            )
            stats = run_grid_point(contrast, item_count, n, params, seed, n_sims)
            row = PowerGridRow(
                contrast=contrast,
                item_count=item_count,
                n=n,
                sim_batch=sim_batch,
                n_sims=stats.n_sims,
                n_significant=stats.n_significant,
                n_converged=stats.n_converged,
                n_convergence_failures=stats.n_convergence_failures,
                n_fallback_used=stats.n_fallback_used,
                power=stats.power,
                effect_size=effect_size,
                frac_clipped=stats.frac_clipped,
                seed=seed,
                timestamp=time.time(),
            )
            append_jsonl(row, fh)
            done_keys.add(key)
            n_run += 1

    return n_run, n_skipped


# ---------------------------------------------------------------------------
# Decision report: power_report.md + PNG power curves (WO-4 §4, gate
# artifact for G2)
# ---------------------------------------------------------------------------

GridAgg = dict[str, dict[int, dict[int, dict]]]


def _aggregate_grid(rows: Sequence[PowerGridRow]) -> GridAgg:
    """Sums counts across sim_batch for each (contrast, item_count, n),
    recomputing power from the pooled counts -- so a grid point split
    across multiple checkpointed batches reports one honest power number."""
    agg: GridAgg = {}
    for r in rows:
        by_ic = agg.setdefault(r.contrast, {})
        by_n = by_ic.setdefault(r.item_count, {})
        cell = by_n.setdefault(
            r.n,
            {
                "n_sims": 0, "n_significant": 0, "n_convergence_failures": 0,
                "n_fallback_used": 0, "effect_size": r.effect_size,
            },
        )
        cell["n_sims"] += r.n_sims
        cell["n_significant"] += r.n_significant
        cell["n_convergence_failures"] += r.n_convergence_failures
        cell["n_fallback_used"] += r.n_fallback_used
    for by_ic in agg.values():
        for by_n in by_ic.values():
            for cell in by_n.values():
                cell["power"] = cell["n_significant"] / cell["n_sims"] if cell["n_sims"] else 0.0
    return agg


def _min_point_reaching(by_ic: dict[int, dict[int, dict]], threshold: float) -> tuple[int, int] | None:
    """First (item_count, n) point -- item_count ascending, then n
    ascending -- whose pooled power is >= threshold; None if no grid point
    reaches it."""
    for item_count in sorted(by_ic):
        for n in sorted(by_ic[item_count]):
            if by_ic[item_count][n]["power"] >= threshold:
                return item_count, n
    return None


def _plot_power_curve(contrast: str, by_ic: dict[int, dict[int, dict]], out_dir: Path) -> Path:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover -- exercised only without the 'stats' extra
        raise RuntimeError(
            "matplotlib is required for power curve plots -- install the "
            "'stats' extra (`uv pip install -e '.[stats]'`)."
        ) from exc

    fig, ax = plt.subplots()
    for item_count in sorted(by_ic):
        ns = sorted(by_ic[item_count])
        powers = [by_ic[item_count][n]["power"] for n in ns]
        ax.plot(ns, powers, marker="o", label=f"item_count={item_count}")
    ax.axhline(0.8, color="gray", linestyle="--", linewidth=1)
    ax.axhline(0.9, color="gray", linestyle=":", linewidth=1)
    ax.set_xlabel("response-level N per item")
    ax.set_ylabel("power")
    ax.set_ylim(0, 1.05)
    ax.set_title(f"Power curve -- contrast {contrast}")
    ax.legend(fontsize="small")
    path = out_dir / f"power_curve_{contrast}.png"
    fig.savefig(path)
    plt.close(fig)
    return path


# Caveats that must appear in power_report.md's OWN TEXT, not just in
# docstrings/YAML comments (reviewer finding on the first version of this
# report, task-6-brief.md follow-up): a gate artifact for G2 has to carry
# its own limitations where a reader of the artifact will actually see
# them, not only where a code-reader would.
CAVEAT_1B_NOT_CALIBRATED = (
    "**1b (blame/praise slope difference) is NOT yet calibrated to real blame/praise scales.** "
    "Its power curve is simulated from a fictional standardized predictor (x ~ N(0, 1)) around an "
    "arbitrary base_slope of 0.5, combined with a placeholder effect-size magnitude borrowed from "
    "the other contrasts' pilot-derived MB-MG gap (see `power_sim.simulate_1b`'s docstring) -- it "
    "is not a slope estimated from real pilot blame/praise data. Do not let 1b's numbers in this "
    "report drive family-count decisions until real pilot blame/praise data exists to calibrate "
    "the predictor scale and effect size."
)
CAVEAT_NO_ITEM_VARIANCE = (
    "**No item-in-family variance component is estimated or simulated anywhere in this report.** "
    "Only two variance components are used throughout (family, response-level residual -- WO-4 "
    "§1's per-subject-model simplification, itself required by a statsmodels `MixedLM` limitation, "
    "see `power.py`'s module docstring): item-to-item variation within a family folds into the "
    "residual term instead of getting its own component. Every power number in this report may "
    "therefore be systematically OPTIMISTIC relative to the true design, which has a genuine "
    "item-level source of noise on top of family and residual variance."
)


def generate_report(
    grid_rows: Sequence[PowerGridRow],
    variance_components: Sequence[VarianceComponents],
    out_dir: str | Path,
    thresholds: tuple[float, ...] = DEFAULT_THRESHOLDS,
) -> str:
    """Writes ``power_report.md`` + one PNG power curve per contrast to
    ``out_dir``. Returns the report's markdown text (also what's written to
    disk). This is WO-4's gate artifact for G2 (WO4_pilot_power.md §3):
    states, per contrast, the smallest (item_count, N) grid point reaching
    each power threshold, or that none does and the item count must grow.

    The report carries its own caveats in-line (``CAVEAT_1B_NOT_CALIBRATED``,
    ``CAVEAT_NO_ITEM_VARIANCE``) -- a reader of the artifact itself, not just
    a reader of this module's source, needs to see them before using this
    report to set G2 family counts."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    agg = _aggregate_grid(grid_rows)

    lines = [
        "# WO-4 pilot power decision report",
        "",
        "Gate artifact for G2 (WO4_pilot_power.md §3): states the chosen response-level N "
        "and whether the per-cell item count must grow, at 80%/90% power, per RQ1 "
        "sub-question contrast. `item_count` below is a PER-CELL item target (DR §16), and the "
        "multiplier from item_count to TOTAL families simulated differs by contrast -- see each "
        "contrast's own note below and `power_sim.FAMILY_MULTIPLIER`.",
        "",
        "## Caveats (read before using this report to set G2 family counts)",
        "",
        f"- {CAVEAT_NO_ITEM_VARIANCE}",
        f"- {CAVEAT_1B_NOT_CALIBRATED}",
        "",
        "## Pilot variance components",
        "",
        "| model_key | question | var_family | var_resid | ICC | n_families | n_items | "
        "n_responses | convergence_ok | fallback_used |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for vc in variance_components:
        lines.append(
            f"| {vc.model_key} | {vc.question} | {vc.var_family:.4f} | {vc.var_resid:.4f} | "
            f"{vc.icc:.4f} | {vc.n_families} | {vc.n_items} | {vc.n_responses} | "
            f"{vc.convergence_ok} | {vc.fallback_used} |"
        )
    lines.append("")

    total_sims = sum(r.n_sims for r in grid_rows)
    total_conv_fail = sum(r.n_convergence_failures for r in grid_rows)
    total_fallback = sum(r.n_fallback_used for r in grid_rows)
    lines.append(
        f"Across the whole grid: {total_conv_fail}/{total_sims} simulation replicates failed "
        f"to converge under mixedlm ({total_fallback} used the OLS-cluster-robust fallback to "
        f"still contribute a p-value -- never dropped from the power denominator, per WO-4's "
        f"convergence policy). Per-cell fallback rates are broken out in each contrast's second "
        f"table below."
    )
    lines.append("")

    for contrast in sorted(agg):
        by_ic = agg[contrast]
        all_ns = sorted({n for by_n in by_ic.values() for n in by_n})
        es_values = {cell["effect_size"] for by_n in by_ic.values() for cell in by_n.values()}
        multiplier = FAMILY_MULTIPLIER[contrast]

        lines.append(f"## Contrast {contrast}")
        lines.append("")
        if contrast == "1b":
            lines.append(CAVEAT_1B_NOT_CALIBRATED)
            lines.append("")
        if len(es_values) == 1:
            lines.append(f"Effect size simulated: {next(iter(es_values)):.4f}")
        else:
            lines.append(f"Effect sizes simulated across this grid: {sorted(es_values)}")
        lines.append(
            f"Family multiplier for this contrast: total families simulated per grid point = "
            f"item_count × {multiplier}."
        )
        lines.append("")

        lines.append("Power (fraction of replicates with p < alpha):")
        lines.append("")
        lines.append(
            "| item_count (total families = item_count × "
            f"{multiplier}) \\ N | " + " | ".join(str(n) for n in all_ns) + " |"
        )
        lines.append("|" + "---|" * (len(all_ns) + 1))
        for item_count in sorted(by_ic):
            row_cells = [
                f"{by_ic[item_count][n]['power']:.3f}" if n in by_ic[item_count] else "-"
                for n in all_ns
            ]
            total_families = item_count * multiplier
            lines.append(
                f"| {item_count} ({total_families} families) | " + " | ".join(row_cells) + " |"
            )
        lines.append("")

        lines.append(
            "Fallback rate (share of replicates whose p-value came from the OLS-cluster-robust "
            "fallback because mixedlm didn't converge -- a higher rate here means the power "
            "number above is less reliable):"
        )
        lines.append("")
        lines.append("| item_count \\ N | " + " | ".join(str(n) for n in all_ns) + " |")
        lines.append("|" + "---|" * (len(all_ns) + 1))
        for item_count in sorted(by_ic):
            row_cells = []
            for n in all_ns:
                cell = by_ic[item_count].get(n)
                if cell is None:
                    row_cells.append("-")
                else:
                    fallback_rate = cell["n_fallback_used"] / cell["n_sims"] if cell["n_sims"] else 0.0
                    row_cells.append(f"{fallback_rate:.1%}")
            lines.append(f"| {item_count} | " + " | ".join(row_cells) + " |")
        lines.append("")

        for threshold in thresholds:
            point = _min_point_reaching(by_ic, threshold)
            pct = int(round(threshold * 100))
            if point is None:
                max_power = max(
                    (cell["power"] for by_n in by_ic.values() for cell in by_n.values()), default=0.0,
                )
                max_item_count = max(by_ic) if by_ic else None
                lines.append(
                    f"- **{pct}% power: NOT reached** within the tested grid (max observed power "
                    f"{max_power:.3f} at item_count<={max_item_count}) -- the per-cell item count "
                    f"must grow beyond what was simulated here."
                )
            else:
                item_count, n = point
                total_families = item_count * multiplier
                lines.append(
                    f"- **{pct}% power reached** at item_count={item_count} (per cell; total "
                    f"families = {total_families}), N={n}."
                )
        lines.append("")

        png_path = _plot_power_curve(contrast, by_ic, out_dir)
        lines.append(f"![power curve for {contrast}]({png_path.name})")
        lines.append("")

    text = "\n".join(lines)
    (out_dir / "power_report.md").write_text(text, encoding="utf-8")
    return text


# ---------------------------------------------------------------------------
# CLI-facing orchestration (called by knobe.cli's "power estimate/simulate/report/run")
# ---------------------------------------------------------------------------


def run_estimate(
    results_path: str | Path,
    vignettes_path: str | Path,
    *,
    model_key: str,
    question: QuestionType = "intentionality",
    out_path: str | Path,
) -> int:
    out_path = Path(out_path)
    existing = read_jsonl(out_path, VarianceComponents) if out_path.exists() and out_path.stat().st_size > 0 else []
    if any(e.model_key == model_key and e.question == question for e in existing):
        print(f"model_key={model_key!r} question={question!r} already estimated in {out_path}; skipping (resume).")
        return 0

    results = read_jsonl(results_path, ResultRecord)
    vignettes = read_csv_validated(vignettes_path, VignetteRow)
    vc = estimate_variance_components(results, vignettes, question=question, model_key=model_key)

    with open(out_path, "a", encoding="utf-8") as fh:
        append_jsonl(vc, fh)

    print(
        f"model_key={vc.model_key} question={vc.question}: var_family={vc.var_family:.4f} "
        f"var_resid={vc.var_resid:.4f} icc={vc.icc:.4f} n_families={vc.n_families} "
        f"n_items={vc.n_items} n_responses={vc.n_responses} convergence_ok={vc.convergence_ok} "
        f"fallback_used={vc.fallback_used}"
    )
    return 0


def run_simulate(
    *,
    variance_components_path: str | Path,
    model_key: str,
    config_path: str | Path,
    out_path: str | Path,
    pilot_results_path: str | Path | None = None,
    pilot_vignettes_path: str | Path | None = None,
    seed: int | None = None,
    item_counts: Sequence[int] | None = None,
    response_ns: Sequence[int] | None = None,
    n_sims: int | None = None,
    contrasts: Sequence[str] | None = None,
    shard: tuple[int, int] | None = None,
    limit: int | None = None,
) -> int:
    config = load_power_config(config_path)
    vc_rows = read_jsonl(variance_components_path, VarianceComponents)
    vc = next((v for v in vc_rows if v.model_key == model_key and v.question == config.pilot.question), None)
    if vc is None:
        print(
            f"ERROR: no VarianceComponents for model_key={model_key!r} "
            f"question={config.pilot.question!r} in {variance_components_path} "
            f"-- run `knobe power estimate` first.",
            file=sys.stderr,
        )
        return 1

    contrast_list = list(contrasts) if contrasts is not None else list(config.contrasts)
    needs_default = any(config.effect_sizes.get(c) is None for c in contrast_list)
    pilot_default_es = None
    if needs_default:
        if not pilot_results_path or not pilot_vignettes_path:
            print(
                "ERROR: some contrasts have effect_sizes: null in the config and need "
                "--pilot-results/--pilot-vignettes to derive the default (half the pilot "
                "MB-MG gap).",
                file=sys.stderr,
            )
            return 1
        results = read_jsonl(pilot_results_path, ResultRecord)
        vignettes = read_csv_validated(pilot_vignettes_path, VignetteRow)
        pilot_default_es = default_effect_size(
            results, vignettes, question=config.pilot.question, model_key=model_key
        )

    n_run, n_skipped = simulate_grid(
        variance_components=vc,
        config=config,
        out_path=out_path,
        pilot_default_effect_size=pilot_default_es,
        seed=seed,
        item_counts=item_counts,
        response_ns=response_ns,
        n_sims=n_sims,
        contrasts=contrasts,
        shard=shard,
        limit=limit,
    )
    print(f"Simulated {n_run} grid point(s); skipped {n_skipped} already-completed (resume).")
    return 0


def run_report(
    grid_path: str | Path,
    variance_components_path: str | Path,
    out_dir: str | Path,
) -> int:
    grid_path = Path(grid_path)
    if not grid_path.exists() or grid_path.stat().st_size == 0:
        print(f"ERROR: no grid rows found in {grid_path} -- run `knobe power simulate` first.", file=sys.stderr)
        return 1
    grid_rows = read_jsonl(grid_path, PowerGridRow)

    vc_path = Path(variance_components_path)
    vc_rows = read_jsonl(vc_path, VarianceComponents) if vc_path.exists() and vc_path.stat().st_size > 0 else []

    generate_report(grid_rows, vc_rows, out_dir)
    print(f"Wrote power_report.md + PNG power curves to {out_dir}")
    return 0


def run_pipeline(
    *,
    pilot_results_path: str | Path,
    pilot_vignettes_path: str | Path,
    model_key: str,
    config_path: str | Path,
    variance_components_path: str | Path,
    grid_path: str | Path,
    report_dir: str | Path,
    question: QuestionType | None = None,
    seed: int | None = None,
    item_counts: Sequence[int] | None = None,
    response_ns: Sequence[int] | None = None,
    n_sims: int | None = None,
    contrasts: Sequence[str] | None = None,
    shard: tuple[int, int] | None = None,
    limit: int | None = None,
) -> int:
    """``knobe power run``: estimate -> simulate -> report in one call, for
    convenience (task-6-brief.md CLI item 5: "one command with stages --
    your call, document"). Each stage is independently resumable, so
    re-running this after a partial failure picks up where it left off."""
    config = load_power_config(config_path)
    q = question or config.pilot.question

    rc = run_estimate(
        pilot_results_path, pilot_vignettes_path,
        model_key=model_key, question=q, out_path=variance_components_path,
    )
    if rc != 0:
        return rc

    rc = run_simulate(
        variance_components_path=variance_components_path,
        model_key=model_key,
        config_path=config_path,
        out_path=grid_path,
        pilot_results_path=pilot_results_path,
        pilot_vignettes_path=pilot_vignettes_path,
        seed=seed, item_counts=item_counts, response_ns=response_ns,
        n_sims=n_sims, contrasts=contrasts, shard=shard, limit=limit,
    )
    if rc != 0:
        return rc

    return run_report(grid_path, variance_components_path, report_dir)
