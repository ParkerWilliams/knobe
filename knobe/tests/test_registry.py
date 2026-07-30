from pathlib import Path

import pytest
import yaml

from knobe.registry import (
    Family,
    RegistryConfigError,
    check_family_pairs,
    check_reviewer_model_forbidden,
    load_registry,
    model_key_for,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
MODELS_YAML = REPO_ROOT / "configs" / "models.yaml"


def _family(**overrides):
    kwargs = dict(
        pretrained="org/model-base", finetuned="org/model-instruct",
        tl_name="org/model-base", d_model=4096, n_layers=32, role="extension",
    )
    kwargs.update(overrides)
    return Family(**kwargs)


class TestRealRegistry:
    def test_loads_without_error(self):
        registry = load_registry(MODELS_YAML)
        assert "llama-3.1-8b" in registry
        assert "gemma-2-9b" in registry

    def test_core_families_present(self):
        registry = load_registry(MODELS_YAML)
        core = {name for name, fam in registry.items() if fam.role == "core"}
        assert core == {"llama-3.1-8b", "mistral-7b-v0.1", "gemma-2-9b"}

    def test_every_family_has_both_checkpoints(self):
        registry = load_registry(MODELS_YAML)
        for name, fam in registry.items():
            assert fam.pretrained, name
            assert fam.finetuned, name


class TestCheckFamilyPairs:
    def test_core_family_missing_checkpoint_is_hard_error(self):
        registry = {"foo": _family(role="core", finetuned=None)}
        with pytest.raises(RegistryConfigError):
            check_family_pairs(registry)

    def test_non_core_family_missing_checkpoint_is_warning_only(self):
        registry = {"foo": _family(role="debug", finetuned=None)}
        with pytest.warns(UserWarning):
            check_family_pairs(registry)  # must not raise

    def test_complete_family_no_warning_no_error(self, recwarn):
        registry = {"foo": _family(role="core")}
        check_family_pairs(registry)
        assert len(recwarn) == 0


class TestReviewerModelForbidden:
    def test_claude_in_pretrained_is_error(self):
        registry = {"foo": _family(pretrained="anthropic/claude-3-5-sonnet")}
        with pytest.raises(RegistryConfigError):
            check_reviewer_model_forbidden(registry)

    def test_claude_case_insensitive(self):
        registry = {"foo": _family(finetuned="Some/CLAUDE-model")}
        with pytest.raises(RegistryConfigError):
            check_reviewer_model_forbidden(registry)

    def test_no_claude_is_fine(self):
        registry = {"foo": _family()}
        check_reviewer_model_forbidden(registry)  # must not raise

    def test_load_registry_rejects_claude_in_yaml(self, tmp_path):
        bad_yaml = tmp_path / "models.yaml"
        bad_yaml.write_text(yaml.safe_dump({
            "families": {
                "sneaky": {
                    "pretrained": "anthropic/claude-3-5-haiku",
                    "finetuned": "anthropic/claude-3-5-haiku",
                    "d_model": 100, "n_layers": 10, "role": "debug",
                }
            }
        }))
        with pytest.raises(RegistryConfigError):
            load_registry(bad_yaml)


class TestModelKeyFor:
    def test_pretrained_suffix(self):
        assert model_key_for("llama-3.1-8b", "pretrained") == "llama-3.1-8b-pretrained"

    def test_finetuned_suffix_is_instruct(self):
        assert model_key_for("llama-3.1-8b", "finetuned") == "llama-3.1-8b-instruct"
