"""Guess analysis service for analyzing individual guesses."""

from typing import Any, TypedDict

from core.algorithms.solver_engine import SolverEngine
from infrastructure.data.word_lexicon import WordLexicon
from utils.logging_config import get_logger


class GuessAnalysis(TypedDict):
    """Type definition for guess analysis."""

    word: str
    entropy: float
    pattern_count: int
    calculation_time: float
    possible_answers_count: int
    information_bits: float
    is_optimal_first_guess: bool


class GuessAnalysisService:
    """Service for analyzing individual guesses."""

    def __init__(self, solver_engine: SolverEngine, lexicon: WordLexicon):
        """Initialize the guess analysis service.

        Args:
            solver_engine: The solver engine instance
            lexicon: The word lexicon instance
        """
        self.solver_engine = solver_engine
        self.lexicon = lexicon
        self.logger = get_logger(__name__)

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
        if possible_answers is None:
            possible_answers = self.lexicon.answers

        if not self.lexicon.is_valid_guess(guess):
            raise ValueError(f"'{guess}' is not a valid guess word")

        # Calculate detailed entropy
        entropy_calc = self.solver_engine.calculate_detailed_entropy(
            guess, possible_answers
        )

        return {
            "word": guess,
            "entropy": entropy_calc.entropy,
            "pattern_count": entropy_calc.pattern_count,
            "calculation_time": entropy_calc.calculation_time or 0.0,
            "possible_answers_count": len(possible_answers),
            "information_bits": entropy_calc.entropy,
            "is_optimal_first_guess": guess.upper()
            == self.solver_engine.OPTIMAL_FIRST_GUESS,
        }

    def validate_guess(self, guess: str) -> bool:
        """Validate if guess is valid.

        Args:
            guess: The guess to validate

        Returns:
            True if guess is valid
        """
        return self.lexicon.is_valid_guess(guess)

    def get_optimal_first_guess(self) -> str:
        """Get optimal first guess.

        Returns:
            The optimal first guess word
        """
        return self.solver_engine.OPTIMAL_FIRST_GUESS
