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
    status: str


@dataclass
class Player:
    name: str
    status: PlayerStatus

    def __post_init__(self):
        if not isinstance(self.status, PlayerStatus):
            raise TypeError(
                f"status must be a PlayerStatus enum, got {type(self.status)}"
            )

