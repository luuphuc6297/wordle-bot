"""Word-target mode entry points.

Wrappers around Orchestrator for /word/{target}.
"""

from __future__ import annotations

from config.settings import Settings
from core.algorithms.orchestrator import Orchestrator, SimulationResult


def play_word_target(target: str, settings: Settings | None = None) -> SimulationResult:
    orchestrator = Orchestrator(app_settings=settings)
    return orchestrator.play_word_target(target)
