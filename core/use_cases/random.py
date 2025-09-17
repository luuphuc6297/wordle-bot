"""Random mode entry points.

Thin wrappers around Orchestrator for Random gameplay and analytics.
"""

from __future__ import annotations

from typing import Any

from config.settings import Settings
from core.algorithms.orchestrator import Orchestrator, SimulationResult


def play_random(settings: Settings | None = None) -> SimulationResult:
    orchestrator = Orchestrator(app_settings=settings)
    return orchestrator.play_random_game()


def benchmark_random(
    games: int = 20, settings: Settings | None = None
) -> dict[str, Any]:
    orchestrator = Orchestrator(app_settings=settings)
    return orchestrator.run_online_benchmark(num_games=games, mode="random")
