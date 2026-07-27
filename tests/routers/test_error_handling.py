import logging
from collections.abc import AsyncGenerator

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.main import app as fastapi_app


async def test_unhandled_exception_is_logged_and_produces_500_envelope(
    client: AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    """Starlette's ServerErrorMiddleware sends our JSON envelope to the
    wire *and* re-raises so the ASGI server can log/crash-report it. Real
    HTTP clients behind uvicorn only ever see the clean JSON response; here,
    talking to the app in-process via ASGITransport, the re-raise surfaces
    directly in this test — so we assert on the log output (which is what a
    real deployment would show) rather than a response object."""

    async def _broken_db_session() -> AsyncGenerator[AsyncSession]:
        raise RuntimeError("simulated database outage")
        yield  # pragma: no cover - unreachable, satisfies the generator type

    fastapi_app.dependency_overrides[get_db_session] = _broken_db_session
    try:
        with caplog.at_level(logging.ERROR, logger="app.core.error_handlers"):
            with pytest.raises(RuntimeError, match="simulated database outage"):
                await client.post(
                    "/api/v1/auth/login",
                    json={"email": "someone@polton.ua", "password": "whatever123"},
                )
    finally:
        fastapi_app.dependency_overrides.pop(get_db_session, None)

    assert any(record.levelno == logging.ERROR for record in caplog.records)
    assert "500 internal_error" in caplog.text
