"""Rich console display utilities for Wordle bot visualization."""

import time
from datetime import datetime
from typing import Any

from core.domain.models import FeedbackType, GuessResult


class GameDisplay:
    """Handles rich console display for game progress."""

    # Emoji mappings for visual feedback
    FEEDBACK_EMOJIS = {
        FeedbackType.CORRECT: "🟩",  # Green square
        FeedbackType.PRESENT: "🟨",  # Yellow square
        FeedbackType.ABSENT: "⬛",  # Black square
    }

    FEEDBACK_SYMBOLS = {
        FeedbackType.CORRECT: "+",
        FeedbackType.PRESENT: "o",
        FeedbackType.ABSENT: "-",
    }

    def __init__(self, show_detailed: bool = True):
        """Initialize display with options.

        Args:
            show_detailed: Whether to show detailed entropy calculations
        """
        self.show_detailed = show_detailed
        self.game_start_time = None
        self.game_id = None

    def print_header(self):
        """Print game header."""
        print("=" * 70)
        print("🧠 WORDLE BOT - AUTONOMOUS PUZZLE SOLVER")
        print("🎯 Using Shannon Entropy Maximization")
        print("=" * 70)

    def start_new_game(self, game_id: str = None):
        """Start tracking a new game.

        Args:
            game_id: Optional game identifier
        """
        self.game_start_time = time.time()
        self.game_id = game_id or f"game_{int(time.time())}"

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[INFO] {timestamp} - Starting new game...")

        if game_id:
            print(f"[INFO] {timestamp} - New game started with ID: {game_id}")

    def show_guess_submission(
        self,
        turn: int,
        guess: str,
        remaining_count: int = None,
        entropy: float = None,
        calculation_time: float = None,
    ):
        """Display guess submission with details.

        Args:
            turn: Current turn number
            guess: The word being guessed
            remaining_count: Number of remaining possible answers
            entropy: Entropy value of the guess
            calculation_time: Time taken to calculate the guess
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"\n[INFO] {timestamp} - Guess {turn}/6: Submitting word '{guess}'...")

        if self.show_detailed and entropy is not None:
            print(
                f"[DEBUG] {timestamp} - Entropy: {entropy:.3f} bits | "
                f"Calculation time: {calculation_time:.3f}s"
            )

        if remaining_count is not None:
            print(
                f"[DEBUG] {timestamp} - Searching among {remaining_count:,} possible answers"
            )

    def show_feedback(self, guess_result: GuessResult, remaining_count: int):
        """Display feedback with emoji visualization.

        Args:
            guess_result: The guess result with feedback
            remaining_count: Number of remaining possible answers after filtering
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Create emoji feedback
        emoji_feedback = [self.FEEDBACK_EMOJIS[f] for f in guess_result.feedback]
        symbol_feedback = [self.FEEDBACK_SYMBOLS[f] for f in guess_result.feedback]

        print(f"[INFO] {timestamp} - Feedback: [{', '.join(emoji_feedback)}]")
        print(
            f"[INFO] {timestamp} - Pattern: {guess_result.guess} -> {''.join(symbol_feedback)}"
        )
        print(f"[INFO] {timestamp} - Remaining possible words: {remaining_count}")

        # Victory display should be controlled by caller with accurate total guesses

    def show_victory(self, total_guesses: int):
        """Display victory message.

        Args:
            total_guesses: Total number of guesses used
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        game_duration = (
            time.time() - self.game_start_time if self.game_start_time else 0
        )

        print(
            f"\n🎉 [SUCCESS] {timestamp} - Game {self.game_id} won in {total_guesses} guesses!"
        )
        print(f"⏱️  Game completed in {game_duration:.2f} seconds")

        # Performance rating
        if total_guesses <= 3:
            rating = "🏆 EXCELLENT"
        elif total_guesses <= 4:
            rating = "⭐ GOOD"
        elif total_guesses <= 5:
            rating = "👍 AVERAGE"
        else:
            rating = "😅 CLOSE CALL"

        print(f"📊 Performance: {rating}")

    def show_failure(self, total_guesses: int, target_word: str = None):
        """Display failure message.

        Args:
            total_guesses: Total number of guesses used
            target_word: The correct answer (if known)
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        game_duration = (
            time.time() - self.game_start_time if self.game_start_time else 0
        )

        print(
            f"\n💔 [FAILURE] {timestamp} - Game {self.game_id} lost after {total_guesses} guesses"
        )
        if target_word:
            print(f"🎯 The correct word was: '{target_word}'")
        print(f"⏱️  Game duration: {game_duration:.2f} seconds")

    def show_thinking(self, message: str):
        """Show bot thinking process.

        Args:
            message: Thinking process message
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[DEBUG] {timestamp} - 🤔 {message}")

    def show_word_analysis(
        self, word: str, entropy: float, patterns: int, remaining: int
    ):
        """Show detailed word analysis.

        Args:
            word: Word being analyzed
            entropy: Entropy value
            patterns: Number of unique patterns
            remaining: Remaining possible answers
        """
        if not self.show_detailed:
            return

        print(
            f"  📈 {word}: {entropy:.3f} bits | {patterns} patterns | {remaining} remaining"
        )


class BenchmarkDisplay:
    """Handles benchmark results display."""

    def __init__(self):
        self.start_time = None
        self.games_completed = 0
        self.total_games = 0

    def start_benchmark(self, total_games: int):
        """Start benchmark tracking.

        Args:
            total_games: Total number of games to play
        """
        self.start_time = time.time()
        self.total_games = total_games
        self.games_completed = 0

        print("\n" + "=" * 60)
        print(f"🎯 BENCHMARK MODE: Testing {total_games} games")
        print("=" * 60)

    def update_progress(self, completed: int, wins: int, avg_guesses: float):
        """Update benchmark progress.

        Args:
            completed: Games completed so far
            wins: Games won so far
            avg_guesses: Current average guesses for wins
        """
        self.games_completed = completed
        progress_percent = (completed / self.total_games) * 100
        win_rate = (wins / completed) * 100 if completed > 0 else 0

        print(
            f"\r🔄 Progress: {completed}/{self.total_games} ({progress_percent:.1f}%) | "
            f"Win Rate: {win_rate:.1f}% | Avg Guesses: {avg_guesses:.2f}",
            end="",
        )

    def show_final_results(self, results: dict[str, Any]):
        """Display final benchmark results.

        Args:
            results: Benchmark results dictionary
        """
        total_time = time.time() - self.start_time if self.start_time else 0

        print("\n\n" + "=" * 50)
        print("📊 BENCHMARK REPORT")
        print("=" * 50)

        print(f"🎮 Games Played: {results['games_played']}")
        print(f"🏆 Win Rate: {results['win_rate']:.1f}%")
        print(f"📈 Average Guesses (for wins): {results['avg_guesses']:.2f}")
        print(f"⏱️  Total Time: {total_time:.1f}s")
        print(f"⚡ Avg Time per Game: {total_time / results['games_played']:.2f}s")

        print("\n📊 Distribution:")
        for guess_count, count in results["distribution"].items():
            if guess_count == "losses":
                print(f"  💔 Losses: {count}")
            else:
                bar_length = int((count / results["games_played"]) * 30)
                bar = "█" * bar_length + "░" * (30 - bar_length)
                percentage = (count / results["games_played"]) * 100
                print(
                    f"  {guess_count} Guess{'es' if guess_count != 1 else ''}: "
                    f"{count:3d} {bar} {percentage:5.1f}%"
                )

        # Performance assessment
        print("\n🎯 Performance Assessment:")
        if results["win_rate"] >= 98 and results["avg_guesses"] <= 3.8:
            print("  🏆 EXCELLENT: Top-tier performance!")
        elif results["win_rate"] >= 95 and results["avg_guesses"] <= 4.0:
            print("  ⭐ VERY GOOD: Strong performance")
        elif results["win_rate"] >= 90 and results["avg_guesses"] <= 4.5:
            print("  👍 GOOD: Solid performance")
        else:
            print("  🔧 NEEDS IMPROVEMENT: Consider algorithm tuning")
