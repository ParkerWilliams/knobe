"""Tests for src/knobe/tracking.py (WO-1): set summaries, tracking-log
text, and balance math, ported from update_tracking_log.py and
generalized to the combined ALL_DOMAINS_master_matrix.csv.

Acceptance criteria under test (task-3-brief.md / WO1_generation.md):
  - status regression-pins the real matrix's subdomain imbalance
    (aesthetic 24, procedural 16, prudential 2, etiquette 0).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from knobe import tracking

REPO_ROOT = Path(__file__).resolve().parents[1]
REAL_MATRIX = REPO_ROOT / "data" / "authoring" / "ALL_DOMAINS_master_matrix.csv"


def _fam(family_id, domain="Environment", valence="MB", subdomain="", agent="The plant manager", goal="a goal"):
    return {
        "family_id": family_id, "domain": domain, "valence": valence,
        "nonmoral_subdomain": subdomain, "agent": agent, "goal": goal,
    }


# ---------------------------------------------------------------------------
# extract_set_number
# ---------------------------------------------------------------------------


class TestExtractSetNumber:
    def test_plain(self):
        assert tracking.extract_set_number("ENV-MB-01") == 1

    def test_ignores_revision_suffix(self):
        assert tracking.extract_set_number("ENV-MB-01r2") == 1

    def test_two_digit(self):
        assert tracking.extract_set_number("WORK-NEU-12") == 12

    def test_malformed_raises(self):
        with pytest.raises(ValueError):
            tracking.extract_set_number("not-a-family-id")


# ---------------------------------------------------------------------------
# summarize_sets / next_set_number / domain_set_count
# ---------------------------------------------------------------------------


class TestSummarizeSets:
    def test_groups_by_set_number_within_domain(self):
        families = [
            _fam("ENV-MB-01", agent="The plant manager", goal="cut costs"),
            _fam("ENV-MG-01", agent="The plant manager", goal="cut costs"),
            _fam("ENV-MB-02", agent="Maria", goal="win a grant"),
            _fam("FIN-MB-01", domain="Finance", agent="The auditor", goal="close the books"),
        ]
        summaries = tracking.summarize_sets(families, "Environment")
        assert [s.set_num for s in summaries] == [1, 2]
        assert summaries[0].agent == "The plant manager"
        assert summaries[0].goal == "cut costs"
        assert summaries[1].agent == "Maria"

    def test_ignores_other_domains(self):
        families = [_fam("FIN-MB-01", domain="Finance")]
        assert tracking.summarize_sets(families, "Environment") == []

    def test_revision_suffix_stays_in_same_set(self):
        families = [
            _fam("ENV-MB-01", agent="The plant manager", goal="cut costs"),
            _fam("ENV-MG-01r1", agent="The plant manager", goal="cut costs"),
        ]
        summaries = tracking.summarize_sets(families, "Environment")
        assert len(summaries) == 1
        assert summaries[0].set_num == 1

    def test_subdomain_taken_from_first_row_that_has_one(self):
        families = [
            _fam("ENV-MB-01", subdomain=""),
            _fam("ENV-NMB-01", subdomain="etiquette"),
        ]
        summaries = tracking.summarize_sets(families, "Environment")
        assert summaries[0].subdomain == "etiquette"

    def test_empty_matrix(self):
        assert tracking.summarize_sets([], "Environment") == []


class TestNextSetNumber:
    def test_empty_is_one(self):
        assert tracking.next_set_number([], "Environment") == 1

    def test_one_past_highest(self):
        families = [_fam("ENV-MB-01"), _fam("ENV-MB-03")]
        assert tracking.next_set_number(families, "Environment") == 4

    def test_domain_set_count(self):
        families = [_fam("ENV-MB-01"), _fam("ENV-MB-02"), _fam("FIN-MB-01", domain="Finance")]
        assert tracking.domain_set_count(families, "Environment") == 2
        assert tracking.domain_set_count(families, "Finance") == 1


# ---------------------------------------------------------------------------
# format_tracking_log -- the exact "already used" block text
# ---------------------------------------------------------------------------


class TestFormatTrackingLog:
    def test_no_sets_yet(self):
        assert tracking.format_tracking_log([]) == "(none yet)"

    def test_one_set_with_subdomain(self):
        summaries = [tracking.SetSummary(set_num=1, agent="The plant manager", goal="cut costs", subdomain="aesthetic")]
        block = tracking.format_tracking_log(summaries)
        assert block == '  - Set 01: agent = "The plant manager"; goal = "cut costs" [subdomain: aesthetic]'

    def test_set_without_subdomain_omits_bracket(self):
        summaries = [tracking.SetSummary(set_num=1, agent="Maria", goal="win a grant", subdomain="")]
        block = tracking.format_tracking_log(summaries)
        assert block == '  - Set 01: agent = "Maria"; goal = "win a grant"'
        assert "[subdomain" not in block

    def test_does_not_repeat_the_per_set_template_header(self):
        """PER_SET_PROMPT_TEMPLATE already supplies 'Already used in this
        domain...'; the tracking-log block itself must not duplicate it."""
        summaries = [tracking.SetSummary(set_num=1, agent="Maria", goal="win a grant", subdomain="")]
        block = tracking.format_tracking_log(summaries)
        assert "already used" not in block.lower()

    def test_multi_set_two_digit_padding(self):
        summaries = [tracking.SetSummary(set_num=n, agent=f"Agent{n}", goal=f"goal{n}", subdomain="") for n in (1, 12)]
        block = tracking.format_tracking_log(summaries)
        assert "Set 01:" in block
        assert "Set 12:" in block


