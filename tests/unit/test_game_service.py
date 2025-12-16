import pytest

from game.game_service import GameService
from game.model import GameBoard


class TestGameService:
    def test_create_game_service(self):
        service: GameService = GameService()
        assert service, "Can't create GameService"
        assert len(service.games) == 0

    def test_create_single_player_game(self):
        service: GameService = GameService()
        alice_id = "alice12345"
        game_id: str = service.create_single_player_game(
            player_id=alice_id, player_name="Alice"
        )
        assert len(game_id) == 24  # game_id should be a ?? length random string
        assert len(service.games) == 1

    def test_get_game_board_from_known_player_id(self):
        service: GameService = GameService()
        alice_id = "alice12345"
        service.create_single_player_game(player_id=alice_id, player_name="Alice")

        board: GameBoard = service.get_game_board(player_id=alice_id)
        assert board, "Didn't get GameBoard from GameService"

    # def test_get_game_from_player_id(self):
    #     player_id: str = "abcde12345"
    #     game_state: GameState = GameService.get_game(player_id)
