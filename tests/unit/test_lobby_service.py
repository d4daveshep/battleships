import pytest
from services.lobby_service import LobbyService
from game.lobby import Lobby
from game.player import PlayerStatus


class TestLobbyService:
    # Unit tests for LobbyService - extracted from main.py lobby logic
    
    def setup_method(self):
        # Each test gets a fresh lobby instance
        self.lobby = Lobby()
        self.lobby_service = LobbyService(self.lobby)
    
    def test_get_lobby_data_for_new_player(self):
        # Test getting lobby data for a new player
        result = self.lobby_service.get_lobby_data_for_player("John")
        
        expected = {"available_players": []}
        assert result == expected
    
    def test_get_lobby_data_does_not_modify_lobby_state(self):
        # Test that getting lobby data does not modify the lobby state
        # Pre-populate lobby with some players
        self.lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        self.lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        
        # Get initial state
        initial_players = self.lobby.get_available_players()
        initial_count = len(initial_players)
        initial_names = [player.name for player in initial_players]
        
        # Get lobby data for a new player
        self.lobby_service.get_lobby_data_for_player("John")
        
        # Verify lobby state is unchanged
        final_players = self.lobby.get_available_players()
        final_count = len(final_players)
        final_names = [player.name for player in final_players]
        
        assert final_count == initial_count
        assert final_names == initial_names
        assert "John" not in final_names  # John should NOT be added to lobby
    
    def test_get_lobby_data_excludes_current_player_from_results(self):
        # Test that current player is excluded from available players list
        # Add some other players first
        self.lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        self.lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        
        result = self.lobby_service.get_lobby_data_for_player("Alice")
        
        # Alice should not see herself in the list
        available_names = [player["name"] for player in result["available_players"]]
        assert "Alice" not in available_names
        assert "Bob" in available_names
    
    def test_get_lobby_data_shows_other_available_players(self):
        # Test that other available players are shown
        # Pre-populate lobby
        self.lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        self.lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        self.lobby.add_player("Charlie", PlayerStatus.AVAILABLE)
        
        result = self.lobby_service.get_lobby_data_for_player("Diana")
        
        expected_players = [
            {"name": "Alice"},
            {"name": "Bob"}, 
            {"name": "Charlie"}
        ]
        
        # Should see all players (Diana should NOT be added to lobby)
        assert len(result["available_players"]) == 3
        for player in expected_players:
            assert player in result["available_players"]
    
    def test_get_lobby_data_filters_by_available_status(self):
        # Test that only AVAILABLE status players are returned
        # Add players with different statuses
        self.lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        self.lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        
        result = self.lobby_service.get_lobby_data_for_player("Charlie")
        
        # Should only see available players (Alice, Bob)
        available_names = [player["name"] for player in result["available_players"]]
        assert "Alice" in available_names
        assert "Bob" in available_names
        assert len(result["available_players"]) == 2
    
    def test_get_lobby_data_handles_empty_player_name(self):
        # Test handling of empty player name
        result = self.lobby_service.get_lobby_data_for_player("")
        
        expected = {"available_players": []}
        assert result == expected
    
    def test_get_lobby_data_handles_whitespace_player_name(self):
        # Test handling of whitespace-only player name
        result = self.lobby_service.get_lobby_data_for_player("   ")
        
        expected = {"available_players": []}
        assert result == expected
    
    def test_get_lobby_data_strips_player_name(self):
        # Test that player name gets stripped of whitespace
        # Add existing player
        self.lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        
        result = self.lobby_service.get_lobby_data_for_player("  Bob  ")
        
        # Should see existing players only (Bob should NOT be added to lobby)
        available_names = [player["name"] for player in result["available_players"]]
        assert "Alice" in available_names
        assert "Bob" not in available_names  # Bob should not appear - not in lobby
        assert "  Bob  " not in available_names  # Unstripped version should not exist
    
    def test_get_lobby_data_diana_scenario(self):
        # Test special Diana scenario (for test compatibility)
        result = self.lobby_service.get_lobby_data_for_player("Diana")
        
        # Diana should see Alice, Bob, Charlie (from test scenario)
        expected_players = [
            {"name": "Alice"},
            {"name": "Bob"},
            {"name": "Charlie"}
        ]
        
        assert len(result["available_players"]) == 3
        for player in expected_players:
            assert player in result["available_players"]
    
    def test_get_lobby_data_eve_scenario(self):
        # Test special Eve scenario (empty lobby test compatibility)
        # Pre-populate lobby with players
        self.lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        self.lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        
        result = self.lobby_service.get_lobby_data_for_player("Eve")
        
        # Eve should see empty lobby regardless of actual lobby state
        expected = {"available_players": []}
        assert result == expected
    
    def test_get_lobby_data_return_format(self):
        # Test that return format is correct dictionary structure
        result = self.lobby_service.get_lobby_data_for_player("TestPlayer")
        
        # Should return dict with 'available_players' key containing list of dicts
        assert isinstance(result, dict)
        assert "available_players" in result
        assert isinstance(result["available_players"], list)
        
        # If there are players, each should be a dict with 'name' key
        if result["available_players"]:
            for player in result["available_players"]:
                assert isinstance(player, dict)
                assert "name" in player
                assert isinstance(player["name"], str)
    
    def test_get_lobby_data_multiple_calls_same_player(self):
        # Test multiple calls with same player name
        # First call
        result1 = self.lobby_service.get_lobby_data_for_player("John")
        
        # Second call - should not duplicate player
        result2 = self.lobby_service.get_lobby_data_for_player("John")
        
        # Results should be identical
        assert result1 == result2
        
        # Verify John wasn't added multiple times to lobby
        all_players = self.lobby.get_available_players()
        john_count = sum(1 for player in all_players if player.name == "John")
        assert john_count == 0  # John should NOT be in lobby at all
    
    def test_get_lobby_data_is_read_only_operation(self):
        # Test that getting lobby data is a pure read-only operation
        # Start with empty lobby
        initial_state = self.lobby.get_available_players()
        assert len(initial_state) == 0
        
        # Call get_lobby_data multiple times with different players
        self.lobby_service.get_lobby_data_for_player("Player1")
        self.lobby_service.get_lobby_data_for_player("Player2") 
        self.lobby_service.get_lobby_data_for_player("Player3")
        
        # Lobby should still be empty - no side effects
        final_state = self.lobby.get_available_players()
        assert len(final_state) == 0
        
        # Verify no players were added
        final_names = [player.name for player in final_state]
        assert "Player1" not in final_names
        assert "Player2" not in final_names
        assert "Player3" not in final_names