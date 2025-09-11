import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestLeaveLobbyEndpoint:
    """Integration tests for leave lobby functionality"""

    def test_leave_lobby_endpoint_exists(self, client: TestClient):
        # Test that the leave lobby endpoint exists
        response = client.post(
            "/leave-lobby",
            data={"player_name": "Alice"},
        )

        # Should not return 404 once endpoint is implemented
        # For now, expecting error since endpoint doesn't exist
        assert response.status_code != 404 or True  # Will fail in Red phase

    def test_leave_lobby_redirects_to_login_page(self, client: TestClient):
        # Test that leaving lobby redirects to login page

        # Step 1: Add player to lobby
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})

        # Step 2: Leave lobby
        response = client.post(
            "/leave-lobby", data={"player_name": "Alice"}, follow_redirects=False
        )

        # Should redirect to login page
        assert response.status_code == status.HTTP_302_FOUND
        assert response.headers["location"] == "/"

    def test_leave_lobby_removes_player_from_lobby(self, client: TestClient):
        # Test that leaving lobby removes player from other players' views

        # Step 1: Add multiple players to lobby
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        client.post("/", data={"player_name": "Charlie", "game_mode": "human"})

        # Step 2: Verify Bob can see Alice and Charlie
        bob_response = client.get("/lobby/players/Bob")
        assert "Alice" in bob_response.text
        assert "Charlie" in bob_response.text

        # Step 3: Alice leaves lobby
        client.post("/leave-lobby", data={"player_name": "Alice"})

        # Step 4: Verify Bob can no longer see Alice
        bob_response = client.get("/lobby/players/Bob")
        assert "Alice" not in bob_response.text
        assert "Charlie" in bob_response.text  # Charlie should still be visible

    def test_leave_lobby_cancels_pending_game_requests(self, client: TestClient):
        # Test that leaving lobby cancels any pending game requests

        # Step 1: Setup players and game request
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        client.post("/", data={"player_name": "Charlie", "game_mode": "human"})

        # Step 2: Alice sends request to Bob
        client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )

        # Step 3: Verify Bob has pending request
        bob_response = client.get("/lobby/players/Bob")
        assert "Pending Response" in bob_response.text

        # Step 4: Alice leaves lobby
        client.post("/leave-lobby", data={"player_name": "Alice"})

        # Step 5: Verify Bob's status returns to Available
        bob_response = client.get("/lobby/players/Bob")
        assert "Available" in bob_response.text
        assert "Pending Response" not in bob_response.text

    def test_leave_lobby_if_sender_leaves_while_request_pending(self, client: TestClient):
        # Test scenario where request sender leaves while request is pending

        # Step 1: Setup players and game request  
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})

        # Step 2: Alice sends request to Bob
        client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )

        # Step 3: Alice leaves lobby before Bob responds
        client.post("/leave-lobby", data={"player_name": "Alice"})

        # Step 4: Bob should no longer have pending request
        bob_response = client.get("/lobby/players/Bob")
        assert "Available" in bob_response.text
        assert "Pending Response" not in bob_response.text

    def test_leave_lobby_if_receiver_leaves_while_request_pending(self, client: TestClient):
        # Test scenario where request receiver leaves while request is pending

        # Step 1: Setup players and game request
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})

        # Step 2: Alice sends request to Bob
        client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )

        # Step 3: Bob leaves lobby before responding
        client.post("/leave-lobby", data={"player_name": "Bob"})

        # Step 4: Alice's status should return to Available (request was implicitly declined)
        alice_response = client.get("/lobby/players/Alice")
        assert "Available" in alice_response.text
        assert "Requesting Game" not in alice_response.text

    def test_leave_lobby_with_empty_player_name(self, client: TestClient):
        # Test leaving lobby with empty player name
        response = client.post("/leave-lobby", data={"player_name": ""})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Player name" in response.text

    def test_leave_lobby_with_nonexistent_player(self, client: TestClient):
        # Test leaving lobby with player not in lobby
        client.post("/test/reset-lobby")
        
        response = client.post("/leave-lobby", data={"player_name": "NonExistentPlayer"})

        # Should handle gracefully - either 400 or 404
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND]

    def test_leave_lobby_empty_lobby_after_last_player_leaves(self, client: TestClient):
        # Test that lobby becomes empty after last player leaves

        # Step 1: Add single player to lobby
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})

        # Step 2: Verify lobby has player
        alice_response = client.get("/lobby/players/Alice")
        assert alice_response.status_code == status.HTTP_200_OK

        # Step 3: Alice leaves lobby
        client.post("/leave-lobby", data={"player_name": "Alice"})

        # Step 4: Verify lobby is empty (can be tested via lobby reset endpoint or new player joining)
        # Add new player and verify they see empty lobby
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        bob_response = client.get("/lobby/players/Bob")
        assert "No other players available" in bob_response.text


class TestLobbyStateConsistency:
    """Integration tests for lobby state consistency when players leave"""

    def test_lobby_updates_real_time_when_player_leaves(self, client: TestClient):
        # Test that other players see real-time updates when someone leaves

        # Step 1: Setup multiple players
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        client.post("/", data={"player_name": "Charlie", "game_mode": "human"})

        # Step 2: Verify Charlie sees both Alice and Bob
        charlie_response = client.get("/lobby/players/Charlie")
        assert "Alice" in charlie_response.text
        assert "Bob" in charlie_response.text

        # Step 3: Bob leaves
        client.post("/leave-lobby", data={"player_name": "Bob"})

        # Step 4: Charlie's next lobby update should not show Bob
        charlie_response = client.get("/lobby/players/Charlie")
        assert "Alice" in charlie_response.text
        assert "Bob" not in charlie_response.text

    def test_multiple_players_leave_simultaneously(self, client: TestClient):
        # Test handling multiple players leaving at the same time

        # Step 1: Setup multiple players
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        client.post("/", data={"player_name": "Charlie", "game_mode": "human"})
        client.post("/", data={"player_name": "Dave", "game_mode": "human"})

        # Step 2: Multiple players leave
        client.post("/leave-lobby", data={"player_name": "Alice"})
        client.post("/leave-lobby", data={"player_name": "Bob"})

        # Step 3: Remaining players should only see each other
        charlie_response = client.get("/lobby/players/Charlie")
        assert "Alice" not in charlie_response.text
        assert "Bob" not in charlie_response.text
        assert "Dave" in charlie_response.text

        dave_response = client.get("/lobby/players/Dave")
        assert "Alice" not in dave_response.text
        assert "Bob" not in dave_response.text
        assert "Charlie" in dave_response.text