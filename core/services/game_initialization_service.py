"""Game initialization service for setting up game state managers."""

from config.settings import Settings
from core.algorithms.state_manager import DailyGameStateManager, GameStateManager
from infrastructure.api.game_client import GameClient, WordleAPIError
from utils.logging_config import get_logger


class GameInitializationService:
    """Service for game initialization logic."""

    def __init__(self, settings: Settings):
        """Initialize the game initialization service.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.logger = get_logger(__name__)

    def initialize_standard_game(self) -> GameStateManager:
        """Initialize standard game state manager.

        Returns:
            Initialized game state manager

        Raises:
            WordleAPIError: If initialization fails
        """
        try:
            # Initialize game state manager with all possible answers
            game_state_manager = GameStateManager(app_settings=self.settings)
            self.logger.info(msg="Game initialization completed (standard mode)")
            return game_state_manager
        except WordleAPIError as e:
            self.logger.error(msg=f"Failed to initialize game: {e}")
            raise

    def initialize_daily_game(self) -> DailyGameStateManager:
        """Initialize daily game state manager.

        Returns:
            Initialized daily game state manager
        """
        try:
            # Initialize daily game state manager
            daily_game_manager = DailyGameStateManager(app_settings=self.settings)
            self.logger.info(msg="Game initialization completed (daily mode)")
            return daily_game_manager
        except Exception as e:
            self.logger.error(msg=f"Failed to initialize daily game: {e}")
            raise

    def validate_game_initialization(self, game_manager: GameStateManager) -> bool:
        """Validate game initialization.

        Args:
            game_manager: The game state manager to validate

        Returns:
            True if initialization is valid
        """
        if not game_manager:
            self.logger.error("Game state manager is not initialized")
            return False
        return True
