"""Tests for domain models and game state management."""

import pytest

from core.algorithms.game_state_manager import GameStateManager
from core.domain.models import EntropyCalculation, FeedbackType, GameState, GuessResult


class TestGuessResult:
    """Test GuessResult model functionality."""

    def test_from_api_response_basic(self):
        """Test creating GuessResult from API response format."""
        result = GuessResult.from_api_response("CRANE", "++o--")

        assert result.guess == "CRANE"
        assert len(result.feedback) == 5
        assert result.feedback[0] == FeedbackType.CORRECT
        assert result.feedback[1] == FeedbackType.CORRECT
        assert result.feedback[2] == FeedbackType.PRESENT
        assert result.feedback[3] == FeedbackType.ABSENT
        assert result.feedback[4] == FeedbackType.ABSENT
        assert not result.is_correct

    def test_from_api_response_correct_guess(self):
        """Test creating GuessResult for a correct guess."""
        result = GuessResult.from_api_response("CRANE", "+++++")

        assert result.guess == "CRANE"
        assert all(f == FeedbackType.CORRECT for f in result.feedback)
        assert result.is_correct

    def test_from_api_response_various_formats(self):
        """Test different API response formats."""
        # Using 'x' instead of '-' for absent
        result = GuessResult.from_api_response("CRANE", "++xoo")
        assert result.feedback[2] == FeedbackType.ABSENT

        # Mixed format
        result = GuessResult.from_api_response("CRANE", "+-ox-")
        expected = [
            FeedbackType.CORRECT,
            FeedbackType.ABSENT,
            FeedbackType.PRESENT,
            FeedbackType.ABSENT,
            FeedbackType.ABSENT,
        ]
        assert result.feedback == expected

    def test_from_api_response_invalid(self):
        """Test error handling for invalid API responses."""
        with pytest.raises(ValueError, match="Invalid result string length"):
            GuessResult.from_api_response("CRANE", "+++")

        with pytest.raises(ValueError, match="Invalid feedback character"):
            GuessResult.from_api_response("CRANE", "++z--")

    def test_to_pattern_string(self):
        """Test converting feedback back to pattern string."""
        result = GuessResult.from_api_response("CRANE", "++o--")
        assert result.to_pattern_string() == "++o--"

        result = GuessResult.from_api_response("CRANE", "+++++")
        assert result.to_pattern_string() == "+++++"

    def test_case_handling(self):
        """Test that guess is converted to uppercase."""
        result = GuessResult.from_api_response("crane", "+++++")
        assert result.guess == "CRANE"


class TestGameState:
    """Test GameState model functionality."""

    def test_initial_state(self):
        """Test initial game state."""
        state = GameState()

        assert state.turn == 1
        assert len(state.guesses) == 0
        assert not state.is_solved
        assert not state.is_failed
        assert not state.is_game_over
        assert state.remaining_turns == 6

    def test_add_guess_normal(self):
        """Test adding a normal (incorrect) guess."""
        state = GameState()
        guess = GuessResult.from_api_response("CRANE", "++o--")

        state.add_guess(guess)

        assert state.turn == 2
        assert len(state.guesses) == 1
        assert state.guesses[0] == guess
        assert not state.is_solved
        assert not state.is_failed
        assert state.remaining_turns == 5

    def test_add_guess_correct(self):
        """Test adding a correct guess."""
        state = GameState()
        guess = GuessResult.from_api_response("CRANE", "+++++")

        state.add_guess(guess)

        assert state.turn == 2
        assert len(state.guesses) == 1
        assert state.is_solved
        assert not state.is_failed
        assert state.is_game_over

    def test_game_failure_after_6_guesses(self):
        """Test game failure after 6 incorrect guesses."""
        state = GameState()

        # Add 6 incorrect guesses
        for _i in range(6):
            guess = GuessResult.from_api_response("WRONG", "-----")
            state.add_guess(guess)

        assert state.turn == 7
        assert len(state.guesses) == 6
        assert not state.is_solved
        assert state.is_failed
        assert state.is_game_over
        assert state.remaining_turns == 0

    def test_get_last_guess(self):
        """Test getting the last guess."""
        state = GameState()

        # No guesses yet
        assert state.get_last_guess() is None

        # Add a guess
        guess = GuessResult.from_api_response("CRANE", "++o--")
        state.add_guess(guess)

        assert state.get_last_guess() == guess


