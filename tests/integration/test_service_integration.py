from fastapi import status


class TestAuthServiceIntegration:
    # Integration tests for AuthService integration with FastAPI endpoints

    def test_auth_service_integration_in_login_form(self, client):
        # Test that AuthService validation is properly integrated in login flow
        response = client.post(
            "/",
            data={"player_name": "AB", "game_mode": "human"},
            follow_redirects=False,
        )  # Min length

        assert response.status_code == status.HTTP_303_SEE_OTHER
        assert "/lobby?player_name=AB" in response.headers["location"]

    def test_auth_service_integration_in_player_name_validation_htmx_endpoint(
        self, client
    ):
        # Test that AuthService validation is properly integrated in HTMX endpoint
        response = client.post("/player-name", data={"player_name": "ValidPlayer"})

        assert response.status_code == status.HTTP_200_OK
        assert "valid" in response.text
        assert "ValidPlayer" in response.text

    def test_auth_service_quote_stripping_behavior_difference(self, client):
        # Test that login form strips quotes but HTMX endpoint doesn't
        quoted_name = '"QuotedName"'

        # Login form should strip quotes (strip_quotes=True)
        login_response = client.post(
            "/",
            data={"player_name": quoted_name, "game_mode": "human"},
            follow_redirects=False,
        )
        assert login_response.status_code == status.HTTP_303_SEE_OTHER
        # Note: URL encoding preserves quotes in URL but validation strips them for processing
        assert "/lobby?player_name=" in login_response.headers["location"]
        assert "QuotedName" in login_response.headers["location"]

        # HTMX endpoint should NOT strip quotes (strip_quotes=False)
        htmx_response = client.post("/player-name", data={"player_name": quoted_name})
        assert htmx_response.status_code == status.HTTP_200_OK
        assert "error" in htmx_response.text  # Should fail validation due to quotes


class TestLobbyServiceIntegration:
    # Integration tests for LobbyService integration with FastAPI endpoints

    def test_lobby_service_integration_basic_flow(self, client):
        # Test that LobbyService is properly called for lobby page
        response = client.get("/lobby?player_name=TestPlayer")

        assert response.status_code == status.HTTP_200_OK
        assert "TestPlayer" in response.text
        # Should contain available_players data structure from LobbyService

    def test_lobby_service_diana_scenario_integration(self, client):
        # Test that Diana special scenario works end-to-end
        # First, clear the lobby to ensure clean state
        client.post("/test/reset-lobby")

        # Add Alice, Bob, and Charlie to the lobby
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        client.post("/", data={"player_name": "Charlie", "game_mode": "human"})

        # Now add Diana
        client.post("/", data={"player_name": "Diana", "game_mode": "human"})

        # Now Diana should see them when accessing the lobby
        response = client.get("/lobby?player_name=Diana")

        assert response.status_code == status.HTTP_200_OK
        assert "Diana" in response.text
        # Diana should see Alice, Bob, Charlie from LobbyService
        assert "Alice" in response.text
        assert "Bob" in response.text
        assert "Charlie" in response.text

    def test_lobby_service_eve_scenario_integration(self, client):
        # Test that Eve special scenario works end-to-end
        response = client.get("/lobby?player_name=Eve")

        assert response.status_code == status.HTTP_200_OK
        assert "Eve" in response.text
        # Eve should see empty lobby regardless of actual state

    def test_lobby_service_empty_name_handling(self, client):
        # Test lobby service integration with empty player name
        response = client.get("/lobby?player_name=")

        assert response.status_code == status.HTTP_200_OK
        # Should handle empty name gracefully via LobbyService

    def test_lobby_service_whitespace_handling(self, client):
        # Test lobby service integration with whitespace player name
        response = client.get("/lobby?player_name=%20%20%20")  # URL-encoded spaces

        assert response.status_code == status.HTTP_200_OK
        # Should handle whitespace gracefully via LobbyService


class TestGlobalLobbyState:
    # Integration tests for global lobby state consistency

    def test_global_lobby_consistency_across_requests(self, client):
        # Test that the same global lobby instance is used across requests
        # This is hard to test directly, but we can verify consistent behavior

        # Multiple requests to lobby should behave consistently
        response1 = client.get("/lobby?player_name=Player1")
        response2 = client.get("/lobby?player_name=Player2")

        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        # Both should be using the same lobby service instance

    def test_service_instances_are_properly_initialized(self, client):
        # Test that service instances are working by triggering their methods

        # Test AuthService is working
        auth_response = client.post("/player-name", data={"player_name": "TestAuth"})
        assert auth_response.status_code == status.HTTP_200_OK

        # Test LobbyService is working
        lobby_response = client.get("/lobby?player_name=TestLobby")
        assert lobby_response.status_code == status.HTTP_200_OK

        # Both services should be functioning properly


