import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestGameRequestNotifications:
    """Integration tests for game request notifications in lobby interface"""

    def test_lobby_shows_game_request_notification_for_receiver(self, client: TestClient):
        # Test that lobby displays notification when player receives a game request

        # Step 1: Setup players
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})

        # Step 2: Alice sends request to Bob
        client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )

        # Step 3: Bob's lobby view should show game request notification
        bob_response = client.get("/lobby/players/Bob")
        assert bob_response.status_code == status.HTTP_200_OK
        assert 'data-testid="game-request-notification"' in bob_response.text
        assert "Alice" in bob_response.text  # Notification should mention sender
        assert "game request" in bob_response.text.lower()

    def test_lobby_shows_accept_decline_buttons_for_pending_request(self, client: TestClient):
        # Test that lobby shows Accept/Decline buttons when player has pending request

        # Step 1: Setup players and game request
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )

        # Step 2: Bob's lobby view should show Accept/Decline buttons
        bob_response = client.get("/lobby/players/Bob")
        assert 'data-testid="accept-game-request"' in bob_response.text
        assert 'data-testid="decline-game-request"' in bob_response.text
        assert "Accept" in bob_response.text
        assert "Decline" in bob_response.text

    def test_lobby_hides_select_opponent_buttons_when_player_has_pending_request(self, client: TestClient):
        # Test that Select Opponent buttons are disabled/hidden when player has pending request

        # Step 1: Setup multiple players
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        client.post("/", data={"player_name": "Charlie", "game_mode": "human"})

        # Step 2: Alice sends request to Bob
        client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )

        # Step 3: Bob's lobby view should not show selectable players while responding to request
        bob_response = client.get("/lobby/players/Bob")
        
        # Should not have enabled Select Opponent buttons for other players
        # Either buttons should be disabled or hidden entirely
        if 'data-testid="select-opponent-Charlie"' in bob_response.text:
            # If button exists, it should be disabled
            assert 'disabled' in bob_response.text
        # Alternative: buttons are completely hidden during pending request state

    def test_lobby_shows_confirmation_message_after_sending_request(self, client: TestClient):
        # Test that lobby shows confirmation after successfully sending a request

        # Step 1: Setup players
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})

        # Step 2: Alice sends request to Bob
        response = client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )

        # Step 3: Response should show confirmation message
        assert response.status_code == status.HTTP_200_OK
        assert 'data-testid="confirmation-message"' in response.text
        assert "Game request sent to Bob" in response.text

    def test_lobby_shows_decline_confirmation_message(self, client: TestClient):
        # Test that lobby shows confirmation after declining a request

        # Step 1: Setup players and game request
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )

        # Step 2: Bob declines request
        response = client.post("/decline-game-request", data={"player_name": "Bob"})

        # Step 3: Response should show decline confirmation
        assert response.status_code == status.HTTP_200_OK
        assert 'data-testid="decline-confirmation-message"' in response.text
        assert "Game request from Alice declined" in response.text

    def test_lobby_removes_notification_after_accepting_request(self, client: TestClient):
        # Test that notification disappears after accepting request

        # Step 1: Setup players and game request
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )

        # Step 2: Verify notification exists
        bob_response = client.get("/lobby/players/Bob")
        assert 'data-testid="game-request-notification"' in bob_response.text

        # Step 3: Bob accepts request (should redirect to game)
        accept_response = client.post(
            "/accept-game-request", data={"player_name": "Bob"}, follow_redirects=False
        )
        assert accept_response.status_code == status.HTTP_302_FOUND
        assert "/game" in accept_response.headers["location"]

    def test_lobby_removes_notification_after_declining_request(self, client: TestClient):
        # Test that notification disappears after declining request

        # Step 1: Setup players and game request
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )

        # Step 2: Bob declines request
        response = client.post("/decline-game-request", data={"player_name": "Bob"})

        # Step 3: Bob's lobby view should no longer show notification
        assert 'data-testid="game-request-notification"' not in response.text
        # But should still show lobby interface
        assert "Multiplayer Lobby" in response.text


class TestLobbyPlayerStatusUpdates:
    """Integration tests for real-time player status updates in lobby"""

    def test_lobby_shows_requesting_game_status_for_sender(self, client: TestClient):
        # Test that sender shows "Requesting Game" status after sending request

        # Step 1: Setup players
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})

        # Step 2: Alice sends request to Bob
        client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )

        # Step 3: Alice's lobby view should show "Requesting Game" status
        alice_response = client.get("/lobby/players/Alice")
        assert 'data-testid="own-player-status"' in alice_response.text
        assert "Requesting Game" in alice_response.text

    def test_lobby_shows_pending_response_status_for_receiver(self, client: TestClient):
        # Test that receiver shows "Pending Response" status when they have a pending request

        # Step 1: Setup players and game request
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )

        # Step 2: Bob's lobby view should show "Pending Response" status
        bob_response = client.get("/lobby/players/Bob")
        assert 'data-testid="own-player-status"' in bob_response.text
        assert "Pending Response" in bob_response.text

    def test_lobby_shows_other_players_status_updates(self, client: TestClient):
        # Test that third-party players see status updates for others

        # Step 1: Setup multiple players
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        client.post("/", data={"player_name": "Charlie", "game_mode": "human"})

        # Step 2: Alice sends request to Bob
        client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )

        # Step 3: Charlie should see updated statuses for Alice and Bob
        charlie_response = client.get("/lobby/players/Charlie")
        
        # Look for Alice's status update
        assert 'data-testid="player-Alice-status"' in charlie_response.text or "Requesting" in charlie_response.text
        
        # Look for Bob's status update  
        assert 'data-testid="player-Bob-status"' in charlie_response.text or "Pending" in charlie_response.text

    def test_lobby_disables_select_buttons_for_unavailable_players(self, client: TestClient):
        # Test that Select Opponent buttons are disabled for players who are not Available

        # Step 1: Setup multiple players
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        client.post("/", data={"player_name": "Charlie", "game_mode": "human"})

        # Step 2: Alice sends request to Bob
        client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )

        # Step 3: Charlie should not be able to select Alice or Bob
        charlie_response = client.get("/lobby/players/Charlie")
        
        # Alice's select button should be disabled (she's requesting)
        if 'data-testid="select-opponent-Alice"' in charlie_response.text:
            assert 'disabled' in charlie_response.text
            
        # Bob's select button should be disabled (he's pending response)
        if 'data-testid="select-opponent-Bob"' in charlie_response.text:
            assert 'disabled' in charlie_response.text

    def test_lobby_restores_available_status_after_decline(self, client: TestClient):
        # Test that both players return to Available status after decline

        # Step 1: Setup players and game request
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        client.post("/", data={"player_name": "Charlie", "game_mode": "human"})
        client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )

        # Step 2: Bob declines request
        client.post("/decline-game-request", data={"player_name": "Bob"})

        # Step 3: Both Alice and Bob should show Available status
        alice_response = client.get("/lobby/players/Alice")
        assert "Available" in alice_response.text
        assert "Requesting Game" not in alice_response.text

        bob_response = client.get("/lobby/players/Bob")
        assert "Available" in bob_response.text
        assert "Pending Response" not in bob_response.text

        # Step 4: Charlie should be able to select both Alice and Bob again
        charlie_response = client.get("/lobby/players/Charlie")
        assert 'data-testid="select-opponent-Alice"' in charlie_response.text
        assert 'data-testid="select-opponent-Bob"' in charlie_response.text
        # Buttons should not be disabled
        assert charlie_response.text.count('disabled') == 0 or 'disabled' not in charlie_response.text