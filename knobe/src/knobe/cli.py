"""``knobe`` console entry point: argparse with subparsers, dispatched via a
small registry table (common-context.md: "the `knobe` console entry point
dispatches subcommands... Add your subcommand to the existing CLI registry
pattern.").

Later tasks register their own subcommands into ``SUBCOMMANDS`` below
(``generate``, ``jobs``, ``curate``, etc.) rather than hand-rolling their own
argparse entry point.
"""
from __future__ import annotations

import argparse
import sys
from typing import Callable

SubcommandRegistrar = Callable[[argparse._SubParsersAction], None]


def _register_version(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("version", help="Print the installed knobe version.")
    parser.set_defaults(func=_run_version)


def _run_version(args: argparse.Namespace) -> int:
    from knobe import constants

    print(f"knobe schema_version={constants.SCHEMA_VERSION}")
    return 0


def _register_assemble(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "assemble",
        help="Assemble a master_matrix.csv/.xlsx into vignettes.csv (S2; WO-2 Part A).",
    )
    parser.add_argument("input", help="Path to master_matrix.csv or .xlsx")
    parser.add_argument(
        "out_prefix",
        help="Output path prefix; writes <prefix>.csv, <prefix>.xlsx, <prefix>_preview.txt",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Write output even if validation errors were found (for inspecting partial output).",
    )
    parser.add_argument(
        "--release", metavar="vX.Y",
        help="Also write a frozen release into data/release/vX.Y/ (requires --curated).",
    )
    parser.add_argument("--curated", help="Path to curated.csv; required with --release.")
    parser.add_argument(
        "--changelog", default="", help="Changelog string recorded in the release manifest.",
    )
    parser.add_argument(
        "--gates-passed", default="", metavar="G0,G1,...",
        help="Comma-separated gate names recorded in the release manifest.",
    )
    parser.set_defaults(func=_run_assemble)


def _run_assemble(args: argparse.Namespace) -> int:
    from knobe.assemble import run as run_assemble

    gates_passed = [g.strip() for g in args.gates_passed.split(",") if g.strip()]
    return run_assemble(
        args.input,
        args.out_prefix,
        force=args.force,
        release=args.release,
        curated=args.curated,
        changelog=args.changelog,
        gates_passed=gates_passed,
    )


def _register_render(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "render",
        help="Render vignettes.csv into prompts.jsonl (S2; WO-2 Part B).",
    )
    parser.add_argument("vignettes", help="Path to vignettes.csv")
    parser.add_argument("--out", required=True, help="Output path for prompts.jsonl")
    parser.add_argument(
        "--formats", default="raw,chat",
        help="Comma-separated prompt formats to render (raw,chat). Default: raw,chat.",
    )
    parser.set_defaults(func=_run_render)


def _run_render(args: argparse.Namespace) -> int:
    from knobe.render import run as run_render

    formats = tuple(f.strip() for f in args.formats.split(",") if f.strip())
    return run_render(args.vignettes, args.out, formats=formats)


def _register_jobs(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "jobs",
        help="Job-manifest construction + resume primitives (WO-2 Part C).",
    )
    jobs_subparsers = parser.add_subparsers(dest="jobs_command")

    build_parser = jobs_subparsers.add_parser(
        "build", help="Expand prompts.jsonl x a run config into jobs.jsonl.",
    )
    build_parser.add_argument("--config", required=True, help="Path to configs/run_*.yaml")
    build_parser.add_argument("--prompts", required=True, help="Path to prompts.jsonl")
    build_parser.add_argument("--out", required=True, help="Output path for jobs.jsonl")
    build_parser.set_defaults(func=_run_jobs_build)

    diff_parser = jobs_subparsers.add_parser(
        "diff",
        help="Remaining-work report: set-difference of jobs.jsonl vs results.jsonl by job_id.",
    )
    diff_parser.add_argument("--jobs", required=True, dest="jobs_path", help="Path to jobs.jsonl")
    diff_parser.add_argument(
        "--results", required=True, dest="results_path",
        help="Path to results.jsonl (missing/empty file means nothing done yet).",
    )
    diff_parser.add_argument(
        "--out", default=None,
        help="Optional path to write the remaining JobRecords as JSONL.",
    )
    diff_parser.set_defaults(func=_run_jobs_diff)

    def _run_jobs_no_subcommand(_args: argparse.Namespace) -> int:
        parser.print_help()
        return 1

    parser.set_defaults(func=_run_jobs_no_subcommand)


def _run_jobs_build(args: argparse.Namespace) -> int:
    from knobe.jobs import run_build

    return run_build(args.config, args.prompts, args.out)


def _run_jobs_diff(args: argparse.Namespace) -> int:
    from knobe.jobs import run_diff

    return run_diff(args.jobs_path, args.results_path, out_path=args.out)


def _register_curate(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "curate",
        help="Curation-stage elicitation + acceptance workflow (S3; WO-3).",
    )
    curate_subparsers = parser.add_subparsers(dest="curate_command")

    run_parser = curate_subparsers.add_parser(
        "run", help="Elicit curation ratings for every variant and assemble curated.csv.",
    )
    run_parser.add_argument("vignettes", help="Path to vignettes.csv")
    run_parser.add_argument(
        "--reviewer-model", required=True,
        help="Model string for the CURATION reviewer -- must not be a model you plan to "
             "test as a subject (checked automatically against configs/models.yaml).",
    )
    run_parser.add_argument(
        "--mock", action="store_true",
        help="Use a deterministic fake client -- zero network calls (G0 rehearsal).",
    )
    run_parser.add_argument("--out", default="curated.csv", help="Output path for curated.csv")
    run_parser.add_argument(
        "--raw", default="curated_raw.jsonl", dest="raw_out",
        help="Checkpoint path for per-job raw results (resumable: appended-to, "
             "completed jobs skipped on restart).",
    )
    run_parser.add_argument("--concurrency", type=int, default=8)
    run_parser.add_argument("--max-retries", type=int, default=3)
    run_parser.add_argument("--max-tokens", type=int, default=10)
    run_parser.add_argument("--limit", type=int, default=None, help="Only run the first N jobs.")
    run_parser.add_argument(
        "--shard", default=None, metavar="i/n",
        help="Only run this shard's jobs, e.g. --shard 0/4.",
    )
    run_parser.add_argument(
        "--report-dir", default="curation_reports",
        help="Directory for the distribution-check text report + PNG plots.",
    )
    run_parser.add_argument("--runlog", default=None, dest="runlog_path")
    run_parser.add_argument(
        "--registry", default=None, dest="registry_path",
        help="Path to configs/models.yaml (default: the repo's own).",
    )
    run_parser.add_argument(
        "--curation-config", default=None, dest="curation_config_path",
        help="Path to configs/curation.yaml (default: the repo's own).",
    )
    run_parser.add_argument(
        "--curation-date", default=None,
        help="ISO date recorded in curated.csv's curation_date column "
             "(default: today; pass explicitly for deterministic tests/reruns).",
    )
    run_parser.set_defaults(func=_run_curate_run)

    review_parser = curate_subparsers.add_parser(
        "review", help="Human acceptance workflow: review flagged items, write `accepted` in place.",
    )
    review_parser.add_argument("--curated", required=True, help="Path to curated.csv")
    review_parser.add_argument(
        "--accept-unflagged", action="store_true",
        help="Batch mode: accept every unflagged row non-interactively (scripted G0 runs).",
    )
    review_parser.set_defaults(func=_run_curate_review)

    def _run_curate_no_subcommand(_args: argparse.Namespace) -> int:
        parser.print_help()
        return 1

    parser.set_defaults(func=_run_curate_no_subcommand)


def _run_curate_run(args: argparse.Namespace) -> int:
    from knobe import curate

    shard = None
    if args.shard:
        i_str, _, n_str = args.shard.partition("/")
        try:
            shard = (int(i_str), int(n_str))
        except ValueError:
            print(f"ERROR: --shard must be 'i/n', e.g. 0/4; got {args.shard!r}", file=sys.stderr)
            return 1

    return curate.run(
        args.vignettes,
        reviewer_model=args.reviewer_model,
        mock=args.mock,
        out=args.out,
        raw_out=args.raw_out,
        concurrency=args.concurrency,
        max_retries=args.max_retries,
        max_tokens=args.max_tokens,
        limit=args.limit,
        shard=shard,
        report_dir=args.report_dir,
        runlog_path=args.runlog_path,
        registry_path=args.registry_path,
        curation_config_path=args.curation_config_path,
        curation_date=args.curation_date,
    )


def _run_curate_review(args: argparse.Namespace) -> int:
    from knobe.curate import review_curated

    return review_curated(args.curated, accept_unflagged=args.accept_unflagged)


def _register_elicit(subparsers: argparse._SubParsersAction) -> None:
    from knobe import elicit_vllm

    parser = subparsers.add_parser(
        "elicit",
        help="Behavioral elicitation runner: execute a jobs.jsonl manifest against a "
             "subject model (S5; WO-5).",
    )
    parser.add_argument("--jobs", required=True, dest="jobs_path", help="Path to jobs.jsonl")
    parser.add_argument("--prompts", required=True, dest="prompts_path", help="Path to prompts.jsonl")
    parser.add_argument(
        "--run-config", required=True, dest="run_config_path",
        help="Path to configs/run_*.yaml (the release string it names is manifest-guard-checked).",
    )
    parser.add_argument(
        "--engine", default="vllm", choices=sorted(("vllm", "hf", "fake")),
        help="Generation backend. 'fake' is deterministic and requires no GPU/model download "
             "(G0 rehearsal + this repo's test suite); 'hf' is a slow CPU-friendly fallback; "
             "'vllm' is the real H200 backend. Default: vllm.",
    )
    parser.add_argument("--out", default="results.jsonl", dest="out_path", help="Output path for results.jsonl")
    parser.add_argument(
        "--shard", default=None, metavar="i/n",
        help="Only run this shard's jobs (job_index %% n == i over jobs.jsonl's own order), "
             "e.g. --shard 0/4 for one process per GPU.",
    )
    parser.add_argument("--limit", type=int, default=None, help="Only run the first N remaining jobs.")
    parser.add_argument(
        "--storage", default=None, dest="storage_config_path",
        help="Path to configs/storage.yaml (default: no storage sync -- NullStorage).",
    )
    parser.add_argument(
        "--checkpoint-every", type=int, default=elicit_vllm.DEFAULT_CHECKPOINT_EVERY,
        help=f"Push the results shard to storage every N rows (default: "
             f"{elicit_vllm.DEFAULT_CHECKPOINT_EVERY}).",
    )
    parser.add_argument(
        "--batch-size", type=int, default=elicit_vllm.DEFAULT_BATCH_SIZE,
        help=f"Jobs per engine.generate() call (default: {elicit_vllm.DEFAULT_BATCH_SIZE}).",
    )
    parser.add_argument(
        "--report-every", type=int, default=elicit_vllm.DEFAULT_REPORT_EVERY_BATCHES,
        dest="report_every_batches",
        help="Print a throughput report every N batches (default: "
             f"{elicit_vllm.DEFAULT_REPORT_EVERY_BATCHES}).",
    )
    parser.add_argument(
        "--skip-manifest-check", action="store_true",
        help="Bypass the release manifest hash guard (spec §3.10). Only for a throwaway G0 "
             "toy run -- prominently logged when used.",
    )
    parser.add_argument(
        "--registry", default=None, dest="registry_path",
        help="Path to configs/models.yaml (default: the repo's own).",
    )
    parser.add_argument(
        "--release-root", default=None, dest="release_root",
        help="Directory containing <release>/manifest.json for the manifest guard "
             "(default: the repo's own data/release/). Needed when knobe is "
             "wheel-installed and the release dir ships alongside the job data.",
    )
    parser.add_argument(
        "--logit-fallback", default="", dest="logit_fallback",
        metavar="model_key[,model_key...]",
        help="Comma-separated model_keys whose measured regex parse rate fell below 95%% in "
             "a prior run (spec §4.4) -- enables expected-value scoring from logprobs for "
             "just those checkpoints.",
    )
    parser.add_argument("--dtype", default="bfloat16")
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.9)
    parser.add_argument(
        "--runlog", default=None, dest="runlog_path",
        help="Path for per-run throughput telemetry (default: alongside --out).",
    )
    parser.set_defaults(func=_run_elicit)