class TestEndToEndWorkflows:
    # Integration tests for complete user workflows

    def test_complete_human_game_workflow(self, client):
        # Test complete flow: login form -> lobby

        # Step 1: Get login form
        login_page = client.get("/")
        assert login_page.status_code == status.HTTP_200_OK

        # Step 2: Submit valid login for human mode
        login_submit = client.post(
            "/",
            data={"player_name": "WorkflowUser", "game_mode": "human"},
            follow_redirects=False,
        )
        assert login_submit.status_code == status.HTTP_303_SEE_OTHER
        assert "/lobby?player_name=WorkflowUser" in login_submit.headers["location"]

        # Step 3: Access lobby page
        lobby_page = client.get("/lobby?player_name=WorkflowUser")
        assert lobby_page.status_code == status.HTTP_200_OK
        assert "WorkflowUser" in lobby_page.text

    def test_complete_computer_game_workflow(self, client):
        # Test complete flow: login form -> game

        # Step 1: Get login form
        login_page = client.get("/")
        assert login_page.status_code == status.HTTP_200_OK

        # Step 2: Submit valid login for computer mode
        login_submit = client.post(
            "/",
            data={"player_name": "ComputerUser", "game_mode": "computer"},
            follow_redirects=False,
        )
        assert login_submit.status_code == status.HTTP_303_SEE_OTHER
        assert "/game?player_name=ComputerUser" in login_submit.headers["location"]

        # Step 3: Access game page
        game_page = client.get("/game?player_name=ComputerUser")
        assert game_page.status_code == status.HTTP_200_OK
        assert "ComputerUser" in game_page.text

    def test_validation_error_workflow(self, client):
        # Test workflow with validation errors

        # Step 1: Submit invalid login
        response = client.post("/", data={"player_name": "X", "game_mode": "human"})
        assert response.status_code == status.HTTP_200_OK
        assert "Player name must be between 2 and 20 characters" in response.text

        # User should be able to retry with valid input
        # (This would require maintaining form state, which the app does)


class TestHealthEndpoint:
    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK


class TestLeaveLobbyIntegration:
    # Integration tests for leave lobby functionality

    def test_leave_lobby_endpoint_exists_and_accepts_post(self, client):
        # Test that the leave lobby endpoint exists and accepts POST requests
        response = client.post("/leave-lobby", data={"player_name": "TestPlayer"})

        # Should not return 404 (endpoint should exist)
        # Should not return 405 (method should be allowed)
        assert response.status_code != status.HTTP_404_NOT_FOUND
        assert response.status_code != status.HTTP_405_METHOD_NOT_ALLOWED

    def test_leave_lobby_removes_player_from_lobby_state(self, client):
        # Test that leaving lobby removes player from the lobby state
        # First, clear the lobby
        client.post("/test/reset-lobby")

        # Add player to lobby
        client.post("/", data={"player_name": "LeavingPlayer", "game_mode": "human"})

        # Verify player is in lobby
        lobby_response = client.get("/lobby?player_name=AnotherPlayer")
        assert "LeavingPlayer" in lobby_response.text

        # Player leaves lobby
        leave_response = client.post(
            "/leave-lobby", data={"player_name": "LeavingPlayer"}
        )
        assert leave_response.status_code == status.HTTP_200_OK

        # Verify player is no longer in lobby
        lobby_check = client.get("/lobby?player_name=AnotherPlayer")
        assert "LeavingPlayer" not in lobby_check.text

    def test_leave_lobby_redirects_to_home_page(self, client):
        # Test that leaving lobby redirects to home/login page
        # Add player to lobby first
        client.post("/", data={"player_name": "RedirectTest", "game_mode": "human"})

        # Leave lobby
        response = client.post(
            "/leave-lobby", data={"player_name": "RedirectTest"}, follow_redirects=False
        )

        # Should redirect to home page
        assert response.status_code == status.HTTP_302_FOUND
        assert response.headers["location"] == "/"

    def test_leave_lobby_with_invalid_player_name(self, client):
        # Test leaving lobby with player name that doesn't exist
        response = client.post(
            "/leave-lobby", data={"player_name": "NonExistentPlayer"}
        )

        # Should handle gracefully (not crash)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]

    def test_leave_lobby_with_empty_player_name(self, client):
        # Test leaving lobby with empty player name
        response = client.post("/leave-lobby", data={"player_name": ""})

        # Should handle gracefully
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]

    def test_leave_lobby_affects_other_players_view(self, client):
        # Test that when a player leaves, other players' views are updated
        # Clear lobby first
        client.post("/test/reset-lobby")

        # Add multiple players
        client.post("/", data={"player_name": "StayingPlayer", "game_mode": "human"})
        client.post("/", data={"player_name": "LeavingPlayer", "game_mode": "human"})

        # Verify both players are visible to each other
        staying_view = client.get("/lobby?player_name=StayingPlayer")
        assert "LeavingPlayer" in staying_view.text

        # One player leaves
        client.post("/leave-lobby", data={"player_name": "LeavingPlayer"})

        # Check that staying player no longer sees the leaving player
        updated_view = client.get("/lobby?player_name=StayingPlayer")
        assert "LeavingPlayer" not in updated_view.text
        assert "StayingPlayer" in updated_view.text  # Should still see themselves

    def test_leave_lobby_endpoint_real_time_polling_integration(self, client):
        # Test that leave lobby integrates properly with real-time polling endpoint
        # Add players to lobby
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "PollingPlayer", "game_mode": "human"})
        client.post(
            "/", data={"player_name": "LeavingPlayerPolling", "game_mode": "human"}
        )

        # Check initial state via polling endpoint
        initial_poll = client.get("/lobby/players/PollingPlayer")
        assert "LeavingPlayerPolling" in initial_poll.text

        # Player leaves
        client.post("/leave-lobby", data={"player_name": "LeavingPlayerPolling"})

        # Check updated state via polling endpoint
        updated_poll = client.get("/lobby/players/PollingPlayer")
        assert "LeavingPlayerPolling" not in updated_poll.text
