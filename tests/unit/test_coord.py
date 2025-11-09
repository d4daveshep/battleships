import pytest
from game.model import Coord

validation_test_data: list[tuple[str, bool]] = [
    # Valid coords
    ("A1", True),
    ("a1", True),
    ("E5", True),
    ("J10", True),
    # Invalid coords
    ("1A", False),
    ("A0", False),
    ("A11", False),
    ("K1", False),
    ("@#", False),
]


class TestCoordCreation:
    def test_create_coord_from_string(self):
        coord: Coord = Coord("A1")
        assert coord.row == "A"
        assert coord.col == 1
        assert coord.row_index == 1

    @pytest.mark.parametrize("coord, expected", validation_test_data)
    def test_coord_validation(self, coord: str, expected: bool):
        if expected:
            Coord(coord)
        else:
            with pytest.raises(ValueError):
                Coord(coord)
