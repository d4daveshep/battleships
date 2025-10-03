import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture(autouse=True)
def reset_lobby(client: "TestClient") -> None:
    """Reset lobby state before each test"""
    client.post("/test/reset-lobby")


@pytest.fixture
def client() -> TestClient:
    # FastAPI TestClient for integration testing
    return TestClient(app)
