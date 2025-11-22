import json
from base64 import b64decode

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from httpx import Response
from itsdangerous import TimestampSigner


class TestSessionCreation:
    """Verify sessions are created correctly on login"""

    def test_login_multiplayer_creates_session_with_player_name(
        self, client: TestClient
    ):
        """Test that logging in for multiplayer stores player_name in session"""
        response: Response = client.post(
            "/", data={"player_name": "Alice", "game_mode": "human"}
        )
        assert response.status_code == status.HTTP_200_OK

        # Verify session contains player_name
        assert "session" in client.cookies
        session_data = _decode_session(client.cookies["session"])

        # This test expects player_name to be stored (not yet implemented)
        assert "player_name" in session_data, "Session should contain player_name"
        assert session_data["player_name"] == "Alice"

    def test_login_computer_creates_session_with_player_name(self, client: TestClient):
        """Test that logging in for computer mode also stores player_name in session"""
        response: Response = client.post(
            "/", data={"player_name": "Bob", "game_mode": "computer"}
        )
        assert response.status_code == status.HTTP_200_OK

        # Verify session contains player_name
        session_data = _decode_session(client.cookies["session"])
        assert "player_name" in session_data
        assert session_data["player_name"] == "Bob"

    def test_multiple_players_have_independent_sessions(self, client: TestClient):
        """Test that different clients have different sessions"""
        # Create two separate clients
        client1 = TestClient(client.app)
        client2 = TestClient(client.app)

        # Both login
        client1.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client2.post("/", data={"player_name": "Bob", "game_mode": "human"})

        # Verify they have different session data
        session1 = _decode_session(client1.cookies["session"])
        session2 = _decode_session(client2.cookies["session"])

        assert session1["player_name"] == "Alice"
        assert session2["player_name"] == "Bob"
        assert session1["player-id"] != session2["player-id"]


