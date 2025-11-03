"""Unit tests for game/ship.py - Core ship data structures"""

import pytest
from game.ship import Ship, ShipType


class TestShipType:
    """Tests for ShipType enum"""

    def test_ship_type_enum_values(self) -> None:
        """ShipType enum has all required ship types"""
        assert ShipType.CARRIER == "Carrier"
        assert ShipType.BATTLESHIP == "Battleship"
        assert ShipType.CRUISER == "Cruiser"
        assert ShipType.SUBMARINE == "Submarine"
        assert ShipType.DESTROYER == "Destroyer"

    def test_ship_type_is_string_enum(self) -> None:
        """ShipType values are strings"""
        assert isinstance(ShipType.CARRIER.value, str)
        assert isinstance(ShipType.BATTLESHIP.value, str)

    def test_ship_type_count(self) -> None:
        """ShipType enum has exactly 5 ship types"""
        assert len(list(ShipType)) == 5

    def test_carrier_properties(self) -> None:
        """Carrier has correct length and shots_available"""
        assert ShipType.CARRIER.length == 5
        assert ShipType.CARRIER.shots_available == 2

    def test_battleship_properties(self) -> None:
        """Battleship has correct length and shots_available"""
        assert ShipType.BATTLESHIP.length == 4
        assert ShipType.BATTLESHIP.shots_available == 1

    def test_cruiser_properties(self) -> None:
        """Cruiser has correct length and shots_available"""
        assert ShipType.CRUISER.length == 3
        assert ShipType.CRUISER.shots_available == 1

    def test_submarine_properties(self) -> None:
        """Submarine has correct length and shots_available"""
        assert ShipType.SUBMARINE.length == 3
        assert ShipType.SUBMARINE.shots_available == 1

    def test_destroyer_properties(self) -> None:
        """Destroyer has correct length and shots_available"""
        assert ShipType.DESTROYER.length == 2
        assert ShipType.DESTROYER.shots_available == 1


class TestShip:
    """Tests for Ship dataclass"""

    def test_create_carrier(self) -> None:
        """Can create a Carrier ship with correct attributes"""
        ship = Ship(
            ship_type=ShipType.CARRIER,
            coordinates=["A1", "A2", "A3", "A4", "A5"],
            orientation="horizontal",
            is_placed=True
        )
        assert ship.name == "Carrier"
        assert ship.length == 5
        assert ship.shots_available == 2
        assert ship.coordinates == ["A1", "A2", "A3", "A4", "A5"]
        assert ship.orientation == "horizontal"
        assert ship.is_placed is True

    def test_create_battleship(self) -> None:
        """Can create a Battleship with correct attributes"""
        ship = Ship(
            ship_type=ShipType.BATTLESHIP,
            coordinates=["B1", "C1", "D1", "E1"],
            orientation="vertical",
            is_placed=True
        )
        assert ship.name == "Battleship"
        assert ship.length == 4
        assert ship.shots_available == 1
        assert len(ship.coordinates) == 4

    def test_create_cruiser(self) -> None:
        """Can create a Cruiser with correct attributes"""
        ship = Ship(
            ship_type=ShipType.CRUISER,
            coordinates=["A1", "B2", "C3"],
            orientation="diagonal",
            is_placed=True
        )
        assert ship.name == "Cruiser"
        assert ship.length == 3
        assert ship.shots_available == 1

    def test_create_submarine(self) -> None:
        """Can create a Submarine with correct attributes"""
        ship = Ship(
            ship_type=ShipType.SUBMARINE,
            coordinates=["E5", "E6", "E7"],
            orientation="horizontal",
            is_placed=True
        )
        assert ship.name == "Submarine"
        assert ship.length == 3
        assert ship.shots_available == 1

    def test_create_destroyer(self) -> None:
        """Can create a Destroyer with correct attributes"""
        ship = Ship(
            ship_type=ShipType.DESTROYER,
            coordinates=["J9", "J10"],
            orientation="horizontal",
            is_placed=True
        )
        assert ship.name == "Destroyer"
        assert ship.length == 2
        assert ship.shots_available == 1

    def test_ship_not_placed(self) -> None:
        """Can create a ship that is not yet placed"""
        ship = Ship(
            ship_type=ShipType.CARRIER,
            coordinates=[],
            orientation="",
            is_placed=False
        )
        assert ship.is_placed is False
        assert ship.coordinates == []
        assert ship.orientation == ""

    def test_ship_with_empty_coordinates(self) -> None:
        """Ship can have empty coordinates list"""
        ship = Ship(
            ship_type=ShipType.DESTROYER,
            coordinates=[],
            orientation="horizontal",
            is_placed=False
        )
        assert ship.coordinates == []
        assert len(ship.coordinates) == 0

    def test_ship_coordinates_match_length(self) -> None:
        """Ship coordinates list length matches ship length"""
        ship = Ship(
            ship_type=ShipType.CARRIER,
            coordinates=["A1", "A2", "A3", "A4", "A5"],
            orientation="horizontal",
            is_placed=True
        )
        assert len(ship.coordinates) == ship.length

    def test_ship_horizontal_orientation(self) -> None:
        """Ship can have horizontal orientation"""
        ship = Ship(
            ship_type=ShipType.DESTROYER,
            coordinates=["A1", "A2"],
            orientation="horizontal",
            is_placed=True
        )
        assert ship.orientation == "horizontal"

    def test_ship_vertical_orientation(self) -> None:
        """Ship can have vertical orientation"""
        ship = Ship(
            ship_type=ShipType.DESTROYER,
            coordinates=["A1", "B1"],
            orientation="vertical",
            is_placed=True
        )
        assert ship.orientation == "vertical"

    def test_ship_diagonal_orientation(self) -> None:
        """Ship can have diagonal orientation"""
        ship = Ship(
            ship_type=ShipType.CRUISER,
            coordinates=["A1", "B2", "C3"],
            orientation="diagonal",
            is_placed=True
        )
        assert ship.orientation == "diagonal"

    def test_ship_is_dataclass(self) -> None:
        """Ship is a dataclass"""
        ship = Ship(
            ship_type=ShipType.CARRIER,
            coordinates=["A1", "A2", "A3", "A4", "A5"],
            orientation="horizontal",
            is_placed=True
        )
        # Dataclasses have __dataclass_fields__ attribute
        assert hasattr(Ship, '__dataclass_fields__')

    def test_ship_equality(self) -> None:
        """Two ships with same attributes are equal"""
        ship1 = Ship(
            ship_type=ShipType.DESTROYER,
            coordinates=["A1", "A2"],
            orientation="horizontal",
            is_placed=True
        )
        ship2 = Ship(
            ship_type=ShipType.DESTROYER,
            coordinates=["A1", "A2"],
            orientation="horizontal",
            is_placed=True
        )
        assert ship1 == ship2

    def test_ship_inequality_different_coordinates(self) -> None:
        """Two ships with different coordinates are not equal"""
        ship1 = Ship(
            ship_type=ShipType.DESTROYER,
            coordinates=["A1", "A2"],
            orientation="horizontal",
            is_placed=True
        )
        ship2 = Ship(
            ship_type=ShipType.DESTROYER,
            coordinates=["B1", "B2"],
            orientation="horizontal",
            is_placed=True
        )
        assert ship1 != ship2

    def test_ship_inequality_different_placement_status(self) -> None:
        """Two ships with different placement status are not equal"""
        ship1 = Ship(
            ship_type=ShipType.DESTROYER,
            coordinates=["A1", "A2"],
            orientation="horizontal",
            is_placed=True
        )
        ship2 = Ship(
            ship_type=ShipType.DESTROYER,
            coordinates=["A1", "A2"],
            orientation="horizontal",
            is_placed=False
        )
        assert ship1 != ship2

    def test_ship_type_property_is_immutable(self) -> None:
        """Ship's ship_type determines its immutable properties"""
        ship = Ship(
            ship_type=ShipType.CARRIER,
            coordinates=["A1", "A2", "A3", "A4", "A5"],
            orientation="horizontal",
            is_placed=True
        )
        assert ship.ship_type == ShipType.CARRIER
        assert ship.name == ShipType.CARRIER.value
        assert ship.length == ShipType.CARRIER.length
        assert ship.shots_available == ShipType.CARRIER.shots_available


