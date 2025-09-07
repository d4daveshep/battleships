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


class TestLobbyGameRequests:
    """Tests for new game request functionality in Lobby class"""

    def test_lobby_has_game_requests_attribute(self, empty_lobby):
        # Test that lobby has game_requests dictionary
        assert hasattr(empty_lobby, 'game_requests')
        assert isinstance(empty_lobby.game_requests, dict)
        assert len(empty_lobby.game_requests) == 0

    def test_send_game_request_creates_request(self, empty_lobby):
        # Setup: Add two available players
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        
        # Test: Send game request from Alice to Bob
        empty_lobby.send_game_request("Alice", "Bob")
        
        # Verify: Request is stored and player statuses are updated
        assert "Bob" in empty_lobby.game_requests
        game_request = empty_lobby.game_requests["Bob"]
        
        assert game_request.sender == "Alice"
        assert game_request.receiver == "Bob"
        assert game_request.status == "pending"
        
        # Verify: Player statuses are updated
        assert empty_lobby.get_player_status("Alice") == PlayerStatus.REQUESTING_GAME
        assert empty_lobby.get_player_status("Bob") == PlayerStatus.PENDING_RESPONSE

    def test_send_game_request_sender_not_available(self, empty_lobby):
        # Setup: Add players with Alice not available
        empty_lobby.add_player("Alice", PlayerStatus.REQUESTING_GAME)
        empty_lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        
        # Test: Should raise error when sender is not available
        with pytest.raises(ValueError, match="Sender Alice is not available"):
            empty_lobby.send_game_request("Alice", "Bob")

    def test_send_game_request_receiver_not_available(self, empty_lobby):
        # Setup: Add players with Bob not available
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Bob", PlayerStatus.IN_GAME)
        
        # Test: Should raise error when receiver is not available
        with pytest.raises(ValueError, match="Receiver Bob is not available"):
            empty_lobby.send_game_request("Alice", "Bob")

    def test_send_game_request_nonexistent_players(self, empty_lobby):
        # Test: Should raise error for nonexistent sender
        with pytest.raises(ValueError, match="Player 'Alice' not found"):
            empty_lobby.send_game_request("Alice", "Bob")
        
        # Setup: Add only Alice
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        
        # Test: Should raise error for nonexistent receiver
        with pytest.raises(ValueError, match="Player 'Bob' not found"):
            empty_lobby.send_game_request("Alice", "Bob")

    def test_get_pending_request_exists(self, empty_lobby):
        # Setup: Add players and send request
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        empty_lobby.send_game_request("Alice", "Bob")
        
        # Test: Get pending request for Bob
        request = empty_lobby.get_pending_request("Bob")
        
        assert request is not None
        assert request.sender == "Alice"
        assert request.receiver == "Bob"
        assert request.status == "pending"

    def test_get_pending_request_none_exists(self, empty_lobby):
        # Setup: Add player with no pending request
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        
        # Test: Should return None when no request exists
        request = empty_lobby.get_pending_request("Alice")
        assert request is None

    def test_accept_game_request_success(self, empty_lobby):
        # Setup: Add players and send request
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        empty_lobby.send_game_request("Alice", "Bob")
        
        # Test: Bob accepts the request
        sender, receiver = empty_lobby.accept_game_request("Bob")
        
        # Verify: Returns correct player names
        assert sender == "Alice"
        assert receiver == "Bob"
        
        # Verify: Both players are now IN_GAME
        assert empty_lobby.get_player_status("Alice") == PlayerStatus.IN_GAME
        assert empty_lobby.get_player_status("Bob") == PlayerStatus.IN_GAME
        
        # Verify: Request is removed from pending
        assert "Bob" not in empty_lobby.game_requests

    def test_accept_game_request_no_pending_request(self, empty_lobby):
        # Setup: Add player with no pending request
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        
        # Test: Should raise error when no request to accept
        with pytest.raises(ValueError, match="No pending game request for Alice"):
            empty_lobby.accept_game_request("Alice")

    def test_decline_game_request_success(self, empty_lobby):
        # Setup: Add players and send request
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        empty_lobby.send_game_request("Alice", "Bob")
        
        # Test: Bob declines the request
        sender = empty_lobby.decline_game_request("Bob")
        
        # Verify: Returns sender name
        assert sender == "Alice"
        
        # Verify: Both players are back to AVAILABLE
        assert empty_lobby.get_player_status("Alice") == PlayerStatus.AVAILABLE
        assert empty_lobby.get_player_status("Bob") == PlayerStatus.AVAILABLE
        
        # Verify: Request is removed from pending
        assert "Bob" not in empty_lobby.game_requests

    def test_decline_game_request_no_pending_request(self, empty_lobby):
        # Setup: Add player with no pending request
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        
        # Test: Should raise error when no request to decline
        with pytest.raises(ValueError, match="No pending game request for Alice"):
            empty_lobby.decline_game_request("Alice")

    def test_multiple_game_requests_to_different_receivers(self, empty_lobby):
        # Setup: Add multiple players
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Charlie", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Diana", PlayerStatus.AVAILABLE)
        
        # Test: Send multiple requests
        empty_lobby.send_game_request("Alice", "Bob")
        empty_lobby.send_game_request("Charlie", "Diana")
        
        # Verify: Both requests exist
        assert "Bob" in empty_lobby.game_requests
        assert "Diana" in empty_lobby.game_requests
        
        bob_request = empty_lobby.get_pending_request("Bob")
        diana_request = empty_lobby.get_pending_request("Diana")
        
        assert bob_request.sender == "Alice"
        assert diana_request.sender == "Charlie"

    def test_cannot_send_request_while_having_pending_request(self, empty_lobby):
        # Setup: Add three players
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Charlie", PlayerStatus.AVAILABLE)
        
        # Test: Alice sends request to Bob
        empty_lobby.send_game_request("Alice", "Bob")
        
        # Test: Alice cannot send another request while first is pending
        with pytest.raises(ValueError, match="Sender Alice is not available"):
            empty_lobby.send_game_request("Alice", "Charlie")
