"""Application configuration settings (immutable)."""

import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Settings:
    """Immutable application settings loaded from environment."""

    # API Configuration
    WORDLE_API_BASE_URL: str
    API_TIMEOUT_SECONDS: int
    API_RETRY_ATTEMPTS: int

    # Solver Configuration
    SOLVER_TIME_BUDGET_SECONDS: float
    SOLVER_MAX_WORKERS: int | None
    OPTIMAL_FIRST_GUESS: str

    # Logging Configuration
    LOG_LEVEL: str
    LOG_FORMAT: str
    LOG_JSON_FORMAT: bool

    # Performance Configuration
    ENABLE_PERFORMANCE_METRICS: bool

    # Development Configuration
    DEBUG_MODE: bool
    SIMULATION_MODE: bool

    @classmethod
    def from_env(cls, overrides: dict[str, Any] | None = None) -> "Settings":
        """Create Settings from environment variables with optional overrides."""
        overrides = overrides or {}

        def get_bool(name: str, default: bool) -> bool:
            value = str(overrides.get(name, os.getenv(name, str(default)))).lower()
            return value in {"1", "true", "yes", "on"}

        def get_int(name: str, default: int) -> int:
            return int(overrides.get(name, os.getenv(name, str(default))))

        def get_float(name: str, default: float) -> float:
            return float(overrides.get(name, os.getenv(name, str(default))))

        def get_str(name: str, default: str) -> str:
            return str(overrides.get(name, os.getenv(name, default)))

        solver_max_workers_env = overrides.get(
            "SOLVER_MAX_WORKERS", os.getenv("SOLVER_MAX_WORKERS")
        )
        solver_max_workers = (
            int(solver_max_workers_env) if solver_max_workers_env else None
        )

        return cls(
            WORDLE_API_BASE_URL=get_str(
                "WORDLE_API_BASE_URL", "https://wordle.votee.dev:8000"
            ),
            API_TIMEOUT_SECONDS=get_int("API_TIMEOUT_SECONDS", 10),
            API_RETRY_ATTEMPTS=get_int("API_RETRY_ATTEMPTS", 3),
            SOLVER_TIME_BUDGET_SECONDS=get_float("SOLVER_TIME_BUDGET_SECONDS", 5.0),
            SOLVER_MAX_WORKERS=solver_max_workers,
            OPTIMAL_FIRST_GUESS=get_str("OPTIMAL_FIRST_GUESS", "SALET"),
            LOG_LEVEL=get_str("LOG_LEVEL", "INFO"),
            LOG_FORMAT=get_str(
                "LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            ),
            LOG_JSON_FORMAT=get_bool("LOG_JSON_FORMAT", False),
            ENABLE_PERFORMANCE_METRICS=get_bool("ENABLE_PERFORMANCE_METRICS", True),
            DEBUG_MODE=get_bool("DEBUG", False),
            SIMULATION_MODE=get_bool("SIMULATION_MODE", False),
        )


# Global default settings instance (can be shadowed at runtime with overrides)
settings = Settings.from_env()
