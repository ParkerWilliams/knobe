"""WO-8 acceptance tests for src/knobe/analysis/.

Covers: ingest join + never-silent exclusions ledger; contrasts.yaml
governance (undeclared -> hard error); simulation recovery of planted effects;
Holm correction; byte-identical determinism (seeded bootstraps); Type-I rate
(25-sim smoke in the default suite, 200-sim @slow); figures; the ordinal
sensitivity companion; and the G0 end-to-end button-press
(render->jobs->FakeEngine elicit->mock curate->analyze on a 20-item toy).
"""
from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from fixtures.analysis_fixture import (
    make_analysis_data, make_domain_slope_tidy, make_domain_variance_tidy, make_null_tidy,
)
from knobe.analysis import figures, ingest, models
from knobe.analysis.models import (
    UndeclaredContrastError, UndeclaredSensitivityError, _bootstrap_ci, _bootstrap_formula,
    _fit_domain_slope, _fit_lmm,
)
from knobe.analysis.report import DEVIATION_NOTE, run_analyze
from knobe.schemas import ResultRecord, write_jsonl

DEFAULT_CONTRASTS = Path(__file__).resolve().parents[1] / "configs" / "contrasts.yaml"


# ---------------------------------------------------------------------------
# Ingest + exclusions ledger (never silent)
# ---------------------------------------------------------------------------


def test_ingest_joins_and_denormalizes(tmp_path):
    p = make_analysis_data(tmp_path, n_families_per_valence=3, n_samples=3, seed=5)
    df, ledger = ingest.ingest([p["results"]], p["vignettes"], curated_path=p["curated"], release="v1")
    assert not df.empty
    # denormalized fields present + derived
    for col in ("model_family", "tuning_status", "valence_type", "sign", "vividness"):
        assert col in df.columns
    assert set(df["tuning_status"]) == {"pretrained", "finetuned"}
    assert set(df["valence_type"]) == {"moral", "nonmoral", "neutral"}
    assert ledger.n_included == len(df)
    assert ledger.n_excluded == 0


def test_exclusions_never_silent(tmp_path):
    """A parse failure, an unknown variant, and a missing manifest job are all
    counted in the ledger -- never silently dropped."""
    good = ResultRecord(
        job_id="ENV-MB-00-A::intentionality::raw::m-instruct::0",
        prompt_id="ENV-MB-00-A::intentionality::raw", model_key="llama-3.1-8b-instruct",
        sample_idx=0, temperature=1.0, seed=1, raw_response="7", parsed_rating=7,
        parse_ok=True, parse_method="regex", model_revision="x", runner_version="t", timestamp=0.0,
    )
    parse_fail = good.model_copy(update={
        "job_id": "ENV-MB-00-A::intentionality::raw::llama-3.1-8b-instruct::1",
        "raw_response": "no number", "parsed_rating": None, "parse_ok": False,
    })
    unknown_variant = good.model_copy(update={
        "job_id": "ZZZ-MB-99-A::intentionality::raw::llama-3.1-8b-instruct::0",
        "prompt_id": "ZZZ-MB-99-A::intentionality::raw",
    })
    results_path = tmp_path / "results.jsonl"
    write_jsonl([good, parse_fail, unknown_variant], results_path)

    # one released variant so `good` joins
    from knobe.schemas import VignetteRow, write_csv_validated
    vig = VignetteRow(
        variant_id="ENV-MB-00-A", family_id="ENV-MB-00", domain="Environment", valence="MB",
        nonmoral_subdomain="", sign="bad", typicality="common", evocativeness="low",
        scenario="s", q_intentionality="q", q_blame="q", q_praise="q",
    )
    vig_path = tmp_path / "vignettes.csv"
    write_csv_validated([vig], vig_path, VignetteRow)

    df, ledger = ingest.ingest([results_path], vig_path, release="v1")
    reasons = {e.reason: e.count for e in ledger.entries}
    assert reasons.get("parse_failure") == 1
    assert reasons.get("unknown_variant") == 1
    assert ledger.n_included == 1
    assert ledger.n_excluded == 2