class TestShipSpecifications:
    """Tests for ship specifications according to game rules"""

    def test_carrier_specifications(self) -> None:
        """Carrier has length 5 and 2 shots available"""
        ship = Ship(
            ship_type=ShipType.CARRIER,
            coordinates=["A1", "A2", "A3", "A4", "A5"],
            orientation="horizontal",
            is_placed=True
        )
        assert ship.length == 5
        assert ship.shots_available == 2

    def test_battleship_specifications(self) -> None:
        """Battleship has length 4 and 1 shot available"""
        ship = Ship(
            ship_type=ShipType.BATTLESHIP,
            coordinates=["A1", "A2", "A3", "A4"],
            orientation="horizontal",
            is_placed=True
        )
        assert ship.length == 4
        assert ship.shots_available == 1

    def test_cruiser_specifications(self) -> None:
        """Cruiser has length 3 and 1 shot available"""
        ship = Ship(
            ship_type=ShipType.CRUISER,
            coordinates=["A1", "A2", "A3"],
            orientation="horizontal",
            is_placed=True
        )
        assert ship.length == 3
        assert ship.shots_available == 1

    def test_submarine_specifications(self) -> None:
        """Submarine has length 3 and 1 shot available"""
        ship = Ship(
            ship_type=ShipType.SUBMARINE,
            coordinates=["A1", "A2", "A3"],
            orientation="horizontal",
            is_placed=True
        )
        assert ship.length == 3
        assert ship.shots_available == 1

    def test_destroyer_specifications(self) -> None:
        """Destroyer has length 2 and 1 shot available"""
        ship = Ship(
            ship_type=ShipType.DESTROYER,
            coordinates=["A1", "A2"],
            orientation="horizontal",
            is_placed=True
        )
        assert ship.length == 2
        assert ship.shots_available == 1

    def test_total_shots_available(self) -> None:
        """All ships together provide 6 shots per round"""
        ships = [
            Ship(ShipType.CARRIER, [], "", False),
            Ship(ShipType.BATTLESHIP, [], "", False),
            Ship(ShipType.CRUISER, [], "", False),
            Ship(ShipType.SUBMARINE, [], "", False),
            Ship(ShipType.DESTROYER, [], "", False),
        ]
        total_shots = sum(ship.shots_available for ship in ships)
        assert total_shots == 6
