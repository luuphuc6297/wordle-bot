"""Word target game mode handler.

Handles the word target mode (/word/{target}) gameplay logic.
"""

import time
from typing import Any

from config.settings import Settings
from core.algorithms.solver_engine import SolverEngine
from core.algorithms.state_manager import GameStateManager
from infrastructure.api.game_client import GameClient
from infrastructure.data.word_lexicon import WordLexicon
from utils.display import GameDisplay
from utils.logging_config import get_logger


class WordHandler:
    """Handler for word target game mode."""

    def __init__(
        self,
        client: GameClient,
        solver: SolverEngine,
        lexicon: WordLexicon,
        display: GameDisplay | None,
        settings: Settings,
    ) -> None:
        self.client = client
        self.solver = solver
        self.lexicon = lexicon
        self.display = display
        self.settings = settings
        self.logger = get_logger(__name__)

    def run_game(self, target_answer: str) -> dict[str, Any]:
        """Play a game against a specific target using /word/{target}."""
        if self.display:
            self.display.print_header()
            self.display.start_new_game(f"word_{target_answer}")

        game_manager = GameStateManager()
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
        return {
            "target_answer": target_answer,
            "solved": game_manager.is_solved(),
            "turns_used": len(game_manager.get_current_state().guesses),
            "simulation_time": round(time.time() - start, 2),
            "final_state": {
                "turn": summary["turn"],
                "total_guesses": summary["total_guesses"],
                "remaining_answers": summary["remaining_answers"],
                "is_solved": summary["is_solved"],
                "is_failed": summary["is_failed"],
                "remaining_turns": summary["remaining_turns"],
                "guesses": summary["guesses"],
                "possible_answers": summary["possible_answers"],
            },
        }
