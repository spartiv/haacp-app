import logging

import pytest
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request

from app.core.error_handlers import (
    app_error_handler,
    unhandled_exception_handler,
    validation_error_handler,
)
from app.core.errors import AppError


def _fake_request(path: str = "/api/v1/test", method: str = "GET") -> Request:
    scope = {"type": "http", "method": method, "path": path, "headers": []}
    return Request(scope)


async def test_app_error_handler_returns_envelope_and_logs_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    exc = AppError(409, "already_member", "This email already belongs to the organization")

    with caplog.at_level(logging.WARNING, logger="app.core.error_handlers"):
        response = await app_error_handler(_fake_request(), exc)

    assert response.status_code == 409
    assert response.body is not None
    assert b"already_member" in response.body
    assert "already_member" in caplog.text
    assert any(record.levelno == logging.WARNING for record in caplog.records)


async def test_validation_error_handler_returns_envelope_and_logs_info(
    caplog: pytest.LogCaptureFixture,
) -> None:
    exc = RequestValidationError(errors=[])

    with caplog.at_level(logging.INFO, logger="app.core.error_handlers"):
        response = await validation_error_handler(_fake_request(), exc)

    assert response.status_code == 422
    assert b"validation_error" in response.body
    assert any(record.levelno == logging.INFO for record in caplog.records)


async def test_unhandled_exception_handler_returns_generic_envelope_and_logs_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    exc = RuntimeError("boom")

    with caplog.at_level(logging.ERROR, logger="app.core.error_handlers"):
        response = await unhandled_exception_handler(_fake_request(), exc)

    assert response.status_code == 500
    assert b"internal_error" in response.body
    assert b"boom" not in response.body  # never leak internals to the client
    assert any(record.levelno == logging.ERROR for record in caplog.records)
    assert "boom" in caplog.text  # but it must be in the logs for debugging
