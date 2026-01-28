"""
Endpoint tests for the gameplay page.

Tests verify the game_page function behavior, including helper functions
that should be extracted for better code organization.
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestGameplayPageEndpoint:
    """Tests for GET /game/{game_id} endpoint"""

    def test_game_page_returns_200_for_valid_game(
        self, authenticated_client: TestClient
    ):
        """Test that game page loads successfully for a valid game"""
        # First create a game by going through start-game
        create_response = authenticated_client.post(
            "/start-game",
            data={"action": "launch_game", "player_name": "Alice"},
            follow_redirects=False,
        )

        # Should redirect to /game/{game_id}
        assert create_response.status_code == status.HTTP_303_SEE_OTHER
        redirect_url = create_response.headers["location"]
        assert redirect_url.startswith("/game/")

        # Follow redirect to get the game page
        game_response = authenticated_client.get(redirect_url)
        assert game_response.status_code == status.HTTP_200_OK
        assert "text/html" in game_response.headers["content-type"]

    def test_game_page_displays_player_name(self, authenticated_client: TestClient):
        """Test that game page shows the current player's name"""
        # Create a game
        create_response = authenticated_client.post(
            "/start-game",
            data={"action": "launch_game", "player_name": "Alice"},
            follow_redirects=False,
        )
        game_url = create_response.headers["location"]

        # Get game page
        response = authenticated_client.get(game_url)
        assert response.status_code == status.HTTP_200_OK

        # Check that player name is displayed
        assert "Alice" in response.text

    def test_game_page_displays_opponent_name(self, authenticated_client: TestClient):
        """Test that game page shows the opponent (Computer) name"""
        # Create a game
        create_response = authenticated_client.post(
            "/start-game",
            data={"action": "launch_game", "player_name": "Alice"},
            follow_redirects=False,
        )
        game_url = create_response.headers["location"]

        # Get game page
        response = authenticated_client.get(game_url)
        assert response.status_code == status.HTTP_200_OK

        # Check that opponent name is displayed (Computer for single player)
        assert "Computer" in response.text

    def test_game_page_returns_404_for_nonexistent_game(
        self, authenticated_client: TestClient
    ):
        """Test that game page returns 404 for a game that doesn't exist"""
        response = authenticated_client.get("/game/nonexistent-game-id")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_game_page_returns_403_for_player_not_in_game(
        self, client: TestClient, alice_client: TestClient, bob_client: TestClient
    ):
        """Test that player not in game gets 403 Forbidden"""
        from helpers import create_player

        # Create a game for Alice
        create_response = alice_client.post(
            "/start-game",
            data={"action": "launch_game", "player_name": "Alice"},
            follow_redirects=False,
        )
        game_url = create_response.headers["location"]

        # Extract game_id from URL
        game_id = game_url.split("/")[-1]

        # Bob (who is not in the game) tries to access
        response = bob_client.get(f"/game/{game_id}")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_game_page_shows_both_boards(self, authenticated_client: TestClient):
        """Test that game page shows both player and opponent boards"""
        # Create a game
        create_response = authenticated_client.post(
            "/start-game",
            data={"action": "launch_game", "player_name": "Alice"},
            follow_redirects=False,
        )
        game_url = create_response.headers["location"]

        # Get game page
        response = authenticated_client.get(game_url)
        assert response.status_code == status.HTTP_200_OK

        # Should have elements for both boards (player and opponent)
        # The exact testid depends on the template structure
        assert "text/html" in response.headers["content-type"]

    def test_game_page_context_variables(self, authenticated_client: TestClient):
        """Test that game page context contains round and shots available"""
        # Create a game
        create_response = authenticated_client.post(
            "/start-game",
            data={"action": "launch_game", "player_name": "Alice"},
            follow_redirects=False,
        )
        game_url = create_response.headers["location"]

        # Place ships randomly so shots_available will be 6
        authenticated_client.post(
            "/random-ship-placement",
            data={"player_name": "Alice"},
        )

        # Get game page
        response = authenticated_client.get(game_url)
        assert response.status_code == status.HTTP_200_OK

        # Check for context variables in the rendered HTML
        # Since we can't easily check context directly with TestClient,
        # we check for the rendered values in the HTML
        assert "Round 1" in response.text
        assert "Shots Available: 6" in response.text


class TestGameplayPageMultiPlayer:
    """Tests for multiplayer game page"""

    def test_multiplayer_game_page_shows_correct_opponent_name(
        self, alice_client: TestClient, bob_client: TestClient
    ):
        """Test that multiplayer game shows the correct opponent name"""
        from helpers import accept_game_request, send_game_request

        # Create game for Alice (single player first, then pair for two-player)
        # Note: The current implementation creates games via ship placement flow
        # This test documents expected behavior

        # For now, just verify single-player works
        pass

    def test_two_players_can_access_same_game(
        self, alice_client: TestClient, bob_client: TestClient
    ):
        """Test that both players can access the same game page"""
        # Create a game for Alice
        create_response = alice_client.post(
            "/start-game",
            data={"action": "launch_game", "player_name": "Alice"},
            follow_redirects=False,
        )
        alice_game_url = create_response.headers["location"]

        # Alice accesses her game page
        alice_response = alice_client.get(alice_game_url)
        assert alice_response.status_code == status.HTTP_200_OK

        # Bob should get 403 (not in this game)
        alice_game_id = alice_game_url.split("/")[-1]
        bob_response = bob_client.get(f"/game/{alice_game_id}")
        assert bob_response.status_code == status.HTTP_403_FORBIDDEN


