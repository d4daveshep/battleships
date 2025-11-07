"""Unit tests for game/coord.py - Coordinate data structure"""

import pytest
from game.coord import Coord


class TestCoordCreation:
    """Tests for creating Coord objects"""

    def test_create_coord_from_string_A1(self) -> None:
        """Can create a Coord from string 'A1'"""
        coord = Coord.from_string("A1")
        assert coord.row == "A"
        assert coord.col == 1

    def test_create_coord_from_string_J10(self) -> None:
        """Can create a Coord from string 'J10'"""
        coord = Coord.from_string("J10")
        assert coord.row == "J"
        assert coord.col == 10

    def test_create_coord_from_string_E5(self) -> None:
        """Can create a Coord from string 'E5'"""
        coord = Coord.from_string("E5")
        assert coord.row == "E"
        assert coord.col == 5

    def test_create_coord_from_row_col(self) -> None:
        """Can create a Coord from row and column"""
        coord = Coord(row="B", col=3)
        assert coord.row == "B"
        assert coord.col == 3

    def test_coord_is_dataclass(self) -> None:
        """Coord is a dataclass"""
        coord = Coord(row="A", col=1)
        assert hasattr(Coord, "__dataclass_fields__")


class TestCoordValidation:
    """Tests for validating Coord values"""

    def test_reject_invalid_row_below_A(self) -> None:
        """Reject row before 'A'"""
        with pytest.raises(ValueError, match="Row must be A-J"):
            Coord(row="@", col=1)

    def test_reject_invalid_row_above_J(self) -> None:
        """Reject row after 'J'"""
        with pytest.raises(ValueError, match="Row must be A-J"):
            Coord(row="K", col=1)

    def test_reject_lowercase_row(self) -> None:
        """Reject lowercase row letters"""
        with pytest.raises(ValueError, match="Row must be A-J"):
            Coord(row="a", col=1)

    def test_reject_invalid_col_zero(self) -> None:
        """Reject column 0"""
        with pytest.raises(ValueError, match="Column must be 1-10"):
            Coord(row="A", col=0)

    def test_reject_invalid_col_negative(self) -> None:
        """Reject negative column"""
        with pytest.raises(ValueError, match="Column must be 1-10"):
            Coord(row="A", col=-1)

    def test_reject_invalid_col_above_10(self) -> None:
        """Reject column above 10"""
        with pytest.raises(ValueError, match="Column must be 1-10"):
            Coord(row="A", col=11)

    def test_reject_invalid_string_empty(self) -> None:
        """Reject empty string"""
        with pytest.raises(ValueError, match="Invalid coordinate format"):
            Coord.from_string("")

    def test_reject_invalid_string_no_number(self) -> None:
        """Reject string without number"""
        with pytest.raises(ValueError, match="Invalid coordinate format"):
            Coord.from_string("A")

    def test_reject_invalid_string_no_letter(self) -> None:
        """Reject string without letter"""
        with pytest.raises(ValueError, match="Invalid coordinate format"):
            Coord.from_string("10")

    def test_reject_invalid_string_multiple_letters(self) -> None:
        """Reject string with multiple letters"""
        with pytest.raises(ValueError, match="Invalid coordinate format"):
            Coord.from_string("AB5")

    def test_accept_all_valid_rows(self) -> None:
        """Accept all valid rows A-J"""
        valid_rows = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
        for row in valid_rows:
            coord = Coord(row=row, col=5)
            assert coord.row == row

    def test_accept_all_valid_columns(self) -> None:
        """Accept all valid columns 1-10"""
        for col in range(1, 11):
            coord = Coord(row="E", col=col)
            assert coord.col == col


class TestCoordEquality:
    """Tests for comparing Coord objects"""

    def test_coords_equal_same_values(self) -> None:
        """Two coords with same values are equal"""
        coord1 = Coord(row="A", col=1)
        coord2 = Coord(row="A", col=1)
        assert coord1 == coord2

    def test_coords_not_equal_different_row(self) -> None:
        """Two coords with different rows are not equal"""
        coord1 = Coord(row="A", col=1)
        coord2 = Coord(row="B", col=1)
        assert coord1 != coord2

    def test_coords_not_equal_different_col(self) -> None:
        """Two coords with different columns are not equal"""
        coord1 = Coord(row="A", col=1)
        coord2 = Coord(row="A", col=2)
        assert coord1 != coord2

    def test_coords_not_equal_different_row_and_col(self) -> None:
        """Two coords with different row and column are not equal"""
        coord1 = Coord(row="A", col=1)
        coord2 = Coord(row="B", col=2)
        assert coord1 != coord2


