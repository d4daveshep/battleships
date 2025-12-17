import pytest
from game.player import Player, PlayerStatus

from game.game_service import (
    Game,
    GameMode,
    GameService,
    PlayerAlreadyInGameException,
    UnknownPlayerException,
)
from game.model import GameBoard


class TestGameService:
    @pytest.fixture
    def service(self) -> GameService:
        return GameService()

    @pytest.fixture
    def alice(self) -> Player:
        return Player(name="Alice", status=PlayerStatus.AVAILABLE)

    @pytest.fixture
    def bob(self) -> Player:
        return Player(name="Bob", status=PlayerStatus.AVAILABLE)

    def test_new_add_player(self, service, alice):
        service.add_player(alice)
        assert alice.id in service.players

    def test_create_game_service(self, service):
        assert service, "Can't create GameService"
        assert len(service.games) == 0

    def test_create_single_player_game(self, service, alice):
        service.add_player(alice)

        game_id: str = service.create_single_player_game(player_id=alice.id)

        # game_id should be a 22 character URL-safe random string
        assert len(game_id) == 22

        assert len(service.games) == 1
        assert game_id in service.games
        game: Game = service.games[game_id]
        assert game.id == game_id
        assert game.game_mode == GameMode.SINGLE_PLAYER
        assert game.player_1 == alice
        assert len(service.games_by_player) == 1
        assert alice.id in service.games_by_player
        assert service.games_by_player[alice.id] == game
        assert alice.status == PlayerStatus.IN_GAME

    def test_create_single_player_game_fails_with_unknown_player(self, service):
        john_doe: Player = Player("John Doe", status=PlayerStatus.AVAILABLE)
        with pytest.raises(UnknownPlayerException):
            service.create_single_player_game(john_doe.id)

    def test_create_single_player_game_fails_with_player_already_in_game(
        self, service, alice
    ):
        service.add_player(alice)
        service.create_single_player_game(alice.id)

        with pytest.raises(PlayerAlreadyInGameException):
            service.create_single_player_game(alice.id)

    def test_get_game_board_from_known_player_id(self, service, alice):
        service.add_player(alice)
        service.create_single_player_game(player_id=alice.id)

        board: GameBoard = service.get_game_board(player_id=alice.id)
        assert board, "Didn't get GameBoard from GameService"

    # def test_get_game_from_player_id(self):
    #     player_id: str = "abcde12345"
    #     game_state: GameState = GameService.get_game(player_id)
