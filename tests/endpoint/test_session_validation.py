from fastapi import status
from fastapi.testclient import TestClient
from test_helpers import (
    accept_game_request,
    decline_game_request,
    decode_session,
    leave_lobby,
    send_game_request,
)

from main import app


class TestSessionCreation:
    """Verify sessions are created correctly on login"""

    def test_login_two_player_creates_session_with_player_id(
        self, alice_client: TestClient
    ):
        """Test that logging in for two player stores player-id in session"""
        # Verify session contains player_name
        assert "session" in alice_client.cookies
        session_data = decode_session(alice_client.cookies["session"])

        # This test expects player_name to be stored (not yet implemented)
        assert "player-id" in session_data, "Session should contain player-id"
        assert len(session_data["player-id"]) == 22

    def test_login_computer_creates_session_with_player_id(
        self, authenticated_client: TestClient
    ):
        """Test that logging in for computer mode also stores player-id in session"""
        # Verify session contains player_name
        session_data = decode_session(authenticated_client.cookies["session"])
        assert "player-id" in session_data
        assert len(session_data["player-id"]) == 22

    def test_two_players_have_independent_sessions(
        self, alice_client: TestClient, bob_client: TestClient
    ):
        """Test that different clients have different sessions"""
        # Verify they have different session data
        session1 = decode_session(alice_client.cookies["session"])
        session2 = decode_session(bob_client.cookies["session"])

        assert session1["player-id"]
        assert session2["player-id"]
        assert session1["player-id"] != session2["player-id"]