def test_logit_fallback_scores_whole_checkpoint_uniformly(tmp_path):
    """Spec §4.4: a checkpoint listed in logit_fallback_checkpoints gets EV
    scoring from logprobs_0_10 for EVERY row (even ones that parsed fine),
    rows without logprobs are excluded as logprobs_missing, and unlisted
    checkpoints keep their parsed ratings."""
    import math

    from knobe.schemas import VignetteRow, write_csv_validated

    vig = VignetteRow(
        variant_id="ENV-MB-00-A", family_id="ENV-MB-00", domain="Environment", valence="MB",
        nonmoral_subdomain="", sign="bad", typicality="common", evocativeness="low",
        scenario="s", q_intentionality="q", q_blame="q", q_praise="q",
    )
    vig_path = tmp_path / "vignettes.csv"
    write_csv_validated([vig], vig_path, VignetteRow)

    # Mass concentrated on rating 8 => EV close to 8, far from parsed 2.
    lp = [-20.0] * 11
    lp[8] = 0.0
    fb_parsed_ok = ResultRecord(
        job_id="ENV-MB-00-A::intentionality::raw::gemma-2-9b-instruct::0",
        prompt_id="ENV-MB-00-A::intentionality::raw", model_key="gemma-2-9b-instruct",
        sample_idx=0, temperature=1.0, seed=1, raw_response="2", parsed_rating=2,
        parse_ok=True, parse_method="regex", logprobs_0_10=lp,
        model_revision="x", runner_version="t", timestamp=0.0,
    )
    fb_parse_fail = fb_parsed_ok.model_copy(update={
        "job_id": "ENV-MB-00-A::intentionality::raw::gemma-2-9b-instruct::1",
        "sample_idx": 1, "raw_response": "no number", "parsed_rating": None, "parse_ok": False,
    })
    fb_no_logprobs = fb_parsed_ok.model_copy(update={
        "job_id": "ENV-MB-00-A::intentionality::raw::gemma-2-9b-instruct::2",
        "sample_idx": 2, "logprobs_0_10": None,
    })
    unlisted = fb_parsed_ok.model_copy(update={
        "job_id": "ENV-MB-00-A::intentionality::raw::llama-3.1-8b-instruct::0",
        "model_key": "llama-3.1-8b-instruct",
    })
    results_path = tmp_path / "results.jsonl"
    write_jsonl([fb_parsed_ok, fb_parse_fail, fb_no_logprobs, unlisted], results_path)

    df, ledger = ingest.ingest(
        [results_path], vig_path, release="v1",
        logit_fallback_checkpoints=["gemma-2-9b-instruct"],
    )
    reasons = {e.reason: e.count for e in ledger.entries}
    assert reasons == {"logprobs_missing": 1}
    assert ledger.n_included == 3

    ev = ingest.logit_ev_rating(lp)
    assert math.isclose(ev, 8.0, abs_tol=1e-6)
    fb_rows = df[df["model_key"] == "gemma-2-9b-instruct"]
    assert set(fb_rows["score_source"]) == {"logit_ev"}
    assert all(math.isclose(r, ev, abs_tol=1e-9) for r in fb_rows["rating"])

    unlisted_rows = df[df["model_key"] == "llama-3.1-8b-instruct"]
    assert set(unlisted_rows["score_source"]) == {"parsed"}
    assert list(unlisted_rows["rating"]) == [2.0]


def test_cancel_format_filtered_with_note(tmp_path):
    """format=='cancel' robustness-stub rows are filtered out of primary
    analyses with a logged reason (WO-8 §4), never silently."""
    from knobe.schemas import VignetteRow, write_csv_validated
    vig = VignetteRow(
        variant_id="ENV-MB-00-A", family_id="ENV-MB-00", domain="Environment", valence="MB",
        nonmoral_subdomain="", sign="bad", typicality="common", evocativeness="low",
        scenario="s", q_intentionality="q", q_blame="q", q_praise="q",
    )
    vig_path = tmp_path / "vignettes.csv"
    write_csv_validated([vig], vig_path, VignetteRow)
    cancel = ResultRecord(
        job_id="ENV-MB-00-A::intentionality::cancel::llama-3.1-8b-instruct::0",
        prompt_id="ENV-MB-00-A::intentionality::cancel", model_key="llama-3.1-8b-instruct",
        sample_idx=0, temperature=1.0, seed=1, raw_response="7", parsed_rating=7,
        parse_ok=True, parse_method="regex", model_revision="x", runner_version="t", timestamp=0.0,
    )
    results_path = tmp_path / "r.jsonl"
    write_jsonl([cancel], results_path)
    df, ledger = ingest.ingest([results_path], vig_path, release="v1")
    assert df.empty
    assert {e.reason for e in ledger.entries} == {"cancel_format_filtered"}


def test_ingest_validates_row_counts_against_jobs_manifest(tmp_path):
    p = make_analysis_data(tmp_path, n_families_per_valence=2, n_samples=2, seed=5)
    # a jobs manifest with one extra job that has no result -> "incomplete".
    from knobe.schemas import JobRecord
    jobs = [JobRecord(
        job_id="PHANTOM::intentionality::raw::llama-3.1-8b-instruct::0",
        prompt_id="PHANTOM::intentionality::raw", model_key="llama-3.1-8b-instruct",
        sample_idx=0, temperature=1.0, seed=1,
    )]
    jobs_path = tmp_path / "jobs.jsonl"
    write_jsonl(jobs, jobs_path)
    _, ledger = ingest.ingest([p["results"]], p["vignettes"], jobs_path=jobs_path, release="v1")
    assert ledger.n_job_rows == 1
    assert ledger.n_missing_results == 1
    # missing manifest jobs are tracked SEPARATELY, not folded into result-row
    # exclusions -- reconciliation must hold (reviewer minor 4).
    assert not any(e.reason == "incomplete" for e in ledger.entries)
    assert ledger.n_included + ledger.n_excluded == ledger.n_result_rows


