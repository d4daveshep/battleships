from typing import Any

import pytest

from game.model import (
    Coord,
    GameBoard,
    Ship,
    ShipType,
    Orientation,
    GameBoardHelper,
    ShipAlreadyPlacedError,
    ShipPlacementOutOfBoundsError,
    ShipPlacementTooCloseError,
    ShotInfo,
    ShipHitData,
)
from tests.unit.conftest import board_with_single_ship


class TestShotInfo:
    """Tests for ShotInfo NamedTuple."""

    def test_shot_info_creation(self) -> None:
        """Test that ShotInfo can be created with all required fields."""
        shot_info: ShotInfo = ShotInfo(
            round_number=3,
            is_hit=True,
            ship_type=ShipType.CARRIER,
        )
        assert shot_info.round_number == 3
        assert shot_info.is_hit is True
        assert shot_info.ship_type == ShipType.CARRIER

    def test_shot_info_creation_with_miss(self) -> None:
        """Test that ShotInfo can be created for a miss (no ship_type)."""
        shot_info: ShotInfo = ShotInfo(
            round_number=1,
            is_hit=False,
            ship_type=None,
        )
        assert shot_info.round_number == 1
        assert shot_info.is_hit is False
        assert shot_info.ship_type is None

    def test_shot_info_is_immutable(self) -> None:
        """Test that ShotInfo is immutable (NamedTuple)."""
        shot_info: ShotInfo = ShotInfo(
            round_number=2,
            is_hit=True,
            ship_type=ShipType.DESTROYER,
        )
        with pytest.raises(AttributeError):
            shot_info.round_number = 5  # type: ignore


