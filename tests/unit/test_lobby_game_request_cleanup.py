import pytest
from datetime import datetime

from game.lobby import Lobby
from game.player import GameRequest, Player, PlayerStatus


class TestLobbyGameRequestCleanup:
    """Unit tests for game request cleanup functionality in Lobby class"""

    def test_remove_player_cancels_outgoing_request(self, empty_lobby: Lobby):
        # Test that removing a player cancels their outgoing game request
        
        # Setup: Add players and create request
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        empty_lobby.send_game_request("Alice", "Bob")
        
        # Verify request exists and statuses are correct
        assert empty_lobby.get_pending_request("Bob") is not None
        assert empty_lobby.get_player_status("Alice") == PlayerStatus.REQUESTING_GAME
        assert empty_lobby.get_player_status("Bob") == PlayerStatus.PENDING_RESPONSE
        
        # Test: Remove Alice (sender)
        empty_lobby.remove_player("Alice")
        
        # Verify: Bob's status should return to AVAILABLE
        assert empty_lobby.get_player_status("Bob") == PlayerStatus.AVAILABLE
        
        # Verify: Request should be removed
        assert empty_lobby.get_pending_request("Bob") is None
        
        # Verify: Alice is no longer in lobby
        assert "Alice" not in empty_lobby.players

    def test_remove_player_cancels_incoming_request(self, empty_lobby: Lobby):
        # Test that removing a player cancels their incoming game request
        
        # Setup: Add players and create request
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        empty_lobby.send_game_request("Alice", "Bob")
        
        # Verify request exists and statuses are correct
        assert empty_lobby.get_pending_request("Bob") is not None
        assert empty_lobby.get_player_status("Alice") == PlayerStatus.REQUESTING_GAME
        assert empty_lobby.get_player_status("Bob") == PlayerStatus.PENDING_RESPONSE
        
        # Test: Remove Bob (receiver)
        empty_lobby.remove_player("Bob")
        
        # Verify: Alice's status should return to AVAILABLE
        assert empty_lobby.get_player_status("Alice") == PlayerStatus.AVAILABLE
        
        # Verify: Request should be removed (Bob no longer exists)
        assert empty_lobby.get_pending_request("Bob") is None
        
        # Verify: Bob is no longer in lobby
        assert "Bob" not in empty_lobby.players

    def test_remove_player_cleans_multiple_requests(self, empty_lobby: Lobby):
        # Test that removing a player cleans up multiple requests involving them
        
        # Setup: Add multiple players
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Charlie", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Diana", PlayerStatus.AVAILABLE)
        
        # Create multiple requests: Alice->Bob, Charlie->Diana
        empty_lobby.send_game_request("Alice", "Bob")
        empty_lobby.send_game_request("Charlie", "Diana")
        
        # Verify both requests exist
        assert empty_lobby.get_pending_request("Bob") is not None
        assert empty_lobby.get_pending_request("Diana") is not None
        
        # Test: Remove Alice (affects only Alice->Bob request)
        empty_lobby.remove_player("Alice")
        
        # Verify: Bob's status returns to AVAILABLE, request removed
        assert empty_lobby.get_player_status("Bob") == PlayerStatus.AVAILABLE
        assert empty_lobby.get_pending_request("Bob") is None
        
        # Verify: Charlie->Diana request unaffected
        assert empty_lobby.get_pending_request("Diana") is not None
        assert empty_lobby.get_player_status("Charlie") == PlayerStatus.REQUESTING_GAME
        assert empty_lobby.get_player_status("Diana") == PlayerStatus.PENDING_RESPONSE

    def test_remove_player_no_requests_no_side_effects(self, empty_lobby: Lobby):
        # Test that removing player with no requests has no side effects
        
        # Setup: Add players with no requests
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        
        # Test: Remove Alice (no requests)
        empty_lobby.remove_player("Alice")
        
        # Verify: Bob's status unchanged
        assert empty_lobby.get_player_status("Bob") == PlayerStatus.AVAILABLE
        
        # Verify: No requests exist
        assert empty_lobby.get_pending_request("Bob") is None
        
        # Verify: Alice removed, Bob remains
        assert "Alice" not in empty_lobby.players
        assert "Bob" in empty_lobby.players

    def test_clear_all_except_cancels_all_requests(self, empty_lobby: Lobby):
        # Test that clear_all_except cancels all game requests
        
        # Setup: Add players with multiple requests
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Charlie", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Diana", PlayerStatus.AVAILABLE)
        
        # Create requests: Alice->Bob, Charlie->Diana
        empty_lobby.send_game_request("Alice", "Bob")
        empty_lobby.send_game_request("Charlie", "Diana")
        
        # Verify requests exist
        assert empty_lobby.get_pending_request("Bob") is not None
        assert empty_lobby.get_pending_request("Diana") is not None
        
        # Test: Clear all except Bob
        empty_lobby.clear_all_except("Bob")
        
        # Verify: Only Bob remains
        assert len(empty_lobby.players) == 1
        assert "Bob" in empty_lobby.players
        assert empty_lobby.get_player_status("Bob") == PlayerStatus.AVAILABLE
        
        # Verify: All requests should be cleared
        assert empty_lobby.get_pending_request("Bob") is None
        assert empty_lobby.get_pending_request("Diana") is None
        assert len(empty_lobby.game_requests) == 0

    def test_clear_all_except_preserves_keeper_status(self, empty_lobby: Lobby):
        # Test that clear_all_except preserves the kept player's status
        
        # Setup: Add players, set Bob to REQUESTING_GAME
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        empty_lobby.send_game_request("Alice", "Bob")
        
        # Bob is now PENDING_RESPONSE
        assert empty_lobby.get_player_status("Bob") == PlayerStatus.PENDING_RESPONSE
        
        # Test: Clear all except Bob
        empty_lobby.clear_all_except("Bob")
        
        # Verify: Bob's status should be reset to AVAILABLE (request was cancelled)
        assert empty_lobby.get_player_status("Bob") == PlayerStatus.AVAILABLE
        assert len(empty_lobby.players) == 1

    def test_cancel_request_by_sender_name(self, empty_lobby: Lobby):
        # Test utility method to cancel request by sender name
        
        # Setup: Add players and create request
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        empty_lobby.send_game_request("Alice", "Bob")
        
        # Test: Cancel request by sender name (this method needs to be implemented)
        empty_lobby.cancel_requests_involving_player("Alice")
        
        # Verify: Request cancelled, both players back to AVAILABLE
        assert empty_lobby.get_pending_request("Bob") is None
        assert empty_lobby.get_player_status("Alice") == PlayerStatus.AVAILABLE
        assert empty_lobby.get_player_status("Bob") == PlayerStatus.AVAILABLE

    def test_cancel_request_by_receiver_name(self, empty_lobby: Lobby):
        # Test utility method to cancel request by receiver name
        
        # Setup: Add players and create request
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        empty_lobby.send_game_request("Alice", "Bob")
        
        # Test: Cancel request by receiver name
        empty_lobby.cancel_requests_involving_player("Bob")
        
        # Verify: Request cancelled, both players back to AVAILABLE
        assert empty_lobby.get_pending_request("Bob") is None
        assert empty_lobby.get_player_status("Alice") == PlayerStatus.AVAILABLE
        assert empty_lobby.get_player_status("Bob") == PlayerStatus.AVAILABLE

    def test_cancel_requests_no_requests_no_effect(self, empty_lobby: Lobby):
        # Test that cancelling requests when none exist has no effect
        
        # Setup: Add players with no requests
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        
        # Test: Cancel requests for Alice (none exist)
        empty_lobby.cancel_requests_involving_player("Alice")
        
        # Verify: No changes
        assert empty_lobby.get_player_status("Alice") == PlayerStatus.AVAILABLE
        assert empty_lobby.get_player_status("Bob") == PlayerStatus.AVAILABLE
        assert len(empty_lobby.game_requests) == 0

    def test_cancel_requests_multiple_concurrent_requests(self, empty_lobby: Lobby):
        # Test cancelling requests when multiple concurrent requests exist
        
        # Setup: Add players with multiple requests
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Charlie", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Diana", PlayerStatus.AVAILABLE)
        
        # Create requests: Alice->Bob, Charlie->Diana
        empty_lobby.send_game_request("Alice", "Bob")
        empty_lobby.send_game_request("Charlie", "Diana")
        
        # Test: Cancel requests involving Alice
        empty_lobby.cancel_requests_involving_player("Alice")
        
        # Verify: Alice->Bob request cancelled
        assert empty_lobby.get_pending_request("Bob") is None
        assert empty_lobby.get_player_status("Alice") == PlayerStatus.AVAILABLE
        assert empty_lobby.get_player_status("Bob") == PlayerStatus.AVAILABLE
        
        # Verify: Charlie->Diana request unaffected
        assert empty_lobby.get_pending_request("Diana") is not None
        assert empty_lobby.get_player_status("Charlie") == PlayerStatus.REQUESTING_GAME
        assert empty_lobby.get_player_status("Diana") == PlayerStatus.PENDING_RESPONSE


