"""Tests for src/knobe/power.py + power_sim.py (WO-4) and the `knobe power`
CLI.

Acceptance criteria under test (WO4_pilot_power.md / task-6-brief.md):
  - Synthetic recovery: estimate_variance_components recovers known
    var_family/var_resid within loose tolerance, seed-pinned.
  - Monotonicity: simulated power is non-decreasing in item_count and in
    response-level N on a small, seed-pinned synthetic grid.
  - Toy end-to-end: the full CLI pipeline (estimate -> simulate -> report)
    on a bundled synthetic pilot fixture completes well under 5 minutes and
    emits power_report.md + PNGs.
  - Resume: completed grid points are skipped on restart, never re-run.
"""
from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pytest

from fixtures.pilot_fixture import MODEL_KEY as FIXTURE_MODEL_KEY
from fixtures.pilot_fixture import make_pilot_fixture
from knobe import constants
from knobe.power import (
    CAVEAT_1B_NOT_CALIBRATED,
    CAVEAT_NO_ITEM_VARIANCE,
    PowerConfig,
    _aggregate_grid,
    _min_point_reaching,
    default_effect_size,
    estimate_variance_components,
    generate_report,
    pilot_mb_mg_gap,
    run_pipeline,
    simulate_grid,
)
from knobe.power_sim import CONTRASTS, FAMILY_MULTIPLIER, SimParams, derive_seed, run_grid_point
from knobe.schemas import PowerGridRow, ResultRecord, VarianceComponents, VignetteRow


# ---------------------------------------------------------------------------
# Fixtures / builders
# ---------------------------------------------------------------------------


def _synthetic_intercept_pilot(
    rng: np.random.Generator,
    n_families: int,
    n_per_family: int,
    mu: float,
    var_family: float,
    var_resid: float,
    valence: str = "MB",
    model_key: str = "toy-instruct",
    question: str = "intentionality",
) -> tuple[list[ResultRecord], list[VignetteRow]]:
    """Builds a pilot results/vignettes pair whose intentionality ratings
    follow EXACTLY the intercept-only DGP (rating = mu + family_effect +
    residual_noise) with known variance components -- the ground truth the
    recovery test checks estimate_variance_components against. One "A"
    variant per family (item count doesn't matter for this test, only the
    family/residual decomposition)."""
    sd_family = np.sqrt(var_family)
    sd_resid = np.sqrt(var_resid)
    sign = constants.SIGN_BY_VALENCE[valence]
    vignette_rows: list[VignetteRow] = []
    result_rows: list[ResultRecord] = []
    for j in range(n_families):
        family_id = f"ENV-{valence}-{j:02d}"
        variant_id = f"{family_id}-A"
        vignette_rows.append(
            VignetteRow(
                variant_id=variant_id, family_id=family_id, domain="Environment", valence=valence,
                sign=sign, typicality="common", evocativeness="low",
                scenario="s", q_intentionality="q", q_blame="q", q_praise="q",
            )
        )
        fam_eff = rng.normal(0.0, sd_family)
        for sample_idx in range(n_per_family):
            rating = mu + fam_eff + rng.normal(0.0, sd_resid)
            prompt_id = f"{variant_id}::{question}::raw"
            result_rows.append(
                ResultRecord(
                    job_id=f"{prompt_id}::{model_key}::{sample_idx}", prompt_id=prompt_id,
                    model_key=model_key, sample_idx=sample_idx, temperature=1.0, seed=sample_idx,
                    raw_response=str(rating), parsed_rating=float(rating), parse_ok=True,
                    parse_method="regex", logprobs_0_10=None, model_revision="x",
                    runner_version="test", timestamp=0.0,
                )
            )
    return result_rows, vignette_rows


def _minimal_power_config(**overrides) -> PowerConfig:
    kwargs = dict(
        seed=999, n_sims=20, item_counts=[3, 5], response_ns=[4, 8], mu=5.0, alpha=0.05,
        contrasts=["1d"], effect_sizes={"1d": 1.0},
    )
    kwargs.update(overrides)
    return PowerConfig(**kwargs)


# ---------------------------------------------------------------------------
# Seeding
# ---------------------------------------------------------------------------


