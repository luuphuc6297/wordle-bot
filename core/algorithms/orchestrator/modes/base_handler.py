"""Base game handler with common functionality.

This module provides the base class for all game mode handlers to reduce
code duplication and ensure consistent behavior.
"""

from abc import ABC, abstractmethod

from config.settings import Settings
from core.algorithms.solver_engine import SolverEngine
from core.domain.types import GameSummary
from infrastructure.data.word_lexicon import WordLexicon
from utils.display import GameDisplay
from utils.logging_config import get_logger


class BaseGameHandler(ABC):
    """Base class for all game mode handlers."""

    def __init__(
        self,
        solver: SolverEngine,
        lexicon: WordLexicon,
        display: GameDisplay,
        settings: Settings,
    ) -> None:
        """Initialize the base game handler.

        Args:
            solver: The solver engine instance
            lexicon: The word lexicon instance
            display: The game display instance
            settings: Application settings
        """
        self.solver = solver
        self.lexicon = lexicon
        self.display = display
        self.settings = settings
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    def run_game(self) -> GameSummary:
        """Run the game and return the summary.

        Returns:
            Game summary with results
        """
        pass

    def _log_game_start(self, mode: str) -> None:
        """Log the start of a game.

        Args:
            mode: The game mode being played
        """
        self.logger.info(f"Starting {mode} game")

    def _log_game_end(
        self, mode: str, solved: bool, turns: int, time_taken: float
    ) -> None:
        """Log the end of a game.

        Args:
            mode: The game mode being played
            solved: Whether the game was solved
            turns: Number of turns taken
            time_taken: Time taken in seconds
        """
        status = "SOLVED" if solved else "FAILED"
        self.logger.info(f"{mode} game {status} in {turns} turns ({time_taken:.2f}s)")

    def _log_turn_start(self, turn: int, remaining_answers: int) -> None:
        """Log the start of a turn.

        Args:
            turn: Current turn number
            remaining_answers: Number of remaining possible answers
        """
        self.logger.info(f"Turn {turn}: {remaining_answers} possible answers remaining")

    def _log_guess_selection(self, guess: str, calculation_time: float) -> None:
        """Log the selection of a guess.

        Args:
            guess: The selected guess
            calculation_time: Time taken to calculate the guess
        """
        self.logger.info(f"Selected guess '{guess}' in {calculation_time:.2f}s")

    def _log_feedback(self, guess: str, feedback: str, correct: bool) -> None:
        """Log the feedback received.

        Args:
            guess: The guess that was made
            feedback: The feedback pattern received
            correct: Whether the guess was correct
        """
        self.logger.info(f"Guess '{guess}' -> {feedback} (Correct: {correct})")

    def _log_fallback_strategy(self, guess: str) -> None:
        """Log the use of a fallback strategy.

        Args:
            guess: The fallback guess selected
        """
        self.logger.warning(f"Fallback strategy: using '{guess}' from full lexicon")

    def _log_no_possible_answers(self) -> None:
        """Log when no possible answers remain."""
        self.logger.warning(
            "No possible answers remaining - this may be a difficult word with conflicting constraints"
        )
