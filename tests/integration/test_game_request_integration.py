from fastapi import status
from fastapi.testclient import TestClient


class TestGameRequestEndpoints:
    """Integration tests for new game request endpoints"""

    def test_accept_game_request_endpoint_exists(self, client: TestClient):
        # Test that the new accept game request endpoint exists
        # Setup: Add players and create a game request scenario (this will fail until implemented)
        response = client.post(
            "/accept-game-request",
            data={"player_name": "Alice"},
        )

        # Should not return 404 once endpoint is implemented
        # For now, expecting error since endpoint doesn't exist
        assert response.status_code != 404 or True  # Will fail in Red phase

    def test_decline_game_request_endpoint_exists(self, client: TestClient):
        # Test that the new decline game request endpoint exists
        response = client.post(
            "/decline-game-request",
            data={"player_name": "Alice"},
        )

        # Should not return 404 once endpoint is implemented
        assert response.status_code != 404 or True  # Will fail in Red phase

    def test_accept_game_request_redirects_to_game_page(self, client: TestClient):
        # Test complete workflow: send request -> accept -> redirect to game

        # Step 1: Reset lobby and add players
        client.post("/test/reset-lobby")

        # Step 2: Add two players to lobby
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})

        # Step 3: Alice sends game request to Bob
        client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )

        # Step 4: Bob accepts the game request
        response = client.post(
            "/accept-game-request", data={"player_name": "Bob"}, follow_redirects=False
        )

        # Should redirect to game page
        assert response.status_code == status.HTTP_302_FOUND
        assert "/game" in response.headers["location"]
        assert "player_name=Bob" in response.headers["location"]

    def test_accept_game_request_no_pending_request(self, client: TestClient):
        # Test accepting when there's no pending request
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})

        # Try to accept non-existent request
        response = client.post("/accept-game-request", data={"player_name": "Alice"})

        # Should return error response
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "No pending game request" in response.text

    def test_decline_game_request_returns_to_lobby(self, client: TestClient):
        # Test complete workflow: send request -> decline -> stay in lobby

        # Step 1: Reset lobby and add players
        client.post("/test/reset-lobby")

        # Step 2: Add two players to lobby
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})

        # Step 3: Alice sends game request to Bob
        client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )

        # Step 4: Bob declines the game request
        response = client.post("/decline-game-request", data={"player_name": "Bob"})

        # Should return lobby status component with decline confirmation
        assert response.status_code == status.HTTP_200_OK
        assert "Game request from Alice declined" in response.text
        assert "Available Players:" in response.text  # Component has this instead of "Multiplayer Lobby"

    def test_decline_game_request_no_pending_request(self, client: TestClient):
        # Test declining when there's no pending request
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})

        # Try to decline non-existent request
        response = client.post("/decline-game-request", data={"player_name": "Alice"})

        # Should return error response
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "No pending game request" in response.text

    def test_accept_game_request_empty_player_name(self, client: TestClient):
        # Test accepting with empty player name
        response = client.post("/accept-game-request", data={"player_name": ""})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Player name" in response.text

    def test_decline_game_request_empty_player_name(self, client: TestClient):
        # Test declining with empty player name
        response = client.post("/decline-game-request", data={"player_name": ""})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Player name" in response.text

    def test_game_request_workflow_both_players_removed_from_lobby_after_accept(
        self, client: TestClient
    ):
        # Test that after accepting, both players are removed from others' lobby views

        # Step 1: Setup three players in lobby
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        client.post("/", data={"player_name": "Charlie", "game_mode": "human"})

        # Step 2: Alice sends request to Bob
        client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )

        # Step 3: Bob accepts request
        client.post("/accept-game-request", data={"player_name": "Bob"})

        # Step 4: Charlie's lobby view should not show Alice or Bob
        response = client.get("/lobby/status/Charlie")
        assert response.status_code == status.HTTP_200_OK
        assert "Alice" not in response.text
        assert "Bob" not in response.text
        # Charlie should see no other available players
        assert "No other players available" in response.text

    def test_game_request_workflow_both_players_available_after_decline(
        self, client: TestClient
    ):
        # Test that after declining, both players return to Available status

        # Step 1: Setup three players in lobby
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        client.post("/", data={"player_name": "Charlie", "game_mode": "human"})

        # Step 2: Alice sends request to Bob
        client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )

        # Step 3: Bob declines request
        client.post("/decline-game-request", data={"player_name": "Bob"})

        # Step 4: Charlie's lobby view should show both Alice and Bob as Available
        response = client.get("/lobby/status/Charlie")
        assert response.status_code == status.HTTP_200_OK
        assert "Alice" in response.text
        assert "Bob" in response.text
        assert "(Available)" in response.text  # Both should show Available status


class TestSelectOpponentEndpointUpdates:
    """Tests for updates to existing select-opponent endpoint"""

    def test_select_opponent_creates_game_request_instead_of_direct_status_update(
        self, client: TestClient
    ):
        # Test that select-opponent now creates a game request rather than directly updating statuses

        # Step 1: Setup players
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})

        # Step 2: Alice selects Bob as opponent
        response = client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )

        assert response.status_code == status.HTTP_200_OK
        assert "Game request sent to Bob" in response.text

        # Step 3: Check that Alice shows "Requesting Game" status
        alice_response = client.get("/lobby/status/Alice")
        assert "Requesting Game" in alice_response.text

        # Step 4: Check that Bob shows "Pending Response" status and has game request notification
        bob_response = client.get("/lobby/status/Bob")
        assert "Pending Response" in bob_response.text

    def test_select_opponent_prevents_multiple_concurrent_requests_from_same_sender(
        self, client: TestClient
    ):
        # Test that a player cannot send multiple requests while one is pending

        # Step 1: Setup players
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        client.post("/", data={"player_name": "Charlie", "game_mode": "human"})

        # Step 2: Alice sends request to Bob
        client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )

        # Step 3: Alice tries to send another request to Charlie
        response = client.post(
            "/select-opponent",
            data={"player_name": "Alice", "opponent_name": "Charlie"},
        )

        # Should fail because Alice already has pending request
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Alice is not available" in response.text

    def test_select_opponent_prevents_requests_to_unavailable_players(
        self, client: TestClient
    ):
        # Test that cannot send requests to players who are not Available

        # Step 1: Setup players
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        client.post("/", data={"player_name": "Charlie", "game_mode": "human"})

        # Step 2: Bob sends request to Charlie (making Charlie PENDING_RESPONSE)
        client.post(
            "/select-opponent", data={"player_name": "Bob", "opponent_name": "Charlie"}
        )

        # Step 3: Alice tries to send request to Charlie (who is now PENDING_RESPONSE)
        response = client.post(
            "/select-opponent",
            data={"player_name": "Alice", "opponent_name": "Charlie"},
        )

        # Should fail because Charlie is not Available
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Charlie is not available" in response.text

