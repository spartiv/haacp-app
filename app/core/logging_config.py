import logging.config

from app.core.config import get_settings


def configure_logging() -> None:
    """Wires up the root logger so every `logging.getLogger(__name__)` call
    in the app actually shows up, at the level set by HACCP_LOG_LEVEL.

    Without this, Python's default root logger level (WARNING) silently
    swallows INFO/DEBUG logs no matter how many logger.info(...) calls exist
    in the code.
    """
    settings = get_settings()
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s %(levelname)-8s %(name)s: %(message)s",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                },
            },
            "root": {
                "handlers": ["console"],
                "level": settings.log_level,
            },
            "loggers": {
                # Per-request access lines are noisy at INFO; keep them opt-in.
                "uvicorn.access": {"level": "WARNING"},
            },
        }
    )
