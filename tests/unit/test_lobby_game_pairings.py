"""
Unit tests for Lobby game pairing functionality.

These tests follow the TDD RED phase for tracking matched player pairs
when a game request is accepted.

Tests should fail initially as the pairing system is not yet implemented.
"""

import pytest
from game.lobby import Lobby
from game.player import PlayerStatus


class TestLobbyGamePairings:
    """Tests for tracking active game pairings in Lobby"""

    def test_lobby_has_active_games_attribute(self):
        """Test that Lobby has an active_games dictionary for tracking pairings"""
        lobby = Lobby()
        assert hasattr(lobby, "active_games"), "Lobby should have an active_games attribute"
        assert isinstance(
            lobby.active_games, dict
        ), "active_games should be a dictionary"

    def test_active_games_initially_empty(self):
        """Test that active_games dictionary is empty on initialization"""
        lobby = Lobby()
        assert len(lobby.active_games) == 0, "active_games should be empty initially"

    def test_accept_game_request_creates_pairing(self):
        """Test that accepting a game request creates a bidirectional pairing"""
        lobby = Lobby()
        lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        lobby.send_game_request("Alice", "Bob")

        # Accept the request
        lobby.accept_game_request("Bob")

        # Both players should be paired with each other
        assert "Alice" in lobby.active_games, "Alice should be in active_games"
        assert "Bob" in lobby.active_games, "Bob should be in active_games"
        assert lobby.active_games["Alice"] == "Bob", "Alice should be paired with Bob"
        assert lobby.active_games["Bob"] == "Alice", "Bob should be paired with Alice"

    def test_get_opponent_method_exists(self):
        """Test that Lobby has a get_opponent method"""
        lobby = Lobby()
        assert hasattr(lobby, "get_opponent"), "Lobby should have a get_opponent method"
        assert callable(lobby.get_opponent), "get_opponent should be callable"

    def test_get_opponent_returns_paired_player(self):
        """Test that get_opponent returns the correct opponent for a paired player"""
        lobby = Lobby()
        lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        lobby.send_game_request("Alice", "Bob")
        lobby.accept_game_request("Bob")

        # Get opponent for each player
        alice_opponent = lobby.get_opponent("Alice")
        bob_opponent = lobby.get_opponent("Bob")

        assert alice_opponent == "Bob", "Alice's opponent should be Bob"
        assert bob_opponent == "Alice", "Bob's opponent should be Alice"

    def test_get_opponent_returns_none_for_unpaired_player(self):
        """Test that get_opponent returns None for a player not in a game"""
        lobby = Lobby()
        lobby.add_player("Charlie", PlayerStatus.AVAILABLE)

        opponent = lobby.get_opponent("Charlie")
        assert opponent is None, "Unpaired player should have no opponent"

    def test_get_opponent_returns_none_for_nonexistent_player(self):
        """Test that get_opponent returns None for a player not in lobby"""
        lobby = Lobby()

        opponent = lobby.get_opponent("NonExistent")
        assert opponent is None, "Nonexistent player should have no opponent"

    def test_multiple_game_pairings_tracked_independently(self):
        """Test that multiple game pairings can coexist without interference"""
        lobby = Lobby()
        # Set up two pairs of players
        lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        lobby.add_player("Charlie", PlayerStatus.AVAILABLE)
        lobby.add_player("Diana", PlayerStatus.AVAILABLE)

        # Create two game requests
        lobby.send_game_request("Alice", "Bob")
        lobby.accept_game_request("Bob")

        lobby.send_game_request("Charlie", "Diana")
        lobby.accept_game_request("Diana")

        # Verify both pairings are tracked correctly
        assert lobby.get_opponent("Alice") == "Bob"
        assert lobby.get_opponent("Bob") == "Alice"
        assert lobby.get_opponent("Charlie") == "Diana"
        assert lobby.get_opponent("Diana") == "Charlie"

    def test_pairing_created_before_request_deleted(self):
        """Test that pairing is created even though game request is deleted"""
        lobby = Lobby()
        lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        lobby.send_game_request("Alice", "Bob")

        # Accept the request
        lobby.accept_game_request("Bob")

        # Game request should be deleted
        assert lobby.get_pending_request("Bob") is None
        assert lobby.get_pending_request_by_sender("Alice") is None

        # But pairing should still exist
        assert lobby.get_opponent("Alice") == "Bob"
        assert lobby.get_opponent("Bob") == "Alice"

    def test_pairing_not_created_when_request_declined(self):
        """Test that declining a game request does not create a pairing"""
        lobby = Lobby()
        lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        lobby.send_game_request("Alice", "Bob")

        # Decline the request
        lobby.decline_game_request("Bob")

        # No pairing should exist
        assert lobby.get_opponent("Alice") is None
        assert lobby.get_opponent("Bob") is None
        assert len(lobby.active_games) == 0

    def test_accept_game_request_still_returns_correct_tuple(self):
        """Test that accept_game_request still returns (sender, receiver) tuple"""
        lobby = Lobby()
        lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        lobby.send_game_request("Alice", "Bob")

        # Accept and verify return value
        sender, receiver = lobby.accept_game_request("Bob")

        assert sender == "Alice", "Should return sender name"
        assert receiver == "Bob", "Should return receiver name"
        # And pairing should be created
        assert lobby.get_opponent("Alice") == "Bob"
        assert lobby.get_opponent("Bob") == "Alice"


