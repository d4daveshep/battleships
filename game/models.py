# from enum import Enum
# from dataclasses import dataclass, field
# from typing import List, Tuple, Optional, Set
# import json
#
#
# class Direction(Enum):
#     HORIZONTAL = "horizontal"
#     VERTICAL = "vertical"
#     DIAGONAL_NE = "diagonal_ne"
#     DIAGONAL_SE = "diagonal_se"
#
#
# class ShipType(Enum):
#     CARRIER = ("Carrier", 5, 2)
#     BATTLESHIP = ("Battleship", 4, 1)
#     CRUISER = ("Cruiser", 3, 1)
#     SUBMARINE = ("Submarine", 3, 1)
#     DESTROYER = ("Destroyer", 2, 1)
#
#     def __init__(self, ship_name: str, length: int, guns: int):
#         self.ship_name = ship_name
#         self.length = length
#         self.guns = guns
#
#
# @dataclass
# class Coordinate:
#     row: int  # 0-9 (A-J)
#     col: int  # 0-9 (1-10)
#
#     def __post_init__(self):
#         if not (0 <= self.row <= 9):
#             raise ValueError(f"row must be 0-9: {self.row}")
#         if not (0 <= self.col <= 9):
#             raise ValueError(f"row must be 0-9: {self.col}")
#
#     @classmethod
#     def from_string(cls, coord_str: str) -> "Coordinate":
#         """Convert 'A1' format to Coordinate(0, 0)"""
#         if len(coord_str) < 2:
#             raise ValueError(f"Invalid coordinate: {coord_str}")
#
#         row = ord(coord_str[0].upper()) - ord("A")
#         col = int(coord_str[1:]) - 1
#
#         if not (0 <= row <= 9) or not (0 <= col <= 9):
#             raise ValueError(f"Coordinate out of bounds: {coord_str}")
#
#         return cls(row, col)
#
#     def to_string(self) -> str:
#         """Convert Coordinate(0, 0) to 'A1' format"""
#         return f"{chr(ord('A') + self.row)}{self.col + 1}"
#
#     def __hash__(self):
#         return hash((self.row, self.col))
#
#
# @dataclass
# class Ship:
#     ship_type: ShipType
#     positions: List[Coordinate] = field(default_factory=list)
#     hits: Set[Coordinate] = field(default_factory=set)
#
#     @property
#     def is_sunk(self) -> bool:
#         return len(self.hits) >= self.ship_type.length
#
#     @property
#     def is_afloat(self) -> bool:
#         return not self.is_sunk
#
#     @property
#     def length(self) -> int:
#         return self.ship_type.length
#
#     @property
#     def guns_available(self) -> int:
#         return self.ship_type.guns if self.is_afloat else 0
#
#     def is_at(self, coordinate: Coordinate) -> bool:
#         return coordinate in self.positions
#
#     def incoming_shot(self, coordinate: Coordinate) -> bool:
#         """Return True if incoming_shot is a hit (ship is at that position)"""
#         if self.is_at(coordinate):
#             self.hits.add(coordinate)
#             return True
#         return False
#
#     def place_ship(self, start: Coordinate, direction: Direction) -> List[Coordinate]:
#         """Calculate and set ship positions based on start coordinate and direction"""
#         positions = []
#
#         for i in range(self.ship_type.length):
#             if direction == Direction.HORIZONTAL:
#                 pos = Coordinate(start.row, start.col + i)
#             elif direction == Direction.VERTICAL:
#                 pos = Coordinate(start.row + i, start.col)
#             elif direction == Direction.DIAGONAL_NE:
#                 pos = Coordinate(start.row - i, start.col + i)
#             elif direction == Direction.DIAGONAL_SE:
#                 pos = Coordinate(start.row + i, start.col + i)
#             else:
#                 raise ValueError(f"Invalid direction: {direction}")
#
#             # Validate position is within board bounds
#             if not (0 <= pos.row <= 9 and 0 <= pos.col <= 9):
#                 raise ValueError(
#                     f"Ship placement would go out of bounds at {pos.to_string()}"
#                 )
#
#             positions.append(pos)
#
#         self.positions = positions
#         return positions
