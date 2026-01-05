"""
Endpoint tests for game pairing and redirect functionality.

These tests follow the TDD RED phase for the opponent name discovery
when a player with IN_GAME status is redirected to the game interface.

Tests should fail initially as the pairing lookup is not yet implemented.
"""

from fastapi.testclient import TestClient
from test_helpers import accept_game_request, send_game_request


class TestGamePairingRedirect:
    """Tests for correct opponent name in game redirect"""

    def test_sender_redirected_with_correct_opponent_after_acceptance(
        self, game_request_pending: tuple[TestClient, TestClient]
    ):
        """Test that game requester is redirected with correct opponent name"""
        alice_client, bob_client = game_request_pending

        # Bob accepts the request (Bob gets immediate redirect)
        response = accept_game_request(bob_client, follow_redirects=False)
        assert response.status_code == 302
        # Player and opponent info from session/lobby state
        assert response.headers["location"] == "/start-game"

        # Alice polls for status - should get redirect with correct opponent
        response = alice_client.get("/lobby/status")

        # Should be a redirect response
        assert response.status_code == 204, "Should return 204 with HX-Redirect header"
        assert "HX-Redirect" in response.headers, "Should have HX-Redirect header"

        redirect_url = response.headers["HX-Redirect"]
        assert "/start-game" in redirect_url, (
            f"Redirect URL should contain /start-game, got: {redirect_url}"
        )
        # Both player and opponent now come from session/lobby state
        assert redirect_url == "/start-game", (
            f"Redirect should be clean /start-game URL, got: {redirect_url}"
        )

    def test_receiver_redirected_with_correct_opponent_immediately(
        self, game_request_pending: tuple[TestClient, TestClient]
    ):
        """Test that game receiver gets correct opponent in immediate redirect"""
        alice_client, bob_client = game_request_pending

        # Bob accepts the request
        response = accept_game_request(bob_client, follow_redirects=False)

        assert response.status_code == 302
        redirect_url = response.headers["location"]
        # Both player and opponent now come from session/lobby state
        assert redirect_url == "/start-game", (
            f"Redirect should be clean /start-game URL, got: {redirect_url}"
        )

    def test_both_players_can_discover_each_other_as_opponents(
        self, game_paired: tuple[TestClient, TestClient]
    ):
        """Test that both players in a matched game can find their opponent"""
        alice_client, bob_client = game_paired

        # Check Alice's status
        alice_response = alice_client.get("/lobby/status")
        assert alice_response.status_code == 204
        alice_redirect = alice_response.headers["HX-Redirect"]
        assert alice_redirect == "/start-game"

        # Check Bob's status (in case they poll again)
        bob_response = bob_client.get("/lobby/status")
        assert bob_response.status_code == 204
        bob_redirect = bob_response.headers["HX-Redirect"]
        assert bob_redirect == "/start-game"

    def test_multiple_concurrent_games_have_correct_pairings(
        self, charlie_client: TestClient, diana_client: TestClient
    ):
        """Test that multiple simultaneous games maintain correct opponent pairings"""
        # Create Alice and Bob separately for this test
        from main import app

        alice_client = TestClient(app)
        bob_client = TestClient(app)

        from test_helpers import create_player

        # Four players join with their respective clients
        create_player(alice_client, "Alice", "human")
        create_player(bob_client, "Bob", "human")
        # charlie_client and diana_client already created by fixtures

        # Two separate game requests
        send_game_request(alice_client, "Bob")
        send_game_request(charlie_client, "Diana")

        # Both requests accepted
        accept_game_request(bob_client)
        accept_game_request(diana_client)

        # Verify each player is paired correctly (all redirected to /start-game)
        alice_response = alice_client.get("/lobby/status")
        assert alice_response.headers["HX-Redirect"] == "/start-game"

        bob_response = bob_client.get("/lobby/status")
        assert bob_response.headers["HX-Redirect"] == "/start-game"

        charlie_response = charlie_client.get("/lobby/status")
        assert charlie_response.headers["HX-Redirect"] == "/start-game"

        diana_response = diana_client.get("/lobby/status")
        assert diana_response.headers["HX-Redirect"] == "/start-game"

    def test_long_poll_endpoint_also_uses_correct_opponent(
        self, game_paired: tuple[TestClient, TestClient]
    ):
        """Test that long polling endpoint also redirects with correct opponent"""
        alice_client, bob_client = game_paired

        # Alice uses long-poll endpoint
        response = alice_client.get("/lobby/status/long-poll")

        assert response.status_code == 204
        assert "HX-Redirect" in response.headers
        redirect_url = response.headers["HX-Redirect"]
        # Player and opponent info from session/lobby state
        assert redirect_url == "/start-game", (
            f"Long poll should redirect to clean /start-game URL, got: {redirect_url}"
        )


class TestGamePairingEdgeCases:
    """Tests for edge cases in game pairing"""

    def test_declined_request_does_not_create_pairing(
        self, game_request_pending: tuple[TestClient, TestClient]
    ):
        """Test that declined requests don't create opponent pairings"""
        alice_client, bob_client = game_request_pending

        # Bob declines the request
        from test_helpers import decline_game_request

        decline_game_request(bob_client)

        # Check that neither player is redirected to game
        alice_response = alice_client.get("/lobby/status")
        assert alice_response.status_code == 200, "Alice should still be in lobby"
        assert "HX-Redirect" not in alice_response.headers

        bob_response = bob_client.get("/lobby/status")
        assert bob_response.status_code == 200, "Bob should still be in lobby"
        assert "HX-Redirect" not in bob_response.headers

    def test_pairing_persists_across_multiple_status_checks(
        self, game_paired: tuple[TestClient, TestClient]
    ):
        """Test that opponent pairing persists across multiple polls"""
        alice_client, bob_client = game_paired

        # Poll multiple times
        for _ in range(3):
            response = alice_client.get("/lobby/status")
            assert response.status_code == 204
            # Player and opponent info from session/lobby state
            assert response.headers["HX-Redirect"] == "/start-game"