class TestLobbyServiceGamePairings:
    """Tests for LobbyService integration with game pairings"""

    def test_lobby_service_has_get_opponent_method(self):
        """Test that LobbyService exposes get_opponent method"""
        from services.lobby_service import LobbyService

        lobby = Lobby()
        lobby_service = LobbyService(lobby)

        assert hasattr(
            lobby_service, "get_opponent"
        ), "LobbyService should have get_opponent method"
        assert callable(lobby_service.get_opponent), "get_opponent should be callable"

    def test_lobby_service_get_opponent_returns_paired_player(self):
        """Test that LobbyService.get_opponent returns correct opponent"""
        from services.lobby_service import LobbyService

        lobby = Lobby()
        lobby_service = LobbyService(lobby)

        # Set up game pairing via service
        lobby_service.join_lobby("Alice")
        lobby_service.join_lobby("Bob")
        lobby_service.send_game_request("Alice", "Bob")
        lobby_service.accept_game_request("Bob")

        # Get opponents via service
        alice_opponent = lobby_service.get_opponent("Alice")
        bob_opponent = lobby_service.get_opponent("Bob")

        assert alice_opponent == "Bob", "Alice's opponent should be Bob"
        assert bob_opponent == "Alice", "Bob's opponent should be Alice"

    def test_lobby_service_get_opponent_validates_player_name(self):
        """Test that LobbyService.get_opponent validates player name input"""
        from services.lobby_service import LobbyService

        lobby = Lobby()
        lobby_service = LobbyService(lobby)

        # Test with empty name - should handle gracefully
        opponent = lobby_service.get_opponent("")
        assert opponent is None, "Empty player name should return None"

        # Test with whitespace - should strip and process
        opponent = lobby_service.get_opponent("  ")
        assert opponent is None, "Whitespace player name should return None"

    def test_lobby_service_get_opponent_strips_player_name(self):
        """Test that LobbyService.get_opponent strips whitespace from player name"""
        from services.lobby_service import LobbyService

        lobby = Lobby()
        lobby_service = LobbyService(lobby)

        lobby_service.join_lobby("Alice")
        lobby_service.join_lobby("Bob")
        lobby_service.send_game_request("Alice", "Bob")
        lobby_service.accept_game_request("Bob")

        # Get opponent with whitespace
        alice_opponent = lobby_service.get_opponent("  Alice  ")

        assert alice_opponent == "Bob", "Should strip whitespace and find opponent"