# ---------------------------------------------------------------------------
# subdomain_tally / rarest_subdomain -- balance math
# ---------------------------------------------------------------------------


class TestSubdomainTally:
    def test_all_four_subdomains_always_present(self):
        families = [_fam("ENV-NMB-01", valence="NMB", subdomain="aesthetic")]
        tally = tracking.subdomain_tally(families)
        assert tally == {"prudential": 0, "procedural": 0, "aesthetic": 1, "etiquette": 0}

    def test_approved_only_excludes_pending(self):
        families = [
            {**_fam("ENV-NMB-01", valence="NMB", subdomain="aesthetic"), "human_approved": True},
            {**_fam("ENV-NMB-02", valence="NMB", subdomain="aesthetic"), "human_approved": False},
        ]
        approved_tally = tracking.subdomain_tally(families, approved_only=True)
        assert approved_tally["aesthetic"] == 1
        all_tally = tracking.subdomain_tally(families, approved_only=False)
        assert all_tally["aesthetic"] == 2

    def test_real_matrix_regression(self):
        """Acceptance criterion: status on the real current matrix reports
        exactly aesthetic 24, procedural 16, prudential 2, etiquette 0."""
        families = tracking.load_matrix_rows(REAL_MATRIX)
        tally = tracking.subdomain_tally(families, approved_only=True)
        assert tally == {"prudential": 2, "procedural": 16, "aesthetic": 24, "etiquette": 0}


class TestRarestSubdomain:
    def test_balanced_returns_none(self):
        tally = {"prudential": 5, "procedural": 5, "aesthetic": 5, "etiquette": 5}
        assert tracking.rarest_subdomain(tally) is None

    def test_within_2x_returns_none(self):
        tally = {"prudential": 5, "procedural": 10, "aesthetic": 8, "etiquette": 6}
        assert tracking.rarest_subdomain(tally) is None

    def test_nothing_generated_returns_none(self):
        tally = {"prudential": 0, "procedural": 0, "aesthetic": 0, "etiquette": 0}
        assert tracking.rarest_subdomain(tally) is None

    def test_real_matrix_deficit_is_etiquette(self):
        tally = {"prudential": 2, "procedural": 16, "aesthetic": 24, "etiquette": 0}
        assert tracking.rarest_subdomain(tally) == "etiquette"

    def test_deficit_exactly_at_2x_boundary_is_balanced(self):
        tally = {"prudential": 10, "procedural": 5, "aesthetic": 5, "etiquette": 5}
        assert tracking.rarest_subdomain(tally) is None

    def test_deficit_just_over_2x_boundary_flags(self):
        tally = {"prudential": 11, "procedural": 5, "aesthetic": 5, "etiquette": 5}
        assert tracking.rarest_subdomain(tally) == "procedural"  # tie-break: SUBDOMAIN_ORDER


