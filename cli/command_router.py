"""Command router for Wordle Bot CLI."""

import argparse
from collections.abc import Mapping
from typing import Any

from core.algorithms.orchestrator import Orchestrator
from utils.logging_config import get_logger


class CommandRouter:
    """Routes commands to appropriate handlers."""

    def __init__(self, orchestrator: Orchestrator) -> None:
        """Initialize command router.

        Args:
            orchestrator: The orchestrator instance
        """
        self.orchestrator = orchestrator
        self.logger = get_logger(__name__)

    def route_command(self, args: argparse.Namespace) -> Mapping[str, Any]:
        """Route command to appropriate handler.

        Args:
            args: Parsed command line arguments

        Returns:
            Command execution results

        Raises:
            ValueError: If command is not recognized
        """
        command = args.command

        if command == "solve":
            return self._handle_solve()
        elif command == "simulate":
            return self._handle_simulate(args)
        elif command == "analyze":
            return self._handle_analyze(args)
        elif command == "benchmark":
            return self._handle_benchmark(args)
        elif command == "analytics":
            return self._handle_analytics(args)
        elif command == "play-random":
            return self._handle_play_random()
        elif command == "play-word":
            return self._handle_play_word(args)
        elif command == "online-benchmark":
            return self._handle_online_benchmark(args)
        elif command == "online-analytics":
            return self._handle_online_analytics(args)
        else:
            raise ValueError(f"Unknown command: {command}")

    def _handle_solve(self) -> Mapping[str, Any]:
        """Handle solve command.

        Returns:
            Solution results
        """
        self.logger.info("Starting daily puzzle solution...")
        return self.orchestrator.solve_daily_puzzle()

    def _handle_simulate(self, args: argparse.Namespace) -> Mapping[str, Any]:
        """Handle simulate command.

        Args:
            args: Command line arguments

        Returns:
            Simulation results

        Raises:
            ValueError: If target is not provided
        """
        if not args.target:
            raise ValueError("Target answer required for simulation mode")

        self.logger.info(f"Simulating game with target: {args.target}")
        return self.orchestrator.simulate_game(args.target.upper())

    def _handle_analyze(self, args: argparse.Namespace) -> Mapping[str, Any]:
        """Handle analyze command.

        Args:
            args: Command line arguments

        Returns:
            Analysis results

        Raises:
            ValueError: If word is not provided
        """
        if not args.word:
            raise ValueError("Word required for analyze mode")

        # Load possible answers if file provided
        possible_answers = None
        if args.answers:
            try:
                with open(args.answers) as f:
                    possible_answers = [
                        line.strip().upper() for line in f if line.strip()
                    ]
                self.logger.info(
                    f"Loaded {len(possible_answers)} possible answers from {args.answers}"
                )
            except Exception as e:
                self.logger.error(f"Failed to load answers file: {e}")
                raise

        self.logger.info(f"Analyzing word: {args.word}")
        return self.orchestrator.analyze_guess(args.word.upper(), possible_answers)

    def _handle_benchmark(self, args: argparse.Namespace) -> dict[str, Any]:
        """Handle benchmark command.

        Args:
            args: Command line arguments

        Returns:
            Benchmark results
        """
        from config.settings import settings
        from core.algorithms.benchmark_engine import BenchmarkEngine

        # Create benchmark engine
        benchmark = BenchmarkEngine(
            solver_time_budget=settings.SOLVER_TIME_BUDGET_SECONDS, max_workers=4
        )

        # Run appropriate benchmark based on flags
        if args.quick:
            self.logger.info("Running quick benchmark...")
            result = benchmark.run_quick_test(20)
        elif args.stress:
            self.logger.info("Running stress test...")
            result = benchmark.run_stress_test()
        else:
            num_games = args.games
            self.logger.info(f"Running full benchmark with {num_games} games...")
            result = benchmark.run_benchmark(num_games, show_progress=True)

        # Analyze performance
        analysis = benchmark.analyze_algorithm_performance(result)
        result["performance_analysis"] = analysis

        return result

    def _handle_analytics(self, args: argparse.Namespace) -> Mapping[str, Any]:
        """Handle analytics command.

        Args:
            args: Command line arguments

        Returns:
            Analytics results
        """
        from core.algorithms.analytics_engine import AnalyticsEngine

        # Create analytics engine
        analytics = AnalyticsEngine()

        self.logger.info(f"Running {args.analysis_type} analysis...")

        if args.analysis_type == "difficulty":
            result = {
                "analysis_type": "word_difficulty",
                "results": analytics.analyze_word_difficulty(
                    sample_size=args.sample_size
                ),
            }
        elif args.analysis_type == "patterns":
            result = {
                "analysis_type": "feedback_patterns",
                "results": analytics.analyze_feedback_patterns(),
            }
        elif args.analysis_type == "positions":
            result = {
                "analysis_type": "position_analysis",
                "results": analytics.analyze_position_patterns(),
            }
        else:  # strategy
            result = {
                "analysis_type": "strategy_insights",
                "results": analytics.generate_strategy_insights(),
            }

        return result

    def _handle_play_random(self) -> Mapping[str, Any]:
        """Handle play-random command.

        Returns:
            Random game results
        """
        return self.orchestrator.play_random_game()

    def _handle_play_word(self, args: argparse.Namespace) -> Mapping[str, Any]:
        """Handle play-word command.

        Args:
            args: Command line arguments

        Returns:
            Word game results

        Raises:
            ValueError: If target is not provided
        """
        if not hasattr(args, "target") or not args.target:
            raise ValueError("Target answer required for play-word")

        return self.orchestrator.play_word_target(args.target)

    def _handle_online_benchmark(self, args: argparse.Namespace) -> Mapping[str, Any]:
        """Handle online-benchmark command.

        Args:
            args: Command line arguments

        Returns:
            Online benchmark results
        """
        # Get API mode and target words
        api_mode = getattr(args, "api_mode", "random")
        target_words = getattr(args, "target_words", None)

        # Run appropriate benchmark based on flags
        if args.quick:
            self.logger.info(f"Running quick online benchmark using {api_mode} API...")
            num_games = 20
        else:
            num_games = args.games
            self.logger.info(
                f"Running online benchmark with {num_games} games using {api_mode} API..."
            )

        return self.orchestrator.run_online_benchmark(
            num_games=num_games, mode=api_mode, target_words=target_words
        )

    def _handle_online_analytics(self, args: argparse.Namespace) -> Mapping[str, Any]:
        """Handle online-analytics command.

        Args:
            args: Command line arguments

        Returns:
            Online analytics results
        """
        api_mode = getattr(args, "api_mode", "random")
        analysis_type = getattr(args, "analysis_type", "strategy")
        sample_size = getattr(args, "sample_size", 20)

        self.logger.info(f"Running online analytics using {api_mode} API...")

        return self.orchestrator.run_online_analytics(
            mode=api_mode, analysis_type=analysis_type, sample_size=sample_size
        )
