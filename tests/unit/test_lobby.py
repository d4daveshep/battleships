from game.player import Player, PlayerStatus
import pytest


class TestLobby:
    def test_lobby_creation(self, empty_lobby):
        assert empty_lobby

    def test_add_player_to_empty_lobby(self, empty_lobby):
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)

        available_players: list[Player] = empty_lobby.get_available_players()
        assert len(available_players) == 1
        assert isinstance(available_players[0], Player)
        alice: Player = available_players[0]
        assert alice.name == "Alice"
        assert alice.status == PlayerStatus.AVAILABLE

    def test_add_multiple_players(self, empty_lobby):
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Charlie", PlayerStatus.AVAILABLE)

        available_players: list[Player] = empty_lobby.get_available_players()
        assert len(available_players) == 3

    def test_remove_player_existing(self, empty_lobby):
        # Add some players first
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Bob", PlayerStatus.AVAILABLE)

        # Remove Alice
        empty_lobby.remove_player("Alice")

        # Verify Alice is gone but Bob remains
        available_players = empty_lobby.get_available_players()
        assert len(available_players) == 1
        assert available_players[0].name == "Bob"

    def test_remove_player_nonexistent(self, empty_lobby):
        # Add a player
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)

        # Try to remove a player that doesn't exist - should raise ValueError
        with pytest.raises(ValueError):
            empty_lobby.remove_player("NonExistent")

        # Verify Alice is still there
        available_players = empty_lobby.get_available_players()
        assert len(available_players) == 1
        assert available_players[0].name == "Alice"