def test_derive_seed_is_deterministic_and_varies_with_every_input():
    base = derive_seed(1, 10, 5, "1a", 0)
    assert base == derive_seed(1, 10, 5, "1a", 0)
    assert base != derive_seed(2, 10, 5, "1a", 0)
    assert base != derive_seed(1, 11, 5, "1a", 0)
    assert base != derive_seed(1, 10, 6, "1a", 0)
    assert base != derive_seed(1, 10, 5, "1b", 0)
    assert base != derive_seed(1, 10, 5, "1a", 1)
    assert 0 <= base < 2**32


# ---------------------------------------------------------------------------
# Synthetic recovery (seed-pinned)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("var_family,var_resid", [(4.0, 1.0), (1.0, 4.0)])
def test_variance_recovery_within_tolerance(var_family, var_resid):
    rng = np.random.default_rng(20260727)
    results, vignettes = _synthetic_intercept_pilot(
        rng, n_families=60, n_per_family=25, mu=5.0,
        var_family=var_family, var_resid=var_resid,
    )
    vc = estimate_variance_components(results, vignettes, question="intentionality", model_key="toy-instruct")

    assert vc.n_families == 60
    assert vc.n_items == 60  # one "A" variant per family
    assert vc.n_responses == 60 * 25
    assert vc.var_family == pytest.approx(var_family, rel=0.30)
    assert vc.var_resid == pytest.approx(var_resid, rel=0.30)
    expected_icc = var_family / (var_family + var_resid)
    assert vc.icc == pytest.approx(expected_icc, rel=0.30)


def test_variance_recovery_missing_model_raises():
    rng = np.random.default_rng(1)
    results, vignettes = _synthetic_intercept_pilot(rng, 10, 5, 5.0, 1.0, 1.0, model_key="toy-instruct")
    with pytest.raises(ValueError, match="no pilot rows"):
        estimate_variance_components(results, vignettes, question="intentionality", model_key="nonexistent-model")


# ---------------------------------------------------------------------------
# Monotonicity (seed-pinned, coarse grid, large-enough sim count)
# ---------------------------------------------------------------------------


def test_power_monotonic_in_item_count_and_response_n():
    params = SimParams(mu=5.0, var_family=1.5, var_resid=4.0, effect_size=0.8, alpha=0.05)
    seed = 123
    n_sims = 300

    power = {}
    for item_count in (10, 30):
        for n in (5, 20):
            stats = run_grid_point("1d", item_count, n, params, seed, n_sims)
            power[(item_count, n)] = stats.power

    tol = 0.05  # MC noise allowance
    assert power[(30, 5)] >= power[(10, 5)] - tol
    assert power[(30, 20)] >= power[(10, 20)] - tol
    assert power[(10, 20)] >= power[(10, 5)] - tol
    assert power[(30, 20)] >= power[(30, 5)] - tol
    # Sanity: the grid spans a genuinely informative power range (not
    # floored/ceilinged everywhere, which would make monotonicity trivial).
    assert min(power.values()) < 0.6
    assert max(power.values()) > 0.75


# ---------------------------------------------------------------------------
# Convergence-failure policy: never silently dropped
# ---------------------------------------------------------------------------


def test_convergence_failures_counted_never_dropped():
    # A deliberately small/noisy grid point where mixedlm sometimes fails
    # to converge (empirically observed at item_count=10, n=5 under these
    # variance components) -- every replicate must still contribute to
    # n_sims and to the significance count via the OLS fallback.
    params = SimParams(mu=5.0, var_family=1.5, var_resid=4.0, effect_size=0.8, alpha=0.05)
    stats = run_grid_point("1d", 10, 5, params, seed=123, n_sims=100)
    assert stats.n_sims == 100
    assert stats.n_significant <= stats.n_sims
    assert stats.n_converged + stats.n_convergence_failures == stats.n_sims
    assert stats.n_convergence_failures > 0  # this grid point is known to produce some
    assert stats.n_fallback_used >= stats.n_convergence_failures


# ---------------------------------------------------------------------------
# Resume: completed grid points skipped on restart
# ---------------------------------------------------------------------------


