import csv
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from knobe import constants
from knobe.schemas import (
    CuratedRow,
    FamilyRow,
    FamilySplit,
    JobRecord,
    PatchInfo,
    PatchRecord,
    ProbeRecord,
    PromptRecord,
    ReleaseCounts,
    ReleaseManifest,
    ResultRecord,
    VignetteRow,
    append_jsonl,
    read_csv_validated,
    read_jsonl,
    sha256_for_messages,
    sha256_for_text,
    write_csv_validated,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
MASTER_MATRIX = REPO_ROOT / "data" / "authoring" / "ALL_DOMAINS_master_matrix.csv"


def _minimal_family_kwargs(**overrides):
    kwargs = dict(
        family_id="ENV-MB-01",
        domain="Environment",
        valence="MB",
        nonmoral_subdomain="",
        agent="The plant manager",
        goal="reduce operating costs",
        common_action="switched providers",
        uncommon_action="commissioned a custom process",
        affected_entity="the town",
        low_evocative_outcome="an audit found levels had risen",
        high_evocative_outcome="residents reported an outbreak",
        outcome_verb="contaminate the water supply",
    )
    kwargs.update(overrides)
    return kwargs


def _minimal_vignette_kwargs(**overrides):
    kwargs = dict(
        variant_id="ENV-MB-01-A",
        family_id="ENV-MB-01",
        domain="Environment",
        valence="MB",
        nonmoral_subdomain="",
        sign="bad",
        typicality="common",
        evocativeness="low",
        scenario="The plant manager did a thing.",
        q_intentionality="Did the plant manager intentionally do it? 0-10.",
        q_blame="How blameworthy? 0-10.",
        q_praise="How praiseworthy? 0-10.",
    )
    kwargs.update(overrides)
    return kwargs


class TestFamilyRow:
    def test_valid_family_row_round_trips(self):
        row = FamilyRow(**_minimal_family_kwargs())
        assert row.family_id == "ENV-MB-01"
        assert row.human_approved is False

    def test_bad_valence_rejected(self):
        with pytest.raises(ValidationError):
            FamilyRow(**_minimal_family_kwargs(valence="XX"))

    def test_nmb_without_subdomain_rejected(self):
        with pytest.raises(ValidationError):
            FamilyRow(**_minimal_family_kwargs(valence="NMB", nonmoral_subdomain=""))

    def test_nmb_with_valid_subdomain_accepted(self):
        row = FamilyRow(**_minimal_family_kwargs(valence="NMB", nonmoral_subdomain="aesthetic"))
        assert row.nonmoral_subdomain == "aesthetic"

    def test_nmb_with_invalid_subdomain_rejected(self):
        with pytest.raises(ValidationError):
            FamilyRow(**_minimal_family_kwargs(valence="NMB", nonmoral_subdomain="bogus"))

    def test_mb_with_nonempty_subdomain_rejected(self):
        """Only empty is allowed for MB/MG/NEU -- a non-empty subdomain on a
        moral row is a real error, not a benign extra field."""
        with pytest.raises(ValidationError):
            FamilyRow(**_minimal_family_kwargs(valence="MB", nonmoral_subdomain="aesthetic"))

    def test_bad_family_id_format_rejected(self):
        with pytest.raises(ValidationError):
            FamilyRow(**_minimal_family_kwargs(family_id="not-a-valid-id"))

    def test_revision_suffix_family_id_accepted(self):
        row = FamilyRow(**_minimal_family_kwargs(family_id="ENV-MB-01r2"))
        assert row.family_id == "ENV-MB-01r2"

    def test_missing_required_field_rejected(self):
        with pytest.raises(ValidationError):
            FamilyRow(**_minimal_family_kwargs(agent=""))

    def test_provenance_fields_tolerated_absent(self):
        kwargs = _minimal_family_kwargs()
        row = FamilyRow(**kwargs)
        assert row.generator_model is None
        assert row.ingest_date is None
        assert row.human_approved is False

    def test_unknown_field_rejected(self):
        with pytest.raises(ValidationError):
            FamilyRow(**_minimal_family_kwargs(bogus_field="x"))


class TestRealMasterMatrix:
    def test_real_matrix_loads_as_105_valid_family_rows(self):
        rows = read_csv_validated(MASTER_MATRIX, FamilyRow)
        assert len(rows) == 105
        assert all(isinstance(r, FamilyRow) for r in rows)


class TestVignetteRow:
    def test_valid_vignette_row(self):
        row = VignetteRow(**_minimal_vignette_kwargs())
        assert row.variant_id == "ENV-MB-01-A"

    @pytest.mark.parametrize(
        "typicality,evocativeness,bad_variant_id",
        [
            ("common", "low", "ENV-MB-01-B"),
            ("common", "high", "ENV-MB-01-A"),
            ("uncommon", "low", "ENV-MB-01-A"),
            ("uncommon", "high", "ENV-MB-01-C"),
        ],
    )
    def test_variant_letter_disagreement_rejected(self, typicality, evocativeness, bad_variant_id):
        with pytest.raises(ValidationError):
            VignetteRow(**_minimal_vignette_kwargs(
                variant_id=bad_variant_id, typicality=typicality, evocativeness=evocativeness,
            ))

    def test_sign_disagreement_with_valence_rejected(self):
        with pytest.raises(ValidationError):
            VignetteRow(**_minimal_vignette_kwargs(valence="MB", sign="good"))

    def test_neu_sign_must_be_na(self):
        row = VignetteRow(**_minimal_vignette_kwargs(
            variant_id="ENV-NEU-01-A", family_id="ENV-NEU-01", valence="NEU", sign="na",
        ))
        assert row.sign == "na"
        with pytest.raises(ValidationError):
            VignetteRow(**_minimal_vignette_kwargs(
                variant_id="ENV-NEU-01-A", family_id="ENV-NEU-01", valence="NEU", sign="bad",
            ))

    def test_csv_fieldnames_match_output_fieldnames_constant(self):
        assert VignetteRow.csv_fieldnames() == constants.OUTPUT_FIELDNAMES


class TestCuratedRow:
    def _kwargs(self, **overrides):
        kwargs = _minimal_vignette_kwargs()
        kwargs.update(
            moral_relevance=9,
            moral_relevance_raw="9",
            severity=7,
            severity_raw="7",
            vividness=6,
            vividness_raw="6",
            typicality_perception=5,
            typicality_perception_raw="5",
            individual_flags="",
            pair_flag="",
            reviewer_model="claude-sonnet-4-6",
            curation_date="2026-07-27",
            accepted=True,
        )
        kwargs.update(overrides)
        return kwargs

    def test_valid_curated_row(self):
        row = CuratedRow(**self._kwargs())
        assert row.accepted is True

    def test_empty_string_rating_becomes_none(self):
        row = CuratedRow(**self._kwargs(moral_relevance="", moral_relevance_raw="unparseable"))
        assert row.moral_relevance is None

    def test_rating_out_of_range_rejected(self):
        with pytest.raises(ValidationError):
            CuratedRow(**self._kwargs(severity=11))

    def test_accepted_string_coercion(self):
        row = CuratedRow(**self._kwargs(accepted="False"))
        assert row.accepted is False

    def test_csv_round_trip(self, tmp_path):
        row = CuratedRow(**self._kwargs())
        out = tmp_path / "curated.csv"
        write_csv_validated([row], out, CuratedRow)
        reloaded = read_csv_validated(out, CuratedRow)
        assert len(reloaded) == 1
        assert reloaded[0] == row

    def test_csv_round_trip_with_unparseable_rating(self, tmp_path):
        row = CuratedRow(**self._kwargs(severity="", severity_raw="ten"))
        out = tmp_path / "curated.csv"
        write_csv_validated([row], out, CuratedRow)
        with open(out, newline="", encoding="utf-8") as f:
            raw_rows = list(csv.DictReader(f))
        assert raw_rows[0]["severity"] == ""
        reloaded = read_csv_validated(out, CuratedRow)
        assert reloaded[0].severity is None


class TestPromptRecord:
    def test_raw_format_valid(self):
        text = "Read carefully..."
        rec = PromptRecord(
            prompt_id="ENV-MB-01-A::intentionality::raw",
            variant_id="ENV-MB-01-A",
            question_type="intentionality",
            format="raw",
            text=text,
            messages=None,
            sha256=sha256_for_text(text),
        )
        assert rec.messages is None

    def test_chat_format_requires_messages(self):
        with pytest.raises(ValidationError):
            PromptRecord(
                prompt_id="ENV-MB-01-A::intentionality::chat",
                variant_id="ENV-MB-01-A",
                question_type="intentionality",
                format="chat",
                text="whatever",
                messages=None,
                sha256=sha256_for_text("whatever"),
            )

    def test_raw_format_rejects_messages(self):
        with pytest.raises(ValidationError):
            PromptRecord(
                prompt_id="ENV-MB-01-A::intentionality::raw",
                variant_id="ENV-MB-01-A",
                question_type="intentionality",
                format="raw",
                text="whatever",
                messages=[{"role": "user", "content": "whatever"}],
                sha256=sha256_for_text("whatever"),
            )

    def test_chat_format_valid_with_messages(self):
        messages = [{"role": "user", "content": "Scenario: ...\n\nQuestion: ...\nAnswer:"}]
        rec = PromptRecord(
            prompt_id="ENV-MB-01-A::intentionality::chat",
            variant_id="ENV-MB-01-A",
            question_type="intentionality",
            format="chat",
            text="Scenario: ...\n\nQuestion: ...\nAnswer:",
            messages=messages,
            sha256=sha256_for_messages(messages),
        )
        assert rec.messages == messages

    def test_prompt_id_mismatch_rejected(self):
        with pytest.raises(ValidationError):
            PromptRecord(
                prompt_id="WRONG-ID",
                variant_id="ENV-MB-01-A",
                question_type="intentionality",
                format="raw",
                text="whatever",
                sha256=sha256_for_text("whatever"),
            )

    def test_bad_sha256_shape_rejected(self):
        with pytest.raises(ValidationError):
            PromptRecord(
                prompt_id="ENV-MB-01-A::intentionality::raw",
                variant_id="ENV-MB-01-A",
                question_type="intentionality",
                format="raw",
                text="whatever",
                sha256="not-a-hash",
            )

    def test_sha256_for_text_matches_hashlib(self):
        import hashlib

        assert sha256_for_text("hello") == hashlib.sha256(b"hello").hexdigest()

    def test_sha256_for_messages_is_order_stable(self):
        m1 = [{"role": "user", "content": "hi"}]
        m2 = [{"content": "hi", "role": "user"}]
        assert sha256_for_messages(m1) == sha256_for_messages(m2)


class TestResultRecord:
    def _kwargs(self, **overrides):
        kwargs = dict(
            job_id="job-1",
            prompt_id="ENV-MB-01-A::intentionality::raw",
            model_key="llama-3.1-8b-instruct",
            sample_idx=0,
            temperature=1.0,
            seed=12345,
            raw_response="7",
            parsed_rating=7,
            parse_ok=True,
            parse_method="regex",
            logprobs_0_10=None,
            model_revision="abc123",
            runner_version="0.1.0",
            timestamp=1234567890.0,
        )
        kwargs.update(overrides)
        return kwargs

    def test_valid_result_record(self):
        rec = ResultRecord(**self._kwargs())
        assert rec.parsed_rating == 7

    def test_no_denormalized_item_fields(self):
        forbidden = {"family_id", "valence", "typicality", "evocativeness", "domain",
                     "nonmoral_subdomain", "tuning_status", "model_family"}
        assert forbidden.isdisjoint(ResultRecord.model_fields.keys())

    def test_logprobs_wrong_length_rejected(self):
        with pytest.raises(ValidationError):
            ResultRecord(**self._kwargs(logprobs_0_10=[0.1] * 10, parse_method="logit_fallback"))

    def test_logprobs_correct_length_accepted(self):
        rec = ResultRecord(**self._kwargs(logprobs_0_10=[0.1] * 11, parse_method="logit_fallback"))
        assert len(rec.logprobs_0_10) == 11

    def test_float_parsed_rating_accepted_for_logit_fallback(self):
        rec = ResultRecord(**self._kwargs(parsed_rating=5.42, parse_method="logit_fallback"))
        assert rec.parsed_rating == pytest.approx(5.42)

    def test_jsonl_round_trip(self, tmp_path):
        rec = ResultRecord(**self._kwargs())
        out = tmp_path / "results.jsonl"
        with open(out, "a", encoding="utf-8") as f:
            append_jsonl(rec, f)
        reloaded = read_jsonl(out, ResultRecord)
        assert reloaded == [rec]

    def test_jsonl_append_is_resumable(self, tmp_path):
        out = tmp_path / "results.jsonl"
        rec1 = ResultRecord(**self._kwargs(job_id="job-1"))
        rec2 = ResultRecord(**self._kwargs(job_id="job-2"))
        with open(out, "a", encoding="utf-8") as f:
            append_jsonl(rec1, f)
        with open(out, "a", encoding="utf-8") as f:
            append_jsonl(rec2, f)
        reloaded = read_jsonl(out, ResultRecord)
        assert [r.job_id for r in reloaded] == ["job-1", "job-2"]


class TestPatchRecord:
    def test_valid_patch_record(self):
        rec = PatchRecord(
            job_id="job-1", prompt_id="ENV-MB-01-A::intentionality::raw",
            model_key="llama-3.1-8b-instruct", sample_idx=0, temperature=1.0, seed=1,
            raw_response="7", parsed_rating=7, parse_ok=True, parse_method="regex",
            model_revision="abc", runner_version="0.1.0", timestamp=1.0,
            patch=PatchInfo(donor="pretrained", layers=[12], positions="all"),
            scoring="logits_0_10",
        )
        assert rec.patch.donor == "pretrained"
        assert rec.scoring == "logits_0_10"

    def test_bad_scoring_literal_rejected(self):
        with pytest.raises(ValidationError):
            PatchRecord(
                job_id="job-1", prompt_id="p", model_key="m", sample_idx=0,
                temperature=1.0, seed=1, raw_response="7", parsed_rating=7,
                parse_ok=True, parse_method="regex", model_revision="abc",
                runner_version="0.1.0", timestamp=1.0,
                patch=PatchInfo(donor="pretrained", layers=[1]),
                scoring="bogus",
            )


class TestProbeRecord:
    def test_valid_probe_record(self):
        rec = ProbeRecord(
            model_key="gemma-2-9b-instruct",
            construct="blame_rating",
            layer=15,
            weights_ref="probes/gemma-2-9b-instruct/blame_rating__layer15.npy",
            split=FamilySplit(train=["ENV-MB-01"], test=["ENV-MB-02"]),
            cv_score=0.83,
            residualization_recipe="regress out severity, vividness",
        )
        assert rec.construct == "blame_rating"

    def test_bad_construct_rejected(self):
        with pytest.raises(ValidationError):
            ProbeRecord(
                model_key="m", construct="not_a_construct", layer=1,
                weights_ref="x", split=FamilySplit(train=[], test=[]),
                cv_score=0.5, residualization_recipe="none",
            )


class TestReleaseManifest:
    def test_valid_manifest(self):
        # by_valence/by_domain report BOTH levels, labeled (researcher
        # decision d2, docs/DECISIONS_FOR_HUMANS.md item (d)): e.g.
        # {"MB": {"families": 50, "variants": 200}, ...}.
        manifest = ReleaseManifest(
            release="v1.0",
            created="2026-07-27T00:00:00Z",
            git_commit="deadbeef",
            files={"vignettes.csv": {"sha256": "a" * 64, "rows": 1000}},
            counts=ReleaseCounts(
                families=250, variants=1000,
                by_valence={"MB": {"families": 50, "variants": 200}},
                by_domain={"Environment": {"families": 25, "variants": 100}},
            ),
            gates_passed=["G0", "G1"],
            changelog="initial release",
        )
        assert manifest.counts.families == 250
        assert manifest.files["vignettes.csv"].rows == 1000
        assert manifest.counts.by_valence["MB"].families == 50
        assert manifest.counts.by_valence["MB"].variants == 200
        assert manifest.counts.by_domain["Environment"].variants == 100
