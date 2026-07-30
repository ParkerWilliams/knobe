"""Tests for src/knobe/generate.py + the `knobe generate` CLI (WO-1).

Acceptance criteria under test (task-3-brief.md / WO1_generation.md):
  - Round-trip: synthetic valid set ingests, matrix + tracking log update.
  - Each documented failure mode rejected with its specific error: banned
    word, "to"-prefixed goal, noun-phrase outcome_verb, NMB missing
    subdomain, duplicate agent within domain.
  - status regression-pins the real matrix's imbalance numbers.
  - next-prompt on the current matrix injects the etiquette instruction.
  - No network calls anywhere (verified by inspection: generate.py imports
    only csv/datetime/io/re/dataclasses/pathlib + sibling knobe modules).

Tests operate ONLY on tmp_path copies of the real matrix, never on the
committed data/authoring/ALL_DOMAINS_master_matrix.csv itself.
"""
from __future__ import annotations

import csv
import shutil
from pathlib import Path

import pytest

from knobe import cli, constants, generate, tracking
from knobe.schemas import FamilyRow

REPO_ROOT = Path(__file__).resolve().parents[1]
REAL_MATRIX = REPO_ROOT / "data" / "authoring" / "ALL_DOMAINS_master_matrix.csv"

FIELDNAMES = FamilyRow.csv_fieldnames()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def real_matrix_copy(tmp_path):
    """A tmp-dir copy of the real 105-family matrix -- safe to read from
    for regression assertions; never written to by these tests."""
    dest = tmp_path / "ALL_DOMAINS_master_matrix.csv"
    shutil.copy(REAL_MATRIX, dest)
    return dest


def _valid_set_rows(set_num: int, *, agent: str = "The lab director", goal: str = "expand the lab's research capacity") -> list[dict]:
    """A synthetic, fully-valid 5-family set (one storyline, all 5
    valences) for the Environment domain -- passes every assemble.py
    structural check and every WO-1 set-level check. Individual tests
    mutate a copy of this to trigger one specific failure mode."""
    n = f"{set_num:02d}"
    common_action = "reallocated existing equipment budget toward new instruments"
    uncommon_action = "sought a special one-time grant earmarked for equipment upgrades"

    rows = [
        {
            "family_id": f"ENV-MB-{n}", "domain": "Environment", "valence": "MB", "nonmoral_subdomain": "",
            "agent": agent, "goal": goal, "common_action": common_action, "uncommon_action": uncommon_action,
            "affected_entity": "the research assistants working in the lab",
            "low_evocative_outcome": "a safety audit found the new instruments lacked required protective enclosures",
            "high_evocative_outcome": "a research assistant suffered a chemical burn from an instrument lacking a protective enclosure",
            "outcome_verb": "expose lab assistants to unsafe equipment",
        },
        {
            "family_id": f"ENV-MG-{n}", "domain": "Environment", "valence": "MG", "nonmoral_subdomain": "",
            "agent": agent, "goal": goal, "common_action": common_action, "uncommon_action": uncommon_action,
            "affected_entity": "the research assistants working in the lab",
            "low_evocative_outcome": "a safety audit found the new instruments met every required protective enclosure standard",
            "high_evocative_outcome": "a research assistant said the protective enclosures made the new instruments noticeably safer to operate",
            "outcome_verb": "improve safety conditions for lab assistants",
        },
        {
            "family_id": f"ENV-NMB-{n}", "domain": "Environment", "valence": "NMB", "nonmoral_subdomain": "etiquette",
            "agent": agent, "goal": goal, "common_action": common_action, "uncommon_action": uncommon_action,
            "affected_entity": "other lab staff filling out equipment-request paperwork",
            "low_evocative_outcome": "the equipment-request form used inconsistent field labels across sections",
            "high_evocative_outcome": "a lab staff member said the request form field labels looked mismatched and confusing across sections",
            "outcome_verb": "confuse readers of the equipment-request form",
        },
        {
            "family_id": f"ENV-NMG-{n}", "domain": "Environment", "valence": "NMG", "nonmoral_subdomain": "etiquette",
            "agent": agent, "goal": goal, "common_action": common_action, "uncommon_action": uncommon_action,
            "affected_entity": "other lab staff filling out equipment-request paperwork",
            "low_evocative_outcome": "the equipment-request form used consistent field labels across every section",
            "high_evocative_outcome": "a lab staff member said the request form field labels now read clearly and consistently across sections",
            "outcome_verb": "clarify the equipment-request form's layout",
        },
        {
            "family_id": f"ENV-NEU-{n}", "domain": "Environment", "valence": "NEU", "nonmoral_subdomain": "",
            "agent": agent, "goal": goal, "common_action": common_action, "uncommon_action": uncommon_action,
            "affected_entity": "the lab's internal archive folder naming convention",
            "low_evocative_outcome": "the archive folder naming convention was updated from an old numeric scheme to a new date-based scheme",
            "high_evocative_outcome": "a records clerk noted the archive folders now sort automatically by date instead of by number",
            "outcome_verb": "reorganize the lab's archive folder naming convention",
        },
    ]
    return rows


