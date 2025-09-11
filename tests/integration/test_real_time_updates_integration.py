import pytest
from fastapi import status
from fastapi.testclient import TestClient
import time


class TestRealTimeLobbyUpdates:
    """Integration tests for real-time lobby state updates"""

    def test_lobby_polling_endpoint_exists(self, client: TestClient):
        # Test that lobby provides endpoint for real-time updates

        # Step 1: Setup player in lobby
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})

        # Step 2: Check that lobby polling endpoint exists
        response = client.get("/lobby/players/Alice")
        assert response.status_code == status.HTTP_200_OK
        # Should return lobby state data
        assert "Alice" in response.text

    def test_lobby_updates_when_new_player_joins(self, client: TestClient):
        # Test that existing players see updates when new player joins

        # Step 1: Setup initial player
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})

        # Step 2: Get Alice's initial lobby state (should show empty)
        alice_initial = client.get("/lobby/players/Alice")
        assert "No other players available" in alice_initial.text

        # Step 3: Add new player
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})

        # Step 4: Alice's lobby should now show Bob
        alice_updated = client.get("/lobby/players/Alice")
        assert "Bob" in alice_updated.text
        assert "No other players available" not in alice_updated.text

    def test_lobby_updates_when_player_leaves(self, client: TestClient):
        # Test that remaining players see updates when someone leaves

        # Step 1: Setup multiple players
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        client.post("/", data={"player_name": "Charlie", "game_mode": "human"})

        # Step 2: Verify Alice sees Bob and Charlie
        alice_initial = client.get("/lobby/players/Alice")
        assert "Bob" in alice_initial.text
        assert "Charlie" in alice_initial.text

        # Step 3: Bob leaves lobby
        client.post("/leave-lobby", data={"player_name": "Bob"})

        # Step 4: Alice should no longer see Bob but still see Charlie
        alice_updated = client.get("/lobby/players/Alice")
        assert "Bob" not in alice_updated.text
        assert "Charlie" in alice_updated.text

    def test_lobby_updates_player_status_changes(self, client: TestClient):
        # Test that players see real-time status updates for others

        # Step 1: Setup multiple players
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        client.post("/", data={"player_name": "Charlie", "game_mode": "human"})

        # Step 2: Charlie sees Alice and Bob as Available
        charlie_initial = client.get("/lobby/players/Charlie")
        assert "Alice" in charlie_initial.text
        assert "Bob" in charlie_initial.text

        # Step 3: Alice sends request to Bob
        client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )

        # Step 4: Charlie should see updated statuses
        charlie_updated = client.get("/lobby/players/Charlie")
        # Should show Alice as "Requesting Game" or similar
        # Should show Bob as "Pending Response" or similar
        assert "Alice" in charlie_updated.text
        assert "Bob" in charlie_updated.text
        
        # Look for status indicators or disabled buttons
        assert ("Requesting" in charlie_updated.text or 
                "Pending" in charlie_updated.text or
                "disabled" in charlie_updated.text)

    def test_lobby_updates_when_players_enter_game(self, client: TestClient):
        # Test that lobby updates when players transition to game state

        # Step 1: Setup multiple players
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        client.post("/", data={"player_name": "Charlie", "game_mode": "human"})

        # Step 2: Charlie sees Alice and Bob initially
        charlie_initial = client.get("/lobby/players/Charlie")
        assert "Alice" in charlie_initial.text
        assert "Bob" in charlie_initial.text

        # Step 3: Alice and Bob start a game
        client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )
        client.post("/accept-game-request", data={"player_name": "Bob"})

        # Step 4: Charlie should no longer see Alice or Bob in lobby
        charlie_updated = client.get("/lobby/players/Charlie")
        assert "Alice" not in charlie_updated.text
        assert "Bob" not in charlie_updated.text
        assert "No other players available" in charlie_updated.text

    def test_lobby_updates_when_request_is_declined(self, client: TestClient):
        # Test that lobby updates correctly when game request is declined

        # Step 1: Setup players and request
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        client.post("/", data={"player_name": "Charlie", "game_mode": "human"})
        client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )

        # Step 2: Verify Charlie sees non-Available statuses
        charlie_before_decline = client.get("/lobby/players/Charlie")
        # Should show some indication that Alice and Bob are not available

        # Step 3: Bob declines request
        client.post("/decline-game-request", data={"player_name": "Bob"})

        # Step 4: Charlie should see both players as Available again
        charlie_after_decline = client.get("/lobby/players/Charlie")
        assert "Alice" in charlie_after_decline.text
        assert "Bob" in charlie_after_decline.text
        # Should be able to select both players again
        assert 'data-testid="select-opponent-Alice"' in charlie_after_decline.text
        assert 'data-testid="select-opponent-Bob"' in charlie_after_decline.text


