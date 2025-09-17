"""Centralized constants for the Wordle bot.

This module contains all application constants to avoid magic numbers and strings
scattered throughout the codebase.
"""

# Game Configuration
MAX_TURNS = 6
WORD_LENGTH = 5
DEFAULT_TIME_BUDGET = 5.0
OPTIMAL_FIRST_GUESS = "SALET"

# API Configuration
DEFAULT_API_BASE_URL = "https://wordle.votee.dev:8000"
DEFAULT_API_TIMEOUT = 30
DEFAULT_API_RETRY_ATTEMPTS = 3

# Solver Configuration
TIME_BUDGET_BUFFER = 0.8  # Use 80% of time budget to account for overhead
DEFAULT_MAX_WORKERS = 8

# Logging Configuration
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Performance Configuration
ENABLE_PERFORMANCE_METRICS = True

# Development Configuration
DEBUG_MODE = False
SIMULATION_MODE = False


# Feedback Types
class FeedbackType:
    """Constants for feedback types."""

    CORRECT = "+"
    PRESENT = "o"
    ABSENT = "-"


# Display Configuration
DEFAULT_SHOW_RICH_DISPLAY = True
DEFAULT_SHOW_DETAILED = True

# File Paths
DEFAULT_ANSWERS_FILE = "infrastructure/data/answers.txt"
DEFAULT_ALLOWED_FILE = "infrastructure/data/allowed.txt"
