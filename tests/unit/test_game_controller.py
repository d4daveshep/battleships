from os import name
import pytest
from game.player import Player
from game.game_controller import Game, GameController


@pytest.fixture
def player_alice() -> Player:
    return Player(name="Alice")


@pytest.fixture
def player_bob() -> Player:
    return Player(name="Bob")


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
