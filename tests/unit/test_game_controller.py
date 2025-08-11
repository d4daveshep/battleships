import pytest
from dataclasses import replace
from game.player import Player, PlayerNum
from game.game_controller import Game, GameController, GamePhase, GameNotReadyError
from game.ship import ShipLocation, ShipType, Coordinate


@pytest.fixture
def player_alice() -> Player:
    return Player(name="Alice")


@pytest.fixture
def player_bob() -> Player:
    return Player(name="Bob")


@pytest.fixture()
def two_player_game(player_alice, player_bob) -> Game:
    return Game(player_1=player_alice, player_2=player_bob)


# Define an invalid ship layout (modifying an valid one)
@pytest.fixture
def ship_layout_invalid(ship_layout_1) -> list[ShipLocation]:
    invalid_location: ShipLocation = ship_layout_1[4]
    invalid_location.start_point = Coordinate(7, 0)  # Too close to another ship
    ship_layout_1[4] = invalid_location
    return ship_layout_1


# Define and incomplete layout of ships (modifying a valid layout)
@pytest.fixture
def ship_layout_incomplete(ship_layout_1) -> list[ShipLocation]:
    del ship_layout_1[-1]  # Remove last ship
    return ship_layout_1


# Define a layout with too many ships (modifying a valid layout)
@pytest.fixture
def ship_layout_too_many(ship_layout_1) -> list[ShipLocation]:
    extra_location: ShipLocation = replace(
        ship_layout_1[4], start_point=Coordinate(8, 4)
    )
    ship_layout_1.append(extra_location)
    return ship_layout_1


@pytest.fixture()
def two_player_game_with_ship_layout(
    two_player_game: Game, ship_layout_1: list[ShipLocation]
) -> Game:
    GameController.place_ships(two_player_game, PlayerNum.PLAYER_1, ship_layout_1)
    GameController.place_ships(two_player_game, PlayerNum.PLAYER_2, ship_layout_1)
    return two_player_game


class TestGamePhase:
    def test_game_phases(self):
        game_phases: set[GamePhase] = set(GamePhase)
        assert game_phases == {
            GamePhase.SETUP,
            GamePhase.PLAYING,
            GamePhase.FINISHED,
            GamePhase.ABANDONED,
        }


class TestGame:
    def test_create_game_object(self, player_alice: Player, player_bob: Player):
        game: Game = Game(player_1=player_alice, player_2=player_bob)
        assert game
        assert game.player_1 == player_alice
        assert game.player_2 == player_bob
        assert game.phase == GamePhase.SETUP
        assert game.current_round == 0

    def test_get_player_by_player_num(self, two_player_game: Game):
        assert (
            two_player_game.get_player_by_num(PlayerNum.PLAYER_1)
            == two_player_game.player_1
        )
        assert (
            two_player_game.get_player_by_num(PlayerNum.PLAYER_2)
            == two_player_game.player_2
        )

    def test_game_is_ready_to_start(
        self, two_player_game: Game, ship_layout_1: list[ShipLocation]
    ):
        # Test game can't start without ships placed
        assert not two_player_game.is_ready_to_start

        # Test game can't start with only one player's ships
        GameController.place_ships(two_player_game, PlayerNum.PLAYER_1, ship_layout_1)
        assert not two_player_game.is_ready_to_start

        # Test game can start after second player adds ships
        GameController.place_ships(two_player_game, PlayerNum.PLAYER_2, ship_layout_1)
        assert two_player_game.is_ready_to_start
        pass


class TestGameController:
    def test_create_game_with_two_players(self):
        game: Game = GameController.create_game(
            player_1_name="Alice", player_2_name="Bob"
        )
        assert game
        assert game.player_1.name == "Alice"
        assert game.player_2.name == "Bob"
        assert game.current_round == 0
        assert game.phase == GamePhase.SETUP

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

    def test_place_too_many_ships(
        self, two_player_game: Game, ship_layout_too_many: list[ShipLocation]
    ):
        with pytest.raises(ValueError):
            GameController.place_ships(
                game=two_player_game,
                player_num=PlayerNum.PLAYER_1,
                ships=ship_layout_too_many,
            )

    def test_start_game(self, two_player_game_with_ship_layout: Game):
        game: Game = two_player_game_with_ship_layout
        assert game.is_ready_to_start

        GameController.start_game(game=game)
        assert game.current_round == 1
        assert game.phase == GamePhase.PLAYING

    def test_cant_start_game_if_not_ready(self, two_player_game: Game):
        game: Game = two_player_game
        assert not game.is_ready_to_start

        with pytest.raises(GameNotReadyError):
            GameController.start_game(two_player_game)

        assert game.current_round == 0
        assert game.phase == GamePhase.SETUP
