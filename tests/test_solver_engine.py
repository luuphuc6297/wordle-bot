"""Tests for SolverEngine, focusing on feedback simulation edge cases."""

import pytest

from core.use_cases.solver_engine import SolverEngine


class TestFeedbackSimulation:
    """Test the critical feedback simulation logic with edge cases."""

    @pytest.fixture
    def solver(self):
        """Create a SolverEngine instance for testing."""
        return SolverEngine(time_budget_seconds=1.0)  # Short budget for testing

    def test_basic_feedback_simulation(self, solver):
        """Test basic feedback without duplicates."""
        # Perfect match
        assert solver._simulate_feedback("CRANE", "CRANE") == "+++++"

        # No matches
        assert solver._simulate_feedback("CRANE", "SPLIT") == "-----"

        # Mixed feedback
        assert solver._simulate_feedback("CRANE", "TRACK") == "o++--"

        # All present but wrong positions
        assert solver._simulate_feedback("CRANE", "NERAC") == "ooooo"

    def test_duplicate_letters_in_guess_single_in_answer(self, solver):
        """Test duplicate letters in guess when answer has single occurrence."""
        # Guess has duplicate E, answer has single E
        assert (
            solver._simulate_feedback("SPEED", "CRANE") == "-----"
        )  # No S,P,E,E,D in CRANE
        assert (
            solver._simulate_feedback("GEESE", "CRANE") == "--o--"
        )  # Only one E should be yellow
        assert (
            solver._simulate_feedback("ERASE", "CRANE") == "o-+--"
        )  # E yellow, A green

        # More complex case
        assert (
            solver._simulate_feedback("ALLEY", "PLANE") == "+--o-"
        )  # A green, L yellow (only one)

    def test_duplicate_letters_in_answer_single_in_guess(self, solver):
        """Test single letter in guess when answer has duplicates."""
        # Guess has single L, answer has double L
        assert (
            solver._simulate_feedback("PLANE", "ALLEY") == "-+---"
        )  # L green at position 2
        assert (
            solver._simulate_feedback("LOGIC", "ALLEY") == "+----"
        )  # L green at position 1
        assert (
            solver._simulate_feedback("CHILD", "ALLEY") == "----o"
        )  # L yellow (not in position)

    def test_duplicate_letters_both_guess_and_answer(self, solver):
        """Test duplicates in both guess and answer."""
        # Both have double L
        assert (
            solver._simulate_feedback("ALLEY", "LLAMA") == "-++--"
        )  # Both Ls match positions

        # Different duplicate patterns
        assert (
            solver._simulate_feedback("SPEED", "ERASE") == "o-oo-"
        )  # Complex E handling
        assert (
            solver._simulate_feedback("GEESE", "ERASE") == "---o+"
        )  # E,S,E all handled correctly

    def test_tricky_duplicate_cases(self, solver):
        """Test particularly tricky duplicate letter scenarios."""
        # The classic SPEED vs ERASE case
        assert solver._simulate_feedback("SPEED", "ERASE") == "o-oo-"

        # TESTS vs SPEED (multiple duplicates)
        assert solver._simulate_feedback("TESTS", "SPEED") == "-oo--"

        # GEESE vs SPEED
        assert solver._simulate_feedback("GEESE", "SPEED") == "---o+"

        # ALLEY vs LLAMA
        assert solver._simulate_feedback("ALLEY", "LLAMA") == "o+o--"

    def test_edge_cases(self, solver):
        """Test edge cases and boundary conditions."""
        # Same word
        assert solver._simulate_feedback("HELLO", "HELLO") == "+++++"

        # All different
        assert solver._simulate_feedback("ABCDE", "FGHIJ") == "-----"

        # One letter different
        assert solver._simulate_feedback("HELLO", "HALLO") == "+-+++"

        # Anagram
        assert (
            solver._simulate_feedback("LISTEN", "SILENT") == "ooooo-"
        )  # All letters present but wrong positions

    def test_invalid_inputs(self, solver):
        """Test error handling for invalid inputs."""
        with pytest.raises(ValueError, match="Words must be exactly 5 letters"):
            solver._simulate_feedback("HI", "HELLO")

        with pytest.raises(ValueError, match="Words must be exactly 5 letters"):
            solver._simulate_feedback("HELLO", "TOOLONG")

        with pytest.raises(ValueError, match="Words must be exactly 5 letters"):
            solver._simulate_feedback("", "HELLO")

    def test_case_insensitivity(self, solver):
        """Test that feedback simulation is case-insensitive."""
        assert solver._simulate_feedback("hello", "WORLD") == "-----"
        assert solver._simulate_feedback("HELLO", "world") == "-----"
        assert solver._simulate_feedback("hello", "world") == "-----"
        assert solver._simulate_feedback("CrAnE", "crane") == "+++++"

    def test_known_wordle_examples(self, solver):
        """Test against known Wordle examples from real gameplay."""
        # Real Wordle patterns that have caused issues
        test_cases = [
            # (guess, answer, expected_pattern)
            ("AUDIO", "ADIEU", "+ooo-"),
            ("STARE", "ROAST", "oo+o-"),
            ("SLATE", "LEAST", "oo+oo"),
            ("CRANE", "TRACE", "o++-+"),
            ("LIGHT", "MIGHT", "-++++"),
            ("ABOUT", "DOUBT", "-++++"),
            ("DANCE", "CANED", "o++oo"),
        ]

        for guess, answer, expected in test_cases:
            result = solver._simulate_feedback(guess, answer)
            assert (
                result == expected
            ), f"Failed: {guess} vs {answer}, got {result}, expected {expected}"


