"""Daily game mode handler.

Handles the daily puzzle mode gameplay logic.
"""

import time
from typing import Any

from config.settings import Settings
from core.algorithms.solver_engine import SolverEngine
from core.algorithms.state_manager import (
    DailyGameStateManager,
    GameStateManager,
)
from core.domain.types import GameSummary, GuessHistoryItem
from infrastructure.api.game_client import GameClient
from infrastructure.data.word_lexicon import WordLexicon
from utils.display import GameDisplay

from .base_handler import BaseGameHandler


class DailyHandler(BaseGameHandler):
    """Handler for daily game mode."""

    def __init__(
        self,
        client: GameClient,
        solver: SolverEngine,
        lexicon: WordLexicon,
        display: GameDisplay | None,
        settings: Settings,
    ) -> None:
        """Initialize the daily handler.

        Args:
            client: The game client for API calls
            solver: The solver engine
            lexicon: The word lexicon
            display: The game display (optional)
            settings: Application settings
        """
        super().__init__(solver, lexicon, display, settings)
        self.client = client

    def run_game(self) -> GameSummary:
        """Solve the daily Wordle puzzle using improved strategy."""
        self.logger.info(msg="Starting daily puzzle solution")
        game_start_time = time.time()

        try:
            # Initialize new game
            self._initialize_game()

            # Step 1: Get initial feedback from Daily API
            initial_guess = self.solver.find_best_guess(
                self.lexicon.get_all_answers(), 1
            )
            daily_result = self.client.submit_guess(initial_guess)

            self.logger.info(
                msg=f"Daily API: '{initial_guess}' -> {daily_result.to_pattern_string()} "
                + f"(Correct: {daily_result.is_correct})"
            )

            # Add display feedback for consistency with Random mode
            if self.display:
                self.display.show_feedback(
                    daily_result, 0
                )  # Will be updated after we know remaining count

            if daily_result.is_correct:
                # Lucky! We got it on first try
                if self.game_state_manager:
                    self.game_state_manager.add_guess_result(daily_result)
                total_game_time = time.time() - game_start_time
                return self._generate_final_summary(total_game_time)

            # Step 2: Update game state with Daily API feedback using improved manager
            daily_game_manager = DailyGameStateManager(app_settings=self.settings)
            daily_game_manager.add_guess_result(daily_result)
            possible_answers = daily_game_manager.get_possible_answers()
            self.logger.info(
                f"Daily API revealed target has {len(possible_answers)} possible answers"
            )

            # Step 3: Determine the actual target using /word/{candidate} that matches first feedback
            target_word = self._find_daily_target_word(
                initial_guess, daily_result, daily_game_manager
            )

            if not target_word:
                self.logger.warning("Could not determine target word from Daily API")
                # Fall back to original strategy
                return self._solve_daily_original()

            # Step 4: Continue solving using /word/{target}
            return self._solve_daily_with_target(
                target_word, daily_game_manager, game_start_time
            )

        except Exception as e:
            self.logger.error(msg=f"Error during puzzle solving: {e}")
            raise
        finally:
            # Cleanup
            self.client.close()

    def _initialize_game(self) -> None:
        """Initialize a new game session."""
        try:
            # Initialize game state manager with all possible answers
            self.game_state_manager = GameStateManager(app_settings=self.settings)
            self.logger.info(msg="Game initialization completed (daily mode)")
        except Exception as e:
            self.logger.error(msg=f"Failed to initialize game: {e}")
            raise

    def _find_daily_target_word(
        self,
        initial_guess: str,
        daily_result,
        daily_game_manager: DailyGameStateManager,
    ) -> str | None:
        """Find the actual target word by testing candidates."""
        current_answers = daily_game_manager.get_possible_answers()
        for candidate in current_answers:
            try:
                test_result = self.client.submit_word_target_guess(
                    candidate, initial_guess
                )
                if test_result.to_pattern_string() == daily_result.to_pattern_string():
                    self.logger.info(f"Found daily target word: {candidate}")
                    return candidate
            except Exception as e:
                self.logger.debug(f"Testing {candidate}: {e}")
                continue
        return None

    def _solve_daily_with_target(
        self,
        target_word: str,
        daily_game_manager: DailyGameStateManager,
        game_start_time: float,
    ) -> dict[str, Any]:
        """Continue solving using /word/{target}."""
        turn = 2
        max_turns = 6

        while turn <= max_turns and not daily_game_manager.is_game_over():
            current_answers = daily_game_manager.get_possible_answers()

            if len(current_answers) == 0:
                self.logger.warning("No possible answers remaining")
                break

            if len(current_answers) == 1:
                final_guess = current_answers[0]
                self.logger.info(f"Final guess: {final_guess}")
                try:
                    final_result = self.client.submit_word_target_guess(
                        target_word, final_guess
                    )
                    daily_game_manager.add_guess_result(final_result)
                    if final_result.is_correct:
                        self.logger.info(
                            f"🎉 SOLVED! Daily target word: {target_word} in {turn} turns"
                        )
                    break
                except Exception as e:
                    self.logger.error(f"Error submitting final guess: {e}")
                    break

            best_guess = self.solver.find_best_guess(current_answers, turn)
            self.logger.info(
                f"Turn {turn}: Guessing '{best_guess}' from {len(current_answers)} possible answers"
            )
            try:
                guess_result = self.client.submit_word_target_guess(
                    target_word, best_guess
                )
                daily_game_manager.add_guess_result(guess_result)
                if self.display:
                    self.display.show_feedback(
                        guess_result,
                        len(daily_game_manager.get_possible_answers()),
                    )
                if guess_result.is_correct:
                    self.logger.info(
                        f"🎉 SOLVED! Daily target word: {target_word} in {turn} turns"
                    )
                    break
            except Exception as e:
                self.logger.error(f"Error submitting guess: {e}")
                break

            turn += 1

        # Game completed - generate final results
        total_game_time = time.time() - game_start_time
        return self._generate_daily_final_summary(total_game_time, daily_game_manager)

    def _solve_daily_original(self) -> dict[str, Any]:
        """Original daily puzzle solving strategy as fallback."""
        self.logger.info("Using original daily solving strategy as fallback")
        game_start_time = time.time()

        try:
            # Initialize new game
            self._initialize_game()

            # Main game loop (max 6 turns)
            while (
                self.game_state_manager and not self.game_state_manager.is_game_over()
            ):
                current_state = self.game_state_manager.get_current_state()
                turn_number = current_state.turn

                self.logger.info(
                    msg=f"Turn {turn_number}: {len(current_state.possible_answers)} possible answers remaining"
                )

                # Calculate optimal guess
                turn_start_time: float = time.time()
                best_guess: str = self.solver.find_best_guess(
                    current_state.possible_answers, turn=turn_number
                )
                calculation_time = time.time() - turn_start_time

                self.logger.info(
                    msg=f"Selected guess '{best_guess}' in {calculation_time:.2f}s"
                )

                # Check if we have no possible answers (constraints impossible)
                if len(current_state.possible_answers) == 0:
                    self.logger.warning(
                        msg="No possible answers remaining - this may be a difficult word with conflicting constraints"
                    )
                    # Try a different strategy: use a word that eliminates many possibilities
                    best_guess = self.solver.find_best_guess(
                        self.lexicon.get_all_answers(), turn=turn_number
                    )
                    self.logger.info(
                        msg=f"Fallback strategy: using '{best_guess}' from full lexicon"
                    )

                # Submit guess and get feedback
                try:
                    guess_result = self.client.submit_guess(best_guess)
                    self.logger.info(
                        msg=f"Guess '{guess_result.guess}' -> {guess_result.to_pattern_string()} "
                        + f"(Correct: {guess_result.is_correct})"
                    )

                    # Update game state with result
                    if self.game_state_manager:
                        self.game_state_manager.add_guess_result(guess_result)

                except Exception as e:
                    self.logger.error(msg=f"API error during guess submission: {e}")
                    raise

            # Game completed - generate final results
            total_game_time: float = time.time() - game_start_time
            final_summary: dict[str, Any] = self._generate_final_summary(
                total_game_time
            )

            return final_summary

        except Exception as e:
            self.logger.error(msg=f"Error during original puzzle solving: {e}")
            raise

    def _generate_daily_final_summary(
        self, total_time: float, daily_game_manager: DailyGameStateManager
    ) -> GameSummary:
        """Generate final game summary for Daily mode."""
        game_summary = daily_game_manager.get_game_summary()

        # Type-safe access to game_summary
        guess_history: list[GuessHistoryItem] = game_summary["guesses"]
        remaining_answers: list[str] = game_summary["possible_answers"]

        # Get lexicon stats in proper format
        lexicon_stats = self.lexicon.get_stats()

        final_summary: GameSummary = {
            "game_result": {
                "solved": daily_game_manager.is_solved(),
                "failed": daily_game_manager.is_failed(),
                "total_turns": len(guess_history),
                "final_answer": (guess_history[-1]["guess"] if guess_history else None),
            },
            "performance_metrics": {
                "total_game_time_seconds": round(number=total_time, ndigits=2),
                "average_time_per_turn": round(
                    number=total_time / max(1, len(guess_history)), ndigits=2
                ),
                "remaining_possibilities": remaining_answers,
            },
            "guess_history": guess_history,
            "lexicon_stats": lexicon_stats,
            "timestamp": time.time(),
        }

        # Log final result
        if daily_game_manager.is_solved():
            self.logger.info(
                f"PUZZLE SOLVED! Answer: {final_summary['game_result']['final_answer']} "
                + f"in {final_summary['game_result']['total_turns']} turns "
                + f"({final_summary['performance_metrics']['total_game_time_seconds']}s)"
            )
        else:
            self.logger.warning(
                f"Puzzle failed after {final_summary['game_result']['total_turns']} turns "
                + f"({final_summary['performance_metrics']['total_game_time_seconds']}s)"
            )

        return final_summary

    def _generate_final_summary(self, total_time: float) -> GameSummary:
        """Generate final game summary."""
        if not self.game_state_manager:
            raise RuntimeError("Game state manager is not initialized")

        game_summary = self.game_state_manager.get_game_summary()

        # Type-safe access to game_summary
        guess_history: list[GuessHistoryItem] = game_summary["guesses"]
        remaining_answers: list[str] = game_summary["possible_answers"]

        # Get lexicon stats in proper format
        lexicon_stats = self.lexicon.get_stats()

        final_summary: GameSummary = {
            "game_result": {
                "solved": self.game_state_manager.is_solved(),
                "failed": self.game_state_manager.is_failed(),
                "total_turns": len(guess_history),
                "final_answer": (guess_history[-1]["guess"] if guess_history else None),
            },
            "performance_metrics": {
                "total_game_time_seconds": round(number=total_time, ndigits=2),
                "average_time_per_turn": round(
                    number=total_time / max(1, len(guess_history)), ndigits=2
                ),
                "remaining_possibilities": remaining_answers,
            },
            "guess_history": guess_history,
            "lexicon_stats": lexicon_stats,
            "timestamp": time.time(),
        }

        # Log final result
        if self.game_state_manager and self.game_state_manager.is_solved():
            self.logger.info(
                f"PUZZLE SOLVED! Answer: {final_summary['game_result']['final_answer']} "
                + f"in {final_summary['game_result']['total_turns']} turns "
                + f"({final_summary['performance_metrics']['total_game_time_seconds']}s)"
            )
        else:
            self.logger.warning(
                f"Puzzle failed after {final_summary['game_result']['total_turns']} turns "
                + f"({final_summary['performance_metrics']['total_game_time_seconds']}s)"
            )

        return final_summary
