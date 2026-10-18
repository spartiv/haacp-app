from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_JWT_SECRET = "change-me-in-production"
MIN_JWT_SECRET_LENGTH = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="HACCP_", extra="ignore")

    environment: str = "development"
    log_level: str = "INFO"
    database_url: str = "postgresql+asyncpg://haccp:haccp@localhost:5432/haccp"
    jwt_secret_key: str = DEFAULT_JWT_SECRET
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    invite_token_expire_days: int = 7
    s3_bucket_name: str = "change-me-haccp-attachments"
    aws_region: str = "eu-central-1"
    attachment_max_size_bytes: int = 20 * 1024 * 1024
    # Where uploaded files live. None = automatic: local disk in development,
    # S3 everywhere else (so a misconfigured server never keeps files on disk).
    storage_backend: Literal["s3", "local"] | None = None
    local_storage_dir: Path = Path("uploads")
    # Built web app (web/dist) to serve from this same server, so the site and
    # the API share one origin (no CORS). None in local dev, where Vite serves it.
    frontend_dist_dir: Path | None = None

    @field_validator("database_url")
    @classmethod
    def _use_async_driver(cls, value: str) -> str:
        """Hosts like Railway hand out `postgresql://` (or `postgres://`) URLs;
        the app needs the asyncpg driver, so accept those as-is."""
        for prefix in ("postgresql://", "postgres://"):
            if value.startswith(prefix):
                return "postgresql+asyncpg://" + value.removeprefix(prefix)
        return value

    @model_validator(mode="after")
    def _require_real_secret_outside_development(self) -> "Settings":
        """Never sign logins with the public placeholder (or a short key) on a
        real server: fail the deploy loudly instead."""
        if self.environment != "development" and (
            self.jwt_secret_key == DEFAULT_JWT_SECRET
            or len(self.jwt_secret_key) < MIN_JWT_SECRET_LENGTH
        ):
            raise ValueError(
                "Set HACCP_JWT_SECRET_KEY to a random value of at least "
                f"{MIN_JWT_SECRET_LENGTH} characters (e.g. `openssl rand -hex 32`)"
            )
        return self

    @property
    def resolved_storage_backend(self) -> Literal["s3", "local"]:
        if self.storage_backend is not None:
            return self.storage_backend
        return "local" if self.environment == "development" else "s3"


@lru_cache
def get_settings() -> Settings:
    return Settings()
