"""Endpoint tests for shot firing functionality."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient


def _create_game_with_ships(client: TestClient, player_name: str) -> str:
    """Helper to create a game with ships placed - returns game_id"""
    create_response = client.post(
        "/start-game",
        data={"action": "launch_game", "player_name": player_name},
        follow_redirects=False,
    )
    game_url = create_response.headers["location"]
    game_id = game_url.split("/")[-1]

    client.post(
        "/random-ship-placement",
        data={"player_name": player_name},
    )

    return game_id


@pytest.fixture
def game_with_ships(authenticated_client: TestClient) -> str:
    """Create a game with ships placed for testing"""
    # Use "Alice" to match the authenticated_client session
    return _create_game_with_ships(authenticated_client, "Alice")


class TestFireShotsEndpoint:
    """Tests for POST /fire-shots endpoint"""

    def test_fire_shots_endpoint_exists(
        self, authenticated_client: TestClient, game_with_ships: str
    ) -> None:
        """Test that the /fire-shots endpoint exists and accepts POST"""
        # Aim at one coordinate first
        authenticated_client.post(
            "/aim-shot",
            data={"game_id": game_with_ships, "coordinate": "A1"},
            headers={"HX-Request": "true"},
        )

        # Fire shots should return 200 (not 404)
        response = authenticated_client.post(
            "/fire-shots",
            data={"game_id": game_with_ships, "player_name": "Alice"},
        )
        assert response.status_code != status.HTTP_404_NOT_FOUND

    def test_fire_shots_submits_aimed_shots(
        self, authenticated_client: TestClient, game_with_ships: str
    ) -> None:
        """Test that firing shots submits the 4 aimed shots."""
        # Aim at 4 coordinates
        for coord in ["A1", "B2", "C3", "D4"]:
            authenticated_client.post(
                "/aim-shot",
                data={"game_id": game_with_ships, "coordinate": coord},
                headers={"HX-Request": "true"},
            )

        # Fire the shots
        response = authenticated_client.post(
            "/fire-shots",
            data={"game_id": game_with_ships, "player_name": "Alice"},
        )

        assert response.status_code == status.HTTP_200_OK
        # Should see waiting message in response
        assert "Waiting for opponent" in response.text

    def test_fire_shots_with_fewer_than_available(
        self, authenticated_client: TestClient, game_with_ships: str
    ) -> None:
        """Test that firing fewer shots than available is allowed."""
        # Aim at only 4 coordinates (out of 6 available)
        for coord in ["A1", "B2", "C3", "D4"]:
            authenticated_client.post(
                "/aim-shot",
                data={"game_id": game_with_ships, "coordinate": coord},
                headers={"HX-Request": "true"},
            )

        response = authenticated_client.post(
            "/fire-shots",
            data={"game_id": game_with_ships, "player_name": "Alice"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert "Waiting for opponent" in response.text

    def test_cannot_aim_after_firing(
        self, authenticated_client: TestClient, game_with_ships: str
    ) -> None:
        """Test that aiming is blocked after firing shots."""
        # Aim at one shot
        authenticated_client.post(
            "/aim-shot",
            data={"game_id": game_with_ships, "coordinate": "A1"},
            headers={"HX-Request": "true"},
        )

        # Fire the shots
        fire_response = authenticated_client.post(
            "/fire-shots",
            data={"game_id": game_with_ships, "player_name": "Alice"},
        )
        assert fire_response.status_code == status.HTTP_200_OK

        # Attempt to aim another shot - should get an error message
        htmx_response = authenticated_client.post(
            "/aim-shot",
            data={"game_id": game_with_ships, "coordinate": "E5"},
            headers={"HX-Request": "true"},
        )

        assert htmx_response.status_code == status.HTTP_200_OK
        assert "Cannot aim shots after firing" in htmx_response.text

    def test_fire_shots_with_no_aimed_shots_shows_error(
        self, authenticated_client: TestClient, game_with_ships: str
    ) -> None:
        """Test that firing with no aimed shots shows an error."""
        response = authenticated_client.post(
            "/fire-shots",
            data={"game_id": game_with_ships, "player_name": "Alice"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert "Cannot fire shots" in response.text
