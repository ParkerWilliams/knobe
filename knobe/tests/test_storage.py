"""Tests for src/knobe/storage.py (WO-5): the StorageBackend adapter surface
(push/pull/exists/list) and its three implementations.

Acceptance criteria under this module's remit (task-5-brief.md):
  - LocalDirStorage: push/pull/exists/list all work against a local
    directory standing in for a bucket (what the elicit_vllm.py tests use
    to exercise checkpoint-interval + crash-time sync without any network).
  - NullStorage: every operation is inert (push/exists/list), pull raises
    (nothing was ever configured to pull FROM).
  - S3Storage: raises a clear RuntimeError at construction (not import
    time) when boto3 isn't installed -- this repo's test environment never
    has the 'aws' extra installed, so this also proves knobe.storage
    imports cleanly without boto3.
  - configs/storage.yaml loading dispatches on `backend` to the right impl.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from knobe import storage


class TestNullStorage:
    def test_push_is_a_noop(self, tmp_path):
        s = storage.NullStorage()
        local = tmp_path / "f.txt"
        local.write_text("hello")
        s.push(local, "some/key")  # must not raise

    def test_pull_raises_file_not_found(self, tmp_path):
        s = storage.NullStorage()
        with pytest.raises(FileNotFoundError):
            s.pull("some/key", tmp_path / "out.txt")

    def test_exists_always_false(self):
        assert storage.NullStorage().exists("anything") is False

    def test_list_always_empty(self):
        assert storage.NullStorage().list("prefix") == []


class TestLocalDirStorage:
    def test_push_then_pull_roundtrip(self, tmp_path):
        bucket_dir = tmp_path / "bucket"
        local_dir = tmp_path / "local"
        local_dir.mkdir()
        s = storage.LocalDirStorage(bucket_dir)

        src = local_dir / "results.jsonl"
        src.write_text('{"a": 1}\n{"a": 2}\n')
        s.push(src, "results/v1.0/m/results.jsonl")

        assert s.exists("results/v1.0/m/results.jsonl") is True
        assert (bucket_dir / "results" / "v1.0" / "m" / "results.jsonl").read_text() == src.read_text()

        dest = local_dir / "pulled.jsonl"
        s.pull("results/v1.0/m/results.jsonl", dest)
        assert dest.read_text() == src.read_text()

    def test_exists_false_for_missing_key(self, tmp_path):
        s = storage.LocalDirStorage(tmp_path / "bucket")
        assert s.exists("does/not/exist.jsonl") is False

    def test_pull_missing_key_raises(self, tmp_path):
        s = storage.LocalDirStorage(tmp_path / "bucket")
        with pytest.raises(FileNotFoundError):
            s.pull("does/not/exist.jsonl", tmp_path / "out.jsonl")

    def test_push_overwrites_existing_key(self, tmp_path):
        s = storage.LocalDirStorage(tmp_path / "bucket")
        src = tmp_path / "src.txt"
        src.write_text("v1")
        s.push(src, "k")
        src.write_text("v2")
        s.push(src, "k")
        dest = tmp_path / "out.txt"
        s.pull("k", dest)
        assert dest.read_text() == "v2"

    def test_list_returns_keys_under_prefix_only(self, tmp_path):
        s = storage.LocalDirStorage(tmp_path / "bucket")
        src = tmp_path / "src.txt"
        src.write_text("x")
        s.push(src, "results/v1.0/m1/results.jsonl")
        s.push(src, "results/v1.0/m2/results.jsonl")
        s.push(src, "runlog/v1.0/runlog.jsonl")

        under_results = s.list("results/v1.0")
        assert set(under_results) == {"results/v1.0/m1/results.jsonl", "results/v1.0/m2/results.jsonl"}
        assert s.list("runlog") == ["runlog/v1.0/runlog.jsonl"]
        assert s.list("nonexistent-prefix") == []

    def test_root_created_on_construction(self, tmp_path):
        root = tmp_path / "does" / "not" / "exist" / "yet"
        assert not root.exists()
        storage.LocalDirStorage(root)
        assert root.exists()


class TestS3StorageGuardedImport:
    def test_raises_runtime_error_at_construction_not_import(self):
        assert storage.boto3 is None  # precondition: 'aws' extra not installed in this env
        with pytest.raises(RuntimeError, match="boto3"):
            storage.S3Storage(bucket="my-bucket")

    def test_module_imports_cleanly_without_boto3(self):
        # If we got this far, `import knobe.storage` already succeeded
        # despite boto3 being unavailable -- this test just makes that
        # invariant explicit and regression-checkable.
        assert storage.boto3 is None


class TestStorageConfigLoading:
    def test_null_backend_default(self, tmp_path):
        path = tmp_path / "storage.yaml"
        path.write_text(yaml.safe_dump({"backend": "null"}))
        s = storage.load_storage_config(path)
        assert isinstance(s, storage.NullStorage)

    def test_empty_file_defaults_to_null(self, tmp_path):
        path = tmp_path / "storage.yaml"
        path.write_text("")
        s = storage.load_storage_config(path)
        assert isinstance(s, storage.NullStorage)

    def test_local_backend(self, tmp_path):
        bucket_dir = tmp_path / "bucket"
        path = tmp_path / "storage.yaml"
        path.write_text(yaml.safe_dump({"backend": "local", "root": str(bucket_dir)}))
        s = storage.load_storage_config(path)
        assert isinstance(s, storage.LocalDirStorage)
        assert s.root == bucket_dir

    def test_local_backend_missing_root_rejected(self, tmp_path):
        path = tmp_path / "storage.yaml"
        path.write_text(yaml.safe_dump({"backend": "local"}))
        with pytest.raises(ValueError, match="root"):
            storage.load_storage_config(path)

    def test_s3_backend_missing_bucket_rejected(self, tmp_path):
        path = tmp_path / "storage.yaml"
        path.write_text(yaml.safe_dump({"backend": "s3"}))
        with pytest.raises(ValueError, match="bucket"):
            storage.load_storage_config(path)

    def test_s3_backend_without_boto3_raises_at_build(self, tmp_path):
        path = tmp_path / "storage.yaml"
        path.write_text(yaml.safe_dump({"backend": "s3", "bucket": "my-bucket", "prefix": "knobe/v1.0"}))
        with pytest.raises(RuntimeError, match="boto3"):
            storage.load_storage_config(path)

    def test_unknown_field_rejected(self, tmp_path):
        path = tmp_path / "storage.yaml"
        path.write_text(yaml.safe_dump({"backend": "null", "bogus": "x"}))
        with pytest.raises(Exception):
            storage.load_storage_config(path)