class TestCoordHashing:
    """Tests for using Coord in sets and dicts"""

    def test_coord_is_hashable(self) -> None:
        """Coord can be hashed"""
        coord = Coord(row="A", col=1)
        hash_value = hash(coord)
        assert isinstance(hash_value, int)

    def test_equal_coords_same_hash(self) -> None:
        """Equal coords have same hash"""
        coord1 = Coord(row="A", col=1)
        coord2 = Coord(row="A", col=1)
        assert hash(coord1) == hash(coord2)

    def test_coord_in_set(self) -> None:
        """Coord can be used in a set"""
        coord1 = Coord(row="A", col=1)
        coord2 = Coord(row="B", col=2)
        coord_set = {coord1, coord2}
        assert len(coord_set) == 2
        assert coord1 in coord_set
        assert coord2 in coord_set

    def test_coord_as_dict_key(self) -> None:
        """Coord can be used as dict key"""
        coord = Coord(row="A", col=1)
        coord_dict = {coord: "ship"}
        assert coord_dict[coord] == "ship"

    def test_duplicate_coords_in_set(self) -> None:
        """Duplicate coords are not added to set"""
        coord1 = Coord(row="A", col=1)
        coord2 = Coord(row="A", col=1)
        coord_set = {coord1, coord2}
        assert len(coord_set) == 1


class TestCoordSerialization:
    """Tests for converting Coord to/from strings"""

    def test_to_string_A1(self) -> None:
        """Convert Coord to string 'A1'"""
        coord = Coord(row="A", col=1)
        assert coord.to_string() == "A1"

    def test_to_string_J10(self) -> None:
        """Convert Coord to string 'J10'"""
        coord = Coord(row="J", col=10)
        assert coord.to_string() == "J10"

    def test_to_string_E5(self) -> None:
        """Convert Coord to string 'E5'"""
        coord = Coord(row="E", col=5)
        assert coord.to_string() == "E5"

    def test_str_representation(self) -> None:
        """Coord __str__ returns coordinate string"""
        coord = Coord(row="C", col=7)
        assert str(coord) == "C7"

    def test_repr_representation(self) -> None:
        """Coord __repr__ returns useful representation"""
        coord = Coord(row="D", col=4)
        repr_str = repr(coord)
        assert "Coord" in repr_str
        assert "D" in repr_str
        assert "4" in repr_str

    def test_round_trip_from_string_to_string(self) -> None:
        """Can convert string -> Coord -> string"""
        original = "F8"
        coord = Coord.from_string(original)
        result = coord.to_string()
        assert result == original


class TestCoordRowColConversion:
    """Tests for converting to row/col tuples and indices"""

    def test_to_indices_A1(self) -> None:
        """Convert A1 to 0-based indices (0, 0)"""
        coord = Coord(row="A", col=1)
        row_idx, col_idx = coord.to_indices()
        assert row_idx == 0
        assert col_idx == 0

    def test_to_indices_J10(self) -> None:
        """Convert J10 to 0-based indices (9, 9)"""
        coord = Coord(row="J", col=10)
        row_idx, col_idx = coord.to_indices()
        assert row_idx == 9
        assert col_idx == 9

    def test_to_indices_E5(self) -> None:
        """Convert E5 to 0-based indices (4, 4)"""
        coord = Coord(row="E", col=5)
        row_idx, col_idx = coord.to_indices()
        assert row_idx == 4
        assert col_idx == 4

    def test_from_indices_0_0(self) -> None:
        """Create Coord from indices (0, 0) -> A1"""
        coord = Coord.from_indices(0, 0)
        assert coord.row == "A"
        assert coord.col == 1

    def test_from_indices_9_9(self) -> None:
        """Create Coord from indices (9, 9) -> J10"""
        coord = Coord.from_indices(9, 9)
        assert coord.row == "J"
        assert coord.col == 10

    def test_from_indices_4_4(self) -> None:
        """Create Coord from indices (4, 4) -> E5"""
        coord = Coord.from_indices(4, 4)
        assert coord.row == "E"
        assert coord.col == 5

    def test_round_trip_indices(self) -> None:
        """Can convert indices -> Coord -> indices"""
        original_row, original_col = 3, 7
        coord = Coord.from_indices(original_row, original_col)
        result_row, result_col = coord.to_indices()
        assert result_row == original_row
        assert result_col == original_col


