"""SolverEngine - Core entropy-maximization algorithm for Wordle solving."""

import math
import os
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np

from shared.domain.models import EntropyCalculation
from shared.infrastructure.data.word_lexicon import WordLexicon


class SolverEngine:
  """Core solver using information-theoretic approach with entropy maximization."""

  OPTIMAL_FIRST_GUESS = "SALET"  # Pre-computed optimal first guess

  def __init__(self, time_budget_seconds: float = 5.0, max_workers: int = None):
    """Initialize the solver engine.

    Args:
        time_budget_seconds: Maximum time allowed for guess calculation
        max_workers: Number of threads for parallel computation (None = auto)
    """
    self.time_budget = time_budget_seconds
    self.max_workers = max_workers or min(8, (os.cpu_count() or 1) + 4)
    self.lexicon = WordLexicon()

    # Convert to numpy arrays for better performance
    self._all_guesses = np.array(self.lexicon.allowed_guesses)
    self._all_answers = np.array(self.lexicon.answers)

  def find_best_guess(self, possible_answers: list[str], turn: int = 1) -> str:
    """Find the best guess using entropy maximization.

    Args:
        possible_answers: Current list of possible answer words
        turn: Current turn number (1-6)

    Returns:
        The optimal guess word
    """
    if turn == 1:
      return self.OPTIMAL_FIRST_GUESS

    if len(possible_answers) <= 2:
      return possible_answers[0]

    return self._find_optimal_guess(possible_answers)

  def _find_optimal_guess(self, possible_answers: list[str]) -> str:
    """Find optimal guess using parallel entropy calculation."""
    possible_answers_array = np.array(possible_answers)
    best_word = possible_answers[0]
    best_entropy = 0.0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
      futures = self._submit_entropy_tasks(executor, possible_answers_array, start_time)
      best_word, best_entropy = self._collect_entropy_results(
        futures, best_word, best_entropy, start_time
      )

    return best_word

  def _submit_entropy_tasks(self, executor, possible_answers_array, start_time):
    """Submit entropy calculation tasks to executor."""
    futures = {}
    for guess_word in self._all_guesses:
      if time.time() - start_time > self.time_budget * 0.9:
        break
      future = executor.submit(
        self._calculate_entropy_for_word, guess_word, possible_answers_array
      )
      futures[future] = guess_word
    return futures

  def _collect_entropy_results(self, futures, best_word, best_entropy, start_time):
    """Collect entropy calculation results."""
    for future in as_completed(futures, timeout=self.time_budget):
      try:
        entropy = future.result()
        word = futures[future]
        if entropy > best_entropy:
          best_entropy = entropy
          best_word = word
      except Exception:
        continue
      if time.time() - start_time > self.time_budget:
        break
    return best_word, best_entropy

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
    pattern_counts = defaultdict(int)

    # Simulate feedback for each possible answer
    for answer in possible_answers:
      pattern = self._simulate_feedback(guess_word, answer)
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
    answer_letter_counts = defaultdict(int)
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

    possible_answers_array = np.array(possible_answers)
    entropy = self._calculate_entropy_for_word(guess_word, possible_answers_array)

    # Count unique patterns
    patterns = set()
    for answer in possible_answers:
      pattern = self._simulate_feedback(guess_word, answer)
      patterns.add(pattern)

    calculation_time = time.time() - start_time

    return EntropyCalculation(
      word=guess_word,
      entropy=entropy,
      pattern_count=len(patterns),
      calculation_time=calculation_time,
    )
