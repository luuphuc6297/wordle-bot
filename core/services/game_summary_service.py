"""Game summary service for generating consistent game summaries."""

import time
from typing import Union

from core.algorithms.state_manager import DailyGameStateManager, GameStateManager
from core.domain.types import GameSummary, GuessHistoryItem
from infrastructure.data.word_lexicon import WordLexicon
from utils.logging_config import get_logger


class GameSummaryService:
    """Centralized service for generating game summaries."""

    def __init__(self, lexicon: WordLexicon):
        """Initialize the game summary service.

        Args:
            lexicon: The word lexicon instance
        """
        self.lexicon = lexicon
        self.logger = get_logger(__name__)

    def generate_summary(
        self,
        game_state_manager: Union[GameStateManager, DailyGameStateManager],
        total_time: float,
        game_type: str = "standard",
    ) -> GameSummary:
        """Generate consistent game summary for all game types.

        Args:
            game_state_manager: The game state manager
            total_time: Total time taken for the entire game
            game_type: Type of game ("standard", "daily")

        Returns:
            Comprehensive game summary
        """
        game_summary = game_state_manager.get_game_summary()

        # Type-safe access to game_summary
        guess_history: list[GuessHistoryItem] = game_summary["guesses"]
        remaining_answers: list[str] = game_summary["possible_answers"]

        # Get lexicon stats in proper format
        lexicon_stats = self.lexicon.get_stats()

        final_summary: GameSummary = {
            "game_result": {
                "solved": game_state_manager.is_solved(),
                "failed": game_state_manager.is_failed(),
                "total_turns": len(guess_history),
                "final_answer": (guess_history[-1]["guess"] if guess_history else None),
            },
            "performance_metrics": {
                "total_game_time_seconds": round(number=total_time, ndigits=2),
                "average_time_per_turn": round(
                    number=total_time / max(1, len(guess_history)), ndigits=2
                ),
                "remaining_possibilities": remaining_answers,
            },
            "guess_history": guess_history,
            "lexicon_stats": lexicon_stats,
            "timestamp": time.time(),
        }

        # Log final result
        if game_state_manager.is_solved():
            self.logger.info(
                f"PUZZLE SOLVED! Answer: {final_summary['game_result']['final_answer']} "
                + f"in {final_summary['game_result']['total_turns']} turns "
                + f"({final_summary['performance_metrics']['total_game_time_seconds']}s)"
            )
        else:
            self.logger.warning(
                f"Puzzle failed after {final_summary['game_result']['total_turns']} turns "
                + f"({final_summary['performance_metrics']['total_game_time_seconds']}s)"
            )

        return final_summary