class TestLeaveLobbySessionValidation:
    """Test session validation for /leave-lobby endpoint"""

    def test_leave_lobby_succeeds_with_valid_session(self, client: TestClient):
        """Test that player with valid session can leave lobby"""
        # Login (creates session)
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})

        # Leave lobby with matching session
        response = client.post("/leave-lobby", data={"player_name": "Alice"})

        # Should succeed (200 OK or redirect)
        # Without HX-Request header, returns 302, with HTMX returns 204
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_302_FOUND,
            status.HTTP_303_SEE_OTHER,
            status.HTTP_204_NO_CONTENT,
        ]

    def test_leave_lobby_fails_without_session(self, client: TestClient):
        """Test that player without session cannot leave lobby"""
        # Alice joins lobby
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})

        # Create new client without session
        new_client = TestClient(client.app)
        new_client.post("/test/reset-lobby")  # Use same lobby state

        # Try to leave without session
        response = new_client.post("/leave-lobby", data={"player_name": "Alice"})

        # Should fail with 401 Unauthorized
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_leave_lobby_fails_with_mismatched_session(self, client: TestClient):
        """Test that player cannot leave lobby using another player's name"""
        # Alice joins lobby
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})

        # Create second client for Bob
        bob_client = TestClient(client.app)
        bob_client.post("/", data={"player_name": "Bob", "game_mode": "human"})

        # Bob tries to leave using Alice's name (with Bob's session)
        response = bob_client.post("/leave-lobby", data={"player_name": "Alice"})

        # Should fail with 403 Forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestSelectOpponentSessionValidation:
    """Test session validation for /select-opponent endpoint"""

    def test_select_opponent_succeeds_with_valid_session(self, client: TestClient):
        """Test that player with valid session can send game request"""
        # Create two players
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})

        bob_client = TestClient(client.app)
        bob_client.post("/", data={"player_name": "Bob", "game_mode": "human"})

        # Alice sends request to Bob (with Alice's session)
        response = client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )

        # Should succeed
        assert response.status_code == status.HTTP_200_OK

    def test_select_opponent_fails_without_session(self, client: TestClient):
        """Test that request without session is rejected"""
        # Create Alice and Bob
        alice_client = TestClient(client.app)
        alice_client.post("/", data={"player_name": "Alice", "game_mode": "human"})

        bob_client = TestClient(client.app)
        bob_client.post("/", data={"player_name": "Bob", "game_mode": "human"})

        # Create client without session
        no_session_client = TestClient(client.app)

        # Try to send request without session
        response = no_session_client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )

        # Should fail with 401 Unauthorized
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_select_opponent_fails_with_mismatched_session(self, client: TestClient):
        """Test that player cannot send request as another player"""
        # Create Alice and Bob
        alice_client = TestClient(client.app)
        alice_client.post("/", data={"player_name": "Alice", "game_mode": "human"})

        bob_client = TestClient(client.app)
        bob_client.post("/", data={"player_name": "Bob", "game_mode": "human"})

        # Bob tries to send request as Alice (using Bob's session)
        response = bob_client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )

        # Should fail with 403 Forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestAcceptGameRequestSessionValidation:
    """Test session validation for /accept-game-request endpoint"""

    def test_accept_game_request_succeeds_with_valid_session(self, client: TestClient):
        """Test that player with valid session can accept request"""
        # Create Alice and Bob
        alice_client = TestClient(client.app)
        alice_client.post("/", data={"player_name": "Alice", "game_mode": "human"})

        bob_client = TestClient(client.app)
        bob_client.post("/", data={"player_name": "Bob", "game_mode": "human"})

        # Alice sends request to Bob
        alice_client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )

        # Bob accepts with valid session
        response = bob_client.post("/accept-game-request", data={"player_name": "Bob"})

        # Should succeed (200 OK or redirect)
        # Without HX-Request header, returns 302, with HTMX returns 204
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_302_FOUND,
            status.HTTP_303_SEE_OTHER,
            status.HTTP_204_NO_CONTENT,
        ]

    def test_accept_game_request_fails_without_session(self, client: TestClient):
        """Test that accepting without session is rejected"""
        # Setup game request
        alice_client = TestClient(client.app)
        alice_client.post("/", data={"player_name": "Alice", "game_mode": "human"})

        bob_client = TestClient(client.app)
        bob_client.post("/", data={"player_name": "Bob", "game_mode": "human"})

        alice_client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )

        # Try to accept without session
        no_session_client = TestClient(client.app)
        response = no_session_client.post(
            "/accept-game-request", data={"player_name": "Bob"}
        )

        # Should fail with 401 Unauthorized
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_accept_game_request_fails_with_mismatched_session(
        self, client: TestClient
    ):
        """Test that player cannot accept request for another player"""
        # Setup: Alice sends request to Bob, Charlie exists
        alice_client = TestClient(client.app)
        alice_client.post("/", data={"player_name": "Alice", "game_mode": "human"})

        bob_client = TestClient(client.app)
        bob_client.post("/", data={"player_name": "Bob", "game_mode": "human"})

        charlie_client = TestClient(client.app)
        charlie_client.post("/", data={"player_name": "Charlie", "game_mode": "human"})

        alice_client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )

        # Charlie tries to accept using Bob's name (with Charlie's session)
        response = charlie_client.post(
            "/accept-game-request", data={"player_name": "Bob"}
        )

        # Should fail with 403 Forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestDeclineGameRequestSessionValidation:
    """Test session validation for /decline-game-request endpoint"""

    def test_decline_game_request_succeeds_with_valid_session(self, client: TestClient):
        """Test that player with valid session can decline request"""
        # Setup game request
        alice_client = TestClient(client.app)
        alice_client.post("/", data={"player_name": "Alice", "game_mode": "human"})

        bob_client = TestClient(client.app)
        bob_client.post("/", data={"player_name": "Bob", "game_mode": "human"})

        alice_client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )

        # Bob declines with valid session
        response = bob_client.post("/decline-game-request", data={"player_name": "Bob"})

        # Should succeed
        assert response.status_code == status.HTTP_200_OK

    def test_decline_game_request_fails_without_session(self, client: TestClient):
        """Test that declining without session is rejected"""
        # Setup game request
        alice_client = TestClient(client.app)
        alice_client.post("/", data={"player_name": "Alice", "game_mode": "human"})

        bob_client = TestClient(client.app)
        bob_client.post("/", data={"player_name": "Bob", "game_mode": "human"})

        alice_client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )

        # Try to decline without session
        no_session_client = TestClient(client.app)
        response = no_session_client.post(
            "/decline-game-request", data={"player_name": "Bob"}
        )

        # Should fail with 401 Unauthorized
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_decline_game_request_fails_with_mismatched_session(
        self, client: TestClient
    ):
        """Test that player cannot decline request for another player"""
        # Setup: Alice sends request to Bob, Charlie exists
        alice_client = TestClient(client.app)
        alice_client.post("/", data={"player_name": "Alice", "game_mode": "human"})

        bob_client = TestClient(client.app)
        bob_client.post("/", data={"player_name": "Bob", "game_mode": "human"})

        charlie_client = TestClient(client.app)
        charlie_client.post("/", data={"player_name": "Charlie", "game_mode": "human"})

        alice_client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )

        # Charlie tries to decline using Bob's name
        response = charlie_client.post(
            "/decline-game-request", data={"player_name": "Bob"}
        )

        # Should fail with 403 Forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestLobbyStatusSessionValidation:
    """Test session validation for lobby status endpoints"""

    def test_lobby_status_succeeds_with_valid_session(self, client: TestClient):
        """Test that player with valid session can get their status"""
        # Login
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})

        # Get status with valid session
        response = client.get("/lobby/status/Alice")

        # Should succeed
        assert response.status_code == status.HTTP_200_OK

    def test_lobby_status_fails_without_session(self, client: TestClient):
        """Test that getting status without session is rejected"""
        # Alice joins
        alice_client = TestClient(client.app)
        alice_client.post("/", data={"player_name": "Alice", "game_mode": "human"})

        # Try to get status without session
        no_session_client = TestClient(client.app)
        response = no_session_client.get("/lobby/status/Alice")

        # Should fail with 401 Unauthorized
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_lobby_status_fails_with_mismatched_session(self, client: TestClient):
        """Test that player cannot get another player's status"""
        # Create Alice and Bob
        alice_client = TestClient(client.app)
        alice_client.post("/", data={"player_name": "Alice", "game_mode": "human"})

        bob_client = TestClient(client.app)
        bob_client.post("/", data={"player_name": "Bob", "game_mode": "human"})

        # Bob tries to get Alice's status (with Bob's session)
        response = bob_client.get("/lobby/status/Alice")

        # Should fail with 403 Forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_long_poll_succeeds_with_valid_session(self, client: TestClient):
        """Test that long polling works with valid session"""
        # Login
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})

        # Long poll with valid session
        response = client.get("/lobby/status/Alice/long-poll")

        # Should succeed
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT]

    def test_long_poll_fails_without_session(self, client: TestClient):
        """Test that long polling without session is rejected"""
        # Alice joins
        alice_client = TestClient(client.app)
        alice_client.post("/", data={"player_name": "Alice", "game_mode": "human"})

        # Try to long poll without session
        no_session_client = TestClient(client.app)
        response = no_session_client.get("/lobby/status/Alice/long-poll")

        # Should fail with 401 Unauthorized
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_long_poll_fails_with_mismatched_session(self, client: TestClient):
        """Test that player cannot long poll another player's status"""
        # Create Alice and Bob
        alice_client = TestClient(client.app)
        alice_client.post("/", data={"player_name": "Alice", "game_mode": "human"})

        bob_client = TestClient(client.app)
        bob_client.post("/", data={"player_name": "Bob", "game_mode": "human"})

        # Bob tries to long poll Alice's status
        response = bob_client.get("/lobby/status/Alice/long-poll")

        # Should fail with 403 Forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN


# Helper functions


def _decode_session(session_cookie: str) -> dict[str, str]:
    """Decode a session cookie to get the session data"""
    signer: TimestampSigner = TimestampSigner("your-secret-key-here")
    unsigned_data: bytes = signer.unsign(session_cookie.encode("utf-8"))
    session_data: dict[str, str] = json.loads(b64decode(unsigned_data))
    return session_data