def _run_elicit(args: argparse.Namespace) -> int:
    from knobe import elicit_vllm

    shard = None
    if args.shard:
        i_str, _, n_str = args.shard.partition("/")
        try:
            shard = (int(i_str), int(n_str))
        except ValueError:
            print(f"ERROR: --shard must be 'i/n', e.g. 0/4; got {args.shard!r}", file=sys.stderr)
            return 1

    logit_fallback_checkpoints = [m.strip() for m in args.logit_fallback.split(",") if m.strip()]

    return elicit_vllm.run(
        jobs_path=args.jobs_path,
        prompts_path=args.prompts_path,
        run_config_path=args.run_config_path,
        out_path=args.out_path,
        engine_name=args.engine,
        shard=shard,
        limit=args.limit,
        storage_config_path=args.storage_config_path,
        checkpoint_every=args.checkpoint_every,
        batch_size=args.batch_size,
        report_every_batches=args.report_every_batches,
        skip_manifest_check=args.skip_manifest_check,
        release_root=args.release_root,
        registry_path=args.registry_path,
        logit_fallback_checkpoints=logit_fallback_checkpoints,
        dtype=args.dtype,
        gpu_memory_utilization=args.gpu_memory_utilization,
        runlog_path=args.runlog_path,
    )


def _parse_shard(shard_arg: str | None) -> tuple[int, int] | None:
    if not shard_arg:
        return None
    i_str, _, n_str = shard_arg.partition("/")
    return int(i_str), int(n_str)


