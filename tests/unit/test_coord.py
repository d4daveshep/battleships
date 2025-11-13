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

    def test_get_adjacent_coords_to_single_central_coord(self):
        centre: Coord = Coord.D4
        expected: set[Coord] = {
            Coord.C3,
            Coord.C4,
            Coord.C5,
            Coord.D3,
            Coord.D5,
            Coord.E3,
            Coord.E4,
            Coord.E5,
        }
        adjacent_coords: set[Coord] = CoordHelper.coords_adjacent_to_a_coord(centre)
        assert adjacent_coords == expected

    def test_get_adjacent_coords_to_single_edge_coord(self):
        edge: Coord = Coord.D1
        expected: set[Coord] = {Coord.C1, Coord.C2, Coord.D2, Coord.E1, Coord.E2}
        adjacent_coords: set[Coord] = CoordHelper.coords_adjacent_to_a_coord(edge)
        assert adjacent_coords == expected

    def test_get_adjacent_coords_to_single_corner_coord(self):
        corner: Coord = Coord.A1
        expected: set[Coord] = {Coord.A2, Coord.B1, Coord.B2}
        adjacent_coords: set[Coord] = CoordHelper.coords_adjacent_to_a_coord(corner)
        assert adjacent_coords == expected

    def test_get_adjacent_coords_to_list_of_central_coords(self):
        centre: list[Coord] = [Coord.D4, Coord.D5, Coord.D6]
        expected: set[Coord] = {
            Coord.C3,
            Coord.C4,
            Coord.C5,
            Coord.C6,
            Coord.C7,
            Coord.D3,
            Coord.D7,
            Coord.E3,
            Coord.E4,
            Coord.E5,
            Coord.E6,
            Coord.E7,
        }
        adjacent_coords: set[Coord] = CoordHelper.coords_adjacent_to_a_coords_list(
            centre
        )
        assert adjacent_coords == expected

    def test_get_adjacent_coords_to_list_of_edge_coords(self):
        centre: list[Coord] = [Coord.D1, Coord.E1, Coord.F1]
        expected: set[Coord] = {
            Coord.C1,
            Coord.C2,
            Coord.D2,
            Coord.E2,
            Coord.F2,
            Coord.G1,
            Coord.G2,
        }
        adjacent_coords: set[Coord] = CoordHelper.coords_adjacent_to_a_coords_list(
            centre
        )
        assert adjacent_coords == expected

    def test_get_adjacent_coords_to_diagonal_list_of_coords(self):
        diagonal: list[Coord] = [Coord.D4, Coord.E5, Coord.F6]
        expected: set[Coord] = {
            Coord.C3,
            Coord.C4,
            Coord.C5,
            Coord.D3,
            Coord.D5,
            Coord.D6,
            Coord.E3,
            Coord.E4,
            Coord.E6,
            Coord.E7,
            Coord.F4,
            Coord.F5,
            Coord.F7,
            Coord.G5,
            Coord.G6,
            Coord.G7,
        }
        adjacent_coords: set[Coord] = CoordHelper.coords_adjacent_to_a_coords_list(
            diagonal
        )
        assert adjacent_coords == expected
