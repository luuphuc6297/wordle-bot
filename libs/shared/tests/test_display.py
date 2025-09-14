"""Unit tests for GameDisplay class."""

from unittest.mock import patch

from shared.domain.models import FeedbackType
from shared.utils.display import GameDisplay


class TestGameDisplay:
  """Test cases for GameDisplay class."""

  def test_init_default_values(self):
    """Test GameDisplay initialization with default values."""
    display = GameDisplay()

    assert display.show_detailed is True
    assert display.game_start_time is None
    assert display.game_id is None

  def test_init_custom_values(self):
    """Test GameDisplay initialization with custom values."""
    display = GameDisplay(show_detailed=False)

    assert display.show_detailed is False
    assert display.game_start_time is None
    assert display.game_id is None

  def test_start_new_game_with_id(self):
    """Test starting a new game with custom ID."""
    display = GameDisplay()

    with patch("time.time", return_value=1234567890.0):
      display.start_new_game("test_game_123")

    assert display.game_start_time == 1234567890.0
    assert display.game_id == "test_game_123"

  def test_start_new_game_without_id(self):
    """Test starting a new game without ID (auto-generated)."""
    display = GameDisplay()

    with patch("time.time", return_value=1234567890.0):
      display.start_new_game()

    assert display.game_start_time == 1234567890.0
    assert display.game_id == "game_1234567890"

  def test_feedback_emojis_mapping(self):
    """Test feedback emojis mapping is correct."""
    display = GameDisplay()

    assert display.FEEDBACK_EMOJIS[FeedbackType.CORRECT] == "🟩"
    assert display.FEEDBACK_EMOJIS[FeedbackType.PRESENT] == "🟨"
    assert display.FEEDBACK_EMOJIS[FeedbackType.ABSENT] == "⬛"

  def test_feedback_symbols_mapping(self):
    """Test feedback symbols mapping is correct."""
    display = GameDisplay()

    assert display.FEEDBACK_SYMBOLS[FeedbackType.CORRECT] == "+"
    assert display.FEEDBACK_SYMBOLS[FeedbackType.PRESENT] == "o"
    assert display.FEEDBACK_SYMBOLS[FeedbackType.ABSENT] == "-"

  def test_show_victory_performance_rating(self):
    """Test victory message with different performance ratings."""
    display = GameDisplay()
    display.game_start_time = 1000.0

    with patch("time.time", return_value=1005.0):
      # Test excellent performance (3 guesses)
      with patch("builtins.print") as mock_print:
        display.show_victory(3)
        assert any("🏆 EXCELLENT" in str(call) for call in mock_print.call_args_list)

  def test_show_failure_with_target_word(self):
    """Test failure message with target word."""
    display = GameDisplay()
    display.game_id = "test_game"
    display.game_start_time = 1000.0

    with patch("time.time", return_value=1005.0):
      with patch("builtins.print") as mock_print:
        display.show_failure(6, "TARGET")
        assert any(
          "The correct word was: 'TARGET'" in str(call)
          for call in mock_print.call_args_list
        )

  def test_show_thinking_message(self):
    """Test thinking message display."""
    display = GameDisplay()

    with patch("builtins.print") as mock_print:
      display.show_thinking("Calculating entropy...")
      assert any(
        "🤔 Calculating entropy..." in str(call) for call in mock_print.call_args_list
      )
