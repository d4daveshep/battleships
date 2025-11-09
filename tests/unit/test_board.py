import pytest

from game.model import Coord, GameBoard, Ship, ShipType


class TestGameBoard:
    def test_board_creation(self):
        board: GameBoard = GameBoard()
        assert len(board.ships) == 0
        assert len(board.shots_received) == 0
        assert len(board.shots_fired) == 0

    def test_place_ship_valid(self):
        board: GameBoard = GameBoard()
        ship: Ship = Ship(ship_type=ShipType.DESTROYER)
        result: bool = board.place_ship(
            ship=ship, start=Coord("A1"), orientation=Orientation.HORIZONTAL
        )
        assert result is True
        assert len(board.ships) == 1
        assert ship in board.ships
