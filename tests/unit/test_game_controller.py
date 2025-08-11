import pytest
from game.player import Player, PlayerNum
from game.game_controller import Game, GameController
from game.ship import ShipLocation, ShipType, Coordinate, Direction


@pytest.fixture
def player_alice() -> Player:
    return Player(name="Alice")


@pytest.fixture
def player_bob() -> Player:
    return Player(name="Bob")


@pytest.fixture()
def two_player_game(player_alice, player_bob) -> Game:
    return Game(player_1=player_alice, player_2=player_bob)


# Define a valid ship layout
@pytest.fixture()
def ship_layout_1() -> list[ShipLocation]:
    ship_layout: list[ShipLocation] = [
        ShipLocation(
            ship_type=ShipType.CARRIER,
            start_point=Coordinate(0, 0),
            direction=Direction.HORIZONTAL,
        ),
        ShipLocation(
            ship_type=ShipType.BATTLESHIP,
            start_point=Coordinate(2, 0),
            direction=Direction.HORIZONTAL,
        ),
        ShipLocation(
            ship_type=ShipType.CRUISER,
            start_point=Coordinate(4, 0),
            direction=Direction.HORIZONTAL,
        ),
        ShipLocation(
            ship_type=ShipType.SUBMARINE,
            start_point=Coordinate(6, 0),
            direction=Direction.HORIZONTAL,
        ),
        ShipLocation(
            ship_type=ShipType.DESTROYER,
            start_point=Coordinate(8, 0),
            direction=Direction.HORIZONTAL,
        ),
    ]
    return ship_layout


# Define an invalid ship layout (modifing an invalid one)
@pytest.fixture
def ship_layout_invalid(ship_layout_1) -> list[ShipLocation]:
    invalid_location: ShipLocation = ship_layout_1[4]
    invalid_location.start_point = Coordinate(7, 0)  # Too close to another ship
    ship_layout_1[4] = invalid_location
    return ship_layout_1


@pytest.fixture
def ship_layout_incomplete() -> list[ShipLocation]:
    return []


class TestGame:
    def test_create_game_object(self, player_alice: Player, player_bob: Player):
        game: Game = Game(player_1=player_alice, player_2=player_bob)
        assert game
        assert game.player_1 == player_alice
        assert game.player_2 == player_bob

    def test_get_player_by_player_num(self, two_player_game: Game):
        assert (
            two_player_game.get_player_by_num(PlayerNum.PLAYER_1)
            == two_player_game.player_1
        )
        assert (
            two_player_game.get_player_by_num(PlayerNum.PLAYER_2)
            == two_player_game.player_2
        )


class TestGameController:
    def test_create_game_with_two_players(self):
        game: Game = GameController.create_game(
            player_1_name="Alice", player_2_name="Bob"
        )
        assert game
        assert game.player_1.name == "Alice"
        assert game.player_2.name == "Bob"

    def test_place_ships(
        self, two_player_game: Game, ship_layout_1: list[ShipLocation]
    ):
        assert GameController.place_ships(
            game=two_player_game, player_num=PlayerNum.PLAYER_1, ships=ship_layout_1
        )
        player_1: Player = two_player_game.player_1
        assert player_1.board
        assert len(player_1.board.ships) == len(list(ShipType))
        assert player_1.all_ships_are_placed

    def test_place_ships_invalid_layout(
        self, two_player_game: Game, ship_layout_invalid: list[ShipLocation]
    ):
        with pytest.raises(ValueError):
            GameController.place_ships(
                game=two_player_game,
                player_num=PlayerNum.PLAYER_1,
                ships=ship_layout_invalid,
            )

    def test_place_ships_incomplete_layout(
        self, two_player_game: Game, ship_layout_incomplete: list[ShipLocation]
    ):
        with pytest.raises(ValueError):
            GameController.place_ships(
                game=two_player_game,
                player_num=PlayerNum.PLAYER_1,
                ships=ship_layout_incomplete,
            )
