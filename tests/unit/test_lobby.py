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

    def test_update_player_status_existing_player(self, empty_lobby):
        # Add a player with AVAILABLE status
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        
        # Update Alice's status to REQUESTING_GAME
        empty_lobby.update_player_status("Alice", PlayerStatus.REQUESTING_GAME)
        
        # Verify status was updated
        alice_status = empty_lobby.get_player_status("Alice")
        assert alice_status == PlayerStatus.REQUESTING_GAME
        
        # Verify player object was updated
        assert empty_lobby.players["Alice"].status == PlayerStatus.REQUESTING_GAME

    def test_update_player_status_nonexistent_player(self, empty_lobby):
        # Try to update status of a player that doesn't exist
        with pytest.raises(ValueError, match="Player 'NonExistent' not found in lobby"):
            empty_lobby.update_player_status("NonExistent", PlayerStatus.REQUESTING_GAME)

    def test_update_player_status_all_statuses(self, empty_lobby):
        # Add a player and test updating to all different statuses
        empty_lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        
        # Test updating to REQUESTING_GAME
        empty_lobby.update_player_status("Bob", PlayerStatus.REQUESTING_GAME)
        assert empty_lobby.get_player_status("Bob") == PlayerStatus.REQUESTING_GAME
        
        # Test updating to IN_GAME
        empty_lobby.update_player_status("Bob", PlayerStatus.IN_GAME)
        assert empty_lobby.get_player_status("Bob") == PlayerStatus.IN_GAME
        
        # Test updating back to AVAILABLE
        empty_lobby.update_player_status("Bob", PlayerStatus.AVAILABLE)
        assert empty_lobby.get_player_status("Bob") == PlayerStatus.AVAILABLE

    def test_get_player_status_existing_player(self, empty_lobby):
        # Add players with different statuses
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        empty_lobby.update_player_status("Bob", PlayerStatus.REQUESTING_GAME)
        
        # Verify we can get each player's status
        assert empty_lobby.get_player_status("Alice") == PlayerStatus.AVAILABLE
        assert empty_lobby.get_player_status("Bob") == PlayerStatus.REQUESTING_GAME

    def test_get_player_status_nonexistent_player(self, empty_lobby):
        # Try to get status of a player that doesn't exist
        with pytest.raises(ValueError, match="Player 'NonExistent' not found in lobby"):
            empty_lobby.get_player_status("NonExistent")

    def test_get_available_players_filters_by_status(self, empty_lobby):
        # Add players with different statuses
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Charlie", PlayerStatus.AVAILABLE)
        
        # Update some players to different statuses
        empty_lobby.update_player_status("Bob", PlayerStatus.REQUESTING_GAME)
        empty_lobby.update_player_status("Charlie", PlayerStatus.IN_GAME)
        
        # get_available_players should only return Alice
        available_players = empty_lobby.get_available_players()
        assert len(available_players) == 1
        assert available_players[0].name == "Alice"
        assert available_players[0].status == PlayerStatus.AVAILABLE