def _parse_int_list(arg: str | None) -> list[int] | None:
    if not arg:
        return None
    return [int(x.strip()) for x in arg.split(",") if x.strip()]


def _parse_str_list(arg: str | None) -> list[str] | None:
    if not arg:
        return None
    return [x.strip() for x in arg.split(",") if x.strip()]


def _register_power(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "power",
        help="Pilot variance decomposition + simulation-based power determination (S4; WO-4).",
    )
    power_subparsers = parser.add_subparsers(dest="power_command")

    estimate_parser = power_subparsers.add_parser(
        "estimate",
        help="Fit variance components (random intercept for family + response-level residual) "
             "from a pilot results.jsonl/vignettes.csv for one subject model.",
    )
    estimate_parser.add_argument("--results", required=True, dest="results_path", help="Path to pilot results.jsonl")
    estimate_parser.add_argument("--vignettes", required=True, dest="vignettes_path", help="Path to vignettes.csv")
    estimate_parser.add_argument("--model-key", required=True, help="Subject model_key to fit (WO-4: per subject model).")
    estimate_parser.add_argument("--question", default="intentionality", choices=("intentionality", "blame", "praise", "affect_salience"))
    estimate_parser.add_argument(
        "--out", default="variance_components.jsonl",
        help="Checkpoint path (append-only; skips a model_key/question already present -- resume).",
    )
    estimate_parser.set_defaults(func=_run_power_estimate)

    simulate_parser = power_subparsers.add_parser(
        "simulate",
        help="Run (or resume) the simulation-based power grid for one subject model's variance components.",
    )
    simulate_parser.add_argument(
        "--variance-components", required=True, dest="variance_components_path",
        help="Path to the JSONL written by `knobe power estimate`.",
    )
    simulate_parser.add_argument("--model-key", required=True, help="Selects the VarianceComponents row to simulate from.")
    simulate_parser.add_argument("--config", default="configs/power.yaml", dest="config_path")
    simulate_parser.add_argument("--out", default="power_grid.jsonl", dest="out_path")
    simulate_parser.add_argument(
        "--pilot-results", default=None, dest="pilot_results_path",
        help="Path to pilot results.jsonl -- required iff the config has effect_sizes: null "
             "for a simulated contrast (derives the default: half the pilot MB-MG gap).",
    )
    simulate_parser.add_argument("--pilot-vignettes", default=None, dest="pilot_vignettes_path")
    simulate_parser.add_argument("--seed", type=int, default=None, help="Overrides configs/power.yaml's seed.")
    simulate_parser.add_argument("--item-counts", default=None, help="Comma-separated override, e.g. 15,25,40.")
    simulate_parser.add_argument("--response-ns", default=None, help="Comma-separated override, e.g. 5,10,15.")
    simulate_parser.add_argument("--n-sims", type=int, default=None, dest="n_sims", help="Overrides configs/power.yaml's n_sims.")
    simulate_parser.add_argument(
        "--contrasts", default=None,
        help="Comma-separated override, e.g. 1a,1d (default: config's contrasts list).",
    )
    simulate_parser.add_argument("--shard", default=None, metavar="i/n", help="Shard the grid-point list, e.g. --shard 0/4.")
    simulate_parser.add_argument("--limit", type=int, default=None, help="Only run the first N (post-shard) grid points.")
    simulate_parser.set_defaults(func=_run_power_simulate)

    report_parser = power_subparsers.add_parser(
        "report",
        help="Render power_report.md + PNG power curves (gate artifact for G2) from a simulation grid.",
    )
    report_parser.add_argument("--grid", required=True, dest="grid_path", help="Path to power_grid.jsonl")
    report_parser.add_argument(
        "--variance-components", required=True, dest="variance_components_path",
        help="Path to the JSONL written by `knobe power estimate` (reported alongside the curves).",
    )
    report_parser.add_argument("--out-dir", default="power_report", dest="out_dir")
    report_parser.set_defaults(func=_run_power_report)

    run_parser = power_subparsers.add_parser(
        "run",
        help="estimate -> simulate -> report in one call (each stage independently resumable).",
    )
    run_parser.add_argument("--pilot-results", required=True, dest="pilot_results_path")
    run_parser.add_argument("--pilot-vignettes", required=True, dest="pilot_vignettes_path")
    run_parser.add_argument("--model-key", required=True)
    run_parser.add_argument("--config", default="configs/power.yaml", dest="config_path")
    run_parser.add_argument("--variance-components", default="variance_components.jsonl", dest="variance_components_path")
    run_parser.add_argument("--grid", default="power_grid.jsonl", dest="grid_path")
    run_parser.add_argument("--report-dir", default="power_report", dest="report_dir")
    run_parser.add_argument(
        "--question", default=None, choices=("intentionality", "blame", "praise", "affect_salience"),
        help="Default: configs/power.yaml's pilot.question (usually 'intentionality').",
    )
    run_parser.add_argument("--seed", type=int, default=None)
    run_parser.add_argument("--item-counts", default=None)
    run_parser.add_argument("--response-ns", default=None)
    run_parser.add_argument("--n-sims", type=int, default=None, dest="n_sims")
    run_parser.add_argument("--contrasts", default=None)
    run_parser.add_argument("--shard", default=None, metavar="i/n")
    run_parser.add_argument("--limit", type=int, default=None)
    run_parser.set_defaults(func=_run_power_run)

    def _run_power_no_subcommand(_args: argparse.Namespace) -> int:
        parser.print_help()
        return 1

    parser.set_defaults(func=_run_power_no_subcommand)


