import pytest
from game.model import Coord, Orientation


class TestCoordCreation:
    def test_create_coord_from_string(self):
        coord: Coord = Coord("A1")
        assert coord.row == "A"
        assert coord.col == 1
        assert coord.row_index == 1

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

    @pytest.mark.parametrize("coord, expected", validation_test_data)
    def test_coord_validation_on_creation(self, coord: str, expected: bool):
        if expected:
            Coord(coord)
        else:
            with pytest.raises(ValueError):
                Coord(coord)


class TestCoordHelperFunctions:
    def test_get_coords_for_ship_placement(self):
        start: Coord = Coord("A1")
        length: int = 5
        orientation: Orientation = Orientation.HORIZONTAL

        coords: list[Coord] = start.coords_for_length_and_orientation(
            start=start, length=length, orientation=orientation
        )
        assert len(coords) == length
        assert coords == [
            Coord("A1"),
            Coord("A2"),
            Coord("A3"),
            Coord("A4"),
            Coord("A5"),
        ]


from enum import Enum

coords: dict[str, tuple[str, int, int]] = {
    f"{row_letter}{row_number}": (row_letter, ord(row_letter) - 64, row_number)
    for row_letter in "ABCDEFGHIJ"
    for row_number in range(1, 11)
}


# CoordEnum = Enum("CoordEnum", coords)
class CoordEnum(Enum):
    pass


for key, value in coords.items():
    setattr(CoordEnum, key, value)


class TestCoordEnum:
    def test_coords(self):
        a1: CoordEnum = CoordEnum.A1
        assert a1 == ("A", 1, 1)

        d9: CoordEnum = CoordEnum.D9
        assert d9 == ("D", 4, 9)
