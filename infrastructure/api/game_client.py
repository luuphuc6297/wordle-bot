"""GameClient - API adapter for Wordle game communication."""

from typing import Any, Dict

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from core.domain.models import GuessResult


class WordleAPIError(Exception):
    """Custom exception for Wordle API errors."""



class GameClient:
    """API client for communicating with the Wordle game server."""

    def __init__(
        self, base_url: str = "https://wordle.votee.dev:8000", timeout: int = 10
    ):
        """Initialize the game client.
        Args:
            base_url: Base URL for the Wordle API
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

        # Set common headers
        self.session.headers.update(
            {"Content-Type": "application/json", "User-Agent": "Wordle-Bot/1.0"}
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((requests.RequestException, WordleAPIError)),
    )
    def start_game(self) -> Dict[str, Any]:
        """Start a new Wordle game.

        Returns:
            Game initialization response

        Raises:
            WordleAPIError: If the API request fails
        """
        try:
            response = self.session.post(f"{self.base_url}/daily", timeout=self.timeout)

            self._validate_response(response)

            return response.json()

        except requests.RequestException as e:
            raise WordleAPIError(f"Failed to start game: {str(e)}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((requests.RequestException, WordleAPIError)),
    )
    def submit_guess(self, guess: str) -> GuessResult:
        """Submit a guess to the Wordle API.

        Args:
            guess: The 5-letter word to guess

        Returns:
            GuessResult with feedback from the API

        Raises:
            WordleAPIError: If the API request fails
            ValueError: If the guess is invalid
        """
        if not guess or len(guess) != 5:
            raise ValueError(f"Guess must be exactly 5 letters, got: '{guess}'")

        guess = guess.upper()

        try:
            payload = {"guess": guess}

            response = self.session.put(
                f"{self.base_url}/daily", json=payload, timeout=self.timeout
            )

            self._validate_response(response)

            data = response.json()

            # Extract result from API response
            # Expected format: {"result": "++x--", ...}
            if "result" not in data:
                raise WordleAPIError(
                    f"Invalid API response format: missing 'result' field"
                )

            result_string = data["result"]

            # Convert API response to our domain model
            guess_result = GuessResult.from_api_response(guess, result_string)

            return guess_result

        except requests.RequestException as e:
            raise WordleAPIError(f"Failed to submit guess '{guess}': {str(e)}") from e
        except (KeyError, ValueError) as e:
            raise WordleAPIError(
                f"Invalid API response for guess '{guess}': {str(e)}"
            ) from e

    def _validate_response(self, response: requests.Response) -> None:
        """Validate API response and raise appropriate errors.

        Args:
            response: The HTTP response to validate

        Raises:
            WordleAPIError: If the response indicates an error
        """
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            # Try to get error details from response body
            try:
                error_data = response.json()
                error_message = error_data.get("error", str(e))
            except (ValueError, KeyError):
                error_message = str(e)

            raise WordleAPIError(f"HTTP {response.status_code}: {error_message}") from e

        # Validate content type
        content_type = response.headers.get("content-type", "")
        if not content_type.startswith("application/json"):
            raise WordleAPIError(
                f"Expected JSON response, got content-type: {content_type}"
            )

        # Validate that we can parse JSON
        try:
            response.json()
        except ValueError as e:
            raise WordleAPIError(f"Invalid JSON response: {str(e)}") from e

    def get_game_status(self) -> Dict[str, Any]:
        """Get current game status.

        Returns:
            Current game status information

        Raises:
            WordleAPIError: If the API request fails
        """
        try:
            response = self.session.get(f"{self.base_url}/daily", timeout=self.timeout)

            self._validate_response(response)

            return response.json()

        except requests.RequestException as e:
            raise WordleAPIError(f"Failed to get game status: {str(e)}") from e

    def close(self) -> None:
        """Close the HTTP session and cleanup resources."""
        if self.session:
            self.session.close()
