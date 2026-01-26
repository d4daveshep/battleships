import pytest
from fastapi.testclient import TestClient
from main import app

# Import helpers from the same directory
from helpers import accept_game_request, create_player, send_game_request


@pytest.fixture(autouse=True)
def reset_lobby(client: "TestClient") -> None:
    """Reset lobby state before each test"""
    client.post("/test/reset-lobby")


@pytest.fixture
def client() -> TestClient:
    # FastAPI TestClient for integration testing
    return TestClient(app)


@pytest.fixture
def authenticated_client(client: TestClient) -> TestClient:
    """TestClient with an authenticated session for Alice (computer mode)

    Args:
        client: TestClient instance

    Returns:
        TestClient with authenticated session
    """
    create_player(client, "Alice", "computer")
    return client


@pytest.fixture
def alice_client(client: TestClient) -> TestClient:
    """TestClient with Alice logged in (human mode)

    Args:
        client: TestClient instance

    Returns:
        TestClient with Alice authenticated in human mode
    """
    create_player(client, "Alice", "human")
    return client


@pytest.fixture
def bob_client() -> TestClient:
    """TestClient with Bob logged in (human mode)

    Returns:
        TestClient with Bob authenticated in human mode
    """
    client = TestClient(app)
    create_player(client, "Bob", "human")
    return client


@pytest.fixture
def charlie_client() -> TestClient:
    """TestClient with Charlie logged in (human mode)

    Returns:
        TestClient with Charlie authenticated in human mode
    """
    client = TestClient(app)
    create_player(client, "Charlie", "human")
    return client


@pytest.fixture
def diana_client() -> TestClient:
    """TestClient with Diana logged in (human mode)

    Returns:
        TestClient with Diana authenticated in human mode
    """
    client = TestClient(app)
    create_player(client, "Diana", "human")
    return client


@pytest.fixture
def two_player_lobby(
    alice_client: TestClient, bob_client: TestClient
) -> tuple[TestClient, TestClient]:
    """Two players (Alice, Bob) in lobby

    Args:
        alice_client: TestClient with Alice authenticated
        bob_client: TestClient with Bob authenticated

    Returns:
        Tuple of (alice_client, bob_client)
    """
    return (alice_client, bob_client)


@pytest.fixture
def game_request_pending(
    alice_client: TestClient, bob_client: TestClient
) -> tuple[TestClient, TestClient]:
    """Alice has sent game request to Bob (pending)

    Args:
        alice_client: TestClient with Alice authenticated
        bob_client: TestClient with Bob authenticated

    Returns:
        Tuple of (alice_client, bob_client) with request pending
    """
    send_game_request(alice_client, "Bob")
    return (alice_client, bob_client)


@pytest.fixture
def game_paired(
    alice_client: TestClient, bob_client: TestClient
) -> tuple[TestClient, TestClient]:
    """Alice and Bob paired (request accepted)

    Args:
        alice_client: TestClient with Alice authenticated
        bob_client: TestClient with Bob authenticated

    Returns:
        Tuple of (alice_client, bob_client) with game paired
    """
    send_game_request(alice_client, "Bob")
    accept_game_request(bob_client)
    return (alice_client, bob_client)
