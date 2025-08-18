import pytest
from game.lobby import Lobby


class TestLobby:
    def test_lobby_creation(self):
        lobby: Lobby = Lobby()
        assert lobby

    def test_add_player_to_empty_lobby(self):
        lobby: Lobby = Lobby()
        lobby.add_player("Alice", "Available")

        available_players: list = lobby.get_available_players()
        assert len(available_players) == 1

    def test_add_multiple_players(self):
        lobby: Lobby = Lobby()
        lobby.add_player("Alice", "Available")
        lobby.add_player("Bob", "Available")
        lobby.add_player("Charlie", "Available")

        available_players: list = lobby.get_available_players()
        assert len(available_players) == 3

        player_names: list[str] = [player.name for player in available_players]
        assert "Alice" in player_names
        assert "Bob" in player_names
        assert "Charlie" in player_names
