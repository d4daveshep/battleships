import pytest
from datetime import datetime

from game.lobby import Lobby
from game.player import GameRequest, Player, PlayerStatus
from services.lobby_service import LobbyService


class TestLobbyAdvancedLeavingScenarios:
    """Unit tests for advanced leave lobby scenarios involving game requests"""

    def test_leave_lobby_cancels_pending_request_as_receiver(self, empty_lobby: Lobby):
        # Test that leaving lobby cancels pending request when player is receiver
        lobby_service = LobbyService(empty_lobby)
        
        # Setup: Add players and create game request
        lobby_service.join_lobby("Alice")
        lobby_service.join_lobby("Bob")
        lobby_service.send_game_request("Alice", "Bob")
        
        # Verify request exists
        assert lobby_service.get_pending_request_for_player("Bob") is not None
        assert lobby_service.get_player_status("Alice") == PlayerStatus.REQUESTING_GAME
        assert lobby_service.get_player_status("Bob") == PlayerStatus.PENDING_RESPONSE
        
        # Test: Bob (receiver) leaves lobby
        lobby_service.leave_lobby("Bob")
        
        # Verify: Alice's status should return to AVAILABLE (request cancelled)
        assert lobby_service.get_player_status("Alice") == PlayerStatus.AVAILABLE
        
        # Verify: Bob is removed from lobby
        players = lobby_service.get_available_players()
        assert len(players) == 1
        assert players[0].name == "Alice"

    def test_leave_lobby_cancels_pending_request_as_sender(self, empty_lobby: Lobby):
        # Test that leaving lobby cancels pending request when player is sender
        lobby_service = LobbyService(empty_lobby)
        
        # Setup: Add players and create game request
        lobby_service.join_lobby("Alice")
        lobby_service.join_lobby("Bob")
        lobby_service.send_game_request("Alice", "Bob")
        
        # Verify request exists
        assert lobby_service.get_pending_request_for_player("Bob") is not None
        assert lobby_service.get_player_status("Alice") == PlayerStatus.REQUESTING_GAME
        assert lobby_service.get_player_status("Bob") == PlayerStatus.PENDING_RESPONSE
        
        # Test: Alice (sender) leaves lobby
        lobby_service.leave_lobby("Alice")
        
        # Verify: Bob's status should return to AVAILABLE (request cancelled)
        assert lobby_service.get_player_status("Bob") == PlayerStatus.AVAILABLE
        
        # Verify: Request should be removed
        assert lobby_service.get_pending_request_for_player("Bob") is None
        
        # Verify: Alice is removed from lobby
        players = lobby_service.get_available_players()
        assert len(players) == 1
        assert players[0].name == "Bob"

    def test_leave_lobby_handles_multiple_pending_requests(self, empty_lobby: Lobby):
        # Test leaving lobby when multiple game requests are active
        lobby_service = LobbyService(empty_lobby)
        
        # Setup: Add multiple players with multiple requests
        lobby_service.join_lobby("Alice")
        lobby_service.join_lobby("Bob")
        lobby_service.join_lobby("Charlie")
        lobby_service.join_lobby("Diana")
        
        # Create multiple requests: Alice->Bob, Charlie->Diana
        lobby_service.send_game_request("Alice", "Bob")
        lobby_service.send_game_request("Charlie", "Diana")
        
        # Verify both requests exist
        assert lobby_service.get_pending_request_for_player("Bob") is not None
        assert lobby_service.get_pending_request_for_player("Diana") is not None
        
        # Test: Alice leaves (affects Alice->Bob request only)
        lobby_service.leave_lobby("Alice")
        
        # Verify: Bob's status returns to AVAILABLE, Bob's request is cancelled
        assert lobby_service.get_player_status("Bob") == PlayerStatus.AVAILABLE
        assert lobby_service.get_pending_request_for_player("Bob") is None
        
        # Verify: Charlie->Diana request is unaffected
        assert lobby_service.get_pending_request_for_player("Diana") is not None
        assert lobby_service.get_player_status("Charlie") == PlayerStatus.REQUESTING_GAME
        assert lobby_service.get_player_status("Diana") == PlayerStatus.PENDING_RESPONSE

    def test_leave_lobby_in_game_status_removes_from_lobby(self, empty_lobby: Lobby):
        # Test that players with IN_GAME status can still leave lobby
        lobby_service = LobbyService(empty_lobby)
        
        # Setup: Add players, send request, accept to get IN_GAME status
        lobby_service.join_lobby("Alice")
        lobby_service.join_lobby("Bob")
        lobby_service.join_lobby("Charlie")
        lobby_service.send_game_request("Alice", "Bob")
        lobby_service.accept_game_request("Bob")
        
        # Verify both players are IN_GAME
        assert lobby_service.get_player_status("Alice") == PlayerStatus.IN_GAME
        assert lobby_service.get_player_status("Bob") == PlayerStatus.IN_GAME
        
        # Test: Alice leaves lobby while IN_GAME
        lobby_service.leave_lobby("Alice")
        
        # Verify: Alice is removed from lobby
        charlie_view = lobby_service.get_lobby_players_for_player("Charlie")
        charlie_names = [p.name for p in charlie_view]
        assert "Alice" not in charlie_names
        assert "Bob" in charlie_names  # Bob should still be there

    def test_lobby_remove_player_cancels_associated_requests(self, empty_lobby: Lobby):
        # Test that Lobby.remove_player cancels game requests involving that player
        
        # Setup: Add players and create requests
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Charlie", PlayerStatus.AVAILABLE)
        
        # Create requests: Alice->Bob
        empty_lobby.send_game_request("Alice", "Bob")
        
        # Verify request exists
        assert empty_lobby.get_pending_request("Bob") is not None
        assert empty_lobby.get_player_status("Alice") == PlayerStatus.REQUESTING_GAME
        assert empty_lobby.get_player_status("Bob") == PlayerStatus.PENDING_RESPONSE
        
        # Test: Remove Alice from lobby
        empty_lobby.remove_player("Alice")
        
        # Verify: Bob's status should return to AVAILABLE
        assert empty_lobby.get_player_status("Bob") == PlayerStatus.AVAILABLE
        
        # Verify: Request should be removed
        assert empty_lobby.get_pending_request("Bob") is None

    def test_lobby_remove_player_cancels_requests_as_receiver(self, empty_lobby: Lobby):
        # Test that removing request receiver cancels the request
        
        # Setup: Add players and create request
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        
        empty_lobby.send_game_request("Alice", "Bob")
        
        # Verify request exists
        assert empty_lobby.get_pending_request("Bob") is not None
        assert empty_lobby.get_player_status("Alice") == PlayerStatus.REQUESTING_GAME
        
        # Test: Remove Bob (receiver) from lobby
        empty_lobby.remove_player("Bob")
        
        # Verify: Alice's status should return to AVAILABLE
        assert empty_lobby.get_player_status("Alice") == PlayerStatus.AVAILABLE
        
        # Verify: Request should be implicitly cancelled (no receiver)
        assert empty_lobby.get_pending_request("Bob") is None

    def test_lobby_clear_all_except_cancels_other_players_requests(self, empty_lobby: Lobby):
        # Test that clear_all_except cancels requests involving removed players
        
        # Setup: Add multiple players with requests
        empty_lobby.add_player("Alice", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Bob", PlayerStatus.AVAILABLE)
        empty_lobby.add_player("Charlie", PlayerStatus.AVAILABLE)
        
        # Create request: Alice->Bob  
        empty_lobby.send_game_request("Alice", "Bob")
        
        # Verify request exists
        assert empty_lobby.get_pending_request("Bob") is not None
        
        # Test: Clear all except Charlie
        empty_lobby.clear_all_except("Charlie")
        
        # Verify: Only Charlie remains
        assert "Alice" not in empty_lobby.players
        assert "Bob" not in empty_lobby.players
        assert "Charlie" in empty_lobby.players
        
        # Verify: Request should be implicitly cancelled
        assert empty_lobby.get_pending_request("Bob") is None


class TestLobbyGameRequestStateTransitions:
    """Unit tests for game request state transitions and edge cases"""

    def test_send_request_to_player_with_pending_response_fails(self, empty_lobby: Lobby):
        # Test that cannot send request to player who already has pending response
        lobby_service = LobbyService(empty_lobby)
        
        # Setup: Add three players, Alice->Bob request
        lobby_service.join_lobby("Alice")
        lobby_service.join_lobby("Bob")
        lobby_service.join_lobby("Charlie")
        lobby_service.send_game_request("Alice", "Bob")
        
        # Test: Charlie tries to send request to Bob (who has PENDING_RESPONSE)
        with pytest.raises(ValueError, match="Receiver Bob is not available"):
            lobby_service.send_game_request("Charlie", "Bob")

    def test_send_request_from_requesting_game_player_fails(self, empty_lobby: Lobby):
        # Test that player with REQUESTING_GAME status cannot send another request
        lobby_service = LobbyService(empty_lobby)
        
        # Setup: Add three players, Alice->Bob request
        lobby_service.join_lobby("Alice")
        lobby_service.join_lobby("Bob")
        lobby_service.join_lobby("Charlie")
        lobby_service.send_game_request("Alice", "Bob")
        
        # Test: Alice tries to send another request while already requesting
        with pytest.raises(ValueError, match="Sender Alice is not available"):
            lobby_service.send_game_request("Alice", "Charlie")

    def test_accept_request_transitions_both_players_to_in_game(self, empty_lobby: Lobby):
        # Test that accepting request properly transitions both players to IN_GAME
        lobby_service = LobbyService(empty_lobby)
        
        # Setup: Add players and send request
        lobby_service.join_lobby("Alice")
        lobby_service.join_lobby("Bob")
        lobby_service.send_game_request("Alice", "Bob")
        
        # Test: Accept request
        sender, receiver = lobby_service.accept_game_request("Bob")
        
        # Verify: Both players are IN_GAME
        assert lobby_service.get_player_status("Alice") == PlayerStatus.IN_GAME
        assert lobby_service.get_player_status("Bob") == PlayerStatus.IN_GAME
        
        # Verify: Request is removed
        assert lobby_service.get_pending_request_for_player("Bob") is None
        
        # Verify: Returned names are correct
        assert sender == "Alice"
        assert receiver == "Bob"

    def test_decline_request_transitions_both_players_to_available(self, empty_lobby: Lobby):
        # Test that declining request properly transitions both players to AVAILABLE
        lobby_service = LobbyService(empty_lobby)
        
        # Setup: Add players and send request
        lobby_service.join_lobby("Alice")
        lobby_service.join_lobby("Bob")
        lobby_service.send_game_request("Alice", "Bob")
        
        # Test: Decline request
        sender = lobby_service.decline_game_request("Bob")
        
        # Verify: Both players are AVAILABLE
        assert lobby_service.get_player_status("Alice") == PlayerStatus.AVAILABLE
        assert lobby_service.get_player_status("Bob") == PlayerStatus.AVAILABLE
        
        # Verify: Request is removed
        assert lobby_service.get_pending_request_for_player("Bob") is None
        
        # Verify: Returned sender name is correct
        assert sender == "Alice"

    def test_multiple_concurrent_requests_different_pairs(self, empty_lobby: Lobby):
        # Test that multiple concurrent requests between different player pairs work
        lobby_service = LobbyService(empty_lobby)
        
        # Setup: Add four players
        lobby_service.join_lobby("Alice")
        lobby_service.join_lobby("Bob")
        lobby_service.join_lobby("Charlie")
        lobby_service.join_lobby("Diana")
        
        # Test: Send concurrent requests Alice->Bob, Charlie->Diana
        lobby_service.send_game_request("Alice", "Bob")
        lobby_service.send_game_request("Charlie", "Diana")
        
        # Verify: Both requests exist independently
        bob_request = lobby_service.get_pending_request_for_player("Bob")
        diana_request = lobby_service.get_pending_request_for_player("Diana")
        
        assert bob_request is not None
        assert diana_request is not None
        assert bob_request.sender == "Alice"
        assert diana_request.sender == "Charlie"
        
        # Verify: All players have correct statuses
        assert lobby_service.get_player_status("Alice") == PlayerStatus.REQUESTING_GAME
        assert lobby_service.get_player_status("Bob") == PlayerStatus.PENDING_RESPONSE
        assert lobby_service.get_player_status("Charlie") == PlayerStatus.REQUESTING_GAME
        assert lobby_service.get_player_status("Diana") == PlayerStatus.PENDING_RESPONSE

    def test_request_to_self_fails(self, empty_lobby: Lobby):
        # Test that player cannot send game request to themselves
        lobby_service = LobbyService(empty_lobby)
        
        # Setup: Add player
        lobby_service.join_lobby("Alice")
        
        # Test: Alice tries to send request to herself
        with pytest.raises(ValueError):
            lobby_service.send_game_request("Alice", "Alice")

    def test_game_request_timestamp_is_set(self, empty_lobby: Lobby):
        # Test that game requests have timestamps
        lobby_service = LobbyService(empty_lobby)
        
        # Setup: Add players and send request
        lobby_service.join_lobby("Alice")
        lobby_service.join_lobby("Bob")
        
        before_request = datetime.now()
        lobby_service.send_game_request("Alice", "Bob")
        after_request = datetime.now()
        
        # Test: Request should have timestamp between before and after
        request = lobby_service.get_pending_request_for_player("Bob")
        assert request is not None
        assert before_request <= request.timestamp <= after_request


class TestLobbyServiceGameStateManagement:
    """Unit tests for game state management in lobby service"""

    def test_get_lobby_players_filters_in_game_players_for_lobby_view(self, empty_lobby: Lobby):
        # Test that IN_GAME players are handled appropriately in lobby views
        lobby_service = LobbyService(empty_lobby)
        
        # Setup: Add players, some go to game
        lobby_service.join_lobby("Alice")
        lobby_service.join_lobby("Bob")
        lobby_service.join_lobby("Charlie")
        lobby_service.join_lobby("Diana")
        
        # Alice and Bob start a game
        lobby_service.send_game_request("Alice", "Bob")
        lobby_service.accept_game_request("Bob")
        
        # Test: Charlie's lobby view should show all players including IN_GAME
        charlie_view = lobby_service.get_lobby_players_for_player("Charlie")
        charlie_names = [p.name for p in charlie_view]
        
        # get_lobby_players_for_player should return ALL players except requesting player
        # It's up to the template/UI layer to filter for display
        assert "Alice" in charlie_names
        assert "Bob" in charlie_names
        assert "Diana" in charlie_names
        assert "Charlie" not in charlie_names

    def test_get_available_players_excludes_in_game_players(self, empty_lobby: Lobby):
        # Test that get_available_players excludes IN_GAME players
        lobby_service = LobbyService(empty_lobby)
        
        # Setup: Add players, some go to game
        lobby_service.join_lobby("Alice")
        lobby_service.join_lobby("Bob")
        lobby_service.join_lobby("Charlie")
        
        # Alice and Bob start a game
        lobby_service.send_game_request("Alice", "Bob")
        lobby_service.accept_game_request("Bob")
        
        # Test: get_available_players should only return AVAILABLE players
        available_players = lobby_service.get_available_players()
        available_names = [p.name for p in available_players]
        
        assert "Charlie" in available_names  # AVAILABLE
        assert "Alice" not in available_names  # IN_GAME
        assert "Bob" not in available_names  # IN_GAME
        assert len(available_names) == 1

    def test_lobby_data_consistency_after_game_transitions(self, empty_lobby: Lobby):
        # Test that lobby data remains consistent through game state transitions
        lobby_service = LobbyService(empty_lobby)
        
        # Setup: Complex scenario with multiple state changes
        lobby_service.join_lobby("Alice")
        lobby_service.join_lobby("Bob")
        lobby_service.join_lobby("Charlie")
        lobby_service.join_lobby("Diana")
        
        # Step 1: Alice->Bob request
        lobby_service.send_game_request("Alice", "Bob")
        available_after_request = lobby_service.get_available_players()
        assert len(available_after_request) == 2  # Charlie, Diana
        
        # Step 2: Bob declines
        lobby_service.decline_game_request("Bob")
        available_after_decline = lobby_service.get_available_players()
        assert len(available_after_decline) == 4  # All back to AVAILABLE
        
        # Step 3: Charlie->Diana request and accept
        lobby_service.send_game_request("Charlie", "Diana")
        lobby_service.accept_game_request("Diana")
        available_after_accept = lobby_service.get_available_players()
        assert len(available_after_accept) == 2  # Alice, Bob
        
        # Verify final state consistency
        charlie_diana_names = [p.name for p in available_after_accept]
        assert "Alice" in charlie_diana_names
        assert "Bob" in charlie_diana_names
        assert "Charlie" not in charlie_diana_names  # IN_GAME
        assert "Diana" not in charlie_diana_names  # IN_GAME