def _run_power_estimate(args: argparse.Namespace) -> int:
    from knobe.power import run_estimate

    return run_estimate(
        args.results_path, args.vignettes_path,
        model_key=args.model_key, question=args.question, out_path=args.out,
    )


def _run_power_simulate(args: argparse.Namespace) -> int:
    from knobe.power import run_simulate

    try:
        shard = _parse_shard(args.shard)
    except ValueError:
        print(f"ERROR: --shard must be 'i/n', e.g. 0/4; got {args.shard!r}", file=sys.stderr)
        return 1

    return run_simulate(
        variance_components_path=args.variance_components_path,
        model_key=args.model_key,
        config_path=args.config_path,
        out_path=args.out_path,
        pilot_results_path=args.pilot_results_path,
        pilot_vignettes_path=args.pilot_vignettes_path,
        seed=args.seed,
        item_counts=_parse_int_list(args.item_counts),
        response_ns=_parse_int_list(args.response_ns),
        n_sims=args.n_sims,
        contrasts=_parse_str_list(args.contrasts),
        shard=shard,
        limit=args.limit,
    )


def _run_power_report(args: argparse.Namespace) -> int:
    from knobe.power import run_report

    return run_report(args.grid_path, args.variance_components_path, args.out_dir)


def _run_power_run(args: argparse.Namespace) -> int:
    from knobe.power import run_pipeline

    try:
        shard = _parse_shard(args.shard)
    except ValueError:
        print(f"ERROR: --shard must be 'i/n', e.g. 0/4; got {args.shard!r}", file=sys.stderr)
        return 1

    return run_pipeline(
        pilot_results_path=args.pilot_results_path,
        pilot_vignettes_path=args.pilot_vignettes_path,
        model_key=args.model_key,
        config_path=args.config_path,
        variance_components_path=args.variance_components_path,
        grid_path=args.grid_path,
        report_dir=args.report_dir,
        question=args.question,
        seed=args.seed,
        item_counts=_parse_int_list(args.item_counts),
        response_ns=_parse_int_list(args.response_ns),
        n_sims=args.n_sims,
        contrasts=_parse_str_list(args.contrasts),
        shard=shard,
        limit=args.limit,
    )