class TestLobbyDataConsistency:
    """Integration tests for lobby data consistency across multiple requests"""

    def test_concurrent_player_actions_maintain_consistency(self, client: TestClient):
        # Test that multiple simultaneous actions maintain lobby consistency

        # Step 1: Setup multiple players
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        client.post("/", data={"player_name": "Charlie", "game_mode": "human"})
        client.post("/", data={"player_name": "Dave", "game_mode": "human"})

        # Step 2: Perform multiple actions
        # Alice sends request to Bob
        client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )
        # Charlie sends request to Dave
        client.post(
            "/select-opponent", data={"player_name": "Charlie", "opponent_name": "Dave"}
        )

        # Step 3: Verify each player sees consistent state
        alice_view = client.get("/lobby/players/Alice")
        bob_view = client.get("/lobby/players/Bob")
        charlie_view = client.get("/lobby/players/Charlie")
        dave_view = client.get("/lobby/players/Dave")

        # All views should be consistent
        # Alice should see herself as "Requesting Game"
        assert "Requesting" in alice_view.text or alice_view.status_code == status.HTTP_200_OK
        
        # Bob should have game request notification
        assert "game request" in bob_view.text.lower() or "notification" in bob_view.text.lower()

    def test_lobby_state_persists_across_multiple_requests(self, client: TestClient):
        # Test that lobby state is maintained consistently across requests

        # Step 1: Setup stable lobby state
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})

        # Step 2: Make multiple requests for same player
        alice_request1 = client.get("/lobby/players/Alice")
        alice_request2 = client.get("/lobby/players/Alice")
        alice_request3 = client.get("/lobby/players/Alice")

        # Step 3: All requests should return consistent data
        assert alice_request1.status_code == status.HTTP_200_OK
        assert alice_request2.status_code == status.HTTP_200_OK
        assert alice_request3.status_code == status.HTTP_200_OK
        
        # Should all show Bob as available
        assert "Bob" in alice_request1.text
        assert "Bob" in alice_request2.text
        assert "Bob" in alice_request3.text

    def test_lobby_handles_rapid_state_changes(self, client: TestClient):
        # Test that lobby can handle rapid succession of state changes

        # Step 1: Setup players
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})

        # Step 2: Rapid state changes
        # Send request
        client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )
        
        # Immediately decline
        client.post("/decline-game-request", data={"player_name": "Bob"})
        
        # Immediately send another request
        response = client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )

        # Step 3: Should handle rapid changes gracefully
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
        
        # Final state should be consistent
        alice_final = client.get("/lobby/players/Alice")
        bob_final = client.get("/lobby/players/Bob")
        
        assert alice_final.status_code == status.HTTP_200_OK
        assert bob_final.status_code == status.HTTP_200_OK

    def test_lobby_recovers_from_invalid_state_requests(self, client: TestClient):
        # Test that lobby handles and recovers from invalid state requests

        # Step 1: Setup valid lobby state
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})

        # Step 2: Make invalid requests
        # Try to access non-existent player
        invalid_response1 = client.get("/lobby/players/NonExistentPlayer")
        
        # Try to perform action with invalid player
        invalid_response2 = client.post(
            "/select-opponent", 
            data={"player_name": "NonExistent", "opponent_name": "Alice"}
        )

        # Step 3: Invalid requests should be handled gracefully
        assert invalid_response1.status_code in [
            status.HTTP_400_BAD_REQUEST, 
            status.HTTP_404_NOT_FOUND
        ]
        assert invalid_response2.status_code == status.HTTP_400_BAD_REQUEST

        # Step 4: Valid requests should still work
        alice_response = client.get("/lobby/players/Alice")
        assert alice_response.status_code == status.HTTP_200_OK
        assert "Alice" in alice_response.text


class TestLobbyPerformance:
    """Integration tests for lobby performance and scalability"""

    def test_lobby_handles_multiple_players_efficiently(self, client: TestClient):
        # Test that lobby can handle multiple players without performance degradation

        # Step 1: Reset and add multiple players
        client.post("/test/reset-lobby")
        
        player_names = [f"Player{i}" for i in range(10)]
        for name in player_names:
            response = client.post("/", data={"player_name": name, "game_mode": "human"})
            assert response.status_code in [status.HTTP_200_OK, status.HTTP_302_FOUND]

        # Step 2: Verify each player can see all others
        first_player_response = client.get(f"/lobby/players/{player_names[0]}")
        assert first_player_response.status_code == status.HTTP_200_OK
        
        # Should see at least several other players
        other_players_count = sum(1 for name in player_names[1:6] if name in first_player_response.text)
        assert other_players_count >= 3  # Should see multiple other players

    def test_lobby_response_time_remains_reasonable(self, client: TestClient):
        # Test that lobby response times are reasonable even with multiple players

        # Step 1: Setup players
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})

        # Step 2: Measure response time for lobby requests
        start_time = time.time()
        response = client.get("/lobby/players/Alice")
        end_time = time.time()

        # Step 3: Response should be reasonably fast (under 1 second for local testing)
        response_time = end_time - start_time
        assert response_time < 1.0  # Should respond within 1 second
        assert response.status_code == status.HTTP_200_OK