# ---------------------------------------------------------------------------
# contrasts.yaml governance
# ---------------------------------------------------------------------------


def test_prereg_loads_and_declares_rq1_set():
    prereg = models.load_prereg()
    names = set(prereg.names)
    for expected in ("rq1_base_sign_x_tuning", "rq1a_sign_x_valence_type", "rq1b_moral",
                     "rq1c_typicality_x_sign", "rq1d_neu_offset"):
        assert expected in names
    assert prereg.prereg_frozen is False


def test_undeclared_contrast_hard_errors():
    prereg = models.load_prereg()
    with pytest.raises(UndeclaredContrastError):
        models.select_contrasts(prereg, ["totally_made_up_contrast"])


def test_undeclared_contrast_hard_errors_through_run_analyze(tmp_path):
    p = make_analysis_data(tmp_path, n_families_per_valence=2, n_samples=2, seed=5)
    with pytest.raises(UndeclaredContrastError):
        run_analyze(
            results_paths=[p["results"]], vignettes_path=p["vignettes"],
            out_dir=tmp_path / "out", release="v1", contrast_names=["nope"],
            n_boot=0, make_figures=False,
        )


# ---------------------------------------------------------------------------
# Simulation recovery
# ---------------------------------------------------------------------------


def test_simulation_recovery_of_planted_effects(tmp_path):
    p = make_analysis_data(tmp_path, n_families_per_valence=6, n_samples=6, seed=11)
    df, _ = ingest.ingest([p["results"]], p["vignettes"], curated_path=p["curated"], release="v1")
    prepared = models.prepare_frame(df)
    specs = models.select_contrasts(models.load_prereg(), None)
    records, _ = models.fit_all(prepared, specs, base_seed=1, n_boot=0)
    by_name = {r.contrast: r for r in records}

    # base bad>good gap in finetuned, ~ avg(MORAL_GAP, NONMORAL_GAP) = 2.0
    base = by_name["rq1_base_sign_finetuned"]
    assert base.estimate > 0 and 1.0 < base.estimate < 3.0 and base.direction_ok
    # finetuning-contingency: positive sign x tuning
    assert by_name["rq1_base_sign_x_tuning"].estimate > 0
    assert by_name["rq1_base_sign_x_tuning"].direction_ok
    # 1a moral gap > nonmoral gap -> positive interaction
    assert by_name["rq1a_sign_x_valence_type"].estimate > 0
    assert by_name["rq1a_sign_x_valence_type"].direction_ok
    # 1c dissociation: typicality effect on positive (negative interaction under
    # our coding), evocativeness effect on negative (positive interaction). Both
    # significant after Holm.
    assert by_name["rq1c_typicality_x_sign"].estimate < 0
    assert by_name["rq1c_typicality_x_sign"].p_holm < 0.05
    assert by_name["rq1c_evocativeness_x_sign"].estimate > 0
    assert by_name["rq1c_evocativeness_x_sign"].p_holm < 0.05
    # 1d NEU offset above midpoint
    assert by_name["rq1d_neu_offset"].estimate > 0 and by_name["rq1d_neu_offset"].direction_ok


def test_primary_method_label_is_honest_never_claims_domain_vc(tmp_path):
    """Regression (reviewer Important 1): the primary LMM models family
    clustering ONLY; its method label must say `lmm-familyRI` (or the
    `ols-familyRI` cluster fallback) and NEVER claim a domain variance
    component, which was mathematically inert."""
    p = make_analysis_data(tmp_path, n_families_per_valence=5, n_samples=5, seed=11)
    df, _ = ingest.ingest([p["results"]], p["vignettes"], curated_path=p["curated"], release="v1")
    prepared = models.prepare_frame(df)
    specs = models.select_contrasts(models.load_prereg(), None)
    records, _ = models.fit_all(prepared, specs, base_seed=1, n_boot=0)
    assert records
    for r in records:
        assert "domainVC" not in r.method
        assert r.method in ("lmm-familyRI", "ols-familyRI")
        assert r.ci_method in ("none", "cluster_bootstrap_ols")


