"""Dependency injection container for the Wordle bot.

This module provides a centralized way to manage dependencies and reduce
coupling between components.
"""

from config.settings import Settings
from core.algorithms.analytics_engine import AnalyticsEngine
from core.algorithms.benchmark_engine import BenchmarkEngine
from core.algorithms.solver_engine import SolverEngine
from core.algorithms.state_manager import GameStateManager
from infrastructure.api.game_client import GameClient
from infrastructure.data.word_lexicon import WordLexicon
from utils.display import GameDisplay
from utils.logging_config import get_logger


class DependencyContainer:
    """Container for managing application dependencies."""

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialize the dependency container.

        Args:
            settings: Application settings (optional)
        """
        self.settings = settings or Settings.from_env()
        self.logger = get_logger(__name__)

        # Lazy-loaded dependencies
        self._solver: SolverEngine | None = None
        self._lexicon: WordLexicon | None = None
        self._game_client: GameClient | None = None
        self._display: GameDisplay | None = None
        self._analytics_engine: AnalyticsEngine | None = None
        self._benchmark_engine: BenchmarkEngine | None = None

    @property
    def solver(self) -> SolverEngine:
        """Get the solver engine instance."""
        if self._solver is None:
            self._solver = SolverEngine(
                time_budget_seconds=self.settings.SOLVER_TIME_BUDGET_SECONDS,
                max_workers=self.settings.SOLVER_MAX_WORKERS,
                app_settings=self.settings,
            )
        return self._solver

    @property
    def lexicon(self) -> WordLexicon:
        """Get the word lexicon instance."""
        if self._lexicon is None:
            self._lexicon = WordLexicon()
        return self._lexicon

    @property
    def game_client(self) -> GameClient:
        """Get the game client instance."""
        if self._game_client is None:
            self._game_client = GameClient(
                base_url=self.settings.WORDLE_API_BASE_URL,
                timeout=self.settings.API_TIMEOUT_SECONDS,
                app_settings=self.settings,
            )
        return self._game_client

    @property
    def display(self) -> GameDisplay:
        """Get the game display instance."""
        if self._display is None:
            self._display = GameDisplay()
        return self._display

    @property
    def analytics_engine(self) -> AnalyticsEngine:
        """Get the analytics engine instance."""
        if self._analytics_engine is None:
            self._analytics_engine = AnalyticsEngine()
        return self._analytics_engine

    @property
    def benchmark_engine(self) -> BenchmarkEngine:
        """Get the benchmark engine instance."""
        if self._benchmark_engine is None:
            self._benchmark_engine = BenchmarkEngine(
                solver_time_budget=self.settings.SOLVER_TIME_BUDGET_SECONDS,
                max_workers=self.settings.SOLVER_MAX_WORKERS,
            )
        return self._benchmark_engine

    def create_game_state_manager(self, mode: str = "standard") -> GameStateManager:
        """Create a game state manager for the specified mode.

        Args:
            mode: The game mode ("standard" or "daily")

        Returns:
            Configured game state manager
        """
        if mode == "daily":
            return GameStateManager(app_settings=self.settings)
        else:
            return GameStateManager(app_settings=self.settings)

    def reset(self) -> None:
        """Reset all dependencies (useful for testing)."""
        self._solver = None
        self._lexicon = None
        self._game_client = None
        self._display = None
        self._analytics_engine = None
        self._benchmark_engine = None
        self.logger.info("Dependency container reset")
