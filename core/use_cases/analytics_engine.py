"""Advanced analytics engine for Wordle bot performance analysis."""

import statistics
from collections import defaultdict
from dataclasses import dataclass
from logging import Logger
from typing import Any, TypedDict

import numpy as np

from core.domain.models import EntropyCalculation
from core.use_cases.game_state_manager import GameStateManager
from core.use_cases.solver_engine import SolverEngine
from infrastructure.data.word_lexicon import WordLexicon
from utils.logging_config import get_logger


class PositionInsights(TypedDict):
    """Type definition for position insights."""

    most_informative_position: int
    least_informative_position: int
    entropy_by_position: list[float]


class PatternInsights(TypedDict):
    """Type definition for pattern insights."""

    most_effective_pattern: str
    most_common_pattern: str
    pattern_diversity: int


class StrategyInsights(TypedDict):
    """Type definition for strategy insights."""

    position_insights: PositionInsights
    pattern_insights: PatternInsights
    recommendations: list[str]


class GuessInfo(TypedDict):
    """Type definition for guess information."""

    pattern: str
    entropy: float
    remaining_before: int
    remaining_after: int


class GameResult(TypedDict):
    """Type definition for game simulation result."""

    solved: bool
    turns_used: int
    guesses: list[GuessInfo]
    target_word: str


class FeedbackAnalysis(TypedDict):
    """Type definition for feedback pattern analysis."""

    most_common_patterns: list[tuple[str, int]]
    most_effective_patterns: list[tuple[str, dict[str, float | int]]]
    pattern_details: dict[str, dict[str, float | int]]


@dataclass
class WordDifficulty:
    """Word difficulty analysis result."""

    word: str
    avg_guesses: float
    success_rate: float
    entropy_profile: list[float]
    difficulty_score: float


@dataclass
class PositionAnalysis:
    """Letter position frequency analysis."""

    position: int
    letter_frequencies: dict[str, float]
    entropy_contribution: float
    common_patterns: list[str]


