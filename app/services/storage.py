import asyncio
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Protocol

from app.core.config import get_settings

_STREAM_CHUNK_SIZE = 1024 * 1024


class StorageBackend(Protocol):
    async def save(self, *, key: str, data: bytes) -> None: ...
    async def load(self, *, key: str) -> bytes: ...
    async def delete(self, *, key: str) -> None: ...
    def stream(self, *, key: str) -> AsyncIterator[bytes]: ...


class LocalDiskStorageBackend:
    """Dev/prod-lite storage backend: files live under HACCP_STORAGE_ROOT.

    Swappable for an S3 (or other object-store) backend later purely by
    implementing the same StorageBackend protocol and changing what
    get_storage_backend() returns — nothing else in the app needs to change.
    """

    def __init__(self, root: Path) -> None:
        self._root = root

    async def save(self, *, key: str, data: bytes) -> None:
        path = self._root / key
        await asyncio.to_thread(path.parent.mkdir, parents=True, exist_ok=True)
        await asyncio.to_thread(path.write_bytes, data)

    async def load(self, *, key: str) -> bytes:
        path = self._root / key
        if not path.is_file():
            raise FileNotFoundError(key)
        return await asyncio.to_thread(path.read_bytes)

    async def delete(self, *, key: str) -> None:
        path = self._root / key
        await asyncio.to_thread(path.unlink, True)

    async def stream(self, *, key: str) -> AsyncIterator[bytes]:
        """Yields the file one chunk at a time so a large download never
        needs the whole file resident in memory at once."""
        path = self._root / key
        if not path.is_file():
            raise FileNotFoundError(key)
        handle = await asyncio.to_thread(path.open, "rb")
        try:
            while True:
                chunk = await asyncio.to_thread(handle.read, _STREAM_CHUNK_SIZE)
                if not chunk:
                    break
                yield chunk
        finally:
            await asyncio.to_thread(handle.close)


_default_storage_backend = LocalDiskStorageBackend(Path(get_settings().storage_root))


def get_storage_backend() -> StorageBackend:
    return _default_storage_backend