# User-facing `knobe mech --backend` choices, defined once (not duplicated
# per parser). Kept as a literal here rather than imported from
# knobe.mech.cache_acts so the CLI startup stays lazy -- that module pulls in
# pandas/numpy/elicit_vllm, which must not load for unrelated subcommands.
# knobe.mech.cache_acts.BACKEND_CHOICES is the authoritative copy; these must
# agree (both are just the four backend names).
_MECH_BACKEND_CHOICES = ("fake", "tl", "nnsight", "auto")


def _register_mech(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "mech",
        help="Mechanistic interp: activation caching + δ_l, and pretrained→finetuned "
             "layer patching (S6; WO-6).",
    )
    mech_subparsers = parser.add_subparsers(dest="mech_command")

    cache_parser = mech_subparsers.add_parser(
        "cache",
        help="Cache final-token residuals (all layers) for a checkpoint + compute δ_l "
             "contrasts (spec §3.7, §5.3).",
    )
    cache_parser.add_argument("--release", required=True, metavar="vX.Y")
    cache_parser.add_argument("--model-key", required=True, help="e.g. gemma-2-2b-instruct")
    cache_parser.add_argument(
        "--backend", default="auto", choices=_MECH_BACKEND_CHOICES,
        help="Residual backend. 'fake' is deterministic + GPU-free (plumbing rehearsal + tests); "
             "'auto' picks per the registry's mech_backend field. Default: auto.",
    )
    cache_parser.add_argument("--prompts", required=True, dest="prompts_path", help="Path to prompts.jsonl")
    cache_parser.add_argument("--vignettes", required=True, dest="vignettes_path", help="Path to vignettes.csv")
    cache_parser.add_argument("--out-root", default="results", dest="out_root")
    cache_parser.add_argument("--registry", default=None, dest="registry_path")
    cache_parser.add_argument("--limit", type=int, default=None)
    cache_parser.add_argument("--shard", default=None, metavar="i/n")
    cache_parser.add_argument("--force", action="store_true", help="Recompute even if a complete cache exists.")
    cache_parser.add_argument(
        "--merge-shards", action="store_true", dest="merge_shards",
        help="Merge previously-written shard_i_of_n/ sub-caches for --model-key/--release "
             "into the top-level final_token_resid.safetensors + index.json that probes "
             "consumes (validates the shard set is complete + disjoint). Skips caching.",
    )
    cache_parser.add_argument(
        "--storage", default=None, dest="storage_config_path",
        help="Path to configs/storage.yaml -- push the cache + summary artifacts to the "
             "configured backend (spec §1.1 durability). Default: no push.",
    )
    cache_parser.set_defaults(func=_run_mech_cache)

    patch_parser = mech_subparsers.add_parser(
        "patch",
        help="Patch pretrained residuals into the finetuned model per layer + metrics "
             "(spec §3.8, §5.2-5.3).",
    )
    patch_parser.add_argument("--release", required=True, metavar="vX.Y")
    patch_parser.add_argument("--family", required=True, help="Registry family, e.g. gemma-2-2b")
    patch_parser.add_argument(
        "--backend", default="auto", choices=_MECH_BACKEND_CHOICES,
    )
    patch_parser.add_argument("--prompts", required=True, dest="prompts_path")
    patch_parser.add_argument("--vignettes", required=True, dest="vignettes_path")
    patch_parser.add_argument(
        "--layers", default="sweep", dest="layers_spec",
        help="'sweep' (each layer, default), 'top-k:K' (from a prior sweep's patch_metrics), "
             "or explicit '3,7,11' (one joint multi-layer config).",
    )
    patch_parser.add_argument("--out-root", default="results", dest="out_root")
    patch_parser.add_argument("--registry", default=None, dest="registry_path")
    patch_parser.add_argument("--limit", type=int, default=None)
    patch_parser.add_argument(
        "--shard", default=None, metavar="i/n",
        help="Single-process prompt subsetting ONLY. Do NOT use to parallelize a sweep across "
             "processes: every shard writes the same layer_<tag>.jsonl paths and would clobber. "
             "Parallelize by --layers instead (distinct filenames per config).",
    )
    patch_parser.add_argument(
        "--force", action="store_true",
        help="Recompute every config even if a complete layer_<tag>.jsonl already exists "
             "(default: resume -- skip complete configs, recompute incomplete ones).",
    )
    patch_parser.add_argument(
        "--storage", default=None, dest="storage_config_path",
        help="Path to configs/storage.yaml -- push each config's jsonl + patch_metrics.parquet "
             "to the configured backend (spec §1.1 durability). Default: no push.",
    )
    patch_parser.set_defaults(func=_run_mech_patch)

    probes_parser = mech_subparsers.add_parser(
        "probes",
        help="Train per-layer linear probes per construct (§3.9) + RQ2 localization "
             "(leakage-controlled by scaffold split; residualized; WO-7).",
    )
    probes_parser.add_argument("--release", required=True, metavar="vX.Y")
    probes_parser.add_argument("--model-key", required=True, help="e.g. gemma-2-2b-instruct")
    probes_parser.add_argument(
        "--acts", required=True, dest="acts_dir",
        help="Path to the acts/<model_key>/ cache directory (safetensors + index.json).",
    )
    probes_parser.add_argument("--vignettes", required=True, dest="vignettes_path")
    probes_parser.add_argument(
        "--curated", default=None, dest="curated_path",
        help="Path to curated.csv (curation ratings; enables severity/vividness/"
             "typicality_perception ridge probes).",
    )
    probes_parser.add_argument(
        "--results", default=None, dest="results_path",
        help="Path to a raw-format results.jsonl (behavioral means; enables the "
             "blame/intentionality ridge probes -- skipped gracefully if absent).",
    )
    probes_parser.add_argument("--out-root", default="results", dest="out_root")
    probes_parser.add_argument("--test-frac", type=float, default=0.25)
    probes_parser.add_argument("--seed", type=int, default=0)
    probes_parser.add_argument("--n-boot", type=int, default=200, dest="n_boot")
    probes_parser.set_defaults(func=_run_mech_probes)

    decompose_parser = mech_subparsers.add_parser(
        "decompose",
        help="RQ3 patch decomposition + RQ4 probe alignment report from patch metrics "
             "+ probes (WO-7).",
    )
    decompose_parser.add_argument("--release", required=True, metavar="vX.Y")
    decompose_parser.add_argument("--model-key", required=True)
    decompose_parser.add_argument(
        "--patch-metrics", default=None, dest="patch_metrics_path",
        help="Path to a patch_metrics.parquet (RQ3 decomposition table + figure).",
    )
    decompose_parser.add_argument("--out-root", default="results", dest="out_root")
    decompose_parser.set_defaults(func=_run_mech_decompose)

    def _run_mech_no_subcommand(_args: argparse.Namespace) -> int:
        parser.print_help()
        return 1

    parser.set_defaults(func=_run_mech_no_subcommand)


