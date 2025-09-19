"""Main entry point for the Wordle-solving bot."""

import argparse
import json
import sys
from collections.abc import Mapping
from typing import Any

from config.settings import Settings, settings
from core.algorithms.analytics_engine import AnalyticsEngine
from core.algorithms.benchmark_engine import BenchmarkEngine
from core.algorithms.orchestrator import Orchestrator
from utils.logging_config import get_logger, setup_logging


def main() -> int:
    """Main application entry point.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Setup logging with default settings first
    setup_logging(settings)
    logger = get_logger(__name__)

    try:
        # Parse command line arguments
        args = parse_arguments()

        # Build runtime settings overrides from CLI flags (immutable)
        overrides: dict[str, object] = {}
        if args.time_budget:
            overrides["SOLVER_TIME_BUDGET_SECONDS"] = args.time_budget
        if args.verbose:
            overrides["LOG_LEVEL"] = "DEBUG"

        runtime_settings = Settings.from_env(overrides=overrides)

        # Reconfigure logging if level changed
        if args.verbose:
            setup_logging(runtime_settings)

        # Initialize orchestrator
        logger.info("Initializing Wordle Bot...")
        orchestrator = Orchestrator(
            api_base_url=runtime_settings.WORDLE_API_BASE_URL,
            solver_time_budget=runtime_settings.SOLVER_TIME_BUDGET_SECONDS,
            show_rich_display=not args.no_display,
            show_detailed=args.verbose,
        )

        # Execute the requested command
        if args.command == "solve":
            result = solve_daily_puzzle(orchestrator)
        elif args.command == "simulate":
            if not args.target:
                logger.error("Target answer required for simulation mode")
                return 1
            result = simulate_game(orchestrator, args.target)
        elif args.command == "analyze":
            if not args.word:
                logger.error("Word required for analyze mode")
                return 1
            result = analyze_guess(orchestrator, args.word, args.answers)
        elif args.command == "benchmark":
            result = run_benchmark(orchestrator, args)
        elif args.command == "analytics":
            result = run_analytics(orchestrator, args)
        elif args.command == "play-random":
            result = orchestrator.play_random_game()
        elif args.command == "play-word":
            if not hasattr(args, "target") or not args.target:
                logger.error("Target answer required for play-word")
                return 1
            result = orchestrator.play_word_target(args.target)
        elif args.command == "online-benchmark":
            result = run_online_benchmark(orchestrator, args)
        elif args.command == "online-analytics":
            result = run_online_analytics(orchestrator, args)
        else:
            logger.error(f"Unknown command: {args.command}")
            return 1

        # Output results
        if hasattr(args, "output") and args.output:
            save_results_to_file(result, args.output)
        else:
            output_results(result, args.output_format)

        return 0

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Application error: {e}")
        if settings.DEBUG_MODE:
            logger.exception("Full error details:")
        return 1


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments
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

    parser.add_argument("word", nargs="?", help="Word to analyze (for analyze command)")

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
        help=f"Time budget for solver in seconds (default: {settings.SOLVER_TIME_BUDGET_SECONDS})",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

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

    args = parser.parse_args()
    return args


def solve_daily_puzzle(orchestrator: Orchestrator) -> Mapping[str, Any]:
    """Solve the daily Wordle puzzle.

    Args:
        orchestrator: The orchestrator instance

    Returns:
        Solution results
    """
    logger = get_logger(__name__)
    logger.info("Starting daily puzzle solution...")

    result = orchestrator.solve_daily_puzzle()

    return result


def simulate_game(orchestrator: Orchestrator, target_answer: str) -> Mapping[str, Any]:
    """Simulate solving a game with known target.

    Args:
        orchestrator: The orchestrator instance
        target_answer: The target word to solve for

    Returns:
        Simulation results
    """
    logger = get_logger(__name__)
    logger.info(f"Simulating game with target: {target_answer}")

    result = orchestrator.simulate_game(target_answer.upper())

    return result


def analyze_guess(
    orchestrator: Orchestrator, word: str, answers_file: str | None = None
) -> Mapping[str, Any]:
    """Analyze the entropy of a specific guess.

    Args:
        orchestrator: The orchestrator instance
        word: The word to analyze
        answers_file: Optional file containing possible answers

    Returns:
        Analysis results
    """
    logger = get_logger(__name__)

    # Load possible answers if file provided
    possible_answers = None
    if answers_file:
        try:
            with open(answers_file) as f:
                possible_answers = [line.strip().upper() for line in f if line.strip()]
            logger.info(
                f"Loaded {len(possible_answers)} possible answers from {answers_file}"
            )
        except Exception as e:
            logger.error(f"Failed to load answers file: {e}")
            raise

    logger.info(f"Analyzing word: {word}")

    result = orchestrator.analyze_guess(word.upper(), possible_answers)

    return result


def run_benchmark(orchestrator: Orchestrator, args) -> dict[str, Any]:
    """Run benchmark tests.

    Args:
        orchestrator: The orchestrator instance
        args: Command line arguments

    Returns:
        Benchmark results
    """
    logger = get_logger(__name__)

    # Create benchmark engine
    benchmark = BenchmarkEngine(
        solver_time_budget=settings.SOLVER_TIME_BUDGET_SECONDS, max_workers=4
    )

    # Run appropriate benchmark based on flags
    if args.quick:
        logger.info("Running quick benchmark...")
        result = benchmark.run_quick_test(20)
    elif args.stress:
        logger.info("Running stress test...")
        result = benchmark.run_stress_test()
    else:
        num_games = args.games
        logger.info(f"Running full benchmark with {num_games} games...")
        result = benchmark.run_benchmark(num_games, show_progress=True)

    # Analyze performance
    analysis = benchmark.analyze_algorithm_performance(result)
    result["performance_analysis"] = analysis

    return result


def run_analytics(orchestrator: Orchestrator, args) -> Mapping[str, Any]:
    """Run advanced analytics.

    Args:
        orchestrator: The orchestrator instance
        args: Command line arguments

    Returns:
        Analytics results
    """
    logger = get_logger(__name__)

    # Create analytics engine
    analytics = AnalyticsEngine()

    logger.info(f"Running {args.analysis_type} analysis...")

    if args.analysis_type == "difficulty":
        result = {
            "analysis_type": "word_difficulty",
            "results": analytics.analyze_word_difficulty(sample_size=args.sample_size),
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


def run_online_benchmark(orchestrator: Orchestrator, args) -> Mapping[str, Any]:
    """Run online benchmark tests.

    Args:
        orchestrator: The orchestrator instance
        args: Parsed command line arguments

    Returns:
        Benchmark results from online APIs
    """
    logger = get_logger(__name__)

    # Get API mode and target words
    api_mode = getattr(args, "api_mode", "random")
    target_words = getattr(args, "target_words", None)

    # Run appropriate benchmark based on flags
    if args.quick:
        logger.info(f"Running quick online benchmark using {api_mode} API...")
        num_games = 20
    elif args.stress:
        logger.info(f"Running stress test using {api_mode} API...")
        num_games = 50
    else:
        num_games = args.games
        logger.info(
            f"Running online benchmark with {num_games} games using {api_mode} API..."
        )

    result = orchestrator.run_online_benchmark(
        num_games=num_games,
        mode=api_mode,
        target_words=target_words,
        show_progress=True,
    )

    return result


def run_online_analytics(orchestrator: Orchestrator, args) -> Mapping[str, Any]:
    """Run online analytics.

    Args:
        orchestrator: The orchestrator instance
        args: Parsed command line arguments

    Returns:
        Analytics results from online APIs
    """
    logger = get_logger(__name__)

    # Get API mode and analysis parameters
    api_mode = getattr(args, "api_mode", "random")
    analysis_type = getattr(args, "analysis_type", "strategy")
    sample_size = getattr(args, "sample_size", 20)

    logger.info(f"Running online {analysis_type} analysis using {api_mode} API...")

    result = orchestrator.run_online_analytics(
        analysis_type=analysis_type, sample_size=sample_size, mode=api_mode
    )

    return result


def save_results_to_file(results: Mapping[str, Any], output_file: str) -> None:
    """Save results to a JSON file.

    Args:
        results: Results dictionary to save
        output_file: Path to output file
    """
    import json

    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results saved to: {output_file}")


def output_results(results: Mapping[str, Any], output_format: str) -> None:
    """Output results in the specified format.

    Args:
        results: Results dictionary to output
        output_format: Format to use ('json' or 'text')
    """
    if output_format == "json":
        print(json.dumps(results, indent=2, default=str))
    else:
        # Text format
        print("=" * 50)
        print("WORDLE BOT RESULTS")
        print("=" * 50)

        if "game_result" in results:
            # Game solution results
            game_result = results["game_result"]
            if game_result["solved"]:
                print("✅ PUZZLE SOLVED!")
                print(f"Answer: {game_result['final_answer']}")
                print(f"Turns: {game_result['total_turns']}")
            else:
                print(f"❌ Puzzle failed after {game_result['total_turns']} turns")

            print("\nPerformance:")
            perf = results["performance_metrics"]
            print(f"  Total time: {perf['total_game_time_seconds']:.2f}s")
            print(f"  Avg per turn: {perf['average_time_per_turn']:.2f}s")

            print("\nGuess history:")
            for i, guess in enumerate(results["guess_history"], 1):
                status = "✅" if guess.get("correct", False) else "⭕"
                print(f"  {i}. {guess['guess']} -> {guess['feedback']} {status}")

        elif "target_answer" in results:
            # Simulation results
            print(f"Target: {results['target_answer']}")
            if results["solved"]:
                print(f"✅ Solved in {results['turns_used']} turns")
            else:
                print(f"❌ Failed to solve in {results['turns_used']} turns")
            print(f"Simulation time: {results['simulation_time']:.2f}s")

        elif "entropy" in results:
            # Analysis results
            print(f"Word: {results['word']}")
            print(f"Entropy: {results['entropy']:.3f} bits")
            print(f"Pattern count: {results['pattern_count']}")
            print(f"Calculation time: {results['calculation_time']:.4f}s")
            if results["is_optimal_first_guess"]:
                print("⭐ This is the optimal first guess!")

        elif "games_played" in results:
            # Benchmark results (already displayed by BenchmarkDisplay)
            if "performance_analysis" in results:
                analysis = results["performance_analysis"]
                print("\n🔍 Algorithm Analysis:")
                print(f"  Grade: {analysis['grade']} ({analysis['performance_level']})")
                print(f"  Efficiency Score: {analysis['efficiency_score']:.2f}")
                print(f"  Speed Score: {analysis['speed_score']:.2f}")

                if analysis["recommendations"]:
                    print("\n💡 Recommendations:")
                    for rec in analysis["recommendations"]:
                        print(f"  • {rec}")

        elif "analysis_type" in results:
            # Analytics results
            analysis_type = results["analysis_type"]
            data = results["results"]

            print(f"\n🔬 {analysis_type.replace('_', ' ').title()} Analysis")
            print("=" * 50)

            if analysis_type == "word_difficulty":
                print(f"📊 Analyzed {len(data)} words:")
                for i, word_data in enumerate(data[:10], 1):
                    difficulty = word_data.difficulty_score
                    avg_guesses = word_data.avg_guesses
                    success_rate = word_data.success_rate
                    print(
                        f"  {i:2d}. {word_data.word}: {difficulty:.2f} difficulty | {avg_guesses:.1f} avg guesses | {success_rate:.1%} success"
                    )

            elif analysis_type == "position_analysis":
                for pos_data in data:
                    print(f"\n📍 Position {pos_data.position}:")
                    print(f"  Entropy: {pos_data.entropy_contribution:.2f}")
                    print(f"  Common: {', '.join(pos_data.common_patterns[:3])}")

            elif analysis_type == "strategy_insights":
                insights = data
                print("\n🎯 Position Insights:")
                print(
                    f"  Most informative: Position {insights['position_insights']['most_informative_position']}"
                )
                print(
                    f"  Least informative: Position {insights['position_insights']['least_informative_position']}"
                )

                print("\n📈 Pattern Insights:")
                print(
                    f"  Most effective: {insights['pattern_insights']['most_effective_pattern']}"
                )
                print(
                    f"  Most common: {insights['pattern_insights']['most_common_pattern']}"
                )

                if insights["recommendations"]:
                    print("\n💡 Strategic Recommendations:")
                    for rec in insights["recommendations"]:
                        print(f"  • {rec}")


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