def test_domain_sensitivity_runs_and_differs_from_family_fit():
    """Reviewer Important 1(b): the config-gated domain-cluster fit (groups=
    domain) genuinely differs from the family-RI fit on data with real
    domain-level variance -- proving it is NOT the inert vc_formula."""
    df = make_domain_variance_tidy(seed=3)
    fam = _fit_lmm(df, "rating ~ sign_c", "sign_c", groups="family_id")
    dom = _fit_lmm(df, "rating ~ sign_c", "sign_c", groups="domain")
    assert fam.method == "lmm-familyRI"
    assert dom.method == "lmm-domainCluster"
    # domain clustering accounts for between-domain confounding -> materially
    # larger SE for the (between-domain) sign contrast.
    assert dom.se > 1.5 * fam.se


def test_domain_sensitivity_all_populates_on_multidomain_fixture(tmp_path):
    p = make_analysis_data(tmp_path, n_families_per_valence=4, n_samples=4, seed=11)
    df, _ = ingest.ingest([p["results"]], p["vignettes"], release="v1")
    prepared = models.prepare_frame(df)
    specs = models.select_contrasts(models.load_prereg(), None)
    ds = models.domain_sensitivity_all(prepared, specs)
    assert ds  # the synthetic fixture spans 2 domains
    for s in ds:
        assert s.n_domains >= 2
        assert "domain" in s.method or s.method.endswith("Cluster")


# ---------------------------------------------------------------------------
# Declared domain-random-slope sensitivity (researcher decision 2026-07-28)
# ---------------------------------------------------------------------------


def test_prereg_declares_domain_random_slope_sensitivity():
    prereg = models.load_prereg()
    assert "domain_random_slope" in prereg.sensitivity_names
    sa = prereg.sensitivity_by_name("domain_random_slope")
    assert "rq1_base_sign_x_tuning" in sa.contrasts
    assert "rq1a_sign_x_valence_type" in sa.contrasts
    assert "rq1c_typicality_x_sign" in sa.contrasts and "rq1c_evocativeness_x_sign" in sa.contrasts
    assert "ratio > 1.5" in sa.interpretation_rule


def test_undeclared_sensitivity_analysis_hard_errors():
    prereg = models.load_prereg()
    with pytest.raises(UndeclaredSensitivityError):
        models.select_sensitivity_analysis(prereg, "made_up_sensitivity")


def test_domain_slope_fit_runs_on_multidomain_fixture():
    df = make_domain_slope_tidy(5, heterogeneous=True)
    fit = _fit_domain_slope(df, "rating ~ sign_c", "sign_c")
    assert fit.n_domains == 10
    assert fit.slope_variance is not None and fit.slope_variance > 0


def test_domain_slope_qualified_fires_on_heterogeneous_effect():
    """Real between-domain slope heterogeneity -> domain-slope CI materially
    wider than primary + large slope variance -> QUALIFIED per the declared rule."""
    df = make_domain_slope_tidy(5, heterogeneous=True)
    primary = _fit_lmm(df, "rating ~ sign_c", "sign_c", groups="family_id")
    slope = _fit_domain_slope(df, "rating ~ sign_c", "sign_c")
    primary_width = 2 * 1.96 * primary.se
    slope_width = slope.ci_high - slope.ci_low
    ratio = slope_width / primary_width
    assert ratio > models.CI_WIDTH_RATIO_THRESHOLD
    assert slope.slope_variance > models.SLOPE_VAR_THRESHOLD


def test_domain_slope_unqualified_on_homogeneous_effect():
    """Homogeneous effect across domains -> slope variance ~ 0 and CI ratio ~ 1
    -> UNQUALIFIED (non-convergence at the RE boundary must NOT by itself
    qualify)."""
    df = make_domain_slope_tidy(5, heterogeneous=False)
    primary = _fit_lmm(df, "rating ~ sign_c", "sign_c", groups="family_id")
    slope = _fit_domain_slope(df, "rating ~ sign_c", "sign_c")
    primary_width = 2 * 1.96 * primary.se
    slope_width = slope.ci_high - slope.ci_low
    ratio = slope_width / primary_width
    assert ratio <= models.CI_WIDTH_RATIO_THRESHOLD
    assert slope.slope_variance is None or slope.slope_variance <= models.SLOPE_VAR_THRESHOLD


def test_domain_slope_sensitivity_qualified_and_unqualified_verdicts():
    """The full governed path over prepared-frame-shaped data: build one
    het-effect and one homo-effect prepared frame and check the QUALIFIED flag."""
    import pandas as pd

    def _prepared(heterogeneous):
        df = make_domain_slope_tidy(5, heterogeneous=heterogeneous)
        # shape it like an analysis prepared frame for a single contrast fit
        df = df.assign(model_family="mf", format="raw", family_id=df["family_id"])
        return df

    spec = models.ContrastSpec(
        name="rq_x", rq="RQX", kind="lmm", formula="rating ~ sign_c", term="sign_c",
        direction="two-sided", tuning="both", subset={},
    )
    analysis = models.SensitivityAnalysis(name="domain_random_slope", contrasts=("rq_x",), interpretation_rule="r")
    het = models.domain_slope_sensitivity(_prepared(True), [spec], analysis)
    homo = models.domain_slope_sensitivity(_prepared(False), [spec], analysis)
    assert het and het[0].qualified is True
    assert homo and homo[0].qualified is False