class TestGameStateManager:
    """Test GameStateManager functionality."""

    def test_initialization(self):
        """Test GameStateManager initialization."""
        manager = GameStateManager()

        assert manager.get_remaining_answers_count() > 2000  # Should have ~2315 answers
        assert not manager.is_game_over()
        assert not manager.is_solved()
        assert not manager.is_failed()

    def test_add_guess_result_filtering(self):
        """Test that adding guess results filters possible answers."""
        manager = GameStateManager()
        initial_count = manager.get_remaining_answers_count()

        # Add a guess that should eliminate many possibilities
        guess_result = GuessResult.from_api_response("CRANE", "-----")
        manager.add_guess_result(guess_result)

        final_count = manager.get_remaining_answers_count()

        # Should have fewer possible answers now
        assert final_count < initial_count
        assert final_count > 0  # But still have some possibilities

    def test_game_completion_on_correct_guess(self):
        """Test game completion when correct guess is made."""
        # Start with a small set of answers for predictable testing
        manager = GameStateManager(initial_answers=["CRANE", "PLANE", "FRAME"])

        # Make a correct guess
        guess_result = GuessResult.from_api_response("CRANE", "+++++")
        manager.add_guess_result(guess_result)

        assert manager.is_solved()
        assert manager.is_game_over()
        assert not manager.is_failed()

    def test_consistent_filtering(self):
        """Test that filtering is consistent with feedback simulation."""
        # Use a controlled set of answers
        initial_answers = ["CRANE", "PLANE", "FRAME", "BLAME", "FLAME"]
        manager = GameStateManager(initial_answers=initial_answers)

        # Simulate a guess that should eliminate some but not all answers
        guess_result = GuessResult.from_api_response(
            "STARE", "---o-"
        )  # Only E is present
        manager.add_guess_result(guess_result)

        remaining = manager.get_possible_answers()

        # All remaining answers should contain E but not S, T, A, R
        for answer in remaining:
            assert "E" in answer
            assert not any(letter in answer for letter in "STAR")

    def test_get_game_summary(self):
        """Test getting game summary."""
        manager = GameStateManager()

        # Add a couple of guesses
        guess1 = GuessResult.from_api_response("CRANE", "++o--")
        guess2 = GuessResult.from_api_response("PLUMB", "-----")

        manager.add_guess_result(guess1)
        manager.add_guess_result(guess2)

        summary = manager.get_game_summary()

        assert summary["turn"] == 3
        assert summary["total_guesses"] == 2
        assert len(summary["guesses"]) == 2
        assert summary["guesses"][0]["guess"] == "CRANE"
        assert summary["guesses"][1]["guess"] == "PLUMB"
        assert summary["remaining_answers"] > 0

    def test_reset_game(self):
        """Test resetting game state."""
        manager = GameStateManager()

        # Add some guesses and change state
        guess = GuessResult.from_api_response("CRANE", "++o--")
        manager.add_guess_result(guess)

        original_count = len(manager.lexicon.answers)
        assert manager.get_remaining_answers_count() < original_count

        # Reset the game
        manager.reset_game()

        assert manager.get_remaining_answers_count() == original_count
        assert not manager.is_game_over()
        assert manager.game_state.turn == 1
        assert len(manager.game_state.guesses) == 0


class TestEntropyCalculation:
    """Test EntropyCalculation model."""

    def test_creation(self):
        """Test creating EntropyCalculation instance."""
        calc = EntropyCalculation(
            word="CRANE", entropy=5.23, pattern_count=243, calculation_time=0.123
        )

        assert calc.word == "CRANE"
        assert calc.entropy == 5.23
        assert calc.pattern_count == 243
        assert calc.calculation_time == 0.123

    def test_validation(self):
        """Test validation of EntropyCalculation fields."""
        # Valid creation
        calc = EntropyCalculation(word="CRANE", entropy=0.0, pattern_count=1)
        assert calc.entropy >= 0

        # Invalid word length should be caught by Field validation
        with pytest.raises(ValueError):  # Pydantic validation error
            EntropyCalculation(word="HI", entropy=1.0, pattern_count=1)

        # Negative entropy should be caught
        with pytest.raises(ValueError):  # Pydantic validation error
            EntropyCalculation(word="CRANE", entropy=-1.0, pattern_count=1)