class TestLeaveLobbySessionValidation:
    """Test session validation for /leave-lobby endpoint"""

    def test_leave_lobby_succeeds_with_valid_session(self, alice_client: TestClient):
        """Test that player with valid session can leave lobby"""
        # Leave lobby with matching session
        # FIXME: change the /lobby endpoints to use player-id not player_name
        response = leave_lobby(alice_client, "Alice")

        # Should succeed (200 OK or redirect)
        # Without HX-Request header, returns 302, with HTMX returns 204
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_302_FOUND,
            status.HTTP_303_SEE_OTHER,
            status.HTTP_204_NO_CONTENT,
        ]

    def test_leave_lobby_fails_without_session(self, alice_client: TestClient):
        """Test that player without session cannot leave lobby"""
        # Create new client without session
        new_client = TestClient(app)
        new_client.post("/test/reset-lobby")  # Use same lobby state

        # Try to leave without session
        response = leave_lobby(new_client, "Alice")

        # Should fail with 401 Unauthorized
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_leave_lobby_fails_with_mismatched_session(
        self, alice_client: TestClient, bob_client: TestClient
    ):
        """Test that player cannot leave lobby using another player's name"""
        # Bob tries to leave using Alice's name (with Bob's session)
        response = leave_lobby(bob_client, "Alice")

        # Should fail with 403 Forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestSelectOpponentSessionValidation:
    """Test session validation for /select-opponent endpoint"""

    def test_select_opponent_succeeds_with_valid_session(
        self, two_player_lobby: tuple[TestClient, TestClient]
    ):
        """Test that player with valid session can send game request"""
        alice_client, bob_client = two_player_lobby

        # Alice sends request to Bob (with Alice's session)
        response = send_game_request(alice_client, "Alice", "Bob")

        # Should succeed
        assert response.status_code == status.HTTP_200_OK

    def test_select_opponent_fails_without_session(
        self, alice_client: TestClient, bob_client: TestClient
    ):
        """Test that request without session is rejected"""
        # Create client without session
        no_session_client = TestClient(app)

        # Try to send request without session
        response = send_game_request(no_session_client, "Alice", "Bob")

        # Should fail with 401 Unauthorized
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_select_opponent_fails_with_mismatched_session(
        self, alice_client: TestClient, bob_client: TestClient
    ):
        """Test that player cannot send request as another player"""
        # Bob tries to send request as Alice (using Bob's session)
        response = send_game_request(bob_client, "Alice", "Bob")

        # Should fail with 403 Forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestAcceptGameRequestSessionValidation:
    """Test session validation for /accept-game-request endpoint"""

    def test_accept_game_request_succeeds_with_valid_session(
        self, game_request_pending: tuple[TestClient, TestClient]
    ):
        """Test that player with valid session can accept request"""
        alice_client, bob_client = game_request_pending

        # Bob accepts with valid session
        response = accept_game_request(bob_client, "Bob")

        # Should succeed (200 OK or redirect)
        # Without HX-Request header, returns 302, with HTMX returns 204
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_302_FOUND,
            status.HTTP_303_SEE_OTHER,
            status.HTTP_204_NO_CONTENT,
        ]

    def test_accept_game_request_fails_without_session(
        self, game_request_pending: tuple[TestClient, TestClient]
    ):
        """Test that accepting without session is rejected"""
        # Try to accept without session
        no_session_client = TestClient(app)
        response = accept_game_request(no_session_client, "Bob")

        # Should fail with 401 Unauthorized
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_accept_game_request_fails_with_mismatched_session(
        self,
        alice_client: TestClient,
        bob_client: TestClient,
        charlie_client: TestClient,
    ):
        """Test that player cannot accept request for another player"""
        # Setup: Alice sends request to Bob, Charlie exists
        send_game_request(alice_client, "Alice", "Bob")

        # Charlie tries to accept using Bob's name (with Charlie's session)
        response = accept_game_request(charlie_client, "Bob")

        # Should fail with 403 Forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestDeclineGameRequestSessionValidation:
    """Test session validation for /decline-game-request endpoint"""

    def test_decline_game_request_succeeds_with_valid_session(
        self, game_request_pending: tuple[TestClient, TestClient]
    ):
        """Test that player with valid session can decline request"""
        alice_client, bob_client = game_request_pending

        # Bob declines with valid session
        response = decline_game_request(bob_client, "Bob")

        # Should succeed
        assert response.status_code == status.HTTP_200_OK

    def test_decline_game_request_fails_without_session(
        self, game_request_pending: tuple[TestClient, TestClient]
    ):
        """Test that declining without session is rejected"""
        # Try to decline without session
        no_session_client = TestClient(app)
        response = decline_game_request(no_session_client, "Bob")

        # Should fail with 401 Unauthorized
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_decline_game_request_fails_with_mismatched_session(
        self,
        alice_client: TestClient,
        bob_client: TestClient,
        charlie_client: TestClient,
    ):
        """Test that player cannot decline request for another player"""
        # Setup: Alice sends request to Bob, Charlie exists
        send_game_request(alice_client, "Alice", "Bob")

        # Charlie tries to decline using Bob's name
        response = decline_game_request(charlie_client, "Bob")

        # Should fail with 403 Forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestLobbyStatusSessionValidation:
    """Test session validation for lobby status endpoints"""

    def test_lobby_status_succeeds_with_valid_session(self, alice_client: TestClient):
        """Test that player with valid session can get their status"""
        # Get status with valid session
        response = alice_client.get("/lobby/status/Alice")

        # Should succeed
        assert response.status_code == status.HTTP_200_OK

    def test_lobby_status_fails_without_session(self, alice_client: TestClient):
        """Test that getting status without session is rejected"""
        # Try to get status without session
        no_session_client = TestClient(app)
        response = no_session_client.get("/lobby/status/Alice")

        # Should fail with 401 Unauthorized
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_lobby_status_fails_with_mismatched_session(
        self, alice_client: TestClient, bob_client: TestClient
    ):
        """Test that player cannot get another player's status"""
        # Bob tries to get Alice's status (with Bob's session)
        response = bob_client.get("/lobby/status/Alice")

        # Should fail with 403 Forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_long_poll_succeeds_with_valid_session(self, alice_client: TestClient):
        """Test that long polling works with valid session"""
        # Long poll with valid session
        response = alice_client.get("/lobby/status/Alice/long-poll")

        # Should succeed
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT]

    def test_long_poll_fails_without_session(self, alice_client: TestClient):
        """Test that long polling without session is rejected"""
        # Try to long poll without session
        no_session_client = TestClient(app)
        response = no_session_client.get("/lobby/status/Alice/long-poll")

        # Should fail with 401 Unauthorized
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_long_poll_fails_with_mismatched_session(
        self, alice_client: TestClient, bob_client: TestClient
    ):
        """Test that player cannot long poll another player's status"""
        # Bob tries to long poll Alice's status
        response = bob_client.get("/lobby/status/Alice/long-poll")

        # Should fail with 403 Forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN
