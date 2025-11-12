import pytest

from game.model import Coord, GameBoard, Ship, ShipType, Orientation


class TestGameBoard:
    def test_board_creation(self):
        board: GameBoard = GameBoard()
        assert len(board.ships) == 0
        assert len(board.shots_received) == 0
        assert len(board.shots_fired) == 0

    valid_ship_placement_data: list[
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

    @pytest.mark.parametrize(
        "type,start,orientation,positions", valid_ship_placement_data
    )
    def test_place_all_ships_in_valid_positions(
        self,
        type: ShipType,
        start: Coord,
        orientation: Orientation,
        positions: list[Coord],
    ):
        board: GameBoard = GameBoard()
        ship: Ship = Ship(ship_type=type)
        result: bool = board.place_ship(ship, start, orientation)
        assert result is True
        assert len(board.ships) == 1
        assert ship in board.ships

        assert ship.positions == positions

    def test_place_ship_invalid_position_out_of_bounds(self):
        board: GameBoard = GameBoard()
        destroyer: Ship = Ship(ship_type=ShipType.DESTROYER)
        with pytest.raises(ValueError):
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
        with pytest.raises(ValueError):
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
