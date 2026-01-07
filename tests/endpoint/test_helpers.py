"""Helper functions for endpoint tests.

This module contains reusable helper functions to reduce duplication
across endpoint test files.
"""

import json
from base64 import b64decode

from fastapi.testclient import TestClient
from httpx import Response
from itsdangerous import TimestampSigner


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
