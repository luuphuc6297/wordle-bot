"""Orchestrator - Main business logic coordinator for the Wordle-solving bot."""

import logging
import time
from typing import Any, TypedDict

from core.domain.models import EntropyCalculation
from core.use_cases.game_state_manager import GameStateManager, GameSummaryDict
from core.use_cases.solver_engine import SolverEngine
from infrastructure.api.game_client import GameClient, WordleAPIError
from infrastructure.data.word_lexicon import WordLexicon
from utils.display import GameDisplay


class GameResult(TypedDict):
    """Type definition for game result."""

    solved: bool
    failed: bool
    total_turns: int
    final_answer: str | None


class PerformanceMetrics(TypedDict):
    """Type definition for performance metrics."""

    total_game_time_seconds: float
    average_time_per_turn: float
    remaining_possibilities: list[str]


class GameSummary(TypedDict):
    """Type definition for game summary."""

    game_result: GameResult
    performance_metrics: PerformanceMetrics
    guess_history: list[dict[str, str | bool]]
    lexicon_stats: dict[str, int]
    timestamp: float


class GuessAnalysis(TypedDict):
    """Type definition for guess analysis."""

    word: str
    entropy: float
    pattern_count: int
    calculation_time: float
    possible_answers_count: int
    information_bits: float
    is_optimal_first_guess: bool


class SimulationResult(TypedDict):
    """Type definition for simulation result."""

    target_answer: str
    solved: bool
    turns_used: int
    simulation_time: float
    final_state: dict[
        str, str | int | float | bool | list[str] | list[dict[str, str | bool]]
    ]


