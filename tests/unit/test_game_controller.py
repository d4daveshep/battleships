import pytest
from game.game_controller import Game, GameController


class TestGame:
    def test_create_game_object(self):
        game: Game = Game()
        assert game


class TestGameController:
    def test_create_game(self):
        game: Game = GameController.create_game()
        assert game