class TestLobbyGameRequestEdgeCases:
    """Unit tests for edge cases in game request handling"""

    def test_send_game_request_to_self_raises_error(self, empty_lobby: Lobby):
        # Test that player cannot send game request to themselves
        
        # Setup: Add player
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        
        # Test: Alice tries to send request to herself
        with pytest.raises(ValueError, match="Cannot send game request to yourself"):
            empty_lobby.send_game_request("Alice", "Alice")

    def test_accept_nonexistent_request_raises_error(self, empty_lobby: Lobby):
        # Test that accepting nonexistent request raises error
        
        # Setup: Add player with no pending request
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        
        # Test: Try to accept nonexistent request
        with pytest.raises(ValueError, match="No pending game request for Alice"):
            empty_lobby.accept_game_request("Alice")

    def test_decline_nonexistent_request_raises_error(self, empty_lobby: Lobby):
        # Test that declining nonexistent request raises error
        
        # Setup: Add player with no pending request  
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        
        # Test: Try to decline nonexistent request
        with pytest.raises(ValueError, match="No pending game request for Alice"):
            empty_lobby.decline_game_request("Alice")

    def test_send_request_from_nonexistent_player_raises_error(self, empty_lobby: Lobby):
        # Test that sending request from nonexistent player raises error
        
        # Setup: Add only Bob
        empty_lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        
        # Test: NonExistent tries to send request to Bob
        with pytest.raises(ValueError, match="not found in lobby"):
            empty_lobby.send_game_request("NonExistent", "Bob")

    def test_send_request_to_nonexistent_player_raises_error(self, empty_lobby: Lobby):
        # Test that sending request to nonexistent player raises error
        
        # Setup: Add only Alice
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        
        # Test: Alice tries to send request to NonExistent
        with pytest.raises(ValueError, match="not found in lobby"):
            empty_lobby.send_game_request("Alice", "NonExistent")

    def test_game_request_replaces_existing_request_for_receiver(self, empty_lobby: Lobby):
        # Test that new request to same receiver fails because receiver is not available
        
        # Setup: Add three players
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Charlie", PlayerStatus.AVAILABLE)
        
        # Step 1: Alice sends request to Bob
        empty_lobby.send_game_request("Alice", "Bob")
        first_request = empty_lobby.get_pending_request("Bob")
        assert first_request is not None
        assert first_request.sender == "Alice"
        
        # Step 2: Charlie tries to send request to Bob (should fail - Bob not available)
        with pytest.raises(ValueError, match="Receiver Bob is not available"):
            empty_lobby.send_game_request("Charlie", "Bob")

    def test_multiple_requests_from_same_sender_not_allowed(self, empty_lobby: Lobby):
        # Test that sender cannot send multiple concurrent requests
        
        # Setup: Add three players
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Charlie", PlayerStatus.AVAILABLE)
        
        # Step 1: Alice sends request to Bob
        empty_lobby.send_game_request("Alice", "Bob")
        
        # Step 2: Alice tries to send another request to Charlie (should fail)
        with pytest.raises(ValueError, match="Sender Alice is not available"):
            empty_lobby.send_game_request("Alice", "Charlie")

    def test_request_timestamp_within_reasonable_time(self, empty_lobby: Lobby):
        # Test that request timestamps are set correctly
        
        # Setup: Add players
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        
        # Test: Send request and check timestamp
        before = datetime.now()
        empty_lobby.send_game_request("Alice", "Bob")
        after = datetime.now()
        
        request = empty_lobby.get_pending_request("Bob")
        assert request is not None
        assert before <= request.timestamp <= after

    def test_game_requests_dict_consistency(self, empty_lobby: Lobby):
        # Test that game_requests dict maintains consistency
        
        # Setup: Add players and create requests
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Charlie", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Diana", PlayerStatus.AVAILABLE)
        
        # Create requests: Alice->Bob, Charlie->Diana
        empty_lobby.send_game_request("Alice", "Bob")
        empty_lobby.send_game_request("Charlie", "Diana")
        
        # Verify dict state
        assert len(empty_lobby.game_requests) == 2
        assert "Bob" in empty_lobby.game_requests
        assert "Diana" in empty_lobby.game_requests
        
        # Accept one request
        empty_lobby.accept_game_request("Bob")
        
        # Verify dict updated
        assert len(empty_lobby.game_requests) == 1
        assert "Bob" not in empty_lobby.game_requests
        assert "Diana" in empty_lobby.game_requests
        
        # Decline other request
        empty_lobby.decline_game_request("Diana")
        
        # Verify dict cleared
        assert len(empty_lobby.game_requests) == 0