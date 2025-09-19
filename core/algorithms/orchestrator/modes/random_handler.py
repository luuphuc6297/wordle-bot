"""Random game mode handler.

Handles the random API mode (/random) gameplay logic.
"""

import time

from config.settings import Settings
from core.algorithms.solver_engine import SolverEngine
from core.algorithms.state_manager import ApiGameStateManager
from core.domain.types import SimulationResult
from infrastructure.api.game_client import GameClient
from infrastructure.data.word_lexicon import WordLexicon
from utils.display import GameDisplay

from .base_handler import BaseGameHandler


class RandomHandler(BaseGameHandler):
    """Handler for random game mode."""

    def __init__(
        self,
        client: GameClient,
        solver: SolverEngine,
        lexicon: WordLexicon,
        display: GameDisplay | None,
        settings: Settings,
    ) -> None:
        super().__init__(solver, lexicon, display, settings)
        self.client = client

    def run_game(self) -> SimulationResult:
        """Play a game using the random API mode (/random)."""
        if self.display:
            self.display.print_header()
            self.display.start_new_game("random")

        start = time.time()

        # Step 1: Get a random target word by calling Random API
        initial_guess = self.solver.find_best_guess(self.lexicon.get_all_answers(), 1)
        random_result = self.client.submit_random_guess(initial_guess)

        if random_result.is_correct:
            # Lucky! We got it on first try
            if self.display:
                self.display.show_feedback(random_result, 0)
            return {
                "game_result": {
                    "solved": True,
                    "failed": False,
                    "total_turns": 1,
                    "final_answer": initial_guess,
                },
                "performance_metrics": {
                    "total_game_time_seconds": round(time.time() - start, 2),
                    "average_time_per_turn": round(time.time() - start, 2),
                    "remaining_possibilities": [],
                },
                "guess_history": [
                    {
                        "guess": initial_guess,
                        "feedback": random_result.to_pattern_string(),
                        "correct": True,
                    }
                ],
                "lexicon_stats": self.lexicon.get_stats(),
                "timestamp": time.time(),
            }

        # Step 2: Find the actual target word by trying all possible answers
        game_manager = ApiGameStateManager(app_settings=self.settings)
        game_manager.add_guess_result(random_result)
        possible_answers = game_manager.get_possible_answers()

        if self.display:
            self.display.show_feedback(random_result, len(possible_answers))

        self.logger.info(
            f"Random API revealed target has {len(possible_answers)} possible answers"
        )

        # Step 3: Find the actual target word by trying each possible answer
        target_word = self._find_target_word(
            initial_guess, random_result, possible_answers
        )

        if not target_word:
            self.logger.warning("Could not determine target word from Random API")
            return {
                "game_result": {
                    "solved": False,
                    "failed": True,
                    "total_turns": 1,
                    "final_answer": None,
                },
                "performance_metrics": {
                    "total_game_time_seconds": round(time.time() - start, 2),
                    "average_time_per_turn": round(time.time() - start, 2),
                    "remaining_possibilities": possible_answers,
                },
                "guess_history": [
                    {
                        "guess": initial_guess,
                        "feedback": random_result.to_pattern_string(),
                        "correct": False,
                    }
                ],
                "lexicon_stats": self.lexicon.get_stats(),
                "timestamp": time.time(),
            }

        # Step 4: Use entropy algorithm to solve the target word
        return self._solve_target_word(target_word, game_manager, start)

    def _find_target_word(
        self, initial_guess: str, random_result, possible_answers: list[str]
    ) -> str | None:
        """Find the actual target word by testing candidates."""
        for candidate in possible_answers:
            try:
                test_result = self.client.submit_word_target_guess(
                    candidate, initial_guess
                )
                if test_result.to_pattern_string() == random_result.to_pattern_string():
                    self.logger.info(f"Found target word: {candidate}")
                    return candidate
            except Exception as e:
                self.logger.debug(f"Testing {candidate}: {e}")
                continue
        return None

    def _solve_target_word(
        self, target_word: str, game_manager: ApiGameStateManager, start_time: float
    ) -> SimulationResult:
        """Solve the target word using entropy algorithm."""
        turn = 2
        max_turns = 6

        while turn <= max_turns and not game_manager.is_game_over():
            current_answers = game_manager.get_possible_answers()

            if len(current_answers) == 0:
                self.logger.warning("No possible answers remaining")
                break

            if len(current_answers) == 1:
                # Only one possible answer left
                final_guess = current_answers[0]
                self.logger.info(f"Final guess: {final_guess}")

                try:
                    final_result = self.client.submit_word_target_guess(
                        target_word, final_guess
                    )
                    game_manager.add_guess_result(final_result)

                    if self.display:
                        self.display.show_feedback(final_result, 0)

                    if final_result.is_correct:
                        self.logger.info(
                            f"🎉 SOLVED! Target word: {target_word} in {turn} turns"
                        )
                    break
                except Exception as e:
                    self.logger.error(f"Error submitting final guess: {e}")
                    break

            # Use entropy algorithm to find best guess
            best_guess = self.solver.find_best_guess(current_answers, turn)
            self.logger.info(
                f"Turn {turn}: Guessing '{best_guess}' from {len(current_answers)} possible answers"
            )

            # Submit guess using Word-target API
            try:
                guess_result = self.client.submit_word_target_guess(
                    target_word, best_guess
                )
                game_manager.add_guess_result(guess_result)

                if self.display:
                    self.display.show_feedback(
                        guess_result, len(game_manager.get_possible_answers())
                    )

                if guess_result.is_correct:
                    self.logger.info(
                        f"🎉 SOLVED! Target word: {target_word} in {turn} turns"
                    )
                    break

            except Exception as e:
                self.logger.error(f"Error submitting guess: {e}")
                break

            turn += 1

        # Final result
        solved = game_manager.is_solved()
        turns_used = len(game_manager.get_current_state().guesses)

        game_summary = game_manager.get_game_summary()

        return {
            "game_result": {
                "solved": solved,
                "failed": game_manager.is_failed(),
                "total_turns": turns_used,
                "final_answer": target_word if solved else None,
            },
            "performance_metrics": {
                "total_game_time_seconds": round(time.time() - start_time, 2),
                "average_time_per_turn": round(
                    (time.time() - start_time) / max(1, turns_used), 2
                ),
                "remaining_possibilities": game_manager.get_possible_answers(),
            },
            "guess_history": game_summary["guesses"],
            "lexicon_stats": self.lexicon.get_stats(),
            "timestamp": time.time(),
        }