class TestGameBoard:
    def test_board_creation(self) -> None:
        board: GameBoard = GameBoard()
        assert len(board.ships) == 0
        assert len(board.shots_received) == 0
        assert len(board.shots_fired) == 0

    def test_shots_received_stores_shot_info(self) -> None:
        """Test that shots_received is dict[Coord, ShotInfo]."""
        # Place a ship so we can test hits
        board, ship = board_with_single_ship(
            ShipType.DESTROYER, Coord.A1, Orientation.HORIZONTAL
        )

        # Receive shots (one hit, one miss)
        board.receive_shots({Coord.A1, Coord.B1}, round_number=1)

        # Verify shots_received contains ShotInfo objects
        assert len(board.shots_received) == 2
        assert Coord.A1 in board.shots_received
        assert Coord.B1 in board.shots_received

        # Check the hit shot
        hit_info: ShotInfo = board.shots_received[Coord.A1]
        assert isinstance(hit_info, ShotInfo)
        assert hit_info.round_number == 1
        assert hit_info.is_hit is True
        assert hit_info.ship_type == ShipType.DESTROYER

        # Check the miss shot
        miss_info: ShotInfo = board.shots_received[Coord.B1]
        assert isinstance(miss_info, ShotInfo)
        assert miss_info.round_number == 1
        assert miss_info.is_hit is False
        assert miss_info.ship_type is None

    def test_receive_shots_with_multiple_rounds(self) -> None:
        """Test that receive_shots can be called multiple times with different rounds."""
        board: GameBoard = GameBoard()

        # Round 1
        board.receive_shots({Coord.A1}, round_number=1)
        assert board.shots_received[Coord.A1].round_number == 1

        # Round 2
        board.receive_shots({Coord.B2}, round_number=2)
        assert board.shots_received[Coord.B2].round_number == 2

        # Both shots should be tracked
        assert len(board.shots_received) == 2

    def test_shots_fired_stores_shot_info(self) -> None:
        """Test that shots_fired is dict[Coord, ShotInfo]."""
        board: GameBoard = GameBoard()

        # Record fired shots
        board.record_fired_shots({Coord.A1, Coord.B2}, round_number=1)

        # Verify shots_fired contains ShotInfo objects
        assert len(board.shots_fired) == 2
        assert Coord.A1 in board.shots_fired
        assert Coord.B2 in board.shots_fired

        # Check shot info (we don't know if hits yet, just that shots were fired)
        shot_a1: ShotInfo = board.shots_fired[Coord.A1]
        assert isinstance(shot_a1, ShotInfo)
        assert shot_a1.round_number == 1
        # For fired shots, hit status is unknown until opponent board is checked
        # So we'll just record is_hit=False as placeholder
        assert shot_a1.is_hit is False
        assert shot_a1.ship_type is None

    def test_record_fired_shots_with_multiple_rounds(self) -> None:
        """Test that record_fired_shots can be called multiple times."""
        board: GameBoard = GameBoard()

        # Round 1
        board.record_fired_shots({Coord.A1}, round_number=1)
        assert board.shots_fired[Coord.A1].round_number == 1

        # Round 2
        board.record_fired_shots({Coord.B2}, round_number=2)
        assert board.shots_fired[Coord.B2].round_number == 2

        # Both shots should be tracked
        assert len(board.shots_fired) == 2

    def test_has_ship_at_returns_true_for_ship_position(self) -> None:
        """Test that has_ship_at returns True when coordinate has a ship."""
        board, ship = board_with_single_ship(
            ShipType.DESTROYER, Coord.A1, Orientation.HORIZONTAL
        )

        # A1 and A2 have the destroyer
        assert board.has_ship_at(Coord.A1) is True
        assert board.has_ship_at(Coord.A2) is True

    def test_has_ship_at_returns_false_for_empty_position(self) -> None:
        """Test that has_ship_at returns False when coordinate is empty."""
        board, ship = board_with_single_ship(
            ShipType.DESTROYER, Coord.A1, Orientation.HORIZONTAL
        )

        # B1 is empty
        assert board.has_ship_at(Coord.B1) is False
        # C5 is empty
        assert board.has_ship_at(Coord.C5) is False

    def test_receive_shots_registers_hit_on_ship(self) -> None:
        """Test that receive_shots registers hits on the ship object."""
        board, ship = board_with_single_ship(
            ShipType.DESTROYER, Coord.A1, Orientation.HORIZONTAL
        )
        # Ship is at A1, A2

        # Receive shot at A1 (hit)
        board.receive_shots({Coord.A1}, round_number=1)

        # Verify hit was registered on ship
        assert Coord.A1 in ship.hits
        assert len(ship.hits) == 1
        assert ship.is_sunk is False

    def test_receive_shots_marks_ship_as_sunk(self) -> None:
        """Test that receive_shots marks ship as sunk when all positions hit."""
        board, ship = board_with_single_ship(
            ShipType.DESTROYER, Coord.A1, Orientation.HORIZONTAL
        )
        # Ship is at A1, A2

        # Receive both hits
        board.receive_shots({Coord.A1, Coord.A2}, round_number=1)

        # Verify ship is sunk
        assert Coord.A1 in ship.hits
        assert Coord.A2 in ship.hits
        assert ship.is_sunk is True

    def test_get_shots_received_by_round_returns_empty_for_no_shots(self) -> None:
        """Test that get_shots_received_by_round returns empty for rounds with no shots."""
        board: GameBoard = GameBoard()

        shots: set[Coord] = board.get_shots_received_by_round(1)
        assert len(shots) == 0

    def test_get_shots_received_by_round_returns_shots_for_round(self) -> None:
        """Test that get_shots_received_by_round returns shots for that round."""
        board: GameBoard = GameBoard()

        # Round 1
        board.receive_shots({Coord.A1, Coord.B1}, round_number=1)
        # Round 2
        board.receive_shots({Coord.C3}, round_number=2)

        # Get round 1 shots
        round1_shots: set[Coord] = board.get_shots_received_by_round(1)
        assert len(round1_shots) == 2
        assert Coord.A1 in round1_shots
        assert Coord.B1 in round1_shots

        # Get round 2 shots
        round2_shots: set[Coord] = board.get_shots_received_by_round(2)
        assert len(round2_shots) == 1
        assert Coord.C3 in round2_shots

    def test_get_shots_fired_by_round(self) -> None:
        """Test that get_shots_fired_by_round returns shots for that round."""
        board: GameBoard = GameBoard()

        # Round 1
        board.record_fired_shots({Coord.A1}, round_number=1)
        # Round 2
        board.record_fired_shots({Coord.B2, Coord.C3}, round_number=2)

        # Get round 1 shots
        round1_shots: set[Coord] = board.get_shots_fired_by_round(1)
        assert len(round1_shots) == 1
        assert Coord.A1 in round1_shots

        # Get round 2 shots
        round2_shots: set[Coord] = board.get_shots_fired_by_round(2)
        assert len(round2_shots) == 2
        assert Coord.B2 in round2_shots
        assert Coord.C3 in round2_shots

    def test_get_hits_made_returns_ship_hit_data(self) -> None:
        """Test that get_hits_made returns hit tracking data for opponent's ships."""
        # Player's board (who fired the shots)
        player_board: GameBoard = GameBoard()

        # Opponent's board with ships
        opponent_board: GameBoard = GameBoard()
        destroyer: Ship = Ship(ShipType.DESTROYER)
        carrier: Ship = Ship(ShipType.CARRIER)
        opponent_board.place_ship(destroyer, Coord.A1, Orientation.HORIZONTAL)  # A1, A2
        opponent_board.place_ship(carrier, Coord.C1, Orientation.HORIZONTAL)  # C1-C5

        # Round 1: Player fires and opponent receives
        player_board.record_fired_shots({Coord.A1}, round_number=1)
        opponent_board.receive_shots({Coord.A1}, round_number=1)

        # Round 2: Player fires and opponent receives
        player_board.record_fired_shots({Coord.C1, Coord.D1}, round_number=2)
        opponent_board.receive_shots({Coord.C1, Coord.D1}, round_number=2)

        # Round 3: Player fires and opponent receives (sinks Destroyer)
        player_board.record_fired_shots({Coord.A2, Coord.C2}, round_number=3)
        opponent_board.receive_shots({Coord.A2, Coord.C2}, round_number=3)

        # Get hits made (need to pass opponent board to determine hits)
        hits_made: dict[str, ShipHitData] = player_board.get_hits_made(opponent_board)

        # Should have entries for all 5 ship types
        assert len(hits_made) == 5
        assert "Destroyer" in hits_made
        assert "Carrier" in hits_made
        assert "Battleship" in hits_made
        assert "Cruiser" in hits_made
        assert "Submarine" in hits_made

        # Check Destroyer (sunk)
        destroyer_data: ShipHitData = hits_made["Destroyer"]
        assert destroyer_data.is_sunk is True
        assert len(destroyer_data.hits) == 2
        assert ("A1", 1) in destroyer_data.hits
        assert ("A2", 3) in destroyer_data.hits

        # Check Carrier (not sunk)
        carrier_data: ShipHitData = hits_made["Carrier"]
        assert carrier_data.is_sunk is False
        assert len(carrier_data.hits) == 2
        assert ("C1", 2) in carrier_data.hits
        assert ("C2", 3) in carrier_data.hits

        # Check unhit ships (no hits)
        assert hits_made["Battleship"].hits == []
        assert hits_made["Cruiser"].hits == []
        assert hits_made["Submarine"].hits == []

    valid_horizontal_ship_placement_data: list[
        tuple[ShipType, Coord, Orientation, list[Coord]]
    ] = [
        (
            ShipType.CARRIER,
            Coord.A1,
            Orientation.HORIZONTAL,
            [Coord.A1, Coord.A2, Coord.A3, Coord.A4, Coord.A5],
        ),
        (
            ShipType.BATTLESHIP,
            Coord.C1,
            Orientation.HORIZONTAL,
            [Coord.C1, Coord.C2, Coord.C3, Coord.C4],
        ),
        (
            ShipType.CRUISER,
            Coord.E1,
            Orientation.HORIZONTAL,
            [Coord.E1, Coord.E2, Coord.E3],
        ),
        (
            ShipType.SUBMARINE,
            Coord.G1,
            Orientation.HORIZONTAL,
            [Coord.G1, Coord.G2, Coord.G3],
        ),
        (ShipType.DESTROYER, Coord.I1, Orientation.HORIZONTAL, [Coord.I1, Coord.I2]),
    ]

    def test_place_all_ships_in_valid_horizontal_positions(self):
        board: GameBoard = GameBoard()
        for ship_data in self.valid_horizontal_ship_placement_data:
            ship_type, start, orientation, expected_coords = ship_data
            ship: Ship = Ship(ship_type)
            result: bool = board.place_ship(ship, start, orientation)
            assert result is True
            assert ship in board.ships
            assert ship.positions == expected_coords

        assert len(board.ships) == 5
        assert len(board._invalid_coords()) == 44

    def test_place_ship_invalid_position_out_of_bounds(self):
        board: GameBoard = GameBoard()
        destroyer: Ship = Ship(ship_type=ShipType.DESTROYER)
        with pytest.raises(ShipPlacementOutOfBoundsError):
            board.place_ship(
                ship=destroyer, start=Coord.J10, orientation=Orientation.HORIZONTAL
            )
        assert len(board.ships) == 0
        assert destroyer not in board.ships

        assert destroyer.positions == []

    def test_cant_place_duplicate_ship_type(self):
        board: GameBoard = GameBoard()
        destroyer_1: Ship = Ship(ship_type=ShipType.DESTROYER)

        result: bool = board.place_ship(
            ship=destroyer_1, start=Coord.A1, orientation=Orientation.HORIZONTAL
        )
        assert result is True
        assert len(board.ships) == 1
        assert destroyer_1 in board.ships

        # place duplicate ship typeat different location
        destroyer_2: Ship = Ship(ShipType.DESTROYER)
        with pytest.raises(ShipAlreadyPlacedError):
            board.place_ship(
                ship=destroyer_2, start=Coord.C1, orientation=Orientation.HORIZONTAL
            )
        # check original ship is still in place
        assert len(board.ships) == 1
        assert destroyer_1 in board.ships
        assert destroyer_1.positions == [Coord.A1, Coord.A2]

        # check duplicate ship is not added
        assert destroyer_2 not in board.ships
        assert destroyer_2.positions == []

    def test_place_ships_with_close_spacing(self):
        board: GameBoard = GameBoard()
        cruiser: Ship = Ship(ShipType.CRUISER)
        sub: Ship = Ship(ShipType.SUBMARINE)
        board.place_ship(cruiser, Coord.D4, Orientation.DIAGONAL_DOWN)
        board.place_ship(sub, Coord.D7, Orientation.HORIZONTAL)

        assert board.ships == [cruiser, sub]

    def test_cant_place_ships_touching(self):
        board: GameBoard = GameBoard()
        cruiser: Ship = Ship(ShipType.CRUISER)
        sub: Ship = Ship(ShipType.SUBMARINE)
        board.place_ship(cruiser, Coord.D4, Orientation.DIAGONAL_DOWN)
        assert Coord.D6 in board._invalid_coords()
        # try to place Sub touching Cruiser
        with pytest.raises(ShipPlacementTooCloseError) as err:
            board.place_ship(sub, Coord.D6, Orientation.HORIZONTAL)

        assert board.ships == [cruiser]
        assert "too close to another ship" in str(err.value)

    def test_cant_place_ships_overlapping(self):
        board: GameBoard = GameBoard()
        cruiser: Ship = Ship(ShipType.CRUISER)
        sub: Ship = Ship(ShipType.SUBMARINE)
        board.place_ship(cruiser, Coord.D4, Orientation.DIAGONAL_DOWN)
        # try to place Sub overlapping Cruiser
        with pytest.raises(ShipPlacementTooCloseError) as err:
            board.place_ship(sub, Coord.E5, Orientation.HORIZONTAL)

        assert board.ships == [cruiser]
        assert "too close to another ship" in str(err.value)

    def test_no_invalid_coords_with_no_ships_placed(self):
        board: GameBoard = GameBoard()
        invalid_coords: set[Coord] = board._invalid_coords()
        assert len(invalid_coords) == 0

    def test_ship_type_at_empty_coord(self):
        board: GameBoard = GameBoard()
        assert board.ship_type_at(Coord.A1) is None

    def test_ship_type_at_ship_coord(self):
        board: GameBoard = GameBoard()
        board.place_ship(Ship(ShipType.CRUISER), Coord.D4, Orientation.HORIZONTAL)
        assert board.ship_type_at(Coord.D4) == ShipType.CRUISER
        assert board.ship_type_at(Coord.D6) == ShipType.CRUISER

    def test_get_placed_ships_for_display_empty_board(self):
        """Test get_placed_ships_for_display returns empty dict for empty board"""
        board: GameBoard = GameBoard()
        result = board.get_placed_ships_for_display()
        assert result == {}

    def test_get_placed_ships_for_display_single_ship(self):
        """Test get_placed_ships_for_display with one ship"""
        board: GameBoard = GameBoard()
        carrier = Ship(ShipType.CARRIER)
        board.place_ship(carrier, Coord.A1, Orientation.HORIZONTAL)

        result = board.get_placed_ships_for_display()

        assert "Carrier" in result
        assert result["Carrier"]["cells"] == ["A1", "A2", "A3", "A4", "A5"]
        assert result["Carrier"]["code"] == "A"

    def test_get_placed_ships_for_display_multiple_ships(self):
        """Test get_placed_ships_for_display with multiple ships"""
        board: GameBoard = GameBoard()
        carrier = Ship(ShipType.CARRIER)
        battleship = Ship(ShipType.BATTLESHIP)
        destroyer = Ship(ShipType.DESTROYER)

        board.place_ship(carrier, Coord.A1, Orientation.HORIZONTAL)
        board.place_ship(battleship, Coord.C1, Orientation.VERTICAL)
        board.place_ship(destroyer, Coord.E5, Orientation.HORIZONTAL)

        result = board.get_placed_ships_for_display()

        assert len(result) == 3
        assert "Carrier" in result
        assert "Battleship" in result
        assert "Destroyer" in result

        assert result["Carrier"]["cells"] == ["A1", "A2", "A3", "A4", "A5"]
        assert result["Battleship"]["cells"] == ["C1", "D1", "E1", "F1"]
        assert result["Destroyer"]["cells"] == ["E5", "E6"]


