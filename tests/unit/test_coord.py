import pytest
from game.model import Coord


class TestCoordCreation:
    def test_create_coord_from_string(self):
        coord: Coord = Coord("A1")
        assert coord.row == "A"
        assert coord.col == 1
        assert coord.row_index == 1

    def test_coord_validation(self):
        assert False
