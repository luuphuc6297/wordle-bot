"""Orchestrator - Main business logic coordinator for the Wordle-solving bot."""

import logging
import time
from typing import Any, TypedDict

from config.settings import Settings
from config.settings import settings as default_settings
from core.algorithms.solver_engine import SolverEngine
from core.algorithms.state_manager import (
    DailyGameStateManager,
    GameStateManager,
)
from core.domain.types import GameSummary, GuessHistoryItem, SimulationResult
from infrastructure.api.game_client import GameClient, WordleAPIError
from infrastructure.data.word_lexicon import WordLexicon
from utils.display import GameDisplay
from utils.logging_config import get_logger

from .modes.daily_handler import DailyHandler
from .modes.offline_handler import OfflineHandler
from .modes.random_handler import RandomHandler
from .modes.word_handler import WordHandler


class GuessAnalysis(TypedDict):
    """Type definition for guess analysis."""

    word: str
    entropy: float
    pattern_count: int
    calculation_time: float
    possible_answers_count: int
    information_bits: float
    is_optimal_first_guess: bool


class Orchestrator:
    """Main coordinator that manages the complete game solving process."""

    def __init__(
        self,
        api_base_url: str = "https://wordle.votee.dev:8000",
        solver_time_budget: float = 5.0,
        show_rich_display: bool = True,
        show_detailed: bool = True,
        app_settings: Settings | None = None,
    ) -> None:
        """Initialize the orchestrator.

        Args:
            api_base_url: Base URL for the Wordle API
            solver_time_budget: Time budget for solver calculations in seconds
            show_rich_display: Whether to show rich console display
            show_detailed: Whether to show detailed entropy information
        """
        self.logger: logging.Logger = get_logger(__name__)

        # Initialize components
        self.settings: Settings = app_settings or default_settings
        self.lexicon: WordLexicon = WordLexicon()
        self.game_client: GameClient = GameClient(
            base_url=api_base_url, app_settings=self.settings
        )
        self.solver_engine: SolverEngine = SolverEngine(
            time_budget_seconds=solver_time_budget,
            app_settings=self.settings,
        )
        self.game_state_manager: GameStateManager | None = None

        # Initialize display
        self.show_rich_display: bool = show_rich_display
        self.display: GameDisplay | None = (
            GameDisplay(show_detailed=show_detailed) if show_rich_display else None
        )

        # Initialize mode handlers
        self._handlers = {
            "daily": DailyHandler(
                self.game_client,
                self.solver_engine,
                self.lexicon,
                self.display,
                self.settings,
            ),
            "random": RandomHandler(
                self.game_client,
                self.solver_engine,
                self.lexicon,
                self.display,
                self.settings,
            ),
            "word": WordHandler(
                self.game_client,
                self.solver_engine,
                self.lexicon,
                self.display,
                self.settings,
            ),
            "offline": OfflineHandler(
                self.solver_engine, self.lexicon, self.display, self.settings
            ),
        }

        self.logger.info(
            msg=f"Orchestrator initialized with {len(self.lexicon.answers)} possible answers"
        )

    def solve_daily_puzzle(self) -> GameSummary:
        """Solve the daily Wordle puzzle using improved strategy.

        STRATEGY:
        1. Call Daily API to get feedback and narrow down possible answers
        2. Find the actual target word by testing possible answers
        3. Use Word-target API to continue with entropy algorithm
        4. Continue until solved or max turns reached
        """
        return self._handlers["daily"].run_game()

    def _generate_daily_final_summary(
        self, total_time: float, daily_game_manager: DailyGameStateManager
    ) -> GameSummary:
        """Generate final game summary for Daily mode.

        Args:
            total_time: Total time taken for the entire game
            daily_game_manager: The daily game state manager

        Returns:
            Comprehensive game summary
        """
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
            "lexicon_stats": {
                "total_answers": lexicon_stats["total_answers"],
                "total_allowed_guesses": lexicon_stats["total_allowed_guesses"],
                "answers_in_allowed": lexicon_stats["answers_in_allowed"],
            },
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

    def _solve_daily_original(self) -> GameSummary:
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
                best_guess: str = self.solver_engine.find_best_guess(
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
                    best_guess = self.solver_engine.find_best_guess(
                        self.lexicon.get_all_answers(), turn=turn_number
                    )
                    self.logger.info(
                        msg=f"Fallback strategy: using '{best_guess}' from full lexicon"
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
                    raise

            # Game completed - generate final results
            total_game_time: float = time.time() - game_start_time
            final_summary: GameSummary = self._generate_final_summary(total_game_time)

            return final_summary

        except Exception as e:
            self.logger.error(msg=f"Error during original puzzle solving: {e}")
            raise

    def _initialize_game(self) -> None:
        """Initialize a new game session."""
        try:
            # Initialize game state manager with all possible answers
            self.game_state_manager = GameStateManager(app_settings=self.settings)

            self.logger.info(msg="Game initialization completed (daily mode)")

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
            "lexicon_stats": {
                "total_answers": lexicon_stats["total_answers"],
                "total_allowed_guesses": lexicon_stats["total_allowed_guesses"],
                "answers_in_allowed": lexicon_stats["answers_in_allowed"],
            },
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

    def play_random_game(self) -> SimulationResult:
        """Play a game using the random API mode (/random).

        STRATEGY:
        1. Call Random API to get a random target word
        2. Use our entropy algorithm to solve that specific target word
        3. Continue until solved or max turns reached
        """
        return self._handlers["random"].run_game()

    def play_word_target(self, target_answer: str) -> SimulationResult:
        """Play a game against a specific target using /word/{target}."""
        return self._handlers["word"].run_game(target_answer)

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
        return self._handlers["offline"].run_game(target_answer, game_id)

    def run_online_benchmark(
        self,
        num_games: int = 100,
        mode: str = "random",
        target_words: list[str] | None = None,
        show_progress: bool = True,
    ) -> dict[str, Any]:
        """Run benchmark using online APIs.

        Args:
            num_games: Number of games to play
            mode: API mode - "daily", "random", or "word"
            target_words: Specific words for "word" mode (if None, random selection)
            show_progress: Whether to show progress updates

        Returns:
            Benchmark results with online API data
        """
        from core.algorithms.benchmark_engine import BenchmarkEngine

        self.logger.info(
            f"Starting online benchmark with {num_games} games using {mode} API"
        )

        # Create benchmark engine with online orchestrator
        benchmark = BenchmarkEngine(
            solver_time_budget=self.settings.SOLVER_TIME_BUDGET_SECONDS, max_workers=4
        )

        # Override the benchmark's game playing logic to use online APIs
        def online_play_game(target_word: str) -> dict[str, Any]:
            """Play a single game using online API."""
            try:
                if mode == "daily":
                    result = self.solve_daily_puzzle()
                elif mode == "random":
                    result = self.play_random_game()
                elif mode == "word":
                    result = self.play_word_target(target_word)
                else:
                    raise ValueError(f"Invalid mode: {mode}")

                # Convert to benchmark format per mode/result shape
                if (
                    mode == "daily"
                    and isinstance(result, dict)
                    and "game_result" in result
                ):
                    game_result = result["game_result"]
                    perf = result.get("performance_metrics", {})
                    won = bool(game_result.get("solved", False))
                    turns = int(game_result.get("total_turns", 0))
                    return {
                        "target_word": "daily",
                        "won": won,
                        "guesses_used": turns,
                        "guesses": [],
                        "game_duration": float(
                            perf.get("total_game_time_seconds", 0.0)
                        ),
                        "final_state": result,
                        "success": won,
                    }
                else:
                    return {
                        "target_word": result.get("target_answer", "unknown"),
                        "won": result.get("solved", False),
                        "guesses_used": result.get("turns_used", 0),
                        "guesses": [],
                        "game_duration": result.get("simulation_time", 0.0),
                        "final_state": result.get("final_state", {}),
                        "success": result.get("solved", False),
                    }
            except Exception as e:
                self.logger.error(f"Error in online game: {e}")
                return {
                    "target_word": target_word,
                    "won": False,
                    "guesses_used": 6,
                    "guesses": [],
                    "game_duration": 0.0,
                    "final_state": {},
                    "success": False,
                    "error": str(e),
                }

        # Replace the game playing method
        benchmark._play_single_game = online_play_game

        # Run benchmark
        if mode == "word" and target_words:
            result = benchmark.run_benchmark(
                num_games=len(target_words),
                target_words=target_words,
                show_progress=show_progress,
            )
        else:
            result = benchmark.run_benchmark(
                num_games=num_games,
                target_words=target_words,
                show_progress=show_progress,
            )

        # Add online-specific metadata
        result["api_mode"] = mode
        result["online_benchmark"] = True

        return result

    def run_online_analytics(
        self,
        analysis_type: str = "strategy",
        sample_size: int = 50,
        mode: str = "random",
    ) -> dict[str, Any]:
        """Run analytics using online APIs.

        Args:
            analysis_type: Type of analysis - "strategy", "difficulty", "patterns", "positions"
            sample_size: Number of games to sample for analysis
            mode: API mode - "daily", "random", or "word"

        Returns:
            Analytics results with online API data
        """
        from core.algorithms.analytics_engine import AnalyticsEngine

        self.logger.info(
            f"Running online {analysis_type} analysis with {sample_size} samples using {mode} API"
        )

        # Create analytics engine
        analytics = AnalyticsEngine()

        # For online analytics, we need to collect data from actual API games
        if analysis_type == "difficulty":
            # Run sample games to collect difficulty data
            sample_results = []
            for i in range(min(sample_size, 20)):  # Limit to avoid too many API calls
                try:
                    if mode == "daily":
                        result = self.solve_daily_puzzle()
                    elif mode == "random":
                        result = self.play_random_game()
                    else:
                        # For word mode, use random words from lexicon
                        word: str = self.lexicon.get_random_answer()
                        result = self.play_word_target(word)

                    sample_results.append(
                        {
                            "target_word": result.get("target_answer", "unknown"),
                            "solved": result.get("solved", False),
                            "turns_used": result.get("turns_used", 0),
                            "simulation_time": result.get("simulation_time", 0.0),
                        }
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to collect sample {i}: {e}")
                    continue

            # Analyze the collected data
            result = {
                "analysis_type": "online_word_difficulty",
                "api_mode": mode,
                "sample_size": len(sample_results),
                "results": analytics.analyze_word_difficulty_from_results(
                    sample_results
                ),
            }
        else:
            # For other analysis types, use the existing methods but mark as online
            if analysis_type == "patterns":
                analysis_result = analytics.analyze_feedback_patterns()
            elif analysis_type == "positions":
                analysis_result = analytics.analyze_position_patterns()
            else:  # strategy
                analysis_result = analytics.generate_strategy_insights()

            result = {
                "analysis_type": f"online_{analysis_type}",
                "api_mode": mode,
                "results": analysis_result,
            }

        return result


# Internal Handler Classes have been moved to separate files in modes/
