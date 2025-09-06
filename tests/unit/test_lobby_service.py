from pytest_bdd import when
from game import player
import pytest
from game.player import Player, PlayerStatus
from services.lobby_service import LobbyService


class TestLobbyService:
    # Unit tests for join_lobby method

    def test_join_lobby_adds_regular_player(self, empty_lobby_service: LobbyService):
        # Test that join_lobby adds a regular player to the lobby
        empty_lobby_service.join_lobby("John")

        # Verify John was added to the lobby
        players: list[Player] = empty_lobby_service.get_available_players()
        assert len(players) == 1
        john: Player = players[0]
        assert john.name == "John"
        assert john.status == PlayerStatus.AVAILABLE

    def test_join_lobby_handles_empty_player_name(
        self, empty_lobby_service: LobbyService
    ):
        # Test that empty player name raises ValueError
        with pytest.raises(ValueError):
            empty_lobby_service.join_lobby("")

        # Lobby should remain empty
        players = empty_lobby_service.get_available_players()
        assert len(players) == 0

    def test_join_lobby_handles_whitespace_player_name(
        self, empty_lobby_service: LobbyService
    ):
        # Test that whitespace-only player name raises ValueError
        with pytest.raises(ValueError):
            empty_lobby_service.join_lobby("   ")

        # Lobby should remain empty
        players = empty_lobby_service.get_available_players()
        assert len(players) == 0

    def test_join_lobby_strips_player_name(self, empty_lobby_service: LobbyService):
        # Test that player name gets stripped of whitespace
        empty_lobby_service.join_lobby("  Alice  ")

        # Verify Alice was added with stripped name
        players = empty_lobby_service.get_available_players()
        assert len(players) == 1
        alice: Player = players[0]
        assert alice.name == "Alice"  # Should be stripped

    def test_join_lobby_with_existing_player_name(
        self, empty_lobby_service: LobbyService
    ):
        # Test that same player joining multiple times raises ValueError
        empty_lobby_service.join_lobby("Alice")
        with pytest.raises(ValueError):
            empty_lobby_service.join_lobby("Alice")

        # Should still have only one Alice
        players = empty_lobby_service.get_available_players()
        assert len(players) == 1

    # Unit tests for get_lobby_data_for_player method
    def test_get_lobby_data_expected_results(
        self, populated_lobby_service: LobbyService
    ):
        results: list[str] = populated_lobby_service.get_lobby_data_for_player("Alice")
        assert len(results) == 2
        assert results == ["Bob", "Charlie"]

    def test_get_lobby_data_for_new_player(self, empty_lobby_service: LobbyService):
        # Test getting lobby data for a new player
        empty_lobby_service.join_lobby("Alice")
        results: list[str] = empty_lobby_service.get_lobby_data_for_player("Alice")

        assert results == []

    def test_get_lobby_data_does_not_modify_lobby_state(
        self, populated_lobby_service: LobbyService
    ):
        # Test that getting lobby data does not modify the lobby state
        # populated_lobby_service.get_lobby_data_for_player("Alice")

        # Get initial state
        initial_players: list[Player] = populated_lobby_service.get_available_players()
        initial_count: int = len(initial_players)
        initial_names: list[str] = [player.name for player in initial_players]

        # Get lobby data for a new player
        populated_lobby_service.get_lobby_data_for_player("Alice")

        # Verify lobby state is unchanged
        final_players: list[Player] = populated_lobby_service.get_available_players()
        final_count: int = len(final_players)
        final_names: list[str] = [player.name for player in final_players]

        assert final_count == initial_count
        assert final_names == initial_names

    def test_get_lobby_data_filters_by_available_status(self):
        # TODO: Implement when we have other PlayerStatus defined
        pass

    def test_get_lobby_data_handles_empty_player_name(
        self, empty_lobby_service: LobbyService
    ):
        # Test handling of empty player name
        with pytest.raises(ValueError):
            empty_lobby_service.get_lobby_data_for_player("")

    def test_get_lobby_data_handles_whitespace_player_name(
        self, empty_lobby_service, empty_result
    ):
        # Test handling of whitespace-only player name
        with pytest.raises(ValueError):
            empty_lobby_service.get_lobby_data_for_player("   ")

    def test_get_lobby_data_strips_player_name(
        self, populated_lobby_service: LobbyService
    ):
        # Test that player name gets stripped of whitespace
        # Add existing player

        results: list[str] = populated_lobby_service.get_lobby_data_for_player(
            "  Bob  "
        )

        # Should see existing players only (Bob should NOT be added to lobby)
        assert "Alice" in results
        assert "Bob" not in results  # Bob should not appear - not in lobby
        assert "  Bob  " not in results  # Unstripped version should not exist

    def test_get_lobby_data_multiple_calls_same_player(
        self, empty_lobby, empty_lobby_service
    ):
        # Test multiple calls with same player name
        # First call
        result1 = empty_lobby_service.get_lobby_data_for_player("John")

        # Second call - should not duplicate player
        result2 = empty_lobby_service.get_lobby_data_for_player("John")

        # Results should be identical
        assert result1 == result2

        # Verify John wasn't added multiple times to lobby
        all_players = empty_lobby.get_available_players()
        john_count = sum(1 for player in all_players if player.name == "John")
        assert john_count == 0  # John should NOT be in lobby at all

    # Unit tests for new status management methods

    def test_update_player_status_existing_player(
        self, empty_lobby_service: LobbyService
    ):
        # Add a player first
        empty_lobby_service.join_lobby("Alice")

        # Update Alice's status
        empty_lobby_service.update_player_status("Alice", PlayerStatus.REQUESTING_GAME)

        # Verify status was updated
        alice_status: PlayerStatus = empty_lobby_service.get_player_status("Alice")
        assert alice_status == PlayerStatus.REQUESTING_GAME

    def test_update_player_status_nonexistent_player(
        self, empty_lobby_service: LobbyService
    ):
        # Try to update status of player that doesn't exist
        with pytest.raises(ValueError, match="Player 'NonExistent' not found in lobby"):
            empty_lobby_service.update_player_status(
                "NonExistent", PlayerStatus.REQUESTING_GAME
            )

    def test_update_player_status_all_statuses(self, empty_lobby_service: LobbyService):
        # Add a player and test updating to all different statuses
        empty_lobby_service.join_lobby("Bob")

        # Test updating to REQUESTING_GAME
        empty_lobby_service.update_player_status("Bob", PlayerStatus.REQUESTING_GAME)
        assert (
            empty_lobby_service.get_player_status("Bob") == PlayerStatus.REQUESTING_GAME
        )

        # Test updating to IN_GAME
        empty_lobby_service.update_player_status("Bob", PlayerStatus.IN_GAME)
        assert empty_lobby_service.get_player_status("Bob") == PlayerStatus.IN_GAME

        # Test updating back to AVAILABLE
        empty_lobby_service.update_player_status("Bob", PlayerStatus.AVAILABLE)
        assert empty_lobby_service.get_player_status("Bob") == PlayerStatus.AVAILABLE

    def test_get_player_status_existing_player(self, empty_lobby_service: LobbyService):
        # Add players with different statuses
        empty_lobby_service.join_lobby("Alice")
        empty_lobby_service.join_lobby("Bob")
        empty_lobby_service.update_player_status("Bob", PlayerStatus.REQUESTING_GAME)

        # Verify we can get each player's status
        assert empty_lobby_service.get_player_status("Alice") == PlayerStatus.AVAILABLE
        assert (
            empty_lobby_service.get_player_status("Bob") == PlayerStatus.REQUESTING_GAME
        )

    def test_get_player_status_nonexistent_player(
        self, empty_lobby_service: LobbyService
    ):
        # Try to get status of player that doesn't exist
        with pytest.raises(ValueError, match="Player 'NonExistent' not found in lobby"):
            empty_lobby_service.get_player_status("NonExistent")

    # Unit tests for get_lobby_players_for_player method

    def test_get_lobby_players_for_player_returns_player_objects(
        self, empty_lobby_service: LobbyService
    ):
        # Add players with different statuses
        empty_lobby_service.join_lobby("Alice")
        empty_lobby_service.join_lobby("Bob")
        empty_lobby_service.join_lobby("Charlie")
        empty_lobby_service.update_player_status("Bob", PlayerStatus.REQUESTING_GAME)
        empty_lobby_service.update_player_status("Charlie", PlayerStatus.IN_GAME)

        # Get lobby players for Alice
        players: list[Player] = empty_lobby_service.get_lobby_players_for_player(
            "Alice"
        )

        # Should return Bob and Charlie (all other players regardless of status)
        assert len(players) == 2
        assert all(isinstance(player, Player) for player in players)

        player_names: list[str] = [player.name for player in players]
        assert "Bob" in player_names
        assert "Charlie" in player_names
        assert "Alice" not in player_names  # Should not include requesting player

    def test_get_lobby_players_for_player_excludes_requesting_player(
        self, empty_lobby_service: LobbyService
    ):
        # Add several players
        empty_lobby_service.join_lobby("Alice")
        empty_lobby_service.join_lobby("Bob")
        empty_lobby_service.join_lobby("Charlie")

        # Get lobby players for Bob
        players: list[Player] = empty_lobby_service.get_lobby_players_for_player("Bob")

        # Should return Alice and Charlie, but not Bob
        assert len(players) == 2
        player_names: list[str] = [player.name for player in players]
        assert "Alice" in player_names
        assert "Charlie" in player_names
        assert "Bob" not in player_names

    def test_get_lobby_players_for_player_includes_all_statuses(
        self, empty_lobby_service: LobbyService
    ):
        # Add players with different statuses
        empty_lobby_service.join_lobby("Alice")
        empty_lobby_service.join_lobby("Bob")
        empty_lobby_service.join_lobby("Charlie")
        empty_lobby_service.join_lobby("Diana")

        # Update players to different statuses
        empty_lobby_service.update_player_status("Bob", PlayerStatus.REQUESTING_GAME)
        empty_lobby_service.update_player_status("Charlie", PlayerStatus.IN_GAME)
        # Alice and Diana remain AVAILABLE

        # Get lobby players for Diana
        players: list[Player] = empty_lobby_service.get_lobby_players_for_player(
            "Diana"
        )

        # Should return all other players regardless of status
        assert len(players) == 3
        player_names_and_statuses: list[tuple[str, PlayerStatus]] = [
            (p.name, p.status) for p in players
        ]

        assert ("Alice", PlayerStatus.AVAILABLE) in player_names_and_statuses
        assert ("Bob", PlayerStatus.REQUESTING_GAME) in player_names_and_statuses
        assert ("Charlie", PlayerStatus.IN_GAME) in player_names_and_statuses
        assert all(name != "Diana" for name, _ in player_names_and_statuses)

    def test_get_lobby_players_for_player_empty_lobby(
        self, empty_lobby_service: LobbyService
    ):
        # Add only one player
        empty_lobby_service.join_lobby("Lonely")

        # Get lobby players for the only player
        players: list[Player] = empty_lobby_service.get_lobby_players_for_player(
            "Lonely"
        )

        # Should return empty list (no other players)
        assert len(players) == 0
        assert players == []

    def test_get_lobby_players_for_player_handles_empty_player_name(
        self, empty_lobby_service: LobbyService
    ):
        # Test handling of empty player name
        with pytest.raises(ValueError, match="Player name '' is invalid"):
            empty_lobby_service.get_lobby_players_for_player("")

    def test_get_lobby_players_for_player_handles_whitespace_player_name(
        self, empty_lobby_service: LobbyService
    ):
        # Test handling of whitespace-only player name
        with pytest.raises(ValueError, match="Player name '   ' is invalid"):
            empty_lobby_service.get_lobby_players_for_player("   ")

    def test_get_lobby_players_for_player_strips_player_name(
        self, empty_lobby_service: LobbyService
    ):
        # Add players
        empty_lobby_service.join_lobby("Alice")
        empty_lobby_service.join_lobby("Bob")

        # Get lobby players with whitespace around name
        players: list[Player] = empty_lobby_service.get_lobby_players_for_player(
            "  Alice  "
        )

        # Should work correctly and exclude Alice
        assert len(players) == 1
        assert players[0].name == "Bob"

    # Unit tests for leave_lobby method
    
    def test_leave_lobby_removes_existing_player(self, empty_lobby_service: LobbyService):
        # Test that leave_lobby removes an existing player from the lobby
        empty_lobby_service.join_lobby("Alice")
        empty_lobby_service.join_lobby("Bob")
        
        # Verify both players are in lobby
        players = empty_lobby_service.get_available_players()
        assert len(players) == 2
        
        # Alice leaves the lobby
        empty_lobby_service.leave_lobby("Alice")
        
        # Verify Alice is no longer in lobby but Bob remains
        remaining_players = empty_lobby_service.get_available_players()
        assert len(remaining_players) == 1
        assert remaining_players[0].name == "Bob"
        
    def test_leave_lobby_with_nonexistent_player(self, empty_lobby_service: LobbyService):
        # Test that leave_lobby with nonexistent player raises ValueError
        with pytest.raises(ValueError, match="Player 'NonExistent' not found in lobby"):
            empty_lobby_service.leave_lobby("NonExistent")
            
    def test_leave_lobby_with_empty_player_name(self, empty_lobby_service: LobbyService):
        # Test that leave_lobby with empty player name raises ValueError
        with pytest.raises(ValueError, match="Player name cannot be empty"):
            empty_lobby_service.leave_lobby("")
            
    def test_leave_lobby_with_whitespace_player_name(self, empty_lobby_service: LobbyService):
        # Test that leave_lobby with whitespace-only player name raises ValueError
        with pytest.raises(ValueError, match="Player name cannot be empty"):
            empty_lobby_service.leave_lobby("   ")
            
    def test_leave_lobby_strips_player_name(self, empty_lobby_service: LobbyService):
        # Test that leave_lobby strips whitespace from player name
        empty_lobby_service.join_lobby("Alice")
        
        # Leave with whitespace around name
        empty_lobby_service.leave_lobby("  Alice  ")
        
        # Alice should be removed
        players = empty_lobby_service.get_available_players()
        assert len(players) == 0
        
    def test_leave_lobby_from_empty_lobby(self, empty_lobby_service: LobbyService):
        # Test that leave_lobby from empty lobby raises ValueError
        with pytest.raises(ValueError, match="Player 'Alice' not found in lobby"):
            empty_lobby_service.leave_lobby("Alice")
            
    def test_leave_lobby_updates_other_players_views(self, empty_lobby_service: LobbyService):
        # Test that when a player leaves, it affects other players' lobby views
        empty_lobby_service.join_lobby("Alice")
        empty_lobby_service.join_lobby("Bob")
        empty_lobby_service.join_lobby("Charlie")
        
        # Bob should see Alice and Charlie
        bob_view = empty_lobby_service.get_lobby_players_for_player("Bob")
        bob_view_names = [p.name for p in bob_view]
        assert "Alice" in bob_view_names
        assert "Charlie" in bob_view_names
        
        # Alice leaves
        empty_lobby_service.leave_lobby("Alice")
        
        # Bob should now only see Charlie
        updated_bob_view = empty_lobby_service.get_lobby_players_for_player("Bob")
        updated_names = [p.name for p in updated_bob_view]
        assert "Alice" not in updated_names
        assert "Charlie" in updated_names
        assert len(updated_names) == 1
        
    def test_leave_lobby_with_different_player_statuses(self, empty_lobby_service: LobbyService):
        # Test that players can leave regardless of their status
        empty_lobby_service.join_lobby("Alice")
        empty_lobby_service.join_lobby("Bob")
        empty_lobby_service.join_lobby("Charlie")
        
        # Set different statuses
        empty_lobby_service.update_player_status("Alice", PlayerStatus.REQUESTING_GAME)
        empty_lobby_service.update_player_status("Bob", PlayerStatus.IN_GAME)
        # Charlie remains AVAILABLE
        
        # All players should be able to leave regardless of status
        empty_lobby_service.leave_lobby("Alice")  # REQUESTING_GAME status
        empty_lobby_service.leave_lobby("Bob")    # IN_GAME status
        empty_lobby_service.leave_lobby("Charlie") # AVAILABLE status
        
        # Lobby should be empty
        players = empty_lobby_service.get_available_players()
        assert len(players) == 0
        
    def test_leave_lobby_multiple_times_same_player(self, empty_lobby_service: LobbyService):
        # Test that calling leave_lobby multiple times for same player raises ValueError
        empty_lobby_service.join_lobby("Alice")
        
        # First leave should succeed
        empty_lobby_service.leave_lobby("Alice")
        
        # Second leave should fail
        with pytest.raises(ValueError, match="Player 'Alice' not found in lobby"):
            empty_lobby_service.leave_lobby("Alice")
            
    def test_leave_lobby_last_player(self, empty_lobby_service: LobbyService):
        # Test that the last player can leave, resulting in empty lobby
        empty_lobby_service.join_lobby("LastPlayer")
        
        # Verify player is in lobby
        players = empty_lobby_service.get_available_players()
        assert len(players) == 1
        assert players[0].name == "LastPlayer"
        
        # Last player leaves
        empty_lobby_service.leave_lobby("LastPlayer")
        
        # Lobby should be empty
        final_players = empty_lobby_service.get_available_players()
        assert len(final_players) == 0
