"""CLI application for Wordle Bot using Typer."""

import json
import sys
from typing import Optional

import typer
from core.algorithms.analytics_engine import AnalyticsEngine
from core.algorithms.benchmark_engine import BenchmarkEngine
# Import from workspace packages
from core.algorithms.orchestrator import Orchestrator
from shared.config.settings import settings
from shared.utils.logging_config import get_logger, setup_logging

app = typer.Typer(
    name="wordle-bot",
    help="Autonomous Wordle-solving bot using entropy maximization",
    no_args_is_help=True,
)


def version_callback(value: bool):
    """Print version and exit."""
    if value:
        typer.echo("Wordle Bot 1.0.0")
        raise typer.Exit()


@app.callback()
def main(
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging"
    ),
    version: Optional[bool] = typer.Option(
        None, "--version", callback=version_callback, is_eager=True, help="Show version"
    ),
):
    """Main callback to set up global options."""
    if verbose:
        settings.LOG_LEVEL = "DEBUG"
    setup_logging()


@app.command()
def solve(
    time_budget: Optional[float] = typer.Option(
        None, "--time-budget", "-b", help="Time budget for solver in seconds"
    ),
    output_format: str = typer.Option(
        "text", "--output-format", "-f", help="Output format (json/text)"
    ),
    no_display: bool = typer.Option(
        False, "--no-display", help="Disable rich console display"
    ),
    output_file: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file for results"
    ),
):
    """Solve the daily Wordle puzzle."""
    logger = get_logger(__name__)
    logger.info("Starting daily puzzle solution...")

    try:
        solver_time_budget = time_budget or settings.SOLVER_TIME_BUDGET_SECONDS

        orchestrator = Orchestrator(
            api_base_url=settings.WORDLE_API_BASE_URL,
            solver_time_budget=solver_time_budget,
            show_rich_display=not no_display,
            show_detailed=True,
        )

        result = orchestrator.solve_daily_puzzle()

        if output_file:
            save_results_to_file(result, output_file)
        else:
            output_results(result, output_format)

    except Exception as e:
        logger.error(f"Error solving puzzle: {e}")
        sys.exit(1)


@app.command()
def simulate(
    target: str = typer.Argument(..., help="Target answer for simulation"),
    time_budget: Optional[float] = typer.Option(
        None, "--time-budget", "-b", help="Time budget for solver in seconds"
    ),
    output_format: str = typer.Option(
        "text", "--output-format", "-f", help="Output format (json/text)"
    ),
    no_display: bool = typer.Option(
        False, "--no-display", help="Disable rich console display"
    ),
):
    """Simulate solving a game with known target."""
    if len(target) != 5:
        typer.echo("Error: Target must be exactly 5 letters")
        sys.exit(1)

    logger = get_logger(__name__)
    logger.info(f"Simulating game with target: {target}")

    try:
        solver_time_budget = time_budget or settings.SOLVER_TIME_BUDGET_SECONDS

        orchestrator = Orchestrator(
            solver_time_budget=solver_time_budget,
            show_rich_display=not no_display,
            show_detailed=True,
        )

        result = orchestrator.simulate_game(target.upper())
        output_results(result, output_format)

    except Exception as e:
        logger.error(f"Error in simulation: {e}")
        sys.exit(1)


@app.command()
def analyze(
    word: str = typer.Argument(..., help="Word to analyze"),
    answers_file: Optional[str] = typer.Option(
        None, "--answers", "-a", help="File containing possible answers"
    ),
    output_format: str = typer.Option(
        "text", "--output-format", "-f", help="Output format (json/text)"
    ),
):
    """Analyze the entropy of a specific word."""
    if len(word) != 5:
        typer.echo("Error: Word must be exactly 5 letters")
        sys.exit(1)

    logger = get_logger(__name__)
    logger.info(f"Analyzing word: {word}")

    try:
        # Load possible answers if file provided
        possible_answers = None
        if answers_file:
            try:
                with open(answers_file, "r") as f:
                    possible_answers = [
                        line.strip().upper() for line in f if line.strip()
                    ]
                logger.info(
                    f"Loaded {len(possible_answers)} possible answers "
                    f"from {answers_file}"
                )
            except Exception as e:
                typer.echo(f"Error: Failed to load answers file: {e}")
                sys.exit(1)

        orchestrator = Orchestrator(
            show_rich_display=False,
            show_detailed=False,
        )

        result = orchestrator.analyze_guess(word.upper(), possible_answers)
        output_results(result, output_format)

    except Exception as e:
        logger.error(f"Error in analysis: {e}")
        sys.exit(1)