class TestEntropyCalculation:
    """Test entropy calculation functionality."""

    @pytest.fixture
    def solver(self):
        """Create a SolverEngine instance for testing."""
        return SolverEngine(time_budget_seconds=0.1)  # Very short for fast tests

    def test_entropy_calculation_basic(self, solver):
        """Test basic entropy calculation."""
        # Single possible answer should give 0 entropy
        entropy = solver._calculate_entropy_for_word("CRANE", ["CRANE"])
        assert entropy == 0.0

        # Two equally likely outcomes should give 1 bit
        possible_answers = ["CRANE", "PLANE"]  # Only differ in first letter
        entropy = solver._calculate_entropy_for_word("XRAXE", possible_answers)
        assert entropy == pytest.approx(1.0, abs=0.1)

    def test_entropy_with_different_word_lists(self, solver):
        """Test entropy calculation with different word list sizes."""
        small_list = ["CRANE", "PLANE", "FRAME"]
        large_list = solver.lexicon.answers[:100]  # First 100 answers

        # Entropy should generally increase with more possibilities
        entropy_small = solver._calculate_entropy_for_word("STARE", small_list)
        entropy_large = solver._calculate_entropy_for_word("STARE", large_list)

        assert entropy_small >= 0
        assert entropy_large >= 0
        assert entropy_large > entropy_small

    def test_find_best_guess_first_turn(self, solver):
        """Test that first guess returns SALET."""
        possible_answers = solver.lexicon.answers[:100]
        best_guess = solver.find_best_guess(possible_answers, turn=1)
        assert best_guess == "SALET"

    def test_find_best_guess_single_answer(self, solver):
        """Test behavior when only one answer remains."""
        best_guess = solver.find_best_guess(["CRANE"], turn=2)
        assert best_guess == "CRANE"

    def test_find_best_guess_two_answers(self, solver):
        """Test behavior when two answers remain."""
        best_guess = solver.find_best_guess(["CRANE", "PLANE"], turn=2)
        assert best_guess in ["CRANE", "PLANE"]


class TestPerformance:
    """Test performance-related aspects."""

    @pytest.fixture
    def solver(self):
        """Create a SolverEngine instance for performance testing."""
        return SolverEngine(time_budget_seconds=0.5)

    def test_time_budget_respected(self, solver):
        """Test that time budget is roughly respected."""
        import time

        # Use a reasonable subset of answers for timing test
        possible_answers = solver.lexicon.answers[:50]

        start_time = time.time()
        best_guess = solver.find_best_guess(possible_answers, turn=2)
        elapsed_time = time.time() - start_time

        # Should not exceed time budget by more than 50% (accounting for overhead)
        assert elapsed_time <= solver.time_budget * 1.5
        assert best_guess is not None
        assert len(best_guess) == 5

    def test_detailed_entropy_calculation(self, solver):
        """Test detailed entropy calculation method."""
        possible_answers = ["CRANE", "PLANE", "FRAME", "BLAME", "FLAME"]

        result = solver.calculate_detailed_entropy("STARE", possible_answers)

        assert result.word == "STARE"
        assert result.entropy > 0
        assert result.pattern_count > 0
        assert result.calculation_time is not None
        assert result.calculation_time >= 0
