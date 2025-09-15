import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client() -> TestClient:
    # FastAPI TestClient for integration testing
    return TestClient(app)
