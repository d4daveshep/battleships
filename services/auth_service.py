from typing import NamedTuple


class PlayerNameValidation(NamedTuple):
    """
    Represents the result of player name validation.

    Attributes:
        is_valid: Whether the player name passed validation
        error_message: Human-readable error message if validation failed
        css_class: CSS class name for styling ('valid' or 'error')
    """

    is_valid: bool
    error_message: str
    css_class: str


class AuthService:
    """
    Service for handling authentication and validation logic.

    Provides centralized validation for player names and authentication
    operations in the battleships game.
    """

    def validate_player_name(
        self, player_name: str, strip_quotes: bool = False
    ) -> PlayerNameValidation:
        """
        Validates a player name according to game rules.

        Args:
            player_name: The player name to validate
            strip_quotes: Whether to strip surrounding quotes from the name

        Returns:
            PlayerNameValidation: Validation result with status, error message, and CSS class

        Validation Rules:
            - Name must not be empty after stripping whitespace
            - Length must be between 2 and 20 characters
            - Must contain only letters, numbers, and spaces
        """
        # Centralized player name validation logic - extracted from main.py
        clean_name: str = player_name.strip()
        if strip_quotes:
            clean_name = clean_name.strip("\"'")

        if not clean_name:
            return self._validation_error("Player name is required")

        if not (2 <= len(clean_name) <= 20):
            return self._validation_error(
                "Player name must be between 2 and 20 characters"
            )

        if not clean_name.replace(" ", "").isalnum():
            return self._validation_error(
                "Player name can only contain letter, numbers and spaces"
            )

        return PlayerNameValidation(is_valid=True, error_message="", css_class="valid")

    def _validation_error(self, message: str) -> PlayerNameValidation:
        """
        Creates a validation error response.

        Args:
            message: The error message to include

        Returns:
            PlayerNameValidation: Validation result indicating failure
        """
        # Helper function to create validation error responses
        return PlayerNameValidation(
            is_valid=False, error_message=message, css_class="error"
        )