def _run_mech_cache(args: argparse.Namespace) -> int:
    from knobe.mech.cache_acts import run_cache, run_merge_shards

    if getattr(args, "merge_shards", False):
        try:
            return run_merge_shards(
                release=args.release,
                model_key=args.model_key,
                out_root=args.out_root,
                force=args.force,
                storage_config_path=args.storage_config_path,
            )
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1

    try:
        shard = _parse_shard(args.shard)
    except ValueError:
        print(f"ERROR: --shard must be 'i/n', e.g. 0/4; got {args.shard!r}", file=sys.stderr)
        return 1
    return run_cache(
        release=args.release,
        model_key=args.model_key,
        backend_name=args.backend,
        prompts_path=args.prompts_path,
        vignettes_path=args.vignettes_path,
        out_root=args.out_root,
        registry_path=args.registry_path,
        limit=args.limit,
        shard=shard,
        force=args.force,
        storage_config_path=args.storage_config_path,
    )


def _run_mech_patch(args: argparse.Namespace) -> int:
    from knobe.mech.patch import run_patch

    try:
        shard = _parse_shard(args.shard)
    except ValueError:
        print(f"ERROR: --shard must be 'i/n', e.g. 0/4; got {args.shard!r}", file=sys.stderr)
        return 1
    return run_patch(
        release=args.release,
        family=args.family,
        backend_name=args.backend,
        prompts_path=args.prompts_path,
        vignettes_path=args.vignettes_path,
        layers_spec=args.layers_spec,
        out_root=args.out_root,
        registry_path=args.registry_path,
        limit=args.limit,
        shard=shard,
        force=args.force,
        storage_config_path=args.storage_config_path,
    )


def _run_mech_probes(args: argparse.Namespace) -> int:
    from knobe.mech.probes import run_probes

    return run_probes(
        release=args.release,
        model_key=args.model_key,
        acts_dir=args.acts_dir,
        vignettes_path=args.vignettes_path,
        curated_path=args.curated_path,
        results_path=args.results_path,
        out_root=args.out_root,
        test_frac=args.test_frac,
        seed=args.seed,
        n_boot=args.n_boot,
    )


def _run_mech_decompose(args: argparse.Namespace) -> int:
    from knobe.mech.decompose import run_decompose

    return run_decompose(
        release=args.release,
        model_key=args.model_key,
        patch_metrics_path=args.patch_metrics_path,
        out_root=args.out_root,
    )


