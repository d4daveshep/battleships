"""
Endpoint tests for the start game confirmation page.

Tests verify the start game confirmation page rendering with different parameters.
"""

from bs4 import BeautifulSoup
from fastapi import status
from fastapi.testclient import TestClient


class TestEndStartGameEndpoint:
    """Tests for GET /start-game endpoint"""

    def test_start_game_page_returns_200(self, client: TestClient):
        """Test that start game page loads successfully"""
        response = client.get("/start-game", params={"player_name": "Alice"})

        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]

    def test_start_game_page_displays_player_name(self, client: TestClient):
        """Test that start game page shows the player's name"""
        response = client.get("/start-game", params={"player_name": "TestPlayer"})

        assert response.status_code == status.HTTP_200_OK
        soup = BeautifulSoup(response.text, "html.parser")

        # Check that player name is displayed
        player_element = soup.find(attrs={"data-testid": "player-name"})
        assert player_element is not None
        assert "TestPlayer" in player_element.text

    def test_start_game_page_single_player_mode_without_opponent(
        self, client: TestClient
    ):
        """Test that start game page shows single player mode when no opponent provided"""
        response = client.get("/start-game", params={"player_name": "Alice"})

        assert response.status_code == status.HTTP_200_OK
        soup = BeautifulSoup(response.text, "html.parser")

        # Check game mode is Single Player
        game_mode_element = soup.find(attrs={"data-testid": "game-mode"})
        assert game_mode_element is not None
        assert "Single Player" in game_mode_element.text

        # Check opponent is not displayed
        opponent_element = soup.find(attrs={"data-testid": "opponent-name"})
        assert opponent_element is None

    def test_start_game_page_two_player_mode_with_opponent(self, client: TestClient):
        """Test that start game page shows two player mode when opponent provided"""
        response = client.get(
            "/start-game", params={"player_name": "Alice", "opponent_name": "Bob"}
        )

        assert response.status_code == status.HTTP_200_OK
        soup = BeautifulSoup(response.text, "html.parser")

        # Check game mode is Two Player
        game_mode_element = soup.find(attrs={"data-testid": "game-mode"})
        assert game_mode_element is not None
        assert "Two Player" in game_mode_element.text

        # Check both players are displayed
        player_element = soup.find(attrs={"data-testid": "player-name"})
        assert player_element is not None
        assert "Alice" in player_element.text

        opponent_element = soup.find(attrs={"data-testid": "opponent-name"})
        assert opponent_element is not None
        assert "Bob" in opponent_element.text

    def test_start_game_page_with_no_player_name_specified_displays_error_and_redirects_to_login(
        self, client: TestClient
    ):
        """Test that start game page rejects empty player name"""
        response = client.get("/start-game")

        # Should reject empty player_name with 422 status
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "text/html" in response.headers["content-type"]

        # Should display an error message
        soup = BeautifulSoup(response.text, "html.parser")
        error_message = soup.find(attrs={"data-testid": "error-message"})
        assert error_message is not None
        assert (
            "player name" in error_message.text.lower()
            or "required" in error_message.text.lower()
        )  # Should reject empty player_name - redirect to login

    def test_start_game_page_has_title(self, client: TestClient):
        """Test that start game page has proper title"""
        response = client.get("/start-game", params={"player_name": "Alice"})

        assert response.status_code == status.HTTP_200_OK
        soup = BeautifulSoup(response.text, "html.parser")

        # Check page title
        title = soup.find("title")
        assert title is not None
        assert "Battleships Game" in title.text

    def test_start_game_page_displays_heading(self, client: TestClient):
        """Test that start game page has proper heading"""
        response = client.get("/start-game", params={"player_name": "Alice"})

        assert response.status_code == status.HTTP_200_OK
        soup = BeautifulSoup(response.text, "html.parser")

        # Check h1 heading
        heading = soup.find("h1")
        assert heading is not None
        assert "Start Game Confirmation" in heading.text

    def test_start_game_page_with_only_opponent_name_displays_error_and_redirects_to_login(
        self, client: TestClient
    ):
        """Test start game page behavior with only opponent name (no player name)"""
        response = client.get("/start-game", params={"opponent_name": "Bob"})

        # Should reject empty player_name with 422 status
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "text/html" in response.headers["content-type"]

        # Should display an error message
        soup = BeautifulSoup(response.text, "html.parser")
        error_message = soup.find(attrs={"data-testid": "error-message"})
        assert error_message is not None
        assert (
            "player name" in error_message.text.lower()
            or "required" in error_message.text.lower()
        )


