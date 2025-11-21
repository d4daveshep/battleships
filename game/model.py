from dataclasses import dataclass, field
from enum import Enum, StrEnum
from typing import NamedTuple


class ShipAlreadyPlacedError(Exception):
    """Raised when attempting to place a ship type that has already been placed on the board."""

    pass


class ShipPlacementOutOfBoundsError(Exception):
    """Raised when attempting to place a ship that would extend beyond the board boundaries."""

    pass


class ShipPlacementTooCloseError(Exception):
    """Raised when attempting to place a ship too close to (touching or overlapping) another ship."""

    pass


class Orientation(StrEnum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    DIAGONAL_UP = "diagonal up"
    DIAGONAL_DOWN = "diagonal down"


class ShipType(Enum):
    CARRIER = ("Carrier", 5, 2, "A")
    BATTLESHIP = ("Battleship", 4, 1, "B")
    CRUISER = ("Cruiser", 3, 1, "C")
    SUBMARINE = ("Submarine", 3, 1, "S")
    DESTROYER = ("Destroyer", 2, 1, "D")

    def __init__(self, ship_name: str, length: int, shots_available: int, code: str):
        self.ship_name = ship_name
        self.length = length
        self.shots_available = shots_available
        self.code = code

    @classmethod
    def from_ship_name(cls, ship_name: str) -> "ShipType":
        for ship_type in cls:
            if ship_type.ship_name == ship_name:
                return ship_type
        raise ValueError(f"No ShipType with ship_name: {ship_name}")


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

        if orientation == Orientation.HORIZONTAL:
            for i in range(1, length):
                coords.append(
                    cls.lookup(
                        CoordDetails(start.value.row_index, start.value.col_index + i)
                    )
                )
        elif orientation == Orientation.VERTICAL:
            for i in range(1, length):
                coords.append(
                    cls.lookup(
                        CoordDetails(start.value.row_index + i, start.value.col_index)
                    )
                )
        elif orientation == Orientation.DIAGONAL_DOWN:
            for i in range(1, length):
                coords.append(
                    cls.lookup(
                        CoordDetails(
                            start.value.row_index + i, start.value.col_index + i
                        )
                    )
                )

        elif orientation == Orientation.DIAGONAL_UP:
            for i in range(1, length):
                coords.append(
                    cls.lookup(
                        CoordDetails(
                            start.value.row_index - i, start.value.col_index + i
                        )
                    )
                )
        else:
            raise ValueError(f"Invalid orientation: {orientation}")

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

    def _invalid_coords(self) -> set[Coord]:
        invalid_coords: set[Coord] = set()
        for ship in self.ships:
            invalid_coords.update(
                CoordHelper.coords_adjacent_to_a_coords_list(ship.positions)
            )
            invalid_coords.update(ship.positions)
        return invalid_coords

    def place_ship(self, ship: Ship, start: Coord, orientation: Orientation) -> bool:
        """Place a ship on the board with spacing validation.

        Validates that the ship type hasn't been placed yet, fits within board boundaries,
        and maintains required spacing (no touching or overlapping with other ships).

        Raises ValueError if placement is invalid (duplicate type, out of bounds, or too close to another ship).
        """
        ship_types_already_on_board: set[ShipType] = {
            ship.ship_type for ship in self.ships
        }

        if ship.ship_type not in ship_types_already_on_board:
            # get all invalid positions
            all_invalid_coords: set[Coord] = self._invalid_coords()

            # get planned ship positions
            try:
                positions: list[Coord] = CoordHelper.coords_for_length_and_orientation(
                    start, ship.length, orientation
                )

            except KeyError:
                raise ShipPlacementOutOfBoundsError(
                    f"Ship placement out of bounds: {ship.ship_type.name} {orientation.name} at {start.name}"
                )

            # check ship positions don't include an invalid position
            invalid_ship_positions: set[Coord] = set(positions).intersection(
                all_invalid_coords
            )
            if len(invalid_ship_positions) > 0:
                raise ShipPlacementTooCloseError(
                    f"Ship placement is too close to another ship: {ship.ship_type.name} {orientation.name} at {start.name}"
                )

            self.ships.append(ship)
            # add positions to ship
            ship.positions = positions

        else:
            raise ShipAlreadyPlacedError(
                f"Ship type: {ship.ship_type.name} already placed on board"
            )

        return True

    def ship_type_at(self, coord: Coord) -> ShipType | None:
        # TODO: Reimplement this using a cached map of Coords to Ship.code
        for ship in self.ships:
            if coord in ship.positions:
                return ship.ship_type
        return None


class GameBoardHelper:
    @classmethod
    def print(cls, board: GameBoard, show_invalid: bool = False) -> list[str]:
        """Generate ASCII visualization of game board with ships and optionally invalid placement zones.

        Returns list of strings representing board rows with ship codes (A/B/C/S/D), empty cells (.),
        and optionally invalid placement zones (x) if show_invalid=True.
        """
        ship_coords: dict[Coord, ShipType] = {
            coord: ship.ship_type for ship in board.ships for coord in ship.positions
        }
        invalid_coords: set[Coord] = board._invalid_coords() if show_invalid else set()

        output: list[str] = []
        output.append("  1 2 3 4 5 6 7 8 9 10")
        output.append("-|--------------------")
        for row_index, row_letter in enumerate("ABCDEFGHIJ", start=1):
            row_output: str = f"{row_letter}|"
            for col_index in range(1, 11):
                coord: Coord = CoordHelper.lookup(CoordDetails(row_index, col_index))
                ship_type: ShipType | None = ship_coords.get(coord)
                if ship_type:
                    row_output += ship_type.code + " "
                elif show_invalid and coord in invalid_coords:
                    row_output += "x "
                else:
                    row_output += ". "

            output.append(row_output)
        return output
