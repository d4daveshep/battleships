"""Integration tests for gameplay endpoints - aiming shots during gameplay."""

from typing import Any

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from httpx import Response

from game.model import Coord, GameBoard, Orientation, Ship, ShipType
from game.game_service import Game, GameMode
from game.player import Player


def create_test_game_with_boards(client: TestClient) -> tuple[str, str]:
    """Helper to create a test game with boards set up.

    Returns:
        Tuple of (game_id, player_id)
    """
    # Create a player
    response: Response = client.post(
        "/login", data={"player_name": "TestPlayer", "game_mode": "computer"}
    )
    assert response.status_code == status.HTTP_200_OK

    # Place ships randomly
    response = client.post("/random-ship-placement", data={"player_name": "TestPlayer"})
    assert response.status_code == status.HTTP_200_OK

    # Start the game
    response = client.post(
        "/start-game",
        data={"action": "launch_game", "player_name": "TestPlayer"},
        follow_redirects=False,
    )
    assert response.status_code == status.HTTP_303_SEE_OTHER

    # Extract game_id from redirect URL
    redirect_url: str = response.headers["location"]
    game_id: str = redirect_url.split("/")[-1]

    # Get player_id from session
    session_cookie_value: str | None = response.cookies.get("session")
    assert session_cookie_value is not None

    # Import game_service to get player_id
    from main import game_service

    game: Game | None = game_service.games.get(game_id)
    assert game is not None
    player_id: str = game.player_1.id

    return game_id, player_id


