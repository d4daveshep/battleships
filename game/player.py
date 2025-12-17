import secrets
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class PlayerStatus(StrEnum):
    AVAILABLE = "Available"
    REQUESTING_GAME = "Requesting Game"
    PENDING_RESPONSE = "Pending Response"
    IN_GAME = "In Game"


@dataclass
class GameRequest:
    sender: str
    receiver: str
    timestamp: datetime


class Player:
    def __init__(self, name: str, status: PlayerStatus) -> None:
        self.name: str = name
        self.status: PlayerStatus
        if isinstance(status, PlayerStatus):
            self.status = status
        else:
            raise TypeError(f"status must be a PlayerStatus enum, got {type(status)}")
        self._id: str = Player.generate_id()

    @property
    def id(self) -> str:
        """Read-only player ID that is automatically generated at creation."""
        return self._id

    @classmethod
    def generate_id(cls) -> str:
        """Generate a unique player ID using a cryptographically secure random token.

        Returns:
            str: A URL-safe random token string (always 22 characters, from 16 random bytes)
        """
        return secrets.token_urlsafe(16)
