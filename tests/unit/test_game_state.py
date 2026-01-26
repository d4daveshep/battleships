import pytest

from game.game_service import Game, GameMode, GameStatus
from game.player import Player, PlayerStatus


class TestGameModeEnum:
    """Unit tests for GameMode enumeration"""

    def test_game_mode_values(self):
        expected_modes = {
            GameMode.SINGLE_PLAYER,
            GameMode.TWO_PLAYER,
        }
        actual_modes: set[GameMode] = {mode for mode in GameMode}
        assert expected_modes == actual_modes


class TestGameStatusEnum:
    """Unit tests for GameStatus enumeration"""

    def test_game_status_values(self):
        expected_statuses = {
            GameStatus.CREATED,
            GameStatus.SETUP,
            GameStatus.PLAYING,
            GameStatus.FINISHED,
            GameStatus.ABANDONED,
        }
        actual_statuses: set[GameStatus] = {status for status in GameStatus}
        assert expected_statuses == actual_statuses


class TestGameModel:
    """Unit tests for Game"""

    @pytest.fixture
    def alice(self) -> Player:
        return Player("Alice", PlayerStatus.AVAILABLE)

    @pytest.fixture
    def bob(self) -> Player:
        return Player("Bob", PlayerStatus.AVAILABLE)

    def test_single_player_game_creation(self, alice):
        # Test creating a valid single player game
        game = Game(player_1=alice, game_mode=GameMode.SINGLE_PLAYER)

        game_id: str = game.id
        assert isinstance(game_id, str)
        assert len(game_id) == 22
        assert game.player_1 == alice
        assert game.game_mode == GameMode.SINGLE_PLAYER
        assert game.player_2 is None

    def test_two_player_game_creation(self, alice, bob):
        # Test creating a valid two player game
        game = Game(player_1=alice, player_2=bob, game_mode=GameMode.TWO_PLAYER)

        assert game.player_1 == alice
        assert game.player_2 == bob
        assert game.game_mode == GameMode.TWO_PLAYER

    def test_create_two_player_game_fails_with_one_player(self, alice):
        # Test that two player game requires two players
        with pytest.raises(ValueError, match="Two player games must have two players"):
            Game(player_1=alice, game_mode=GameMode.TWO_PLAYER)

    def test_create_single_player_game_fails_with_two_players(self, alice, bob):
        # Test that single player game cannot two players
        with pytest.raises(
            ValueError, match="Single player games cannot have two players"
        ):
            Game(player_1=alice, player_2=bob, game_mode=GameMode.SINGLE_PLAYER)
