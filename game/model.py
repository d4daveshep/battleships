import re
from dataclasses import dataclass, field
from enum import Enum, StrEnum
from typing import NamedTuple


class Orientation(StrEnum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    DIAGONAL_UP = "diagonal up"
    DIAGONAL_DOWN = "diagonal down"


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

    @classmethod
    def coords_adjacent_to_a_coord(cls, centre: Coord) -> set[Coord]:
        adjacent_coords: set[Coord] = set()
        for row_delta in [-1, 0, 1]:
            for col_delta in [-1, 0, 1]:
                if row_delta == 0 and col_delta == 0:
                    continue
                try:
                    adjacent_coord: Coord = cls.lookup(
                        CoordDetails(
                            centre.value.row_index + row_delta,
                            centre.value.col_index + col_delta,
                        )
                    )
                    adjacent_coords.add(adjacent_coord)
                except KeyError:
                    pass  # skip any coords that are out of bounds
        return adjacent_coords

    @classmethod
    def coords_adjacent_to_a_coords_list(cls, coords: list[Coord]) -> set[Coord]:
        adjacent_coords: set[Coord] = set()
        for coord in coords:
            adjacent_coords.update(cls.coords_adjacent_to_a_coord(coord))
        adjacent_coords = adjacent_coords - set(coords)
        return adjacent_coords


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
        ship_types_already_on_board: set[ShipType] = {
            ship.ship_type for ship in self.ships
        }

        if ship.ship_type not in ship_types_already_on_board:
            # get all invalid positions
            all_invalid_coords: set[Coord] = self._get_invalid_coords()

            # get planned ship positions
            try:
                positions: list[Coord] = CoordHelper.coords_for_length_and_orientation(
                    start, ship.length, orientation
                )

            except KeyError as err:
                raise ValueError(
                    f"Ship placement out of bounds: {ship.ship_type.name} {orientation.name} at {start.name}"
                )

            # check ship positions don't include an invalid position
            invalid_ship_positions: set[Coord] = set(positions).intersection(
                all_invalid_coords
            )
            if len(invalid_ship_positions) > 0:
                raise ValueError(
                    f"Ship placement is too close to another ship: {ship.ship_type.name} {orientation.name} at {start.name}"
                )

            self.ships.append(ship)
            # add positions to ship
            ship.positions = positions

        else:
            raise ValueError(
                f"Ship type: {ship.ship_type.name} already placed on board"
            )

        return True
