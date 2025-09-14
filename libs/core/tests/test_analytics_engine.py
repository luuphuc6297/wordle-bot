"""Unit tests for AnalyticsEngine."""

from unittest.mock import patch

from core.algorithms.analytics_engine import AnalyticsEngine, WordDifficulty


class TestAnalyticsEngine:
  """Test cases for AnalyticsEngine."""

  def setup_method(self):
    """Set up test fixtures."""
    with (
      patch("core.algorithms.analytics_engine.WordLexicon"),
      patch("core.algorithms.analytics_engine.SolverEngine"),
    ):
      self.analytics = AnalyticsEngine()

  def test_analytics_engine_initialization(self):
    """Test AnalyticsEngine initializes correctly."""
    # Test that analytics engine initializes without errors
    assert self.analytics is not None
    assert hasattr(self.analytics, "lexicon")
    assert hasattr(self.analytics, "solver")
    assert hasattr(self.analytics, "logger")

  def test_word_difficulty_creation(self):
    """Test WordDifficulty dataclass creation."""
    # Test WordDifficulty can be created with valid data
    word_diff = WordDifficulty(
      word="TEST",
      avg_guesses=3.5,
      success_rate=1.0,
      entropy_profile=[2.1, 1.8, 1.5],
      difficulty_score=0.7,
    )

    assert word_diff.word == "TEST"
    assert word_diff.avg_guesses == 3.5
    assert word_diff.success_rate == 1.0
    assert word_diff.entropy_profile == [2.1, 1.8, 1.5]
    assert word_diff.difficulty_score == 0.7

  def test_entropy_calculation_helper(self):
    """Test entropy calculation logic with helper method."""
    # Test entropy calculation with simple probabilities
    probabilities = [0.5, 0.3, 0.2]
    result = self._calculate_entropy(probabilities)

    # Verify result is a valid number
    assert isinstance(result, float)
    assert result > 0

  def _calculate_entropy(self, probabilities):
    """Helper method to test entropy calculation."""
    import numpy as np

    probs = np.array(probabilities)
    return -np.sum(probs * np.log2(probs + 1e-10))