class AnalyticsEngine:
    """Advanced analytics for Wordle bot performance and strategy optimization."""

    def __init__(self) -> None:
        self.lexicon: WordLexicon = WordLexicon()
        self.solver: SolverEngine = SolverEngine(time_budget_seconds=1.0)
        self.logger: Logger = get_logger(__name__)

    def analyze_word_difficulty(
        self, words: list[str] | None = None, sample_size: int = 50
    ) -> list[WordDifficulty]:
        """Analyze difficulty of words based on solving performance.

        Args:
            words: Words to analyze (default: random sample)
            sample_size: Number of words to analyze

        Returns:
            List of word difficulty analyses
        """
        if words is None:
            import random

            words = random.sample(
                self.lexicon.answers, min(sample_size, len(self.lexicon.answers))
            )

        difficulties: list[WordDifficulty] = []

        for word in words:
            self.logger.info(f"Analyzing difficulty of: {word}")

            # Run multiple simulations for statistical significance
            game_results: list[int] = []
            entropy_profiles: list[list[float]] = []

            for _ in range(5):  # 5 simulations per word
                result = self._simulate_single_game(word)
                if result["solved"]:
                    game_results.append(result["turns_used"])
                    entropy_profiles.append([g["entropy"] for g in result["guesses"]])

            if game_results:
                avg_guesses = statistics.mean(game_results)
                success_rate = len(game_results) / 5
                avg_entropy_profile = self._average_entropy_profile(entropy_profiles)

                # Calculate difficulty score (higher = more difficult)
                difficulty_score = (
                    (avg_guesses * 0.7)
                    + ((1 - success_rate) * 10)
                    + (avg_entropy_profile[0] * 0.1)
                )

                difficulties.append(
                    WordDifficulty(
                        word=word,
                        avg_guesses=avg_guesses,
                        success_rate=success_rate,
                        entropy_profile=avg_entropy_profile,
                        difficulty_score=difficulty_score,
                    )
                )

        # Sort by difficulty (hardest first)
        return sorted(difficulties, key=lambda x: x.difficulty_score, reverse=True)

    def analyze_position_patterns(self) -> list[PositionAnalysis]:
        """Analyze letter frequency and patterns by position.

        Returns:
            Position-wise analysis of letter patterns
        """
        position_analyses: list[PositionAnalysis] = []

        for pos in range(5):
            letter_counts: dict[str, int] = defaultdict(int)
            total_words: int = len(self.lexicon.answers)

            # Count letter frequencies at each position
            for word in self.lexicon.answers:
                letter_counts[word[pos]] += 1

            # Convert to frequencies
            letter_frequencies = {
                letter: count / total_words for letter, count in letter_counts.items()
            }

            # Calculate entropy contribution of this position
            entropy_contrib = -sum(
                freq * np.log2(freq) for freq in letter_frequencies.values() if freq > 0
            )

            # Find common patterns
            common_patterns = [
                f"{letter} ({freq:.2%})"
                for letter, freq in sorted(
                    letter_frequencies.items(), key=lambda x: x[1], reverse=True
                )[:5]
            ]

            position_analyses.append(
                PositionAnalysis(
                    position=pos + 1,
                    letter_frequencies=letter_frequencies,
                    entropy_contribution=entropy_contrib,
                    common_patterns=common_patterns,
                )
            )

        return position_analyses

    def find_optimal_guess_combinations(
        self, n_guesses: int = 2
    ) -> list[tuple[str, ...]]:
        """Find optimal combinations of first N guesses.

        Args:
            n_guesses: Number of guesses in combination

        Returns:
            Top combinations ranked by average entropy
        """
        if n_guesses != 2:
            raise NotImplementedError("Currently only supports 2-guess combinations")

        # Test combinations of first two guesses
        high_entropy_words = self._get_high_entropy_words(20)  # Top 20 words
        combinations: list[tuple[tuple[str, str], float]] = []

        for first_word in high_entropy_words[:10]:
            for second_word in high_entropy_words:
                if first_word != second_word:
                    avg_entropy = self._calculate_combination_entropy(
                        first_word, second_word
                    )
                    combinations.append(((first_word, second_word), avg_entropy))

        # Sort by average entropy
        combinations.sort(key=lambda x: x[1], reverse=True)
        return [combo[0] for combo in combinations[:10]]

    def analyze_feedback_patterns(self) -> FeedbackAnalysis:
        """Analyze frequency and effectiveness of feedback patterns.

        Returns:
            Comprehensive feedback pattern analysis
        """
        pattern_stats: dict[str, int] = defaultdict(int)
        pattern_effectiveness: dict[str, list[float]] = defaultdict(list)

        # Sample games to analyze patterns
        sample_words: list[str] = self.lexicon.answers[:100]  # First 100 for speed

        for word in sample_words:
            game_result: GameResult = self._simulate_single_game(word)

            for _i, guess_info in enumerate(game_result["guesses"]):
                pattern: str = guess_info["pattern"]
                pattern_stats[pattern] += 1

                # Effectiveness = reduction in possibilities
                remaining_before = guess_info["remaining_before"]
                remaining_after = guess_info["remaining_after"]

                if remaining_before > 0:
                    reduction_ratio = (
                        remaining_before - remaining_after
                    ) / remaining_before
                    pattern_effectiveness[pattern].append(reduction_ratio)

        # Calculate average effectiveness per pattern
        pattern_analysis: dict[str, dict[str, float | int]] = {}
        for pattern, reductions in pattern_effectiveness.items():
            if reductions:
                pattern_analysis[pattern] = {
                    "frequency": pattern_stats[pattern],
                    "avg_effectiveness": statistics.mean(reductions),
                    "total_occurrences": len(reductions),
                }

        return {
            "most_common_patterns": sorted(
                pattern_stats.items(), key=lambda x: x[1], reverse=True
            )[:10],
            "most_effective_patterns": sorted(
                pattern_analysis.items(),
                key=lambda x: x[1]["avg_effectiveness"],
                reverse=True,
            )[:10],
            "pattern_details": pattern_analysis,
        }

    def generate_strategy_insights(self) -> StrategyInsights:
        """Generate high-level strategy insights and recommendations.

        Returns:
            Strategic insights for bot improvement
        """
        # Analyze current performance
        position_analysis: list[PositionAnalysis] = self.analyze_position_patterns()
        feedback_analysis: FeedbackAnalysis = self.analyze_feedback_patterns()

        # Generate insights
        insights: StrategyInsights = {
            "position_insights": {
                "most_informative_position": max(
                    position_analysis, key=lambda x: x.entropy_contribution
                ).position,
                "least_informative_position": min(
                    position_analysis, key=lambda x: x.entropy_contribution
                ).position,
                "entropy_by_position": [
                    p.entropy_contribution for p in position_analysis
                ],
            },
            "pattern_insights": {
                "most_effective_pattern": feedback_analysis["most_effective_patterns"][
                    0
                ][0],
                "most_common_pattern": feedback_analysis["most_common_patterns"][0][0],
                "pattern_diversity": len(feedback_analysis["pattern_details"]),
            },
            "recommendations": self._generate_recommendations(
                position_analysis, feedback_analysis
            ),
        }

        return insights

    def _simulate_single_game(self, target_word: str) -> GameResult:
        """Simulate a single game for analysis."""
        solver: SolverEngine = SolverEngine(
            time_budget_seconds=0.5
        )  # Fast for analysis
        game_manager: GameStateManager = GameStateManager()

        turn = 1
        guesses: list[GuessInfo] = []

        while not game_manager.is_game_over() and turn <= 6:
            current_answers: list[str] = game_manager.get_possible_answers()

            # Get best guess
            best_guess = solver.find_best_guess(current_answers, turn)

            # Calculate entropy
            entropy: float
            if len(current_answers) > 1:
                entropy_calc: EntropyCalculation = solver.calculate_detailed_entropy(
                    best_guess, current_answers
                )
                entropy = entropy_calc.entropy
            else:
                entropy = 0.0

            # Simulate feedback
            feedback_pattern = solver.simulate_feedback(best_guess, target_word)

            from core.domain.models import GuessResult

            guess_result = GuessResult.from_api_response(best_guess, feedback_pattern)

            # Record guess details
            guesses.append(
                {
                    "pattern": feedback_pattern,
                    "entropy": entropy,
                    "remaining_before": len(current_answers),
                    "remaining_after": 0,  # Will be updated after filtering
                }
            )

            # Update state
            game_manager.add_guess_result(guess_result)
            guesses[-1]["remaining_after"] = game_manager.get_remaining_answers_count()

            turn += 1

        return {
            "target_word": target_word,
            "solved": game_manager.is_solved(),
            "turns_used": len(guesses),
            "guesses": guesses,
        }

    def _average_entropy_profile(
        self, entropy_profiles: list[list[float]]
    ) -> list[float]:
        """Average entropy profiles across multiple games."""
        if not entropy_profiles:
            return []

        max_length = max(len(profile) for profile in entropy_profiles)
        averaged: list[float] = []

        for i in range(max_length):
            values = [profile[i] for profile in entropy_profiles if i < len(profile)]
            if values:
                averaged.append(statistics.mean(values))

        return averaged

    def _get_high_entropy_words(self, n: int = 20) -> list[str]:
        """Get top N words by entropy against full answer set."""
        word_entropies: list[tuple[str, float]] = []

        for word in self.lexicon.allowed_guesses[:100]:  # Sample for speed
            try:
                entropy_calc = self.solver.calculate_detailed_entropy(
                    word, self.lexicon.answers
                )
                word_entropies.append((word, entropy_calc.entropy))
            except Exception:
                continue

        word_entropies.sort(key=lambda x: x[1], reverse=True)
        return [word for word, _ in word_entropies[:n]]

    def _calculate_combination_entropy(
        self, first_word: str, second_word: str
    ) -> float:
        """Calculate average entropy for a two-word combination."""
        # Simplified calculation - would need full simulation for accuracy
        try:
            first_entropy = self.solver.calculate_detailed_entropy(
                first_word, self.lexicon.answers
            ).entropy
            # Approximate second word entropy (would need actual filtering)
            second_entropy = (
                self.solver.calculate_detailed_entropy(
                    second_word, self.lexicon.answers
                ).entropy
                * 0.7
            )
            return (first_entropy + second_entropy) / 2
        except Exception:
            return 0.0

    def _generate_recommendations(
        self,
        position_analysis: list[PositionAnalysis],
        feedback_analysis: FeedbackAnalysis,
    ) -> list[str]:
        """Generate strategic recommendations based on analysis."""
        recommendations: list[str] = []

        # Position-based recommendations
        most_informative = max(position_analysis, key=lambda x: x.entropy_contribution)
        recommendations.append(
            f"Focus on position {most_informative.position} optimization - "
            + f"highest entropy contribution ({most_informative.entropy_contribution:.2f})"
        )

        # Pattern-based recommendations
        if feedback_analysis["most_effective_patterns"]:
            best_pattern = feedback_analysis["most_effective_patterns"][0]
            recommendations.append(
                f"Target feedback pattern '{best_pattern[0]}' - "
                + f"average effectiveness: {best_pattern[1]['avg_effectiveness']:.2%}"
            )

        recommendations.append(
            "Consider implementing adaptive first-guess selection based on word difficulty"
        )
        recommendations.append(
            "Implement pattern-based pruning for faster entropy calculations"
        )

        return recommendations

    def analyze_word_difficulty_from_results(
        self, game_results: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Analyze word difficulty from actual game results.

        Args:
            game_results: List of game results with target_word, solved, turns_used, etc.

        Returns:
            List of word difficulty analysis results
        """
        # Group results by target word
        word_stats: dict[str, dict[str, Any]] = {}

        for result in game_results:
            target_word = result.get("target_word", "unknown")
            if target_word not in word_stats:
                word_stats[target_word] = {
                    "word": target_word,
                    "games_played": 0,
                    "games_solved": 0,
                    "total_turns": 0,
                    "total_time": 0.0,
                    "turn_counts": [],
                }

            stats = word_stats[target_word]
            stats["games_played"] += 1
            if result.get("solved", False):
                stats["games_solved"] += 1
            stats["total_turns"] += result.get("turns_used", 0)
            stats["total_time"] += result.get("simulation_time", 0.0)
            stats["turn_counts"].append(result.get("turns_used", 0))

        # Calculate difficulty metrics
        difficulty_results = []
        for word, stats in word_stats.items():
            if stats["games_played"] == 0:
                continue

            success_rate = stats["games_solved"] / stats["games_played"]
            avg_turns = stats["total_turns"] / stats["games_played"]
            avg_time = stats["total_time"] / stats["games_played"]

            # Calculate difficulty score (higher = more difficult)
            # Based on success rate, average turns, and consistency
            turn_variance = (
                np.var(stats["turn_counts"]) if len(stats["turn_counts"]) > 1 else 0
            )
            difficulty_score = (
                (1 - success_rate) * 10 + avg_turns + (turn_variance * 0.1)
            )

            difficulty_results.append(
                {
                    "word": word,
                    "difficulty_score": round(difficulty_score, 2),
                    "success_rate": round(success_rate, 3),
                    "avg_turns": round(avg_turns, 2),
                    "avg_time": round(avg_time, 2),
                    "games_played": stats["games_played"],
                    "turn_variance": round(turn_variance, 2),
                }
            )

        # Sort by difficulty (highest first)
        difficulty_results.sort(key=lambda x: x["difficulty_score"], reverse=True)

        return difficulty_results
