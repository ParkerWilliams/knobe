"""Tests for src/knobe/render.py (WO-2 Part B).

Acceptance criteria under test (task-2-brief.md):
  - 2-family toy matrix -> 8 variants -> 24 raw + 24 chat prompt records.
  - Deterministic output ordering (variant_id, then question in
    intentionality/blame/praise order, then format raw/chat).
  - Property tests: scenario appears verbatim exactly once in every
    rendered prompt; no banned word leaks in outside the frozen,
    already-validated scenario/question text; sha256 stable across runs.
  - `knobe render vignettes.csv --out prompts.jsonl [--formats raw,chat]`.

Note on the banned-word property test's exact operationalization: see the
docstring on TestBannedWordProperty below -- it deliberately strips both
the scenario AND the question substring before checking, not just the
scenario, because "blame"/"praise"/"intentional" are themselves literally
present in the frozen, non-authored question templates
(constants.QUESTIONS / constants.Q_INTENTIONALITY_TEMPLATE) -- they are the
measurement instrument's own wording, not author-injected bias. Stripping
only the scenario would make this test fail on every correct blame/praise/
intentionality prompt.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from knobe import assemble, cli, constants, render
from knobe.schemas import PromptRecord, VignetteRow

REPO_ROOT = Path(__file__).resolve().parents[1]
MASTER_MATRIX = REPO_ROOT / "data" / "authoring" / "ALL_DOMAINS_master_matrix.csv"


# ---------------------------------------------------------------------------
# Fixtures: a 2-family toy matrix -> 8 variants (mirrors test_assemble.py's
# own toy-matrix helper, kept local/independent so render.py's tests don't
# depend on assemble.py's test module).
# ---------------------------------------------------------------------------


def _valid_family(**overrides) -> dict:
    fam = dict(
        family_id="TST-MB-01",
        domain="Testing",
        valence="MB",
        nonmoral_subdomain="",
        agent="The tester",
        goal="pass the test suite",
        common_action="ran the standard test",
        uncommon_action="ran an unusual bespoke test",
        affected_entity="the other developers",
        low_evocative_outcome="a report showed the build had failed",
        high_evocative_outcome="teammates spent the weekend firefighting the outage",
        outcome_verb="break the shared build",
    )
    fam.update(overrides)
    return fam


def _two_family_matrix() -> list[dict]:
    return [
        _valid_family(family_id="TST-MB-01", valence="MB"),
        _valid_family(
            family_id="TST-MG-01", valence="MG",
            low_evocative_outcome="a report showed the build had passed",
            high_evocative_outcome="teammates were able to ship the release on schedule",
            outcome_verb="stabilize the shared build",
        ),
    ]


def _toy_vignette_rows() -> list[VignetteRow]:
    rows = assemble.assemble(_two_family_matrix())
    return [VignetteRow(**r) for r in rows]


# ---------------------------------------------------------------------------
# render_prompt_text / render_prompts_for_variant
# ---------------------------------------------------------------------------


class TestRenderPromptText:
    def test_uses_raimondi_template_verbatim(self):
        text = render.render_prompt_text("SCEN", "QUES")
        assert text == constants.RAIMONDI_PROMPT_TEMPLATE.format(scenario="SCEN", question="QUES")

    def test_scenario_and_question_slotted_in(self):
        text = render.render_prompt_text("A scenario happened.", "How bad, 0-10?")
        assert "A scenario happened." in text
        assert "How bad, 0-10?" in text
        assert text.startswith("Read carefully the following scenario")
        assert text.endswith("Answer:")


class TestRenderPromptsForVariant:
    def test_six_records_default_formats(self):
        row = _toy_vignette_rows()[0]
        records = render.render_prompts_for_variant(row)
        assert len(records) == 6  # 3 questions x 2 formats

    def test_ordering_question_then_format(self):
        row = _toy_vignette_rows()[0]
        records = render.render_prompts_for_variant(row)
        expected = [
            (row.variant_id, "intentionality", "raw"),
            (row.variant_id, "intentionality", "chat"),
            (row.variant_id, "blame", "raw"),
            (row.variant_id, "blame", "chat"),
            (row.variant_id, "praise", "raw"),
            (row.variant_id, "praise", "chat"),
        ]
        actual = [(r.variant_id, r.question_type, r.format) for r in records]
        assert actual == expected

    def test_prompt_id_shape(self):
        row = _toy_vignette_rows()[0]
        records = render.render_prompts_for_variant(row)
        for rec in records:
            assert rec.prompt_id == f"{rec.variant_id}::{rec.question_type}::{rec.format}"

    def test_raw_and_chat_share_identical_text(self):
        row = _toy_vignette_rows()[0]
        records = render.render_prompts_for_variant(row)
        by_key = {(r.question_type, r.format): r for r in records}
        for qtype in ("intentionality", "blame", "praise"):
            assert by_key[(qtype, "raw")].text == by_key[(qtype, "chat")].text

    def test_raw_record_has_no_messages(self):
        row = _toy_vignette_rows()[0]
        records = render.render_prompts_for_variant(row, formats=("raw",))
        assert all(r.messages is None for r in records)

    def test_chat_record_has_single_user_message_matching_text(self):
        row = _toy_vignette_rows()[0]
        records = render.render_prompts_for_variant(row, formats=("chat",))
        for rec in records:
            assert rec.messages == [{"role": "user", "content": rec.text}]

    def test_sha256_differs_by_hash_target_even_when_text_matches(self):
        """Raw hashes sha256_for_text(text); chat hashes
        sha256_for_messages(messages) -- these needn't collide, but do
        confirm each record's own sha256 matches the schema's own helper
        for its format (schemas.py already covers the helpers themselves;
        this pins render.py actually calls the right one per format)."""
        from knobe.schemas import sha256_for_messages, sha256_for_text

        row = _toy_vignette_rows()[0]
        records = render.render_prompts_for_variant(row)
        for rec in records:
            if rec.format == "raw":
                assert rec.sha256 == sha256_for_text(rec.text)
            else:
                assert rec.sha256 == sha256_for_messages(rec.messages)

    def test_unknown_format_rejected(self):
        row = _toy_vignette_rows()[0]
        with pytest.raises(ValueError, match="unknown format"):
            render.render_prompts_for_variant(row, formats=("bogus",))

    def test_cancel_format_not_emitted_by_default(self):
        row = _toy_vignette_rows()[0]
        records = render.render_prompts_for_variant(row)
        assert all(r.format != "cancel" for r in records)


# ---------------------------------------------------------------------------
# render_all: toy-matrix acceptance criterion + deterministic ordering
# ---------------------------------------------------------------------------


class TestRenderAllToyMatrix:
    def test_eight_variants_from_two_families(self):
        rows = _toy_vignette_rows()
        assert len(rows) == 8  # 2 families x 4 variants (A/B/C/D)

    def test_twenty_four_raw_and_twenty_four_chat(self):
        rows = _toy_vignette_rows()
        records = render.render_all(rows)
        raw = [r for r in records if r.format == "raw"]
        chat = [r for r in records if r.format == "chat"]
        assert len(raw) == 24  # 8 variants x 3 questions
        assert len(chat) == 24
        assert len(records) == 48

    def test_formats_filter_raw_only(self):
        rows = _toy_vignette_rows()
        records = render.render_all(rows, formats=("raw",))
        assert len(records) == 24
        assert all(r.format == "raw" for r in records)

    def test_output_ordering_independent_of_input_row_order(self):
        rows = _toy_vignette_rows()
        forward = render.render_all(rows)
        reversed_input = render.render_all(list(reversed(rows)))
        assert forward == reversed_input

    def test_output_ordered_by_variant_id_then_question_then_format(self):
        rows = _toy_vignette_rows()
        records = render.render_all(rows)
        expected_variant_order = sorted(r.variant_id for r in rows)
        expected_keys = [
            (vid, qtype, fmt)
            for vid in expected_variant_order
            for qtype in ("intentionality", "blame", "praise")
            for fmt in ("raw", "chat")
        ]
        actual_keys = [(r.variant_id, r.question_type, r.format) for r in records]
        assert actual_keys == expected_keys

    def test_all_records_pass_prompt_record_schema(self):
        rows = _toy_vignette_rows()
        records = render.render_all(rows)
        assert all(isinstance(r, PromptRecord) for r in records)


# ---------------------------------------------------------------------------
# Property tests (WO-2 Part B item 4)
# ---------------------------------------------------------------------------


class TestScenarioVerbatimProperty:
    def test_scenario_appears_exactly_once_in_every_prompt(self):
        rows = _toy_vignette_rows()
        by_variant = {r.variant_id: r for r in rows}
        records = render.render_all(rows)
        for rec in records:
            scenario = by_variant[rec.variant_id].scenario
            assert rec.text.count(scenario) == 1

    def test_scenario_appears_exactly_once_on_real_105_family_matrix(self):
        families = assemble.load_families(MASTER_MATRIX)
        rows = [VignetteRow(**r) for r in assemble.assemble(families)]
        by_variant = {r.variant_id: r for r in rows}
        records = render.render_all(rows)
        for rec in records:
            scenario = by_variant[rec.variant_id].scenario
            assert rec.text.count(scenario) == 1


class TestBannedWordProperty:
    """See module docstring for why both scenario AND question are
    stripped before checking, not just the scenario."""

    def _remainder(self, rec: PromptRecord, row: VignetteRow) -> str:
        question_text = getattr(row, constants.MAIN_QUESTION_COLUMNS[rec.question_type])
        remainder = rec.text.replace(row.scenario, "", 1)
        remainder = remainder.replace(question_text, "", 1)
        return remainder

    def test_no_banned_word_outside_scenario_and_question_toy_matrix(self):
        rows = _toy_vignette_rows()
        by_variant = {r.variant_id: r for r in rows}
        records = render.render_all(rows)
        for rec in records:
            row = by_variant[rec.variant_id]
            remainder = self._remainder(rec, row)
            assert render.find_banned_words(remainder) == [], (rec.prompt_id, remainder)

    def test_no_banned_word_outside_scenario_and_question_real_matrix(self):
        families = assemble.load_families(MASTER_MATRIX)
        rows = [VignetteRow(**r) for r in assemble.assemble(families)]
        by_variant = {r.variant_id: r for r in rows}
        records = render.render_all(rows)
        for rec in records:
            row = by_variant[rec.variant_id]
            remainder = self._remainder(rec, row)
            assert render.find_banned_words(remainder) == [], (rec.prompt_id, remainder)

    def test_blame_and_praise_question_wording_itself_would_trip_a_naive_scan(self):
        """Documents WHY the remainder must also exclude the question:
        find_banned_words on the raw q_blame/q_praise/q_intentionality
        column text (not the remainder) legitimately finds "blame"/
        "praise"/"intentional" -- they're the fixed measurement wording,
        not authored bias. If this ever stops being true (e.g. the
        question wording changes), the exemption in the property test
        above needs re-examining."""
        row = _toy_vignette_rows()[0]
        assert render.find_banned_words(row.q_blame) == ["blame"]
        assert render.find_banned_words(row.q_praise) == ["praise"]
        # constants.ALL_BANNED lists "intentional" and "intentionally" as
        # separate entries; Q_INTENTIONALITY_TEMPLATE's wording ("Did ...
        # intentionally ...? ... completely intentionally") matches both.
        assert render.find_banned_words(row.q_intentionality) == ["intentional", "intentionally"]

    def test_find_banned_words_case_insensitive_and_inflected(self):
        assert render.find_banned_words("They acted RECKLESSLY and unethical.") == [
            "reckless", "unethical",
        ]

    def test_find_banned_words_clean_text_empty(self):
        assert render.find_banned_words("A perfectly ordinary sentence.") == []


class TestSha256StableAcrossRuns:
    def test_render_all_produces_equal_records_across_two_calls(self):
        rows = _toy_vignette_rows()
        records1 = render.render_all(rows)
        records2 = render.render_all(rows)
        assert records1 == records2
        assert [r.sha256 for r in records1] == [r.sha256 for r in records2]

    def test_double_build_prompts_jsonl_byte_equal(self, tmp_path):
        rows = _toy_vignette_rows()
        records = render.render_all(rows)

        out1 = tmp_path / "prompts_1.jsonl"
        out2 = tmp_path / "prompts_2.jsonl"
        render.write_prompts_jsonl(records, out1)
        render.write_prompts_jsonl(render.render_all(rows), out2)

        assert out1.read_bytes() == out2.read_bytes()
        assert out1.read_bytes() != b""

    def test_written_jsonl_lines_round_trip_as_prompt_records(self, tmp_path):
        rows = _toy_vignette_rows()
        records = render.render_all(rows)
        out = tmp_path / "prompts.jsonl"
        render.write_prompts_jsonl(records, out)

        lines = out.read_text(encoding="utf-8").splitlines()
        assert len(lines) == len(records)
        reloaded = [PromptRecord(**json.loads(line)) for line in lines]
        assert reloaded == records


# ---------------------------------------------------------------------------
# CLI wiring
# ---------------------------------------------------------------------------


class TestCLI:
    def test_render_subcommand_registered(self):
        assert "render" in cli.SUBCOMMANDS

    def test_cli_help_mentions_render(self, capsys):
        with pytest.raises(SystemExit):
            cli.build_parser().parse_args(["--help"])
        out = capsys.readouterr().out
        assert "render" in out

    def _write_vignettes_csv(self, path: Path) -> None:
        rows = [VignetteRow(**r) for r in assemble.assemble(_two_family_matrix())]
        from knobe.schemas import write_csv_validated

        write_csv_validated(rows, path, VignetteRow)

    def test_cli_main_runs_render_successfully(self, tmp_path):
        vignettes_csv = tmp_path / "vignettes.csv"
        self._write_vignettes_csv(vignettes_csv)
        out = tmp_path / "prompts.jsonl"

        rc = cli.main(["render", str(vignettes_csv), "--out", str(out)])

        assert rc == 0
        assert out.exists()
        lines = out.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 48

    def test_cli_render_respects_formats_flag(self, tmp_path):
        vignettes_csv = tmp_path / "vignettes.csv"
        self._write_vignettes_csv(vignettes_csv)
        out = tmp_path / "prompts.jsonl"

        rc = cli.main(["render", str(vignettes_csv), "--out", str(out), "--formats", "raw"])

        assert rc == 0
        lines = out.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 24
        assert all(json.loads(line)["format"] == "raw" for line in lines)

    def test_cli_double_build_byte_equal(self, tmp_path):
        vignettes_csv = tmp_path / "vignettes.csv"
        self._write_vignettes_csv(vignettes_csv)
        out1 = tmp_path / "prompts_1.jsonl"
        out2 = tmp_path / "prompts_2.jsonl"

        assert cli.main(["render", str(vignettes_csv), "--out", str(out1)]) == 0
        assert cli.main(["render", str(vignettes_csv), "--out", str(out2)]) == 0

        assert out1.read_bytes() == out2.read_bytes()

    def test_cli_subprocess_console_script(self, tmp_path):
        vignettes_csv = tmp_path / "vignettes.csv"
        self._write_vignettes_csv(vignettes_csv)
        out = tmp_path / "prompts.jsonl"

        result = subprocess.run(
            [sys.executable, "-m", "knobe.cli", "render", str(vignettes_csv), "--out", str(out)],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, result.stderr
        assert out.exists()
