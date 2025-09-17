"""GameStateManager - Manages game state and filters possible answers based on feedback."""

from typing import TypedDict

from config.settings import Settings
from config.settings import settings as default_settings
from core.algorithms.game_state_manager_strategy import (
    FilterStrategy,
    StandardFilterStrategy,
)
from core.algorithms.solver_engine import SolverEngine
from core.domain.models import FeedbackType, GameState, GuessResult
from infrastructure.data.word_lexicon import WordLexicon


class GameSummaryDict(TypedDict):
    """Type definition for game summary dictionary."""

    turn: int
    total_guesses: int
    remaining_answers: int
    is_solved: bool
    is_failed: bool
    remaining_turns: int
    guesses: list[dict[str, str | bool]]
    possible_answers: list[str]


class GameStateManager:
    """Manages the current game state and filters possible answers."""

    def __init__(
        self,
        initial_answers: list[str] | None = None,
        app_settings: Settings | None = None,
    ):
        """Initialize game state manager.

        Args:
            initial_answers: Optional list of initial possible answers.
            If None, uses all possible answers from lexicon.
        """
        self.settings: Settings = app_settings or default_settings
        self.lexicon: WordLexicon = WordLexicon()
        self.solver: SolverEngine = SolverEngine(app_settings=self.settings)
        self.filter_strategy: FilterStrategy = StandardFilterStrategy(self.solver)

        initial_possible_answers = initial_answers or self.lexicon.answers

        self.game_state: GameState = GameState(
            turn=1,
            possible_answers=initial_possible_answers.copy(),
            is_solved=False,
            is_failed=False,
        )

    def add_guess_result(self, guess_result: GuessResult) -> None:
        """Add a guess result and update possible answers.

        Args:
            guess_result: The result of the guess including feedback
        """
        # Add guess to game state
        self.game_state.add_guess(guess_result)

        # If game is over, don't filter further
        if self.game_state.is_game_over:
            return

        # Filter possible answers based on the new feedback
        self._filter_possible_answers(guess_result)

    def _filter_possible_answers(self, guess_result: GuessResult) -> None:
        """Filter possible answers based on guess feedback.

        Args:
            guess_result: The guess result to use for filtering
        """
        self.game_state.possible_answers = self.filter_strategy.filter_answers(
            guess_result=guess_result,
            candidates=self.game_state.possible_answers,
        )

    def _is_answer_consistent(
        self, guess: str, feedback: list[FeedbackType], answer: str
    ) -> bool:
        """Check if an answer is consistent with the given guess and feedback.

        Args:
            guess: The guessed word
            feedback: The feedback received
            answer: The potential answer to check

        Returns:
            True if the answer is consistent with the feedback
        """
        # Simulate what the feedback would be if this answer were correct
        simulated_pattern = self.solver.simulate_feedback(guess, answer)

        # Convert our feedback to pattern string for comparison
        expected_pattern = "".join(
            "+"
            if f == FeedbackType.CORRECT
            else ("o" if f == FeedbackType.PRESENT else "-")
            for f in feedback
        )

        return simulated_pattern == expected_pattern

    def get_current_state(self) -> GameState:
        """Get the current game state.

        Returns:
            Current game state
        """
        return self.game_state

    def get_possible_answers(self) -> list[str]:
        """Get the current list of possible answers.

        Returns:
            List of possible answer words
        """
        return self.game_state.possible_answers.copy()

    def get_remaining_answers_count(self) -> int:
        """Get the count of remaining possible answers.

        Returns:
            Number of possible answers remaining
        """
        return len(self.game_state.possible_answers)

    def is_game_over(self) -> bool:
        """Check if the game is over.

        Returns:
            True if the game is solved or failed
        """
        return self.game_state.is_game_over

    def is_solved(self) -> bool:
        """Check if the game is solved.

        Returns:
            True if the correct word was found
        """
        return self.game_state.is_solved

    def is_failed(self) -> bool:
        """Check if the game failed.

        Returns:
            True if maximum turns were reached without solving
        """
        return self.game_state.is_failed

    def get_game_summary(self) -> GameSummaryDict:
        """Get a summary of the current game state.

        Returns:
            Dictionary containing game summary information
        """
        return {
            "turn": self.game_state.turn,
            "total_guesses": len(self.game_state.guesses),
            "remaining_answers": len(self.game_state.possible_answers),
            "is_solved": self.game_state.is_solved,
            "is_failed": self.game_state.is_failed,
            "remaining_turns": self.game_state.remaining_turns,
            "guesses": [
                {
                    "guess": guess.guess,
                    "pattern": guess.to_pattern_string(),
                    "is_correct": guess.is_correct,
                }
                for guess in self.game_state.guesses
            ],
            "possible_answers": self.game_state.possible_answers.copy(),
        }

    def reset_game(self) -> None:
        """Reset the game state for a new game."""
        self.game_state = GameState(
            turn=1,
            possible_answers=self.lexicon.answers.copy(),
            is_solved=False,
            is_failed=False,
        )
