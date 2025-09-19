"""JSON formatter for Wordle Bot output."""

import json
from collections.abc import Mapping
from typing import Any

from .base_formatter import BaseFormatter


class JsonFormatter(BaseFormatter):
    """JSON output formatter."""

    def format(self, result: Mapping[str, Any]) -> str:
        """Format the result as JSON.

        Args:
            result: The result to format

        Returns:
            JSON formatted string
        """
        return json.dumps(result, indent=2, default=str)

    def save_to_file(self, result: Mapping[str, Any], filename: str) -> None:
        """Save the result to a JSON file.

        Args:
            result: The result to save
            filename: The filename to save to
        """
        with open(filename, "w") as f:
            json.dump(result, f, indent=2, default=str)
