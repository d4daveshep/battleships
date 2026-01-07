"""
Endpoint tests for the start game confirmation page.

Tests verify the start game confirmation page rendering with different parameters.
"""

from bs4 import BeautifulSoup
from fastapi import status
from fastapi.testclient import TestClient


class TestEndStartGameEndpoint:
    """Tests for GET /start-game endpoint"""

    def test_start_game_page_returns_200(self, authenticated_client: TestClient):
        """Test that start game page loads successfully"""
        response = authenticated_client.get("/start-game")

        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]

    def test_start_game_page_displays_player_name(
        self, authenticated_client: TestClient
    ):
        """Test that start game page shows the player's name"""
        response = authenticated_client.get("/start-game")

        assert response.status_code == status.HTTP_200_OK
        soup = BeautifulSoup(response.text, "html.parser")

        # Check that player name is displayed (Alice from authenticated_client fixture)
        player_element = soup.find(attrs={"data-testid": "player-name"})
        assert player_element is not None
        assert "Alice" in player_element.text

    def test_start_game_page_single_player_mode_without_opponent(
        self, authenticated_client: TestClient
    ):
        """Test that start game page shows single player mode when no opponent provided"""
        response = authenticated_client.get("/start-game")

        assert response.status_code == status.HTTP_200_OK
        soup = BeautifulSoup(response.text, "html.parser")

        # Check game mode is Single Player
        game_mode_element = soup.find(attrs={"data-testid": "game-mode"})
        assert game_mode_element is not None
        assert "Single Player" in game_mode_element.text

        # Check opponent is not displayed
        opponent_element = soup.find(attrs={"data-testid": "opponent-name"})
        assert opponent_element is None

    def test_start_game_page_two_player_mode_with_opponent(
        self, game_paired: tuple[TestClient, TestClient]
    ):
        """Test that start game page shows two player mode when opponent paired via lobby"""
        alice_client, bob_client = game_paired

        # Alice accesses the start game page after pairing with Bob
        response = alice_client.get("/start-game")

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
        """Test that start game page requires session"""
        response = client.get("/start-game")

        # Should reject no session with 401 status
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_start_game_page_has_title(self, authenticated_client: TestClient):
        """Test that start game page has proper title"""
        response = authenticated_client.get("/start-game")

        assert response.status_code == status.HTTP_200_OK
        soup = BeautifulSoup(response.text, "html.parser")

        # Check page title
        title = soup.find("title")
        assert title is not None
        assert "Battleships Game" in title.text

    def test_start_game_page_displays_heading(self, authenticated_client: TestClient):
        """Test that start game page has proper heading"""
        response = authenticated_client.get("/start-game")

        assert response.status_code == status.HTTP_200_OK
        soup = BeautifulSoup(response.text, "html.parser")

        # Check h1 heading
        heading = soup.find("h1")
        assert heading is not None
        assert "Start Game Confirmation" in heading.text

    def test_start_game_page_with_only_opponent_name_displays_error_and_redirects_to_login(
        self, client: TestClient
    ):
        """Test start game page behavior without session"""
        response = client.get("/start-game")

        # Should reject no session with 401 status
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestPostStartGameEndpoint:
    """Tests for POST /start-game endpoint"""

    def test_post_start_game_with_start_action_redirects_to_ship_placement(
        self, authenticated_client: TestClient
    ):
        """Test POST /start-game with action=start_game redirects to ship placement"""
        # Submit start game form with start_game action
        response = authenticated_client.post(
            "/start-game",
            data={"player_name": "Alice", "action": "start_game"},
            follow_redirects=False,
        )

        # Should redirect with 303 status
        assert response.status_code == status.HTTP_303_SEE_OTHER
        redirect_url = response.headers.get("location")
        assert redirect_url is not None
        assert "place-ships" in redirect_url

    def test_post_start_game_with_abandon_game_redirects_to_login(
        self, authenticated_client: TestClient
    ):
        """Test POST /start-game with action=abandon_game redirects to login page"""
        # Submit start game form with return_to_login action
        response = authenticated_client.post(
            "/start-game",
            data={"player_name": "Alice", "action": "abandon_game"},
            follow_redirects=False,
        )

        # Should redirect with 303 status
        assert response.status_code == status.HTTP_303_SEE_OTHER
        redirect_url = response.headers.get("location")
        assert redirect_url is not None
        assert redirect_url == "/" or "login" in redirect_url

    def test_post_start_game_without_action_returns_400(
        self, authenticated_client: TestClient
    ):
        """Test POST /start-game without action parameter returns 400 Bad Request"""
        # Submit start game form without action
        response = authenticated_client.post(
            "/start-game",
            data={"player_name": "Alice"},
            follow_redirects=False,
        )

        # Should return 400 Bad Request
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_start_game_with_invalid_action_returns_400(
        self, authenticated_client: TestClient
    ):
        """Test POST /start-game with invalid action returns 400 Bad Request"""
        # Submit start game form with invalid action
        response = authenticated_client.post(
            "/start-game",
            data={"player_name": "Alice", "action": "invalid_action"},
            follow_redirects=False,
        )

        # Should return 400 Bad Request
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_start_game_without_player_name_returns_422(self, client: TestClient):
        """Test POST /start-game without session returns 401 Unauthorized"""
        response = client.post(
            "/start-game",
            data={"action": "start_game"},
            follow_redirects=False,
        )

        # Should return 401 Unauthorized (no session)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestStartGamePageIntegration:
    """Integration tests for start game page flow"""

    def test_start_game_page_accessible_after_login_computer_mode(
        self, authenticated_client: TestClient
    ):
        """Test that start game page is accessible after single player login flow"""
        # Verify start game page works after single player login
        start_game_response = authenticated_client.get(
            "/start-game", params={"player_name": "Alice"}
        )
        assert start_game_response.status_code == status.HTTP_200_OK

        soup = BeautifulSoup(start_game_response.text, "html.parser")
        start_game_mode_element = soup.find(attrs={"data-testid": "game-mode"})
        assert start_game_mode_element is not None
        assert "Single Player" in start_game_mode_element.text

    def test_game_page_accessible_after_multiplayer_pairing(
        self, game_paired: tuple[TestClient, TestClient]
    ):
        """Test that game page works after multiplayer game pairing"""
        alice_client, bob_client = game_paired

        # Access start game page directly (player and opponent from session/lobby)
        start_game_response = alice_client.get("/start-game")
        assert start_game_response.status_code == status.HTTP_200_OK

        soup = BeautifulSoup(start_game_response.text, "html.parser")
        start_game_mode_element = soup.find(attrs={"data-testid": "game-mode"})
        assert start_game_mode_element is not None
        assert "Two Player" in start_game_mode_element.text

        # Both players should be shown
        assert "Alice" in start_game_response.text
        assert "Bob" in start_game_response.text
