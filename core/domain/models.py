"""Domain models for the Wordle bot."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class FeedbackType(Enum):
    """Feedback types for each letter position."""

    CORRECT = "+"  # Green: correct letter in correct position
    PRESENT = "o"  # Yellow: correct letter in wrong position
    ABSENT = "-"  # Gray: letter not in the word


class LetterFeedback(BaseModel):
    """Feedback for a single letter position."""

    letter: str = Field(..., min_length=1, max_length=1)
    feedback: FeedbackType
    position: int = Field(..., ge=0, le=4)


class GuessResult(BaseModel):
    """Result of a single guess."""

    guess: str = Field(..., min_length=5, max_length=5)
    feedback: List[FeedbackType] = Field(..., min_length=5, max_length=5)
    is_correct: bool = False

    @classmethod
    def from_api_response(cls, guess: str, result_string: str) -> "GuessResult":
        """Create GuessResult from API response format (e.g., '++x--')."""
        feedback_map = {
            "+": FeedbackType.CORRECT,
            "o": FeedbackType.PRESENT,
            "x": FeedbackType.ABSENT,
            "-": FeedbackType.ABSENT,
        }

        if len(result_string) != 5:
            raise ValueError(f"Invalid result string length: {len(result_string)}")

        feedback = []
        for char in result_string:
            if char not in feedback_map:
                raise ValueError(f"Invalid feedback character: {char}")
            feedback.append(feedback_map[char])

        is_correct = all(f == FeedbackType.CORRECT for f in feedback)

        return cls(guess=guess.upper(), feedback=feedback, is_correct=is_correct)

    def to_pattern_string(self) -> str:
        """Convert feedback to pattern string for entropy calculations."""
        pattern_map = {
            FeedbackType.CORRECT: "+",
            FeedbackType.PRESENT: "o",
            FeedbackType.ABSENT: "-",
        }
        return "".join(pattern_map[f] for f in self.feedback)


class GameState(BaseModel):
    """Current state of the Wordle game."""

    turn: int = Field(default=1, ge=1, le=6)
    guesses: List[GuessResult] = Field(default_factory=list)
    possible_answers: List[str] = Field(default_factory=list)
    is_solved: bool = False
    is_failed: bool = False

    def add_guess(self, guess_result: GuessResult):
        """Add a new guess result to the game state."""
        self.guesses.append(guess_result)
        self.turn = len(self.guesses) + 1

        if guess_result.is_correct:
            self.is_solved = True
        elif self.turn > 6:
            self.is_failed = True

    def get_last_guess(self) -> Optional[GuessResult]:
        """Get the most recent guess."""
        return self.guesses[-1] if self.guesses else None

    @property
    def remaining_turns(self) -> int:
        """Get number of turns remaining."""
        return max(0, 6 - len(self.guesses))

    @property
    def is_game_over(self) -> bool:
        """Check if the game is over (won or lost)."""
        return self.is_solved or self.is_failed


class EntropyCalculation(BaseModel):
    """Result of entropy calculation for a potential guess."""

    word: str = Field(..., min_length=5, max_length=5)
    entropy: float = Field(..., ge=0.0)
    pattern_count: int = Field(..., ge=1)
    calculation_time: Optional[float] = None
