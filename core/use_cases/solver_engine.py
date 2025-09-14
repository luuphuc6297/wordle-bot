"""SolverEngine - Core entropy-maximization algorithm for Wordle solving."""

import math
import os
import time
from collections import defaultdict
from concurrent.futures import Future, ThreadPoolExecutor, as_completed

import numpy as np

from core.domain.models import EntropyCalculation
from infrastructure.data.word_lexicon import WordLexicon


class SolverEngine:
    """Core solver using information-theoretic approach with entropy maximization."""

    OPTIMAL_FIRST_GUESS: str = "SALET"  # Pre-computed optimal first guess

    def __init__(
        self, time_budget_seconds: float = 5.0, max_workers: int | None = None
    ):
        """Initialize the solver engine.

        Args:
            time_budget_seconds: Maximum time allowed for guess calculation
            max_workers: Number of threads for parallel computation (None = auto)
        """
        self.time_budget: float = time_budget_seconds
        self.max_workers: int = max_workers or min(8, (os.cpu_count() or 1) + 4)
        self.lexicon: WordLexicon = WordLexicon()

        # Convert to numpy arrays for better performance
        self._all_guesses: np.ndarray = np.array(self.lexicon.allowed_guesses)
        self._all_answers: np.ndarray = np.array(self.lexicon.answers)

    def find_best_guess(self, possible_answers: list[str], turn: int = 1) -> str:
        """Find the best guess using entropy maximization.

        Args:
            possible_answers: Current list of possible answer words
            turn: Current turn number (1-6)

        Returns:
            The optimal guess word
        """
        # Use pre-computed first guess
        if turn == 1:
            return self.OPTIMAL_FIRST_GUESS

        # If only one answer remains, guess it
        if len(possible_answers) == 1:
            return possible_answers[0]

        # If very few answers remain, just pick the first one
        if len(possible_answers) <= 2:
            return possible_answers[0]

        possible_answers_array: np.ndarray = np.array(possible_answers)

        # Calculate entropy for all potential guesses within time budget
        best_word: str = possible_answers[0]  # Fallback
        best_entropy: float = 0.0

        start_time: float = time.time()

        # Use threading for parallelization (NumPy releases GIL)
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit entropy calculation tasks
            futures: dict[Future[float], str] = {}
            for guess_word in self._all_guesses.tolist():
                guess_word: str = str(guess_word)
                if (
                    time.time() - start_time > self.time_budget * 0.9
                ):  # Leave some buffer
                    break

                future = executor.submit(
                    self._calculate_entropy_for_word, guess_word, possible_answers_array
                )
                futures[future] = guess_word

            # Collect results as they complete
            for future in as_completed(futures, timeout=self.time_budget):  # type: ignore
                try:
                    entropy: float = future.result()  # type: ignore
                    word: str = futures[future]  # type: ignore

                    if entropy > best_entropy:
                        best_entropy = entropy
                        best_word = word

                except Exception:
                    # Skip failed calculations
                    continue

                # Check time budget
                if time.time() - start_time > self.time_budget:
                    break

        return best_word

    def _calculate_entropy_for_word(
        self, guess_word: str, possible_answers: np.ndarray
    ) -> float:
        """Calculate entropy for a single guess word against possible answers.

        Args:
            guess_word: The word to calculate entropy for
            possible_answers: Array of possible answer words

        Returns:
            Entropy value in bits
        """
        pattern_counts: defaultdict[str, int] = defaultdict(int)

        # Simulate feedback for each possible answer
        for answer in possible_answers:
            answer: str = str(answer)
            pattern: str = self._simulate_feedback(guess_word, answer)
            pattern_counts[pattern] += 1

        # Calculate Shannon entropy
        total_answers = len(possible_answers)
        entropy = 0.0

        for count in pattern_counts.values():
            if count > 0:
                probability = count / total_answers
                entropy -= probability * math.log2(probability)

        return entropy

    def _simulate_feedback(self, guess: str, answer: str) -> str:
        """Simulate Wordle feedback for a guess against an answer.

        This is the critical function that must handle duplicate letters correctly.

        Args:
            guess: The guessed word
            answer: The actual answer word

        Returns:
            Feedback pattern string (e.g., "++o--")
        """
        guess = guess.upper()
        answer = answer.upper()

        if len(guess) != 5 or len(answer) != 5:
            raise ValueError("Words must be exactly 5 letters")

        # Initialize feedback array
        feedback = ["-"] * 5

        # Count letter frequencies in the answer
        answer_letter_counts: defaultdict[str, int] = defaultdict(int)
        for letter in answer:
            answer_letter_counts[letter] += 1

        # First pass: Mark exact matches (green)
        for i in range(5):
            if guess[i] == answer[i]:
                feedback[i] = "+"
                answer_letter_counts[guess[i]] -= 1

        # Second pass: Mark present but wrong position (yellow)
        for i in range(5):
            if feedback[i] != "+":  # Not already marked as correct
                letter = guess[i]
                if answer_letter_counts[letter] > 0:
                    feedback[i] = "o"
                    answer_letter_counts[letter] -= 1

        return "".join(feedback)

    def simulate_feedback(self, guess: str, answer: str) -> str:
        """Public method to simulate Wordle feedback for a guess against an answer.

        Args:
            guess: The guessed word
            answer: The actual answer word

        Returns:
            Feedback pattern string (e.g., "++o--")
        """
        return self._simulate_feedback(guess, answer)

    def calculate_detailed_entropy(
        self, guess_word: str, possible_answers: list[str]
    ) -> EntropyCalculation:
        """Calculate detailed entropy information for a specific word.

        Args:
            guess_word: Word to analyze
            possible_answers: Current possible answers

        Returns:
            Detailed entropy calculation result
        """
        start_time = time.time()

        possible_answers_array: np.ndarray = np.array(possible_answers)
        entropy = self._calculate_entropy_for_word(guess_word, possible_answers_array)

        # Count unique patterns
        patterns: set[str] = set()
        for answer in possible_answers:
            answer: str = str(answer)
            pattern: str = self._simulate_feedback(guess_word, answer)
            patterns.add(pattern)

        calculation_time = time.time() - start_time

        return EntropyCalculation(
            word=guess_word,
            entropy=entropy,
            pattern_count=len(patterns),
            calculation_time=calculation_time,
        )