# ---------------------------------------------------------------------------
# chat-vs-raw format robustness stub (WO-8 §4)
# ---------------------------------------------------------------------------


def test_chat_comparison_runs_when_chat_rows_present(tmp_path):
    p = make_analysis_data(tmp_path, n_families_per_valence=4, n_samples=4, seed=11, include_chat=True)
    df, _ = ingest.ingest([p["results"]], p["vignettes"], release="v1")
    prepared = models.prepare_frame(df)
    specs = models.select_contrasts(models.load_prereg(), None)
    rows, had_chat = models.chat_format_comparison(prepared, specs)
    assert had_chat is True
    assert rows
    r = rows[0]
    assert r.raw_estimate == r.raw_estimate  # not NaN
    assert r.chat_estimate == r.chat_estimate


def test_chat_comparison_skipped_when_no_chat_rows(tmp_path):
    p = make_analysis_data(tmp_path, n_families_per_valence=3, n_samples=3, seed=5)  # raw only
    df, _ = ingest.ingest([p["results"]], p["vignettes"], release="v1")
    prepared = models.prepare_frame(df)
    specs = models.select_contrasts(models.load_prereg(), None)
    rows, had_chat = models.chat_format_comparison(prepared, specs)
    assert had_chat is False
    assert rows == []


def test_primary_fits_ignore_chat_rows(tmp_path):
    """Primary fits use the raw format only (spec §3.4); the SAME raw rows must
    produce the SAME primary estimates whether or not chat rows sit alongside
    them (a raw-only file filtered from the with-chat file, so the raw data is
    literally identical)."""
    from knobe.schemas import read_jsonl as _read

    p = make_analysis_data(tmp_path, n_families_per_valence=4, n_samples=4, seed=11, include_chat=True)
    all_results = _read(p["results"], ResultRecord)
    raw_only = [r for r in all_results if r.prompt_id.endswith("::raw")]
    raw_path = tmp_path / "results_raw_only.jsonl"
    write_jsonl(raw_only, raw_path)
    specs = models.select_contrasts(models.load_prereg(), None)

    def _estimates(results_path):
        df, _ = ingest.ingest([results_path], p["vignettes"], release="v1")
        recs, _ = models.fit_all(models.prepare_frame(df), specs, base_seed=1, n_boot=0)
        return {r.contrast: round(r.estimate, 8) for r in recs}

    assert _estimates(p["results"]) == _estimates(raw_path)


def test_run_analyze_domain_and_chat_sections(tmp_path):
    p = make_analysis_data(
        tmp_path, n_families_per_valence=6, n_samples=4, seed=11, include_chat=True, n_domains=8,
    )
    out = tmp_path / "paper"
    run_analyze(
        results_paths=[p["results"]], vignettes_path=p["vignettes"], curated_path=p["curated"],
        out_dir=out, release="v1", n_boot=0, make_figures=False,
        domain_sensitivity=True, domain_slope_sensitivity=True, chat_comparison=True,
    )
    assert (out / "domain_sensitivity.csv").exists()
    assert (out / "domain_slope_sensitivity.csv").exists()
    assert (out / "chat_comparison.csv").exists()
    summary = (out / "summary.md").read_text()
    assert "Domain clustering is NOT modeled" in summary
    assert "Domain-cluster sensitivity" in summary
    assert "Domain-random-slope sensitivity" in summary
    assert "ratio > 1.5" in summary  # declared interpretation rule surfaced verbatim
    assert "Chat-vs-raw format robustness" in summary
    # exclusions reconciliation stated as separate sentences
    assert "included + excluded" in summary
    # the declared slope analysis produced rows for the headline contrasts
    slope_csv = (out / "domain_slope_sensitivity.csv").read_text()
    assert "rq1_base_sign_x_tuning" in slope_csv


def test_run_analyze_undeclared_slope_governance(monkeypatch, tmp_path):
    """A contrasts.yaml with no sensitivity_analyses section -> requesting the
    slope analysis hard-errors (governance)."""
    p = make_analysis_data(tmp_path, n_families_per_valence=3, n_samples=3, seed=5, n_domains=4)
    bare = tmp_path / "bare_contrasts.yaml"
    full = models.default_contrasts_path().read_text()
    # strip the sensitivity_analyses section
    bare.write_text(full.split("sensitivity_analyses:")[0], encoding="utf-8")
    with pytest.raises(UndeclaredSensitivityError):
        run_analyze(
            results_paths=[p["results"]], vignettes_path=p["vignettes"], out_dir=tmp_path / "o",
            release="v1", contrasts_path=bare, n_boot=0, make_figures=False,
            domain_slope_sensitivity=True,
        )


