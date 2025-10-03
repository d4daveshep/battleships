import pytest
from fastapi.testclient import TestClient
from httpx import Response
from main import app


@pytest.fixture(autouse=True)
def reset_lobby(client: "TestClient") -> None:
    """Reset lobby state before each test"""
    client.post("/test/reset-lobby")


@pytest.fixture
def client() -> TestClient:
    # FastAPI TestClient for integration testing
    return TestClient(app)


def create_player(client: TestClient, name: str) -> Response:
    """Helper function to create a player in the lobby

    Args:
        client: TestClient instance
        name: Player name

    Returns:
        Response from the login endpoint
    """
    return client.post("/", data={"player_name": name, "game_mode": "human"})
