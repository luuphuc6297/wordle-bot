"""Game coordinator for managing game flow and delegating to services."""

from typing import Any

from config.settings import Settings
from core.algorithms.orchestrator.modes.base_handler import BaseGameHandler
from core.domain.types import GameSummary, SimulationResult
from core.factories.handler_factory import HandlerFactory
from core.services.benchmark_service import BenchmarkService
from core.services.game_summary_service import GameSummaryService
from core.services.guess_analysis_service import GuessAnalysis, GuessAnalysisService
from utils.logging_config import get_logger


class GameCoordinator:
    """Simplified coordinator that delegates to services."""

    def __init__(
        self,
        handler_factory: HandlerFactory,
        summary_service: GameSummaryService,
        benchmark_service: BenchmarkService,
        guess_analysis_service: GuessAnalysisService,
        settings: Settings,
    ):
        """Initialize the game coordinator.

        Args:
            handler_factory: Factory for creating handlers
            summary_service: Service for generating summaries
            benchmark_service: Service for running benchmarks
            guess_analysis_service: Service for analyzing guesses
            settings: Application settings
        """
        self.handlers: dict[str, BaseGameHandler] = handler_factory.create_handlers()
        self.summary_service = summary_service
        self.benchmark_service = benchmark_service
        self.guess_analysis_service = guess_analysis_service
        self.settings = settings
        self.logger = get_logger(__name__)

    def solve_daily_puzzle(self) -> GameSummary:
        """Solve daily puzzle - delegate to handler.

        Returns:
            Game summary with results
        """
        daily_handler = self.handlers["daily"]
        return daily_handler.run_game()

    def play_random_game(self) -> SimulationResult:
        """Play random game - delegate to handler.

        Returns:
            Simulation results
        """
        random_handler = self.handlers["random"]
        return random_handler.run_game()

    def play_word_target(self, target_answer: str) -> SimulationResult:
        """Play word target - delegate to handler.

        Args:
            target_answer: The target word to solve

        Returns:
            Simulation results
        """
        word_handler = self.handlers["word"]
        return word_handler.run_game(target_answer)  # type: ignore

    def simulate_game(
        self, target_answer: str, game_id: str | None = None
    ) -> SimulationResult:
        """Simulate game - delegate to handler.

        Args:
            target_answer: The target word to solve
            game_id: Optional game identifier

        Returns:
            Simulation results
        """
        offline_handler = self.handlers["offline"]
        return offline_handler.run_game(target_answer, game_id)  # type: ignore

    def analyze_guess(
        self, guess: str, possible_answers: list[str] | None = None
    ) -> GuessAnalysis:
        """Analyze guess - delegate to service.

        Args:
            guess: The word to analyze
            possible_answers: Optional list of possible answers

        Returns:
            Analysis results
        """
        return self.guess_analysis_service.analyze_guess(guess, possible_answers)

    def run_online_benchmark(self, **kwargs) -> dict[str, Any]:
        """Run benchmark - delegate to service.

        Args:
            **kwargs: Benchmark parameters

        Returns:
            Benchmark results
        """
        return self.benchmark_service.run_online_benchmark(**kwargs)

    def run_online_analytics(self, **kwargs) -> dict[str, Any]:
        """Run analytics - delegate to service.

        Args:
            **kwargs: Analytics parameters

        Returns:
            Analytics results
        """
        return self.benchmark_service.run_online_analytics(**kwargs)
