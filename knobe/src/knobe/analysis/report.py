"""WO-8 §5/§6: paper-artifact emission + the ``knobe analyze`` / ``make paper``
orchestrator.

Emits, into ``<out_dir>/`` (for ``make paper``: ``results/<release>/paper/``):
  * ``contrast_table.csv`` -- the Holm-corrected planned-contrast table
    (byte-stable: fixed column order, fixed float formatting, deterministically
    sorted rows -- WO-8 determinism acceptance).
  * ``ordinal_sensitivity.csv`` -- the OrderedModel distributional sensitivity
    check (see models.py's LMM-primary/ordinal-sensitivity inversion).
  * ``exclusions.json`` -- the never-silent exclusions ledger (analysis.ingest).
  * ``summary.md`` -- the human-readable summary, which CARRIES the LMM-primary
    deviation note IN ITS OWN TEXT (not only in a docstring) and the 1b EIV
    caveat, plus the corrected contrast table.
  * ``figures/*.png`` -- the descriptive figure set (analysis.figures).

Structural note (reported per the task's "one responsibility per module"): the
four named analysis modules are ingest/models/figures/figstyle; this ``report``
module is the thin fifth that turns their outputs into the paper artifacts and
wires the ``ingest -> models -> figures -> report`` orchestration for the CLI.
It was split out rather than folded into models.py (which stays statistics-only)
or the CLI (which stays argparse-only).
"""
from __future__ import annotations

import csv
import io
import math
from pathlib import Path
from typing import Sequence

from knobe.analysis import figures, ingest, models
from knobe.analysis.models import (
    ChatComparisonRow, ContrastSpec, DomainSensitivity, DomainSlopeSensitivity,
    OrdinalSensitivity, Prereg,
)
from knobe.schemas import ContrastResultRecord, ExclusionsLedger

DOMAIN_SLOPE_ANALYSIS = "domain_random_slope"

# The LMM-primary/ordinal-sensitivity deviation note -- MUST appear in the
# generated report's own text (not just a docstring), per the task brief. It
# is also in models.py's module docstring and contrasts.yaml's header.
DEVIATION_NOTE = (
    "**LMM-primary / ordinal-sensitivity (documented deviation, master spec §7.6).** "
    "WO-8 states a preference for an ordinal cumulative-link mixed model (CLMM) as the "
    "primary fit with a linear mixed model (LMM) as the sensitivity check. statsmodels' "
    "`OrderedModel` has NO random-effects support, and the crossed family/domain "
    "random-effects structure these clustered designs require is load-bearing (master "
    "spec §6, DR §2). We therefore INVERT the two: primary inference is the LMM "
    "(`mixedlm`, random intercept for family + domain as a variance component where "
    "estimable), and the ordinal model (`OrderedModel`, logit link, FIXED EFFECTS ONLY) "
    "is the distributional sensitivity check in `ordinal_sensitivity.csv`. This is a "
    "spec-vs-implementation-reality conflict resolved with documentation, not silently."
)

EIV_CAVEAT_1B = (
    "**1b errors-in-variables caveat.** Response-level pairing of an item's blame/praise "
    "rating with its intentionality rating is impossible (independent completions, DR §12). "
    "The 1b slope regresses intentionality responses on the ITEM's blame mean (bad) / praise "
    "mean (good), which is itself an estimate from finite completions -- that measurement "
    "error attenuates the slope toward 0, so the pred_c:sg_c interaction stays interpretable "
    "in sign but its magnitude is conservative (item-level pairing, WO-8 §2)."
)

_TABLE_COLUMNS = [
    "contrast", "rq", "model_family", "tuning_scope", "term",
    "estimate", "se", "p_value", "p_holm", "ci_low", "ci_high", "ci_method",
    "direction_expected", "direction_ok", "n_obs", "n_groups",
    "method", "converged", "fallback_used",
]
_FLOAT_COLUMNS = {"estimate", "se", "p_value", "p_holm", "ci_low", "ci_high"}


def _fmt(value, is_float: bool) -> str:
    """Byte-stable field formatting: floats to 6 decimals, None/NaN to empty,
    bools as True/False, everything else str()."""
    if value is None:
        return ""
    if is_float:
        if isinstance(value, float) and math.isnan(value):
            return ""
        return f"{float(value):.6f}"
    if isinstance(value, bool):
        return "True" if value else "False"
    return str(value)


