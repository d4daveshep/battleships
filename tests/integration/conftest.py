import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client() -> TestClient:
    # FastAPI TestClient for integration testing
    return TestClient(app)


@pytest.fixture
def valid_login_data() -> dict[str, str]:
    # Valid form data for login POST requests
    return {"player_name": "Alice", "game_mode": "human"}


@pytest.fixture
def valid_computer_mode_data() -> dict[str, str]:
    # Valid form data for computer game mode
    return {"player_name": "Bob", "game_mode": "computer"}


@pytest.fixture
def invalid_login_data() -> dict[str, str]:
    # Invalid form data that should trigger validation errors
    return {"player_name": "A", "game_mode": "human"}  # Too short


@pytest.fixture
def quoted_name_data() -> dict[str, str]:
    # Form data with quoted player name for quote stripping tests
    return {"player_name": '"Charlie"', "game_mode": "human"}