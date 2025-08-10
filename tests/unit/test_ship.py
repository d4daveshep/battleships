# Unit tests for Ship classes
import pytest

from game.ship import Coordinate, Direction, ShipType, ShipLocation


class TestCoordinate:
    def test_coordinate_creation(self):
        coord: Coordinate = Coordinate(0, 0)
        assert coord.row == 0
        assert coord.col == 0

    def test_coordinate_invalid(self):
        with pytest.raises(ValueError):
            Coordinate(10, 0)

        with pytest.raises(ValueError):
            Coordinate(0, 10)

        with pytest.raises(ValueError):
            Coordinate(-10, 0)

        with pytest.raises(ValueError):
            Coordinate(0, -10)

    def test_from_string_valid(self):
        coord: Coordinate = Coordinate.from_string("A1")
        assert coord.row == 0
        assert coord.col == 0

        coord = Coordinate.from_string("J10")
        assert coord.row == 9
        assert coord.col == 9

        coord = Coordinate.from_string("E5")
        assert coord.row == 4
        assert coord.col == 4

    def test_from_string_invalid(self):
        with pytest.raises(ValueError):
            Coordinate.from_string("A")

        with pytest.raises(ValueError):
            Coordinate.from_string("K1")  # Out of bounds

        with pytest.raises(ValueError):
            Coordinate.from_string("A11")  # Out of bounds

    def test_to_string(self):
        coord: Coordinate = Coordinate(0, 0)
        assert coord.to_string() == "A1"

        coord = Coordinate(9, 9)
        assert coord.to_string() == "J10"

        coord = Coordinate(4, 4)
        assert coord.to_string() == "E5"

    def test_coordinate_hashable(self):
        coord1: Coordinate = Coordinate(0, 0)
        coord2: Coordinate = Coordinate(0, 0)
        coord3: Coordinate = Coordinate(1, 1)

        coord_set: set[Coordinate] = {coord1, coord2, coord3}
        assert len(coord_set) == 2  # coord1 and coord2 should be the same

    def test_coordinate_equality(self):
        coord1: Coordinate = Coordinate(0, 0)
        coord2: Coordinate = Coordinate(0, 0)
        coord3: Coordinate = Coordinate(1, 1)

        assert coord1 == coord2
        assert coord1 != coord3


class TestShipType:
    def test_all_ship_types_exist(self):
        types: set[ShipType] = set(ShipType)
        assert len(types) == 5
        assert types == {
            ShipType.BATTLESHIP,
            ShipType.CARRIER,
            ShipType.CRUISER,
            ShipType.DESTROYER,
            ShipType.SUBMARINE,
        }

    def test_ship_type_properties(self):
        carrier_type: ShipType = ShipType.CARRIER
        assert carrier_type.ship_name == "Carrier"
        assert carrier_type.length == 5
        # assert carrier_type.guns == 2

        destroyer_type: ShipType = ShipType.DESTROYER
        assert destroyer_type.ship_name == "Destroyer"
        assert destroyer_type.length == 2
        # assert destroyer_type.guns == 1


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