def test_holm_correction_within_family_is_monotone(tmp_path):
    p = make_analysis_data(tmp_path, n_families_per_valence=4, n_samples=4, seed=3)
    df, _ = ingest.ingest([p["results"]], p["vignettes"], release="v1")
    prepared = models.prepare_frame(df)
    specs = models.select_contrasts(models.load_prereg(), None)
    records, _ = models.fit_all(prepared, specs, base_seed=1, n_boot=0)
    for r in records:
        assert r.p_holm >= r.p_value - 1e-12  # Holm never decreases a p-value


# ---------------------------------------------------------------------------
# Determinism (seeded bootstraps)
# ---------------------------------------------------------------------------


def test_round_trip_determinism_byte_identical(tmp_path):
    p = make_analysis_data(tmp_path, n_families_per_valence=4, n_samples=4, seed=11)
    o1, o2 = tmp_path / "o1", tmp_path / "o2"
    for out in (o1, o2):
        run_analyze(
            results_paths=[p["results"]], vignettes_path=p["vignettes"],
            curated_path=p["curated"], out_dir=out, release="v1",
            base_seed=7, n_boot=25, make_figures=False,
        )
    a = (o1 / "contrast_table.csv").read_bytes()
    b = (o2 / "contrast_table.csv").read_bytes()
    assert a == b
    # bootstrap CIs actually populated (seeded bootstraps ran)
    assert b"," in a and a.count(b"\n") > 5


# ---------------------------------------------------------------------------
# Type-I rate (25-sim smoke in the default suite; 200-sim @slow)
# ---------------------------------------------------------------------------

_PRIMARY_FORMULA = "rating ~ sign_c*vt_c"
_PRIMARY_TERM = "sign_c:vt_c"


def _typeI_rate(n_sims: int, base_seed: int = 2026) -> float:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        rej = sum(
            1 for i in range(n_sims)
            if _fit_lmm(make_null_tidy(base_seed, i), _PRIMARY_FORMULA, _PRIMARY_TERM).p_value < 0.05
        )
    return rej / n_sims


def test_type_i_smoke_25_sims():
    """Coarse gross-miscalibration guard in the default suite. 25 sims have wide
    sampling variance, so the tight nominal-rate check is the @slow 200-sim test
    below; here we only assert the primary contrast is not wildly anti-
    conservative under the null."""
    assert _typeI_rate(25) <= 0.28


@pytest.mark.slow
def test_type_i_rate_200_sims_is_nominal():
    """WO-8 acceptance: empirical rejection rate on null-generated data is in
    [0.01, 0.10] at alpha=.05 across >=200 sims of the primary contrast."""
    assert 0.01 <= _typeI_rate(200) <= 0.10


# ---------------------------------------------------------------------------
# Figures + ordinal sensitivity + full report artifacts
# ---------------------------------------------------------------------------


def test_figures_generated(tmp_path):
    p = make_analysis_data(tmp_path, n_families_per_valence=3, n_samples=3, seed=5)
    df, _ = ingest.ingest([p["results"]], p["vignettes"], release="v1")
    paths = figures.generate_all(df, tmp_path / "figs")
    assert len(paths) >= 2
    for path in paths:
        assert path.exists() and path.stat().st_size > 0


def test_run_analyze_writes_all_artifacts_with_deviation_note(tmp_path):
    p = make_analysis_data(tmp_path, n_families_per_valence=4, n_samples=4, seed=9)
    out = tmp_path / "paper"
    rc = run_analyze(
        results_paths=[p["results"]], vignettes_path=p["vignettes"],
        curated_path=p["curated"], out_dir=out, release="v1", n_boot=10,
    )
    assert rc == 0
    for artifact in ("contrast_table.csv", "ordinal_sensitivity.csv", "summary.md", "exclusions.json"):
        assert (out / artifact).exists()
    summary = (out / "summary.md").read_text()
    # the LMM-primary deviation note appears in the REPORT text, not just docstrings
    assert "LMM-primary" in summary
    assert DEVIATION_NOTE.split(".")[0] in summary
    assert (out / "figures").is_dir()


# ---------------------------------------------------------------------------
# G0 end-to-end: render -> jobs -> FakeEngine elicit -> mock curate -> analyze
# ---------------------------------------------------------------------------


