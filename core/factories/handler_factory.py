"""Handler factory for creating game mode handlers."""

from config.settings import Settings
from core.algorithms.orchestrator.modes.base_handler import BaseGameHandler
from core.algorithms.orchestrator.modes.daily_handler import DailyHandler
from core.algorithms.orchestrator.modes.offline_handler import OfflineHandler
from core.algorithms.orchestrator.modes.random_handler import RandomHandler
from core.algorithms.orchestrator.modes.word_handler import WordHandler
from core.algorithms.solver_engine import SolverEngine
from infrastructure.api.game_client import GameClient
from infrastructure.data.word_lexicon import WordLexicon
from utils.display import GameDisplay


class HandlerFactory:
    """Factory for creating game mode handlers."""

    def __init__(
        self,
        game_client: GameClient,
        solver_engine: SolverEngine,
        lexicon: WordLexicon,
        display: GameDisplay | None,
        settings: Settings,
    ):
        """Initialize the handler factory.

        Args:
            game_client: The game client for API calls
            solver_engine: The solver engine instance
            lexicon: The word lexicon instance
            display: The game display instance
            settings: Application settings
        """
        self.game_client = game_client
        self.solver_engine = solver_engine
        self.lexicon = lexicon
        self.display = display
        self.settings = settings

    def create_handlers(self) -> dict[str, BaseGameHandler]:
        """Create all game mode handlers.

        Returns:
            Dictionary mapping mode names to handler instances
        """
        return {
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
