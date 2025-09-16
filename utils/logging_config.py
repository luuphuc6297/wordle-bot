"""Logging configuration utilities."""

import logging
import logging.config

from config.settings import Settings
from config.settings import settings as default_settings

JSON_MESSAGE_FORMAT = (
    '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": '
    '"%(levelname)s", "message": "%(message)s"}'
)


def build_log_config(active_settings: Settings) -> dict:
    """Build a dictConfig-compatible logging configuration."""
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {"format": active_settings.LOG_FORMAT},
            "json": {
                "format": JSON_MESSAGE_FORMAT,
                "datefmt": "%Y-%m-%dT%H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": active_settings.LOG_LEVEL,
                "formatter": "json" if active_settings.LOG_JSON_FORMAT else "standard",
                "stream": "ext://sys.stdout",
            }
        },
        "loggers": {
            "": {
                "handlers": ["console"],
                "level": active_settings.LOG_LEVEL,
                "propagate": False,
            },
            "wordle_bot": {
                "handlers": ["console"],
                "level": active_settings.LOG_LEVEL,
                "propagate": False,
            },
        },
    }


def setup_logging(active_settings: Settings | None = None) -> None:
    """Setup application logging based on configuration."""
    cfg_settings = active_settings or default_settings
    log_config = build_log_config(cfg_settings)
    logging.config.dictConfig(log_config)

    logger = logging.getLogger(__name__)
    logger.info("Logging configured successfully")
    logger.info(f"Log level: {cfg_settings.LOG_LEVEL}")
    logger.info(f"JSON format: {cfg_settings.LOG_JSON_FORMAT}")


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
