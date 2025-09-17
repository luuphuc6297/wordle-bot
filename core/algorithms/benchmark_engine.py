"""Benchmark engine for testing Wordle bot performance across multiple games."""

import random
import statistics
import time
from collections import defaultdict
from typing import Any

from core.algorithms.game_state_manager import GameStateManager
from core.algorithms.solver_engine import SolverEngine
from core.domain.models import GuessResult
from infrastructure.data.word_lexicon import WordLexicon
from utils.display import BenchmarkDisplay
from utils.logging_config import get_logger


class BenchmarkEngine:
    """Engine for running comprehensive benchmarks of the Wordle bot."""

    def __init__(self, solver_time_budget: float = 3.0, max_workers: int = 4):
        """Initialize benchmark engine.

        Args:
            solver_time_budget: Time budget for solver per guess
            max_workers: Maximum parallel workers for benchmark
        """
        self.solver_time_budget = solver_time_budget
        self.max_workers = max_workers
        self.lexicon = WordLexicon()
        self.display = BenchmarkDisplay()
        self.logger = get_logger(__name__)

    def run_benchmark(
        self,
        num_games: int = 100,
        target_words: list[str] | None = None,
        show_progress: bool = True,
    ) -> dict[str, Any]:
        """Run comprehensive benchmark across multiple games.

        Args:
            num_games: Number of games to play
            target_words: Specific words to test (if None, random selection)
            show_progress: Whether to show progress updates

        Returns:
            Comprehensive benchmark results
        """
        self.logger.info(f"Starting benchmark with {num_games} games")

        if show_progress:
            self.display.start_benchmark(num_games)

        # Prepare target words
        if target_words is None:
            all_answers = self.lexicon.answers
            target_words = random.sample(all_answers, min(num_games, len(all_answers)))
        else:
            target_words = target_words[:num_games]

        # Run games
        results = []
        wins = 0
        total_guesses_for_wins = []

        for i, target_word in enumerate(target_words):
            try:
                game_result = self._play_single_game(target_word)
                results.append(game_result)

                if game_result["won"]:
                    wins += 1
                    total_guesses_for_wins.append(game_result["guesses_used"])

                # Update progress
                if show_progress:
                    avg_guesses = (
                        statistics.mean(total_guesses_for_wins)
                        if total_guesses_for_wins
                        else 0
                    )
                    self.display.update_progress(i + 1, wins, avg_guesses)

            except Exception as e:
                self.logger.error(
                    f"Error in game {i + 1} with target '{target_word}': {e}"
                )
                continue

        # Compile final results
        benchmark_results = self._compile_results(results, target_words)

        if show_progress:
            self.display.show_final_results(benchmark_results)

        return benchmark_results

    def _play_single_game(self, target_word: str) -> dict[str, Any]:
        """Play a single game simulation.

        Args:
            target_word: The target word to guess

        Returns:
            Game result dictionary
        """
        game_start_time = time.time()

        # Initialize components for this game
        solver = SolverEngine(time_budget_seconds=self.solver_time_budget)
        game_manager = GameStateManager()

        turn = 1
        guesses = []

        while not game_manager.is_game_over() and turn <= 6:
            turn_start_time = time.time()

            # Get current possible answers
            current_answers = game_manager.get_possible_answers()

            # Calculate best guess
            best_guess = solver.find_best_guess(current_answers, turn)

            # Calculate entropy for analysis
            if len(current_answers) > 1:
                entropy_calc = solver.calculate_detailed_entropy(
                    best_guess, current_answers
                )
                entropy = entropy_calc.entropy
            else:
                entropy = 0.0

            # Simulate feedback
            feedback_pattern = solver._simulate_feedback(best_guess, target_word)
            guess_result = GuessResult.from_api_response(best_guess, feedback_pattern)

            # Update game state
            game_manager.add_guess_result(guess_result)

            turn_time = time.time() - turn_start_time

            # Record guess details
            guesses.append(
                {
                    "guess": best_guess,
                    "pattern": feedback_pattern,
                    "entropy": entropy,
                    "remaining_before": len(current_answers),
                    "remaining_after": game_manager.get_remaining_answers_count(),
                    "turn_time": turn_time,
                    "is_correct": guess_result.is_correct,
                }
            )

            turn += 1

        game_duration = time.time() - game_start_time

        return {
            "target_word": target_word,
            "won": game_manager.is_solved(),
            "guesses_used": len(guesses),
            "guesses": guesses,
            "game_duration": game_duration,
            "final_state": game_manager.get_game_summary(),
        }

    def _compile_results(
        self, results: list[dict[str, Any]], target_words: list[str]
    ) -> dict[str, Any]:
        """Compile benchmark results into summary statistics.

        Args:
            results: List of individual game results
            target_words: List of target words tested

        Returns:
            Compiled benchmark results
        """
        wins = [r for r in results if r["won"]]
        losses = [r for r in results if not r["won"]]

        # Guess distribution
        distribution = defaultdict(int)
        for result in wins:
            distribution[result["guesses_used"]] += 1
        distribution["losses"] = len(losses)

        # Calculate statistics
        win_rate = (len(wins) / len(results)) * 100 if results else 0

        guess_counts_wins = [r["guesses_used"] for r in wins]
        avg_guesses = statistics.mean(guess_counts_wins) if guess_counts_wins else 0
        median_guesses = (
            statistics.median(guess_counts_wins) if guess_counts_wins else 0
        )

        # Timing statistics
        game_durations = [r["game_duration"] for r in results]
        avg_game_time = statistics.mean(game_durations) if game_durations else 0

        # Turn time analysis
        all_turn_times = []
        for result in results:
            all_turn_times.extend([g["turn_time"] for g in result["guesses"]])
        avg_turn_time = statistics.mean(all_turn_times) if all_turn_times else 0

        # Entropy analysis
        all_entropies = []
        for result in results:
            all_entropies.extend(
                [g["entropy"] for g in result["guesses"] if g["entropy"] > 0]
            )
        avg_entropy = statistics.mean(all_entropies) if all_entropies else 0

        # Hardest words (most guesses among wins)
        hardest_wins = sorted(wins, key=lambda x: x["guesses_used"], reverse=True)[:5]

        # Easiest words (fewest guesses among wins)
        easiest_wins = sorted(wins, key=lambda x: x["guesses_used"])[:5]

        return {
            "games_played": len(results),
            "games_won": len(wins),
            "games_lost": len(losses),
            "win_rate": win_rate,
            "avg_guesses": avg_guesses,
            "median_guesses": median_guesses,
            "distribution": dict(distribution),
            "avg_game_time": avg_game_time,
            "avg_turn_time": avg_turn_time,
            "avg_entropy": avg_entropy,
            "hardest_words": [
                (r["target_word"], r["guesses_used"]) for r in hardest_wins
            ],
            "easiest_words": [
                (r["target_word"], r["guesses_used"]) for r in easiest_wins
            ],
            "failed_words": [r["target_word"] for r in losses],
            "solver_time_budget": self.solver_time_budget,
            "target_words": target_words,
        }

    def run_quick_test(self, num_games: int = 20) -> dict[str, Any]:
        """Run a quick benchmark for rapid testing.

        Args:
            num_games: Number of games for quick test

        Returns:
            Quick test results
        """
        print(f"\n🚀 Running quick test with {num_games} games...")
        return self.run_benchmark(num_games, show_progress=True)

    def run_stress_test(self, difficult_words: list[str] = None) -> dict[str, Any]:
        """Run stress test with known difficult words.

        Args:
            difficult_words: List of words known to be difficult

        Returns:
            Stress test results
        """
        if difficult_words is None:
            # Common difficult Wordle words
            difficult_words = [
                "JAZZY",
                "FIZZY",
                "FUZZY",
                "DIZZY",
                "PIZZA",
                "QUEEN",
                "QUILT",
                "QUITE",
                "QUOTE",
                "QUAKE",
                "OXIDE",
                "PROXY",
                "EPOXY",
                "SIXTY",
                "MIXED",
            ]
            # Filter to only include words in our lexicon
            difficult_words = [
                w for w in difficult_words if self.lexicon.is_valid_answer(w)
            ]

        print(
            f"\n💪 Running stress test with {len(difficult_words)} difficult words..."
        )
        return self.run_benchmark(
            len(difficult_words), target_words=difficult_words, show_progress=True
        )

    def analyze_algorithm_performance(self, results: dict[str, Any]) -> dict[str, Any]:
        """Analyze algorithm performance from benchmark results.

        Args:
            results: Benchmark results to analyze

        Returns:
            Performance analysis
        """
        analysis = {}

        # Overall performance grade
        if results["win_rate"] >= 98 and results["avg_guesses"] <= 3.8:
            analysis["grade"] = "A+"
            analysis["performance_level"] = "EXCELLENT"
        elif results["win_rate"] >= 95 and results["avg_guesses"] <= 4.0:
            analysis["grade"] = "A"
            analysis["performance_level"] = "VERY_GOOD"
        elif results["win_rate"] >= 90 and results["avg_guesses"] <= 4.5:
            analysis["grade"] = "B"
            analysis["performance_level"] = "GOOD"
        elif results["win_rate"] >= 80:
            analysis["grade"] = "C"
            analysis["performance_level"] = "AVERAGE"
        else:
            analysis["grade"] = "D"
            analysis["performance_level"] = "POOR"

        # Efficiency metrics
        analysis["efficiency_score"] = (
            (results["win_rate"] / 100) * (6 - results["avg_guesses"]) / 4
        )
        analysis["speed_score"] = max(
            0, 1 - (results["avg_turn_time"] / 10)
        )  # Normalize to 10s max

        # Recommendations
        recommendations = []
        if results["win_rate"] < 95:
            recommendations.append(
                "Consider increasing solver time budget for better accuracy"
            )
        if results["avg_guesses"] > 4.0:
            recommendations.append(
                "Algorithm may benefit from improved entropy calculation"
            )
        if results["avg_turn_time"] > 3.0:
            recommendations.append("Consider optimizing calculation speed")
        if len(results["failed_words"]) > 0:
            recommendations.append(
                f"Review failures: {', '.join(results['failed_words'][:3])}"
            )

        analysis["recommendations"] = recommendations

        return analysis
