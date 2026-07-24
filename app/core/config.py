from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="HACCP_", extra="ignore")

    environment: str = "development"
    database_url: str = "postgresql+asyncpg://haccp:haccp@localhost:5432/haccp"
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    invite_token_expire_days: int = 7
    storage_root: str = "./data/uploads"


@lru_cache
def get_settings() -> Settings:
    return Settings()
