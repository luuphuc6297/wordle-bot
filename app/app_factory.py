"""Application factory for Wordle Bot."""

import argparse
from collections.abc import Mapping
from typing import Any

from cli import ArgumentParser, CommandRouter
from config.settings import Settings
from core.algorithms.orchestrator import Orchestrator
from formatters import JsonFormatter, TextFormatter
from utils.logging_config import get_logger, setup_logging


class AppFactory:
    """Factory for creating application components."""

    @staticmethod
    def create_app() -> "WordleBotApp":
        """Create a new Wordle Bot application instance.

        Returns:
            Configured application instance
        """
        return WordleBotApp()


class WordleBotApp:
    """Main Wordle Bot application."""

    def __init__(self) -> None:
        """Initialize the application."""
        self.logger = get_logger(__name__)

    def run(self) -> int:
        """Run the application.

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        try:
            # Parse command line arguments
            arg_parser = ArgumentParser()
            args = arg_parser.parse_arguments()

            # Build runtime settings overrides from CLI flags
            overrides = arg_parser.get_runtime_settings_overrides(args)
            runtime_settings = Settings.from_env(overrides=overrides)

            # Setup logging
            setup_logging(runtime_settings)

            # Initialize orchestrator
            self.logger.info("Initializing Wordle Bot...")
            orchestrator = Orchestrator(
                api_base_url=runtime_settings.WORDLE_API_BASE_URL,
                solver_time_budget=runtime_settings.SOLVER_TIME_BUDGET_SECONDS,
                show_rich_display=not args.no_display,
                show_detailed=args.verbose,
            )

            # Route command
            command_router = CommandRouter(orchestrator)
            result = command_router.route_command(args)

            # Output results
            self._output_results(result, args)

            return 0

        except KeyboardInterrupt:
            self.logger.info("Operation cancelled by user")
            return 1
        except Exception as e:
            self.logger.error(f"Application error: {e}")
            from config.settings import settings

            if settings.DEBUG_MODE:
                self.logger.exception("Full error details:")
            return 1

    def _output_results(
        self, result: Mapping[str, Any], args: argparse.Namespace
    ) -> None:
        """Output results in the appropriate format.

        Args:
            result: The result to output
            args: Command line arguments
        """
        if hasattr(args, "output") and args.output:
            self._save_results_to_file(result, args.output, args.output_format)
        else:
            self._print_results(result, args.output_format)

    def _print_results(self, result: Mapping[str, Any], output_format: str) -> None:
        """Print results to console.

        Args:
            result: The result to print
            output_format: The output format (text or json)
        """
        if output_format == "json":
            formatter = JsonFormatter()
        else:
            formatter = TextFormatter()

        print(formatter.format(result))

    def _save_results_to_file(
        self, result: Mapping[str, Any], filename: str, output_format: str
    ) -> None:
        """Save results to file.

        Args:
            result: The result to save
            filename: The filename to save to
            output_format: The output format (text or json)
        """
        if output_format == "json":
            formatter = JsonFormatter()
        else:
            formatter = TextFormatter()

        formatter.save_to_file(result, filename)
