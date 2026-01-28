"""Custom exceptions for the battleships game domain.

This module centralizes all game-specific exceptions for better organization
and easier import management.
"""


# Ship placement exceptions (with user-friendly messages)
class ShipPlacementError(Exception):
    """Base exception for ship placement errors."""

    def __init__(self, message: str, user_message: str = ""):
        super().__init__(message)
        self.user_message: str = user_message or message


class ShipAlreadyPlacedError(ShipPlacementError):
    """Raised when attempting to place a ship type that has already been placed."""

    def __init__(self, message: str):
        super().__init__(message, "Ships must have empty space around them")


class ShipPlacementOutOfBoundsError(ShipPlacementError):
    """Raised when ship placement extends beyond board boundaries."""

    def __init__(self, message: str):
        super().__init__(message, "Ship placement goes outside the board")


class ShipPlacementTooCloseError(ShipPlacementError):
    """Raised when ship placement is too close to another ship."""

    def __init__(self, message: str, is_overlap: bool = False):
        user_msg = (
            "Ships cannot overlap"
            if is_overlap
            else "Ships must have empty space around them"
        )
        super().__init__(message, user_msg)


# Player/Game service exceptions
class PlayerAlreadyInGameException(Exception):
    """Raised when a player attempts to join a game while already in one."""

    pass


class UnknownPlayerException(Exception):
    """Raised when referencing a player that doesn't exist."""

    pass


class PlayerNotInGameException(Exception):
    """Raised when a player is expected to be in a game but isn't."""

    pass


class DuplicatePlayerException(Exception):
    """Raised when attempting to add a player that already exists."""

    pass


class UnknownGameException(Exception):
    """Raised when referencing a game that doesn't exist."""

    pass


# Gameplay exceptions
class GameplayError(Exception):
    """Base exception for gameplay logic errors."""

    pass


class ShotLimitExceededError(GameplayError):
    """Raised when a player aims more shots than allowed."""

    pass


class ActionAfterFireError(GameplayError):
    """Raised when attempting to aim or fire after already firing."""

    pass


class NoShotsAimedError(GameplayError):
    """Raised when attempting to fire with no shots aimed."""

    pass