def test_simulate_grid_resume_skips_completed_points(tmp_path, monkeypatch):
    config = _minimal_power_config(item_counts=[3, 5], response_ns=[4], n_sims=10)
    vc = VarianceComponents(
        model_key="m", question="intentionality", var_family=1.0, var_resid=2.0, icc=0.33,
        n_families=10, n_items=10, n_responses=100, convergence_ok=True,
    )
    out_path = tmp_path / "power_grid.jsonl"

    n_run_1, n_skipped_1 = simulate_grid(variance_components=vc, config=config, out_path=out_path)
    assert n_run_1 == 2  # 2 item_counts x 1 response_n x 1 contrast
    assert n_skipped_1 == 0
    lines_after_first = out_path.read_text(encoding="utf-8").count("\n")
    assert lines_after_first == 2

    calls = []
    import knobe.power as power_module

    real_run_grid_point = power_module.run_grid_point

    def _tracking_run_grid_point(*args, **kwargs):
        calls.append(args[:3])
        return real_run_grid_point(*args, **kwargs)

    monkeypatch.setattr(power_module, "run_grid_point", _tracking_run_grid_point)

    n_run_2, n_skipped_2 = simulate_grid(variance_components=vc, config=config, out_path=out_path)
    assert n_run_2 == 0
    assert n_skipped_2 == 2
    assert calls == []  # the (already-done) grid points must never be re-simulated
    lines_after_second = out_path.read_text(encoding="utf-8").count("\n")
    assert lines_after_second == 2  # no duplicate rows appended


def test_simulate_grid_resume_runs_only_new_points(tmp_path):
    vc = VarianceComponents(
        model_key="m", question="intentionality", var_family=1.0, var_resid=2.0, icc=0.33,
        n_families=10, n_items=10, n_responses=100, convergence_ok=True,
    )
    out_path = tmp_path / "power_grid.jsonl"

    config_a = _minimal_power_config(item_counts=[3], response_ns=[4], n_sims=10)
    simulate_grid(variance_components=vc, config=config_a, out_path=out_path)

    config_b = _minimal_power_config(item_counts=[3, 5], response_ns=[4], n_sims=10)
    n_run, n_skipped = simulate_grid(variance_components=vc, config=config_b, out_path=out_path)
    assert n_run == 1  # only item_count=5 is new
    assert n_skipped == 1

    from knobe.schemas import read_jsonl
    rows = read_jsonl(out_path, PowerGridRow)
    assert sorted(r.item_count for r in rows) == [3, 5]


def test_simulate_grid_shard_covers_full_grid_with_no_overlap(tmp_path):
    vc = VarianceComponents(
        model_key="m", question="intentionality", var_family=1.0, var_resid=2.0, icc=0.33,
        n_families=10, n_items=10, n_responses=100, convergence_ok=True,
    )
    config = _minimal_power_config(item_counts=[3, 5, 7], response_ns=[4, 8], n_sims=10)
    n_shards = 3
    from knobe.schemas import read_jsonl

    all_keys: set[tuple[str, int, int]] = set()
    for i in range(n_shards):
        out_path = tmp_path / f"shard_{i}.jsonl"
        n_run, n_skipped = simulate_grid(
            variance_components=vc, config=config, out_path=out_path, shard=(i, n_shards),
        )
        assert n_skipped == 0
        rows = read_jsonl(out_path, PowerGridRow)
        assert n_run == len(rows)
        shard_keys = {(r.contrast, r.item_count, r.n) for r in rows}
        assert not (shard_keys & all_keys)  # no two shards simulate the same point
        all_keys |= shard_keys

    full_grid = {("1d", ic, n) for ic in config.item_counts for n in config.response_ns}
    assert all_keys == full_grid  # every grid point covered exactly once


