"""Orchestrator - Main business logic coordinator for the Wordle-solving bot."""

import logging
import time
from typing import Any, TypedDict

from config.settings import Settings
from config.settings import settings as default_settings
from core.algorithms.solver_engine import SolverEngine
from core.algorithms.state_manager import (
    ApiGameStateManager,
    GameStateManager,
)
from core.coordinators.game_coordinator import GameCoordinator
from core.domain.types import GameSummary, GuessHistoryItem, SimulationResult
from core.factories.handler_factory import HandlerFactory
from core.services.benchmark_service import BenchmarkService
from core.services.game_initialization_service import GameInitializationService
from core.services.game_summary_service import GameSummaryService
from core.services.guess_analysis_service import GuessAnalysis, GuessAnalysisService
from infrastructure.api.game_client import GameClient, WordleAPIError
from infrastructure.data.word_lexicon import WordLexicon
from utils.display import GameDisplay
from utils.logging_config import get_logger

from .modes.daily_handler import DailyHandler
from .modes.offline_handler import OfflineHandler
from .modes.random_handler import RandomHandler
from .modes.word_handler import WordHandler


# GuessAnalysis moved to core.services.guess_analysis_service


class Orchestrator:
    """Main coordinator that manages the complete game solving process."""

    def __init__(
        self,
        api_base_url: str = "https://wordle.votee.dev:8000",
        solver_time_budget: float = 5.0,
        show_rich_display: bool = True,
        show_detailed: bool = True,
        app_settings: Settings | None = None,
    ) -> None:
        """Initialize the orchestrator.

        Args:
            api_base_url: Base URL for the Wordle API
            solver_time_budget: Time budget for solver calculations in seconds
            show_rich_display: Whether to show rich console display
            show_detailed: Whether to show detailed entropy information
        """
        self.logger: logging.Logger = get_logger(__name__)

        # Initialize components
        self.settings: Settings = app_settings or default_settings
        self.lexicon: WordLexicon = WordLexicon()
        self.game_client: GameClient = GameClient(
            base_url=api_base_url, app_settings=self.settings
        )
        self.solver_engine: SolverEngine = SolverEngine(
            time_budget_seconds=solver_time_budget,
            app_settings=self.settings,
        )
        self.game_state_manager: GameStateManager | None = None

        # Initialize display
        self.show_rich_display: bool = show_rich_display
        self.display: GameDisplay | None = (
            GameDisplay(show_detailed=show_detailed) if show_rich_display else None
        )

        # Initialize services
        self._initialize_services()

        # Initialize mode handlers
        self._handlers = {
            "daily": DailyHandler(
                self.game_client,
                self.solver_engine,
                self.lexicon,
                self.display,
                self.settings,
            ),
            "random": RandomHandler(
                self.game_client,
                self.solver_engine,
                self.lexicon,
                self.display,
                self.settings,
            ),
            "word": WordHandler(
                self.game_client,
                self.solver_engine,
                self.lexicon,
                self.display,
                self.settings,
            ),
            "offline": OfflineHandler(
                self.solver_engine, self.lexicon, self.display, self.settings
            ),
        }

        self.logger.info(
            msg=f"Orchestrator initialized with {len(self.lexicon.answers)} possible answers"
        )

    def _initialize_services(self) -> None:
        """Initialize all services."""
        # Initialize services
        self.summary_service = GameSummaryService(self.lexicon)
        self.initialization_service = GameInitializationService(self.settings)
        self.guess_analysis_service = GuessAnalysisService(self.solver_engine, self.lexicon)
        self.benchmark_service = BenchmarkService(self)
        
        # Initialize handler factory
        self.handler_factory = HandlerFactory(
            self.game_client,
            self.solver_engine,
            self.lexicon,
            self.display,
            self.settings,
        )
        
        # Initialize game coordinator
        self.game_coordinator = GameCoordinator(
            self.handler_factory,
            self.summary_service,
            self.benchmark_service,
            self.guess_analysis_service,
            self.settings,
        )

    def solve_daily_puzzle(self) -> GameSummary:
        """Solve the daily Wordle puzzle using improved strategy.

        STRATEGY:
        1. Call Daily API to get feedback and narrow down possible answers
        2. Find the actual target word by testing possible answers
        3. Use Word-target API to continue with entropy algorithm
        4. Continue until solved or max turns reached
        """
        return self.game_coordinator.solve_daily_puzzle()

    # _generate_daily_final_summary moved to GameSummaryService

    # _solve_daily_original moved to DailyHandler

    # _initialize_game moved to GameInitializationService

    # _generate_final_summary moved to GameSummaryService

    def analyze_guess(
        self, guess: str, possible_answers: list[str] | None = None
    ) -> GuessAnalysis:
        """Analyze the entropy and effectiveness of a specific guess.

        Args:
            guess: The word to analyze
            possible_answers: Optional list of possible answers. If None, uses all answers.

        Returns:
            Analysis results including entropy calculation
        """
        return self.game_coordinator.analyze_guess(guess, possible_answers)

    def play_random_game(self) -> SimulationResult:
        """Play a game using the random API mode (/random).

        STRATEGY:
        1. Call Random API to get a random target word
        2. Use our entropy algorithm to solve that specific target word
        3. Continue until solved or max turns reached
        """
        return self.game_coordinator.play_random_game()

    def play_word_target(self, target_answer: str) -> SimulationResult:
        """Play a game against a specific target using /word/{target}."""
        return self.game_coordinator.play_word_target(target_answer)

    def simulate_game(
        self, target_answer: str, game_id: str | None = None
    ) -> SimulationResult:
        """Simulate a game with a known target answer for testing.

        Args:
            target_answer: The target word to solve for
            game_id: Optional game identifier for display

        Returns:
            Simulation results
        """
        return self.game_coordinator.simulate_game(target_answer, game_id)

    def run_online_benchmark(
        self,
        num_games: int = 100,
        mode: str = "random",
        target_words: list[str] | None = None,
        show_progress: bool = True,
    ) -> dict[str, Any]:
        """Run benchmark using online APIs.

        Args:
            num_games: Number of games to play
            mode: API mode - "daily", "random", or "word"
            target_words: Specific words for "word" mode (if None, random selection)
            show_progress: Whether to show progress updates

        Returns:
            Benchmark results with online API data
        """
        return self.game_coordinator.run_online_benchmark(
            num_games=num_games,
            mode=mode,
            target_words=target_words,
            show_progress=show_progress,
        )

    def run_online_analytics(
        self,
        analysis_type: str = "strategy",
        sample_size: int = 50,
        mode: str = "random",
    ) -> dict[str, Any]:
        """Run analytics using online APIs.

        Args:
            analysis_type: Type of analysis - "strategy", "difficulty", "patterns", "positions"
            sample_size: Number of games to sample for analysis
            mode: API mode - "daily", "random", or "word"

        Returns:
            Analytics results with online API data
        """
        return self.game_coordinator.run_online_analytics(
            analysis_type=analysis_type,
            sample_size=sample_size,
            mode=mode,
        )


# Internal Handler Classes have been moved to separate files in modes/