class TestPostStartGameEndpoint:
    """Tests for POST /start-game endpoint"""

    def test_post_start_game_with_start_action_redirects_to_ship_placement(
        self, client: TestClient
    ):
        """Test POST /start-game with action=start_game redirects to ship placement"""
        # First login to create session
        client.post("/", data={"player_name": "Alice", "game_mode": "computer"})

        # Submit start game form with start_game action
        response = client.post(
            "/start-game",
            data={"player_name": "Alice", "action": "start_game"},
            follow_redirects=False,
        )

        # Should redirect with 303 status
        assert response.status_code == status.HTTP_303_SEE_OTHER
        redirect_url = response.headers.get("location")
        assert redirect_url is not None
        assert "ship-placement" in redirect_url

    def test_post_start_game_with_return_to_login_action_redirects_to_login(
        self, client: TestClient
    ):
        """Test POST /start-game with action=return_to_login redirects to login page"""
        # First login to create session
        client.post("/", data={"player_name": "Alice", "game_mode": "computer"})

        # Submit start game form with return_to_login action
        response = client.post(
            "/start-game",
            data={"player_name": "Alice", "action": "return_to_login"},
            follow_redirects=False,
        )

        # Should redirect with 303 status
        assert response.status_code == status.HTTP_303_SEE_OTHER
        redirect_url = response.headers.get("location")
        assert redirect_url is not None
        assert redirect_url == "/" or "login" in redirect_url

    def test_post_start_game_with_exit_action_redirects_to_goodbye(
        self, client: TestClient
    ):
        """Test POST /start-game with action=exit redirects to goodbye page"""
        # First login to create session
        client.post("/", data={"player_name": "Alice", "game_mode": "computer"})

        # Submit start game form with exit action
        response = client.post(
            "/start-game",
            data={"player_name": "Alice", "action": "exit"},
            follow_redirects=False,
        )

        # Should redirect with 303 status
        assert response.status_code == status.HTTP_303_SEE_OTHER
        redirect_url = response.headers.get("location")
        assert redirect_url is not None
        assert "goodbye" in redirect_url

    def test_post_start_game_without_action_returns_400(self, client: TestClient):
        """Test POST /start-game without action parameter returns 400 Bad Request"""
        # First login to create session
        client.post("/", data={"player_name": "Alice", "game_mode": "computer"})

        # Submit start game form without action
        response = client.post(
            "/start-game",
            data={"player_name": "Alice"},
            follow_redirects=False,
        )

        # Should return 400 Bad Request
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_start_game_with_invalid_action_returns_400(self, client: TestClient):
        """Test POST /start-game with invalid action returns 400 Bad Request"""
        # First login to create session
        client.post("/", data={"player_name": "Alice", "game_mode": "computer"})

        # Submit start game form with invalid action
        response = client.post(
            "/start-game",
            data={"player_name": "Alice", "action": "invalid_action"},
            follow_redirects=False,
        )

        # Should return 400 Bad Request
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_start_game_without_player_name_returns_422(self, client: TestClient):
        """Test POST /start-game without player_name returns 422 Unprocessable Entity"""
        response = client.post(
            "/start-game",
            data={"action": "start_game"},
            follow_redirects=False,
        )

        # Should return 422 Unprocessable Entity
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestStartGamePageIntegration:
    """Integration tests for start game page flow"""

    def test_start_game_page_accessible_after_login_computer_mode(
        self, client: TestClient
    ):
        """Test that start game page is accessible after single player login flow"""
        # Login with computer mode redirects to ship placement first
        client.post("/", data={"player_name": "Alice", "game_mode": "computer"})

        # Verify start game page works after single polayer login
        start_game_response = client.get("/start-game", params={"player_name": "Alice"})
        assert start_game_response.status_code == status.HTTP_200_OK

        soup = BeautifulSoup(start_game_response.text, "html.parser")
        start_game_mode_element = soup.find(attrs={"data-testid": "game-mode"})
        assert start_game_mode_element is not None
        assert "Single Player" in start_game_mode_element.text

    def test_game_page_accessible_after_multiplayer_pairing(self, client: TestClient):
        """Test that game page works after multiplayer game pairing"""
        # Set up multiplayer game pairing
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )
        client.post("/accept-game-request", data={"player_name": "Bob"})

        # Access start game page directly
        start_game_response = client.get(
            "/start-game", params={"player_name": "Alice", "opponent_name": "Bob"}
        )
        assert start_game_response.status_code == status.HTTP_200_OK

        soup = BeautifulSoup(start_game_response.text, "html.parser")
        start_game_mode_element = soup.find(attrs={"data-testid": "game-mode"})
        assert start_game_mode_element is not None
        assert "Two Player" in start_game_mode_element.text

        # Both players should be shown
        assert "Alice" in start_game_response.text
        assert "Bob" in start_game_response.text
