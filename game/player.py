from dataclasses import dataclass
from enum import StrEnum


class PlayerStatus(StrEnum):
    AVAILABLE = "Available"


@dataclass
class Player:
    name: str
    status: str