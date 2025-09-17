"""Daily mode entry points.

Thin wrappers around Orchestrator for Daily gameplay and analytics.
"""

from __future__ import annotations

from typing import Any

from config.settings import Settings
from core.algorithms.orchestrator import GameSummary, Orchestrator
from utils.logging_config import get_logger

logger = get_logger(__name__)


def _create_orchestrator(settings: Settings | None = None) -> Orchestrator:
    """Create orchestrator instance with proper error handling."""
    try:
        return Orchestrator(app_settings=settings)
    except Exception as e:
        logger.error(f"Failed to create orchestrator: {e}")
        raise


def solve_daily(settings: Settings | None = None) -> GameSummary:
    """Solve today's daily Wordle puzzle.

    Args:
        settings: Optional settings override

    Returns:
        Game summary with results

    Raises:
        RuntimeError: If puzzle solving fails
    """
    try:
        orchestrator = _create_orchestrator(settings)
        logger.info("Starting daily puzzle solution")
        result = orchestrator.solve_daily_puzzle()
        logger.info("Daily puzzle solution completed")
        return result
    except Exception as e:
        logger.error(f"Daily puzzle solving failed: {e}")
        raise RuntimeError(f"Failed to solve daily puzzle: {e}") from e


def benchmark_daily(
    games: int = 10, settings: Settings | None = None
) -> dict[str, Any]:
    """Run benchmark on daily puzzles.

    Args:
        games: Number of games to benchmark
        settings: Optional settings override

    Returns:
        Benchmark results

    Raises:
        RuntimeError: If benchmark fails
    """
    try:
        orchestrator = _create_orchestrator(settings)
        logger.info(f"Starting daily benchmark with {games} games")
        result = orchestrator.run_online_benchmark(num_games=games, mode="daily")
        logger.info("Daily benchmark completed")
        return result
    except Exception as e:
        logger.error(f"Daily benchmark failed: {e}")
        raise RuntimeError(f"Failed to run daily benchmark: {e}") from e
