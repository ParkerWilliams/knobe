"""Tests for src/knobe/mech/probes.py + decompose.py (WO-7): per-layer linear
probes with scaffold-split leakage control + residualization (RQ2), patch
decomposition (RQ3), probe alignment (RQ4), and the Gemma Scope stub.

All GPU-free: probes/decompose operate on synthetic caches and hand-built
metrics; the acceptance tests plant known signals so recovery, dissociation,
confound-removal, and null behaviour are exactly checkable.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from knobe import constants
from knobe.mech import decompose, probes
from knobe.mech._data import (
    CONSTRUCT_SPECS,
    ProbeDataset,
    all_specs,
    assemble_items,
    scaffold_key,
)
from knobe.mech.probes import (
    ScaffoldLeakageError,
    build_family_split,
    construct_curve,
    peak_layer,
)
from knobe.schemas import (
    CuratedRow,
    PatchInfo,
    PatchRecord,
    ResultRecord,
    VignetteRow,
    write_csv_validated,
    write_jsonl,
)

VALENCES = ["MB", "MG", "NMB", "NMG", "NEU"]
_SUBDOMAIN = {"NMB": "prudential", "NMG": "prudential"}
DOMAIN_NAME = {"AA": "Alpha", "BB": "Beta"}
N_LAYERS = 8
D_MODEL = 32


# ---------------------------------------------------------------------------
# Fixture builders: vignettes/curated with realistic shared-scaffold scenarios
# so the leakage detector has real storyline stems to check.
# ---------------------------------------------------------------------------


def _scenario(agent: str, action: str, goal: str, affected: str, outcome: str) -> str:
    return (
        f"{agent} {action} to {goal}. {agent} did not care about the outcome for "
        f"{affected}. {agent} knew this would {outcome}."
    )


def build_vignettes(
    domains=("AA", "BB"), n_sets=6, *, shuffle_scaffolds=False
) -> list[VignetteRow]:
    """5 valence families per (domain, set); 4 variants each. Families in a
    set share a storyline stem (agent/action/goal) → a long common scenario
    prefix. ``shuffle_scaffolds`` instead ties the stem to the VALENCE, so a
    (domain, set) scaffold ends up mixing 5 different stems (the leakage
    corruption the split builder must catch)."""
    rows: list[VignetteRow] = []
    for d in domains:
        for s in range(1, n_sets + 1):
            for vi, valence in enumerate(VALENCES):
                stem_key = (d, vi) if shuffle_scaffolds else (d, s)
                agent = f"The {d}manager{stem_key[1]}"
                goal = f"reduce the {d}operating costs variant {stem_key[1]}"
                common_action = f"switched the {d}process number {stem_key[1]}"
                uncommon_action = f"commissioned a custom {d}process number {stem_key[1]}"
                family_id = f"{d}-{valence}-{s:02d}"
                for (typ, evoc), letter in constants.VARIANT_LETTER.items():
                    action = common_action if typ == "common" else uncommon_action
                    affected = f"the {valence} affected entity of set {s}"
                    outcome = f"{'strongly' if evoc == 'high' else 'slightly'} affect {valence} outcome {s}"
                    rows.append(
                        VignetteRow(
                            variant_id=f"{family_id}-{letter}",
                            family_id=family_id,
                            domain=DOMAIN_NAME[d],
                            valence=valence,
                            nonmoral_subdomain=_SUBDOMAIN.get(valence, ""),
                            sign=constants.SIGN_BY_VALENCE[valence],
                            typicality=typ,
                            evocativeness=evoc,
                            scenario=_scenario(agent, action, goal, affected, outcome),
                            q_intentionality="Did they do it intentionally, 0 to 10?",
                            q_blame="How blameworthy, 0 to 10?",
                            q_praise="How praiseworthy, 0 to 10?",
                        )
                    )
    return rows


def _prompt_ids(vignettes) -> list[str]:
    return [f"{v.variant_id}::intentionality::raw" for v in vignettes]


def build_curated(vignettes, severity, vividness, typ_perc) -> list[CuratedRow]:
    """CuratedRow per variant with the given per-item ratings (row-aligned to
    ``vignettes``)."""
    out = []
    for v, sev, viv, tp in zip(vignettes, severity, vividness, typ_perc):
        out.append(
            CuratedRow(
                **v.model_dump(),
                moral_relevance=5,
                severity=int(sev),
                vividness=int(viv),
                typicality_perception=int(tp),
                reviewer_model="reviewer/mock",
                curation_date="2026-07-27",
                accepted=True,
            )
        )
    return out


def _rng(seed=0):
    return np.random.default_rng(seed)


def _orthonormal_dirs(k, d, seed):
    m = _rng(seed).standard_normal((k, d))
    q, _ = np.linalg.qr(m.T)
    return [q[:, i] for i in range(k)]


# ---------------------------------------------------------------------------
# Split builder: scaffold grouping + leakage detection.
# ---------------------------------------------------------------------------


def test_scaffold_key_drops_valence_segment():
    assert scaffold_key("ENV-MB-01") == "ENV-01"
    assert scaffold_key("ENV-NMG-12") == "ENV-12"
    assert scaffold_key("AA-NEU-06") == "AA-06"


def test_split_groups_whole_scaffolds_no_straddle():
    vignettes = build_vignettes()
    split = build_family_split(vignettes, test_frac=0.25, seed=1)
    train_scaffolds = {scaffold_key(f) for f in split.train}
    test_scaffolds = {scaffold_key(f) for f in split.test}
    # No scaffold appears on both sides.
    assert train_scaffolds.isdisjoint(test_scaffolds)
    # Every scaffold's 5 valence families land wholly on one side.
    by_scaffold: dict[str, set[str]] = {}
    for f in split.train + split.test:
        by_scaffold.setdefault(scaffold_key(f), set()).add(f)
    for scaffold, fams in by_scaffold.items():
        assert len(fams) == 5  # MB/MG/NMB/NMG/NEU together
        side_train = all(f in split.train for f in fams)
        side_test = all(f in split.test for f in fams)
        assert side_train or side_test
    # Stratified: each domain contributes to test.
    assert {s.split("-")[0] for s in test_scaffolds} == {"AA", "BB"}


def test_split_leakage_shuffled_family_ids_raises():
    shuffled = build_vignettes(shuffle_scaffolds=True)
    with pytest.raises(ScaffoldLeakageError, match="inconsistent storyline stem|leakage"):
        build_family_split(shuffled, test_frac=0.25, seed=1)
    # ...and the clean dataset does NOT raise (the detector discriminates).
    build_family_split(build_vignettes(), test_frac=0.25, seed=1)


def test_split_is_deterministic_in_seed():
    v = build_vignettes()
    a = build_family_split(v, seed=7)
    b = build_family_split(v, seed=7)
    assert a.train == b.train and a.test == b.test


# -- structural validator against REAL assembled output ----------------------

_REAL_MATRIX = Path(
    "/Users/prwilliams/Documents/Knobe/repotentialexperiments/ALL_DOMAINS_master_matrix.csv"
)


def _real_vignettes(n_sets=3):
    """Assemble a few REAL master-matrix sets into VignetteRows (skips if the
    read-only matrix isn't mounted)."""
    if not _REAL_MATRIX.exists():
        pytest.skip("real master matrix not available in this environment")
    from knobe import assemble

    rows = assemble.assemble(assemble.load_families(_REAL_MATRIX))
    vigs = [VignetteRow(**r) for r in rows]
    keep_scaffolds, kept = [], []
    for v in vigs:
        sk = scaffold_key(v.family_id)
        if sk not in keep_scaffolds:
            if len(keep_scaffolds) >= n_sets:
                continue
            keep_scaffolds.append(sk)
        if sk in keep_scaffolds:
            kept.append(v)
    return kept


def test_scaffold_validator_passes_on_real_assembled_output():
    vigs = _real_vignettes(n_sets=3)
    # Structural validator accepts genuine assembled scaffolds (5 valence
    # families sharing agent/goal/actions, differing only in affected/outcome).
    build_family_split(vigs, test_frac=0.34, seed=0)  # no raise
    probes.validate_scaffold_consistency(probes._vignettes_frame(vigs))


def test_scaffold_validator_raises_on_corrupted_real_scaffold():
    vigs = _real_vignettes(n_sets=2)
    df = probes._vignettes_frame(vigs)
    # Corrupt ONE family's scenario in a scaffold to a different agent/goal
    # (as if a family from another storyline were shuffled in).
    target_scaffold = df["scaffold"].iloc[0]
    idx = df[df["scaffold"] == target_scaffold].index[0]
    df.loc[idx, "scenario"] = (
        "The impostor supervisor rewired the grid to cut a corner. The impostor "
        "supervisor did not care at all about the effect this would have on the town. "
        "The impostor supervisor knew that this would harm someone: a bad thing happened."
    )
    with pytest.raises(ScaffoldLeakageError, match="shared scaffold slots|shared agent"):
        probes.validate_scaffold_consistency(df)


# ---------------------------------------------------------------------------
# Synthetic recovery + dissociation + confound removal (the RQ2 acceptance
# test). Plant: sign signal @ layer 2 (classification), severity @ layer 4 and
# vividness @ layer 6 (ridge), with severity/vividness CORRELATED across items
# so severity's RAW probe leaks vividness's signal at layer 6 and
# residualization must remove it.
# ---------------------------------------------------------------------------

SIGN_LAYER = 2
SEV_LAYER = 4
VIV_LAYER = 6


def _planted_dataset(seed=0):
    vignettes = build_vignettes()
    n = len(vignettes)
    rng = _rng(seed)

    # Correlated severity/vividness latents (shared g) with a substantial
    # UNIQUE component each: enough shared variance that severity's RAW probe
    # leaks vividness's signal, enough unique variance that residualized
    # severity still localizes at its own planted layer.
    g = rng.standard_normal(n)
    sev_latent = g + 0.7 * rng.standard_normal(n)
    viv_latent = g + 0.7 * rng.standard_normal(n)

    def to_int_0_10(x):
        z = (x - x.mean()) / x.std()
        return np.clip(np.round(5 + 2 * z), 0, 10).astype(int)

    severity = to_int_0_10(sev_latent)
    vividness = to_int_0_10(viv_latent)
    typ_perc = to_int_0_10(rng.standard_normal(n))
    curated = build_curated(vignettes, severity, vividness, typ_perc)

    items, _, _ = assemble_items(_prompt_ids(vignettes), vignettes, curated)

    # Standardized targets drive the planted directions (clean linear signal).
    def std(v):
        v = v.astype(float)
        return (v - v.mean()) / v.std()

    sign_pm1 = items["sign_num"].to_numpy()  # +1 bad, -1 good, 0 NEU
    u_sign, u_sev, u_viv = _orthonormal_dirs(3, D_MODEL, seed + 100)

    resid = 0.02 * rng.standard_normal((n, N_LAYERS + 1, D_MODEL))
    resid[:, SIGN_LAYER, :] += 6.0 * sign_pm1[:, None] * u_sign[None, :]
    resid[:, SEV_LAYER, :] += std(severity)[:, None] * u_sev[None, :]
    resid[:, VIV_LAYER, :] += std(vividness)[:, None] * u_viv[None, :]

    dataset = ProbeDataset(
        resid=resid.astype(np.float32),
        items=items,
        layers=list(range(N_LAYERS + 1)),
        model_key="planted-instruct",
    )
    return dataset, vignettes


def test_recovery_peaks_at_planted_layers():
    dataset, vignettes = _planted_dataset()
    split = build_family_split(dataset.items, test_frac=0.25, seed=3)

    sign_res = construct_curve(dataset, CONSTRUCT_SPECS["sign"], split)
    sev_res = construct_curve(dataset, CONSTRUCT_SPECS["severity"], split)

    # Classification sign probe accuracy peaks at its planted layer.
    assert peak_layer(sign_res.curve, "raw_score") == SIGN_LAYER
    # Ridge severity RESIDUALIZED probe peaks at its own planted layer.
    assert peak_layer(sev_res.curve, "resid_score") == SEV_LAYER


def test_residualization_removes_planted_confound():
    dataset, _ = _planted_dataset()
    split = build_family_split(dataset.items, test_frac=0.25, seed=3)
    sev = construct_curve(dataset, CONSTRUCT_SPECS["severity"], split)
    curve = sev.curve.set_index("layer")

    # RAW severity probe leaks vividness's signal at the vividness layer
    # (severity correlates with vividness) -- a clear spurious bump.
    raw_at_viv = curve.loc[VIV_LAYER, "raw_score"]
    assert raw_at_viv > 0.25
    # RESIDUALIZED severity (severity ~ vividness + ...) removes it: near zero
    # at the vividness layer, while staying high at severity's own layer.
    resid_at_viv = curve.loc[VIV_LAYER, "resid_score"]
    resid_at_sev = curve.loc[SEV_LAYER, "resid_score"]
    assert resid_at_viv < 0.15
    assert resid_at_sev > 0.2
    # The confound removal is what discriminates: raw >> residualized at the
    # confound layer.
    assert raw_at_viv - resid_at_viv > 0.2
    # The recipe records the residualization.
    assert sev.recipe.startswith("severity ~") and "vividness" in sev.recipe


def test_mediators_excluded_from_design_factor_recipes():
    """Researcher decision (DECISIONS_FOR_HUMANS.md item a, 2026-07-28,
    extended same day): behavioral means are downstream mediators of the
    design factors, so they are excluded from the residualization confound
    sets of ALL design-factor (condition) probes -- sign, valence_moral,
    typicality_condition, vividness_evocativeness -- but retained for the
    curation-rating probes, whose cross-item correlation is a
    stimulus-construction confound."""
    dataset, _ = _planted_dataset()
    n = dataset.n_items
    rng = _rng(1)
    # Inject behavioral means so they WOULD be eligible confounds if not excluded.
    dataset.items["blame_mean"] = 5 + rng.standard_normal(n)
    dataset.items["intentionality_mean"] = 5 + rng.standard_normal(n)
    split = build_family_split(dataset.items, test_frac=0.25, seed=3)

    design_factor_constructs = (
        "sign", "valence_moral", "typicality_condition", "vividness_evocativeness",
    )
    for name in design_factor_constructs:
        curve = construct_curve(dataset, CONSTRUCT_SPECS[name], split)
        assert "blame_mean" not in curve.recipe, name
        assert "intentionality_mean" not in curve.recipe, name

    # Curation-rating probes still residualize on the behavioral means.
    severity = construct_curve(dataset, CONSTRUCT_SPECS["severity"], split)
    assert "blame_mean" in severity.recipe and "intentionality_mean" in severity.recipe


def test_dissociation_call_correct():
    dataset, _ = _planted_dataset()
    split = build_family_split(dataset.items, test_frac=0.25, seed=3)
    results = [
        construct_curve(dataset, CONSTRUCT_SPECS["severity"], split),
        construct_curve(dataset, CONSTRUCT_SPECS["vividness_evocativeness"], split),
    ]
    # vividness_evocativeness rating variant is in all_specs; fit it too.
    viv_rating = [s for s in all_specs() if s.construct == "vividness_evocativeness" and s.target_kind == "rating"][0]
    results.append(construct_curve(dataset, viv_rating, split))

    dissociation = probes.peak_layer_dissociation(dataset, results, n_boot=60, seed=1)
    # severity vs vividness-rating: peaks are the two distinct planted layers.
    sev_key = "severity::rating"
    viv_key = "vividness_evocativeness::rating"
    row = dissociation[
        ((dissociation["construct_a"] == sev_key) & (dissociation["construct_b"] == viv_key))
        | ((dissociation["construct_a"] == viv_key) & (dissociation["construct_b"] == sev_key))
    ]
    assert len(row) == 1
    peaks = {row["construct_a"].iloc[0]: row["observed_peak_a"].iloc[0],
             row["construct_b"].iloc[0]: row["observed_peak_b"].iloc[0]}
    assert peaks[sev_key] == SEV_LAYER
    assert peaks[viv_key] == VIV_LAYER
    assert abs(row["observed_diff"].iloc[0]) == abs(SEV_LAYER - VIV_LAYER)


def test_subspace_overlap_separates_distinct_constructs():
    dataset, _ = _planted_dataset()
    split = build_family_split(dataset.items, test_frac=0.25, seed=3)
    results = [
        construct_curve(dataset, CONSTRUCT_SPECS["sign"], split),
        construct_curve(dataset, CONSTRUCT_SPECS["severity"], split),
    ]
    overlap = probes.subspace_overlap(results, top_k=1)
    assert len(overlap) == 1
    # Sign and severity were planted along ORTHOGONAL directions → low cosine.
    assert overlap["top_cos"].iloc[0] < 0.5


# ---------------------------------------------------------------------------
# Probe fitting basics.
# ---------------------------------------------------------------------------


def test_fit_probe_skips_degenerate_target():
    X = _rng().standard_normal((10, 4))
    # single-class classification → None
    assert probes.fit_probe(X, np.zeros(10, dtype=int), "classification", "sign", 0) is None
    # zero-variance ridge → None
    assert probes.fit_probe(X, np.full(10, 3.0), "ridge", "severity", 0) is None


def test_probe_direction_is_unit_and_in_resid_space():
    X = _rng().standard_normal((40, 6))
    y = (X @ np.array([1.0, 0, 0, 0, 0, 0]) > 0).astype(int)
    probe = probes.fit_probe(X, y, "classification", "sign", 0)
    d = probe.direction()
    assert abs(np.linalg.norm(d) - 1.0) < 1e-9


# ---------------------------------------------------------------------------
# RQ2 end-to-end: run_probes emits figures + parquet tables with schema.
# ---------------------------------------------------------------------------


def _write_cache(tmp_path: Path, dataset: ProbeDataset, prompt_ids) -> Path:
    from knobe.mech import cache_acts

    acts_dir = tmp_path / "acts" / dataset.model_key
    cache_acts.write_cache(
        dataset.resid, prompt_ids, acts_dir,
        {"model_key": dataset.model_key, "layers": dataset.layers,
         "n_layers": N_LAYERS, "d_model": D_MODEL},
    )
    return acts_dir


def test_run_probes_emits_reports(tmp_path):
    dataset, vignettes = _planted_dataset()
    prompt_ids = _prompt_ids(vignettes)
    acts_dir = _write_cache(tmp_path, dataset, prompt_ids)
    vig_path = tmp_path / "vignettes.csv"
    cur_path = tmp_path / "curated.csv"
    write_csv_validated(vignettes, vig_path, VignetteRow)

    n = len(vignettes)
    rng = _rng(5)
    curated = build_curated(
        vignettes,
        np.clip(np.round(5 + rng.standard_normal(n)), 0, 10),
        np.clip(np.round(5 + rng.standard_normal(n)), 0, 10),
        np.clip(np.round(5 + rng.standard_normal(n)), 0, 10),
    )
    write_csv_validated(curated, cur_path, CuratedRow)

    out_root = tmp_path / "results"
    rc = probes.run_probes(
        release="v0.1", model_key=dataset.model_key, acts_dir=acts_dir,
        vignettes_path=vig_path, curated_path=cur_path, out_root=out_root,
        seed=3, n_boot=40,
    )
    assert rc == 0
    report = out_root / "v0.1" / "mech_report"
    assert (report / "rq2_curves.parquet").exists()
    assert (report / "rq2_curve_cis.parquet").exists()
    assert (report / "rq2_dissociation.parquet").exists()
    assert (report / "rq2_localization.png").exists()

    curves = pd.read_parquet(report / "rq2_curves.parquet")
    assert {"construct", "target_kind", "layer", "raw_score", "resid_score",
            "partial_corr", "cv_score"}.issubset(curves.columns)

    # ProbeRecord json + npz artifacts were written (spec §3.9).
    pdir = out_root / "v0.1" / "probes" / dataset.model_key
    jsons = list(pdir.glob("*.json"))
    npzs = list(pdir.glob("*.npz"))
    assert jsons and len(jsons) == len(npzs)
    from knobe.schemas import ProbeRecord

    rec = ProbeRecord.model_validate_json(jsons[0].read_text())
    assert rec.residualization_recipe and rec.target_kind in ("condition", "rating")


def test_behavioral_means_join_and_probe_fit(tmp_path):
    dataset, vignettes = _planted_dataset()
    prompt_ids = _prompt_ids(vignettes)
    acts_dir = _write_cache(tmp_path, dataset, prompt_ids)
    vig_path = tmp_path / "vignettes.csv"
    write_csv_validated(vignettes, vig_path, VignetteRow)
    n = len(vignettes)
    rng = _rng(11)
    curated = build_curated(
        vignettes,
        np.clip(np.round(5 + rng.standard_normal(n)), 0, 10),
        np.clip(np.round(5 + rng.standard_normal(n)), 0, 10),
        np.clip(np.round(5 + rng.standard_normal(n)), 0, 10),
    )
    cur_path = tmp_path / "curated.csv"
    write_csv_validated(curated, cur_path, CuratedRow)

    # Raw-format results.jsonl with intentionality + blame ratings per variant.
    results = []
    items = dataset.items
    for _, row in items.iterrows():
        for q in ("intentionality", "blame"):
            for sidx in range(2):
                pid = f"{row['variant_id']}::{q}::raw"
                rating = 5.0 + (2.0 if row["sign"] == "bad" else -2.0 if row["sign"] == "good" else 0.0)
                results.append(
                    ResultRecord(
                        job_id=f"{pid}::{sidx}", prompt_id=pid, model_key="m",
                        sample_idx=sidx, temperature=1.0, seed=1, raw_response=str(rating),
                        parsed_rating=int(rating), parse_ok=True, parse_method="regex",
                        model_revision="fake", runner_version="t", timestamp=0.0,
                    )
                )
    res_path = tmp_path / "results.jsonl"
    write_jsonl(results, res_path)

    from knobe.mech._data import load_probe_dataset

    ds = load_probe_dataset(acts_dir, vig_path, cur_path, res_path)
    assert ds.has_behavioral
    assert ds.items["blame_mean"].notna().all()
    assert ds.items["intentionality_mean"].notna().all()

    out_root = tmp_path / "results"
    rc = probes.run_probes(
        release="v0.1", model_key=dataset.model_key, acts_dir=acts_dir,
        vignettes_path=vig_path, curated_path=cur_path, results_path=res_path,
        out_root=out_root, seed=3, n_boot=10,
    )
    assert rc == 0
    curves = pd.read_parquet(out_root / "v0.1" / "mech_report" / "rq2_curves.parquet")
    # The behavioral constructs were fit (labels present).
    assert {"blame_rating", "intentionality_rating"}.issubset(set(curves["construct"]))


def test_run_probes_skips_behavioral_without_results(tmp_path, capsys):
    dataset, vignettes = _planted_dataset()
    prompt_ids = _prompt_ids(vignettes)
    acts_dir = _write_cache(tmp_path, dataset, prompt_ids)
    vig_path = tmp_path / "vignettes.csv"
    write_csv_validated(vignettes, vig_path, VignetteRow)
    n = len(vignettes)
    rng = _rng(5)
    curated = build_curated(
        vignettes,
        np.clip(np.round(5 + rng.standard_normal(n)), 0, 10),
        np.clip(np.round(5 + rng.standard_normal(n)), 0, 10),
        np.clip(np.round(5 + rng.standard_normal(n)), 0, 10),
    )
    cur_path = tmp_path / "curated.csv"
    write_csv_validated(curated, cur_path, CuratedRow)

    probes.run_probes(
        release="v0.1", model_key=dataset.model_key, acts_dir=acts_dir,
        vignettes_path=vig_path, curated_path=cur_path, out_root=tmp_path / "r",
        seed=3, n_boot=10,
    )
    err = capsys.readouterr().err
    assert "behavioral" in err.lower()


# ---------------------------------------------------------------------------
# RQ3: selective vs uniform suppression.
# ---------------------------------------------------------------------------


def _make_gap_long(mode: str, seed=0, n_groups=16):
    """Per-scaffold component gaps under baseline and one patched config, with
    UNEQUAL baselines per component. The RQ3 model normalizes to the baseline
    (proportional), so:
      * "proportional" -- patch takes every component to 50% of ITS baseline
        → parallel normalized gaps → UNIFORM (no interaction).
      * "selective" -- patch collapses ONLY 'moral' → interaction.
    An additive test on the RAW (unequal-baseline) gaps would wrongly flag the
    proportional case as selective; the normalization is what fixes it."""
    rng = _rng(seed)
    rows = []
    base_gap = {"moral": 3.0, "nonmoral": 2.5, "typ": 2.0, "evoc": 1.5, "neu_offset": 1.0}
    for g in range(n_groups):
        group = f"AA-{g:02d}"
        for comp, bg in base_gap.items():
            rows.append({"group": group, "config": "baseline", "component": comp,
                         "gap": bg + 0.2 * rng.standard_normal()})
            if mode == "selective":
                patched = (0.2 if comp == "moral" else bg) + 0.2 * rng.standard_normal()
            else:  # proportional
                patched = 0.5 * bg + 0.2 * rng.standard_normal()
            rows.append({"group": group, "config": "[4]", "component": comp,
                         "gap": patched})
    return pd.DataFrame(rows)


def test_rq3_selective_suppression_detected():
    long_df = _make_gap_long("selective", seed=1)
    res = decompose.fit_suppression_model(long_df)
    assert res["converged"]
    assert res["selective"] is True
    assert res["interaction_p"] < 0.05


def test_rq3_proportional_suppression_not_flagged():
    long_df = _make_gap_long("proportional", seed=2)
    res = decompose.fit_suppression_model(long_df)
    assert res["converged"]
    assert res["selective"] is False
    assert res["interaction_p"] > 0.05


def test_rq3_normalization_is_what_prevents_spurious_selective():
    """Discriminating: proportional suppression of UNEQUAL baselines is
    flagged SELECTIVE by a raw-gap additive interaction test, but UNIFORM once
    normalized -- proving the fix (normalize before testing) matters."""
    import statsmodels.formula.api as smf
    import statsmodels.api as sm

    long_df = _make_gap_long("proportional", seed=4)
    # Raw-gap additive interaction (the buggy formulation) → spurious selective.
    raw_full = smf.ols("gap ~ C(config) * C(component)", data=long_df).fit()
    raw_red = smf.ols("gap ~ C(config) + C(component)", data=long_df).fit()
    raw_p = float(sm.stats.anova_lm(raw_red, raw_full)["Pr(>F)"].iloc[-1])
    assert raw_p < 0.05  # would (wrongly) call it selective
    # Normalized (the fix) → uniform.
    assert decompose.fit_suppression_model(long_df)["selective"] is False


def test_component_gaps_from_records_roundtrip():
    vignettes = build_vignettes(domains=("AA",), n_sets=3)
    by_variant = {v.variant_id: v for v in vignettes}
    # Build PatchRecords where bad>good by a fixed amount (a real Knobe gap).
    def make_records(config, knobe_gap):
        recs = []
        for v in vignettes:
            ev = 5.0 + (knobe_gap / 2 if v.sign == "bad" else -knobe_gap / 2 if v.sign == "good" else 0.0)
            pid = f"{v.variant_id}::intentionality::raw"
            recs.append(
                PatchRecord(
                    job_id=f"{pid}::patch::{config}", prompt_id=pid, model_key="m",
                    sample_idx=0, temperature=0.0, seed=0, raw_response="x",
                    parsed_rating=ev, parse_ok=True, parse_method="logit_fallback",
                    logprobs_0_10=None, model_revision="fake", runner_version="t", timestamp=0.0,
                    patch=PatchInfo(donor="none" if config == "baseline" else "pretrained",
                                    layers=[] if config == "baseline" else [4], positions="all"),
                    scoring="logits_0_10",
                )
            )
        return recs

    long_df = decompose.component_gaps_from_records(
        {"baseline": make_records("baseline", 4.0), "[4]": make_records("[4]", 0.0)},
        vignettes,
    )
    # moral component gap = MB - MG mean = knobe_gap for baseline, ~0 patched.
    base_moral = long_df[(long_df["config"] == "baseline") & (long_df["component"] == "moral")]["gap"]
    patch_moral = long_df[(long_df["config"] == "[4]") & (long_df["component"] == "moral")]["gap"]
    assert base_moral.mean() == pytest.approx(4.0, abs=1e-6)
    assert patch_moral.mean() == pytest.approx(0.0, abs=1e-6)


def test_rq3_normalized_table_and_run_decompose(tmp_path):
    metrics = pd.DataFrame(
        [
            {"model_key": "m", "family": "AA", "layers": "[]", "delta_moral": 4.0,
             "delta_nonmoral": 3.0, "e_typ": 2.0, "e_evoc": 1.0, "delta_neutral_offset": 0.5, "delta_knobe": 3.5},
            {"model_key": "m", "family": "AA", "layers": "[4]", "delta_moral": 0.4,
             "delta_nonmoral": 2.9, "e_typ": 1.9, "e_evoc": 0.9, "delta_neutral_offset": 0.5, "delta_knobe": 1.2},
        ]
    )
    mp = tmp_path / "patch_metrics.parquet"
    metrics.to_parquet(mp)
    table = decompose.rq3_normalized_table(metrics)
    moral = table[table["component"] == "moral"].iloc[0]
    assert moral["normalized"] == pytest.approx(0.1, abs=1e-6)  # 0.4 / 4.0

    rc = decompose.run_decompose(release="v0.1", model_key="m",
                                 patch_metrics_path=mp, out_root=tmp_path / "results")
    assert rc == 0
    report = tmp_path / "results" / "v0.1" / "mech_report"
    assert (report / "rq3_decomposition.parquet").exists()
    assert (report / "rq3_decomposition.png").exists()
    assert (report / "decompose_summary.md").exists()


# ---------------------------------------------------------------------------
# RQ4: probe alignment vs nulls.
# ---------------------------------------------------------------------------


def test_rq4_planted_alignment_beats_null():
    rng = _rng(0)
    d = 64
    direction = rng.standard_normal(d)
    direction /= np.linalg.norm(direction)
    # Δh planted ALONG the probe direction at layer 5, and an UNRELATED
    # (orthogonal) Δh at layer 6.
    other = rng.standard_normal(d)
    other -= other @ direction * direction
    other /= np.linalg.norm(other)
    delta_h = {5: 3.0 * direction + 0.01 * rng.standard_normal(d), 6: 3.0 * other}
    dirs = {"blame_rating::rating": {5: direction, 6: direction}}

    align = decompose.rq4_alignment(delta_h, dirs, random_null_n=2000, seed=1)
    at5 = align[align["layer"] == 5].iloc[0]
    at6 = align[align["layer"] == 6].iloc[0]
    # Planted: |cos| ~ 1, beats the random-vector null.
    assert at5["abs_cos"] > 0.9
    assert at5["aligned_vs_random"]
    # Unrelated: within the null band.
    assert at6["abs_cos"] < 0.2
    assert not at6["aligned_vs_random"]


def test_run_patched_with_cache_sources_delta_h():
    """The RQ4 Δh sourcing path on FakeBackend: run_patched_with_cache −
    run_with_cache. A signal-free donor patched at the planted layer changes
    the downstream residuals (nonzero Δh at/after that layer); self-patch
    leaves them unchanged (Δh ≡ 0)."""
    from knobe.mech.backend import FakeBackend, PlantedSignal

    label_fn = lambda t: (t.split("|")[0], {"bad": 1, "good": -1}.get(t.split("|")[-1], 0))
    recipient = FakeBackend("inst", N_LAYERS, D_MODEL, label_fn=label_fn,
                            planted=PlantedSignal(layer=SEV_LAYER, magnitude=2.0))
    donor = FakeBackend("base", N_LAYERS, D_MODEL, label_fn=label_fn)
    prompts = ["i0|bad", "i1|good", "i2|bad", "i3|good"]

    dh = decompose.mean_delta_h(recipient, donor, prompts, [SEV_LAYER])
    # Patching the signal layer with a signal-free donor removes the signal →
    # nonzero Δh from that layer onward.
    assert np.linalg.norm(dh[SEV_LAYER]) > 1e-6
    assert np.linalg.norm(dh[N_LAYERS]) > 1e-6
    # Self-patch (donor == recipient) is the identity → Δh ≡ 0.
    dh_self = decompose.mean_delta_h(recipient, recipient, prompts, [SEV_LAYER])
    assert all(np.linalg.norm(v) < 1e-9 for v in dh_self.values())


def test_rq4_figure_and_summary_emitted(tmp_path):
    rng = _rng(0)
    d = 48
    direction = rng.standard_normal(d)
    direction /= np.linalg.norm(direction)
    delta_h = {5: 3.0 * direction, 6: rng.standard_normal(d)}
    dirs = {"blame_rating::rating": {5: direction, 6: direction},
            "vividness_evocativeness::condition": {5: rng.standard_normal(d)}}
    align = decompose.rq4_alignment(delta_h, dirs, random_null_n=500, seed=1)

    fig = tmp_path / "rq4.png"
    decompose.plot_rq4(align, fig)
    assert fig.exists()

    summary = tmp_path / "summary.md"
    decompose.write_markdown_summary(
        summary, model_key="m",
        rq3={"selective": True, "interaction_p": 0.01, "lr_stat": 12.0, "df_diff": 4,
             "n_groups": 16, "fallback_used": False},
        rq3_table=None, rq4=align,
    )
    text = summary.read_text()
    assert "RQ3" in text and "RQ4" in text and "exploratory" in text.lower()


def test_random_unit_null_matches_analytic_sd():
    rng = _rng(2)
    dh = rng.standard_normal(100)
    null = decompose.random_unit_null(dh, n=4000, seed=3)
    # Simulated sd concentrates near the analytic 1/sqrt(d).
    assert abs(null["null_sd"] - null["analytic_sd"]) < 0.02


def test_rq4_permuted_label_null_both_modes_beat_planted():
    """The permuted-label null must MIRROR the observed pipeline. For the RAW
    probe direction use the raw null; for the RESIDUALIZED direction use the
    residualized null (which re-residualizes each permuted target). In both
    modes the true planted alignment clears the matched null band."""
    dataset, _ = _planted_dataset()
    split = build_family_split(dataset.items, test_frac=0.25, seed=3)
    sev = construct_curve(dataset, CONSTRUCT_SPECS["severity"], split)

    # Raw mode.
    raw_dir = sev.raw_probes[SEV_LAYER].direction()
    dh_raw = 3.0 * raw_dir
    raw_null = decompose.permuted_label_null(
        dataset, CONSTRUCT_SPECS["severity"], split, SEV_LAYER, dh_raw,
        n_perm=40, seed=1, residualized=False,
    )
    assert 1.0 > raw_null["null_abs_hi"]  # true |cos| ≈ 1 clears the null

    # Residualized mode (the RQ2/RQ4 default).
    resid_dir = sev.resid_probes[SEV_LAYER].direction()
    dh_resid = 3.0 * resid_dir
    resid_null = decompose.permuted_label_null(
        dataset, CONSTRUCT_SPECS["severity"], split, SEV_LAYER, dh_resid,
        n_perm=40, seed=1, residualized=True,
    )
    assert 1.0 > resid_null["null_abs_hi"]


def test_rq4_permuted_null_residualized_differs_from_raw():
    """On the strong-confound planted dataset the residualized null runs the
    residualization step, so it is numerically distinct from the raw null for
    the same Δh -- confirming the pipelines are not silently identical."""
    dataset, _ = _planted_dataset()
    split = build_family_split(dataset.items, test_frac=0.25, seed=3)
    dh = _rng(7).standard_normal(D_MODEL)
    raw_null = decompose.permuted_label_null(
        dataset, CONSTRUCT_SPECS["severity"], split, SEV_LAYER, dh,
        n_perm=60, seed=2, residualized=False,
    )
    resid_null = decompose.permuted_label_null(
        dataset, CONSTRUCT_SPECS["severity"], split, SEV_LAYER, dh,
        n_perm=60, seed=2, residualized=True,
    )
    assert abs(raw_null["null_abs_hi"] - resid_null["null_abs_hi"]) > 1e-6


# ---------------------------------------------------------------------------
# Gemma Scope stub.
# ---------------------------------------------------------------------------


def test_fake_sae_topk_delta_features():
    sae = decompose.load_sae("fake", d_model=D_MODEL, seed=0)
    rng = _rng(0)
    unpatched = rng.standard_normal((20, D_MODEL))
    # Patched differs along one strong direction → some features move most.
    patched = unpatched + 2.0 * sae.W_enc[3][None, :]
    table = decompose.top_k_delta_features(unpatched, patched, sae, k=5)
    assert list(table.columns) == ["feature_id", "mean_delta", "mean_abs_delta", "label"]
    assert len(table) == 5
    # Descending by |Δ|.
    assert (table["mean_abs_delta"].to_numpy()[:-1] >= table["mean_abs_delta"].to_numpy()[1:]).all()
    # Neuronpedia labels are the documented unlabeled stub.
    assert all(lbl is None for lbl in table["label"])


def test_load_sae_real_name_requires_extra():
    with pytest.raises((RuntimeError, NotImplementedError)):
        decompose.load_sae("gemma-scope", d_model=D_MODEL)


# ---------------------------------------------------------------------------
# CLI smoke: knobe mech probes / decompose.
# ---------------------------------------------------------------------------


def test_cli_mech_probes_and_decompose(tmp_path):
    from knobe.cli import main

    dataset, vignettes = _planted_dataset()
    prompt_ids = _prompt_ids(vignettes)
    acts_dir = _write_cache(tmp_path, dataset, prompt_ids)
    vig_path = tmp_path / "vignettes.csv"
    write_csv_validated(vignettes, vig_path, VignetteRow)
    n = len(vignettes)
    rng = _rng(9)
    curated = build_curated(
        vignettes,
        np.clip(np.round(5 + rng.standard_normal(n)), 0, 10),
        np.clip(np.round(5 + rng.standard_normal(n)), 0, 10),
        np.clip(np.round(5 + rng.standard_normal(n)), 0, 10),
    )
    cur_path = tmp_path / "curated.csv"
    write_csv_validated(curated, cur_path, CuratedRow)
    out_root = tmp_path / "results"

    rc = main([
        "mech", "probes", "--release", "v0.1", "--model-key", dataset.model_key,
        "--acts", str(acts_dir), "--vignettes", str(vig_path), "--curated", str(cur_path),
        "--out-root", str(out_root), "--n-boot", "20",
    ])
    assert rc == 0
    assert (out_root / "v0.1" / "mech_report" / "rq2_curves.parquet").exists()

    metrics = pd.DataFrame(
        [
            {"model_key": "m", "family": "AA", "layers": "[]", "delta_moral": 4.0,
             "delta_nonmoral": 3.0, "e_typ": 2.0, "e_evoc": 1.0, "delta_neutral_offset": 0.5, "delta_knobe": 3.5},
            {"model_key": "m", "family": "AA", "layers": "[4]", "delta_moral": 0.4,
             "delta_nonmoral": 2.9, "e_typ": 1.9, "e_evoc": 0.9, "delta_neutral_offset": 0.5, "delta_knobe": 1.2},
        ]
    )
    mp = tmp_path / "patch_metrics.parquet"
    metrics.to_parquet(mp)
    rc = main([
        "mech", "decompose", "--release", "v0.1", "--model-key", "m",
        "--patch-metrics", str(mp), "--out-root", str(out_root),
    ])
    assert rc == 0
    assert (out_root / "v0.1" / "mech_report" / "rq3_decomposition.parquet").exists()
