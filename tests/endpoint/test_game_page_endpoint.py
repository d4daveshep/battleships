"""
Endpoint tests for the game page.

Tests verify the game page rendering with different parameters.
"""

from bs4 import BeautifulSoup
from fastapi import status
from fastapi.testclient import TestClient


class TestGamePageEndpoint:
    """Tests for GET /game endpoint"""

    def test_game_page_returns_200(self, client: TestClient):
        """Test that game page loads successfully"""
        response = client.get("/game", params={"player_name": "Alice"})

        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]

    def test_game_page_displays_player_name(self, client: TestClient):
        """Test that game page shows the player's name"""
        response = client.get("/game", params={"player_name": "TestPlayer"})

        assert response.status_code == status.HTTP_200_OK
        soup = BeautifulSoup(response.text, "html.parser")

        # Check that player name is displayed
        player_element = soup.find(attrs={"data-testid": "player-name"})
        assert player_element is not None
        assert "TestPlayer" in player_element.text

    def test_game_page_single_player_mode_without_opponent(self, client: TestClient):
        """Test that game page shows single player mode when no opponent provided"""
        response = client.get("/game", params={"player_name": "Alice"})

        assert response.status_code == status.HTTP_200_OK
        soup = BeautifulSoup(response.text, "html.parser")

        # Check game mode is Single Player
        game_mode_element = soup.find(attrs={"data-testid": "game-mode"})
        assert game_mode_element is not None
        assert "Single Player" in game_mode_element.text

        # Check opponent is not displayed
        opponent_element = soup.find(attrs={"data-testid": "opponent-name"})
        assert opponent_element is None

    def test_game_page_two_player_mode_with_opponent(self, client: TestClient):
        """Test that game page shows two player mode when opponent provided"""
        response = client.get(
            "/game", params={"player_name": "Alice", "opponent_name": "Bob"}
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

    def test_game_page_works_with_empty_parameters(self, client: TestClient):
        """Test that game page works with empty parameters"""
        response = client.get("/game")

        assert response.status_code == status.HTTP_200_OK
        soup = BeautifulSoup(response.text, "html.parser")

        # Should default to Single Player mode with empty player name
        game_mode_element = soup.find(attrs={"data-testid": "game-mode"})
        assert game_mode_element is not None
        assert "Single Player" in game_mode_element.text

    def test_game_page_has_title(self, client: TestClient):
        """Test that game page has proper title"""
        response = client.get("/game", params={"player_name": "Alice"})

        assert response.status_code == status.HTTP_200_OK
        soup = BeautifulSoup(response.text, "html.parser")

        # Check page title
        title = soup.find("title")
        assert title is not None
        assert "Battleships Game" in title.text

    def test_game_page_displays_heading(self, client: TestClient):
        """Test that game page has proper heading"""
        response = client.get("/game", params={"player_name": "Alice"})

        assert response.status_code == status.HTTP_200_OK
        soup = BeautifulSoup(response.text, "html.parser")

        # Check h1 heading
        heading = soup.find("h1")
        assert heading is not None
        assert "Start Game Confirmation" in heading.text

    def test_game_page_with_special_characters_in_names(self, client: TestClient):
        """Test that game page handles special characters in player names"""
        response = client.get(
            "/game",
            params={
                "player_name": "Alice-123",
                "opponent_name": "Bob_456",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        soup = BeautifulSoup(response.text, "html.parser")

        player_element = soup.find(attrs={"data-testid": "player-name"})
        assert player_element is not None
        assert "Alice-123" in player_element.text

        opponent_element = soup.find(attrs={"data-testid": "opponent-name"})
        assert opponent_element is not None
        assert "Bob_456" in opponent_element.text

    def test_game_page_with_only_opponent_name(self, client: TestClient):
        """Test game page behavior with only opponent name (no player name)"""
        response = client.get("/game", params={"opponent_name": "Bob"})

        assert response.status_code == status.HTTP_200_OK
        soup = BeautifulSoup(response.text, "html.parser")

        # Should still show Two Player mode if opponent is provided
        game_mode_element = soup.find(attrs={"data-testid": "game-mode"})
        assert game_mode_element is not None
        assert "Two Player" in game_mode_element.text

        # Opponent should be displayed
        opponent_element = soup.find(attrs={"data-testid": "opponent-name"})
        assert opponent_element is not None
        assert opponent_element.text is not None
        assert "Bob" in opponent_element.text


class TestGamePageIntegration:
    """Integration tests for game page flow"""

    def test_game_page_accessible_after_login_computer_mode(self, client: TestClient):
        """Test that game page is accessible after single player login flow"""
        # Login with computer mode redirects to ship placement first
        client.post("/", data={"player_name": "Alice", "game_mode": "computer"})

        # Eventually would redirect to game after ship placement
        # For now, just verify game page works independently
        game_response = client.get("/game", params={"player_name": "Alice"})
        assert game_response.status_code == status.HTTP_200_OK

        soup = BeautifulSoup(game_response.text, "html.parser")
        game_mode_element = soup.find(attrs={"data-testid": "game-mode"})
        assert game_mode_element is not None
        assert "Single Player" in game_mode_element.text

    def test_game_page_accessible_after_multiplayer_pairing(self, client: TestClient):
        """Test that game page works after multiplayer game pairing"""
        # Set up multiplayer game pairing
        client.post("/", data={"player_name": "Alice", "game_mode": "human"})
        client.post("/", data={"player_name": "Bob", "game_mode": "human"})
        client.post(
            "/select-opponent", data={"player_name": "Alice", "opponent_name": "Bob"}
        )
        client.post("/accept-game-request", data={"player_name": "Bob"})

        # Access game page directly
        game_response = client.get(
            "/game", params={"player_name": "Alice", "opponent_name": "Bob"}
        )
        assert game_response.status_code == status.HTTP_200_OK

        soup = BeautifulSoup(game_response.text, "html.parser")
        game_mode_element = soup.find(attrs={"data-testid": "game-mode"})
        assert game_mode_element is not None
        assert "Two Player" in game_mode_element.text

        # Both players should be shown
        assert "Alice" in game_response.text
        assert "Bob" in game_response.text
