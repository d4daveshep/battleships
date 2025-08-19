from typing import NamedTuple


class PlayerNameValidation(NamedTuple):
    is_valid: bool
    error_message: str
    css_class: str


class AuthService:
    def validate_player_name(self, player_name: str, strip_quotes: bool = False) -> PlayerNameValidation:
        # Centralized player name validation logic - extracted from main.py
        clean_name: str = player_name.strip()
        if strip_quotes:
            clean_name = clean_name.strip("\"'")

        if not clean_name:
            return self._validation_error("Player name is required")

        if not (2 <= len(clean_name) <= 20):
            return self._validation_error("Player name must be between 2 and 20 characters")

        if not clean_name.replace(" ", "").isalnum():
            return self._validation_error(
                "Player name can only contain letter, numbers and spaces"
            )

        return PlayerNameValidation(is_valid=True, error_message="", css_class="valid")

    def _validation_error(self, message: str) -> PlayerNameValidation:
        # Helper function to create validation error responses
        return PlayerNameValidation(
            is_valid=False, error_message=message, css_class="error"
        )