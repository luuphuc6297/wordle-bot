"""Logging configuration utilities."""

import logging
import logging.config

from config.settings import settings


def setup_logging() -> None:
    """Setup application logging based on configuration."""
    log_config = settings.get_log_config()
    logging.config.dictConfig(log_config)

    # Log startup information
    logger = logging.getLogger(__name__)
    logger.info("Logging configured successfully")
    logger.info(f"Log level: {settings.LOG_LEVEL}")
    logger.info(f"JSON format: {settings.LOG_JSON_FORMAT}")


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
