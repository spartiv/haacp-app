import logging

from app.core.logging_config import configure_logging


def test_configure_logging_sets_root_level_from_settings() -> None:
    configure_logging()

    assert logging.getLogger().level == logging.INFO
    assert logging.getLogger("uvicorn.access").level == logging.WARNING
