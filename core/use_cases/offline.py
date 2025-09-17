"""Offline mode entry points.

Wrappers for offline simulate/benchmark using Orchestrator.
"""

from __future__ import annotations

from typing import Any

from config.settings import Settings
from core.algorithms.orchestrator import Orchestrator, SimulationResult


def simulate(target: str, settings: Settings | None = None) -> SimulationResult:
    orchestrator = Orchestrator(app_settings=settings)
    return orchestrator.simulate_game(target)


def benchmark_local(
    games: int = 100, settings: Settings | None = None
) -> dict[str, Any]:
    orchestrator = Orchestrator(app_settings=settings)
    from core.algorithms.benchmark_engine import BenchmarkEngine

    bench = BenchmarkEngine(
        solver_time_budget=orchestrator.settings.SOLVER_TIME_BUDGET_SECONDS,
        max_workers=4,
    )
    return bench.run_benchmark(num_games=games)