def contrast_table_csv(records: Sequence[ContrastResultRecord]) -> str:
    """Renders the Holm-corrected contrast table to a byte-stable CSV string
    (fixed column order, 6-dp floats, ``\\n`` line terminator). Rows are
    written in the order given -- ``models.holm_correct`` already sorts them
    deterministically by (rq, contrast, model_family)."""
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(_TABLE_COLUMNS)
    for r in records:
        dumped = r.model_dump()
        writer.writerow([_fmt(dumped[c], c in _FLOAT_COLUMNS) for c in _TABLE_COLUMNS])
    return buf.getvalue()


def write_contrast_table(records: Sequence[ContrastResultRecord], out_path: str | Path) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(contrast_table_csv(records), encoding="utf-8")
    return out_path


_SENS_COLUMNS = ["contrast", "model_family", "term", "estimate", "p_value", "converged", "note"]


def ordinal_sensitivity_csv(sens: Sequence[OrdinalSensitivity]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(_SENS_COLUMNS)
    for s in sorted(sens, key=lambda x: (x.contrast, x.model_family)):
        writer.writerow([
            s.contrast, s.model_family, s.term,
            _fmt(s.estimate, True), _fmt(s.p_value, True),
            _fmt(s.converged, False), s.note,
        ])
    return buf.getvalue()


def write_ordinal_sensitivity(sens: Sequence[OrdinalSensitivity], out_path: str | Path) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(ordinal_sensitivity_csv(sens), encoding="utf-8")
    return out_path


DOMAIN_NOTE = (
    "**Domain clustering is NOT modeled by the primary LMM** (`method = lmm-familyRI`). "
    "statsmodels' MixedLM cannot cleanly nest families within a separate domain group, and "
    "a `vc_formula` on domain with family groups is mathematically inert (domain is constant "
    "within a family -- its SEs are byte-identical to plain family-RI). Master spec §6's "
    "\"domain = random effect\" intent is honored instead by the config-gated domain-cluster "
    "sensitivity fit below (same fixed effects, `groups=domain`) in `domain_sensitivity.csv`."
)

_DOMAIN_COLUMNS = ["contrast", "model_family", "term", "estimate", "se", "p_value", "n_domains", "method"]


def domain_sensitivity_csv(sens: Sequence[DomainSensitivity]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(_DOMAIN_COLUMNS)
    for s in sorted(sens, key=lambda x: (x.contrast, x.model_family)):
        writer.writerow([
            s.contrast, s.model_family, s.term, _fmt(s.estimate, True), _fmt(s.se, True),
            _fmt(s.p_value, True), s.n_domains, s.method,
        ])
    return buf.getvalue()


def write_domain_sensitivity(sens: Sequence[DomainSensitivity], out_path: str | Path) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(domain_sensitivity_csv(sens), encoding="utf-8")
    return out_path


_SLOPE_COLUMNS = [
    "contrast", "model_family", "term", "primary_estimate", "primary_ci_low", "primary_ci_high",
    "slope_estimate", "slope_ci_low", "slope_ci_high", "slope_variance", "ci_width_ratio",
    "n_domains", "converged", "qualified", "note",
]


def domain_slope_sensitivity_csv(rows: Sequence[DomainSlopeSensitivity]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(_SLOPE_COLUMNS)
    for r in sorted(rows, key=lambda x: (x.contrast, x.model_family)):
        writer.writerow([
            r.contrast, r.model_family, r.term,
            _fmt(r.primary_estimate, True), _fmt(r.primary_ci_low, True), _fmt(r.primary_ci_high, True),
            _fmt(r.slope_estimate, True), _fmt(r.slope_ci_low, True), _fmt(r.slope_ci_high, True),
            _fmt(r.slope_variance, True), _fmt(r.ci_width_ratio, True), r.n_domains,
            _fmt(r.converged, False), _fmt(r.qualified, False), r.note,
        ])
    return buf.getvalue()


def write_domain_slope_sensitivity(rows: Sequence[DomainSlopeSensitivity], out_path: str | Path) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(domain_slope_sensitivity_csv(rows), encoding="utf-8")
    return out_path


_CHAT_COLUMNS = ["contrast", "model_family", "term", "raw_estimate", "raw_p", "chat_estimate", "chat_p"]


def chat_comparison_csv(rows: Sequence[ChatComparisonRow]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(_CHAT_COLUMNS)
    for r in sorted(rows, key=lambda x: (x.contrast, x.model_family)):
        writer.writerow([
            r.contrast, r.model_family, r.term, _fmt(r.raw_estimate, True), _fmt(r.raw_p, True),
            _fmt(r.chat_estimate, True), _fmt(r.chat_p, True),
        ])
    return buf.getvalue()


def write_chat_comparison(rows: Sequence[ChatComparisonRow], out_path: str | Path) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(chat_comparison_csv(rows), encoding="utf-8")
    return out_path


def summary_markdown(
    records: Sequence[ContrastResultRecord],
    ledger: ExclusionsLedger,
    prereg: Prereg,
    *,
    figure_names: Sequence[str] = (),
    n_ordinal: int = 0,
    domain_sens: Sequence[DomainSensitivity] | None = None,
    slope_sens: Sequence[DomainSlopeSensitivity] | None = None,
    slope_rule: str = "",
    chat_rows: Sequence[ChatComparisonRow] | None = None,
    chat_enabled: bool = False,
    chat_had_rows: bool = False,
) -> str:
    """The human-readable ``summary.md`` -- carries the LMM-primary deviation
    note, the domain-not-modeled note, and the 1b EIV caveat IN ITS OWN TEXT,
    the exclusions summary (result-row exclusions and missing-manifest jobs as
    SEPARATE sentences), and the Holm-corrected contrast table grouped by RQ,
    plus the config-gated domain-cluster and chat-vs-raw sensitivity sections."""
    lines = [
        "# WO-8 behavioral analysis summary",
        "",
        f"Release: `{ledger.release}`. Prereg frozen: `{prereg.prereg_frozen}` "
        f"(contrasts.yaml is the preregistration of record; only declared contrasts are fit).",
        "",
        "## Statistical conventions (read first)",
        "",
        DEVIATION_NOTE,
        "",
        DOMAIN_NOTE,
        "",
        EIV_CAVEAT_1B,
        "",
        "Holm correction is applied within each (model_family, RQ) family. Response-level "
        "ratings are never aggregated for inference (master spec §6.3); item means feed the "
        "descriptive figures only. CIs in the contrast table are seeded family-cluster "
        "bootstrap intervals refit via OLS (`ci_method = cluster_bootstrap_ols`), a "
        "robustness companion to the LMM Wald p-value, not a second estimator of record.",
        "",
        "## Exclusions ledger (never silent)",
        "",
        f"Of {ledger.n_result_rows} result rows read, {ledger.n_included} were included and "
        f"{ledger.n_excluded} excluded (result-row exclusions sum to {ledger.n_excluded}; "
        f"included + excluded = {ledger.n_included + ledger.n_excluded} = result rows read).",
        "",
    ]
    if ledger.n_job_rows is not None:
        if ledger.n_missing_results:
            lines.append(
                f"Separately, {ledger.n_missing_results} of the {ledger.n_job_rows} jobs in the "
                f"manifest had no completed result (incomplete work, not a result-row exclusion)."
            )
        else:
            lines.append(
                f"Separately, all {ledger.n_job_rows} manifest jobs had a completed result "
                f"(no incomplete work)."
            )
        lines.append("")
    if ledger.entries:
        lines.append("| result-row exclusion reason | count |")
        lines.append("|---|---|")
        for e in ledger.entries:
            lines.append(f"| {e.reason} | {e.count} |")
        lines.append("")

    lines.append("## Holm-corrected planned contrasts")
    lines.append("")
    if not records:
        lines.append("_No contrasts were estimable on this dataset (too few groups per cell)._")
        lines.append("")
    else:
        by_rq: dict[str, list[ContrastResultRecord]] = {}
        for r in records:
            by_rq.setdefault(r.rq, []).append(r)
        for rq in sorted(by_rq):
            lines.append(f"### {rq}")
            lines.append("")
            lines.append(
                "| contrast | model_family | scope | estimate | 95% CI | p | p(Holm) | dir | dir_ok | method |"
            )
            lines.append("|---|---|---|---|---|---|---|---|---|---|")
            for r in by_rq[rq]:
                ci = (
                    f"[{r.ci_low:.3f}, {r.ci_high:.3f}]"
                    if r.ci_low is not None and r.ci_high is not None else "-"
                )
                lines.append(
                    f"| {r.contrast} | {r.model_family} | {r.tuning_scope} | {r.estimate:.3f} | "
                    f"{ci} | {r.p_value:.4f} | {r.p_holm:.4f} | {r.direction_expected} | "
                    f"{r.direction_ok} | {r.method} |"
                )
            lines.append("")

    lines.append("## Ordinal sensitivity check")
    lines.append("")
    lines.append(
        f"The distributional sensitivity check (OrderedModel, logit, fixed effects only) "
        f"is in `ordinal_sensitivity.csv` ({n_ordinal} fits). See the deviation note above."
    )
    lines.append("")

    lines.append("## Domain-cluster sensitivity")
    lines.append("")
    if domain_sens:
        lines.append(
            "Same fixed effects refit with `groups=domain` (domain as the clustering unit) -- "
            "the domain-aware companion to the family-RI primary (`domain_sensitivity.csv`):"
        )
        lines.append("")
        lines.append("| contrast | model_family | estimate | p | n_domains | method |")
        lines.append("|---|---|---|---|---|---|")
        for s in sorted(domain_sens, key=lambda x: (x.contrast, x.model_family)):
            lines.append(
                f"| {s.contrast} | {s.model_family} | {s.estimate:.3f} | {s.p_value:.4f} | "
                f"{s.n_domains} | {s.method} |"
            )
        lines.append("")
    else:
        lines.append(
            "_Not run (config-gated, off by default) or no cell spanned >=2 domains -- pass "
            "`--domain-sensitivity` on a multi-domain release to populate it._"
        )
        lines.append("")

    lines.append("## Domain-random-slope sensitivity (declared; researcher decision 2026-07-28)")
    lines.append("")
    lines.append(
        "DECLARED in contrasts.yaml (`sensitivity_analyses.domain_random_slope`): the headline "
        "cross-domain-generalization contrasts refit with `groups=domain` and a random SLOPE for "
        "the focal term, same fixed effects as the primary. Interpretation rule (verbatim from "
        "the prereg): "
    )
    if slope_rule:
        lines.append(f"> {slope_rule}")
    lines.append("")
    if slope_sens:
        lines.append("| contrast | model_family | primary CI | slope CI | CI ratio | slope var | conv | QUALIFIED |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for s in sorted(slope_sens, key=lambda x: (x.contrast, x.model_family)):
            pci = (
                f"[{s.primary_ci_low:.3f}, {s.primary_ci_high:.3f}]"
                if s.primary_ci_low is not None and s.primary_ci_high is not None else "-"
            )
            sci = (
                f"[{s.slope_ci_low:.3f}, {s.slope_ci_high:.3f}]"
                if s.slope_ci_low is not None and s.slope_ci_high is not None else "-"
            )
            ratio = f"{s.ci_width_ratio:.2f}" if s.ci_width_ratio is not None else "-"
            svar = f"{s.slope_variance:.3f}" if s.slope_variance is not None else "-"
            verdict = "**QUALIFIED**" if s.qualified else "unqualified"
            lines.append(
                f"| {s.contrast} | {s.model_family} | {pci} | {sci} | {ratio} | {svar} | "
                f"{s.converged} | {verdict} |"
            )
        lines.append("")
        lines.append("Full detail (with per-row rationale) in `domain_slope_sensitivity.csv`.")
        lines.append("")
    else:
        lines.append(
            "_Not run (config-gated, off by default) or no declared contrast spanned >=2 domains "
            "-- pass `--domain-slope-sensitivity` on a multi-domain release to populate it._"
        )
        lines.append("")

    lines.append("## Chat-vs-raw format robustness (WO-8 §4)")
    lines.append("")
    if not chat_enabled:
        lines.append("_Not run (config-gated, off by default); pass `--chat-comparison` to enable._")
        lines.append("")
    elif not chat_had_rows:
        lines.append("No chat-format rows in the data; comparison skipped (logged, never silent).")
        lines.append("")
    elif chat_rows:
        lines.append("Primary contrasts refit on the `chat` subset, raw vs chat side by side "
                     "(`chat_comparison.csv`):")
        lines.append("")
        lines.append("| contrast | model_family | raw estimate | raw p | chat estimate | chat p |")
        lines.append("|---|---|---|---|---|---|")
        for r in sorted(chat_rows, key=lambda x: (x.contrast, x.model_family)):
            lines.append(
                f"| {r.contrast} | {r.model_family} | {r.raw_estimate:.3f} | {r.raw_p:.4f} | "
                f"{r.chat_estimate:.3f} | {r.chat_p:.4f} |"
            )
        lines.append("")
    else:
        lines.append("Chat-format rows exist but no contrast cell was estimable on both formats.")
        lines.append("")

    if figure_names:
        lines.append("## Figures")
        lines.append("")
        for name in figure_names:
            lines.append(f"![{name}](figures/{name})")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Orchestrator: ingest -> models -> figures -> report (knobe analyze / make paper)
# ---------------------------------------------------------------------------


def run_analyze(
    *,
    results_paths: Sequence[str | Path],
    vignettes_path: str | Path,
    out_dir: str | Path,
    curated_path: str | Path | None = None,
    jobs_path: str | Path | None = None,
    registry_path: str | Path | None = None,
    contrasts_path: str | Path | None = None,
    release: str = "unknown",
    contrast_names: Sequence[str] | None = None,
    base_seed: int = 0,
    n_boot: int = 200,
    alpha: float = 0.05,
    make_figures: bool = True,
    domain_sensitivity: bool = False,
    domain_slope_sensitivity: bool = False,
    chat_comparison: bool = False,
    logit_fallback_checkpoints: Sequence[str] = (),
) -> int:
    """Full S8 pipeline: ingest (join + exclusions ledger) -> fit the declared
    RQ1 contrasts (Holm-corrected) -> descriptive figures -> paper artifacts.
    ``contrast_names`` (default: all declared) is governance-checked against
    contrasts.yaml -- an undeclared name hard-errors (models.select_contrasts).
    Returns a process exit code."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    prereg = models.load_prereg(contrasts_path)
    specs: list[ContrastSpec] = models.select_contrasts(prereg, contrast_names)

    df, ledger = ingest.ingest(
        results_paths, vignettes_path, curated_path=curated_path, jobs_path=jobs_path,
        registry_path=registry_path, release=release,
        logit_fallback_checkpoints=logit_fallback_checkpoints,
    )
    ingest.write_exclusions(ledger, out_dir / "exclusions.json")

    prepared = models.prepare_frame(df)
    records, sens = models.fit_all(
        prepared, specs, base_seed=base_seed, n_boot=n_boot, alpha=alpha,
    )

    write_contrast_table(records, out_dir / "contrast_table.csv")
    write_ordinal_sensitivity(sens, out_dir / "ordinal_sensitivity.csv")

    domain_sens: list[DomainSensitivity] = []
    if domain_sensitivity and not prepared.empty:
        domain_sens = models.domain_sensitivity_all(prepared, specs)
        write_domain_sensitivity(domain_sens, out_dir / "domain_sensitivity.csv")

    slope_sens: list[DomainSlopeSensitivity] = []
    slope_rule = ""
    if domain_slope_sensitivity and not prepared.empty:
        # Governed exactly like contrasts: only a DECLARED sensitivity analysis
        # runs (undeclared -> hard error).
        analysis = models.select_sensitivity_analysis(prereg, DOMAIN_SLOPE_ANALYSIS)
        slope_rule = analysis.interpretation_rule
        slope_sens = models.domain_slope_sensitivity(prepared, specs, analysis)
        write_domain_slope_sensitivity(slope_sens, out_dir / "domain_slope_sensitivity.csv")

    chat_rows: list[ChatComparisonRow] = []
    chat_had_rows = False
    if chat_comparison and not prepared.empty:
        chat_rows, chat_had_rows = models.chat_format_comparison(prepared, specs)
        write_chat_comparison(chat_rows, out_dir / "chat_comparison.csv")
        if not chat_had_rows:
            print("[analysis] no chat-format rows; chat-vs-raw comparison skipped.")

    figure_names: list[str] = []
    if make_figures and not df.empty:
        paths = figures.generate_all(df, out_dir / "figures")
        figure_names = [p.name for p in paths]

    summary = summary_markdown(
        records, ledger, prereg, figure_names=figure_names, n_ordinal=len(sens),
        domain_sens=domain_sens, slope_sens=slope_sens, slope_rule=slope_rule,
        chat_rows=chat_rows, chat_enabled=chat_comparison, chat_had_rows=chat_had_rows,
    )
    (out_dir / "summary.md").write_text(summary, encoding="utf-8")

    print(
        f"[analysis] wrote {len(records)} contrast rows, {len(sens)} ordinal-sensitivity "
        f"fits, {len(domain_sens)} domain-cluster + {len(slope_sens)} domain-slope sensitivity "
        f"fits, {len(figure_names)} figures to {out_dir}"
    )
    return 0
