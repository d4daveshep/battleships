import pytest
from game.ship import ShipLocation, ShipType, Coordinate, Direction


# Define a valid ship layout
@pytest.fixture()
def ship_layout_1() -> list[ShipLocation]:
    ship_layout: list[ShipLocation] = [
        ShipLocation(
            ship_type=ShipType.CARRIER,
            start_point=Coordinate(0, 0),
            direction=Direction.HORIZONTAL,
        ),
        ShipLocation(
            ship_type=ShipType.BATTLESHIP,
            start_point=Coordinate(2, 0),
            direction=Direction.HORIZONTAL,
        ),
        ShipLocation(
            ship_type=ShipType.CRUISER,
            start_point=Coordinate(4, 0),
            direction=Direction.HORIZONTAL,
        ),
        ShipLocation(
            ship_type=ShipType.SUBMARINE,
            start_point=Coordinate(6, 0),
            direction=Direction.HORIZONTAL,
        ),
        ShipLocation(
            ship_type=ShipType.DESTROYER,
            start_point=Coordinate(8, 0),
            direction=Direction.HORIZONTAL,
        ),
    ]
    return ship_layout
