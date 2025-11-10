import re
from dataclasses import dataclass, field
from enum import Enum, StrEnum
from typing import ClassVar


class Orientation(StrEnum):
    HORIZONTAL = "horizontal"


class ShipType(Enum):
    CARRIER = ("Carrier", 5, 2)
    BATTLESHIP = ("Battleship", 4, 1)
    CRUISER = ("Cruiser", 3, 1)
    SUBMARINE = ("Submarine", 3, 1)
    DESTROYER = ("Destroyer", 2, 1)

    def __init__(self, ship_name: str, length: int, shots_available: int):
        self.ship_name = ship_name
        self.length = length
        self.shots_available = shots_available


@dataclass(frozen=True)
class Coord:
    PATTERN: ClassVar[str] = r"^[a-jA-J](10|[1-9])$"  # 10x10 grid from A1 to J10

    _str: str

    def __post_init__(self):
        if not re.match(self.PATTERN, self._str):
            raise ValueError(f"Invalid coord string:{self._str}")

    @property
    def row(self) -> str:
        return self._str[0]

    @property
    def row_index(self) -> int:
        return ord(self._str[0]) - 64

    @property
    def col(self) -> int:
        return int(self._str[1:])


@dataclass
class Ship:
    ship_type: ShipType
    positions: list[Coord] = field(default_factory=list)

    @property
    def length(self) -> int:
        return self.ship_type.length

    @property
    def shots_available(self) -> int:
        return self.ship_type.shots_available


class GameBoard:
    def __init__(self) -> None:
        self.ships: list[Ship] = []
        self.shots_received: dict = {}
        self.shots_fired: dict = {}

    def place_ship(self, ship: Ship, start: Coord, orientation: Orientation) -> bool:
        if ship not in self.ships:
            self.ships.append(ship)
        else:
            raise ValueError(f"Ship: {ship} already placed on board")

        return True
