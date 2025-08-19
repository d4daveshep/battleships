from fastapi import status


class TestLoginFormSubmission:
    # Integration tests for login form submission and routing behavior
    
    def test_valid_login_redirects_to_lobby(self, client, valid_login_data):
        # Test that valid login with human mode redirects to lobby
        response = client.post("/", data=valid_login_data, follow_redirects=False)
        
        assert response.status_code == status.HTTP_302_FOUND
        assert response.headers["location"] == "/lobby?player_name=Alice"
    
    def test_valid_login_computer_mode_redirects_to_game(self, client, valid_computer_mode_data):
        # Test that valid login with computer mode redirects to game
        response = client.post("/", data=valid_computer_mode_data, follow_redirects=False)
        
        assert response.status_code == status.HTTP_302_FOUND
        assert response.headers["location"] == "/game?player_name=Bob"
    
    def test_invalid_login_returns_form_with_error(self, client, invalid_login_data):
        # Test that invalid login returns form page with validation error
        response = client.post("/", data=invalid_login_data)
        
        assert response.status_code == status.HTTP_200_OK
        assert "Player name must be between 2 and 20 characters" in response.text
        assert "error" in response.text  # CSS class for styling
    
    def test_quote_stripping_in_login_form(self, client, quoted_name_data):
        # Test that quotes are stripped during form submission
        response = client.post("/", data=quoted_name_data, follow_redirects=False)
        
        assert response.status_code == status.HTTP_302_FOUND
        # Note: URL encoding preserves quotes in URL but validation strips them for processing
        assert "/lobby?player_name=" in response.headers["location"]
        assert "Charlie" in response.headers["location"]
    
    def test_empty_player_name_returns_error(self, client):
        # Test empty player name validation
        response = client.post("/", data={"player_name": "", "game_mode": "human"})
        
        assert response.status_code == status.HTTP_200_OK
        assert "Player name is required" in response.text
        assert "error" in response.text
    
    def test_whitespace_only_name_returns_error(self, client):
        # Test whitespace-only player name validation  
        response = client.post("/", data={"player_name": "   ", "game_mode": "human"})
        
        assert response.status_code == status.HTTP_200_OK
        assert "Player name is required" in response.text


class TestPlayerNameValidationEndpoint:
    # Integration tests for HTMX player name validation endpoint
    
    def test_valid_name_validation_endpoint(self, client):
        # Test HTMX validation endpoint with valid name
        response = client.post("/player-name", data={"player_name": "ValidName"})
        
        assert response.status_code == status.HTTP_200_OK
        assert "valid" in response.text  # CSS class
        assert "ValidName" in response.text  # Name should be preserved
    
    def test_invalid_name_validation_endpoint(self, client):
        # Test HTMX validation endpoint with invalid name
        response = client.post("/player-name", data={"player_name": "X"})
        
        assert response.status_code == status.HTTP_200_OK
        assert "error" in response.text  # CSS class
        assert "Player name must be between 2 and 20 characters" in response.text
    
    def test_validation_endpoint_preserves_quotes(self, client):
        # Test that validation endpoint doesn't strip quotes (strip_quotes=False)
        response = client.post("/player-name", data={"player_name": '"TestName"'})
        
        assert response.status_code == status.HTTP_200_OK
        assert "error" in response.text  # Should fail due to quotes
        assert "Player name can only contain letter, numbers and spaces" in response.text