class TestGameBoardHelper:
    def test_print_empty_board(self):
        board: GameBoard = GameBoard()
        output: list[str] = GameBoardHelper.print(board)
        assert len(output) == 12
        assert output[0] == "  1 2 3 4 5 6 7 8 9 10"
        assert output[1] == "-|--------------------"
        assert output[2] == "A|. . . . . . . . . . "
        assert output[9] == "H|. . . . . . . . . . "

    def test_print_board_with_2_ships(self):
        board: GameBoard = GameBoard()
        carrier: Ship = Ship(ShipType.CARRIER)
        sub: Ship = Ship(ShipType.SUBMARINE)
        board.place_ship(carrier, Coord.B2, Orientation.DIAGONAL_DOWN)
        board.place_ship(sub, Coord.H3, Orientation.HORIZONTAL)

        output: list[str] = GameBoardHelper.print(board)
        assert len(output) == 12
        assert output[2] == "A|. . . . . . . . . . "
        assert output[3] == "B|. A . . . . . . . . "
        assert output[4] == "C|. . A . . . . . . . "
        assert output[5] == "D|. . . A . . . . . . "
        assert output[6] == "E|. . . . A . . . . . "
        assert output[7] == "F|. . . . . A . . . . "
        assert output[8] == "G|. . . . . . . . . . "
        assert output[9] == "H|. . S S S . . . . . "
        assert output[10] == "I|. . . . . . . . . . "
        assert output[11] == "J|. . . . . . . . . . "

        print()
        for line in output:
            print(line)

        output: list[str] = GameBoardHelper.print(board, show_invalid=True)
        assert len(output) == 12
        assert output[2] == "A|x x x . . . . . . . "
        assert output[3] == "B|x A x x . . . . . . "
        assert output[4] == "C|x x A x x . . . . . "
        assert output[5] == "D|. x x A x x . . . . "
        assert output[6] == "E|. . x x A x x . . . "
        assert output[7] == "F|. . . x x A x . . . "
        assert output[8] == "G|. x x x x x x . . . "
        assert output[9] == "H|. x S S S x . . . . "
        assert output[10] == "I|. x x x x x . . . . "
        assert output[11] == "J|. . . . . . . . . . "

        print()
        for line in output:
            print(line)