def _write_set_csv(rows: list[dict], path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in FIELDNAMES})


# ---------------------------------------------------------------------------
# ingest: round-trip
# ---------------------------------------------------------------------------


class TestIngestRoundTrip:
    def test_valid_set_ingests_and_updates_matrix_and_tracking_log(self, tmp_path):
        matrix = tmp_path / "matrix.csv"
        set_csv = tmp_path / "set01.csv"
        _write_set_csv(_valid_set_rows(1), set_csv)

        result = generate.ingest(set_csv, matrix, generator_model="claude-x", date="2026-01-01")

        assert result.ok is True, result.errors
        assert result.appended_family_ids == [
            "ENV-MB-01", "ENV-MG-01", "ENV-NMB-01", "ENV-NMG-01", "ENV-NEU-01",
        ]
        assert matrix.exists()

        rows = tracking.load_matrix_rows(matrix)
        assert len(rows) == 5
        assert all(r["human_approved"] is False for r in rows)
        assert all(r["generator_model"] == "claude-x" for r in rows)
        assert all(r["ingest_date"] == "2026-01-01" for r in rows)

        # tracking log / next-set-number reflect the new set
        summaries = tracking.summarize_sets(rows, "Environment")
        assert len(summaries) == 1
        assert summaries[0].agent == "The lab director"
        assert tracking.next_set_number(rows, "Environment") == 2

        block = tracking.format_tracking_log(summaries)
        assert "The lab director" in block
        assert "expand the lab's research capacity" in block

    def test_ingest_defaults_date_to_today_when_not_given(self, tmp_path, monkeypatch):
        import datetime

        matrix = tmp_path / "matrix.csv"
        set_csv = tmp_path / "set01.csv"
        _write_set_csv(_valid_set_rows(1), set_csv)

        result = generate.ingest(set_csv, matrix, generator_model="claude-x")
        assert result.ok is True
        rows = tracking.load_matrix_rows(matrix)
        assert rows[0]["ingest_date"] == datetime.date.today().isoformat()

    def test_second_set_appends_without_disturbing_first(self, tmp_path):
        matrix = tmp_path / "matrix.csv"
        _write_set_csv(_valid_set_rows(1), tmp_path / "set01.csv")
        generate.ingest(tmp_path / "set01.csv", matrix, date="2026-01-01")

        _write_set_csv(_valid_set_rows(2, agent="Maria", goal="secure funding for a new survey"), tmp_path / "set02.csv")
        result = generate.ingest(tmp_path / "set02.csv", matrix, date="2026-01-02")

        assert result.ok is True, result.errors
        rows = tracking.load_matrix_rows(matrix)
        assert len(rows) == 10
        assert tracking.next_set_number(rows, "Environment") == 3


