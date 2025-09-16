"""Daily Game State Manager with improved filtering logic for Daily mode."""

from config.settings import Settings
from config.settings import settings as default_settings
from core.domain.constants import WORD_LENGTH
from core.domain.models import FeedbackType, GameState, GuessResult
from core.use_cases.game_state_manager import GameSummaryDict
from core.use_cases.solver_engine import SolverEngine
from infrastructure.data.word_lexicon import WordLexicon
from utils.logging_config import get_logger


class DailyGameStateManager:
    """Game state manager specifically for Daily mode with improved filtering logic."""

    def __init__(
        self,
        initial_answers: list[str] | None = None,
        app_settings: Settings | None = None,
    ):
        """Initialize the daily game state manager.

        Args:
            initial_answers: Initial list of possible answers
            app_settings: Application settings
        """
        self.settings: Settings = app_settings or default_settings
        self.logger = get_logger(__name__)
        self.lexicon: WordLexicon = WordLexicon()
        self.solver: SolverEngine = SolverEngine(app_settings=self.settings)

        # Initialize with all possible answers
        self._possible_answers: list[str] = (
            initial_answers or self.lexicon.get_all_answers()
        )
        self._game_state: GameState = GameState(
            possible_answers=self._possible_answers.copy()
        )
        self._guess_history: list[GuessResult] = []

    def add_guess_result(self, guess_result: GuessResult) -> None:
        """Add a guess result and update possible answers with improved filtering.

        Args:
            guess_result: The result of a guess
        """
        self._guess_history.append(guess_result)
        self._game_state.add_guess(guess_result)

        # Use improved filtering logic for Daily mode
        self._possible_answers = self._filter_answers_improved(guess_result)
        self._game_state.possible_answers = self._possible_answers.copy()

    def _filter_answers_improved(self, guess_result: GuessResult) -> list[str]:
        """Improved filtering logic specifically for Daily mode.

        This method uses a more robust approach to handle edge cases
        that can occur with Daily API responses.

        Args:
            guess_result: The guess result to filter by

        Returns:
            List of possible answers that are consistent with the guess result
        """
        filtered_answers = []

        # Debug logging
        self.logger.info(
            f"Filtering {len(self._possible_answers)} answers with guess: {guess_result.guess} -> {guess_result.to_pattern_string()}"
        )

        for answer in self._possible_answers:
            is_consistent = self._is_answer_consistent_improved(guess_result, answer)
            if is_consistent:
                filtered_answers.append(answer)
            else:
                self.logger.debug(
                    f"Answer '{answer}' is inconsistent with {guess_result.guess} -> {guess_result.to_pattern_string()}"
                )

        self.logger.info(
            f"Filtered from {len(self._possible_answers)} to {len(filtered_answers)} answers"
        )
        if len(filtered_answers) == 0:
            self.logger.warning(
                f"No answers remain after filtering with {guess_result.guess} -> {guess_result.to_pattern_string()}"
            )
        return filtered_answers

    def _is_answer_consistent_improved(
        self, guess_result: GuessResult, answer: str
    ) -> bool:
        """Permissive consistency check tailored for Daily API behavior.

        Rules (permissive to handle API duplicates/inconsistencies):
        - CORRECT: candidate[i] must equal guess[i]
        - PRESENT: candidate must contain guess[i] somewhere, and not at i
        - ABSENT:
            - If the same letter appears as CORRECT/PRESENT at any other index in this feedback,
              do NOT ban it globally; only enforce candidate[i] != letter.
            - Otherwise, the letter should not appear anywhere in candidate.
        """
        guess = guess_result.guess.upper()
        cand = answer.upper()
        fb = guess_result.feedback

        if len(guess) != WORD_LENGTH or len(cand) != WORD_LENGTH:
            return False

        # Pre-compute letter roles in feedback
        letter_has_non_absent: dict[str, bool] = {}
        for g_ch, f_type in zip(guess, fb, strict=False):
            if f_type != FeedbackType.ABSENT:
                letter_has_non_absent[g_ch] = True
            else:
                letter_has_non_absent.setdefault(g_ch, False)

        # Pass 1: enforce CORRECT positions
        for i, (g_ch, f_type) in enumerate(zip(guess, fb, strict=False)):
            if f_type == FeedbackType.CORRECT and cand[i] != g_ch:
                return False

        # Pass 2: enforce PRESENT and ABSENT with permissive rules
        for i, (g_ch, f_type) in enumerate(zip(guess, fb, strict=False)):
            if f_type == FeedbackType.PRESENT:
                if cand[i] == g_ch:
                    return False
                if g_ch not in cand:
                    return False
            elif f_type == FeedbackType.ABSENT:
                if letter_has_non_absent.get(g_ch, False):
                    # Only ban this position
                    if cand[i] == g_ch:
                        return False
                else:
                    # Ban globally
                    if g_ch in cand:
                        return False

        return True

    def get_possible_answers(self) -> list[str]:
        """Get the current list of possible answers.

        Returns:
            List of possible answers
        """
        return self._possible_answers.copy()

    def get_current_state(self) -> GameState:
        """Get the current game state.

        Returns:
            Current game state
        """
        return self._game_state

    def is_solved(self) -> bool:
        """Check if the game is solved.

        Returns:
            True if solved
        """
        return self._game_state.is_solved

    def is_failed(self) -> bool:
        """Check if the game has failed.

        Returns:
            True if failed
        """
        return self._game_state.is_failed

    def is_game_over(self) -> bool:
        """Check if the game is over.

        Returns:
            True if game is over
        """
        return self._game_state.is_solved or self._game_state.is_failed

    def get_remaining_answers_count(self) -> int:
        """Get the count of remaining possible answers.

        Returns:
            Number of remaining answers
        """
        return len(self._possible_answers)

    def get_game_summary(self) -> GameSummaryDict:
        """Get a summary of the current game state.

        Returns:
            Dictionary containing game summary
        """
        return {
            "turn": self._game_state.turn,
            "total_guesses": len(self._guess_history),
            "remaining_answers": len(self._possible_answers),
            "is_solved": self._game_state.is_solved,
            "is_failed": self._game_state.is_failed,
            "remaining_turns": self._game_state.remaining_turns,
            "guesses": [
                {
                    "guess": gr.guess,
                    "feedback": gr.to_pattern_string(),
                    "correct": gr.is_correct,
                }
                for gr in self._guess_history
            ],
            "possible_answers": self._possible_answers.copy(),
        }
