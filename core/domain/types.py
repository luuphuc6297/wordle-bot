"""Shared type definitions for the Wordle bot.

This module centralizes all TypedDict and type definitions to avoid circular imports
and improve code organization.
"""

from typing import TypedDict


class GameResult(TypedDict):
    """Type definition for game result."""

    solved: bool
    failed: bool
    total_turns: int
    final_answer: str | None


class PerformanceMetrics(TypedDict):
    """Type definition for performance metrics."""

    total_game_time_seconds: float
    average_time_per_turn: float
    remaining_possibilities: list[str]


class LexiconStats(TypedDict):
    """Type definition for lexicon statistics."""

    total_answers: int
    total_allowed_guesses: int
    answers_in_allowed: int


class GuessHistoryItem(TypedDict):
    """Type definition for individual guess history item."""

    guess: str
    feedback: str
    correct: bool


class GameSummaryDict(TypedDict):
    """Type definition for game summary dictionary."""

    game_result: GameResult
    performance_metrics: PerformanceMetrics
    guess_history: list[GuessHistoryItem]
    lexicon_stats: LexiconStats
    timestamp: float


class SimulationResult(TypedDict):
    """Type definition for simulation result."""

    game_result: GameResult
    performance_metrics: PerformanceMetrics
    guess_history: list[GuessHistoryItem]
    lexicon_stats: LexiconStats
    timestamp: float


# Alias for backward compatibility
GameSummary = GameSummaryDict
