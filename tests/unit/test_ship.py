# Unit tests for Ship classes
import pytest

from game.ship import Coordinate, Direction, ShipType, ShipLocation, Ship


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


class TestShip:
    def test_ship_creation(self):
        ship: Ship = Ship(ShipType.CARRIER)
        assert ship.ship_type == ShipType.CARRIER
        assert ship.length == 5
        assert ship.guns_available == 2
        assert ship.is_afloat
        assert not ship.is_sunk
        assert len(ship.coordinates) == 0
        assert len(ship.hits_taken) == 0

    def test_place_ship_horizontal(self):
        ship: Ship = Ship(ShipType.DESTROYER)  # Length 2
        start: Coordinate = Coordinate(0, 0)
        coordinates: set[Coordinate] = ship.place_ship(start, Direction.HORIZONTAL)

        expected: set[Coordinate] = {Coordinate(0, 0), Coordinate(0, 1)}
        assert coordinates == expected
        assert ship.coordinates == expected

    def test_place_ship_vertical(self):
        ship: Ship = Ship(ShipType.DESTROYER)  # Length 2
        start: Coordinate = Coordinate(0, 0)
        coordinates: set[Coordinate] = ship.place_ship(start, Direction.VERTICAL)

        expected: set[Coordinate] = {Coordinate(0, 0), Coordinate(1, 0)}
        assert coordinates == expected
        assert ship.coordinates == expected

    def test_place_ship_diagonal_ne(self):
        ship: Ship = Ship(ShipType.DESTROYER)  # Length 2
        start: Coordinate = Coordinate(1, 0)
        coordinates: set[Coordinate] = ship.place_ship(start, Direction.DIAGONAL_NE)

        expected: set[Coordinate] = {Coordinate(1, 0), Coordinate(0, 1)}
        assert coordinates == expected
        assert ship.coordinates == expected

    def test_place_ship_diagonal_se(self):
        ship: Ship = Ship(ShipType.DESTROYER)  # Length 2
        start: Coordinate = Coordinate(0, 0)
        coordinates: set[Coordinate] = ship.place_ship(start, Direction.DIAGONAL_SE)

        expected: set[Coordinate] = {Coordinate(0, 0), Coordinate(1, 1)}
        assert coordinates == expected
        assert ship.coordinates == expected

    def test_place_ship_out_of_bounds(self):
        ship: Ship = Ship(ShipType.CARRIER)  # Length 5

        # Horizontal out of bounds
        with pytest.raises(ValueError):
            ship.place_ship(Coordinate(0, 6), Direction.HORIZONTAL)

        # Vertical out of bounds
        with pytest.raises(ValueError):
            ship.place_ship(Coordinate(6, 0), Direction.VERTICAL)

        # Diagonal out of bounds
        with pytest.raises(ValueError):
            ship.place_ship(Coordinate(0, 6), Direction.DIAGONAL_SE)

    def test_ship_is_at_coordinate(self):
        ship: Ship = Ship(ShipType.DESTROYER)
        ship.place_ship(Coordinate(0, 0), Direction.HORIZONTAL)

        assert ship.is_at(Coordinate(0, 0))
        assert ship.is_at(Coordinate(0, 1))
        assert not ship.is_at(Coordinate(1, 0))
        assert not ship.is_at(Coordinate(1, 1))

    def test_ship_hit(self):
        ship: Ship = Ship(ShipType.DESTROYER)
        ship.place_ship(Coordinate(0, 0), Direction.HORIZONTAL)

        # Hit valid position
        assert ship.incoming_shot(Coordinate(0, 0))
        assert Coordinate(0, 0) in ship.hits_taken
        assert not ship.is_sunk

        # Hit invalid position
        assert not ship.incoming_shot(Coordinate(1, 1))
        assert Coordinate(1, 1) not in ship.hits_taken

        # Hit second position to sink ship
        assert ship.incoming_shot(Coordinate(0, 1))
        assert ship.is_sunk
        assert ship.guns_available == 0

    def test_ship_sinking(self):
        ship: Ship = Ship(ShipType.CRUISER)  # Length 3
        ship.place_ship(Coordinate(0, 0), Direction.HORIZONTAL)

        # Hit all positions
        ship.incoming_shot(Coordinate(0, 0))
        assert ship.is_afloat

        ship.incoming_shot(Coordinate(0, 1))
        assert ship.is_afloat

        ship.incoming_shot(Coordinate(0, 2))
        assert ship.is_sunk
        assert ship.guns_available == 0

    def test_shots_available(self):
        carrier = Ship(ShipType.CARRIER)
        assert carrier.guns_available == 2

        destroyer = Ship(ShipType.DESTROYER)
        assert destroyer.guns_available == 1

        # After sinking
        destroyer.place_ship(Coordinate(0, 0), Direction.HORIZONTAL)
        destroyer.incoming_shot(Coordinate(0, 0))
        destroyer.incoming_shot(Coordinate(0, 1))
        assert destroyer.guns_available == 0
