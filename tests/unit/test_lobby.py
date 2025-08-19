import pytest
from game.lobby import Lobby
from game.player import Player, PlayerStatus


class TestLobby:
    def test_lobby_creation(self):
        lobby: Lobby = Lobby()
        assert lobby

    def test_add_player_to_empty_lobby(self):
        lobby: Lobby = Lobby()
        lobby.add_player("Alice", PlayerStatus.AVAILABLE)

        available_players: list[Player] = lobby.get_available_players()
        assert len(available_players) == 1
        assert isinstance(available_players[0], Player)
        assert available_players[0].name == "Alice"
        assert available_players[0].status == PlayerStatus.AVAILABLE

    def test_add_multiple_players(self):
        lobby: Lobby = Lobby()
        lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        lobby.add_player("Charlie", PlayerStatus.AVAILABLE)

        available_players: list[Player] = lobby.get_available_players()
        assert len(available_players) == 3

    def test_add_player_only_accepts_player_status_enum(self):
        lobby: Lobby = Lobby()

        # Should raise TypeError when passing string instead of PlayerStatus
        with pytest.raises(TypeError):
            lobby.add_player("Alice", "Available")

    def test_add_player_rejects_invalid_string_status(self):
        lobby: Lobby = Lobby()

        # Should raise TypeError when passing any string
        with pytest.raises(TypeError):
            lobby.add_player("Bob", "InvalidStatus")
