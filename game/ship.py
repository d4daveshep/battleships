# Model classes for Ship
from dataclasses import dataclass

from game.models import Coordinate, Direction, ShipType


@dataclass
class ShipLocation:
    ship_type: ShipType
    start_point: Coordinate
    direction: Direction
