"""Application configuration settings."""

import os
from typing import Optional


class Settings:
    """Application settings and configuration."""

    # API Configuration
    WORDLE_API_BASE_URL: str = os.getenv(
        "WORDLE_API_BASE_URL", "https://wordle.votee.dev:8000"
    )
    API_TIMEOUT_SECONDS: int = int(os.getenv("API_TIMEOUT_SECONDS", "10"))
    API_RETRY_ATTEMPTS: int = int(os.getenv("API_RETRY_ATTEMPTS", "3"))

    # Solver Configuration
    SOLVER_TIME_BUDGET_SECONDS: float = float(
        os.getenv("SOLVER_TIME_BUDGET_SECONDS", "5.0")
    )
    SOLVER_MAX_WORKERS: Optional[int] = None
    if os.getenv("SOLVER_MAX_WORKERS"):
        SOLVER_MAX_WORKERS = int(os.getenv("SOLVER_MAX_WORKERS"))

    # Optimal first guess (pre-computed)
    OPTIMAL_FIRST_GUESS: str = os.getenv("OPTIMAL_FIRST_GUESS", "SALET")

    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv(
        "LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    LOG_JSON_FORMAT: bool = os.getenv("LOG_JSON_FORMAT", "false").lower() == "true"

    # Performance Configuration
    ENABLE_PERFORMANCE_METRICS: bool = (
        os.getenv("ENABLE_PERFORMANCE_METRICS", "true").lower() == "true"
    )

    # Development Configuration
    DEBUG_MODE: bool = os.getenv("DEBUG", "false").lower() == "true"
    SIMULATION_MODE: bool = os.getenv("SIMULATION_MODE", "false").lower() == "true"

    @classmethod
    def get_log_config(cls) -> dict:
        """Get logging configuration dictionary.

        Returns:
            Dictionary suitable for logging.config.dictConfig()
        """
        config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {"format": cls.LOG_FORMAT},
                "json": {
                    "format": '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}',
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": cls.LOG_LEVEL,
                    "formatter": "json" if cls.LOG_JSON_FORMAT else "standard",
                    "stream": "ext://sys.stdout",
                }
            },
            "loggers": {
                "": {  # Root logger
                    "handlers": ["console"],
                    "level": cls.LOG_LEVEL,
                    "propagate": False,
                },
                "wordle_bot": {
                    "handlers": ["console"],
                    "level": cls.LOG_LEVEL,
                    "propagate": False,
                },
            },
        }

        return config


# Global settings instance
settings = Settings()
