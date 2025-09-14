"""Advanced analytics engine for Wordle bot performance analysis."""

import statistics
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from shared.infrastructure.data.word_lexicon import WordLexicon
from shared.utils.logging_config import get_logger

from .game_state_manager import GameStateManager
from .solver_engine import SolverEngine


@dataclass
class WordDifficulty:
    """Word difficulty analysis result."""

    word: str
    avg_guesses: float
    success_rate: float
    entropy_profile: List[float]
    difficulty_score: float


@dataclass
class PositionAnalysis:
    """Letter position frequency analysis."""

    position: int
    letter_frequencies: Dict[str, float]
    entropy_contribution: float
    common_patterns: List[str]


class AnalyticsEngine:
    """Advanced analytics for Wordle bot performance and strategy optimization."""

    def __init__(self):
        self.lexicon = WordLexicon()
        self.solver = SolverEngine(time_budget_seconds=1.0)
        self.logger = get_logger(__name__)

    def analyze_word_difficulty(
        self, words: Optional[List[str]] = None, sample_size: int = 50
    ) -> List[WordDifficulty]:
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

        difficulties = []

        for word in words:
            self.logger.info(f"Analyzing difficulty of: {word}")

            # Run multiple simulations for statistical significance
            game_results = []
            entropy_profiles = []

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

    def analyze_position_patterns(self) -> List[PositionAnalysis]:
        """Analyze letter frequency and patterns by position.

        Returns:
            Position-wise analysis of letter patterns
        """
        position_analyses = []

        for pos in range(5):
            letter_counts = defaultdict(int)
            total_words = len(self.lexicon.answers)

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
    ) -> List[Tuple[str, ...]]:
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
        combinations = []

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

    def analyze_feedback_patterns(self) -> Dict[str, Any]:
        """Analyze frequency and effectiveness of feedback patterns.

        Returns:
            Comprehensive feedback pattern analysis
        """
        pattern_stats = defaultdict(int)
        pattern_effectiveness = defaultdict(list)

        # Sample games to analyze patterns
        sample_words = self.lexicon.answers[:100]  # First 100 for speed

        for word in sample_words:
            game_result = self._simulate_single_game(word)

            for i, guess_info in enumerate(game_result["guesses"]):
                pattern = guess_info["pattern"]
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
        pattern_analysis = {}
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

    def generate_strategy_insights(self) -> Dict[str, Any]:
        """Generate high-level strategy insights and recommendations.

        Returns:
            Strategic insights for bot improvement
        """
        # Analyze current performance
        position_analysis = self.analyze_position_patterns()
        feedback_analysis = self.analyze_feedback_patterns()

        # Generate insights
        insights = {
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

    def _simulate_single_game(self, target_word: str) -> Dict[str, Any]:
        """Simulate a single game for analysis."""
        solver = SolverEngine(time_budget_seconds=0.5)  # Fast for analysis
        game_manager = GameStateManager()

        turn = 1
        guesses = []

        while not game_manager.is_game_over() and turn <= 6:
            current_answers = game_manager.get_possible_answers()

            # Get best guess
            best_guess = solver.find_best_guess(current_answers, turn)

            # Calculate entropy
            if len(current_answers) > 1:
                entropy_calc = solver.calculate_detailed_entropy(
                    best_guess, current_answers
                )
                entropy = entropy_calc.entropy
            else:
                entropy = 0.0

            # Simulate feedback
            feedback_pattern = solver._simulate_feedback(best_guess, target_word)

            from shared.domain.models import GuessResult

            guess_result = GuessResult.from_api_response(best_guess, feedback_pattern)

            # Record guess details
            guesses.append(
                {
                    "guess": best_guess,
                    "pattern": feedback_pattern,
                    "entropy": entropy,
                    "remaining_before": len(current_answers),
                    "remaining_after": 0,  # Will be updated after filtering
                    "is_correct": guess_result.is_correct,
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
        self, entropy_profiles: List[List[float]]
    ) -> List[float]:
        """Average entropy profiles across multiple games."""
        if not entropy_profiles:
            return []

        max_length = max(len(profile) for profile in entropy_profiles)
        averaged = []

        for i in range(max_length):
            values = [profile[i] for profile in entropy_profiles if i < len(profile)]
            if values:
                averaged.append(statistics.mean(values))

        return averaged

    def _get_high_entropy_words(self, n: int = 20) -> List[str]:
        """Get top N words by entropy against full answer set."""
        word_entropies = []

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
        position_analysis: List[PositionAnalysis],
        feedback_analysis: Dict[str, Any],
    ) -> List[str]:
        """Generate strategic recommendations based on analysis."""
        recommendations = []

        # Position-based recommendations
        most_informative = max(position_analysis, key=lambda x: x.entropy_contribution)
        recommendations.append(
            f"Focus on position {most_informative.position} optimization - "
            f"entropy contribution ({most_informative.entropy_contribution:.2f})"
        )

        # Pattern-based recommendations
        if feedback_analysis["most_effective_patterns"]:
            best_pattern = feedback_analysis["most_effective_patterns"][0]
            recommendations.append(
                f"Target feedback pattern '{best_pattern[0]}' - "
                f"average effectiveness: {best_pattern[1]['avg_effectiveness']:.2%}"
            )

        recommendations.append("Consider adaptive first-guess selection")
        recommendations.append(
            "Implement pattern-based pruning for faster entropy calculations"
        )

        return recommendations
