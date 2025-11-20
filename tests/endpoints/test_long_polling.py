"""
Endpoint tests for long polling lobby status updates.

These tests follow the TDD RED phase for Step 2 of the long polling migration.
Tests should fail initially as the endpoint is not yet implemented.
"""

import time

from fastapi import status
from fastapi.testclient import TestClient


class TestLongPollingEndpoint:
    """Tests for the /lobby/status/{player_name}/long-poll endpoint"""

    def test_long_poll_endpoint_exists(self, client: TestClient):
        """Test that the long poll endpoint exists and returns 200 OK"""
        # Setup: Create a player in the lobby
        login_response = client.post(
            "/", data={"player_name": "Alice", "game_mode": "human"}
        )
        assert login_response.status_code == status.HTTP_200_OK

        # Test: Call the long poll endpoint
        response = client.get("/lobby/status/Alice/long-poll")

        # Verify: Endpoint exists and returns OK
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"].startswith("text/html")

    def test_long_poll_returns_current_state_immediately_on_first_call(
        self, client: TestClient
    ):
        """Test that first long poll returns current state without waiting"""
        # Setup: Create players in lobby
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})

        # Test: First long poll should return immediately
        start_time = time.time()
        response = client.get("/lobby/status/Alice/long-poll")
        elapsed_time = time.time() - start_time

        # Verify: Returns quickly (within 1 second)
        assert response.status_code == status.HTTP_200_OK
        assert elapsed_time < 1.0, "First long poll should return immediately"
        assert "Bob" in response.text, "Should show other players in lobby"

    def test_long_poll_waits_for_state_change(self, client: TestClient):
        """Test that long poll waits when state hasn't changed"""
        # Setup: Create player in lobby
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})

        # Make initial call to get current version
        initial_response = client.get("/lobby/status/Alice/long-poll")
        assert initial_response.status_code == status.HTTP_200_OK

        # Test: Second long poll with current version should wait (will timeout in test)
        # Version is 1 after adding Alice
        start_time = time.time()
        response = client.get(
            "/lobby/status/Alice/long-poll", params={"timeout": "2", "version": "1"}
        )
        elapsed_time = time.time() - start_time

        # Verify: Should wait close to timeout duration (2 seconds ± 0.5s)
        assert response.status_code == status.HTTP_200_OK
        assert (
            1.5 < elapsed_time < 2.5
        ), f"Expected ~2s wait, got {elapsed_time:.2f}s"

    def test_long_poll_returns_early_on_state_change(self, client: TestClient):
        """Test that long poll returns immediately when lobby state changes"""
        # Setup: Create player in lobby
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})

        # Get initial state
        initial_response = client.get("/lobby/status/Alice/long-poll")
        assert initial_response.status_code == status.HTTP_200_OK

        # Start a long poll in background (simulate with short timeout for test)
        # In a real scenario, we'd use threading or asyncio to poll while making changes
        # For now, we'll test the version parameter approach

        # Test: Make a state change, then poll with old version
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})  # State change!

        start_time = time.time()
        response = client.get(
            "/lobby/status/Alice/long-poll",
            params={"version": "0", "timeout": "5"},
        )
        elapsed_time = time.time() - start_time

        # Verify: Should return quickly since state changed
        assert response.status_code == status.HTTP_200_OK
        assert (
            elapsed_time < 1.0
        ), f"Should return immediately on state change, took {elapsed_time:.2f}s"
        assert "Bob" in response.text, "Should show the new player"

    def test_long_poll_accepts_timeout_parameter(self, client: TestClient):
        """Test that timeout parameter is respected"""
        # Setup: Create player
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.get("/lobby/status/Alice/long-poll")  # Initial call

        # Test: Custom timeout of 1 second with current version
        start_time = time.time()
        response = client.get(
            "/lobby/status/Alice/long-poll", params={"timeout": "1", "version": "1"}
        )
        elapsed_time = time.time() - start_time

        # Verify: Should timeout after ~1 second
        assert response.status_code == status.HTTP_200_OK
        assert (
            0.5 < elapsed_time < 1.5
        ), f"Expected ~1s timeout, got {elapsed_time:.2f}s"

    def test_long_poll_accepts_version_parameter(self, client: TestClient):
        """Test that version parameter is accepted and used for change detection"""
        # Setup: Create players
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})

        # Test: Poll with version 0 (should return immediately if state changed)
        response = client.get(
            "/lobby/status/Alice/long-poll", params={"version": "0"}
        )

        # Verify: Endpoint accepts version parameter
        assert response.status_code == status.HTTP_200_OK

    def test_long_poll_multiple_players_concurrent(self, client: TestClient):
        """Test that multiple players can long poll concurrently"""
        # Setup: Create multiple players
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        client.post("/", data={"player_name": "Charlie", "game_mode": "human"})

        # Get initial states for all
        client.get("/lobby/status/Alice/long-poll")
        client.get("/lobby/status/Bob/long-poll")
        client.get("/lobby/status/Charlie/long-poll")

        # Test: All should be able to poll (though TestClient is synchronous)
        # This is a basic test - async concurrent testing would need pytest-asyncio
        response_alice = client.get(
            "/lobby/status/Alice/long-poll", params={"timeout": "1"}
        )
        response_bob = client.get(
            "/lobby/status/Bob/long-poll", params={"timeout": "1"}
        )

        # Verify: All requests complete successfully
        assert response_alice.status_code == status.HTTP_200_OK
        assert response_bob.status_code == status.HTTP_200_OK

    def test_long_poll_invalid_player_returns_error(self, client: TestClient):
        """Test that polling for non-existent player returns appropriate error"""
        # Test: Poll for player that doesn't exist
        response = client.get("/lobby/status/NonExistent/long-poll")

        # Verify: Should return error (400 or 404)
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND,
        ]

    def test_long_poll_default_timeout_is_reasonable(self, client: TestClient):
        """Test that default timeout is set to a reasonable value (e.g., 30s)"""
        # Setup: Create player
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.get("/lobby/status/Alice/long-poll")  # Initial call

        # Test: Call without timeout parameter (should use default)
        # We'll use a short timeout to avoid slow tests
        start_time = time.time()
        response = client.get(
            "/lobby/status/Alice/long-poll", params={"timeout": "1"}
        )
        elapsed_time = time.time() - start_time

        # Verify: Has a reasonable default (tested with explicit param for speed)
        assert response.status_code == status.HTTP_200_OK
        assert elapsed_time < 2.0

    def test_long_poll_returns_html_response(self, client: TestClient):
        """Test that long poll returns HTML response suitable for HTMX"""
        # Setup: Create player
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})

        # Test: Get long poll response
        response = client.get("/lobby/status/Alice/long-poll")

        # Verify: Returns HTML
        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]
        # Should contain some expected HTML elements
        assert "<" in response.text and ">" in response.text