class Orchestrator:
    """Main coordinator that manages the complete game solving process."""

    def __init__(
        self,
        api_base_url: str = "https://wordle.votee.dev:8000",
        solver_time_budget: float = 5.0,
        show_rich_display: bool = True,
        show_detailed: bool = True,
    ) -> None:
        """Initialize the orchestrator.

        Args:
            api_base_url: Base URL for the Wordle API
            solver_time_budget: Time budget for solver calculations in seconds
            show_rich_display: Whether to show rich console display
            show_detailed: Whether to show detailed entropy information
        """
        self.logger: logging.Logger = logging.getLogger(name=__name__)

        # Initialize components
        self.lexicon: WordLexicon = WordLexicon()
        self.game_client: GameClient = GameClient(base_url=api_base_url)
        self.solver_engine: SolverEngine = SolverEngine(
            time_budget_seconds=solver_time_budget
        )
        self.game_state_manager: GameStateManager | None = None

        # Initialize display
        self.show_rich_display: bool = show_rich_display
        self.display: GameDisplay | None = (
            GameDisplay(show_detailed=show_detailed) if show_rich_display else None
        )

        self.logger.info(
            msg=f"Orchestrator initialized with {len(self.lexicon.answers)} possible answers"
        )

    def solve_daily_puzzle(self) -> GameSummary:
        """Solve the daily Wordle puzzle.

        Returns:
            Dictionary containing the game solution results
        """
        self.logger.info(msg="Starting daily puzzle solution")
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
                best_guess: str = self.solver_engine.find_best_guess(
                    current_state.possible_answers, turn=turn_number
                )
                calculation_time = time.time() - turn_start_time

                self.logger.info(
                    msg=f"Selected guess '{best_guess}' in {calculation_time:.2f}s"
                )

                # Submit guess and get feedback
                try:
                    guess_result = self.game_client.submit_guess(best_guess)
                    self.logger.info(
                        msg=f"Guess '{guess_result.guess}' -> {guess_result.to_pattern_string()} "
                        + f"(Correct: {guess_result.is_correct})"
                    )

                    # Update game state with result
                    if self.game_state_manager:
                        self.game_state_manager.add_guess_result(guess_result)

                except WordleAPIError as e:
                    self.logger.error(msg=f"API error during guess submission: {e}")
                    # Could implement fallback logic here
                    raise

            # Game completed - generate final results
            total_game_time: float = time.time() - game_start_time
            final_summary: GameSummary = self._generate_final_summary(total_game_time)

            return final_summary

        except Exception as e:
            self.logger.error(msg=f"Error during puzzle solving: {e}")
            raise
        finally:
            # Cleanup
            self.game_client.close()

    def _initialize_game(self) -> None:
        """Initialize a new game session."""
        try:
            # Start new game via API
            start_response: dict[str, Any] = self.game_client.start_game()
            self.logger.info(msg=f"Game started: {start_response}")

            # Initialize game state manager with all possible answers
            self.game_state_manager = GameStateManager()

            self.logger.info(msg="Game initialization completed")

        except WordleAPIError as e:
            self.logger.error(msg=f"Failed to initialize game: {e}")
            raise

    def _generate_final_summary(self, total_time: float) -> GameSummary:
        """Generate final game summary.

        Args:
            total_time: Total time taken for the entire game

        Returns:
            Comprehensive game summary
        """
        if not self.game_state_manager:
            raise RuntimeError("Game state manager is not initialized")

        game_summary: GameSummaryDict = self.game_state_manager.get_game_summary()

        # Type-safe access to game_summary
        guesses: list[dict[str, str | bool]] = game_summary["guesses"]
        remaining_answers: list[str] = game_summary["possible_answers"]

        final_summary: GameSummary = {
            "game_result": {
                "solved": self.game_state_manager.is_solved(),
                "failed": self.game_state_manager.is_failed(),
                "total_turns": len(guesses),
                "final_answer": (str(guesses[-1]["guess"]) if guesses else None),
            },
            "performance_metrics": {
                "total_game_time_seconds": round(number=total_time, ndigits=2),
                "average_time_per_turn": round(
                    number=total_time / max(1, len(guesses)), ndigits=2
                ),
                "remaining_possibilities": remaining_answers,
            },
            "guess_history": guesses,
            "lexicon_stats": self.lexicon.get_stats(),
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

    def analyze_guess(
        self, guess: str, possible_answers: list[str] | None = None
    ) -> GuessAnalysis:
        """Analyze the entropy and effectiveness of a specific guess.

        Args:
            guess: The word to analyze
            possible_answers: Optional list of possible answers. If None, uses all answers.

        Returns:
            Analysis results including entropy calculation
        """
        if possible_answers is None:
            possible_answers = self.lexicon.answers

        if not self.lexicon.is_valid_guess(guess):
            raise ValueError(f"'{guess}' is not a valid guess word")

        # Calculate detailed entropy
        entropy_calc = self.solver_engine.calculate_detailed_entropy(
            guess, possible_answers
        )

        return {
            "word": guess,
            "entropy": entropy_calc.entropy,
            "pattern_count": entropy_calc.pattern_count,
            "calculation_time": entropy_calc.calculation_time or 0.0,
            "possible_answers_count": len(possible_answers),
            "information_bits": entropy_calc.entropy,
            "is_optimal_first_guess": guess.upper()
            == self.solver_engine.OPTIMAL_FIRST_GUESS,
        }

    def simulate_game(
        self, target_answer: str, game_id: str | None = None
    ) -> SimulationResult:
        """Simulate a game with a known target answer for testing.

        Args:
            target_answer: The target word to solve for
            game_id: Optional game identifier for display

        Returns:
            Simulation results
        """
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
            guess: str = self.solver_engine.find_best_guess(
                possible_answers=current_answers, turn=turn
            )
            calculation_time: float = time.time() - guess_start_time

            # Calculate entropy for display
            entropy: float = 0.0
            if len(current_answers) > 1 and self.display and self.display.show_detailed:
                entropy_calc: EntropyCalculation = (
                    self.solver_engine.calculate_detailed_entropy(
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
            feedback_pattern: str = self.solver_engine.simulate_feedback(
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

        return {
            "target_answer": target_answer,
            "solved": game_manager.is_solved(),
            "turns_used": len(game_manager.get_current_state().guesses),
            "simulation_time": round(simulation_time, 2),
            "final_state": {
                "turn": game_manager.get_game_summary()["turn"],
                "total_guesses": game_manager.get_game_summary()["total_guesses"],
                "remaining_answers": game_manager.get_game_summary()[
                    "remaining_answers"
                ],
                "is_solved": game_manager.get_game_summary()["is_solved"],
                "is_failed": game_manager.get_game_summary()["is_failed"],
                "remaining_turns": game_manager.get_game_summary()["remaining_turns"],
                "guesses": game_manager.get_game_summary()["guesses"],
                "possible_answers": game_manager.get_game_summary()["possible_answers"],
            },
        }
