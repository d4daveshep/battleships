from dataclasses import dataclass
from enum import StrEnum


class PlayerStatus(StrEnum):
    AVAILABLE = "Available"


@dataclass
class Player:
    name: str
    status: PlayerStatus

    def __post_init__(self):
        if not isinstance(self.status, PlayerStatus):
            raise TypeError(
                f"status must be a PlayerStatus enum, got {type(self.status)}"
            )

