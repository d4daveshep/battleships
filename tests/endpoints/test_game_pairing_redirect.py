"""
Endpoint tests for game pairing and redirect functionality.

These tests follow the TDD RED phase for the opponent name discovery
when a player with IN_GAME status is redirected to the game interface.

Tests should fail initially as the pairing lookup is not yet implemented.
"""

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_lobby(client):
    """Reset lobby state before each test"""
    response = client.post("/test/reset-lobby")
    assert response.status_code == 200
    yield
    # Cleanup after test
    client.post("/test/reset-lobby")


class TestGamePairingRedirect:
    """Tests for correct opponent name in game redirect"""

    def test_sender_redirected_with_correct_opponent_after_acceptance(self, client):
        """Test that game requester is redirected with correct opponent name"""
        # Alice and Bob join lobby
        client.post("/", data={"player_name": "Alice", "game_mode": "Two Player"})
        client.post("/", data={"player_name": "Bob", "game_mode": "Two Player"})

        # Alice sends game request to Bob
        client.post("/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"})

        # Bob accepts the request (Bob gets immediate redirect with opponent)
        response = client.post("/accept-game-request", data={"player_name": "Bob"})
        assert response.status_code == 302
        assert "opponent_name=Alice" in response.headers["location"]

        # Alice polls for status - should get redirect with correct opponent
        response = client.get("/lobby/status/Alice")

        # Should be a redirect response
        assert response.status_code == 204, "Should return 204 with HX-Redirect header"
        assert "HX-Redirect" in response.headers, "Should have HX-Redirect header"

        # The redirect URL should contain Bob as opponent
        redirect_url = response.headers["HX-Redirect"]
        assert "opponent_name=Bob" in redirect_url, f"Redirect should contain opponent Bob, got: {redirect_url}"
        assert "player_name=Alice" in redirect_url, f"Redirect should contain player Alice, got: {redirect_url}"

    def test_receiver_redirected_with_correct_opponent_immediately(self, client):
        """Test that game receiver gets correct opponent in immediate redirect"""
        # Alice and Bob join lobby
        client.post("/", data={"player_name": "Alice", "game_mode": "Two Player"})
        client.post("/", data={"player_name": "Bob", "game_mode": "Two Player"})

        # Alice sends game request to Bob
        client.post("/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"})

        # Bob accepts the request
        response = client.post("/accept-game-request", data={"player_name": "Bob"})

        assert response.status_code == 302
        redirect_url = response.headers["location"]
        assert "opponent_name=Alice" in redirect_url, "Bob should be redirected with Alice as opponent"
        assert "player_name=Bob" in redirect_url

    def test_both_players_can_discover_each_other_as_opponents(self, client):
        """Test that both players in a matched game can find their opponent"""
        # Alice and Bob join lobby
        client.post("/", data={"player_name": "Alice", "game_mode": "Two Player"})
        client.post("/", data={"player_name": "Bob", "game_mode": "Two Player"})

        # Alice sends game request to Bob
        client.post("/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"})

        # Bob accepts
        client.post("/accept-game-request", data={"player_name": "Bob"})

        # Check Alice's status
        alice_response = client.get("/lobby/status/Alice")
        assert alice_response.status_code == 204
        alice_redirect = alice_response.headers["HX-Redirect"]
        assert "opponent_name=Bob" in alice_redirect

        # Check Bob's status (in case they poll again)
        bob_response = client.get("/lobby/status/Bob")
        assert bob_response.status_code == 204
        bob_redirect = bob_response.headers["HX-Redirect"]
        assert "opponent_name=Alice" in bob_redirect

    def test_multiple_concurrent_games_have_correct_pairings(self, client):
        """Test that multiple simultaneous games maintain correct opponent pairings"""
        # Four players join
        client.post("/", data={"player_name": "Alice", "game_mode": "Two Player"})
        client.post("/", data={"player_name": "Bob", "game_mode": "Two Player"})
        client.post("/", data={"player_name": "Charlie", "game_mode": "Two Player"})
        client.post("/", data={"player_name": "Diana", "game_mode": "Two Player"})

        # Two separate game requests
        client.post("/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"})
        client.post("/select-opponent", data={"player_name": "Charlie", "opponent_name": "Diana"})

        # Both requests accepted
        client.post("/accept-game-request", data={"player_name": "Bob"})
        client.post("/accept-game-request", data={"player_name": "Diana"})

        # Verify each player is paired correctly
        alice_response = client.get("/lobby/status/Alice")
        assert "opponent_name=Bob" in alice_response.headers["HX-Redirect"]

        bob_response = client.get("/lobby/status/Bob")
        assert "opponent_name=Alice" in bob_response.headers["HX-Redirect"]

        charlie_response = client.get("/lobby/status/Charlie")
        assert "opponent_name=Diana" in charlie_response.headers["HX-Redirect"]

        diana_response = client.get("/lobby/status/Diana")
        assert "opponent_name=Charlie" in diana_response.headers["HX-Redirect"]

    def test_no_opponent_found_handles_gracefully(self, client):
        """Test that system handles edge case where opponent cannot be found"""
        # This is an edge case that shouldn't happen in normal flow,
        # but we should handle it gracefully

        # Manually set a player to IN_GAME without a pairing
        # (This would require direct lobby manipulation in a real scenario)
        # For now, we document this as a future edge case test

        # If we can't find an opponent, we should either:
        # 1. Return an error message
        # 2. Use a default/fallback value
        # 3. Log an error and keep them in lobby

        # This test documents the expected behavior once implemented
        pass

    def test_long_poll_endpoint_also_uses_correct_opponent(self, client):
        """Test that long polling endpoint also redirects with correct opponent"""
        # Alice and Bob join lobby
        client.post("/", data={"player_name": "Alice", "game_mode": "Two Player"})
        client.post("/", data={"player_name": "Bob", "game_mode": "Two Player"})

        # Alice sends game request to Bob
        client.post("/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"})

        # Bob accepts
        client.post("/accept-game-request", data={"player_name": "Bob"})

        # Alice uses long-poll endpoint
        response = client.get("/lobby/status/Alice/long-poll")

        assert response.status_code == 204
        assert "HX-Redirect" in response.headers
        redirect_url = response.headers["HX-Redirect"]
        assert "opponent_name=Bob" in redirect_url, f"Long poll should redirect with correct opponent, got: {redirect_url}"