def test_g0_end_to_end_button_press(tmp_path):
    """Build a 20-item toy through the REAL pipeline stages with no
    modification and analyze it -- the button-press proof (WO-8 acceptance)."""
    from knobe import curate, elicit_vllm
    from knobe.jobs import build_jobs, write_jobs_jsonl
    from knobe.render import run as render_run
    from knobe.schemas import PromptRecord, VignetteRow, read_jsonl, write_csv_validated
    from knobe import constants

    # 5 families (one per valence) x 4 variants = 20 items.
    vig_rows = []
    for i, valence in enumerate(["MB", "MG", "NMB", "NMG", "NEU"]):
        sign = constants.SIGN_BY_VALENCE[valence]
        sub = "prudential" if valence in constants.NONMORAL_VALENCES else ""
        fid = f"ENV-{valence}-0{i}"
        for (typ, evoc), letter in constants.VARIANT_LETTER.items():
            vig_rows.append(VignetteRow(
                variant_id=f"{fid}-{letter}", family_id=fid, domain="Environment",
                valence=valence, nonmoral_subdomain=sub, sign=sign, typicality=typ,
                evocativeness=evoc, scenario=f"Toy scenario {fid}-{letter}.",
                q_intentionality="Did they intentionally do it, 0 to 10?",
                q_blame="How blameworthy, 0 to 10?", q_praise="How praiseworthy, 0 to 10?",
            ))
    vig_path = tmp_path / "vignettes.csv"
    write_csv_validated(vig_rows, vig_path, VignetteRow)

    # render -> prompts.jsonl (raw only)
    prompts_path = tmp_path / "prompts.jsonl"
    assert render_run(vig_path, prompts_path, formats=("raw",)) == 0

    # jobs.jsonl
    prompts = read_jsonl(prompts_path, PromptRecord)
    model_keys = ["llama-3.1-8b-pretrained", "llama-3.1-8b-instruct"]
    jobs = build_jobs(
        prompts, release="v0-toy", models=model_keys, formats=["raw"],
        questions=["intentionality", "blame", "praise"], n_samples=2,
    )
    jobs_path = tmp_path / "jobs.jsonl"
    write_jobs_jsonl(jobs, jobs_path)

    # FakeEngine elicit -> results.jsonl
    run_config = tmp_path / "run.yaml"
    run_config.write_text(
        "release: v0-toy\nmodels: [llama-3.1-8b-pretrained, llama-3.1-8b-instruct]\n"
        "formats: [raw]\nn_samples: 2\n", encoding="utf-8",
    )
    results_path = tmp_path / "results.jsonl"
    rc = elicit_vllm.run_elicit(
        jobs_path=jobs_path, prompts_path=prompts_path, run_config_path=run_config,
        out_path=results_path, engine_name="fake", skip_manifest_check=True,
        install_signal_handlers=False,
    )
    assert rc == 0 and results_path.exists()

    # mock curate -> curated.csv (+ accept)
    curated_path = tmp_path / "curated.csv"
    assert curate.run(
        vig_path, reviewer_model="mock-reviewer", mock=True, out=curated_path,
        raw_out=tmp_path / "curated_raw.jsonl", report_dir=tmp_path / "curation_reports",
        curation_date="2026-07-27",
    ) == 0
    curate.review_curated(curated_path, accept_unflagged=True)

    # analyze (button-press) -- runs the whole S8 pipeline unmodified
    out = tmp_path / "paper"
    rc = run_analyze(
        results_paths=[results_path], vignettes_path=vig_path, curated_path=curated_path,
        jobs_path=jobs_path, out_dir=out, release="v0-toy", n_boot=0,
    )
    assert rc == 0
    assert (out / "contrast_table.csv").exists()
    assert (out / "summary.md").exists()
    assert (out / "exclusions.json").exists()


# ---------------------------------------------------------------------------
# 1b item-level pairing construction
# ---------------------------------------------------------------------------


def test_1b_frame_uses_item_level_pairing(tmp_path):
    p = make_analysis_data(tmp_path, n_families_per_valence=4, n_samples=4, seed=7)
    df, _ = ingest.ingest([p["results"]], p["vignettes"], release="v1")
    prepared = models.prepare_frame(df)
    ft = prepared[prepared["tuning_status"] == "finetuned"]
    frame = models.prepare_1b_frame(ft, "moral")
    # outcome rows are intentionality responses; predictor is the item mean.
    assert set(frame["question_type"]) == {"intentionality"}
    assert "pred_c" in frame.columns and "sg_c" in frame.columns
    assert len(frame) > len(frame["variant_id"].unique())  # response-level, not item-level


