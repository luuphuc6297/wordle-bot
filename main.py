"""Main entry point for the Wordle-solving bot."""

import sys

from app import AppFactory
from utils.logging_config import get_logger


def main() -> int:
    """Main application entry point.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    logger = get_logger(__name__)

    try:
        app = AppFactory.create_app()
        return app.run()
    except Exception as e:
        logger.error(f"Application error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