# ---------------------------------------------------------------------------
# ingest: documented failure modes (each rejected with its specific error;
# nothing written on any error)
# ---------------------------------------------------------------------------


class TestIngestFailureModes:
    def test_banned_word_rejected(self, tmp_path):
        matrix = tmp_path / "matrix.csv"
        rows = _valid_set_rows(1)
        rows[0]["outcome_verb"] = "recklessly expose lab assistants to unsafe equipment"
        set_csv = tmp_path / "set.csv"
        _write_set_csv(rows, set_csv)

        result = generate.ingest(set_csv, matrix, date="2026-01-01")

        assert result.ok is False
        assert not matrix.exists()
        assert any("banned" in e.lower() and "reckless" in e.lower() for e in result.errors), result.errors

    def test_to_prefixed_goal_rejected(self, tmp_path):
        matrix = tmp_path / "matrix.csv"
        rows = _valid_set_rows(1, goal="to expand the lab's research capacity")
        set_csv = tmp_path / "set.csv"
        _write_set_csv(rows, set_csv)

        result = generate.ingest(set_csv, matrix, date="2026-01-01")

        assert result.ok is False
        assert not matrix.exists()
        assert any("'goal'" in e and 'starts with "to"' in e for e in result.errors), result.errors

    def test_noun_phrase_outcome_verb_rejected(self, tmp_path):
        matrix = tmp_path / "matrix.csv"
        rows = _valid_set_rows(1)
        rows[0]["outcome_verb"] = "the exposure of lab assistants to unsafe equipment"
        set_csv = tmp_path / "set.csv"
        _write_set_csv(rows, set_csv)

        result = generate.ingest(set_csv, matrix, date="2026-01-01")

        assert result.ok is False
        assert not matrix.exists()
        assert any("noun phrase" in e for e in result.errors), result.errors

    def test_nmb_missing_subdomain_rejected(self, tmp_path):
        matrix = tmp_path / "matrix.csv"
        rows = _valid_set_rows(1)
        for r in rows:
            if r["valence"] == "NMB":
                r["nonmoral_subdomain"] = ""
        set_csv = tmp_path / "set.csv"
        _write_set_csv(rows, set_csv)

        result = generate.ingest(set_csv, matrix, date="2026-01-01")

        assert result.ok is False
        assert not matrix.exists()
        assert any("requires a nonmoral_subdomain" in e for e in result.errors), result.errors

    def test_duplicate_agent_within_domain_rejected(self, tmp_path):
        matrix = tmp_path / "matrix.csv"
        _write_set_csv(_valid_set_rows(1, agent="The lab director"), tmp_path / "set01.csv")
        first = generate.ingest(tmp_path / "set01.csv", matrix, date="2026-01-01")
        assert first.ok is True, first.errors

        _write_set_csv(
            _valid_set_rows(2, agent="The lab director", goal="secure funding for a new survey"),
            tmp_path / "set02.csv",
        )
        result = generate.ingest(tmp_path / "set02.csv", matrix, date="2026-01-02")

        assert result.ok is False
        assert any("already used in domain" in e for e in result.errors), result.errors
        # nothing written on error: still exactly the first set's 5 rows
        assert len(tracking.load_matrix_rows(matrix)) == 5


