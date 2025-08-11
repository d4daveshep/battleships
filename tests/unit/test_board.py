from game.ship import Coordinate, Ship, ShipType, Direction
from game.board import GameBoard


class TestGameBoard:
    def test_board_creation(self):
        board: GameBoard = GameBoard()
        assert len(board.ships) == 0
        assert len(board.shots_received) == 0
        assert len(board.shots_fired) == 0

    def test_place_ship_valid(self):
        board = GameBoard()
        ship = Ship(ShipType.DESTROYER)

        result = board.place_ship(ship, Coordinate(0, 0), Direction.HORIZONTAL)
        assert result is True
        assert len(board.ships) == 1
        assert ship in board.ships
        assert len(ship.coordinates) == 2

    def test_place_ship_out_of_bounds(self):
        board = GameBoard()
        ship = Ship(ShipType.CARRIER)

        result = board.place_ship(ship, Coordinate(0, 6), Direction.HORIZONTAL)
        assert result is False
        assert len(board.ships) == 0
        assert len(ship.coordinates) == 0

    def test_place_ship_overlap(self):
        board = GameBoard()
        ship1 = Ship(ShipType.DESTROYER)
        ship2 = Ship(ShipType.CRUISER)

        # Place first ship
        board.place_ship(ship1, Coordinate(0, 0), Direction.HORIZONTAL)

        # Try to place second ship overlapping
        result = board.place_ship(ship2, Coordinate(0, 0), Direction.VERTICAL)
        assert result is False
        assert len(board.ships) == 1

    def test_place_ship_spacing_rule(self):
        board = GameBoard()
        ship1 = Ship(ShipType.DESTROYER)
        ship2 = Ship(ShipType.DESTROYER)

        # Place first ship at (0,0)-(0,1)
        board.place_ship(ship1, Coordinate(0, 0), Direction.HORIZONTAL)

        # Try to place second ship adjacent (violates spacing rule)
        result = board.place_ship(ship2, Coordinate(1, 0), Direction.HORIZONTAL)
        assert result is False

        # But should be able to place with proper spacing
        result = board.place_ship(ship2, Coordinate(2, 0), Direction.HORIZONTAL)
        assert result is True
        assert len(board.ships) == 2

    def test_get_all_occupied_positions(self):
        board = GameBoard()
        ship = Ship(ShipType.DESTROYER)
        board.place_ship(ship, Coordinate(0, 0), Direction.HORIZONTAL)

        occupied = board._get_all_occupied_positions()
        expected = {Coordinate(0, 0), Coordinate(0, 1)}
        assert occupied == expected

    def test_get_all_forbidden_positions(self):
        board = GameBoard()
        ship = Ship(ShipType.DESTROYER)
        board.place_ship(ship, Coordinate(1, 1), Direction.HORIZONTAL)

        forbidden = board._get_all_forbidden_positions()

        # Destroyer at (1,1)-(1,2), so forbidden positions should include all adjacent
        expected_forbidden = {
            Coordinate(0, 0),
            Coordinate(0, 1),
            Coordinate(0, 2),
            Coordinate(0, 3),
            Coordinate(1, 0),
            Coordinate(1, 3),
            Coordinate(2, 0),
            Coordinate(2, 1),
            Coordinate(2, 2),
            Coordinate(2, 3),
        }
        assert forbidden == expected_forbidden

    # def test_receive_shot_hit(self):
    #     board = GameBoard()
    #     ship = Ship(ShipType.DESTROYER)
    #     board.place_ship(ship, Coordinate(0, 0), Direction.HORIZONTAL)
    #
    #     # Hit the ship
    #     hit_ship = board.receive_shot(Coordinate(0, 0), 1)
    #     assert hit_ship == ship
    #     assert Coordinate(0, 0) in board.shots_received
    #     assert board.shots_received[Coordinate(0, 0)] == 1
    #     assert Coordinate(0, 0) in ship.hits
    #
    # def test_receive_shot_miss(self):
    #     board = GameBoard()
    #     ship = Ship(ShipType.DESTROYER)
    #     board.place_ship(ship, Coordinate(0, 0), Direction.HORIZONTAL)
    #
    #     # Miss the ship
    #     hit_ship = board.receive_shot(Coordinate(2, 2), 1)
    #     assert hit_ship is None
    #     assert Coordinate(2, 2) in board.shots_received
    #
    # def test_receive_shot_duplicate(self):
    #     board = GameBoard()
    #     board.receive_shot(Coordinate(0, 0), 1)
    #
    #     with pytest.raises(ValueError, match="already shot at"):
    #         board.receive_shot(Coordinate(0, 0), 2)
    #
    # def test_fire_shot(self):
    #     board = GameBoard()
    #     board.fire_shot(Coordinate(0, 0), 1)
    #
    #     assert Coordinate(0, 0) in board.shots_fired
    #     assert board.shots_fired[Coordinate(0, 0)] == 1
    #
    # def test_fire_shot_duplicate(self):
    #     board = GameBoard()
    #     board.fire_shot(Coordinate(0, 0), 1)
    #
    #     with pytest.raises(ValueError, match="Already fired at"):
    #         board.fire_shot(Coordinate(0, 0), 2)
    #
    # def test_get_ship_at_position(self):
    #     board = GameBoard()
    #     ship = Ship(ShipType.DESTROYER)
    #     board.place_ship(ship, Coordinate(0, 0), Direction.HORIZONTAL)
    #
    #     # Ship is at these positions
    #     assert board.get_ship_at_position(Coordinate(0, 0)) == ship
    #     assert board.get_ship_at_position(Coordinate(0, 1)) == ship
    #
    #     # No ship at this position
    #     assert board.get_ship_at_position(Coordinate(1, 1)) is None
    #
    def test_available_shots(self):
        board = GameBoard()

        # No ships
        assert board.available_shots == 0

        # Add ships
        carrier = Ship(ShipType.CARRIER)  # 2 shots
        destroyer = Ship(ShipType.DESTROYER)  # 1 shot
        board.place_ship(carrier, Coordinate(0, 0), Direction.HORIZONTAL)
        board.place_ship(destroyer, Coordinate(2, 0), Direction.HORIZONTAL)

        assert board.available_shots == 3

        # Sink destroyer
        destroyer.incoming_shot(Coordinate(2, 0))
        destroyer.incoming_shot(Coordinate(2, 1))

        assert board.available_shots == 2  # Only carrier shots remain

    # def test_get_sunk_ships(self):
    #     board = GameBoard()
    #     destroyer = Ship(ShipType.DESTROYER)
    #     carrier = Ship(ShipType.CARRIER)
    #
    #     board.place_ship(destroyer, Coordinate(0, 0), Direction.HORIZONTAL)
    #     board.place_ship(carrier, Coordinate(2, 0), Direction.HORIZONTAL)
    #
    #     # No ships sunk initially
    #     assert len(board.get_sunk_ships()) == 0
    #
    #     # Sink destroyer
    #     destroyer.incoming_shot(Coordinate(0, 0))
    #     destroyer.incoming_shot(Coordinate(0, 1))
    #
    #     sunk_ships = board.get_sunk_ships()
    #     assert len(sunk_ships) == 1
    #     assert destroyer in sunk_ships
    #
    # def test_get_unsunk_ships(self):
    #     board = GameBoard()
    #     destroyer = Ship(ShipType.DESTROYER)
    #     carrier = Ship(ShipType.CARRIER)
    #
    #     board.place_ship(destroyer, Coordinate(0, 0), Direction.HORIZONTAL)
    #     board.place_ship(carrier, Coordinate(2, 0), Direction.HORIZONTAL)
    #
    #     # All ships unsunk initially
    #     unsunk_ships = board.get_unsunk_ships()
    #     assert len(unsunk_ships) == 2
    #
    #     # Sink destroyer
    #     destroyer.incoming_shot(Coordinate(0, 0))
    #     destroyer.incoming_shot(Coordinate(0, 1))
    #
    #     unsunk_ships = board.get_unsunk_ships()
    #     assert len(unsunk_ships) == 1
    #     assert carrier in unsunk_ships
    #
    # def test_is_all_ships_sunk(self):
    #     board = GameBoard()
    #     destroyer = Ship(ShipType.DESTROYER)
    #     board.place_ship(destroyer, Coordinate(0, 0), Direction.HORIZONTAL)
    #
    #     assert not board.is_all_ships_sunk()
    #
    #     # Sink the ship
    #     destroyer.incoming_shot(Coordinate(0, 0))
    #     destroyer.incoming_shot(Coordinate(0, 1))
    #
    #     assert board.is_all_ships_sunk()
    #
    # def test_get_ship_positions(self):
    #     board = GameBoard()
    #     destroyer = Ship(ShipType.DESTROYER)
    #     carrier = Ship(ShipType.CARRIER)
    #
    #     board.place_ship(destroyer, Coordinate(0, 0), Direction.HORIZONTAL)
    #     board.place_ship(carrier, Coordinate(2, 0), Direction.HORIZONTAL)
    #
    #     positions = board.get_ship_positions()
    #     assert ShipType.DESTROYER in positions
    #     assert ShipType.CARRIER in positions
    #     assert len(positions[ShipType.DESTROYER]) == 2
    #     assert len(positions[ShipType.CARRIER]) == 5
    #
    def test_diagonal_ship_placement(self):
        board: GameBoard = GameBoard()
        ship: Ship = Ship(ShipType.CRUISER)  # Length 3

        # Test diagonal NE placement
        ship_placed: bool = board.place_ship(
            ship, Coordinate(2, 0), Direction.DIAGONAL_NE
        )
        assert ship_placed
        expected_coordinates: set[Coordinate] = {
            Coordinate(2, 0),
            Coordinate(1, 1),
            Coordinate(0, 2),
        }
        assert ship.coordinates == expected_coordinates

    def test_ship_spacing_diagonal(self):
        board: GameBoard = GameBoard()
        ship1: Ship = Ship(ShipType.DESTROYER)
        ship2: Ship = Ship(ShipType.DESTROYER)

        # Place first ship diagonally at (2,2)-(1,3)
        board.place_ship(ship1, Coordinate(2, 2), Direction.DIAGONAL_NE)

        # Try to place second ship adjacent (should be blocked)
        ship_placed: bool = board.place_ship(
            ship2, Coordinate(1, 2), Direction.HORIZONTAL
        )
        assert not ship_placed

        # Place with proper spacing
        ship_placed = board.place_ship(ship2, Coordinate(5, 5), Direction.HORIZONTAL)
        assert ship_placed
