import subprocess
import sys

import pytest

from knobe.cli import SUBCOMMANDS, build_parser, main


def test_help_lists_subcommands(capsys):
    with pytest.raises(SystemExit) as exc_info:
        build_parser().parse_args(["--help"])
    assert exc_info.value.code == 0
    out = capsys.readouterr().out
    for name in SUBCOMMANDS:
        assert name in out


def test_version_subcommand_runs(capsys):
    rc = main(["version"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "schema_version=1" in out


def test_no_subcommand_prints_help_and_returns_nonzero(capsys):
    rc = main([])
    assert rc == 1
    out = capsys.readouterr().out
    assert "usage" in out.lower()


def test_unknown_subcommand_errors():
    with pytest.raises(SystemExit):
        build_parser().parse_args(["bogus-subcommand"])


def test_console_script_entry_point_installed():
    """pyproject.toml's [project.scripts] knobe = "knobe.cli:main" must
    actually be installed and runnable, not just declared."""
    result = subprocess.run(
        [sys.executable, "-m", "knobe.cli", "version"],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0
    assert "schema_version=1" in result.stdout
