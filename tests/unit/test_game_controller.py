import pytest
from game.player import Player, PlayerNum
from game.game_controller import Game, GameController
from game.ship import ShipLocation


@pytest.fixture
def player_alice() -> Player:
    return Player(name="Alice")


@pytest.fixture
def player_bob() -> Player:
    return Player(name="Bob")


@pytest.fixture()
def two_player_game(player_alice, player_bob) -> Game:
    return Game(player_1=player_alice, player_2=player_bob)


@pytest.fixture()
def ship_layout_1() -> list[ShipLocation]:
    return []


class TestGame:
    def test_create_game_object(self, player_alice: Player, player_bob: Player):
        game: Game = Game(player_1=player_alice, player_2=player_bob)
        assert game
        assert game.player_1 == player_alice
        assert game.player_2 == player_bob


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

    def test_place_ships_invalid_layout(self, two_player_game: Game):
        with pytest.raises(ValueError):
            GameController.place_ships(
                game=two_player_game,
                player_num=PlayerNum.PLAYER_1,
                ships=ship_layout_invalid,
            )

    def test_place_ships_incomplete_layout(self, two_player_game: Game):
        with pytest.raises(ValueError):
            GameController.place_ships(
                game=two_player_game,
                player_num=PlayerNum.PLAYER_1,
                ships=ship_layout_incomplete,
            )
