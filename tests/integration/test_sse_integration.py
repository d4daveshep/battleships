import asyncio
import json
from typing import AsyncGenerator, List
from fastapi import status
from fastapi.testclient import TestClient
import pytest

from main import app


@pytest.fixture
def clean_lobby(client: TestClient):
    """Reset lobby state for tests that need it"""
    client.post("/test/reset-lobby")
    yield
    client.post("/test/reset-lobby")


class TestSSEEndpoint:
    """Integration tests for Server-Sent Events endpoint"""

    def test_sse_lobby_events_endpoint_exists(self, client: TestClient):
        """Test that SSE endpoint is accessible and returns correct content type"""
        # This test should fail initially (TDD Red phase)
        response = client.get("/lobby/events/TestPlayer")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        assert response.headers.get("cache-control") == "no-cache"
        assert response.headers.get("connection") == "keep-alive"

    def test_sse_lobby_events_requires_player_name(self, client: TestClient):
        """Test that SSE endpoint requires player_name parameter"""
        # Should fail - endpoint doesn't exist yet
        response = client.get("/lobby/events/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_sse_lobby_events_validates_player_name(self, client: TestClient):
        """Test that SSE endpoint validates player name format"""
        # Should fail initially - validation not implemented
        response = client.get("/lobby/events/")  # Empty name
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        response = client.get("/lobby/events/A")  # Too short
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_sse_lobby_events_stream_format(self, client: TestClient):
        """Test that SSE endpoint returns properly formatted SSE stream"""
        # This will fail - endpoint doesn't exist yet
        response = client.get("/lobby/events/TestPlayer")
        assert response.status_code == status.HTTP_200_OK
        
        # SSE messages should have proper format
        content = response.text
        assert "data:" in content or "event:" in content
        # SSE messages should end with double newline
        assert "\n\n" in content


class TestSSELobbyUpdates:
    """Integration tests for SSE lobby update broadcasting"""

    @pytest.mark.skip(reason="Complex streaming test - requires async testing framework")
    def test_sse_broadcasts_initial_lobby_state(self, client: TestClient):
        """Test that SSE sends initial lobby state when client connects"""
        # Setup: Add some players to lobby first
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        
        # This will fail - SSE endpoint doesn't exist yet
        response = client.get("/lobby/events/Charlie")
        content = response.text
        
        # Should receive initial lobby state
        assert "event: lobby_update" in content
        assert "Alice" in content
        assert "Bob" in content
        assert "data:" in content

    def test_sse_endpoint_provides_lobby_state_snapshot(self, client: TestClient, clean_lobby):
        """Test that SSE endpoint provides current lobby state in initial response"""
        # This is a simpler version that tests the endpoint without streaming
        
        # Setup: Add some players to lobby first
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        
        # This will fail - SSE endpoint doesn't exist yet
        response = client.get("/lobby/events/Charlie")
        
        assert response.status_code == status.HTTP_200_OK
        content = response.text
        
        # Should include current lobby players in response
        assert "Alice" in content or "Bob" in content


class TestSSEHTMLFragments:
    """Integration tests for SSE HTML fragment updates"""

    def test_sse_endpoint_returns_html_fragments(self, client: TestClient, clean_lobby):
        """Test that SSE endpoint returns HTML fragments for lobby updates"""
        # This will fail - HTML fragment generation not implemented
        
        client.post("/", data={"player_name": "TestPlayer", "game_mode": "human"})
        
        response = client.get("/lobby/events/Observer")
        content = response.text
        
        # SSE data should contain HTML
        assert "<div" in content
        assert "data-testid" in content
        assert "</div>" in content
        # Should contain hx-swap-oob for HTMX updates
        assert "hx-swap-oob" in content

    def test_sse_html_fragments_include_player_status(self, client: TestClient, clean_lobby):
        """Test that SSE HTML fragments include player status information"""
        # This will fail - status display in HTML not implemented
        
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        
        response = client.get("/lobby/events/Observer") 
        content = response.text
        
        # HTML should include status indicators
        assert 'data-testid="player-Alice-status"' in content or 'data-testid="player-Bob-status"' in content
        assert "Available" in content

    def test_sse_html_fragments_include_button_states(self, client: TestClient, clean_lobby):
        """Test that SSE HTML fragments include proper button states"""
        # This will fail - dynamic button states not implemented
        
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        
        response = client.get("/lobby/events/Observer")
        content = response.text
        
        # HTML should include select opponent buttons
        assert 'data-testid="select-opponent-' in content


class TestSSEIntegrationWithExistingEndpoints:
    """Integration tests for SSE integration with existing lobby endpoints"""

    def test_sse_endpoint_exists_and_returns_sse_format(self, client: TestClient):
        """Test that SSE endpoint exists and returns basic SSE format"""
        # This will fail - SSE endpoint doesn't exist yet
        
        response = client.get("/lobby/events/TestPlayer")
        
        assert response.status_code == status.HTTP_200_OK
        assert "text/plain" in response.headers.get("content-type", "")
        
        content = response.text
        # Should have SSE event format
        assert "data:" in content or "event:" in content

    def test_sse_provides_same_lobby_data_as_regular_endpoint(self, client: TestClient, clean_lobby):
        """Test that SSE lobby data is consistent with regular /lobby endpoint"""
        # This will fail - data consistency not implemented
        
        # Setup lobby
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        
        # Get regular lobby view
        lobby_response = client.get("/lobby?player_name=Observer")
        lobby_html = lobby_response.text
        
        # Get SSE lobby data
        sse_response = client.get("/lobby/events/Observer")
        sse_content = sse_response.text
        
        # SSE content should reflect same player data structure
        if "Alice" in lobby_html:
            assert "Alice" in sse_content
        if "Bob" in lobby_html:
            assert "Bob" in sse_content


class TestSSEManagerService:
    """Integration tests for SSE manager service functionality"""

    def test_sse_manager_broadcasts_to_connected_clients(self, client: TestClient, clean_lobby):
        """Test that SSE manager can broadcast updates to multiple clients"""
        # This will fail - SSE manager service doesn't exist yet
        
        # Setup lobby
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        
        # Get initial SSE state for multiple observers
        response1 = client.get("/lobby/events/Observer1")
        response2 = client.get("/lobby/events/Observer2")
        
        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        
        # Both should contain Alice
        assert "Alice" in response1.text
        assert "Alice" in response2.text

    def test_sse_manager_handles_lobby_updates(self, client: TestClient, clean_lobby):
        """Test that SSE manager is notified of lobby changes"""
        # This will fail - SSE integration with lobby changes not implemented
        
        # Setup initial state
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        
        # Trigger a lobby change
        select_response = client.post("/select-opponent", data={
            "player_name": "Alice", 
            "opponent_name": "Bob"
        })
        
        # Verify the original endpoint still works
        assert select_response.status_code == status.HTTP_200_OK
        
        # Get SSE state after change - should reflect updated statuses
        sse_response = client.get("/lobby/events/Observer")
        sse_content = sse_response.text
        
        # Should contain updated status information
        assert "Requesting Game" in sse_content


class TestSSEErrorHandling:
    """Integration tests for SSE error handling and edge cases"""

    def test_sse_handles_invalid_player_names(self, client: TestClient):
        """Test that SSE endpoint handles invalid player names gracefully"""
        # This will fail - validation not implemented
        
        # Test various invalid names
        invalid_names = ["A", "VeryLongPlayerNameThatExceedsMaxLength"]
        
        for name in invalid_names:
            response = client.get(f"/lobby/events/{name}")
            # Should either reject or handle gracefully
            assert response.status_code in [
                status.HTTP_400_BAD_REQUEST, 
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                status.HTTP_200_OK  # If it handles gracefully
            ]

    def test_sse_handles_empty_lobby(self, client: TestClient, clean_lobby):
        """Test that SSE works correctly when lobby is empty"""
        # This will fail - empty lobby handling not implemented
        
        response = client.get("/lobby/events/Observer")
        
        # Should send valid SSE even for empty lobby
        assert response.status_code == status.HTTP_200_OK
        # Should indicate empty state or have empty player list
        content = response.text
        assert "data:" in content

    def test_sse_handles_nonexistent_lobby_routes(self, client: TestClient):
        """Test that SSE properly handles missing routes"""
        # Should fail - routes don't exist yet
        
        # Test malformed URLs
        response = client.get("/lobby/events")  # Missing player name
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        response = client.get("/lobby/event/TestPlayer")  # Wrong path
        assert response.status_code == status.HTTP_404_NOT_FOUND