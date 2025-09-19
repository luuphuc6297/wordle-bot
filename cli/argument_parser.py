"""Argument parser for Wordle Bot CLI."""

import argparse
from typing import Any


class ArgumentParser:
    """Handles command line argument parsing for Wordle Bot."""

    def __init__(self) -> None:
        """Initialize the argument parser."""
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create and configure the argument parser.

        Returns:
            Configured argument parser
        """
        parser = argparse.ArgumentParser(
            description="Autonomous Wordle-solving bot using entropy maximization",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python main.py solve                    # Solve today's daily puzzle
  python main.py simulate CRANE          # Simulate solving with CRANE as target
  python main.py analyze SALET           # Analyze entropy of SALET as first guess
  python main.py benchmark --games 50    # Run benchmark with 50 games
  python main.py benchmark --quick       # Quick benchmark (20 games)
  python main.py benchmark --stress      # Stress test with difficult words
  python main.py analytics --analysis-type strategy  # Strategic insights
  python main.py analytics --analysis-type difficulty --sample-size 10  # Word difficulty analysis

  # Online API modes
  python main.py play-random             # Play random game via API
  python main.py play-word --target CRANE # Play specific word via API
  python main.py online-benchmark --api-mode random --games 20  # Online benchmark
  python main.py online-analytics --api-mode daily --analysis-type difficulty  # Online analytics
            """,
        )

        # Positional arguments
        parser.add_argument(
            "command",
            choices=[
                "solve",
                "simulate",
                "analyze",
                "benchmark",
                "analytics",
                "play-random",
                "play-word",
                "online-benchmark",
                "online-analytics",
            ],
            help="Command to execute",
        )

        parser.add_argument(
            "word", nargs="?", help="Word to analyze (for analyze command)"
        )

        # Basic arguments
        parser.add_argument("--target", "-t", help="Target answer for simulation mode")

        parser.add_argument(
            "--answers",
            "-a",
            help="File containing possible answers for analysis (one per line)",
        )

        parser.add_argument(
            "--output-format",
            "-f",
            choices=["json", "text"],
            default="text",
            help="Output format (default: text)",
        )

        parser.add_argument(
            "--time-budget",
            "-b",
            type=float,
            help="Time budget for solver in seconds (default: 5.0)",
        )

        parser.add_argument(
            "--verbose", "-v", action="store_true", help="Enable verbose logging"
        )

        # Benchmark arguments
        parser.add_argument(
            "--games",
            "-g",
            type=int,
            default=100,
            help="Number of games for benchmark mode (default: 100)",
        )

        parser.add_argument(
            "--quick", "-q", action="store_true", help="Run quick benchmark (20 games)"
        )

        parser.add_argument(
            "--stress", action="store_true", help="Run stress test with difficult words"
        )

        parser.add_argument(
            "--no-display", action="store_true", help="Disable rich console display"
        )

        parser.add_argument(
            "--output", "-o", help="Output file for benchmark results (JSON format)"
        )

        # Analytics arguments
        parser.add_argument(
            "--analysis-type",
            choices=["difficulty", "patterns", "positions", "strategy"],
            default="strategy",
            help="Type of analysis to run (default: strategy)",
        )

        parser.add_argument(
            "--sample-size",
            type=int,
            default=20,
            help="Sample size for analysis (default: 20)",
        )

        # Online mode arguments
        parser.add_argument(
            "--api-mode",
            choices=["daily", "random", "word"],
            default="random",
            help="API mode for online commands (default: random)",
        )

        parser.add_argument(
            "--target-words",
            nargs="+",
            help="Specific target words for word mode (space-separated)",
        )

        parser.add_argument("--version", action="version", version="Wordle Bot 1.0.0")

        return parser

    def parse_arguments(self) -> argparse.Namespace:
        """Parse command line arguments.

        Returns:
            Parsed arguments
        """
        return self.parser.parse_args()

    def get_runtime_settings_overrides(
        self, args: argparse.Namespace
    ) -> dict[str, Any]:
        """Extract runtime settings overrides from CLI arguments.

        Args:
            args: Parsed command line arguments

        Returns:
            Dictionary of settings overrides
        """
        overrides: dict[str, Any] = {}
        if args.time_budget:
            overrides["SOLVER_TIME_BUDGET_SECONDS"] = args.time_budget
        if args.verbose:
            overrides["LOG_LEVEL"] = "DEBUG"
        return overrides