def test_run_estimate_resume_skips_already_estimated_model(tmp_path, monkeypatch):
    results_path, vignettes_path = make_pilot_fixture(tmp_path, n_families_per_valence=3, n_samples=3, seed=7)
    out_path = tmp_path / "vc.jsonl"

    from knobe import power as power_module

    n_calls = {"count": 0}
    real_estimate = power_module.estimate_variance_components

    def _counting_estimate(*args, **kwargs):
        n_calls["count"] += 1
        return real_estimate(*args, **kwargs)

    monkeypatch.setattr(power_module, "estimate_variance_components", _counting_estimate)

    rc1 = power_module.run_estimate(
        results_path, vignettes_path, model_key=FIXTURE_MODEL_KEY, question="intentionality", out_path=out_path,
    )
    assert rc1 == 0
    assert n_calls["count"] == 1

    rc2 = power_module.run_estimate(
        results_path, vignettes_path, model_key=FIXTURE_MODEL_KEY, question="intentionality", out_path=out_path,
    )
    assert rc2 == 0
    assert n_calls["count"] == 1  # resume: NOT re-fit

    from knobe.schemas import read_jsonl
    rows = read_jsonl(out_path, VarianceComponents)
    assert len(rows) == 1


# ---------------------------------------------------------------------------
# Pilot effect-size derivation
# ---------------------------------------------------------------------------


def test_default_effect_size_is_half_the_mb_mg_gap(tmp_path):
    results_path, vignettes_path = make_pilot_fixture(tmp_path, n_families_per_valence=3, n_samples=3, seed=7)
    from knobe.schemas import read_csv_validated, read_jsonl

    results = read_jsonl(results_path, ResultRecord)
    vignettes = read_csv_validated(vignettes_path, VignetteRow)

    gap = pilot_mb_mg_gap(results, vignettes, question="intentionality", model_key=FIXTURE_MODEL_KEY)
    es = default_effect_size(results, vignettes, question="intentionality", model_key=FIXTURE_MODEL_KEY)
    assert es == pytest.approx(abs(gap) / 2.0)
    # The fixture's engineered MB mean (7.5) is well above its MG mean
    # (3.5), so the gap should be large and positive.
    assert gap > 1.0


# ---------------------------------------------------------------------------
# Report generation (unit-level, no simulation needed)
# ---------------------------------------------------------------------------


def _grid_row(contrast, item_count, n, power, n_sims=100, **overrides):
    kwargs = dict(
        contrast=contrast, item_count=item_count, n=n, sim_batch=0, n_sims=n_sims,
        n_significant=round(power * n_sims), n_converged=n_sims, n_convergence_failures=0,
        n_fallback_used=0, power=power, effect_size=1.0, frac_clipped=0.0, seed=1, timestamp=0.0,
    )
    kwargs.update(overrides)
    return PowerGridRow(**kwargs)


def test_min_point_reaching_picks_smallest_item_count_then_n():
    rows = [
        _grid_row("1a", 10, 5, 0.5), _grid_row("1a", 10, 20, 0.85),
        _grid_row("1a", 30, 5, 0.95), _grid_row("1a", 30, 20, 0.99),
    ]
    agg = _aggregate_grid(rows)
    assert _min_point_reaching(agg["1a"], 0.8) == (10, 20)
    assert _min_point_reaching(agg["1a"], 0.9) == (30, 5)
    assert _min_point_reaching(agg["1a"], 0.999) is None


