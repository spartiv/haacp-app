"""Deployment settings: hosted database URLs, the login-secret guard, and
serving the web app from the API server."""

from pathlib import Path

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import Settings
from app.core.error_handlers import http_exception_handler
from app.core.frontend import mount_frontend

STRONG_SECRET = "x" * 64


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        (
            "postgresql://u:p@db.railway.internal:5432/railway",
            "postgresql+asyncpg://u:p@db.railway.internal:5432/railway",
        ),
        ("postgres://u:p@host/db", "postgresql+asyncpg://u:p@host/db"),
        ("postgresql+asyncpg://u:p@host/db", "postgresql+asyncpg://u:p@host/db"),
    ],
)
def test_hosted_database_urls_use_the_async_driver(given: str, expected: str) -> None:
    assert Settings(database_url=given).database_url == expected


def test_production_refuses_the_placeholder_or_a_short_secret() -> None:
    with pytest.raises(ValidationError, match="HACCP_JWT_SECRET_KEY"):
        Settings(environment="production")
    with pytest.raises(ValidationError, match="HACCP_JWT_SECRET_KEY"):
        Settings(environment="production", jwt_secret_key="short")

    assert (
        Settings(environment="production", jwt_secret_key=STRONG_SECRET).environment == "production"
    )
    assert Settings().environment == "development"  # local dev keeps working with defaults


@pytest.fixture
def frontend_app(tmp_path: Path) -> FastAPI:
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "index-abc123.js").write_text("console.log('app')")
    (tmp_path / "favicon.svg").write_text("<svg/>")
    (tmp_path / "index.html").write_text("<!doctype html><div id=root></div>")
    app = FastAPI()

    @app.get("/api/v1/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.exception_handler(StarletteHTTPException)(http_exception_handler)
    mount_frontend(app, tmp_path)
    return app


async def test_web_app_and_api_share_one_server(frontend_app: FastAPI) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=frontend_app), base_url="http://test"
    ) as client:
        api = await client.get("/api/v1/health")
        deep_link = await client.get("/journals/batches")
        root = await client.get("/")
        asset = await client.get("/assets/index-abc123.js")
        favicon = await client.get("/favicon.svg")
        unknown_api = await client.get("/api/v1/nope")
        escape = await client.get("/..%2F..%2Fetc%2Fpasswd")

    assert api.json() == {"status": "ok"}
    assert "id=root" in deep_link.text and deep_link.headers["cache-control"] == "no-cache"
    assert "id=root" in root.text
    assert asset.text == "console.log('app')"
    assert favicon.text == "<svg/>"
    # Unknown API paths keep the JSON error envelope instead of returning the app.
    assert unknown_api.status_code == 404
    assert unknown_api.json()["error"]["code"]
    assert "id=root" in escape.text  # never a file outside the build folder


def test_missing_build_fails_at_startup(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="Frontend build not found"):
        mount_frontend(FastAPI(), tmp_path)