def _register_analyze(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "analyze",
        help="S8 behavioral analysis: ingest -> RQ1 mixed models (contrasts.yaml "
             "prereg) -> figures -> paper report (WO-8).",
    )
    parser.add_argument(
        "--results", required=True, nargs="+", dest="results_paths",
        help="One or more results.jsonl shards (space-separated).",
    )
    parser.add_argument(
        "--release", default=None,
        help="Release label (also resolves vignettes from data/release/<release>/vignettes.csv "
             "when --vignettes is omitted; a dir or .csv path is also accepted).",
    )
    parser.add_argument(
        "--vignettes", default=None, dest="vignettes_path",
        help="Path to the release vignettes.csv (overrides --release resolution).",
    )
    parser.add_argument("--curated", default=None, dest="curated_path", help="Path to curated.csv (optional).")
    parser.add_argument("--jobs", default=None, dest="jobs_path", help="Path to jobs.jsonl (row-count validation).")
    parser.add_argument("--out-dir", required=True, dest="out_dir", help="Output directory for paper artifacts.")
    parser.add_argument(
        "--contrasts", default=None, dest="contrasts_path",
        help="Path to contrasts.yaml (default: the repo's own configs/contrasts.yaml).",
    )
    parser.add_argument(
        "--contrast-names", default=None,
        help="Comma-separated subset of declared contrasts to fit (default: all). An "
             "undeclared name is a hard error (contrasts.yaml governance).",
    )
    parser.add_argument("--registry", default=None, dest="registry_path", help="Path to configs/models.yaml.")
    parser.add_argument("--seed", type=int, default=0, help="Base seed for the cluster-bootstrap CIs.")
    parser.add_argument("--n-boot", type=int, default=200, dest="n_boot", help="Bootstrap resamples per contrast CI.")
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--no-figures", action="store_true", help="Skip figure generation.")
    parser.add_argument(
        "--domain-sensitivity", action="store_true", dest="domain_sensitivity",
        help="Also run the domain-cluster (intercept) sensitivity fit (groups=domain) -- the "
             "secondary check (the primary LMM models family clustering only).",
    )
    parser.add_argument(
        "--set-sensitivity", action="store_true", dest="set_sensitivity",
        help="Also run the set-cluster sensitivity fit (groups=set_id, the shared-storyline "
             "valence-sibling set) -- v1.1 proposal for RQ1a's between-family power problem, "
             "not yet a confirmed primary spec. See NEXT_RUN_ACTION_ITEMS.md.",
    )
    parser.add_argument(
        "--domain-slope-sensitivity", action="store_true", dest="domain_slope_sensitivity",
        help="Also run the DECLARED domain-random-slope sensitivity analysis (contrasts.yaml "
             "sensitivity_analyses.domain_random_slope) with its QUALIFIED/UNQUALIFIED rule -- "
             "master spec §6's 'domain = random effect' intent (researcher decision 2026-07-28).",
    )
    parser.add_argument(
        "--chat-comparison", action="store_true", dest="chat_comparison",
        help="Also run the chat-vs-raw format robustness comparison (WO-8 §4; off by default).",
    )
    parser.add_argument(
        "--exclude-flagged", action="store_true", dest="exclude_flagged",
        help="Re-analysis toggle (v1.1 proposal): drop any variant with a nonempty "
             "individual_flags/pair_flag curation flag from the SAME already-collected "
             "results (no re-elicitation needed). Run once with this off and once with "
             "it on to compare against the 'accept despite flags' release decision.",
    )
    parser.add_argument(
        "--logit-fallback", default="", dest="logit_fallback",
        metavar="model_key[,model_key...]",
        help="Comma-separated model_keys whose measured regex parse rate fell below 95%% "
             "(spec §4.4): ALL their rows are scored as the softmax-EV over logprobs_0_10 "
             "(score_source='logit_ev') instead of the parsed rating.",
    )
    parser.set_defaults(func=_run_analyze)


def _resolve_vignettes(release: str | None, vignettes: str | None) -> str | None:
    if vignettes:
        return vignettes
    if not release:
        return None
    from pathlib import Path

    p = Path(release)
    if p.is_dir():
        return str(p / "vignettes.csv")
    if p.suffix == ".csv":
        return str(p)
    repo_root = Path(__file__).resolve().parents[2]
    return str(repo_root / "data" / "release" / release / "vignettes.csv")


