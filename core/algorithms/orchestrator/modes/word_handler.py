"""Word target game mode handler.

Handles the word target mode (/word/{target}) gameplay logic.
"""

import time

from config.settings import Settings
from core.algorithms.solver_engine import SolverEngine
from core.algorithms.state_manager import ApiGameStateManager
from core.domain.types import SimulationResult
from infrastructure.api.game_client import GameClient
from infrastructure.data.word_lexicon import WordLexicon
from utils.display import GameDisplay

from .base_handler import BaseGameHandler


class WordHandler(BaseGameHandler):
    """Handler for word target game mode."""

    def __init__(
        self,
        client: GameClient,
        solver: SolverEngine,
        lexicon: WordLexicon,
        display: GameDisplay | None,
        settings: Settings,
    ) -> None:
        super().__init__(solver, lexicon, display, settings)
        self.client = client

    def run_game(self, target_answer: str) -> SimulationResult:
        """Play a game against a specific target using /word/{target}."""
        if self.display:
            self.display.print_header()
            self.display.start_new_game(f"word_{target_answer}")

        game_manager = ApiGameStateManager()
        start = time.time()
        turn = 1

        while not game_manager.is_game_over() and turn <= 6:
            current_answers = game_manager.get_possible_answers()
            guess = self.solver.find_best_guess(current_answers, turn)
            guess_result = self.client.submit_word_target_guess(target_answer, guess)
            game_manager.add_guess_result(guess_result)
            if self.display:
                self.display.show_feedback(
                    guess_result, game_manager.get_remaining_answers_count()
                )
            turn += 1

        summary = game_manager.get_game_summary()
        solved = game_manager.is_solved()
        turns_used = len(game_manager.get_current_state().guesses)

        return {
            "game_result": {
                "solved": solved,
                "failed": game_manager.is_failed(),
                "total_turns": turns_used,
                "final_answer": target_answer if solved else None,
            },
            "performance_metrics": {
                "total_game_time_seconds": round(time.time() - start, 2),
                "average_time_per_turn": round(
                    (time.time() - start) / max(1, turns_used), 2
                ),
                "remaining_possibilities": summary["possible_answers"],
            },
            "guess_history": summary["guesses"],
            "lexicon_stats": self.lexicon.get_stats(),
            "timestamp": time.time(),
        }
