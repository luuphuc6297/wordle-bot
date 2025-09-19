"""Text formatter for Wordle Bot output."""

from collections.abc import Mapping
from typing import Any

from .base_formatter import BaseFormatter


class TextFormatter(BaseFormatter):
    """Text output formatter."""

    def format(self, result: Mapping[str, Any]) -> str:
        """Format the result as text.

        Args:
            result: The result to format

        Returns:
            Text formatted string
        """
        output_lines = []

        if "answer" in result:
            # Game results
            if result.get("is_solved", False):
                output_lines.append("✅ PUZZLE SOLVED!")
                output_lines.append(f"Answer: {result['answer']}")
                output_lines.append(f"Turns: {result['turns_used']}")
            else:
                output_lines.append(
                    f"❌ Failed to solve in {result['turns_used']} turns"
                )
            output_lines.append(f"Simulation time: {result['simulation_time']:.2f}s")

        elif "entropy" in result:
            # Analysis results
            output_lines.append(f"Word: {result['word']}")
            output_lines.append(f"Entropy: {result['entropy']:.3f} bits")
            output_lines.append(f"Pattern count: {result['pattern_count']}")
            output_lines.append(f"Calculation time: {result['calculation_time']:.4f}s")
            if result.get("is_optimal_first_guess", False):
                output_lines.append("⭐ This is the optimal first guess!")

        elif "games_played" in result:
            # Benchmark results (already displayed by BenchmarkDisplay)
            if "performance_analysis" in result:
                analysis = result["performance_analysis"]
                output_lines.append("\n🔍 Algorithm Analysis:")
                output_lines.append(
                    f"  Grade: {analysis['grade']} ({analysis['performance_level']})"
                )
                output_lines.append(
                    f"  Efficiency Score: {analysis['efficiency_score']:.2f}"
                )
                output_lines.append(f"  Speed Score: {analysis['speed_score']:.2f}")

                if analysis.get("recommendations"):
                    output_lines.append("\n💡 Recommendations:")
                    for rec in analysis["recommendations"]:
                        output_lines.append(f"  • {rec}")

        elif "analysis_type" in result:
            # Analytics results
            analysis_type = result["analysis_type"]
            data = result["results"]

            output_lines.append(
                f"\n🔬 {analysis_type.replace('_', ' ').title()} Analysis"
            )
            output_lines.append("=" * 50)

            if analysis_type == "word_difficulty":
                output_lines.append(f"📊 Analyzed {len(data)} words:")
                for i, word_data in enumerate(data[:10], 1):
                    difficulty = word_data.difficulty_score
                    avg_guesses = word_data.avg_guesses
                    success_rate = word_data.success_rate
                    output_lines.append(
                        f"  {i:2d}. {word_data.word}: {difficulty:.2f} difficulty | {avg_guesses:.1f} avg guesses | {success_rate:.1%} success"
                    )

            elif analysis_type == "position_analysis":
                for pos_data in data:
                    output_lines.append(f"\n📍 Position {pos_data.position}:")
                    output_lines.append(
                        f"  Entropy: {pos_data.entropy_contribution:.2f}"
                    )
                    output_lines.append(
                        f"  Common: {', '.join(pos_data.common_patterns[:3])}"
                    )

            elif analysis_type == "strategy_insights":
                insights = data
                output_lines.append("\n🎯 Position Insights:")
                output_lines.append(
                    f"  Most informative: Position {insights['position_insights']['most_informative_position']}"
                )
                output_lines.append(
                    f"  Least informative: Position {insights['position_insights']['least_informative_position']}"
                )

                output_lines.append("\n📈 Pattern Insights:")
                output_lines.append(
                    f"  Most effective: {insights['pattern_insights']['most_effective_pattern']}"
                )
                output_lines.append(
                    f"  Most common: {insights['pattern_insights']['most_common_pattern']}"
                )

                if insights.get("recommendations"):
                    output_lines.append("\n💡 Strategic Recommendations:")
                    for rec in insights["recommendations"]:
                        output_lines.append(f"  • {rec}")

        return "\n".join(output_lines)

    def save_to_file(self, result: Mapping[str, Any], filename: str) -> None:
        """Save the result to a text file.

        Args:
            result: The result to save
            filename: The filename to save to
        """
        formatted_text = self.format(result)
        with open(filename, "w") as f:
            f.write(formatted_text)