class TestAimShotEndpoint:
    """Tests for POST /game/{game_id}/aim-shot endpoint."""

    def test_aim_shot_endpoint_success(self, client: TestClient) -> None:
        """Test successfully aiming a shot."""
        # Arrange
        game_id, player_id = create_test_game_with_boards(client)

        # Act
        response: Response = client.post(
            f"/game/{game_id}/aim-shot", data={"coord": "A1"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        # Verify state via GET endpoint
        state_response: Response = client.get(f"/game/{game_id}/aimed-shots")
        assert state_response.status_code == status.HTTP_200_OK
        data: dict[str, Any] = state_response.json()

        assert data["count"] == 1
        assert data["shots_available"] == 6  # All 5 ships unsunk (2+1+1+1+1)
        assert "A1" in data["coords"]

    def test_aim_shot_endpoint_multiple_shots(self, client: TestClient) -> None:
        """Test aiming multiple shots in sequence."""
        # Arrange
        game_id, player_id = create_test_game_with_boards(client)

        # Act - aim 3 shots
        response1: Response = client.post(
            f"/game/{game_id}/aim-shot", data={"coord": "A1"}
        )
        response2: Response = client.post(
            f"/game/{game_id}/aim-shot", data={"coord": "B2"}
        )
        response3: Response = client.post(
            f"/game/{game_id}/aim-shot", data={"coord": "C3"}
        )

        # Assert
        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        assert response3.status_code == status.HTTP_200_OK

        # Verify final state
        state_response: Response = client.get(f"/game/{game_id}/aimed-shots")
        data: dict[str, Any] = state_response.json()
        assert data["count"] == 3
        assert set(data["coords"]) == {"A1", "B2", "C3"}

    def test_aim_shot_endpoint_duplicate(self, client: TestClient) -> None:
        """Test that aiming at the same coordinate twice returns error."""
        # Arrange
        game_id, player_id = create_test_game_with_boards(client)

        # Aim at A1 first time
        response1: Response = client.post(
            f"/game/{game_id}/aim-shot", data={"coord": "A1"}
        )
        assert response1.status_code == status.HTTP_200_OK

        # Act - aim at A1 again
        response2: Response = client.post(
            f"/game/{game_id}/aim-shot", data={"coord": "A1"}
        )

        # Assert - returns 200 OK with error message in HTML
        assert response2.status_code == status.HTTP_200_OK
        assert "already selected" in response2.text.lower()

    def test_aim_shot_endpoint_exceeds_limit(self, client: TestClient) -> None:
        """Test that aiming more shots than available returns error."""
        # Arrange
        game_id, player_id = create_test_game_with_boards(client)

        # Aim 6 shots (the limit with all ships unsunk)
        coords: list[str] = ["A1", "B2", "C3", "D4", "E5", "F6"]
        for coord in coords:
            response: Response = client.post(
                f"/game/{game_id}/aim-shot", data={"coord": coord}
            )
            assert response.status_code == status.HTTP_200_OK

        # Act - try to aim a 7th shot
        response: Response = client.post(
            f"/game/{game_id}/aim-shot", data={"coord": "G7"}
        )

        # Assert - returns 200 OK with error message in HTML
        assert response.status_code == status.HTTP_200_OK
        assert "limit" in response.text.lower()

    def test_aim_shot_endpoint_invalid_coord(self, client: TestClient) -> None:
        """Test that invalid coordinate format returns error."""
        # Arrange
        game_id, player_id = create_test_game_with_boards(client)

        # Act
        response: Response = client.post(
            f"/game/{game_id}/aim-shot", data={"coord": "INVALID"}
        )

        # Assert - returns 200 OK with error message in HTML
        assert response.status_code == status.HTTP_200_OK
        assert "invalid coordinate" in response.text.lower()


class TestGetAimedShotsEndpoint:
    """Tests for GET /game/{game_id}/aimed-shots endpoint."""

    def test_get_aimed_shots_endpoint_empty(self, client: TestClient) -> None:
        """Test getting aimed shots when none have been aimed."""
        # Arrange
        game_id, player_id = create_test_game_with_boards(client)

        # Act
        response: Response = client.get(f"/game/{game_id}/aimed-shots")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data: dict[str, Any] = response.json()
        assert data["coords"] == []
        assert data["count"] == 0
        assert data["shots_available"] == 6

    def test_get_aimed_shots_endpoint_with_shots(self, client: TestClient) -> None:
        """Test getting aimed shots after aiming several."""
        # Arrange
        game_id, player_id = create_test_game_with_boards(client)

        # Aim at A1, B2, C3
        coords: list[str] = ["A1", "B2", "C3"]
        for coord in coords:
            client.post(f"/game/{game_id}/aim-shot", data={"coord": coord})

        # Act
        response: Response = client.get(f"/game/{game_id}/aimed-shots")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data: dict[str, Any] = response.json()
        assert set(data["coords"]) == set(coords)
        assert data["count"] == 3
        assert data["shots_available"] == 6


class TestClearAimedShotEndpoint:
    """Tests for DELETE /game/{game_id}/aim-shot/{coord} endpoint."""

    def test_clear_aimed_shot_endpoint_success(self, client: TestClient) -> None:
        """Test successfully removing an aimed shot."""
        # Arrange
        game_id, player_id = create_test_game_with_boards(client)

        # Aim at A1 and B2
        client.post(f"/game/{game_id}/aim-shot", data={"coord": "A1"})
        client.post(f"/game/{game_id}/aim-shot", data={"coord": "B2"})

        # Act - remove A1
        response: Response = client.delete(f"/game/{game_id}/aim-shot/A1")

        # Assert
        assert response.status_code == status.HTTP_200_OK

        # Verify state via GET endpoint
        state_response: Response = client.get(f"/game/{game_id}/aimed-shots")
        data: dict[str, Any] = state_response.json()
        assert data["count"] == 1
        assert "A1" not in data["coords"]
        assert "B2" in data["coords"]

    def test_clear_aimed_shot_endpoint_verify_removal(self, client: TestClient) -> None:
        """Test that removed shot is no longer in aimed shots list."""
        # Arrange
        game_id, player_id = create_test_game_with_boards(client)

        # Aim at A1, B2, C3
        client.post(f"/game/{game_id}/aim-shot", data={"coord": "A1"})
        client.post(f"/game/{game_id}/aim-shot", data={"coord": "B2"})
        client.post(f"/game/{game_id}/aim-shot", data={"coord": "C3"})

        # Act - remove B2
        client.delete(f"/game/{game_id}/aim-shot/B2")

        # Verify
        response: Response = client.get(f"/game/{game_id}/aimed-shots")
        data: dict[str, Any] = response.json()
        assert set(data["coords"]) == {"A1", "C3"}
        assert data["count"] == 2

    def test_clear_aimed_shot_endpoint_not_aimed(self, client: TestClient) -> None:
        """Test removing a shot that wasn't aimed."""
        # Arrange
        game_id, player_id = create_test_game_with_boards(client)

        # Aim at A1 only
        client.post(f"/game/{game_id}/aim-shot", data={"coord": "A1"})

        # Act - try to remove B2 (not aimed)
        response: Response = client.delete(f"/game/{game_id}/aim-shot/B2")

        # Assert - should succeed but have no effect
        assert response.status_code == status.HTTP_200_OK

        # Verify state
        state_response: Response = client.get(f"/game/{game_id}/aimed-shots")
        data: dict[str, Any] = state_response.json()
        assert data["count"] == 1
        assert "A1" in data["coords"]

    def test_clear_aimed_shot_endpoint_invalid_coord(self, client: TestClient) -> None:
        """Test that invalid coordinate format returns error."""
        # Arrange
        game_id, player_id = create_test_game_with_boards(client)

        # Act
        response: Response = client.delete(f"/game/{game_id}/aim-shot/INVALID")

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
