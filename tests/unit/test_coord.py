from typing import NamedTuple, Type
import pytest
from game.model import Coord, CoordHelper, Orientation, CoordDetails


class TestCoord:
    def test_referencing_coords(self):
        a1: Coord = Coord.A1
        assert a1.value == CoordDetails(1, 1)
        assert a1.name == "A1"
        assert a1.value.row_index == 1
        assert a1.value.col_index == 1

    def test_finding_coords_by_reference(self):
        a1: Coord = Coord["A1"]
        assert a1.value == CoordDetails(1, 1)

    def test_finding_coords_by_row_col_index(self):
        a1: Coord = CoordHelper.lookup(CoordDetails(1, 1))
        assert a1.name == "A1"


class TestCoordHelperFunctions:
    def test_get_coords_for_ship_placement(self):
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
