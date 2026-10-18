from collections.abc import Iterator
from pathlib import Path
from typing import Literal

import boto3
import pytest
from moto import mock_aws

from app.core.config import Settings, get_settings
from app.services.storage import LocalStorageBackend, S3StorageBackend, get_storage_backend


def test_get_storage_backend_returns_a_singleton() -> None:
    assert get_storage_backend() is get_storage_backend()


@pytest.fixture
def s3_backend() -> Iterator[S3StorageBackend]:
    settings = get_settings()
    with mock_aws():
        boto3.client("s3", region_name=settings.aws_region).create_bucket(
            Bucket=settings.s3_bucket_name,
            CreateBucketConfiguration={"LocationConstraint": settings.aws_region},
        )
        yield S3StorageBackend(bucket_name=settings.s3_bucket_name, region=settings.aws_region)


async def test_save_then_load_roundtrips_bytes(s3_backend: S3StorageBackend) -> None:
    await s3_backend.save(key="org1/file.pdf", data=b"hello world")
    loaded = await s3_backend.load(key="org1/file.pdf")

    assert loaded == b"hello world"


async def test_load_missing_key_raises(s3_backend: S3StorageBackend) -> None:
    with pytest.raises(FileNotFoundError):
        await s3_backend.load(key="does/not/exist.pdf")


async def test_delete_removes_object(s3_backend: S3StorageBackend) -> None:
    await s3_backend.save(key="org1/file.pdf", data=b"bytes")

    await s3_backend.delete(key="org1/file.pdf")

    with pytest.raises(FileNotFoundError):
        await s3_backend.load(key="org1/file.pdf")


async def test_delete_missing_key_is_a_no_op(s3_backend: S3StorageBackend) -> None:
    await s3_backend.delete(key="never/existed.pdf")


async def test_stream_missing_key_raises(s3_backend: S3StorageBackend) -> None:
    with pytest.raises(FileNotFoundError):
        async for _chunk in s3_backend.stream(key="does/not/exist.pdf"):
            pass


async def test_stream_yields_full_content_across_chunks(s3_backend: S3StorageBackend) -> None:
    data = b"x" * (1024 * 1024 + 10)
    await s3_backend.save(key="org1/large.bin", data=data)

    chunks = [chunk async for chunk in s3_backend.stream(key="org1/large.bin")]

    assert len(chunks) == 2
    assert b"".join(chunks) == data


async def test_local_backend_roundtrips_and_deletes(tmp_path: Path) -> None:
    storage = LocalStorageBackend(root=tmp_path)
    await storage.save(key="org-1/abc.pdf", data=b"%PDF-1.4 local")

    assert await storage.load(key="org-1/abc.pdf") == b"%PDF-1.4 local"
    chunks = [chunk async for chunk in storage.stream(key="org-1/abc.pdf")]
    assert b"".join(chunks) == b"%PDF-1.4 local"

    await storage.delete(key="org-1/abc.pdf")
    assert not (tmp_path / "org-1" / "abc.pdf").exists()
    await storage.delete(key="org-1/abc.pdf")  # deleting twice is harmless


async def test_local_backend_missing_key_raises_file_not_found(tmp_path: Path) -> None:
    storage = LocalStorageBackend(root=tmp_path)
    with pytest.raises(FileNotFoundError):
        await storage.load(key="org-1/missing.pdf")
    with pytest.raises(FileNotFoundError):
        _ = [chunk async for chunk in storage.stream(key="org-1/missing.pdf")]


async def test_local_backend_rejects_keys_outside_root(tmp_path: Path) -> None:
    storage = LocalStorageBackend(root=tmp_path / "uploads")
    with pytest.raises(ValueError, match="escapes"):
        await storage.save(key="../outside.pdf", data=b"x")
    assert not (tmp_path / "outside.pdf").exists()


@pytest.mark.parametrize(
    ("environment", "explicit", "expected"),
    [
        ("development", None, "local"),
        ("production", None, "s3"),
        ("staging", None, "s3"),
        ("production", "local", "local"),
        ("development", "s3", "s3"),
    ],
)
def test_storage_backend_defaults_to_local_only_in_development(
    environment: str, explicit: Literal["s3", "local"] | None, expected: str
) -> None:
    settings = Settings(environment=environment, storage_backend=explicit, jwt_secret_key="x" * 64)
    assert settings.resolved_storage_backend == expected
