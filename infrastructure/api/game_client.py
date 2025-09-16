"""GameClient - API adapter for Wordle game communication."""

from typing import Any

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config.settings import Settings
from config.settings import settings as default_settings
from core.domain.models import GuessResult


class WordleAPIError(Exception):
    """Custom exception for Wordle API errors."""


class GameClient:
    """API client for communicating with the Wordle game server."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: int | None = None,
        app_settings: Settings | None = None,
    ):
        """Initialize the game client.
        Args:
            base_url: Base URL for the Wordle API
            timeout: Request timeout in seconds
        """
        settings = app_settings or default_settings
        effective_base = base_url or settings.WORDLE_API_BASE_URL
        effective_timeout = timeout or settings.API_TIMEOUT_SECONDS

        self.base_url = effective_base.rstrip("/")
        self.timeout = effective_timeout
        self.session = requests.Session()

        # Set common headers
        self.session.headers.update(
            {"Content-Type": "application/json", "User-Agent": "Wordle-Bot/1.0"}
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((requests.RequestException, WordleAPIError)),
    )
    def submit_guess(self, guess: str) -> GuessResult:
        """Submit a guess to the Daily Wordle API.

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
            # Daily API: GET /daily?guess=WORD
            # Returns array of slot results for the same target word
            response = self.session.get(
                f"{self.base_url}/daily", params={"guess": guess}, timeout=self.timeout
            )

            self._validate_response(response)

            data = response.json()

            # Daily API returns array of slots, convert to pattern string
            pattern = self._slots_to_pattern(data)
            guess_result = GuessResult.from_api_response(guess, pattern)

            return guess_result

        except requests.RequestException as e:
            raise WordleAPIError(
                f"Failed to submit daily guess '{guess}': {str(e)}"
            ) from e
        except (KeyError, ValueError) as e:
            raise WordleAPIError(
                f"Invalid API response for daily guess '{guess}': {str(e)}"
            ) from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((requests.RequestException, WordleAPIError)),
    )
    def submit_random_guess(self, guess: str) -> GuessResult:
        """Submit a guess in random mode via GET /random?guess=WORD.

        WARNING: Random API returns a DIFFERENT target word for each call!
        This means each guess is against a new random word, not a consistent game.

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
            # Random API: GET /random?guess=WORD
            # WARNING: Each call returns a DIFFERENT target word!
            response = self.session.get(
                f"{self.base_url}/random", params={"guess": guess}, timeout=self.timeout
            )
            self._validate_response(response)
            data = response.json()
            pattern = self._slots_to_pattern(data)
            return GuessResult.from_api_response(guess, pattern)
        except requests.RequestException as e:
            raise WordleAPIError(
                f"Failed to submit random guess '{guess}': {str(e)}"
            ) from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((requests.RequestException, WordleAPIError)),
    )
    def submit_word_target_guess(self, target_word: str, guess: str) -> GuessResult:
        """Submit a guess against a specific target via GET /word/{word}?guess=WORD.

        API returns an array of slot results; we convert it to pattern string.
        """
        if not guess or len(guess) != 5:
            raise ValueError(f"Guess must be exactly 5 letters, got: '{guess}'")
        if not target_word or len(target_word) != 5:
            raise ValueError(f"Target must be exactly 5 letters, got: '{target_word}'")
        guess = guess.upper()
        target = target_word.upper()
        try:
            response = self.session.get(
                f"{self.base_url}/word/{target}",
                params={"guess": guess},
                timeout=self.timeout,
            )
            self._validate_response(response)
            data = response.json()
            pattern = self._slots_to_pattern(data)
            return GuessResult.from_api_response(guess, pattern)
        except requests.RequestException as e:
            raise WordleAPIError(
                f"Failed to submit word-target guess '{guess}' for '{target}': {str(e)}"
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
            # Prefer server-provided error details
            body_text = response.text
            try:
                error_data = response.json()
            except ValueError:
                error_data = None
            error_message = (
                error_data.get("detail")
                if isinstance(error_data, dict) and "detail" in error_data
                else (
                    error_data.get("error")
                    if isinstance(error_data, dict)
                    else body_text
                )
            )
            raise WordleAPIError(f"HTTP {response.status_code}: {error_message}") from e

        # Try to parse JSON regardless of content-type strictness
        try:
            response.json()
        except ValueError as e:
            content_type = response.headers.get("content-type", "")
            raise WordleAPIError(
                f"Invalid JSON response (content-type={content_type}): {str(e)}"
            ) from e

    def _slots_to_pattern(self, slots: list[dict[str, str]]) -> str:
        """Convert API slot array to Wordle pattern string.

        Expected item format: {"slot": int, "guess": str, "result": "correct|present|absent"}
        """
        if not isinstance(slots, list) or len(slots) != 5:
            raise WordleAPIError("Invalid slots array from API")
        mapping = {"correct": "+", "present": "o", "absent": "-"}
        try:
            # Ensure order by slot index
            ordered = sorted(slots, key=lambda x: x["slot"])  # type: ignore[index]
            return "".join(mapping.get(item.get("result", ""), "-") for item in ordered)
        except Exception as e:
            raise WordleAPIError(f"Failed to parse slots: {e}") from e

    def get_game_status(self) -> dict[str, Any]:
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