class TestShipPlacementExceptionMessages:
    """Test that ship placement exceptions have user-friendly messages"""

    def test_out_of_bounds_error_has_user_message(self):
        """Test ShipPlacementOutOfBoundsError has user_message property"""
        board = GameBoard()
        carrier = Ship(ShipType.CARRIER)

        with pytest.raises(ShipPlacementOutOfBoundsError) as exc_info:
            board.place_ship(carrier, Coord.A8, Orientation.HORIZONTAL)

        assert hasattr(exc_info.value, "user_message")
        assert exc_info.value.user_message == "Ship placement goes outside the board"

    def test_overlap_error_has_user_message(self):
        """Test ShipPlacementTooCloseError for overlap has correct user_message"""
        board = GameBoard()
        carrier1 = Ship(ShipType.CARRIER)
        carrier2 = Ship(ShipType.BATTLESHIP)  # Different type to avoid duplicate error

        board.place_ship(carrier1, Coord.A1, Orientation.HORIZONTAL)

        with pytest.raises(ShipPlacementTooCloseError) as exc_info:
            # Try to place ship on same position (overlap)
            board.place_ship(carrier2, Coord.A1, Orientation.HORIZONTAL)

        assert hasattr(exc_info.value, "user_message")
        assert exc_info.value.user_message == "Ships cannot overlap"

    def test_touching_error_has_user_message(self):
        """Test ShipPlacementTooCloseError for touching has correct user_message"""
        board = GameBoard()
        carrier = Ship(ShipType.CARRIER)
        battleship = Ship(ShipType.BATTLESHIP)

        board.place_ship(carrier, Coord.A1, Orientation.HORIZONTAL)

        with pytest.raises(ShipPlacementTooCloseError) as exc_info:
            # Try to place ship adjacent (touching but not overlapping)
            board.place_ship(battleship, Coord.B1, Orientation.HORIZONTAL)

        assert hasattr(exc_info.value, "user_message")
        assert exc_info.value.user_message == "Ships must have empty space around them"

    def test_already_placed_error_has_user_message(self):
        """Test ShipAlreadyPlacedError has user_message property"""
        board = GameBoard()
        carrier1 = Ship(ShipType.CARRIER)
        carrier2 = Ship(ShipType.CARRIER)

        board.place_ship(carrier1, Coord.A1, Orientation.HORIZONTAL)

        with pytest.raises(ShipAlreadyPlacedError) as exc_info:
            board.place_ship(carrier2, Coord.C1, Orientation.HORIZONTAL)

        assert hasattr(exc_info.value, "user_message")
        assert exc_info.value.user_message == "Ships must have empty space around them"
