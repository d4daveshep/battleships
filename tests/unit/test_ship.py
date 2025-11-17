import pytest

from game.model import Ship, ShipType


class TestShipType:
    def test_all_ship_types_exist(self) -> None:
        types: set[ShipType] = set(ShipType)
        assert len(types) == 5
        assert types == {
            ShipType.BATTLESHIP,
            ShipType.CARRIER,
            ShipType.CRUISER,
            ShipType.DESTROYER,
            ShipType.SUBMARINE,
        }

    def test_ship_type_count(self) -> None:
        assert len(list(ShipType)) == 5

    def test_ship_type_properties(self) -> None:
        assert ShipType.CARRIER.ship_name == "Carrier"
        assert ShipType.CARRIER.length == 5
        assert ShipType.CARRIER.shots_available == 2
        assert ShipType.CARRIER.code == "A"

        assert ShipType.BATTLESHIP.ship_name == "Battleship"
        assert ShipType.BATTLESHIP.length == 4
        assert ShipType.BATTLESHIP.shots_available == 1
        assert ShipType.BATTLESHIP.code == "B"

        assert ShipType.CRUISER.ship_name == "Cruiser"
        assert ShipType.CRUISER.length == 3
        assert ShipType.CRUISER.shots_available == 1
        assert ShipType.CRUISER.code == "C"

        assert ShipType.SUBMARINE.ship_name == "Submarine"
        assert ShipType.SUBMARINE.length == 3
        assert ShipType.SUBMARINE.shots_available == 1
        assert ShipType.SUBMARINE.code == "S"

        assert ShipType.DESTROYER.ship_name == "Destroyer"
        assert ShipType.DESTROYER.length == 2
        assert ShipType.DESTROYER.shots_available == 1
        assert ShipType.DESTROYER.code == "D"


class TestShip:
    def test_ship_creation(self):
        ship: Ship = Ship(ship_type=ShipType.CARRIER)
        assert ship.ship_type == ShipType.CARRIER
        assert ship.length == 5
        assert ship.shots_available == 2
