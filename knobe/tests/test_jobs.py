"""Tests for src/knobe/jobs.py (WO-2 Part C).

Acceptance criteria under test (task-2-brief.md):
  - RunConfig loads configs/run_*.yaml.
  - Seeding rule (spec §3.5, EXACT) pinned against 3 hand-computed
    fixtures (see TestSeedingFixtures's docstring for the independent
    derivation snippet).
  - With N=3, 2 models, formats=[raw], on the 24-raw-prompt 2-family toy
    matrix -> exactly 144 raw jobs.
  - jobs.jsonl byte-identical across two builds from the same inputs.
  - `knobe jobs diff` resume semantics: empty results, partial results,
    full results; tolerates a missing/empty results file.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from knobe import cli, jobs
from knobe.schemas import JobRecord, PromptRecord, ResultRecord, sha256_for_text, write_jsonl

REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_EXAMPLE_YAML = REPO_ROOT / "configs" / "run_example.yaml"


def _prompt(prompt_id: str, variant_id: str, question_type: str, fmt: str, text: str = "x") -> PromptRecord:
    if fmt == "chat":
        messages = [{"role": "user", "content": text}]
        from knobe.schemas import sha256_for_messages

        return PromptRecord(
            prompt_id=prompt_id, variant_id=variant_id, question_type=question_type,
            format=fmt, text=text, messages=messages, sha256=sha256_for_messages(messages),
        )
    return PromptRecord(
        prompt_id=prompt_id, variant_id=variant_id, question_type=question_type,
        format=fmt, text=text, messages=None, sha256=sha256_for_text(text),
    )


def _toy_prompts_24_raw_24_chat() -> list[PromptRecord]:
    """8 variants x 3 questions x 2 formats -- exactly what render.py's
    toy-matrix acceptance test produces (kept independent of render.py so
    jobs.py's tests don't depend on that module)."""
    variants = [f"TST-{v}-01-{letter}" for v in ("MB", "MG") for letter in "ABCD"]
    questions = ("intentionality", "blame", "praise")
    formats = ("raw", "chat")
    prompts = []
    for variant_id in variants:
        for qtype in questions:
            for fmt in formats:
                prompt_id = f"{variant_id}::{qtype}::{fmt}"
                prompts.append(_prompt(prompt_id, variant_id, qtype, fmt, text=f"text for {prompt_id}"))
    return prompts


def _job(job_id: str, prompt_id: str = "p", model_key: str = "m", sample_idx: int = 0) -> JobRecord:
    return JobRecord(
        job_id=job_id, prompt_id=prompt_id, model_key=model_key,
        sample_idx=sample_idx, temperature=1.0, seed=1,
    )


def _result(job_id: str, **overrides) -> ResultRecord:
    kwargs = dict(
        job_id=job_id, prompt_id="p", model_key="m", sample_idx=0,
        temperature=1.0, seed=1, raw_response="7", parsed_rating=7,
        parse_ok=True, parse_method="regex", model_revision="abc",
        runner_version="0.1.0", timestamp=1.0,
    )
    kwargs.update(overrides)
    return ResultRecord(**kwargs)


# ---------------------------------------------------------------------------
# RunConfig
# ---------------------------------------------------------------------------


class TestRunConfig:
    def test_loads_real_run_example_yaml(self):
        config = jobs.load_run_config(RUN_EXAMPLE_YAML)
        assert config.release == "v1.0"
        assert "llama-3.1-8b-instruct" in config.models
        assert config.formats == ["raw"]
        assert config.n_samples == 5
        assert config.questions == ["intentionality", "blame", "praise"]

    def test_questions_default_all_three_when_omitted(self, tmp_path):
        path = tmp_path / "run.yaml"
        path.write_text(yaml.safe_dump({
            "release": "v0.1", "models": ["m-instruct"], "formats": ["raw"], "n_samples": 1,
        }))
        config = jobs.load_run_config(path)
        assert config.questions == ["intentionality", "blame", "praise"]

    def test_explicit_questions_subset_respected(self, tmp_path):
        path = tmp_path / "run.yaml"
        path.write_text(yaml.safe_dump({
            "release": "v0.1", "models": ["m-instruct"], "formats": ["raw"],
            "n_samples": 1, "questions": ["blame"],
        }))
        config = jobs.load_run_config(path)
        assert config.questions == ["blame"]

    def test_bad_format_literal_rejected(self, tmp_path):
        path = tmp_path / "run.yaml"
        path.write_text(yaml.safe_dump({
            "release": "v0.1", "models": ["m-instruct"], "formats": ["bogus"], "n_samples": 1,
        }))
        with pytest.raises(ValidationError):
            jobs.load_run_config(path)

    def test_unknown_field_rejected(self, tmp_path):
        path = tmp_path / "run.yaml"
        path.write_text(yaml.safe_dump({
            "release": "v0.1", "models": ["m-instruct"], "formats": ["raw"],
            "n_samples": 1, "bogus_field": "x",
        }))
        with pytest.raises(ValidationError):
            jobs.load_run_config(path)


# ---------------------------------------------------------------------------
# Seeding rule -- exact fixtures (spec §3.5)
# ---------------------------------------------------------------------------


class TestSeedingFixtures:
    """Pins spec §3.5's seeding derivation with 3 fixtures computed
    INDEPENDENTLY of jobs.py -- via the standalone snippet below, run by
    hand outside this repo, with its printed output transcribed as the
    literals in each test. This must never be "fixed" by running
    jobs.derive_temperature_and_seed() and pasting its output back here;
    that would let a silent derivation change go undetected, defeating the
    whole point of pinning it.

        import hashlib

        def derive(release, prompt_id, model_key, sample_idx):
            material = f"{release}|{prompt_id}|{model_key}|{sample_idx}".encode("utf-8")
            digest = hashlib.sha256(material).digest()
            u = int.from_bytes(digest[0:8], "big") / 2**64
            temperature = 0.85 + 0.30 * u
            seed = int.from_bytes(digest[8:16], "big") % 2**31
            return digest.hex(), temperature, seed

        derive("v1.0", "ENV-MB-01-A::intentionality::raw",
               "llama-3.1-8b-instruct", 0)
        # -> digest 2a7c163b30cb26b7834ff4f5c623531d37d1e96efd4df17f839d4d9ad59ffd73
        #    temperature 0.8997867744781961, seed 1176720157

        derive("v1.0", "ENV-MB-01-A::blame::raw",
               "llama-3.1-8b-instruct", 5)
        # -> digest 554f4bda5a8a99089b183e78d27b7456e7012068841b881870d9776b9954c02d
        #    temperature 0.9499723646571169, seed 1383822422

        derive("v0.9", "TST-MG-02-D::praise::chat",
               "mistral-7b-v0.1-pretrained", 17)
        # -> digest 1e7cadd49b8867391a2cb8f70ef60771ec92b56427c01d02687e3ad467ea11ab
        #    temperature 0.8857269852846547, seed 251004785
    """

    def test_fixture_1(self):
        temperature, seed = jobs.derive_temperature_and_seed(
            "v1.0", "ENV-MB-01-A::intentionality::raw", "llama-3.1-8b-instruct", 0,
        )
        assert temperature == 0.8997867744781961
        assert seed == 1176720157

    def test_fixture_2(self):
        temperature, seed = jobs.derive_temperature_and_seed(
            "v1.0", "ENV-MB-01-A::blame::raw", "llama-3.1-8b-instruct", 5,
        )
        assert temperature == 0.9499723646571169
        assert seed == 1383822422

    def test_fixture_3(self):
        temperature, seed = jobs.derive_temperature_and_seed(
            "v0.9", "TST-MG-02-D::praise::chat", "mistral-7b-v0.1-pretrained", 17,
        )
        assert temperature == 0.8857269852846547
        assert seed == 251004785

    def test_temperature_always_in_u_0_85_1_15(self):
        # Sweep a handful of distinct inputs; temperature must always land
        # in [0.85, 1.15) since fraction in digest[0:8] is a proper
        # fraction of 2**64.
        for i in range(50):
            temperature, seed = jobs.derive_temperature_and_seed("v1.0", f"p-{i}", "m-instruct", i)
            assert 0.85 <= temperature < 1.15
            assert 0 <= seed < 2**31

    def test_deterministic_pure_function_of_its_four_inputs(self):
        args = ("v1.0", "ENV-MB-01-A::intentionality::raw", "llama-3.1-8b-instruct", 0)
        assert jobs.derive_temperature_and_seed(*args) == jobs.derive_temperature_and_seed(*args)

    def test_changing_any_one_input_changes_the_derivation(self):
        base = jobs.derive_temperature_and_seed("v1.0", "p1", "m-instruct", 0)
        assert jobs.derive_temperature_and_seed("v1.1", "p1", "m-instruct", 0) != base
        assert jobs.derive_temperature_and_seed("v1.0", "p2", "m-instruct", 0) != base
        assert jobs.derive_temperature_and_seed("v1.0", "p1", "m-pretrained", 0) != base
        assert jobs.derive_temperature_and_seed("v1.0", "p1", "m-instruct", 1) != base


# ---------------------------------------------------------------------------
# build_jobs: toy-matrix acceptance criterion + determinism
# ---------------------------------------------------------------------------


class TestBuildJobsToyMatrix:
    def test_144_raw_jobs_with_n3_two_models_raw_only(self):
        prompts = _toy_prompts_24_raw_24_chat()
        raw_prompts = [p for p in prompts if p.format == "raw"]
        assert len(raw_prompts) == 24

        built = jobs.build_jobs(
            prompts, release="v1.0", models=["model-a", "model-b"],
            formats=["raw"], n_samples=3,
        )
        assert len(built) == 144  # 24 raw prompts x 2 models x 3 samples

    def test_job_id_shape(self):
        prompts = _toy_prompts_24_raw_24_chat()
        built = jobs.build_jobs(prompts, release="v1.0", models=["model-a"], formats=["raw"], n_samples=2)
        for job in built:
            assert job.job_id == f"{job.prompt_id}::{job.model_key}::{job.sample_idx}"

    def test_formats_filter_excludes_chat_when_only_raw_requested(self):
        prompts = _toy_prompts_24_raw_24_chat()
        built = jobs.build_jobs(prompts, release="v1.0", models=["m"], formats=["raw"], n_samples=1)
        chat_ids = {p.prompt_id for p in prompts if p.format == "chat"}
        assert not any(j.prompt_id in chat_ids for j in built)

    def test_questions_filter_restricts_to_named_questions(self):
        prompts = _toy_prompts_24_raw_24_chat()
        built = jobs.build_jobs(
            prompts, release="v1.0", models=["m"], formats=["raw"],
            questions=["blame"], n_samples=1,
        )
        assert len(built) == 8  # 8 variants x 1 question x 1 format x 1 model x 1 sample
        assert all("::blame::" in j.prompt_id for j in built)

    def test_sample_idx_range_and_uniqueness(self):
        prompts = _toy_prompts_24_raw_24_chat()[:2]  # 2 raw+chat prompt pairs -> filter to raw below
        raw_only = [p for p in prompts if p.format == "raw"]
        built = jobs.build_jobs(raw_only, release="v1.0", models=["m"], formats=["raw"], n_samples=4)
        sample_idxs = sorted(j.sample_idx for j in built)
        assert sample_idxs == [0, 1, 2, 3]
        assert len({j.job_id for j in built}) == len(built)  # all unique

    def test_temperature_and_seed_match_derive_function(self):
        prompts = _toy_prompts_24_raw_24_chat()
        built = jobs.build_jobs(prompts, release="v1.0", models=["model-a"], formats=["raw"], n_samples=1)
        for job in built:
            expected_temp, expected_seed = jobs.derive_temperature_and_seed(
                "v1.0", job.prompt_id, job.model_key, job.sample_idx,
            )
            assert job.temperature == expected_temp
            assert job.seed == expected_seed


class TestBuildJobsDeterminism:
    def test_double_build_produces_equal_job_lists(self):
        prompts = _toy_prompts_24_raw_24_chat()
        built1 = jobs.build_jobs(prompts, release="v1.0", models=["a", "b"], formats=["raw"], n_samples=3)
        built2 = jobs.build_jobs(prompts, release="v1.0", models=["a", "b"], formats=["raw"], n_samples=3)
        assert built1 == built2

    def test_double_build_jobs_jsonl_byte_equal(self, tmp_path):
        prompts = _toy_prompts_24_raw_24_chat()
        built = jobs.build_jobs(prompts, release="v1.0", models=["a", "b"], formats=["raw"], n_samples=3)

        out1 = tmp_path / "jobs_1.jsonl"
        out2 = tmp_path / "jobs_2.jsonl"
        jobs.write_jobs_jsonl(built, out1)
        rebuilt = jobs.build_jobs(prompts, release="v1.0", models=["a", "b"], formats=["raw"], n_samples=3)
        jobs.write_jobs_jsonl(rebuilt, out2)

        assert out1.read_bytes() == out2.read_bytes()
        assert out1.read_bytes() != b""

    def test_output_ordering_is_prompt_then_model_then_sample_idx(self):
        prompts = _toy_prompts_24_raw_24_chat()
        raw_first_two = [p for p in prompts if p.format == "raw"][:2]
        built = jobs.build_jobs(raw_first_two, release="v1.0", models=["b", "a"], formats=["raw"], n_samples=2)
        expected = [
            (raw_first_two[0].prompt_id, "b", 0), (raw_first_two[0].prompt_id, "b", 1),
            (raw_first_two[0].prompt_id, "a", 0), (raw_first_two[0].prompt_id, "a", 1),
            (raw_first_two[1].prompt_id, "b", 0), (raw_first_two[1].prompt_id, "b", 1),
            (raw_first_two[1].prompt_id, "a", 0), (raw_first_two[1].prompt_id, "a", 1),
        ]
        actual = [(j.prompt_id, j.model_key, j.sample_idx) for j in built]
        assert actual == expected


# ---------------------------------------------------------------------------
# knobe jobs diff -- resume semantics
# ---------------------------------------------------------------------------


class TestReadResultsTolerant:
    def test_missing_file_returns_empty(self, tmp_path):
        assert jobs.read_results_tolerant(tmp_path / "does_not_exist.jsonl") == []

    def test_empty_file_returns_empty(self, tmp_path):
        path = tmp_path / "empty.jsonl"
        path.write_text("")
        assert jobs.read_results_tolerant(path) == []

    def test_nonempty_file_parses(self, tmp_path):
        path = tmp_path / "results.jsonl"
        write_jsonl([_result("job-1")], path)
        results = jobs.read_results_tolerant(path)
        assert [r.job_id for r in results] == ["job-1"]


class TestDiffJobs:
    def test_no_results_everything_remaining(self):
        job_list = [_job("j1"), _job("j2"), _job("j3")]
        remaining, report = jobs.diff_jobs(job_list, [])
        assert [j.job_id for j in remaining] == ["j1", "j2", "j3"]
        assert (report.total, report.done, report.remaining) == (3, 0, 3)

    def test_partial_results_only_undone_remaining(self):
        job_list = [_job("j1"), _job("j2"), _job("j3")]
        results = [_result("j2")]
        remaining, report = jobs.diff_jobs(job_list, results)
        assert [j.job_id for j in remaining] == ["j1", "j3"]
        assert (report.total, report.done, report.remaining) == (3, 1, 2)

    def test_full_results_nothing_remaining(self):
        job_list = [_job("j1"), _job("j2"), _job("j3")]
        results = [_result("j1"), _result("j2"), _result("j3")]
        remaining, report = jobs.diff_jobs(job_list, results)
        assert remaining == []
        assert (report.total, report.done, report.remaining) == (3, 3, 0)

    def test_extra_unknown_result_ids_ignored(self):
        job_list = [_job("j1"), _job("j2")]
        results = [_result("j1"), _result("j-does-not-exist-in-jobs")]
        remaining, report = jobs.diff_jobs(job_list, results)
        assert [j.job_id for j in remaining] == ["j2"]
        assert (report.total, report.done, report.remaining) == (2, 1, 1)

    def test_remaining_preserves_job_order(self):
        job_list = [_job("j3"), _job("j1"), _job("j2")]
        remaining, _report = jobs.diff_jobs(job_list, [_result("j1")])
        assert [j.job_id for j in remaining] == ["j3", "j2"]


# ---------------------------------------------------------------------------
# CLI wiring: jobs build / jobs diff
# ---------------------------------------------------------------------------


class TestCLIJobsBuild:
    def _write_run_config(self, path: Path, **overrides) -> None:
        data = dict(release="v1.0", models=["model-a", "model-b"], formats=["raw"], n_samples=3)
        data.update(overrides)
        path.write_text(yaml.safe_dump(data))

    def _write_prompts(self, path: Path) -> list[PromptRecord]:
        prompts = _toy_prompts_24_raw_24_chat()
        write_jsonl(prompts, path)
        return prompts

    def test_jobs_subcommand_registered(self):
        assert "jobs" in cli.SUBCOMMANDS

    def test_cli_help_mentions_jobs(self, capsys):
        with pytest.raises(SystemExit):
            cli.build_parser().parse_args(["--help"])
        out = capsys.readouterr().out
        assert "jobs" in out

    def test_jobs_no_subcommand_prints_help_and_returns_nonzero(self, capsys):
        rc = cli.main(["jobs"])
        assert rc == 1
        out = capsys.readouterr().out
        assert "usage" in out.lower()

    def test_cli_jobs_build_writes_144_jobs(self, tmp_path):
        config_path = tmp_path / "run.yaml"
        self._write_run_config(config_path)
        prompts_path = tmp_path / "prompts.jsonl"
        self._write_prompts(prompts_path)
        out_path = tmp_path / "jobs.jsonl"

        rc = cli.main([
            "jobs", "build", "--config", str(config_path),
            "--prompts", str(prompts_path), "--out", str(out_path),
        ])

        assert rc == 0
        lines = out_path.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 144

    def test_cli_jobs_build_double_build_byte_equal(self, tmp_path):
        config_path = tmp_path / "run.yaml"
        self._write_run_config(config_path)
        prompts_path = tmp_path / "prompts.jsonl"
        self._write_prompts(prompts_path)
        out1 = tmp_path / "jobs_1.jsonl"
        out2 = tmp_path / "jobs_2.jsonl"

        assert cli.main([
            "jobs", "build", "--config", str(config_path),
            "--prompts", str(prompts_path), "--out", str(out1),
        ]) == 0
        assert cli.main([
            "jobs", "build", "--config", str(config_path),
            "--prompts", str(prompts_path), "--out", str(out2),
        ]) == 0

        assert out1.read_bytes() == out2.read_bytes()

    def test_cli_subprocess_console_script_jobs_build(self, tmp_path):
        config_path = tmp_path / "run.yaml"
        self._write_run_config(config_path)
        prompts_path = tmp_path / "prompts.jsonl"
        self._write_prompts(prompts_path)
        out_path = tmp_path / "jobs.jsonl"

        result = subprocess.run(
            [
                sys.executable, "-m", "knobe.cli", "jobs", "build",
                "--config", str(config_path), "--prompts", str(prompts_path),
                "--out", str(out_path),
            ],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, result.stderr
        assert out_path.exists()


class TestCLIJobsDiff:
    def _write_jobs(self, path: Path, job_ids: list[str]) -> None:
        write_jsonl([_job(jid, prompt_id=jid) for jid in job_ids], path)

    def test_cli_jobs_diff_no_results_file_all_remaining(self, tmp_path, capsys):
        jobs_path = tmp_path / "jobs.jsonl"
        self._write_jobs(jobs_path, ["j1", "j2", "j3"])
        results_path = tmp_path / "results.jsonl"  # never created

        rc = cli.main(["jobs", "diff", "--jobs", str(jobs_path), "--results", str(results_path)])

        assert rc == 0
        out = capsys.readouterr().out
        assert "total=3" in out
        assert "done=0" in out
        assert "remaining=3" in out

    def test_cli_jobs_diff_partial_results_writes_remaining_out(self, tmp_path):
        jobs_path = tmp_path / "jobs.jsonl"
        self._write_jobs(jobs_path, ["j1", "j2", "j3"])
        results_path = tmp_path / "results.jsonl"
        write_jsonl([_result("j2")], results_path)
        remaining_out = tmp_path / "remaining.jsonl"

        rc = cli.main([
            "jobs", "diff", "--jobs", str(jobs_path), "--results", str(results_path),
            "--out", str(remaining_out),
        ])

        assert rc == 0
        remaining_lines = remaining_out.read_text(encoding="utf-8").splitlines()
        remaining_records = [JobRecord(**json.loads(line)) for line in remaining_lines]
        assert [r.job_id for r in remaining_records] == ["j1", "j3"]

    def test_cli_jobs_diff_full_results_empty_remaining_file(self, tmp_path, capsys):
        jobs_path = tmp_path / "jobs.jsonl"
        self._write_jobs(jobs_path, ["j1", "j2"])
        results_path = tmp_path / "results.jsonl"
        write_jsonl([_result("j1"), _result("j2")], results_path)
        remaining_out = tmp_path / "remaining.jsonl"

        rc = cli.main([
            "jobs", "diff", "--jobs", str(jobs_path), "--results", str(results_path),
            "--out", str(remaining_out),
        ])

        assert rc == 0
        out = capsys.readouterr().out
        assert "remaining=0" in out
        assert remaining_out.read_text(encoding="utf-8") == ""

    def test_cli_jobs_diff_empty_results_file_tolerated(self, tmp_path, capsys):
        jobs_path = tmp_path / "jobs.jsonl"
        self._write_jobs(jobs_path, ["j1"])
        results_path = tmp_path / "results.jsonl"
        results_path.write_text("")  # exists but empty

        rc = cli.main(["jobs", "diff", "--jobs", str(jobs_path), "--results", str(results_path)])

        assert rc == 0
        out = capsys.readouterr().out
        assert "remaining=1" in out

    def test_cli_jobs_diff_out_optional_no_file_written_when_omitted(self, tmp_path):
        jobs_path = tmp_path / "jobs.jsonl"
        self._write_jobs(jobs_path, ["j1"])
        results_path = tmp_path / "results.jsonl"
        results_path.write_text("")

        rc = cli.main(["jobs", "diff", "--jobs", str(jobs_path), "--results", str(results_path)])
        assert rc == 0
        assert not (tmp_path / "remaining.jsonl").exists()

    def test_cli_subprocess_console_script_jobs_diff(self, tmp_path):
        jobs_path = tmp_path / "jobs.jsonl"
        self._write_jobs(jobs_path, ["j1", "j2"])
        results_path = tmp_path / "results.jsonl"
        write_jsonl([_result("j1")], results_path)

        result = subprocess.run(
            [
                sys.executable, "-m", "knobe.cli", "jobs", "diff",
                "--jobs", str(jobs_path), "--results", str(results_path),
            ],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, result.stderr
        assert "remaining=1" in result.stdout
