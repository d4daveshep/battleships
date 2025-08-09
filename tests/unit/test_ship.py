# Unit tests for Ship classes
from game.ship import ShipLocation
from game.models import Coordinate, Direction, ShipType


class TestShipLocation:
    def test_ship_location(self):
        ship_location: ShipLocation = ShipLocation(
            ship_type=ShipType.CARRIER,
            start_point=Coordinate(0, 0),
            direction=Direction.HORIZONTAL,
        )
        assert ship_location.ship_type == ShipType.CARRIER
        assert ship_location.start_point == Coordinate(0, 0)
        assert ship_location.direction == Direction.HORIZONTAL