class TestIngestOtherSetLevelChecks:
    def test_wrong_row_count_rejected(self, tmp_path):
        matrix = tmp_path / "matrix.csv"
        rows = _valid_set_rows(1)[:4]
        set_csv = tmp_path / "set.csv"
        _write_set_csv(rows, set_csv)
        result = generate.ingest(set_csv, matrix, date="2026-01-01")
        assert result.ok is False
        assert any("exactly 5 rows" in e for e in result.errors)

    def test_domain_mismatch_across_rows_rejected(self, tmp_path):
        matrix = tmp_path / "matrix.csv"
        rows = _valid_set_rows(1)
        rows[0]["domain"] = "Finance"
        set_csv = tmp_path / "set.csv"
        _write_set_csv(rows, set_csv)
        result = generate.ingest(set_csv, matrix, date="2026-01-01")
        assert result.ok is False
        assert any("same domain" in e for e in result.errors)

    def test_nonshared_scaffold_rejected(self, tmp_path):
        matrix = tmp_path / "matrix.csv"
        rows = _valid_set_rows(1)
        rows[0]["agent"] = "A different scientist"
        set_csv = tmp_path / "set.csv"
        _write_set_csv(rows, set_csv)
        result = generate.ingest(set_csv, matrix, date="2026-01-01")
        assert result.ok is False
        assert any("'agent' must be identical" in e for e in result.errors)

    def test_wrong_set_number_rejected(self, tmp_path):
        matrix = tmp_path / "matrix.csv"
        _write_set_csv(_valid_set_rows(1), tmp_path / "set01.csv")
        generate.ingest(tmp_path / "set01.csv", matrix, date="2026-01-01")

        # skip 02, jump straight to 03
        _write_set_csv(
            _valid_set_rows(3, agent="Maria", goal="secure funding for a new survey"),
            tmp_path / "set03.csv",
        )
        result = generate.ingest(tmp_path / "set03.csv", matrix, date="2026-01-02")
        assert result.ok is False
        assert any("expected 02" in e for e in result.errors), result.errors

    def test_goal_similarity_flagged_as_nonblocking_warning(self, tmp_path):
        matrix = tmp_path / "matrix.csv"
        _write_set_csv(_valid_set_rows(1, goal="expand the lab's research capacity"), tmp_path / "set01.csv")
        generate.ingest(tmp_path / "set01.csv", matrix, date="2026-01-01")

        _write_set_csv(
            _valid_set_rows(2, agent="Maria", goal="expand the lab's testing capacity"),
            tmp_path / "set02.csv",
        )
        result = generate.ingest(tmp_path / "set02.csv", matrix, date="2026-01-02")

        assert result.ok is True, result.errors
        assert any("token-similar" in w for w in result.warnings), result.warnings


# ---------------------------------------------------------------------------
# next-prompt
# ---------------------------------------------------------------------------


class TestNextPrompt:
    def test_unknown_domain_raises(self, tmp_path):
        with pytest.raises(ValueError):
            generate.next_prompt_text(tmp_path / "matrix.csv", "BOGUS")

    def test_empty_matrix_reports_none_yet_and_no_instruction(self, tmp_path):
        prompt = generate.next_prompt_text(tmp_path / "does_not_exist.csv", "ENV")
        assert "(none yet)" in prompt
        assert "Set number: 01" in prompt
        assert "Domain: Environment" in prompt
        assert "INSTRUCTION" not in prompt  # nothing generated anywhere yet -- no basis to steer

    def test_real_matrix_injects_etiquette_instruction(self, real_matrix_copy):
        """Acceptance criterion: next-prompt on the current matrix injects
        the etiquette instruction (etiquette=0 vs aesthetic=24)."""
        prompt = generate.next_prompt_text(real_matrix_copy, "ENV")
        assert "Domain: Environment" in prompt
        assert "Set number: 04" in prompt  # ENV already has 3 sets (15 families)
        assert "INSTRUCTION" in prompt
        assert "MUST use nonmoral_subdomain = etiquette" in prompt

    def test_domain_at_cap_refuses_without_allow_extra(self, tmp_path):
        matrix = tmp_path / "matrix.csv"
        rows = []
        for set_num in range(1, 6):
            rows.extend(_valid_set_rows(set_num, agent=f"Agent{set_num}", goal=f"goal number {set_num} for the lab"))
        _write_matrix(matrix, rows)

        with pytest.raises(generate.DomainAtCapError):
            generate.next_prompt_text(matrix, "ENV")

        prompt = generate.next_prompt_text(matrix, "ENV", allow_extra=True)
        assert "Set number: 06" in prompt


