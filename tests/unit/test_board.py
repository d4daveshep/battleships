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
)


class TestGameBoard:
    def test_board_creation(self):
        board: GameBoard = GameBoard()
        assert len(board.ships) == 0
        assert len(board.shots_received) == 0
        assert len(board.shots_fired) == 0

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