def _make_1b_family_confound_frame(seed: int = 0, n_fam_per_sign: int = 15, n_variants: int = 6) -> pd.DataFrame:
    """A ``prepared``-shaped frame where an item's blame/praise mean (the 1b
    predictor) is driven mostly by a FAMILY-level confound that also shifts
    that family's sign (mirrors the real v1.1 finding: pred_c correlates
    0.77-0.96 with its own family mean, plausibly via the same severity/
    valence-intensity confound documented for RQ1a). A smaller, independent
    WITHIN-family component drives the true pred_c:sg_c effect. Plain pooled
    OLS conflates the two; family fixed effects (or the family-RI LMM)
    don't."""
    rng = np.random.default_rng(seed)
    rows: list[dict] = []
    for sign, sg_c, level_mean in (("bad", 0.5, 2.0), ("good", -0.5, -2.0)):
        for i in range(n_fam_per_sign):
            family_id = f"{sign}-{i:03d}"
            family_level = rng.normal(level_mean, 1.0)  # confound, correlated with sg_c
            for v in range(n_variants):
                variant_id = f"{family_id}-{v}"
                variant_within = rng.normal(0.0, 1.0)  # true within-family driver
                pred_raw = family_level + variant_within + rng.normal(0.0, 0.2)
                rating = 5.0 + 1.5 * family_level + 2.0 * sg_c * variant_within + rng.normal(0.0, 0.5)
                channel = "blame" if sign == "bad" else "praise"
                rows.append(dict(
                    model_family="test", tuning_status="finetuned", format="raw",
                    valence_type="moral", sign=sign, question_type=channel,
                    variant_id=variant_id, family_id=family_id, rating=float(pred_raw),
                ))
                rows.append(dict(
                    model_family="test", tuning_status="finetuned", format="raw",
                    valence_type="moral", sign=sign, question_type="intentionality",
                    variant_id=variant_id, family_id=family_id, rating=float(rating),
                ))
    return pd.DataFrame(rows)


def test_1b_bootstrap_ci_biased_by_pooled_ols_under_family_confound():
    """Documents the bug this fixture exists to catch: refitting the 1b
    bootstrap with plain pooled OLS (pred_c's family-confound in play) gives a
    CI that does NOT bracket the primary LMM's own point estimate -- exactly
    the pathology found on real v1.1 data for rq1b_moral/llama and
    rq1b_nonmoral/mistral (docs/RQ1_STATISTICAL_METHODS_v1.1.md §4)."""
    prepared = _make_1b_family_confound_frame()
    spec = next(s for s in models.load_prereg().contrasts if s.name == "rq1b_moral")
    frame = models.prepare_1b_frame(prepared[prepared["tuning_status"] == "finetuned"], "moral")
    fit = _fit_lmm(frame, spec.formula, spec.term)

    old_ci = _bootstrap_ci(
        frame, "rating ~ pred_c * sg_c", spec.term,
        base_seed=0, contrast="test", model_family="test", n_boot=300,
    )
    assert old_ci[0] is not None
    assert not (old_ci[0] <= fit.estimate <= old_ci[1]), (
        "expected the unfixed pooled-OLS bootstrap to fail to bracket the LMM "
        "estimate under this family confound -- if this now passes, the "
        "synthetic confound needs strengthening, not the assertion removing."
    )


def test_1b_bootstrap_ci_family_fe_fix_brackets_estimate():
    """The actual regression test for the fix: fit_contrast's family-FE
    bootstrap formula (_bootstrap_formula) gives a CI that DOES bracket the
    primary LMM's point estimate under the same family confound that breaks
    plain pooled OLS above."""
    prepared = _make_1b_family_confound_frame()
    spec = next(s for s in models.load_prereg().contrasts if s.name == "rq1b_moral")
    frame = models.prepare_1b_frame(prepared[prepared["tuning_status"] == "finetuned"], "moral")
    fit = _fit_lmm(frame, spec.formula, spec.term)

    new_ci = _bootstrap_ci(
        frame, _bootstrap_formula(spec), spec.term,
        base_seed=0, contrast="test", model_family="test", n_boot=300,
    )
    assert new_ci[0] is not None
    assert new_ci[0] <= fit.estimate <= new_ci[1]

    # and the full fit_contrast path agrees end to end
    record, _ = models.fit_contrast(prepared, spec, "test", base_seed=0, n_boot=300)
    assert record is not None
    assert record.ci_low <= record.estimate <= record.ci_high


def test_bootstrap_formula_rejects_unexpected_1b_shape():
    """_bootstrap_formula's family-FE string rewrite is a targeted patch on
    the exact 'pred_c * sg_c' shape every lmm_1b contrast uses today; if that
    ever changes, this should hard-error rather than silently skip the fix."""
    import dataclasses

    spec = next(s for s in models.load_prereg().contrasts if s.name == "rq1b_moral")
    bad_spec = dataclasses.replace(spec, formula="rating ~ pred_c + sg_c")  # no "*" shape
    with pytest.raises(ValueError):
        _bootstrap_formula(bad_spec)
