from app.core.config import Settings, get_settings


def test_settings_defaults_are_sane_for_local_development() -> None:
    settings = Settings(_env_file=None)

    assert settings.environment == "development"
    assert settings.jwt_algorithm == "HS256"
    assert settings.access_token_expire_minutes == 15
    assert settings.refresh_token_expire_days == 30
    assert settings.invite_token_expire_days == 7


def test_get_settings_is_cached_so_the_app_shares_one_instance() -> None:
    assert get_settings() is get_settings()
