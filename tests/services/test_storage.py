from pathlib import Path

import pytest

from app.services.storage import LocalDiskStorageBackend, get_storage_backend


def test_get_storage_backend_returns_a_singleton() -> None:
    assert get_storage_backend() is get_storage_backend()


async def test_save_then_load_roundtrips_bytes(tmp_path: Path) -> None:
    backend = LocalDiskStorageBackend(tmp_path)

    await backend.save(key="org1/file.pdf", data=b"hello world")
    loaded = await backend.load(key="org1/file.pdf")

    assert loaded == b"hello world"


async def test_load_missing_key_raises(tmp_path: Path) -> None:
    backend = LocalDiskStorageBackend(tmp_path)

    with pytest.raises(FileNotFoundError):
        await backend.load(key="does/not/exist.pdf")


async def test_delete_removes_file(tmp_path: Path) -> None:
    backend = LocalDiskStorageBackend(tmp_path)
    await backend.save(key="org1/file.pdf", data=b"bytes")

    await backend.delete(key="org1/file.pdf")

    with pytest.raises(FileNotFoundError):
        await backend.load(key="org1/file.pdf")


async def test_delete_missing_key_is_a_no_op(tmp_path: Path) -> None:
    backend = LocalDiskStorageBackend(tmp_path)

    await backend.delete(key="never/existed.pdf")