def test_family_multiplier_matches_actual_simulator_family_counts(monkeypatch):
    """Reviewer follow-up: a hand-typed-literal equality check on
    FAMILY_MULTIPLIER can't catch it drifting from what the simulators
    actually build if someone edits a simulate_* loop later without
    updating the constant. Instead, monkeypatch power_sim._fit_and_test
    (the single choke point every simulate_* function funnels its built
    DataFrame through, right before fitting) to a stub that just records
    the DataFrame's distinct family_id count and returns a dummy result --
    skipping the real statsmodels fit entirely, since only the DGP's
    family-generation shape is under test here, not its statistics. Runs
    every registered contrast once at a known item_count and asserts the
    captured family count equals item_count * FAMILY_MULTIPLIER[contrast]."""
    import knobe.power_sim as power_sim_module

    # Structural check: FAMILY_MULTIPLIER must cover exactly the same
    # contrasts CONTRASTS does (retained from the original version).
    assert set(FAMILY_MULTIPLIER) == set(CONTRASTS)

    captured: dict[str, int] = {}

    def _stub_fit_and_test(df, formula, groups_col, test_term):
        captured["n_families"] = df[groups_col].nunique()
        return 1.0, True, False  # dummy p-value/converged/fallback -- never inspected

    monkeypatch.setattr(power_sim_module, "_fit_and_test", _stub_fit_and_test)

    item_count = 7
    params = SimParams(mu=5.0, var_family=1.0, var_resid=1.0, effect_size=1.0, alpha=0.05)
    for contrast, sim_fn in CONTRASTS.items():
        captured.clear()
        rng = np.random.default_rng(20260101)
        sim_fn(rng, item_count, 3, params)
        assert "n_families" in captured, f"{contrast}'s simulator never reached _fit_and_test"
        expected = item_count * FAMILY_MULTIPLIER[contrast]
        assert captured["n_families"] == expected, (
            f"{contrast}: simulator built {captured['n_families']} distinct families at "
            f"item_count={item_count}, but FAMILY_MULTIPLIER[{contrast!r}]={FAMILY_MULTIPLIER[contrast]} "
            f"implies {expected} -- FAMILY_MULTIPLIER has drifted from the actual DGP."
        )


def test_generate_report_writes_markdown_and_pngs(tmp_path):
    rows = [
        _grid_row("1a", 10, 5, 0.5), _grid_row("1a", 10, 20, 0.85),
        _grid_row("1a", 30, 5, 0.95), _grid_row("1a", 30, 20, 0.99),
        _grid_row("1b", 10, 5, 0.6),
        _grid_row("1d", 10, 5, 0.3, n_fallback_used=15, n_convergence_failures=15),
        _grid_row("1d", 10, 20, 0.4),
    ]
    vc = [
        VarianceComponents(
            model_key="m", question="intentionality", var_family=1.0, var_resid=2.0, icc=0.33,
            n_families=10, n_items=10, n_responses=100, convergence_ok=True,
        )
    ]
    out_dir = tmp_path / "report"
    text = generate_report(rows, vc, out_dir)

    assert "Contrast 1a" in text
    assert "Contrast 1b" in text
    assert "Contrast 1d" in text
    assert "80% power reached" in text
    assert "90% power reached" in text
    assert "NOT reached" in text  # 1d never hits either threshold in this fixture

    # Reviewer requirement: caveats must appear in the artifact TEXT itself.
    assert CAVEAT_1B_NOT_CALIBRATED in text
    assert CAVEAT_NO_ITEM_VARIANCE in text
    assert "NOT yet calibrated to real blame/praise scales" in text
    assert "systematically OPTIMISTIC" in text

    # Machine-readable family multiplier visible per contrast -- 1a and 1d
    # must show DIFFERENT multipliers so their tables can't be misread as
    # equal-family designs.
    assert "item_count × 4" in text  # 1a: 4 cells/item_count
    assert "item_count × 2" in text  # 1b/1c: 2 cells/item_count
    assert "item_count × 1" in text  # 1d: 1 cell/item_count
    assert "10 (40 families)" in text  # 1a, item_count=10 -> 4x -> 40 families
    assert "10 (10 families)" in text  # 1d, item_count=10 -> 1x -> 10 families

    # Fallback-rate column: a cell with 15/100 fallback replicates must show
    # its correctly-computed, nonzero percentage; a clean cell shows 0%.
    assert "15.0%" in text
    assert "0.0%" in text

    assert (out_dir / "power_report.md").exists()
    assert (out_dir / "power_curve_1a.png").exists()
    assert (out_dir / "power_curve_1b.png").exists()
    assert (out_dir / "power_curve_1d.png").exists()


# ---------------------------------------------------------------------------
# Toy end-to-end: full CLI pipeline on a bundled synthetic pilot fixture
# ---------------------------------------------------------------------------


