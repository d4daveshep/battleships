import re
from dataclasses import dataclass, field
from enum import Enum, StrEnum
from typing import NamedTuple


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


class CoordDetails(NamedTuple):
    row_index: int
    col_index: int


_coords: dict[str, CoordDetails] = {
    f"{letter}{number}": CoordDetails(ord(letter) - 64, number)
    for letter in "ABCDEFGHIJ"
    for number in range(1, 11)
}

Coord = Enum("Coord", _coords)


class CoordHelper:
    _coords_by_value: dict[CoordDetails, Coord] = {
        coord.value: coord for coord in Coord
    }

    @classmethod
    def lookup(cls, row_col_index: CoordDetails) -> Coord:
        return cls._coords_by_value[row_col_index]

    @classmethod
    def coords_for_length_and_orientation(
        cls, start: Coord, length: int, orientation: Orientation
    ) -> list[Coord]:
        coords: list[Coord] = [start]

        for i in range(1, length):
            if orientation == Orientation.HORIZONTAL:
                coords.append(
                    cls.lookup(
                        CoordDetails(start.value.row_index, start.value.col_index + i)
                    )
                )

        return coords


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
            # check placement is valid
            # add positions to ship
            self.ships.append(ship)

        else:
            raise ValueError(f"Ship: {ship} already placed on board")

        return True
