"""Helper functions for endpoint tests.

This module contains reusable helper functions to reduce duplication
across endpoint test files.
"""

import json
from base64 import b64decode

from bs4 import BeautifulSoup, Tag
from fastapi import status
from fastapi.testclient import TestClient
from httpx import Response
from itsdangerous import TimestampSigner


# =============================================================================
# HTMX Helpers
# =============================================================================

HTMX_HEADERS: dict[str, str] = {"HX-Request": "true"}


def make_htmx_post(
    client: TestClient,
    url: str,
    data: dict[str, str],
) -> Response:
    """Make a POST request with HTMX headers.

    Args:
        client: TestClient instance
        url: Endpoint URL
        data: Form data

    Returns:
        Response from the endpoint
    """
    return client.post(url, data=data, headers=HTMX_HEADERS)


def make_htmx_get(client: TestClient, url: str) -> Response:
    """Make a GET request with HTMX headers.

    Args:
        client: TestClient instance
        url: Endpoint URL

    Returns:
        Response from the endpoint
    """
    return client.get(url, headers=HTMX_HEADERS)


# =============================================================================
# Response Assertions
# =============================================================================


def assert_html_response(
    response: Response,
    expected_status: int = status.HTTP_200_OK,
) -> None:
    """Assert response is a successful HTML response.

    Args:
        response: HTTP response object
        expected_status: Expected status code (default 200)
    """
    assert response.status_code == expected_status, (
        f"Expected status {expected_status}, got {response.status_code}"
    )
    assert "text/html" in response.headers["content-type"], (
        f"Expected HTML content type, got {response.headers.get('content-type')}"
    )


def assert_redirect_response(
    response: Response,
    expected_location_contains: str | None = None,
) -> str:
    """Assert response is a redirect and return the location.

    Args:
        response: HTTP response object
        expected_location_contains: Optional substring to check in location

    Returns:
        The redirect location URL
    """
    assert response.status_code in [
        status.HTTP_302_FOUND,
        status.HTTP_303_SEE_OTHER,
    ], f"Expected redirect status, got {response.status_code}"
    location = response.headers["location"]
    if expected_location_contains:
        assert expected_location_contains in location, (
            f"Expected '{expected_location_contains}' in location, got '{location}'"
        )
    return location


def assert_htmx_redirect(
    response: Response,
    expected_location: str | None = None,
) -> str:
    """Assert response is an HTMX redirect (204 with HX-Redirect header).

    Args:
        response: HTTP response object
        expected_location: Optional expected redirect location

    Returns:
        The HX-Redirect header value
    """
    assert response.status_code == status.HTTP_204_NO_CONTENT, (
        f"Expected 204 for HTMX redirect, got {response.status_code}"
    )
    assert "HX-Redirect" in response.headers, "Expected HX-Redirect header"
    location = response.headers["HX-Redirect"]
    if expected_location:
        assert location == expected_location, (
            f"Expected HX-Redirect to '{expected_location}', got '{location}'"
        )
    return location


# =============================================================================
# HTML Parsing Helpers
# =============================================================================


def parse_html(response: Response) -> BeautifulSoup:
    """Parse HTML response into BeautifulSoup object.

    Args:
        response: HTTP response with HTML content

    Returns:
        BeautifulSoup object for parsing
    """
    return BeautifulSoup(response.text, "html.parser")


def find_by_testid(soup: BeautifulSoup, testid: str) -> Tag | None:
    """Find element by data-testid attribute.

    Args:
        soup: BeautifulSoup object
        testid: The data-testid value to find

    Returns:
        The element if found, None otherwise
    """
    element = soup.find(attrs={"data-testid": testid})
    if isinstance(element, Tag):
        return element
    return None


def assert_element_contains_text(
    soup: BeautifulSoup,
    testid: str,
    expected_text: str,
) -> Tag:
    """Assert element exists and contains expected text.

    Args:
        soup: BeautifulSoup object
        testid: The data-testid value to find
        expected_text: Text that should be in the element

    Returns:
        The found element
    """
    element = find_by_testid(soup, testid)
    assert element is not None, f"Element with data-testid='{testid}' not found"
    assert expected_text in element.get_text(), (
        f"Expected '{expected_text}' in element text, got: {element.get_text()}"
    )
    return element


# =============================================================================
# Game Creation Helpers
# =============================================================================


def create_game(
    client: TestClient,
    player_name: str = "Alice",
    follow_redirects: bool = False,
) -> str:
    """Create a game and return the game URL.

    Args:
        client: Authenticated TestClient instance
        player_name: Name of the player creating the game
        follow_redirects: Whether to follow redirects (default False)

    Returns:
        The game URL (e.g., "/game/{game_id}")
    """
    response = client.post(
        "/start-game",
        data={"action": "launch_game", "player_name": player_name},
        follow_redirects=follow_redirects,
    )
    assert response.status_code == status.HTTP_303_SEE_OTHER, (
        f"Expected 303 redirect, got {response.status_code}"
    )
    return response.headers["location"]


def get_game_id_from_url(game_url: str) -> str:
    """Extract game_id from a game URL.

    Args:
        game_url: URL like "/game/{game_id}"

    Returns:
        The game_id string
    """
    return game_url.split("/")[-1]


def place_ships_randomly(
    client: TestClient,
    player_name: str = "Alice",
) -> Response:
    """Place ships randomly for a player.

    Args:
        client: Authenticated TestClient instance
        player_name: Name of the player

    Returns:
        Response from the random ship placement endpoint
    """
    return client.post(
        "/random-ship-placement",
        data={"player_name": player_name},
    )


def create_player(client: TestClient, name: str, game_mode: str = "human") -> Response:
    """Helper function to create a player in the lobby

    Args:
        client: TestClient instance
        name: Player name
        game_mode: Game mode ("human" or "computer"), defaults to "human"

    Returns:
        Response from the login endpoint
    """
    return client.post("/login", data={"player_name": name, "game_mode": game_mode})


def send_game_request(client: TestClient, opponent_name: str) -> Response:
    """Helper function to send a game request

    Args:
        client: TestClient instance for the requesting player
        opponent_name: Name of the opponent to send request to

    Returns:
        Response from the select-opponent endpoint
    """
    return client.post(
        "/select-opponent",
        data={"opponent_name": opponent_name},
    )


def accept_game_request(client: TestClient, follow_redirects: bool = True) -> Response:
    """Helper function to accept a game request

    Args:
        client: TestClient instance for the player accepting
        follow_redirects: Whether to follow redirects (defaults to True)

    Returns:
        Response from the accept-game-request endpoint
    """
    return client.post(
        "/accept-game-request",
        data={},
        follow_redirects=follow_redirects,
    )


def decline_game_request(client: TestClient) -> Response:
    """Helper function to decline a game request

    Args:
        client: TestClient instance for the player declining

    Returns:
        Response from the decline-game-request endpoint
    """
    return client.post("/decline-game-request", data={})


def leave_lobby(client: TestClient) -> Response:
    """Helper function to leave the lobby

    Args:
        client: TestClient instance for the player leaving

    Returns:
        Response from the leave-lobby endpoint
    """
    return client.post("/leave-lobby", data={})


def decode_session(session_cookie: str) -> dict[str, str]:
    """Decode a session cookie to get the session data

    Args:
        session_cookie: The session cookie value

    Returns:
        Dictionary containing session data
    """
    signer: TimestampSigner = TimestampSigner("your-secret-key-here")
    unsigned_data: bytes = signer.unsign(session_cookie.encode("utf-8"))
    session_data: dict[str, str] = json.loads(b64decode(unsigned_data))
    return session_data