class TestCoordDistance:
    """Tests for calculating distance between coordinates"""

    def test_distance_horizontal_adjacent(self) -> None:
        """Distance between A1 and A2 is 1"""
        coord1 = Coord(row="A", col=1)
        coord2 = Coord(row="A", col=2)
        assert coord1.distance_to(coord2) == 1

    def test_distance_vertical_adjacent(self) -> None:
        """Distance between A1 and B1 is 1"""
        coord1 = Coord(row="A", col=1)
        coord2 = Coord(row="B", col=1)
        assert coord1.distance_to(coord2) == 1

    def test_distance_diagonal_adjacent(self) -> None:
        """Distance between A1 and B2 is 1 (diagonal)"""
        coord1 = Coord(row="A", col=1)
        coord2 = Coord(row="B", col=2)
        assert coord1.distance_to(coord2) == 1

    def test_distance_horizontal_multiple(self) -> None:
        """Distance between A1 and A5 is 4"""
        coord1 = Coord(row="A", col=1)
        coord2 = Coord(row="A", col=5)
        assert coord1.distance_to(coord2) == 4

    def test_distance_vertical_multiple(self) -> None:
        """Distance between A1 and E1 is 4"""
        coord1 = Coord(row="A", col=1)
        coord2 = Coord(row="E", col=1)
        assert coord1.distance_to(coord2) == 4

    def test_distance_diagonal_multiple(self) -> None:
        """Distance between A1 and D4 is 3 (diagonal)"""
        coord1 = Coord(row="A", col=1)
        coord2 = Coord(row="D", col=4)
        assert coord1.distance_to(coord2) == 3

    def test_distance_to_self(self) -> None:
        """Distance from coord to itself is 0"""
        coord = Coord(row="E", col=5)
        assert coord.distance_to(coord) == 0

    def test_distance_is_symmetric(self) -> None:
        """Distance from A to B equals distance from B to A"""
        coord1 = Coord(row="C", col=3)
        coord2 = Coord(row="F", col=7)
        assert coord1.distance_to(coord2) == coord2.distance_to(coord1)


class TestCoordOrientation:
    """Tests for determining orientation between coordinates"""

    def test_orientation_horizontal(self) -> None:
        """A1 to A5 is horizontal"""
        coord1 = Coord(row="A", col=1)
        coord2 = Coord(row="A", col=5)
        assert coord1.orientation_to(coord2) == "horizontal"

    def test_orientation_vertical(self) -> None:
        """A1 to E1 is vertical"""
        coord1 = Coord(row="A", col=1)
        coord2 = Coord(row="E", col=1)
        assert coord1.orientation_to(coord2) == "vertical"

    def test_orientation_diagonal_down_right(self) -> None:
        """A1 to C3 is diagonal"""
        coord1 = Coord(row="A", col=1)
        coord2 = Coord(row="C", col=3)
        assert coord1.orientation_to(coord2) == "diagonal"

    def test_orientation_diagonal_down_left(self) -> None:
        """A10 to C8 is diagonal"""
        coord1 = Coord(row="A", col=10)
        coord2 = Coord(row="C", col=8)
        assert coord1.orientation_to(coord2) == "diagonal"

    def test_orientation_diagonal_up_right(self) -> None:
        """E3 to C5 is diagonal"""
        coord1 = Coord(row="E", col=3)
        coord2 = Coord(row="C", col=5)
        assert coord1.orientation_to(coord2) == "diagonal"

    def test_orientation_diagonal_up_left(self) -> None:
        """E5 to C3 is diagonal"""
        coord1 = Coord(row="E", col=5)
        coord2 = Coord(row="C", col=3)
        assert coord1.orientation_to(coord2) == "diagonal"

    def test_orientation_invalid_not_aligned(self) -> None:
        """A1 to B3 is not horizontal, vertical, or diagonal"""
        coord1 = Coord(row="A", col=1)
        coord2 = Coord(row="B", col=3)
        assert coord1.orientation_to(coord2) == "invalid"

    def test_orientation_same_coord(self) -> None:
        """Orientation from coord to itself is invalid"""
        coord = Coord(row="E", col=5)
        assert coord.orientation_to(coord) == "invalid"

    def test_orientation_is_symmetric(self) -> None:
        """Orientation from A to B equals orientation from B to A"""
        coord1 = Coord(row="C", col=3)
        coord2 = Coord(row="C", col=7)
        assert coord1.orientation_to(coord2) == coord2.orientation_to(coord1)


