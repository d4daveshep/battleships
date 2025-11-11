from typing import NamedTuple, Type
import pytest
from game.model import Coord, CoordHelper, Orientation, CoordDetails


class TestCoord:
    def test_referencing_valid_coord(self):
        a1: Coord = Coord.A1
        assert a1.value == CoordDetails(1, 1)
        assert a1.name == "A1"
        assert a1.value.row_index == 1
        assert a1.value.col_index == 1

        d9: Coord = Coord.D9
        assert d9.value == CoordDetails(4, 9)
        assert d9.name == "D9"
        assert d9.value.row_index == 4
        assert d9.value.col_index == 9

    def test_referencing_invalid_coord_raises_attribute_error(self):
        with pytest.raises(AttributeError):
            Coord.K12

    def test_finding_coords_by_valid_reference(self):
        a1: Coord = Coord["A1"]
        assert a1.value == CoordDetails(1, 1)

        d9: Coord = Coord["D9"]
        assert d9.value == CoordDetails(4, 9)

    def test_finding_coords_by_invalid_reference_raises_key_error(self):
        with pytest.raises(KeyError):
            Coord["K12"]

        with pytest.raises(KeyError):
            Coord[""]


class TestCoordHelperFunctions:
    def test_finding_coords_by_valid_row_col_index(self):
        a1: Coord = CoordHelper.lookup(CoordDetails(row_index=1, col_index=1))
        assert a1.name == "A1"

        d9: Coord = CoordHelper.lookup((4, 9))
        assert d9.name == "D9"

    def test_finding_coords_by_invalid_rol_col_index_raises_key_error(self):
        with pytest.raises(KeyError):
            CoordHelper.lookup((0, 0))

        with pytest.raises(KeyError):
            CoordHelper.lookup((11, 3))

    def test_get_coords_by_length_and_orientation(self):
        start: Coord = Coord.A1
        length: int = 5
        orientation: Orientation = Orientation.HORIZONTAL

        coords: list[Coord] = CoordHelper.coords_for_length_and_orientation(
            start=start, length=length, orientation=orientation
        )
        assert len(coords) == length
        assert coords == [
            Coord.A1,
            Coord.A2,
            Coord.A3,
            Coord.A4,
            Coord.A5,
        ]