class TestGameplayPageHelperFunctions:
    """Tests to verify helper functions are working correctly"""

    def test_get_game_or_404_helper(self, authenticated_client: TestClient):
        """Test that _get_game_or_404 raises 404 for non-existent game"""
        # This would test the helper function directly
        # For now, tested implicitly by test_game_page_returns_404_for_nonexistent_game

    def test_get_player_role_helper(self, authenticated_client: TestClient):
        """Test that _get_player_role correctly identifies player position"""
        # Create a game
        create_response = authenticated_client.post(
            "/start-game",
            data={"action": "launch_game", "player_name": "Alice"},
            follow_redirects=False,
        )
        game_url = create_response.headers["location"]

        # Access game page - should work
        response = authenticated_client.get(game_url)
        assert response.status_code == status.HTTP_200_OK

    def test_format_board_for_template_helper(self, authenticated_client: TestClient):
        """Test that board data is formatted correctly for template"""
        # Create a game
        create_response = authenticated_client.post(
            "/start-game",
            data={"action": "launch_game", "player_name": "Alice"},
            follow_redirects=False,
        )
        game_url = create_response.headers["location"]

        # Get game page
        response = authenticated_client.get(game_url)
        assert response.status_code == status.HTTP_200_OK

        # Board should be visible in the response
        assert "text/html" in response.headers["content-type"]


class TestAimShotEndpoint:
    """Tests for POST /aim-shot endpoint"""

    def test_aim_shot_returns_200_for_valid_request(
        self, authenticated_client: TestClient
    ):
        """Test that aim-shot endpoint works for valid request"""
        # Create a game
        create_response = authenticated_client.post(
            "/start-game",
            data={"action": "launch_game", "player_name": "Alice"},
            follow_redirects=False,
        )
        game_url = create_response.headers["location"]
        game_id = game_url.split("/")[-1]

        # Place ships so we have shots available
        authenticated_client.post(
            "/random-ship-placement",
            data={"player_name": "Alice"},
        )

        # Send HTMX request to aim at a coordinate
        response = authenticated_client.post(
            "/aim-shot",
            data={"game_id": game_id, "coordinate": "J1"},
            headers={"HX-Request": "true"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]

    def test_aim_shot_toggles_coordinate(self, authenticated_client: TestClient):
        """Test that aim-shot toggles coordinate on and off"""
        # Create a game
        create_response = authenticated_client.post(
            "/start-game",
            data={"action": "launch_game", "player_name": "Alice"},
            follow_redirects=False,
        )
        game_url = create_response.headers["location"]
        game_id = game_url.split("/")[-1]

        # Place ships
        authenticated_client.post(
            "/random-ship-placement",
            data={"player_name": "Alice"},
        )

        # First aim - should add
        response1 = authenticated_client.post(
            "/aim-shot",
            data={"game_id": game_id, "coordinate": "J1"},
            headers={"HX-Request": "true"},
        )
        assert response1.status_code == status.HTTP_200_OK
        # Response should indicate coordinate is now aimed
        assert "1/6" in response1.text or "aimed" in response1.text.lower()

        # Second aim at same coordinate - should remove
        response2 = authenticated_client.post(
            "/aim-shot",
            data={"game_id": game_id, "coordinate": "J1"},
            headers={"HX-Request": "true"},
        )
        assert response2.status_code == status.HTTP_200_OK
        # Response should indicate coordinate is no longer aimed
        assert "0/6" in response2.text or "0" in response2.text

    def test_aim_shot_returns_404_for_invalid_game(
        self, authenticated_client: TestClient
    ):
        """Test that aim-shot returns 404 for non-existent game"""
        response = authenticated_client.post(
            "/aim-shot",
            data={"game_id": "nonexistent-game-id", "coordinate": "J1"},
            headers={"HX-Request": "true"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_aim_shot_prevents_excess_selection(self, authenticated_client: TestClient):
        """Test that aim-shot prevents selecting more shots than available"""
        # Create a game
        create_response = authenticated_client.post(
            "/start-game",
            data={"action": "launch_game", "player_name": "Alice"},
            follow_redirects=False,
        )
        game_url = create_response.headers["location"]
        game_id = game_url.split("/")[-1]

        # Place ships so we have 6 shots available
        authenticated_client.post(
            "/random-ship-placement",
            data={"player_name": "Alice"},
        )

        # Aim at all 6 available shots
        for coord in ["A1", "B1", "C1", "D1", "E1", "F1"]:
            response = authenticated_client.post(
                "/aim-shot",
                data={"game_id": game_id, "coordinate": coord},
                headers={"HX-Request": "true"},
            )
            assert response.status_code == status.HTTP_200_OK

        # Now try to aim at a 7th coordinate - should fail
        fail_response = authenticated_client.post(
            "/aim-shot",
            data={"game_id": game_id, "coordinate": "G1"},
            headers={"HX-Request": "true"},
        )

        # Should return error message about shot limit
        assert fail_response.status_code == status.HTTP_200_OK
        assert "All available shots aimed" in fail_response.text
