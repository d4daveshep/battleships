import pytest
from game.player import Player
from game.game_controller import Game, GameController


class TestGame:
    def test_create_game_object(self):
        game: Game = Game()
        assert game


class TestGameController:
    @pytest.fixture
    def player_alice(self) -> Player:
        return Player(name="Alice")

    @pytest.fixture
    def player_bob(self) -> Player:
        return Player(name="Bob")

    def test_create_game_with_two_players(
        self, player_alice: Player, player_bob: Player
    ):
        game: Game = GameController.create_game(
            player_1=player_alice, player_2=player_bob
        )
        assert game
        assert game.player_1 == player_alice
        assert game.player_2 == player_bob
