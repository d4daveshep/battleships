# Model classes for Ship
from dataclasses import dataclass
from enum import Enum


class Direction(Enum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    DIAGONAL_NE = "diagonal_ne"
    DIAGONAL_SE = "diagonal_se"


class ShipType(Enum):
    CARRIER = ("Carrier", 5, 2)
    BATTLESHIP = ("Battleship", 4, 1)
    CRUISER = ("Cruiser", 3, 1)
    SUBMARINE = ("Submarine", 3, 1)
    DESTROYER = ("Destroyer", 2, 1)

    def __init__(self, ship_name: str, length: int, guns: int):
        self.ship_name = ship_name
        self.length = length
        # self.guns = guns


@dataclass
class Coordinate:
    row: int  # 0-9 (A-J)
    col: int  # 0-9 (1-10)

    def __post_init__(self):
        if not (0 <= self.row <= 9):
            raise ValueError(f"row must be 0-9: {self.row}")
        if not (0 <= self.col <= 9):
            raise ValueError(f"row must be 0-9: {self.col}")

    @classmethod
    def from_string(cls, coord_str: str) -> "Coordinate":
        """Convert 'A1' format to Coordinate(0, 0)"""
        if len(coord_str) < 2:
            raise ValueError(f"Invalid coordinate: {coord_str}")

        row = ord(coord_str[0].upper()) - ord("A")
        col = int(coord_str[1:]) - 1

        if not (0 <= row <= 9) or not (0 <= col <= 9):
            raise ValueError(f"Coordinate out of bounds: {coord_str}")

        return cls(row, col)

    def to_string(self) -> str:
        """Convert Coordinate(0, 0) to 'A1' format"""
        return f"{chr(ord('A') + self.row)}{self.col + 1}"

    def __hash__(self):
        return hash((self.row, self.col))


@dataclass
class ShipLocation:
    ship_type: ShipType
    start_point: Coordinate
    direction: Direction
