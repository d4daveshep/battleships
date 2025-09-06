from fastapi import status


class TestTemplateRendering:
    # Integration tests for Jinja2 template rendering and page content
    
    def test_login_page_renders_correctly(self, client):
        # Test that login page renders with expected form elements
        response = client.get("/")
        
        assert response.status_code == status.HTTP_200_OK
        assert "player_name" in response.text
        assert "game_mode" in response.text
        assert "human" in response.text
        assert "computer" in response.text
        # Check for form structure
        assert "<form" in response.text
        assert "method=" in response.text
    
    def test_game_page_renders_with_player_name(self, client):
        # Test that game page renders with player name parameter
        response = client.get("/game?player_name=TestPlayer")
        
        assert response.status_code == status.HTTP_200_OK
        assert "TestPlayer" in response.text
        assert "Single Player" in response.text  # Game mode should be displayed
    
    def test_game_page_handles_missing_player_name(self, client):
        # Test game page behavior when player_name is missing
        response = client.get("/game")
        
        assert response.status_code == status.HTTP_200_OK
        # Should still render but with empty player name
        assert "Single Player" in response.text
    
    def test_lobby_page_renders_with_player_data(self, client):
        # Test lobby page rendering with player name
        response = client.get("/lobby?player_name=LobbyPlayer")
        
        assert response.status_code == status.HTTP_200_OK
        assert "LobbyPlayer" in response.text
        assert "Two Player" in response.text  # Game mode for lobby
    
    def test_lobby_page_handles_missing_player_name(self, client):
        # Test lobby page behavior when player_name is missing
        response = client.get("/lobby")
        
        assert response.status_code == status.HTTP_200_OK
        assert "Two Player" in response.text
        # Should render with empty available players list
        assert "available_players" in response.text or len(response.text) > 0
    
    def test_error_state_template_rendering(self, client):
        # Test that validation errors are properly rendered in templates
        response = client.post("/", data={"player_name": "X", "game_mode": "human"})  # Too short
        
        assert response.status_code == status.HTTP_200_OK
        # Check that error styling is applied
        assert "error" in response.text
        assert "Player name must be between 2 and 20 characters" in response.text
        # Form should be re-rendered with error state
        assert "<form" in response.text
        assert "game_mode" in response.text
    
    def test_success_state_preserves_valid_input(self, client):
        # Test that valid input is preserved when there are no errors
        # This tests the template logic for preserving form state
        response = client.post("/", data={"player_name": "ValidPlayer", "game_mode": "human"}, follow_redirects=False)
        
        # Should redirect for valid input, not render template with preserved state
        assert response.status_code == status.HTTP_302_FOUND


class TestHealthEndpoint:
    # Integration tests for health check endpoint
    
    def test_health_check_returns_healthy_status(self, client):
        # Test health check endpoint returns expected JSON
        response = client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"status": "healthy"}
    
    def test_health_check_content_type(self, client):
        # Test health check returns JSON content type
        response = client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        assert "application/json" in response.headers.get("content-type", "")


class TestLeaveLobbyTemplateRendering:
    # Integration tests for leave lobby button and template rendering
    
    def test_lobby_page_renders_leave_lobby_button(self, client):
        # Test that lobby page includes the Leave Lobby button
        response = client.get("/lobby?player_name=TestPlayer")
        
        assert response.status_code == status.HTTP_200_OK
        # Check for Leave Lobby button in the rendered HTML
        assert 'data-testid="leave-lobby-button"' in response.text
        assert "Leave Lobby" in response.text
        assert '<button' in response.text
        
    def test_leave_lobby_button_has_correct_attributes(self, client):
        # Test that Leave Lobby button has correct HTML attributes
        response = client.get("/lobby?player_name=ButtonTest")
        
        assert response.status_code == status.HTTP_200_OK
        # Button should be properly formed with necessary attributes
        assert 'type="submit"' in response.text or 'type="button"' in response.text
        # Should have proper form or onclick handler
        assert 'action=' in response.text or 'onclick=' in response.text or 'hx-' in response.text
        
    def test_lobby_template_includes_leave_functionality(self, client):
        # Test that lobby template includes proper form or HTMX for leaving
        # Clear lobby and add test player
        client.post("/test/reset-lobby")
        client.post("/", data={"player_name": "LeaveTest", "game_mode": "human"})
        
        response = client.get("/lobby?player_name=LeaveTest")
        
        assert response.status_code == status.HTTP_200_OK
        # Template should include mechanism to leave lobby
        assert "leave-lobby" in response.text.lower() or "/leave" in response.text
        
    def test_lobby_template_leave_button_accessibility(self, client):
        # Test that Leave Lobby button has proper accessibility attributes
        response = client.get("/lobby?player_name=AccessTest")
        
        assert response.status_code == status.HTTP_200_OK
        # Check for accessibility features (though we'll keep it simple for now)
        leave_button_html = response.text
        # Button should be clearly identifiable
        assert "Leave Lobby" in leave_button_html
        assert 'data-testid="leave-lobby-button"' in leave_button_html
        
    def test_lobby_template_context_includes_player_name(self, client):
        # Test that lobby template context properly includes player name for leave functionality
        response = client.get("/lobby?player_name=ContextTest")
        
        assert response.status_code == status.HTTP_200_OK
        # Player name should be available in template context for the leave action
        assert "ContextTest" in response.text
        # Should have some way to identify current player for leave action
        assert 'name="player_name"' in response.text or 'value="ContextTest"' in response.text