import asyncio
import logging
from collections.abc import AsyncIterator
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

import boto3
from botocore.exceptions import ClientError

from app.core.config import get_settings

if TYPE_CHECKING:  # type stubs are a dev dependency, not installed in production
    from botocore.response import StreamingBody
    from mypy_boto3_s3.client import S3Client

logger = logging.getLogger(__name__)

_STREAM_CHUNK_SIZE = 1024 * 1024

_MISSING_KEY_ERROR_CODES = frozenset({"NoSuchKey", "404"})


class StorageBackend(Protocol):
    async def save(self, *, key: str, data: bytes) -> None: ...
    async def load(self, *, key: str) -> bytes: ...
    async def delete(self, *, key: str) -> None: ...
    def stream(self, *, key: str) -> AsyncIterator[bytes]: ...


class S3StorageBackend:
    """Files live in an S3 bucket, so they survive server restarts,
    redeploys, and scaling out to multiple app instances — none of which a
    local-disk backend can offer. boto3 is synchronous, so every call is
    offloaded to a thread via asyncio.to_thread.
    """

    def __init__(self, *, bucket_name: str, region: str) -> None:
        self._bucket_name = bucket_name
        self._client: S3Client = boto3.client("s3", region_name=region)

    async def save(self, *, key: str, data: bytes) -> None:
        await asyncio.to_thread(
            self._client.put_object, Bucket=self._bucket_name, Key=key, Body=data
        )

    async def load(self, *, key: str) -> bytes:
        body = await self._get_body(key)
        return await asyncio.to_thread(body.read)

    async def delete(self, *, key: str) -> None:
        await asyncio.to_thread(self._client.delete_object, Bucket=self._bucket_name, Key=key)

    async def stream(self, *, key: str) -> AsyncIterator[bytes]:
        """Yields the object one chunk at a time so a large download never
        needs the whole file resident in memory at once."""
        body = await self._get_body(key)
        while True:
            chunk = await asyncio.to_thread(body.read, _STREAM_CHUNK_SIZE)
            if not chunk:
                break
            yield chunk

    async def _get_body(self, key: str) -> StreamingBody:
        try:
            response = await asyncio.to_thread(
                self._client.get_object, Bucket=self._bucket_name, Key=key
            )
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in _MISSING_KEY_ERROR_CODES:
                raise FileNotFoundError(key) from exc
            raise
        return response["Body"]


class LocalStorageBackend:
    """Files on the local disk, for development only: uploads work without
    any cloud credentials. Not for production (lost on redeploy, not shared
    between app instances). File IO runs in a thread to keep the loop free."""

    def __init__(self, *, root: Path) -> None:
        self._root = root.resolve()

    def _path(self, key: str) -> Path:
        path = (self._root / key).resolve()
        # Keys are generated server-side, but never let one escape the root.
        if not path.is_relative_to(self._root):
            raise ValueError(f"Storage key escapes the storage root: {key!r}")
        return path

    async def save(self, *, key: str, data: bytes) -> None:
        path = self._path(key)

        def _write() -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

        await asyncio.to_thread(_write)

    async def load(self, *, key: str) -> bytes:
        return await asyncio.to_thread(self._path(key).read_bytes)

    async def delete(self, *, key: str) -> None:
        await asyncio.to_thread(self._path(key).unlink, missing_ok=True)

    async def stream(self, *, key: str) -> AsyncIterator[bytes]:
        path = self._path(key)
        if not path.is_file():
            raise FileNotFoundError(key)
        handle = await asyncio.to_thread(path.open, "rb")
        try:
            while chunk := await asyncio.to_thread(handle.read, _STREAM_CHUNK_SIZE):
                yield chunk
        finally:
            await asyncio.to_thread(handle.close)


def _build_default_backend() -> StorageBackend:
    settings = get_settings()
    if settings.resolved_storage_backend == "local":
        logger.info("File storage: local disk at %s", settings.local_storage_dir.resolve())
        return LocalStorageBackend(root=settings.local_storage_dir)
    return S3StorageBackend(bucket_name=settings.s3_bucket_name, region=settings.aws_region)


_default_storage_backend = _build_default_backend()


def get_storage_backend() -> StorageBackend:
    return _default_storage_backend