class TestCoordRange:
    """Tests for generating coordinate ranges"""

    def test_range_horizontal_A1_to_A5(self) -> None:
        """Generate range from A1 to A5 horizontally"""
        coord1 = Coord(row="A", col=1)
        coord2 = Coord(row="A", col=5)
        coords = coord1.range_to(coord2)
        expected = [
            Coord(row="A", col=1),
            Coord(row="A", col=2),
            Coord(row="A", col=3),
            Coord(row="A", col=4),
            Coord(row="A", col=5),
        ]
        assert coords == expected

    def test_range_vertical_A1_to_E1(self) -> None:
        """Generate range from A1 to E1 vertically"""
        coord1 = Coord(row="A", col=1)
        coord2 = Coord(row="E", col=1)
        coords = coord1.range_to(coord2)
        expected = [
            Coord(row="A", col=1),
            Coord(row="B", col=1),
            Coord(row="C", col=1),
            Coord(row="D", col=1),
            Coord(row="E", col=1),
        ]
        assert coords == expected

    def test_range_diagonal_A1_to_C3(self) -> None:
        """Generate range from A1 to C3 diagonally"""
        coord1 = Coord(row="A", col=1)
        coord2 = Coord(row="C", col=3)
        coords = coord1.range_to(coord2)
        expected = [
            Coord(row="A", col=1),
            Coord(row="B", col=2),
            Coord(row="C", col=3),
        ]
        assert coords == expected

    def test_range_diagonal_A10_to_B9(self) -> None:
        """Generate range from A10 to B9 diagonally (down-left)"""
        coord1 = Coord(row="A", col=10)
        coord2 = Coord(row="B", col=9)
        coords = coord1.range_to(coord2)
        expected = [
            Coord(row="A", col=10),
            Coord(row="B", col=9),
        ]
        assert coords == expected

    def test_range_reverse_direction_horizontal(self) -> None:
        """Generate range from A5 to A1 (reverse)"""
        coord1 = Coord(row="A", col=5)
        coord2 = Coord(row="A", col=1)
        coords = coord1.range_to(coord2)
        expected = [
            Coord(row="A", col=5),
            Coord(row="A", col=4),
            Coord(row="A", col=3),
            Coord(row="A", col=2),
            Coord(row="A", col=1),
        ]
        assert coords == expected

    def test_range_reverse_direction_vertical(self) -> None:
        """Generate range from E1 to A1 (reverse)"""
        coord1 = Coord(row="E", col=1)
        coord2 = Coord(row="A", col=1)
        coords = coord1.range_to(coord2)
        expected = [
            Coord(row="E", col=1),
            Coord(row="D", col=1),
            Coord(row="C", col=1),
            Coord(row="B", col=1),
            Coord(row="A", col=1),
        ]
        assert coords == expected

    def test_range_single_coord(self) -> None:
        """Range from coord to itself returns single coord"""
        coord = Coord(row="E", col=5)
        coords = coord.range_to(coord)
        assert coords == [coord]

    def test_range_invalid_orientation(self) -> None:
        """Range with invalid orientation raises ValueError"""
        coord1 = Coord(row="A", col=1)
        coord2 = Coord(row="B", col=3)
        with pytest.raises(ValueError, match="Cannot create range"):
            coord1.range_to(coord2)


