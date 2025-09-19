"""Benchmark service for running benchmarks and analytics."""

from typing import TYPE_CHECKING, Any

from core.algorithms.benchmark_engine import BenchmarkEngine

if TYPE_CHECKING:
    from core.algorithms.orchestrator import Orchestrator
from utils.logging_config import get_logger


class BenchmarkService:
    """Service for running benchmarks and analytics."""

    def __init__(self, orchestrator: "Orchestrator"):
        """Initialize the benchmark service.

        Args:
            orchestrator: The orchestrator instance
        """
        self.orchestrator = orchestrator
        self.logger = get_logger(__name__)

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
        # Validate daily mode benchmark
        if mode == "daily" and num_games > 1:
            self.logger.warning(
                f"Daily mode benchmark with {num_games} games is not meaningful. "
                "Daily puzzle only has one word per day. Limiting to 1 game."
            )
            num_games = 1

        self.logger.info(
            f"Starting online benchmark with {num_games} games using {mode} API"
        )

        # Create benchmark engine with online orchestrator
        benchmark = BenchmarkEngine(
            solver_time_budget=self.orchestrator.settings.SOLVER_TIME_BUDGET_SECONDS,
            max_workers=4,
        )

        # Override the benchmark's game playing logic to use online APIs
        def online_play_game(target_word: str) -> dict[str, Any]:
            """Play a single game using online API."""
            try:
                if mode == "daily":
                    result = self.orchestrator.solve_daily_puzzle()
                elif mode == "random":
                    result = self.orchestrator.play_random_game()
                elif mode == "word":
                    result = self.orchestrator.play_word_target(target_word)
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
                    # Handle SimulationResult format
                    game_result = result.get("game_result", {})
                    performance_metrics = result.get("performance_metrics", {})
                    return {
                        "target_word": game_result.get("final_answer", "unknown"),
                        "won": game_result.get("solved", False),
                        "guesses_used": game_result.get("total_turns", 0),
                        "guesses": [],
                        "game_duration": performance_metrics.get(
                            "total_game_time_seconds", 0.0
                        ),
                        "final_state": result,
                        "success": game_result.get("solved", False),
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
                        result = self.orchestrator.solve_daily_puzzle()
                    elif mode == "random":
                        result = self.orchestrator.play_random_game()
                    else:
                        # For word mode, use random words from lexicon
                        word: str = self.orchestrator.lexicon.get_random_answer()
                        result = self.orchestrator.play_word_target(word)

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