class TestGamePairingEdgeCases:
    """Tests for edge cases in game pairing"""

    def test_declined_request_does_not_create_pairing(self, client):
        """Test that declined requests don't create opponent pairings"""
        # Alice and Bob join lobby
        client.post("/", data={"player_name": "Alice", "game_mode": "Two Player"})
        client.post("/", data={"player_name": "Bob", "game_mode": "Two Player"})

        # Alice sends game request to Bob
        client.post("/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"})

        # Bob declines the request
        client.post("/decline-game-request", data={"player_name": "Bob"})

        # Check that neither player is redirected to game
        alice_response = client.get("/lobby/status/Alice")
        assert alice_response.status_code == 200, "Alice should still be in lobby"
        assert "HX-Redirect" not in alice_response.headers

        bob_response = client.get("/lobby/status/Bob")
        assert bob_response.status_code == 200, "Bob should still be in lobby"
        assert "HX-Redirect" not in bob_response.headers

    def test_pairing_persists_across_multiple_status_checks(self, client):
        """Test that opponent pairing persists across multiple polls"""
        # Set up game
        client.post("/", data={"player_name": "Alice", "game_mode": "Two Player"})
        client.post("/", data={"player_name": "Bob", "game_mode": "Two Player"})
        client.post("/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"})
        client.post("/accept-game-request", data={"player_name": "Bob"})

        # Poll multiple times
        for _ in range(3):
            response = client.get("/lobby/status/Alice")
            assert response.status_code == 204
            assert "opponent_name=Bob" in response.headers["HX-Redirect"]