def _write_matrix(path: Path, rows: list[dict]) -> None:
    """Writes a synthetic master_matrix.csv (12 canonical columns, no
    provenance -- exercises the pre-WO-1 / backfill path) directly, for
    tests that need a matrix already containing several sets."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in FIELDNAMES})


# ---------------------------------------------------------------------------
# approve
# ---------------------------------------------------------------------------


class TestApprove:
    def test_approve_by_family_id(self, tmp_path):
        matrix = tmp_path / "matrix.csv"
        _write_set_csv(_valid_set_rows(1), tmp_path / "set01.csv")
        generate.ingest(tmp_path / "set01.csv", matrix, date="2026-01-01")

        matched, missing = generate.approve(matrix, family_ids=["ENV-MB-01", "ENV-MG-01"])
        assert matched == {"ENV-MB-01", "ENV-MG-01"}
        assert missing == set()

        rows = {r["family_id"]: r for r in tracking.load_matrix_rows(matrix)}
        assert rows["ENV-MB-01"]["human_approved"] is True
        assert rows["ENV-MG-01"]["human_approved"] is True
        assert rows["ENV-NMB-01"]["human_approved"] is False

    def test_approve_by_set_selector(self, tmp_path):
        matrix = tmp_path / "matrix.csv"
        _write_set_csv(_valid_set_rows(1), tmp_path / "set01.csv")
        generate.ingest(tmp_path / "set01.csv", matrix, date="2026-01-01")

        matched, missing = generate.approve(matrix, set_selector=("ENV", "01"))
        assert matched == {"ENV-MB-01", "ENV-MG-01", "ENV-NMB-01", "ENV-NMG-01", "ENV-NEU-01"}
        rows = tracking.load_matrix_rows(matrix)
        assert all(r["human_approved"] is True for r in rows)

    def test_approve_reports_missing_family_ids(self, tmp_path):
        matrix = tmp_path / "matrix.csv"
        _write_set_csv(_valid_set_rows(1), tmp_path / "set01.csv")
        generate.ingest(tmp_path / "set01.csv", matrix, date="2026-01-01")

        matched, missing = generate.approve(matrix, family_ids=["ENV-MB-01", "ENV-MB-99"])
        assert matched == {"ENV-MB-01"}
        assert missing == {"ENV-MB-99"}

    def test_approve_with_no_targets_raises(self, tmp_path):
        matrix = tmp_path / "matrix.csv"
        _write_set_csv(_valid_set_rows(1), tmp_path / "set01.csv")
        generate.ingest(tmp_path / "set01.csv", matrix, date="2026-01-01")
        with pytest.raises(ValueError):
            generate.approve(matrix)

    def test_approve_nonexistent_matrix_raises_without_writing(self, tmp_path):
        # Approving into a matrix that doesn't exist must error cleanly, not
        # write a header-only CSV that silently masks the typo'd path.
        missing = tmp_path / "nope.csv"
        with pytest.raises(ValueError, match="does not exist"):
            generate.approve(missing, family_ids=["ENV-MB-01"])
        assert not missing.exists()


# ---------------------------------------------------------------------------
# status (real-matrix regression)
# ---------------------------------------------------------------------------


class TestStatus:
    def test_real_matrix_regression(self, real_matrix_copy):
        """Acceptance criterion: status output on the real current matrix
        reports exactly aesthetic 24, procedural 16, prudential 2,
        etiquette 0."""
        s = generate.status(real_matrix_copy)
        assert s["total_families"] == 105
        assert s["subdomain_tally_approved"] == {
            "prudential": 2, "procedural": 16, "aesthetic": 24, "etiquette": 0,
        }
        assert s["subdomain_tally_pending"] == {
            "prudential": 0, "procedural": 0, "aesthetic": 0, "etiquette": 0,
        }
        assert s["approval_backlog"] == []  # backfill: pre-WO-1 rows are already approved

    def test_format_status_renders_the_pinned_numbers(self, real_matrix_copy):
        text = generate.format_status(generate.status(real_matrix_copy))
        assert "aesthetic: 24" in text
        assert "procedural: 16" in text
        assert "prudential: 2" in text
        assert "etiquette: 0" in text
        assert "steer new NMB/NMG sets toward etiquette" in text


# ---------------------------------------------------------------------------
# qa
# ---------------------------------------------------------------------------


class TestQaPrompt:
    def test_qa_prompt_fills_domain_and_inlines_csv(self, real_matrix_copy):
        prompt = generate.qa_prompt(real_matrix_copy, "ENV")
        assert "Environment (3 sets, 15 families)" in prompt
        assert "family_id,domain,valence" in prompt  # inlined CSV header
        assert "ENV-MB-01" in prompt

    def test_qa_unknown_domain_raises(self, tmp_path):
        with pytest.raises(ValueError):
            generate.qa_prompt(tmp_path / "matrix.csv", "BOGUS")


# ---------------------------------------------------------------------------
# CLI wiring
# ---------------------------------------------------------------------------


class TestCLI:
    def test_generate_registered_in_subcommands(self):
        assert "generate" in cli.SUBCOMMANDS

    def test_no_subcommand_prints_help(self, capsys):
        rc = cli.main(["generate"])
        assert rc == 1
        assert "usage" in capsys.readouterr().out.lower()

    def test_status_via_cli(self, real_matrix_copy, capsys):
        rc = cli.main(["generate", "status", "--matrix", str(real_matrix_copy)])
        assert rc == 0
        assert "aesthetic: 24" in capsys.readouterr().out

    def test_next_prompt_via_cli_unknown_domain_errors(self, tmp_path, capsys):
        rc = cli.main(["generate", "next-prompt", "--domain", "BOGUS", "--matrix", str(tmp_path / "m.csv")])
        assert rc == 1
        assert "ERROR" in capsys.readouterr().err

    def test_next_prompt_via_cli_show_system(self, tmp_path, capsys):
        rc = cli.main(["generate", "next-prompt", "--domain", "ENV", "--matrix", str(tmp_path / "m.csv"), "--show-system"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "SYSTEM PROMPT" in out
        assert constants.GENERATION_SYSTEM_PROMPT in out

    def test_ingest_via_cli_round_trip(self, tmp_path, capsys):
        matrix = tmp_path / "matrix.csv"
        set_csv = tmp_path / "set01.csv"
        _write_set_csv(_valid_set_rows(1), set_csv)
        rc = cli.main([
            "generate", "ingest", str(set_csv), "--matrix", str(matrix),
            "--generator-model", "claude-x", "--date", "2026-01-01",
        ])
        assert rc == 0, capsys.readouterr().out
        assert matrix.exists()

    def test_ingest_via_cli_rejects_invalid_set(self, tmp_path, capsys):
        matrix = tmp_path / "matrix.csv"
        rows = _valid_set_rows(1)
        rows[0]["outcome_verb"] = "recklessly expose lab assistants to unsafe equipment"
        set_csv = tmp_path / "set.csv"
        _write_set_csv(rows, set_csv)
        rc = cli.main(["generate", "ingest", str(set_csv), "--matrix", str(matrix), "--date", "2026-01-01"])
        assert rc == 1
        assert not matrix.exists()

    def test_approve_via_cli(self, tmp_path, capsys):
        matrix = tmp_path / "matrix.csv"
        _write_set_csv(_valid_set_rows(1), tmp_path / "set01.csv")
        generate.ingest(tmp_path / "set01.csv", matrix, date="2026-01-01")
        rc = cli.main(["generate", "approve", "ENV-MB-01", "--matrix", str(matrix)])
        assert rc == 0
        assert tracking.load_matrix_rows(matrix)[0]["human_approved"] is True

    def test_qa_via_cli(self, real_matrix_copy, capsys):
        rc = cli.main(["generate", "qa", "--domain", "ENV", "--matrix", str(real_matrix_copy)])
        assert rc == 0
        assert "family_id,domain,valence" in capsys.readouterr().out
