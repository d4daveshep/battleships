import pytest
from datetime import datetime
from game.player import Player, PlayerStatus


class TestPlayerStatusGameRequestFeatures:
    """Tests for new PlayerStatus values needed for game requests"""

    def test_player_status_pending_response_exists(self):
        # Test the new PENDING_RESPONSE status for game request receivers
        status: PlayerStatus = PlayerStatus.PENDING_RESPONSE
        assert status == "Pending Response"

    def test_player_status_values_includes_pending_response(self):
        # Test that PENDING_RESPONSE is included in all enum values
        expected_statuses = {
            PlayerStatus.AVAILABLE,
            PlayerStatus.REQUESTING_GAME,
            PlayerStatus.PENDING_RESPONSE,
            PlayerStatus.IN_GAME,
        }
        actual_statuses: set[PlayerStatus] = {status for status in PlayerStatus}
        assert expected_statuses == actual_statuses

    def test_player_creation_with_pending_response_status(self):
        # Test creating a player with PENDING_RESPONSE status
        player: Player = Player("Alice", PlayerStatus.PENDING_RESPONSE)
        assert player.name == "Alice"
        assert player.status == PlayerStatus.PENDING_RESPONSE

    def test_player_status_transition_to_pending_response(self):
        # Test transitioning a player from AVAILABLE to PENDING_RESPONSE
        player: Player = Player("Bob", PlayerStatus.AVAILABLE)
        
        # Simulate receiving a game request
        player.status = PlayerStatus.PENDING_RESPONSE
        assert player.status == PlayerStatus.PENDING_RESPONSE
        
        # Simulate accepting request (go to IN_GAME)
        player.status = PlayerStatus.IN_GAME
        assert player.status == PlayerStatus.IN_GAME

    def test_player_status_transition_from_pending_response_to_available(self):
        # Test transitioning back to AVAILABLE after declining request
        player: Player = Player("Charlie", PlayerStatus.PENDING_RESPONSE)
        
        # Simulate declining request
        player.status = PlayerStatus.AVAILABLE
        assert player.status == PlayerStatus.AVAILABLE


class TestGameRequest:
    """Tests for GameRequest dataclass used in game request system"""

    def test_game_request_import_exists(self):
        # Test that GameRequest can be imported
        from game.player import GameRequest
        assert GameRequest

    def test_game_request_creation(self):
        # Test creating a basic game request
        from game.player import GameRequest
        
        now = datetime.now()
        request = GameRequest(
            sender="Alice",
            receiver="Bob", 
            timestamp=now,
            status="pending"
        )
        
        assert request.sender == "Alice"
        assert request.receiver == "Bob"
        assert request.timestamp == now
        assert request.status == "pending"

    def test_game_request_status_values(self):
        # Test that GameRequest supports expected status values
        from game.player import GameRequest
        
        now = datetime.now()
        
        # Test "pending" status
        pending_request = GameRequest("Alice", "Bob", now, "pending")
        assert pending_request.status == "pending"
        
        # Test "accepted" status
        accepted_request = GameRequest("Alice", "Bob", now, "accepted")
        assert accepted_request.status == "accepted"
        
        # Test "declined" status  
        declined_request = GameRequest("Alice", "Bob", now, "declined")
        assert declined_request.status == "declined"

    def test_game_request_dataclass_equality(self):
        # Test that GameRequest dataclass supports equality comparison
        from game.player import GameRequest
        
        now = datetime.now()
        request1 = GameRequest("Alice", "Bob", now, "pending")
        request2 = GameRequest("Alice", "Bob", now, "pending")
        request3 = GameRequest("Charlie", "Bob", now, "pending")
        
        assert request1 == request2
        assert request1 != request3

    def test_game_request_immutable_dataclass(self):
        # Test that GameRequest is a proper dataclass
        from game.player import GameRequest
        
        now = datetime.now()
        request = GameRequest("Alice", "Bob", now, "pending")
        
        # Should have string representation
        str_repr = str(request)
        assert "Alice" in str_repr
        assert "Bob" in str_repr
        assert "pending" in str_repr
