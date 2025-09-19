"""Base formatter for Wordle Bot output."""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any


class BaseFormatter(ABC):
    """Base class for output formatters."""

    @abstractmethod
    def format(self, result: Mapping[str, Any]) -> str:
        """Format the result for output.

        Args:
            result: The result to format

        Returns:
            Formatted string
        """
        pass

    @abstractmethod
    def save_to_file(self, result: Mapping[str, Any], filename: str) -> None:
        """Save the result to a file.

        Args:
            result: The result to save
            filename: The filename to save to
        """
        pass
