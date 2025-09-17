"""Filtering strategies for narrowing possible Wordle answers.

This module defines filtering strategies that can be plugged into
GameState managers without duplicating structure.
"""

from __future__ import annotations

from typing import Protocol

from core.algorithms.solver_engine import SolverEngine
from core.domain.constants import WORD_LENGTH
from core.domain.models import FeedbackType, GuessResult


class FilterStrategy(Protocol):
    """Protocol for filtering strategies used by GameState managers."""

    def filter_answers(
        self, guess_result: GuessResult, candidates: list[str]
    ) -> list[str]:
        """Return subset of candidates consistent with the given guess result."""
        ...


class StandardFilterStrategy:
    """Standard Wordle filtering using simulated feedback equality.

    This matches the classic two-pass Wordle rules and is ideal for offline
    solving and /word/{target} modes where feedback is consistent.
    """

    def __init__(self, solver: SolverEngine) -> None:
        self._solver = solver

    def filter_answers(
        self, guess_result: GuessResult, candidates: list[str]
    ) -> list[str]:
        expected = guess_result.to_pattern_string()
        guess = guess_result.guess
        filtered: list[str] = []
        for answer in candidates:
            if self._solver.simulate_feedback(guess=guess, answer=answer) == expected:
                filtered.append(answer)
        return filtered


class DailyApiFilterStrategy:
    """Permissive filtering tailored to the Daily API feedback behavior.

    Empirically, the Daily API may treat duplicates/ABSENT differently from
    strict Wordle rules. This strategy enforces:
    - CORRECT: candidate[i] == guess[i]
    - PRESENT: letter present somewhere, and not at i
    - ABSENT:
        * If the same letter is CORRECT/PRESENT elsewhere in this feedback,
          only ban this position (candidate[i] != letter)
        * Otherwise, ban globally (letter not in candidate)
    """

    def filter_answers(
        self, guess_result: GuessResult, candidates: list[str]
    ) -> list[str]:
        guess = guess_result.guess.upper()
        fb = guess_result.feedback
        out: list[str] = []

        # Pre-compute letter roles for this feedback
        letter_has_non_absent: dict[str, bool] = {}
        for g_ch, f_type in zip(guess, fb, strict=False):
            if f_type != FeedbackType.ABSENT:
                letter_has_non_absent[g_ch] = True
            else:
                letter_has_non_absent.setdefault(g_ch, False)

        for cand in candidates:
            cand_u = cand.upper()
            if len(cand_u) != WORD_LENGTH:
                continue

            # Pass 1: enforce CORRECT
            ok = True
            for i, (g_ch, f_type) in enumerate(zip(guess, fb, strict=False)):
                if f_type == FeedbackType.CORRECT and cand_u[i] != g_ch:
                    ok = False
                    break
            if not ok:
                continue

            # Pass 2: enforce PRESENT/ABSENT with permissive rules
            for i, (g_ch, f_type) in enumerate(zip(guess, fb, strict=False)):
                if f_type == FeedbackType.PRESENT:
                    if cand_u[i] == g_ch or g_ch not in cand_u:
                        ok = False
                        break
                elif f_type == FeedbackType.ABSENT:
                    if letter_has_non_absent.get(g_ch, False):
                        if cand_u[i] == g_ch:
                            ok = False
                            break
                    else:
                        if g_ch in cand_u:
                            ok = False
                            break
            if ok:
                out.append(cand)

        return out
