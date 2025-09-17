"""Word Lexicon module for loading and managing Wordle word lists."""

import random
from pathlib import Path

from core.domain.types import LexiconStats


class WordLexicon:
    """Singleton class for managing Wordle word lists."""

    _instance: "WordLexicon | None" = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not self._initialized:
            self._answers: list[str] = []
            self._allowed_guesses: list[str] = []
            self._answer_set: set[str] = set()
            self._allowed_set: set[str] = set()
            self._load_word_lists()
            WordLexicon._initialized = True

    def _load_word_lists(self):
        """Load word lists from local files."""
        base_path: Path = Path(__file__).parent

        # Load answers list (~2,315 words)
        answers_path: Path = base_path / "answers.txt"
        if not answers_path.exists():
            raise FileNotFoundError(f"Answers file not found: {answers_path}")

        with open(file=answers_path, encoding="utf-8") as f:
            self._answers = [
                line.strip().upper()
                for line in f
                if line.strip() and len(line.strip()) == 5
            ]

        self._answer_set = set(self._answers)

        # Load allowed guesses list (~12,972 words including answers)
        allowed_path = base_path / "allowed.txt"
        if not allowed_path.exists():
            raise FileNotFoundError(f"Allowed guesses file not found: {allowed_path}")

        with open(allowed_path, encoding="utf-8") as f:
            self._allowed_guesses = [
                line.strip().upper()
                for line in f
                if line.strip() and len(line.strip()) == 5
            ]

        self._allowed_set = set(self._allowed_guesses)

        # Validate data integrity
        if not self._answers:
            raise ValueError("No answers loaded from answers file")
        if not self._allowed_guesses:
            raise ValueError("No allowed guesses loaded from allowed file")
        if len(self._answers) < 100:
            raise ValueError(f"Too few answers loaded: {len(self._answers)}")
        if len(self._allowed_guesses) < len(self._answers):
            raise ValueError(
                f"Allowed guesses ({len(self._allowed_guesses)}) should be >= answers ({len(self._answers)})"
            )

    @property
    def answers(self) -> list[str]:
        """Get list of possible answer words."""
        return self._answers.copy()

    @property
    def allowed_guesses(self) -> list[str]:
        """Get list of all allowed guess words."""
        return self._allowed_guesses.copy()

    def is_valid_answer(self, word: str) -> bool:
        """Check if word is a valid answer."""
        return word.upper() in self._answer_set

    def is_valid_guess(self, word: str) -> bool:
        """Check if word is a valid guess."""
        return word.upper() in self._allowed_set

    def get_random_answer(self) -> str:
        """Get a random answer word."""
        return random.choice(self._answers)

    def get_all_answers(self) -> list[str]:
        """Get all possible answer words."""
        return self._answers.copy()

    def get_stats(self) -> LexiconStats:
        """Get statistics about loaded word lists."""
        return {
            "total_answers": len(self._answers),
            "total_allowed_guesses": len(self._allowed_guesses),
            "answers_in_allowed": len(self._answer_set.intersection(self._allowed_set)),
        }