# ---------------------------------------------------------------------------
# domain_valence_grid / approval_backlog / agent_diversity
# ---------------------------------------------------------------------------


class TestDomainValenceGrid:
    def test_counts_by_domain_and_valence(self):
        families = [
            _fam("ENV-MB-01", valence="MB"),
            _fam("ENV-MB-02", valence="MB"),
            _fam("ENV-MG-01", valence="MG"),
            _fam("FIN-MB-01", domain="Finance", valence="MB"),
        ]
        grid = tracking.domain_valence_grid(families)
        assert grid["Environment"]["MB"] == 2
        assert grid["Environment"]["MG"] == 1
        assert grid["Environment"]["NEU"] == 0
        assert grid["Finance"]["MB"] == 1


class TestApprovalBacklog:
    def test_lists_unapproved_family_ids(self):
        families = [
            {**_fam("ENV-MB-01"), "human_approved": True},
            {**_fam("ENV-MB-02"), "human_approved": False},
        ]
        assert tracking.approval_backlog(families) == ["ENV-MB-02"]


class TestAgentDiversity:
    def test_role_title_vs_proper_name_counted_once_per_set(self):
        families = [
            _fam("ENV-MB-01", agent="The plant manager"),
            _fam("ENV-MG-01", agent="The plant manager"),  # same set -- must not double count
            _fam("ENV-MB-02", agent="Maria"),
        ]
        diversity = tracking.agent_diversity(families)
        assert diversity["role_title_count"] == 1
        assert diversity["proper_name_count"] == 1

    def test_flags_agent_repeated_across_sets_within_domain(self):
        families = [
            _fam("ENV-MB-01", agent="The plant manager"),
            _fam("ENV-MB-02", agent="The plant manager"),
            _fam("FIN-MB-01", domain="Finance", agent="The plant manager"),
        ]
        diversity = tracking.agent_diversity(families)
        assert diversity["repeated_agents_by_domain"]["Environment"] == {"The plant manager": 2}
        assert "Finance" not in diversity["repeated_agents_by_domain"]

    def test_no_repeats_omits_domain_key(self):
        families = [_fam("ENV-MB-01", agent="The plant manager"), _fam("ENV-MB-02", agent="Maria")]
        diversity = tracking.agent_diversity(families)
        assert diversity["repeated_agents_by_domain"] == {}


# ---------------------------------------------------------------------------
# load_matrix_rows -- backfill behavior + provenance parsing
# ---------------------------------------------------------------------------


class TestLoadMatrixRows:
    def test_missing_file_returns_empty(self, tmp_path):
        assert tracking.load_matrix_rows(tmp_path / "nope.csv") == []

    def test_backfills_human_approved_when_column_absent(self):
        """The real matrix predates the WO-1 provenance columns entirely;
        every row must be treated as already human-approved."""
        rows = tracking.load_matrix_rows(REAL_MATRIX)
        assert len(rows) == 105
        assert all(r["human_approved"] is True for r in rows)
        assert all(r["generator_model"] == "" for r in rows)

    def test_reads_provenance_columns_when_present(self, tmp_path):
        matrix = tmp_path / "matrix.csv"
        matrix.write_text(
            "family_id,domain,valence,nonmoral_subdomain,agent,goal,common_action,uncommon_action,"
            "affected_entity,low_evocative_outcome,high_evocative_outcome,outcome_verb,"
            "generator_model,ingest_date,human_approved\n"
            "ENV-MB-01,Environment,MB,,The plant manager,cut costs,switched providers,built in-house,"
            "the town,a low fact,a high fact,contaminate the supply,claude-x,2026-01-01,False\n",
            encoding="utf-8",
        )
        rows = tracking.load_matrix_rows(matrix)
        assert rows[0]["human_approved"] is False
        assert rows[0]["generator_model"] == "claude-x"
        assert rows[0]["ingest_date"] == "2026-01-01"
