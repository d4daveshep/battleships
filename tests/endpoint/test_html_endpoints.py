from bs4 import BeautifulSoup
from fastapi import status
from fastapi.testclient import TestClient
from httpx import Response


class TestHTMLEndpoints:
    def test_login_get_endpoint(self, client: TestClient):
        response: Response = client.get("/")
        assert response.status_code == status.HTTP_200_OK

        soup: BeautifulSoup = BeautifulSoup(response.text, "html.parser")

        assert "Login" in soup.title.string
        form = soup.find("form", {"hx-post": "/"})
        assert form
