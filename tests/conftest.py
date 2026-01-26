"""Root-level test configuration and shared fixtures.

This module provides fixtures and utilities that are shared across all test types:
- Unit tests (tests/unit/)
- Endpoint/integration tests (tests/endpoint/)
- BDD tests (tests/bdd/)
"""

import pytest
from starlette.testclient import TestClient


@pytest.fixture
def base_client() -> TestClient:
    """Base TestClient fixture available to all tests.

    This creates a fresh TestClient with no authentication.
    Use this as a building block for more specialized fixtures.

    Returns:
        TestClient instance with follow_redirects=False
    """
    from main import app

    return TestClient(app, follow_redirects=False)
