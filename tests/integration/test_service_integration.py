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

        assert response.status_code == status.HTTP_302_FOUND
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
        assert login_response.status_code == status.HTTP_302_FOUND
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
        assert login_submit.status_code == status.HTTP_302_FOUND
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
        assert login_submit.status_code == status.HTTP_302_FOUND
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