@app.command()
def benchmark(
    games: int = typer.Option(
        100, "--games", "-g", help="Number of games for benchmark"
    ),
    quick: bool = typer.Option(
        False, "--quick", "-q", help="Run quick benchmark (20 games)"
    ),
    stress: bool = typer.Option(
        False, "--stress", help="Run stress test with difficult words"
    ),
    output_file: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file for results"
    ),
):
    """Run benchmark tests."""
    logger = get_logger(__name__)

    # Create benchmark engine
    benchmark_engine = BenchmarkEngine(
        solver_time_budget=settings.SOLVER_TIME_BUDGET_SECONDS, max_workers=4
    )

    try:
        # Run appropriate benchmark
        if quick:
            logger.info("Running quick benchmark...")
            result = benchmark_engine.run_quick_test(20)
        elif stress:
            logger.info("Running stress test...")
            result = benchmark_engine.run_stress_test()
        else:
            logger.info(f"Running full benchmark with {games} games...")
            result = benchmark_engine.run_benchmark(games, show_progress=True)

        # Analyze performance
        analysis = benchmark_engine.analyze_algorithm_performance(result)
        result["performance_analysis"] = analysis

        if output_file:
            save_results_to_file(result, output_file)
        else:
            output_results(result, "text")

    except Exception as e:
        logger.error(f"Error in benchmark: {e}")
        sys.exit(1)


@app.command()
def analytics(
    analysis_type: str = typer.Option(
        "strategy",
        "--analysis-type",
        help="Type of analysis (difficulty/patterns/positions/strategy)",
    ),
    sample_size: int = typer.Option(
        20, "--sample-size", help="Sample size for analysis"
    ),
):
    """Run advanced analytics."""
    logger = get_logger(__name__)

    # Create analytics engine
    analytics_engine = AnalyticsEngine()

    try:
        logger.info(f"Running {analysis_type} analysis...")

        if analysis_type == "difficulty":
            result = {
                "analysis_type": "word_difficulty",
                "results": analytics_engine.analyze_word_difficulty(
                    sample_size=sample_size
                ),
            }
        elif analysis_type == "patterns":
            result = {
                "analysis_type": "feedback_patterns",
                "results": analytics_engine.analyze_feedback_patterns(),
            }
        elif analysis_type == "positions":
            result = {
                "analysis_type": "position_analysis",
                "results": analytics_engine.analyze_position_patterns(),
            }
        else:  # strategy
            result = {
                "analysis_type": "strategy_insights",
                "results": analytics_engine.generate_strategy_insights(),
            }

        output_results(result, "text")

    except Exception as e:
        logger.error(f"Error in analytics: {e}")
        sys.exit(1)


def save_results_to_file(results: dict, output_file: str) -> None:
    """Save results to a JSON file."""
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    typer.echo(f"Results saved to: {output_file}")


def output_results(results: dict, output_format: str) -> None:
    """Output results in the specified format."""
    if output_format == "json":
        typer.echo(json.dumps(results, indent=2, default=str))
    else:
        # Text format - simplified output for CLI
        typer.echo("=" * 50)
        typer.echo("WORDLE BOT RESULTS")
        typer.echo("=" * 50)

        if "game_result" in results:
            # Game solution results
            game_result = results["game_result"]
            if game_result["solved"]:
                typer.echo("✅ PUZZLE SOLVED!")
                typer.echo(f"Answer: {game_result['final_answer']}")
                typer.echo(f"Turns: {game_result['total_turns']}")
            else:
                typer.echo(f"❌ Puzzle failed after {game_result['total_turns']} turns")

        elif "target_answer" in results:
            # Simulation results
            typer.echo(f"Target: {results['target_answer']}")
            if results["solved"]:
                typer.echo(f"✅ Solved in {results['turns_used']} turns")
            else:
                typer.echo(f"❌ Failed to solve in {results['turns_used']} turns")

        elif "entropy" in results:
            # Analysis results
            typer.echo(f"Word: {results['word']}")
            typer.echo(f"Entropy: {results['entropy']:.3f} bits")
            typer.echo(f"Pattern count: {results['pattern_count']}")


if __name__ == "__main__":
    app()