def _run_analyze(args: argparse.Namespace) -> int:
    from knobe.analysis.models import UndeclaredContrastError, UndeclaredSensitivityError
    from knobe.analysis.report import run_analyze

    vignettes_path = _resolve_vignettes(args.release, args.vignettes_path)
    if not vignettes_path:
        print("ERROR: pass --vignettes or a --release that resolves to a vignettes.csv.", file=sys.stderr)
        return 1

    try:
        return run_analyze(
            results_paths=args.results_paths,
            vignettes_path=vignettes_path,
            out_dir=args.out_dir,
            curated_path=args.curated_path,
            jobs_path=args.jobs_path,
            registry_path=args.registry_path,
            contrasts_path=args.contrasts_path,
            release=args.release or "unknown",
            contrast_names=_parse_str_list(args.contrast_names),
            base_seed=args.seed,
            n_boot=args.n_boot,
            alpha=args.alpha,
            make_figures=not args.no_figures,
            domain_sensitivity=args.domain_sensitivity,
            set_sensitivity=args.set_sensitivity,
            domain_slope_sensitivity=args.domain_slope_sensitivity,
            chat_comparison=args.chat_comparison,
            logit_fallback_checkpoints=_parse_str_list(args.logit_fallback) or (),
            exclude_flagged=args.exclude_flagged,
        )
    except (UndeclaredContrastError, UndeclaredSensitivityError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


def _register_generate(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "generate",
        help="Generation tooling: next-prompt/ingest/approve/status/qa (S1; WO-1).",
    )
    gen_subparsers = parser.add_subparsers(dest="generate_command")

    np_parser = gen_subparsers.add_parser(
        "next-prompt", help="Emit the next per-set generation prompt (GS §8.2) for a domain.",
    )
    np_parser.add_argument("--domain", required=True, help="Domain code, e.g. ENV (see constants.DOMAIN_CODES).")
    np_parser.add_argument(
        "--matrix", default=None,
        help="Path to master_matrix.csv (default: data/authoring/ALL_DOMAINS_master_matrix.csv).",
    )
    np_parser.add_argument(
        "--allow-extra", action="store_true",
        help="Allow generating beyond the 5-sets-per-domain end-state target.",
    )
    np_parser.add_argument(
        "--show-system", action="store_true",
        help="Also print GENERATION_SYSTEM_PROMPT (GS §8.1) to install as the session/system prompt.",
    )
    np_parser.set_defaults(func=_run_generate_next_prompt)

    ingest_parser = gen_subparsers.add_parser(
        "ingest", help="Validate and merge a returned 5-family set CSV into the authoring matrix.",
    )
    ingest_parser.add_argument("set_csv", help="Path to the returned set CSV (5 families, one storyline).")
    ingest_parser.add_argument("--matrix", default=None)
    ingest_parser.add_argument(
        "--generator-model", default="", help="Provenance: the model that generated this set.",
    )
    ingest_parser.add_argument(
        "--date", default=None,
        help="ISO date for the ingest_date provenance column (default: today; pass explicitly "
             "for deterministic tests/reproducible runs).",
    )
    ingest_parser.set_defaults(func=_run_generate_ingest)

    approve_parser = gen_subparsers.add_parser(
        "approve", help="Flip human_approved=True for named families or a whole set.",
    )
    approve_parser.add_argument("family_ids", nargs="*", help="family_id(s) to approve.")
    approve_parser.add_argument("--matrix", default=None)
    approve_parser.add_argument(
        "--set", nargs=2, metavar=("DOMAIN", "NN"), default=None,
        help="Approve a whole set at once, e.g. --set ENV 06.",
    )
    approve_parser.set_defaults(func=_run_generate_approve)

    status_parser = gen_subparsers.add_parser(
        "status",
        help="Dashboard: domain x valence grid, subdomain balance, approval backlog, agent diversity.",
    )
    status_parser.add_argument("--matrix", default=None)
    status_parser.set_defaults(func=_run_generate_status)

    qa_parser = gen_subparsers.add_parser(
        "qa", help="Emit the periodic batch-QA prompt (GS §8.3) for a domain.",
    )
    qa_parser.add_argument("--domain", required=True)
    qa_parser.add_argument("--matrix", default=None)
    qa_parser.set_defaults(func=_run_generate_qa)

    def _run_generate_no_subcommand(_args: argparse.Namespace) -> int:
        parser.print_help()
        return 1

    parser.set_defaults(func=_run_generate_no_subcommand)


def _resolve_matrix(args: argparse.Namespace):
    from knobe.generate import default_matrix_path

    return args.matrix or default_matrix_path()


def _run_generate_next_prompt(args: argparse.Namespace) -> int:
    from knobe import constants
    from knobe.generate import DomainAtCapError, next_prompt_text

    print(
        "REMINDER: install GENERATION_SYSTEM_PROMPT (GS §8.1) as the session/system prompt "
        "before sending the block below -- it is not repeated in this output unless "
        "--show-system is passed.",
        file=sys.stderr,
    )
    if args.show_system:
        print("===== SYSTEM PROMPT (GS §8.1; install once per session) =====")
        print(constants.GENERATION_SYSTEM_PROMPT)
        print("===== END SYSTEM PROMPT =====\n")

    try:
        prompt = next_prompt_text(_resolve_matrix(args), args.domain, allow_extra=args.allow_extra)
    except (ValueError, DomainAtCapError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(prompt)
    return 0


def _run_generate_ingest(args: argparse.Namespace) -> int:
    from knobe.generate import ingest

    result = ingest(
        args.set_csv, _resolve_matrix(args), generator_model=args.generator_model, date=args.date,
    )
    for w in result.warnings:
        print(f"WARNING: {w}")
    if not result.ok:
        print(f"{len(result.errors)} ERROR(S) -- nothing written:")
        for e in result.errors:
            print(f" - {e}")
        return 1
    print(f"Ingested {len(result.appended_family_ids)} families: {result.appended_family_ids}")
    return 0


def _run_generate_approve(args: argparse.Namespace) -> int:
    from knobe.generate import approve

    try:
        matched, missing = approve(
            _resolve_matrix(args), family_ids=args.family_ids, set_selector=args.set,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Approved {len(matched)} families: {sorted(matched)}")
    if missing:
        print(f"WARNING: not found in matrix, skipped: {sorted(missing)}", file=sys.stderr)
    return 0


def _run_generate_status(args: argparse.Namespace) -> int:
    from knobe.generate import format_status, status

    print(format_status(status(_resolve_matrix(args))))
    return 0


def _run_generate_qa(args: argparse.Namespace) -> int:
    from knobe.generate import qa_prompt

    try:
        prompt = qa_prompt(_resolve_matrix(args), args.domain)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(prompt)
    return 0


# Every subcommand registers one entry here: name -> a function that adds
# its own subparser (and wires up its own `func` via set_defaults). Later
# work orders append to this table; nothing else in this file needs to
# change to support a new subcommand.
SUBCOMMANDS: dict[str, SubcommandRegistrar] = {
    "version": _register_version,
    "assemble": _register_assemble,
    "render": _register_render,
    "jobs": _register_jobs,
    "generate": _register_generate,
    "curate": _register_curate,
    "elicit": _register_elicit,
    "power": _register_power,
    "mech": _register_mech,
    "analyze": _register_analyze,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="knobe", description=__doc__)
    subparsers = parser.add_subparsers(dest="command")
    for register in SUBCOMMANDS.values():
        register(subparsers)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
