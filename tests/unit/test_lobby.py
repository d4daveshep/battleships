from game.player import GameRequest, Player, PlayerStatus
import pytest
from tests.unit.conftest import make_player


class TestLobbyVersionTracking:
    """Test version tracking for change detection in long polling"""

    def test_lobby_has_initial_version(self, empty_lobby):
        """Lobby should have an initial version number starting at 0"""
        assert hasattr(empty_lobby, "version")
        assert empty_lobby.version == 0

    def test_version_increments_when_player_added(self, empty_lobby):
        """Version should increment when a player is added"""
        initial_version = empty_lobby.version
        alice = make_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(alice)
        assert empty_lobby.version == initial_version + 1

    def test_version_increments_when_player_removed(self, empty_lobby):
        """Version should increment when a player is removed"""
        alice = make_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(alice)
        version_before_remove = empty_lobby.version
        empty_lobby.remove_player(alice.id)
        assert empty_lobby.version == version_before_remove + 1

    def test_version_increments_when_player_status_updated(self, empty_lobby):
        """Version should increment when a player's status changes"""
        alice = make_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(alice)
        version_before_update = empty_lobby.version
        empty_lobby.update_player_status(alice.id, PlayerStatus.REQUESTING_GAME)
        assert empty_lobby.version == version_before_update + 1

    def test_version_increments_when_game_request_sent(self, empty_lobby):
        """Version should increment when a game request is sent"""
        alice = make_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(alice)
        bob = make_player("Bob", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(bob)
        version_before_request = empty_lobby.version
        empty_lobby.send_game_request(alice.id, bob.id)
        assert empty_lobby.version == version_before_request + 1

    def test_version_increments_when_game_request_accepted(self, empty_lobby):
        """Version should increment when a game request is accepted"""
        alice = make_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(alice)
        bob = make_player("Bob", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(bob)
        empty_lobby.send_game_request(alice.id, bob.id)
        version_before_accept = empty_lobby.version
        empty_lobby.accept_game_request(bob.id)
        assert empty_lobby.version == version_before_accept + 1

    def test_version_increments_when_game_request_declined(self, empty_lobby):
        """Version should increment when a game request is declined"""
        alice = make_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(alice)
        bob = make_player("Bob", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(bob)
        empty_lobby.send_game_request(alice.id, bob.id)
        version_before_decline = empty_lobby.version
        empty_lobby.decline_game_request(bob.id)
        assert empty_lobby.version == version_before_decline + 1

    def test_version_increments_multiple_operations(self, empty_lobby):
        """Version should increment correctly across multiple operations"""
        assert empty_lobby.version == 0

        alice = make_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(alice)
        assert empty_lobby.version == 1

        bob = make_player("Bob", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(bob)
        assert empty_lobby.version == 2

        empty_lobby.update_player_status(alice.id, PlayerStatus.REQUESTING_GAME)
        assert empty_lobby.version == 3

        empty_lobby.remove_player(bob.id)
        assert empty_lobby.version == 4

    def test_get_version_method(self, empty_lobby):
        """Lobby should have a get_version() method"""
        assert hasattr(empty_lobby, "get_version")
        assert callable(empty_lobby.get_version)
        assert empty_lobby.get_version() == 0

        alice = make_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(alice)
        assert empty_lobby.get_version() == 1


class TestLobby:
    def test_lobby_creation(self, empty_lobby):
        assert empty_lobby

    def test_add_player_to_empty_lobby(self, empty_lobby):
        alice = make_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(alice)

        available_players: list[Player] = empty_lobby.get_available_players()
        assert len(available_players) == 1
        assert isinstance(available_players[0], Player)
        alice: Player = available_players[0]
        assert alice.name == "Alice"
        assert alice.status == PlayerStatus.AVAILABLE

    def test_add_multiple_players(self, empty_lobby):
        alice = make_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(alice)
        bob = make_player("Bob", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(bob)
        charlie = make_player("Charlie", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(charlie)

        available_players: list[Player] = empty_lobby.get_available_players()
        assert len(available_players) == 3

    def test_remove_player_existing(self, empty_lobby):
        # Add some players first
        alice = make_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(alice)
        bob = make_player("Bob", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(bob)

        # Remove Alice
        empty_lobby.remove_player(alice.id)

        # Verify Alice is gone but Bob remains
        available_players = empty_lobby.get_available_players()
        assert len(available_players) == 1
        assert available_players[0].name == "Bob"

    def test_remove_player_nonexistent(self, empty_lobby):
        # Add a player
        alice = make_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(alice)

        # Try to remove a player that doesn't exist - should raise ValueError
        with pytest.raises(ValueError):
            empty_lobby.remove_player("NonExistent")

        # Verify Alice is still there
        available_players = empty_lobby.get_available_players()
        assert len(available_players) == 1
        assert available_players[0].name == "Alice"

    def test_update_player_status_existing_player(self, empty_lobby):
        # Add a player with AVAILABLE status
        alice = make_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(alice)

        # Update Alice's status to REQUESTING_GAME
        empty_lobby.update_player_status(alice.id, PlayerStatus.REQUESTING_GAME)

        # Verify status was updated
        alice_status = empty_lobby.get_player_status(alice.id)
        assert alice_status == PlayerStatus.REQUESTING_GAME

        # Verify player object was updated
        assert empty_lobby.players[alice.id].status == PlayerStatus.REQUESTING_GAME

    def test_update_player_status_nonexistent_player(self, empty_lobby):
        # Try to update status of a player that doesn't exist
        with pytest.raises(
            ValueError, match=r"Player with ID \'.*\' not found in lobby"
        ):
            empty_lobby.update_player_status(
                "NonExistent", PlayerStatus.REQUESTING_GAME
            )

    def test_update_player_status_all_statuses(self, empty_lobby):
        # Add a player and test updating to all different statuses
        bob = make_player("Bob", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(bob)

        # Test updating to REQUESTING_GAME
        empty_lobby.update_player_status(bob.id, PlayerStatus.REQUESTING_GAME)
        assert empty_lobby.get_player_status(bob.id) == PlayerStatus.REQUESTING_GAME

        # Test updating to IN_GAME
        empty_lobby.update_player_status(bob.id, PlayerStatus.IN_GAME)
        assert empty_lobby.get_player_status(bob.id) == PlayerStatus.IN_GAME

        # Test updating back to AVAILABLE
        empty_lobby.update_player_status(bob.id, PlayerStatus.AVAILABLE)
        assert empty_lobby.get_player_status(bob.id) == PlayerStatus.AVAILABLE

    def test_get_player_status_existing_player(self, empty_lobby):
        # Add players with different statuses
        alice = make_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(alice)
        bob = make_player("Bob", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(bob)
        empty_lobby.update_player_status(bob.id, PlayerStatus.REQUESTING_GAME)

        # Verify we can get each player's status
        assert empty_lobby.get_player_status(alice.id) == PlayerStatus.AVAILABLE
        assert empty_lobby.get_player_status(bob.id) == PlayerStatus.REQUESTING_GAME

    def test_get_player_status_nonexistent_player(self, empty_lobby):
        # Try to get status of a player that doesn't exist
        with pytest.raises(
            ValueError, match=r"Player with ID \'.*\' not found in lobby"
        ):
            empty_lobby.get_player_status("NonExistent")

    def test_get_available_players_filters_by_status(self, empty_lobby):
        # Add players with different statuses
        alice = make_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(alice)
        bob = make_player("Bob", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(bob)
        charlie = make_player("Charlie", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(charlie)

        # Update some players to different statuses
        empty_lobby.update_player_status(bob.id, PlayerStatus.REQUESTING_GAME)
        empty_lobby.update_player_status(charlie.id, PlayerStatus.IN_GAME)

        # get_available_players should only return Alice
        available_players = empty_lobby.get_available_players()
        assert len(available_players) == 1
        assert available_players[0].name == "Alice"
        assert available_players[0].status == PlayerStatus.AVAILABLE


class TestLobbyGameRequests:
    """Tests for new game request functionality in Lobby class"""

    def test_lobby_has_game_requests_attribute(self, empty_lobby):
        # Test that lobby has game_requests dictionary
        assert hasattr(empty_lobby, "game_requests")
        assert isinstance(empty_lobby.game_requests, dict)
        assert len(empty_lobby.game_requests) == 0

    def test_send_game_request_creates_request(self, empty_lobby):
        # Setup: Add two available players
        alice = make_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(alice)
        bob = make_player("Bob", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(bob)

        # Test: Send game request from Alice to Bob
        empty_lobby.send_game_request(alice.id, bob.id)

        # Verify: Request is stored and player statuses are updated
        assert bob.id in empty_lobby.game_requests
        game_request = empty_lobby.game_requests[bob.id]

        assert game_request.sender_id == alice.id
        assert game_request.receiver_id == bob.id

        # Verify: Player statuses are updated
        assert empty_lobby.get_player_status(alice.id) == PlayerStatus.REQUESTING_GAME
        assert empty_lobby.get_player_status(bob.id) == PlayerStatus.PENDING_RESPONSE

    def test_send_game_request_sender_not_available(self, empty_lobby):
        # Setup: Add players with Alice not available
        alice = make_player("Alice", PlayerStatus.REQUESTING_GAME)
        empty_lobby.add_player(alice)
        bob = make_player("Bob", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(bob)

        # Test: Should raise error when sender is not available
        with pytest.raises(ValueError, match=r"Sender with ID .* is not available"):
            empty_lobby.send_game_request(alice.id, bob.id)

    def test_send_game_request_receiver_not_available(self, empty_lobby):
        # Setup: Add players with Bob not available
        alice = make_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(alice)
        bob = make_player("Bob", PlayerStatus.IN_GAME)
        empty_lobby.add_player(bob)

        # Test: Should raise error when receiver is not available
        with pytest.raises(ValueError, match=r"Receiver with ID .* is not available"):
            empty_lobby.send_game_request(alice.id, bob.id)

    def test_send_game_request_nonexistent_players(self, empty_lobby):
        # Test: Should raise error for nonexistent sender
        with pytest.raises(ValueError, match=r"Player with ID \'.*\' not found"):
            empty_lobby.send_game_request("Alice", "Bob")

        # Setup: Add only Alice
        alice = make_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(alice)

        # Test: Should raise error for nonexistent receiver
        with pytest.raises(ValueError, match=r"Player with ID \'.*\' not found"):
            empty_lobby.send_game_request(alice.id, "Bob")

    def test_get_pending_request_exists(self, empty_lobby):
        # Setup: Add players and send request
        alice = make_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(alice)
        bob = make_player("Bob", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(bob)
        empty_lobby.send_game_request(alice.id, bob.id)

        # Test: Get pending request for Bob
        request = empty_lobby.get_pending_request(bob.id)

        assert request is not None
        assert request.sender_id == alice.id
        assert request.receiver_id == bob.id

    def test_get_pending_request_none_exists(self, empty_lobby):
        # Setup: Add player with no pending request
        alice = make_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(alice)

        # Test: Should return None when no request exists
        request = empty_lobby.get_pending_request(alice.id)
        assert request is None

    def test_accept_game_request_success(self, empty_lobby):
        # Setup: Add players and send request
        alice = make_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(alice)
        bob = make_player("Bob", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(bob)
        empty_lobby.send_game_request(alice.id, bob.id)

        # Test: Bob accepts the request
        sender_id, receiver_id = empty_lobby.accept_game_request(bob.id)

        # Verify: Returns correct player IDs
        assert sender_id == alice.id
        assert receiver_id == bob.id

        # Verify: Both players are now IN_GAME
        assert empty_lobby.get_player_status(alice.id) == PlayerStatus.IN_GAME
        assert empty_lobby.get_player_status(bob.id) == PlayerStatus.IN_GAME

        # Verify: Request is removed from pending
        assert bob.id not in empty_lobby.game_requests

    def test_accept_game_request_no_pending_request(self, empty_lobby):
        # Setup: Add player with no pending request
        alice = make_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(alice)

        # Test: Should raise error when no request to accept
        with pytest.raises(
            ValueError, match=r"No pending game request for player with ID .*"
        ):
            empty_lobby.accept_game_request(alice.id)

    def test_decline_game_request_success(self, empty_lobby):
        # Setup: Add players and send request
        alice = make_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(alice)
        bob = make_player("Bob", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(bob)
        empty_lobby.send_game_request(alice.id, bob.id)

        # Test: Bob declines the request
        sender_id = empty_lobby.decline_game_request(bob.id)

        # Verify: Returns sender ID
        assert sender_id == alice.id

        # Verify: Both players are back to AVAILABLE
        assert empty_lobby.get_player_status(alice.id) == PlayerStatus.AVAILABLE
        assert empty_lobby.get_player_status(bob.id) == PlayerStatus.AVAILABLE

        # Verify: Request is removed from pending
        assert bob.id not in empty_lobby.game_requests

    def test_decline_game_request_no_pending_request(self, empty_lobby):
        # Setup: Add player with no pending request
        alice = make_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(alice)

        # Test: Should raise error when no request to decline
        with pytest.raises(
            ValueError, match=r"No pending game request for player with ID .*"
        ):
            empty_lobby.decline_game_request(alice.id)

    def test_multiple_game_requests_to_different_receivers(self, empty_lobby):
        # Setup: Add multiple players
        alice = make_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(alice)
        bob = make_player("Bob", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(bob)
        charlie = make_player("Charlie", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(charlie)
        diana = make_player("Diana", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(diana)

        # Test: Send multiple requests
        empty_lobby.send_game_request(alice.id, bob.id)
        empty_lobby.send_game_request(charlie.id, diana.id)

        # Verify: Both requests exist
        assert bob.id in empty_lobby.game_requests
        assert diana.id in empty_lobby.game_requests

        bob_request = empty_lobby.get_pending_request(bob.id)
        diana_request = empty_lobby.get_pending_request(diana.id)

        assert bob_request.sender_id == alice.id
        assert diana_request.sender_id == charlie.id

    def test_cannot_send_request_while_having_pending_request(self, empty_lobby):
        # Setup: Add three players
        alice = make_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(alice)
        bob = make_player("Bob", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(bob)
        charlie = make_player("Charlie", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(charlie)

        # Test: Alice sends request to Bob
        empty_lobby.send_game_request(alice.id, bob.id)

        # Test: Alice cannot send another request while first is pending
        with pytest.raises(ValueError, match=r"Sender with ID .* is not available"):
            empty_lobby.send_game_request(alice.id, charlie.id)

    def test_get_pending_request_by_sender(self, empty_lobby):
        # Setup: Add three players
        alice = make_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(alice)
        bob = make_player("Bob", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(bob)
        charlie = make_player("Charlie", PlayerStatus.AVAILABLE)
        empty_lobby.add_player(charlie)

        # Test: Alice sends request to Bob
        empty_lobby.send_game_request(alice.id, bob.id)

        game_request: GameRequest = empty_lobby.get_pending_request_by_sender(alice.id)
        assert game_request is not None
        assert game_request.sender_id == alice.id
        assert game_request.receiver_id == bob.id