class TestCoordAdjacency:
    """Tests for checking if coordinates are adjacent"""

    def test_adjacent_horizontal(self) -> None:
        """A1 and A2 are adjacent"""
        coord1 = Coord(row="A", col=1)
        coord2 = Coord(row="A", col=2)
        assert coord1.is_adjacent_to(coord2)

    def test_adjacent_vertical(self) -> None:
        """A1 and B1 are adjacent"""
        coord1 = Coord(row="A", col=1)
        coord2 = Coord(row="B", col=1)
        assert coord1.is_adjacent_to(coord2)

    def test_adjacent_diagonal(self) -> None:
        """A1 and B2 are adjacent diagonally"""
        coord1 = Coord(row="A", col=1)
        coord2 = Coord(row="B", col=2)
        assert coord1.is_adjacent_to(coord2)

    def test_not_adjacent_horizontal_gap(self) -> None:
        """A1 and A3 are not adjacent (gap of 1)"""
        coord1 = Coord(row="A", col=1)
        coord2 = Coord(row="A", col=3)
        assert not coord1.is_adjacent_to(coord2)

    def test_not_adjacent_vertical_gap(self) -> None:
        """A1 and C1 are not adjacent (gap of 1)"""
        coord1 = Coord(row="A", col=1)
        coord2 = Coord(row="C", col=1)
        assert not coord1.is_adjacent_to(coord2)

    def test_not_adjacent_same_coord(self) -> None:
        """A coord is not adjacent to itself"""
        coord = Coord(row="E", col=5)
        assert not coord.is_adjacent_to(coord)

    def test_adjacent_all_8_directions(self) -> None:
        """E5 is adjacent to all 8 surrounding coordinates"""
        center = Coord(row="E", col=5)
        adjacent_coords = [
            Coord(row="D", col=4),  # up-left
            Coord(row="D", col=5),  # up
            Coord(row="D", col=6),  # up-right
            Coord(row="E", col=4),  # left
            Coord(row="E", col=6),  # right
            Coord(row="F", col=4),  # down-left
            Coord(row="F", col=5),  # down
            Coord(row="F", col=6),  # down-right
        ]
        for coord in adjacent_coords:
            assert center.is_adjacent_to(coord)

    def test_adjacency_is_symmetric(self) -> None:
        """If A is adjacent to B, then B is adjacent to A"""
        coord1 = Coord(row="C", col=3)
        coord2 = Coord(row="C", col=4)
        assert coord1.is_adjacent_to(coord2) == coord2.is_adjacent_to(coord1)


class TestCoordBoundaries:
    """Tests for checking if coordinates are within board boundaries"""

    def test_within_boundaries_A1(self) -> None:
        """A1 is within boundaries"""
        coord = Coord(row="A", col=1)
        assert coord.is_within_boundaries()

    def test_within_boundaries_J10(self) -> None:
        """J10 is within boundaries"""
        coord = Coord(row="J", col=10)
        assert coord.is_within_boundaries()

    def test_within_boundaries_E5(self) -> None:
        """E5 is within boundaries"""
        coord = Coord(row="E", col=5)
        assert coord.is_within_boundaries()

    def test_within_boundaries_all_corners(self) -> None:
        """All four corners are within boundaries"""
        corners = [
            Coord(row="A", col=1),   # top-left
            Coord(row="A", col=10),  # top-right
            Coord(row="J", col=1),   # bottom-left
            Coord(row="J", col=10),  # bottom-right
        ]
        for coord in corners:
            assert coord.is_within_boundaries()

    def test_within_boundaries_all_edges(self) -> None:
        """All edge coordinates are within boundaries"""
        # Top edge
        for col in range(1, 11):
            assert Coord(row="A", col=col).is_within_boundaries()
        # Bottom edge
        for col in range(1, 11):
            assert Coord(row="J", col=col).is_within_boundaries()
        # Left edge
        for row in ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]:
            assert Coord(row=row, col=1).is_within_boundaries()
        # Right edge
        for row in ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]:
            assert Coord(row=row, col=10).is_within_boundaries()
