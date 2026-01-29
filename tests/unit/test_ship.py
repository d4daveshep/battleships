from game.model import Ship, ShipType, Coord, Orientation, GameBoard
from tests.unit.conftest import board_with_single_ship


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

    def test_get_ship_type_from_name(self):
        assert ShipType.from_ship_name("Carrier") == ShipType.CARRIER
        assert ShipType.from_ship_name("Battleship") == ShipType.BATTLESHIP
        assert ShipType.from_ship_name("Cruiser") == ShipType.CRUISER
        assert ShipType.from_ship_name("Submarine") == ShipType.SUBMARINE
        assert ShipType.from_ship_name("Destroyer") == ShipType.DESTROYER


class TestShip:
    def test_ship_creation(self) -> None:
        ship: Ship = Ship(ship_type=ShipType.CARRIER)
        assert ship.ship_type == ShipType.CARRIER
        assert ship.length == 5
        assert ship.shots_available == 2

    def test_ship_has_hits_set(self) -> None:
        """Test that Ship has a hits attribute."""
        ship: Ship = Ship(ship_type=ShipType.DESTROYER)
        assert hasattr(ship, "hits")
        assert isinstance(ship.hits, set)

    def test_ship_hits_initially_empty(self) -> None:
        """Test that hits set is empty on creation."""
        ship: Ship = Ship(ship_type=ShipType.DESTROYER)
        assert len(ship.hits) == 0

    def test_register_hit_adds_coord_to_hits(self) -> None:
        """Test that register_hit adds coordinate to hits if it's in positions."""
        board, ship = board_with_single_ship(
            ShipType.DESTROYER, Coord.A1, Orientation.HORIZONTAL
        )
        # Ship is at A1, A2

        # Register hit at A1
        result: bool = ship.register_hit(Coord.A1)
        assert result is True
        assert Coord.A1 in ship.hits
        assert len(ship.hits) == 1

    def test_register_hit_ignores_non_ship_coords(self) -> None:
        """Test that register_hit does nothing if coord not in positions."""
        board, ship = board_with_single_ship(
            ShipType.DESTROYER, Coord.A1, Orientation.HORIZONTAL
        )
        # Ship is at A1, A2

        # Try to register hit at B1 (not part of ship)
        result: bool = ship.register_hit(Coord.B1)
        assert result is False
        assert Coord.B1 not in ship.hits
        assert len(ship.hits) == 0

    def test_is_sunk_false_when_no_hits(self) -> None:
        """Test that is_sunk returns False when no hits."""
        board, ship = board_with_single_ship(
            ShipType.DESTROYER, Coord.A1, Orientation.HORIZONTAL
        )

        assert ship.is_sunk is False

    def test_is_sunk_false_when_partial_hits(self) -> None:
        """Test that is_sunk returns False when only some positions hit."""
        board, ship = board_with_single_ship(
            ShipType.DESTROYER, Coord.A1, Orientation.HORIZONTAL
        )
        # Ship is at A1, A2

        ship.register_hit(Coord.A1)
        assert ship.is_sunk is False

    def test_is_sunk_true_when_all_positions_hit(self) -> None:
        """Test that is_sunk returns True when all positions hit."""
        board, ship = board_with_single_ship(
            ShipType.DESTROYER, Coord.A1, Orientation.HORIZONTAL
        )
        # Ship is at A1, A2

        ship.register_hit(Coord.A1)
        ship.register_hit(Coord.A2)
        assert ship.is_sunk is True