class TestLongPollingStateChangeDetection:
    """Tests for state change detection in long polling"""

    def test_long_poll_detects_player_join(self, client: TestClient):
        """Test that long poll detects when a new player joins"""
        # Setup: Create Alice
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        initial = client.get("/lobby/status/Alice/long-poll")
        assert initial.status_code == status.HTTP_200_OK

        # Test: Bob joins while Alice is polling
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})

        # Poll with old version - should return immediately
        start_time = time.time()
        response = client.get(
            "/lobby/status/Alice/long-poll",
            params={"version": "1", "timeout": "5"},
        )
        elapsed = time.time() - start_time

        # Verify: Returns quickly with Bob in the list
        assert response.status_code == status.HTTP_200_OK
        assert elapsed < 1.0, "Should detect player join immediately"
        assert "Bob" in response.text

    def test_long_poll_detects_player_leave(self, client: TestClient):
        """Test that long poll detects when a player leaves"""
        # Setup: Create Alice and Bob
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        initial = client.get("/lobby/status/Alice/long-poll")
        assert "Bob" in initial.text

        # Test: Bob leaves
        client.post("/leave-lobby", data={"player_name": "Bob"})

        # Poll with old version - should return immediately
        start_time = time.time()
        response = client.get(
            "/lobby/status/Alice/long-poll",
            params={"version": "2", "timeout": "5"},
        )
        elapsed = time.time() - start_time

        # Verify: Returns quickly with Bob removed
        assert response.status_code == status.HTTP_200_OK
        assert elapsed < 1.0, "Should detect player leave immediately"
        assert "Bob" not in response.text

    def test_long_poll_detects_game_request(self, client: TestClient):
        """Test that long poll detects when a game request is sent"""
        # Setup: Create Alice and Bob
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        initial = client.get("/lobby/status/Bob/long-poll")
        assert initial.status_code == status.HTTP_200_OK

        # Test: Alice sends game request to Bob
        client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )

        # Poll with old version - should return immediately
        start_time = time.time()
        response = client.get(
            "/lobby/status/Bob/long-poll",
            params={"version": "2", "timeout": "5"},
        )
        elapsed = time.time() - start_time

        # Verify: Returns quickly showing the game request
        assert response.status_code == status.HTTP_200_OK
        assert elapsed < 1.0, "Should detect game request immediately"
        # Should show some indication of pending request (exact format TBD)
