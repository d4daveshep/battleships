import json
from base64 import b64decode

from bs4 import BeautifulSoup
from fastapi import status
from fastapi.testclient import TestClient
from httpx import Response
from itsdangerous import TimestampSigner


class TestLoginEndpoints:
    def test_login_get_endpoint(self, client: TestClient):
        response: Response = client.get("/")
        assert response.status_code == status.HTTP_200_OK

        soup: BeautifulSoup = BeautifulSoup(response.text, "html.parser")

        assert soup.title.string
        assert "Login" in soup.title.string
        form = soup.find("form", {"hx-post": "/"})
        assert form

    def test_login_post_sets_player_id_in_session(self, client: TestClient):
        response: Response = client.post(
            "/", data={"player_name": "TestPlayer", "game_mode": "computer"}
        )
        assert response.status_code == status.HTTP_200_OK

        # Verify session cookie exists
        assert "session" in client.cookies

        # Decode session cookie to verify player-id is set
        session_cookie: str = client.cookies["session"]
        signer: TimestampSigner = TimestampSigner("your-secret-key-here")
        unsigned_data: bytes = signer.unsign(session_cookie.encode("utf-8"))
        session_data: dict[str, str] = json.loads(b64decode(unsigned_data))

        # Verify player-id key exists and has a non-empty value
        assert "player-id" in session_data
        assert session_data["player-id"]
