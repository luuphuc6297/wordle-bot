"""Offline simulation mode handler.

Handles offline game simulation logic.
"""

import time

from config.settings import Settings
from core.algorithms.solver_engine import SolverEngine
from core.algorithms.state_manager import GameStateManager
from core.domain.models import EntropyCalculation
from core.domain.types import SimulationResult
from infrastructure.data.word_lexicon import WordLexicon
from utils.display import GameDisplay
from utils.logging_config import get_logger


class OfflineHandler:
    """Handler for offline simulation mode."""

    def __init__(
        self,
        solver: SolverEngine,
        lexicon: WordLexicon,
        display: GameDisplay | None,
        settings: Settings,
    ) -> None:
        self.solver = solver
        self.lexicon = lexicon
        self.display = display
        self.settings = settings
        self.logger = get_logger(__name__)

    def run_game(
        self, target_answer: str, game_id: str | None = None
    ) -> SimulationResult:
        """Simulate a game with a known target answer for testing."""
        if not self.lexicon.is_valid_answer(target_answer):
            raise ValueError(f"'{target_answer}' is not a valid answer word")

        self.logger.info(f"Simulating game with target answer: {target_answer}")

        # Initialize display if enabled
        if self.display:
            self.display.print_header()
            self.display.start_new_game(game_id or f"sim_{target_answer}")

        # Initialize local game state (no API calls)
        game_manager = GameStateManager()
        simulation_start = time.time()

        turn = 1
        while not game_manager.is_game_over() and turn <= 6:
            current_answers = game_manager.get_possible_answers()

            # Show thinking process
            if self.display:
                self.display.show_thinking(
                    f"Analyzing {len(current_answers)} possible answers..."
                )

            # Get best guess with timing
            guess_start_time: float = time.time()
            guess: str = self.solver.find_best_guess(
                possible_answers=current_answers, turn=turn
            )
            calculation_time: float = time.time() - guess_start_time

            # Calculate entropy for display
            entropy: float = 0.0
            if len(current_answers) > 1 and self.display and self.display.show_detailed:
                entropy_calc: EntropyCalculation = (
                    self.solver.calculate_detailed_entropy(
                        guess_word=guess, possible_answers=current_answers
                    )
                )
                entropy = entropy_calc.entropy

            # Show guess submission
            if self.display:
                self.display.show_guess_submission(
                    turn,
                    guess,
                    remaining_count=len(current_answers),
                    entropy=entropy,
                    calculation_time=calculation_time,
                )

            # Simulate feedback
            feedback_pattern: str = self.solver._simulate_feedback(
                guess, answer=target_answer
            )

            # Create guess result
            from core.domain.models import GuessResult

            guess_result = GuessResult.from_api_response(guess, feedback_pattern)

            # Update state
            game_manager.add_guess_result(guess_result)

            # Show feedback
            if self.display:
                self.display.show_feedback(
                    guess_result, game_manager.get_remaining_answers_count()
                )

            self.logger.info(msg=f"Turn {turn}: {guess} -> {feedback_pattern}")

            turn += 1

        simulation_time = time.time() - simulation_start

        # Show final result
        if self.display:
            if game_manager.is_solved():
                self.display.show_victory(len(game_manager.get_current_state().guesses))
            else:
                self.display.show_failure(
                    len(game_manager.get_current_state().guesses), target_answer
                )

        game_summary = game_manager.get_game_summary()
        solved = game_manager.is_solved()
        turns_used = len(game_manager.get_current_state().guesses)

        return {
            "game_result": {
                "solved": solved,
                "failed": game_manager.is_failed(),
                "total_turns": turns_used,
                "final_answer": target_answer if solved else None,
            },
            "performance_metrics": {
                "total_game_time_seconds": round(simulation_time, 2),
                "average_time_per_turn": round(simulation_time / max(1, turns_used), 2),
                "remaining_possibilities": game_summary["possible_answers"],
            },
            "guess_history": game_summary["guesses"],
            "lexicon_stats": self.lexicon.get_stats(),
            "timestamp": time.time(),
        }
