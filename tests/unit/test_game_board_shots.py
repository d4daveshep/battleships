"""Unit tests for GameBoard shot recording functionality."""

import pytest
from game.model import GameBoard, Ship, ShipType, Coord, Orientation


class TestGameBoardShotRecording:
    """Test GameBoard shot recording methods."""

    def test_record_shot_received(self) -> None:
        """Test recording a shot received from opponent."""
        board = GameBoard()
        board.record_shot_received(Coord.A1, round_number=1)

        assert Coord.A1 in board.shots_received
        assert board.shots_received[Coord.A1] == 1

    def test_record_multiple_shots_received(self) -> None:
        """Test recording multiple shots received in same round."""
        board = GameBoard()
        board.record_shot_received(Coord.A1, round_number=1)
        board.record_shot_received(Coord.B2, round_number=1)
        board.record_shot_received(Coord.C3, round_number=1)

        assert len(board.shots_received) == 3
        assert board.shots_received[Coord.A1] == 1
        assert board.shots_received[Coord.B2] == 1
        assert board.shots_received[Coord.C3] == 1

    def test_record_shots_received_different_rounds(self) -> None:
        """Test recording shots received in different rounds."""
        board = GameBoard()
        board.record_shot_received(Coord.A1, round_number=1)
        board.record_shot_received(Coord.B2, round_number=2)
        board.record_shot_received(Coord.C3, round_number=3)

        assert board.shots_received[Coord.A1] == 1
        assert board.shots_received[Coord.B2] == 2
        assert board.shots_received[Coord.C3] == 3

    def test_record_shot_fired(self) -> None:
        """Test recording a shot fired at opponent."""
        board = GameBoard()
        board.record_shot_fired(Coord.E5, round_number=1)

        assert Coord.E5 in board.shots_fired
        assert board.shots_fired[Coord.E5] == 1

    def test_record_multiple_shots_fired(self) -> None:
        """Test recording multiple shots fired in same round."""
        board = GameBoard()
        board.record_shot_fired(Coord.E5, round_number=1)
        board.record_shot_fired(Coord.F6, round_number=1)
        board.record_shot_fired(Coord.G7, round_number=1)

        assert len(board.shots_fired) == 3
        assert board.shots_fired[Coord.E5] == 1
        assert board.shots_fired[Coord.F6] == 1

    def test_record_shots_fired_different_rounds(self) -> None:
        """Test recording shots fired in different rounds."""
        board = GameBoard()
        board.record_shot_fired(Coord.E5, round_number=1)
        board.record_shot_fired(Coord.F6, round_number=2)
        board.record_shot_fired(Coord.G7, round_number=3)

        assert board.shots_fired[Coord.E5] == 1
        assert board.shots_fired[Coord.F6] == 2
        assert board.shots_fired[Coord.G7] == 3


class TestGameBoardShotsAvailable:
    """Test GameBoard shots available calculation."""

    def test_calculate_shots_available_all_ships(self) -> None:
        """Test shots available with all 5 ships placed."""
        board = GameBoard()
        # Place all 5 ships
        board.place_ship(Ship(ShipType.CARRIER), Coord.A1, Orientation.HORIZONTAL)
        board.place_ship(Ship(ShipType.BATTLESHIP), Coord.C1, Orientation.HORIZONTAL)
        board.place_ship(Ship(ShipType.CRUISER), Coord.E1, Orientation.HORIZONTAL)
        board.place_ship(Ship(ShipType.SUBMARINE), Coord.G1, Orientation.HORIZONTAL)
        board.place_ship(Ship(ShipType.DESTROYER), Coord.I1, Orientation.HORIZONTAL)

        # Total: Carrier(2) + Battleship(1) + Cruiser(1) + Submarine(1) + Destroyer(1) = 6
        assert board.calculate_shots_available() == 6

    def test_calculate_shots_available_no_ships(self) -> None:
        """Test shots available with no ships placed."""
        board = GameBoard()

        assert board.calculate_shots_available() == 0

    def test_calculate_shots_available_partial_ships(self) -> None:
        """Test shots available with some ships placed."""
        board = GameBoard()
        board.place_ship(Ship(ShipType.CARRIER), Coord.A1, Orientation.HORIZONTAL)
        board.place_ship(Ship(ShipType.DESTROYER), Coord.C1, Orientation.HORIZONTAL)

        # Total: Carrier(2) + Destroyer(1) = 3
        assert board.calculate_shots_available() == 3

    def test_calculate_shots_available_excludes_sunk_ships(self) -> None:
        """Test that sunk ships do not contribute to available shots."""
        board = GameBoard()
        board.place_ship(Ship(ShipType.CARRIER), Coord.A1, Orientation.HORIZONTAL)
        board.place_ship(Ship(ShipType.DESTROYER), Coord.C1, Orientation.HORIZONTAL)
        
        # Initially 3 shots
        assert board.calculate_shots_available() == 3
        
        # Sink the Destroyer (length 2)
        board.record_hit(ShipType.DESTROYER, Coord.C1, round_number=1)
        board.record_hit(ShipType.DESTROYER, Coord.C2, round_number=2)
        
        # Now should only have 2 shots (from Carrier)
        assert board.calculate_shots_available() == 2
