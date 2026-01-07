from bs4 import BeautifulSoup
from fastapi import status
from fastapi.testclient import TestClient
from httpx import Response
from test_helpers import decode_session


class TestLoginEndpoints:
    def test_login_get_endpoint(self, client: TestClient):
        response: Response = client.get("/login")
        assert response.status_code == status.HTTP_200_OK

        soup: BeautifulSoup = BeautifulSoup(response.text, "html.parser")

        assert soup.title.string
        assert "Login" in soup.title.string
        form = soup.find("form", {"hx-post": "/login"})
        assert form

    def test_login_post_sets_player_id_in_session(self, client: TestClient):
        response: Response = client.post(
            "/login", data={"player_name": "TestPlayer", "game_mode": "computer"}
        )
        assert response.status_code == status.HTTP_200_OK

        # Verify session cookie exists
        assert "session" in client.cookies

        # Decode session cookie to verify player-id is set
        session_data: dict[str, str] = decode_session(client.cookies["session"])

        # Verify player-id key exists and has a non-empty value
        assert "player-id" in session_data
        assert session_data["player-id"]
