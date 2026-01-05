"""
Unit tests for Lobby game pairing functionality.

These tests follow the TDD RED phase for tracking matched player pairs
when a game request is accepted.
"""

from game.lobby import Lobby
from game.player import PlayerStatus
from tests.unit.conftest import make_player


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
        alice = make_player("Alice", PlayerStatus.AVAILABLE)
        bob = make_player("Bob", PlayerStatus.AVAILABLE)
        lobby.add_player(alice)
        lobby.add_player(bob)
        lobby.send_game_request(alice.id, bob.id)

        # Accept the request
        lobby.accept_game_request(bob.id)

        # Both players should be paired with each other
        assert alice.id in lobby.active_games, "Alice should be in active_games"
        assert bob.id in lobby.active_games, "Bob should be in active_games"
        assert lobby.active_games[alice.id] == bob.id, "Alice should be paired with Bob"
        assert lobby.active_games[bob.id] == alice.id, "Bob should be paired with Alice"

    def test_get_opponent_method_exists(self):
        """Test that Lobby has a get_opponent method"""
        lobby = Lobby()
        assert hasattr(lobby, "get_opponent"), "Lobby should have a get_opponent method"
        assert callable(lobby.get_opponent), "get_opponent should be callable"

    def test_get_opponent_returns_paired_player(self):
        """Test that get_opponent returns the correct opponent for a paired player"""
        lobby = Lobby()
        alice = make_player("Alice", PlayerStatus.AVAILABLE)
        bob = make_player("Bob", PlayerStatus.AVAILABLE)
        lobby.add_player(alice)
        lobby.add_player(bob)
        lobby.send_game_request(alice.id, bob.id)
        lobby.accept_game_request(bob.id)

        # Get opponent for each player
        alice_opponent = lobby.get_opponent(alice.id)
        bob_opponent = lobby.get_opponent(bob.id)

        assert alice_opponent == bob.id, "Alice's opponent should be Bob"
        assert bob_opponent == alice.id, "Bob's opponent should be Alice"

    def test_get_opponent_returns_none_for_unpaired_player(self):
        """Test that get_opponent returns None for a player not in a game"""
        lobby = Lobby()
        charlie = make_player("Charlie", PlayerStatus.AVAILABLE)
        lobby.add_player(charlie)

        opponent = lobby.get_opponent(charlie.id)
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
        alice = make_player("Alice", PlayerStatus.AVAILABLE)
        bob = make_player("Bob", PlayerStatus.AVAILABLE)
        charlie = make_player("Charlie", PlayerStatus.AVAILABLE)
        diana = make_player("Diana", PlayerStatus.AVAILABLE)
        
        lobby.add_player(alice)
        lobby.add_player(bob)
        lobby.add_player(charlie)
        lobby.add_player(diana)

        # Create two game requests
        lobby.send_game_request(alice.id, bob.id)
        lobby.accept_game_request(bob.id)

        lobby.send_game_request(charlie.id, diana.id)
        lobby.accept_game_request(diana.id)

        # Verify both pairings are tracked correctly
        assert lobby.get_opponent(alice.id) == bob.id
        assert lobby.get_opponent(bob.id) == alice.id
        assert lobby.get_opponent(charlie.id) == diana.id
        assert lobby.get_opponent(diana.id) == charlie.id

    def test_pairing_created_before_request_deleted(self):
        """Test that pairing is created even though game request is deleted"""
        lobby = Lobby()
        alice = make_player("Alice", PlayerStatus.AVAILABLE)
        bob = make_player("Bob", PlayerStatus.AVAILABLE)
        lobby.add_player(alice)
        lobby.add_player(bob)
        
        lobby.send_game_request(alice.id, bob.id)

        # Accept the request
        lobby.accept_game_request(bob.id)

        # Game request should be deleted
        assert lobby.get_pending_request(bob.id) is None
        assert lobby.get_pending_request_by_sender(alice.id) is None

        # But pairing should still exist
        assert lobby.get_opponent(alice.id) == bob.id
        assert lobby.get_opponent(bob.id) == alice.id

    def test_pairing_not_created_when_request_declined(self):
        """Test that declining a game request does not create a pairing"""
        lobby = Lobby()
        alice = make_player("Alice", PlayerStatus.AVAILABLE)
        bob = make_player("Bob", PlayerStatus.AVAILABLE)
        lobby.add_player(alice)
        lobby.add_player(bob)
        
        lobby.send_game_request(alice.id, bob.id)

        # Decline the request
        lobby.decline_game_request(bob.id)

        # No pairing should exist
        assert lobby.get_opponent(alice.id) is None
        assert lobby.get_opponent(bob.id) is None
        assert len(lobby.active_games) == 0

    def test_accept_game_request_still_returns_correct_tuple(self):
        """Test that accept_game_request still returns (sender, receiver) tuple"""
        lobby = Lobby()
        alice = make_player("Alice", PlayerStatus.AVAILABLE)
        bob = make_player("Bob", PlayerStatus.AVAILABLE)
        lobby.add_player(alice)
        lobby.add_player(bob)
        
        lobby.send_game_request(alice.id, bob.id)

        # Accept and verify return value
        sender_id, receiver_id = lobby.accept_game_request(bob.id)

        assert sender_id == alice.id, "Should return sender ID"
        assert receiver_id == bob.id, "Should return receiver ID"
        # And pairing should be created
        assert lobby.get_opponent(alice.id) == bob.id
        assert lobby.get_opponent(bob.id) == alice.id


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
        alice = make_player("Alice")
        lobby_service.join_lobby(alice)
        bob = make_player("Bob")
        lobby_service.join_lobby(bob)
        lobby_service.send_game_request(alice.id, bob.id)
        lobby_service.accept_game_request(bob.id)

        # Get opponents via service
        alice_opponent = lobby_service.get_opponent(alice.id)
        bob_opponent = lobby_service.get_opponent(bob.id)

        assert alice_opponent == bob.id, "Alice's opponent should be Bob's ID"
        assert bob_opponent == alice.id, "Bob's opponent should be Alice's ID"

    def test_lobby_service_get_opponent_validates_player_id(self):
        """Test that LobbyService.get_opponent validates player ID input"""
        from services.lobby_service import LobbyService

        lobby = Lobby()
        lobby_service = LobbyService(lobby)

        # Test with empty ID - should handle gracefully
        opponent = lobby_service.get_opponent("")
        assert opponent is None, "Empty player ID should return None"

        # Test with whitespace - should result in None as no such player exists
        opponent = lobby_service.get_opponent("  ")
        assert opponent is None, "Whitespace player ID should return None"