def test_toy_end_to_end_pipeline_under_five_minutes(tmp_path):
    results_path, vignettes_path = make_pilot_fixture(
        tmp_path / "pilot", n_families_per_valence=3, n_samples=3, seed=7,
    )
    config_path = tmp_path / "power.yaml"
    config_path.write_text(
        "seed: 42\n"
        "n_sims: 50\n"
        "item_counts: [2, 4]\n"
        "response_ns: [3, 5]\n"
        "mu: 5.0\n"
        "alpha: 0.05\n"
        "contrasts: [1a, 1b, 1c_typicality, 1c_evocativeness, 1d]\n"
        "effect_sizes:\n"
        "  1a: null\n"
        "  1b: null\n"
        "  1c_typicality: null\n"
        "  1c_evocativeness: null\n"
        "  1d: null\n"
        "pilot:\n"
        "  question: intentionality\n",
        encoding="utf-8",
    )

    vc_path = tmp_path / "variance_components.jsonl"
    grid_path = tmp_path / "power_grid.jsonl"
    report_dir = tmp_path / "power_report"

    start = time.monotonic()
    rc = run_pipeline(
        pilot_results_path=results_path,
        pilot_vignettes_path=vignettes_path,
        model_key=FIXTURE_MODEL_KEY,
        config_path=config_path,
        variance_components_path=vc_path,
        grid_path=grid_path,
        report_dir=report_dir,
    )
    elapsed = time.monotonic() - start

    assert rc == 0
    assert elapsed < 300, f"toy end-to-end pipeline took {elapsed:.1f}s, must be < 5 min"

    assert vc_path.exists()
    assert grid_path.exists()
    report_path = report_dir / "power_report.md"
    assert report_path.exists()
    report_text = report_path.read_text(encoding="utf-8")
    for contrast in ("1a", "1b", "1c_typicality", "1c_evocativeness", "1d"):
        assert f"Contrast {contrast}" in report_text
        assert (report_dir / f"power_curve_{contrast}.png").exists()
        assert f"item_count × {FAMILY_MULTIPLIER[contrast]}" in report_text

    # Reviewer requirement: the real end-to-end pipeline's report must also
    # carry both caveats in its own text, not just the unit-level report test.
    assert CAVEAT_1B_NOT_CALIBRATED in report_text
    assert CAVEAT_NO_ITEM_VARIANCE in report_text

    # Resume: re-running the pipeline must not re-simulate anything.
    n_lines_before = grid_path.read_text(encoding="utf-8").count("\n")
    rc2 = run_pipeline(
        pilot_results_path=results_path,
        pilot_vignettes_path=vignettes_path,
        model_key=FIXTURE_MODEL_KEY,
        config_path=config_path,
        variance_components_path=vc_path,
        grid_path=grid_path,
        report_dir=report_dir,
    )
    assert rc2 == 0
    n_lines_after = grid_path.read_text(encoding="utf-8").count("\n")
    assert n_lines_after == n_lines_before


# ---------------------------------------------------------------------------
# CLI wiring smoke test
# ---------------------------------------------------------------------------


def test_power_cli_estimate_simulate_report(tmp_path):
    from knobe.cli import main

    results_path, vignettes_path = make_pilot_fixture(
        tmp_path / "pilot", n_families_per_valence=3, n_samples=3, seed=7,
    )
    vc_path = tmp_path / "vc.jsonl"
    grid_path = tmp_path / "grid.jsonl"
    report_dir = tmp_path / "report"

    rc = main([
        "power", "estimate", "--results", str(results_path), "--vignettes", str(vignettes_path),
        "--model-key", FIXTURE_MODEL_KEY, "--question", "intentionality", "--out", str(vc_path),
    ])
    assert rc == 0
    assert vc_path.exists()

    rc = main([
        "power", "simulate", "--variance-components", str(vc_path), "--model-key", FIXTURE_MODEL_KEY,
        "--config", "configs/power.yaml", "--out", str(grid_path),
        "--pilot-results", str(results_path), "--pilot-vignettes", str(vignettes_path),
        "--item-counts", "2,4", "--response-ns", "3,5", "--n-sims", "20", "--contrasts", "1d",
    ])
    assert rc == 0
    assert grid_path.exists()

    rc = main([
        "power", "report", "--grid", str(grid_path), "--variance-components", str(vc_path),
        "--out-dir", str(report_dir),
    ])
    assert rc == 0
    assert (report_dir / "power_report.md").exists()
