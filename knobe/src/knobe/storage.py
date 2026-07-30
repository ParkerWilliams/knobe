"""S3/local storage adapter (WO-5; master spec §1.1).

Cluster access details (how to connect to the H200 box, which S3 bucket to
use, credentials) are NOT part of this repo -- they live in a local-only
cluster folder the researchers drop in separately. This module is the thin,
storage-backend-agnostic adapter surface that the cluster instructions
configure (via ``configs/storage.yaml``): every H200 stage that needs
durable, off-the-ephemeral-node storage talks to a ``StorageBackend``, never
to boto3 or a bucket name directly.

Deliberately standalone: nothing in this module imports from
``elicit_vllm.py`` or any other stage module, so it can be tested (and
reused by a later mechanistic-interp stage's activation-cache sync) in
isolation.

Three implementations:
  - ``NullStorage`` -- no-op. The default when no ``--storage`` config is
    given; every push/pull/exists/list is inert, so a script that never
    configures storage behaves exactly as if durability sync were disabled
    (fine for a local/offline G0 rehearsal).
  - ``LocalDirStorage`` -- a local directory pretending to be the bucket.
    This is what tests use to exercise the sync logic without any network
    or AWS credentials, and it's also a legitimate lightweight option for a
    single-machine run that just wants a second on-disk copy.
  - ``S3Storage`` -- the real adapter, backed by ``boto3`` (guarded import:
    constructing it without the ``aws`` extra installed raises a clear
    ``RuntimeError``, not an ImportError at module load time, so importing
    ``knobe.storage`` never requires boto3 -- common-context.md constraint
    7 / master spec §7's "heavy deps must be optional extras with guarded
    imports").
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Literal, Protocol

import yaml
from pydantic import BaseModel, ConfigDict

try:
    import boto3
except ImportError:  # pragma: no cover -- exercised whenever the 'aws'
    # extra isn't installed; S3Storage.__init__ is the only thing that ever
    # touches this, and it raises a clear RuntimeError instead.
    boto3 = None


class StorageBackend(Protocol):
    """The adapter surface every H200 stage's durability loop talks to.
    ``remote_key`` is a backend-relative path (e.g.
    ``"results/v1.0/llama-3.1-8b-instruct/results.jsonl"``) -- callers never
    need to know whether that resolves to an S3 object key or a path under
    a local directory."""

    def push(self, local_path: str | Path, remote_key: str) -> None:
        """Uploads/copies ``local_path`` to ``remote_key``."""
        ...

    def pull(self, remote_key: str, local_path: str | Path) -> None:
        """Downloads/copies ``remote_key`` to ``local_path``. Raises if
        ``remote_key`` doesn't exist -- callers should check ``exists``
        first when the absence of a prior checkpoint is an expected case."""
        ...

    def exists(self, remote_key: str) -> bool:
        """Whether ``remote_key`` is present in the backend."""
        ...

    def list(self, prefix: str) -> list[str]:
        """Every remote_key under ``prefix``."""
        ...


class NullStorage:
    """No-op backend -- the default when no storage config is supplied.
    Every H200 stage must work (just without off-node durability) when
    this is the configured backend, so G0 rehearsals never require any
    storage setup at all."""

    def push(self, local_path: str | Path, remote_key: str) -> None:
        pass

    def pull(self, remote_key: str, local_path: str | Path) -> None:
        raise FileNotFoundError(
            f"NullStorage has no object {remote_key!r} -- no storage backend is "
            f"configured (pass --storage configs/storage.yaml to enable one)."
        )

    def exists(self, remote_key: str) -> bool:
        return False

    def list(self, prefix: str) -> list[str]:
        return []


class LocalDirStorage:
    """A local directory pretending to be the bucket -- what tests use, and
    a legitimate lightweight real backend for a single-machine run."""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, remote_key: str) -> Path:
        return self.root / remote_key

    def push(self, local_path: str | Path, remote_key: str) -> None:
        dest = self._path(remote_key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(local_path, dest)

    def pull(self, remote_key: str, local_path: str | Path) -> None:
        src = self._path(remote_key)
        if not src.exists():
            raise FileNotFoundError(f"LocalDirStorage has no object {remote_key!r} under {self.root}")
        local_path = Path(local_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, local_path)

    def exists(self, remote_key: str) -> bool:
        return self._path(remote_key).exists()

    def list(self, prefix: str) -> list[str]:
        out = []
        for p in self.root.rglob("*"):
            if not p.is_file():
                continue
            rel = p.relative_to(self.root).as_posix()
            if rel.startswith(prefix):
                out.append(rel)
        return sorted(out)


class S3Storage:
    """The real S3 adapter (boto3-backed). Bucket/prefix come from
    ``configs/storage.yaml`` -- NOTE: the actual bucket name and
    credentials for a real run come from the local-only cluster folder per
    master spec §1.1; this class is the adapter the cluster instructions
    configure, not a place to hardcode a bucket.

    Raises at CONSTRUCTION time (not import time) if ``boto3`` isn't
    installed, mirroring ``curate.AnthropicClient``'s guarded-import
    pattern -- so importing this module, and every non-S3 code path,
    never requires the ``aws`` extra."""

    def __init__(self, bucket: str, prefix: str = "", region: str | None = None):
        if boto3 is None:
            raise RuntimeError(
                "boto3 is required for S3Storage -- install the 'aws' extra "
                "(`uv pip install -e '.[aws]'`), or use LocalDirStorage/NullStorage instead."
            )
        self.bucket = bucket
        self.prefix = prefix.strip("/")
        self._client = boto3.client("s3", region_name=region) if region else boto3.client("s3")

    def _key(self, remote_key: str) -> str:
        remote_key = remote_key.lstrip("/")
        return f"{self.prefix}/{remote_key}" if self.prefix else remote_key

    def push(self, local_path: str | Path, remote_key: str) -> None:
        self._client.upload_file(str(local_path), self.bucket, self._key(remote_key))

    def pull(self, remote_key: str, local_path: str | Path) -> None:
        local_path = Path(local_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        self._client.download_file(self.bucket, self._key(remote_key), str(local_path))

    def exists(self, remote_key: str) -> bool:
        try:
            self._client.head_object(Bucket=self.bucket, Key=self._key(remote_key))
            return True
        except Exception:
            return False

    def list(self, prefix: str) -> list[str]:
        full_prefix = self._key(prefix)
        keys: list[str] = []
        paginator = self._client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket, Prefix=full_prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                # Strip our own prefix back off so callers see the same
                # remote_key shape they'd pass to push/pull/exists.
                keys.append(key[len(self.prefix) + 1 :] if self.prefix else key)
        return keys


# ---------------------------------------------------------------------------
# configs/storage.yaml loading
# ---------------------------------------------------------------------------

BackendName = Literal["s3", "local", "null"]


class StorageConfig(BaseModel):
    """Schema for ``configs/storage.yaml``. Not a ``KnobeModel`` (this
    isn't a pipeline data artifact validated at every stage boundary per
    common-context.md constraint 3 -- it's a small, standalone runtime
    config for this one module), but still ``extra="forbid"`` so a typo'd
    key fails loudly instead of being silently ignored."""

    model_config = ConfigDict(extra="forbid")

    backend: BackendName = "null"
    bucket: str | None = None
    prefix: str = ""
    region: str | None = None
    root: str | None = None  # "local" backend only: the local directory standing in for the bucket


def build_storage(config: StorageConfig) -> StorageBackend:
    if config.backend == "null":
        return NullStorage()
    if config.backend == "local":
        if not config.root:
            raise ValueError("storage config backend='local' requires 'root' (the local directory).")
        return LocalDirStorage(config.root)
    if config.backend == "s3":
        if not config.bucket:
            raise ValueError("storage config backend='s3' requires 'bucket'.")
        return S3Storage(bucket=config.bucket, prefix=config.prefix, region=config.region)
    raise ValueError(f"unknown storage backend {config.backend!r}")  # pragma: no cover -- Literal already guards this


def load_storage_config(path: str | Path) -> StorageBackend:
    """Loads ``configs/storage.yaml`` (or an equivalent path) and returns
    the configured ``StorageBackend``."""
    path = Path(path)
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return build_storage(StorageConfig(**data))
