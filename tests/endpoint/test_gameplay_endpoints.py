"""Integration tests for gameplay endpoints - aiming shots during gameplay."""

import asyncio
import time
from typing import Any

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from httpx import Response

from game.model import Coord, GameBoard, Orientation, Ship, ShipType
from game.game_service import Game, GameMode
from game.player import Player
from main import app


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


def create_two_player_game_with_boards(
    player_client: TestClient, opponent_client: TestClient
) -> dict[str, str]:
    """Helper to create a two-player game with boards set up.

    Args:
        player_client: TestClient for player 1
        opponent_client: TestClient for player 2

    Returns:
        Dict with keys: game_id, player_id, opponent_id, player_name, opponent_name
    """
    from main import game_service

    player_name: str = "Player1"
    opponent_name: str = "Player2"

    # Reset lobby/game state
    player_client.post("/test/reset-lobby")

    # Login both players
    player_client.post(
        "/login", data={"player_name": player_name, "game_mode": "human"}
    )
    opponent_client.post(
        "/login", data={"player_name": opponent_name, "game_mode": "human"}
    )

    # Get player IDs from game_service
    player_id: str | None = None
    opponent_id: str | None = None
    for player in game_service.players.values():
        if player.name == player_name:
            player_id = player.id
        elif player.name == opponent_name:
            opponent_id = player.id

    assert player_id is not None
    assert opponent_id is not None

    # Match players
    player_client.post("/select-opponent", data={"opponent_name": opponent_name})
    opponent_client.post("/accept-game-request", data={})

    # Navigate to ship placement
    resp1: Response = player_client.get(f"/lobby/status/{player_name}")
    if resp1.status_code in [302, 303]:
        player_client.get(resp1.headers["location"])

    resp2: Response = opponent_client.get(f"/lobby/status/{opponent_name}")
    if resp2.status_code in [302, 303]:
        opponent_client.get(resp2.headers["location"])

    # Start game for both players
    resp1_start: Response = player_client.post(
        "/start-game", data={"action": "start_game", "player_name": player_name}
    )
    if resp1_start.status_code in [302, 303]:
        player_client.get(resp1_start.headers["location"])

    resp2_start: Response = opponent_client.post(
        "/start-game", data={"action": "start_game", "player_name": opponent_name}
    )
    if resp2_start.status_code in [302, 303]:
        opponent_client.get(resp2_start.headers["location"])

    # Place ships for both players (using default positions)
    ships_to_place: list[tuple[str, str, str]] = [
        ("Carrier", "A1", "horizontal"),  # A1-A5
        ("Battleship", "C1", "horizontal"),  # C1-C4 (skipping B row)
        ("Cruiser", "E1", "horizontal"),  # E1-E3 (skipping D row)
        ("Submarine", "G1", "horizontal"),  # G1-G3 (skipping F row)
        ("Destroyer", "I1", "horizontal"),  # I1-I2 (skipping H row)
    ]

    for ship_name, start_coordinate, orientation in ships_to_place:
        player_client.post(
            "/place-ship",
            data={
                "player_name": player_name,
                "ship_name": ship_name,
                "start_coordinate": start_coordinate,
                "orientation": orientation,
            },
        )
        opponent_client.post(
            "/place-ship",
            data={
                "player_name": opponent_name,
                "ship_name": ship_name,
                "start_coordinate": start_coordinate,
                "orientation": orientation,
            },
        )

    # Mark both players as ready
    player_client.post("/ready-for-game", data={"player_name": player_name})
    resp_ready: Response = opponent_client.post(
        "/ready-for-game", data={"player_name": opponent_name}
    )

    # Extract game_id from redirect
    game_id: str | None = None
    if resp_ready.status_code in [302, 303]:
        redirect_url: str = resp_ready.headers["location"]
        if "/game/" in redirect_url:
            game_id = redirect_url.split("/game/")[1].split("/")[0].split("?")[0]

    assert game_id is not None

    # Navigate to game page for both players
    player_client.get(f"/game/{game_id}")
    opponent_client.get(f"/game/{game_id}")

    return {
        "game_id": game_id,
        "player_id": player_id,
        "opponent_id": opponent_id,
        "player_name": player_name,
        "opponent_name": opponent_name,
    }


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


class TestFireShotsEndpoint:
    """Tests for POST /game/{game_id}/fire-shots endpoint."""

    def test_fire_shots_endpoint_first_player_waits(self, client: TestClient) -> None:
        """Test that first player to fire enters waiting state."""
        # Arrange
        game_id, player_id = create_test_game_with_boards(client)

        # Aim some shots
        client.post(f"/game/{game_id}/aim-shot", data={"coord": "A1"})
        client.post(f"/game/{game_id}/aim-shot", data={"coord": "B2"})

        # Act - fire shots
        response: Response = client.post(f"/game/{game_id}/fire-shots")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "waiting" in response.text.lower()

    def test_fire_shots_waiting_state_has_polling_attributes(
        self, client: TestClient
    ) -> None:
        """Test that waiting state includes HTMX polling attributes."""
        # Arrange
        game_id, player_id = create_test_game_with_boards(client)

        # Aim some shots
        client.post(f"/game/{game_id}/aim-shot", data={"coord": "A1"})
        client.post(f"/game/{game_id}/aim-shot", data={"coord": "B2"})

        # Act - fire shots to enter waiting state
        response: Response = client.post(f"/game/{game_id}/fire-shots")

        # Assert - verify HTMX long-polling attributes are present
        assert response.status_code == status.HTTP_200_OK
        assert 'hx-get="/game/' in response.text
        # Long-polling uses "load delay:100ms" instead of "every 2s" for better UX
        assert 'hx-trigger="load delay:100ms"' in response.text
        # Swap uses innerHTML with target to avoid duplicate ID issues
        assert 'hx-swap="innerHTML' in response.text
        assert 'hx-target="#aiming-interface"' in response.text

    def test_fire_shots_endpoint_no_shots_aimed(self, client: TestClient) -> None:
        """Test that firing without aiming returns error."""
        # Arrange
        game_id, player_id = create_test_game_with_boards(client)

        # Act - try to fire without aiming
        response: Response = client.post(f"/game/{game_id}/fire-shots")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "no shots" in response.text.lower()

    def test_fire_shots_endpoint_already_submitted(self, client: TestClient) -> None:
        """Test that firing twice returns error."""
        # Arrange
        game_id, player_id = create_test_game_with_boards(client)

        # Aim and fire
        client.post(f"/game/{game_id}/aim-shot", data={"coord": "A1"})
        client.post(f"/game/{game_id}/fire-shots")

        # Act - try to fire again
        response: Response = client.post(f"/game/{game_id}/fire-shots")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert (
            "already" in response.text.lower() or "submitted" in response.text.lower()
        )

    def test_fire_shots_endpoint_round_resolution(
        self, game_paired: tuple[TestClient, TestClient]
    ) -> None:
        """Test that round is resolved when both players fire (multiplayer scenario)."""
        # Arrange - Setup a multiplayer game
        alice_client, bob_client = game_paired

        # Both players start the game
        alice_client.post("/start-game", data={"action": "start_game"})
        bob_client.post("/start-game", data={"action": "start_game"})

        # Both players place ships randomly
        alice_client.post("/random-ship-placement", data={"player_name": "Alice"})
        bob_client.post("/random-ship-placement", data={"player_name": "Bob"})

        # Both players ready up
        alice_client.post(
            "/ready-for-game", data={"player_name": "Alice"}, follow_redirects=False
        )
        bob_ready_resp = bob_client.post(
            "/ready-for-game", data={"player_name": "Bob"}, follow_redirects=False
        )

        # Extract game_id from Bob's redirect
        assert bob_ready_resp.status_code == status.HTTP_303_SEE_OTHER
        game_id: str = bob_ready_resp.headers["location"].split("/")[-1]

        # Alice aims and fires first
        alice_client.post(f"/game/{game_id}/aim-shot", data={"coord": "A1"})
        alice_client.post(f"/game/{game_id}/aim-shot", data={"coord": "A2"})
        alice_fire_resp = alice_client.post(f"/game/{game_id}/fire-shots")

        # Assert - Alice should be in waiting state
        assert alice_fire_resp.status_code == status.HTTP_200_OK
        assert "waiting" in alice_fire_resp.text.lower()

        # Act - Bob aims and fires (should trigger round resolution)
        bob_client.post(f"/game/{game_id}/aim-shot", data={"coord": "B1"})
        bob_client.post(f"/game/{game_id}/aim-shot", data={"coord": "B2"})
        bob_fire_resp = bob_client.post(f"/game/{game_id}/fire-shots")

        # Assert - Bob should see round results (round resolved)
        assert bob_fire_resp.status_code == status.HTTP_200_OK
        assert "Round" in bob_fire_resp.text
        # Should not be in waiting state since round is resolved
        assert "round-results" in bob_fire_resp.text or "Continue" in bob_fire_resp.text


class TestGetAimingInterfacePolling:
    """Tests for GET /game/{game_id}/aiming-interface endpoint polling behavior."""

    def test_polling_returns_waiting_message_when_player_submitted(
        self, client: TestClient
    ) -> None:
        """Test that polling returns waiting message when player has submitted but round not resolved."""
        # Arrange
        game_id, player_id = create_test_game_with_boards(client)

        # Aim and fire shots
        client.post(f"/game/{game_id}/aim-shot", data={"coord": "A1"})
        client.post(f"/game/{game_id}/aim-shot", data={"coord": "B2"})
        client.post(f"/game/{game_id}/fire-shots")

        # Act - poll the aiming interface
        response: Response = client.get(f"/game/{game_id}/aiming-interface")

        # Assert - should still show waiting message with long-polling
        assert response.status_code == status.HTTP_200_OK
        assert "waiting" in response.text.lower()
        # Long-polling uses "load delay:100ms" instead of "every 2s"
        assert 'hx-trigger="load delay:100ms"' in response.text

    def test_polling_returns_aiming_interface_when_no_submission(
        self, client: TestClient
    ) -> None:
        """Test that polling returns normal aiming interface when player hasn't submitted."""
        # Arrange
        game_id, player_id = create_test_game_with_boards(client)

        # Act - poll the aiming interface without firing
        response: Response = client.get(f"/game/{game_id}/aiming-interface")

        # Assert - should show normal aiming interface
        assert response.status_code == status.HTTP_200_OK
        assert "waiting" not in response.text.lower()
        assert (
            "Select Target Coordinates" in response.text
            or "shots-fired-board" in response.text
        )

    def test_polling_returns_round_results_after_both_players_fire(
        self, game_paired: tuple[TestClient, TestClient]
    ) -> None:
        """Test that polling returns round results when round is resolved (multiplayer)."""
        # Arrange - Get Alice and Bob paired and ready to play
        alice_client, bob_client = game_paired

        # Both players start the game
        alice_client.post("/start-game", data={"action": "start_game"})
        bob_client.post("/start-game", data={"action": "start_game"})

        # Both players place ships randomly
        alice_client.post("/random-ship-placement", data={"player_name": "Alice"})
        bob_client.post("/random-ship-placement", data={"player_name": "Bob"})

        # Alice readies first (gets 200 OK - waiting for Bob)
        alice_ready_resp = alice_client.post(
            "/ready-for-game", data={"player_name": "Alice"}, follow_redirects=False
        )
        assert alice_ready_resp.status_code == status.HTTP_200_OK

        # Bob readies second (gets 303 redirect - game starts)
        bob_ready_resp = bob_client.post(
            "/ready-for-game", data={"player_name": "Bob"}, follow_redirects=False
        )
        assert bob_ready_resp.status_code == status.HTTP_303_SEE_OTHER
        game_id: str = bob_ready_resp.headers["location"].split("/")[-1]

        # Alice fires first (should enter waiting state)
        alice_client.post(f"/game/{game_id}/aim-shot", data={"coord": "A1"})
        alice_client.post(f"/game/{game_id}/aim-shot", data={"coord": "A2"})
        alice_fire_resp = alice_client.post(f"/game/{game_id}/fire-shots")

        # Verify Alice is waiting
        assert alice_fire_resp.status_code == status.HTTP_200_OK
        assert "waiting" in alice_fire_resp.text.lower()

        # Alice polls while waiting (should still show waiting)
        alice_poll_resp1 = alice_client.get(f"/game/{game_id}/aiming-interface")
        assert alice_poll_resp1.status_code == status.HTTP_200_OK
        assert "waiting" in alice_poll_resp1.text.lower()

        # Bob fires (should resolve the round)
        bob_client.post(f"/game/{game_id}/aim-shot", data={"coord": "B1"})
        bob_client.post(f"/game/{game_id}/aim-shot", data={"coord": "B2"})
        bob_fire_resp = bob_client.post(f"/game/{game_id}/fire-shots")

        # Bob should see round results immediately
        assert bob_fire_resp.status_code == status.HTTP_200_OK
        assert "Round" in bob_fire_resp.text

        # Act - Alice polls again (should now get round results)
        alice_poll_resp2 = alice_client.get(f"/game/{game_id}/aiming-interface")

        # Assert - Alice should see round results
        assert alice_poll_resp2.status_code == status.HTTP_200_OK
        assert "Round" in alice_poll_resp2.text
        assert "waiting" not in alice_poll_resp2.text.lower()
        # Should have round results component
        assert (
            "round-results" in alice_poll_resp2.text
            or "Continue" in alice_poll_resp2.text
        )


class TestLongPollingEndpoint:
    """Tests for the /game/{game_id}/long-poll endpoint with proper async waiting."""

    def test_long_poll_endpoint_exists_and_accepts_parameters(
        self, client: TestClient
    ) -> None:
        """Test that long-poll endpoint exists and accepts version/timeout parameters."""
        # Arrange
        game_id, player_id = create_test_game_with_boards(client)

        from main import gameplay_service

        # Get current version
        current_version = gameplay_service.get_round_version(game_id)

        # Act - call long-poll with version parameter
        response = client.get(
            f"/game/{game_id}/long-poll?version={current_version}&timeout=1"
        )

        # Assert - should return successfully (will timeout after 1 second)
        assert response.status_code == status.HTTP_200_OK
        # Should return some game state (aiming interface or results)
        assert len(response.text) > 0

    def test_long_poll_returns_immediately_if_version_behind(
        self, client: TestClient
    ) -> None:
        """Test that long-poll returns immediately if client version is behind server."""
        # Arrange
        game_id, player_id = create_test_game_with_boards(client)

        from main import gameplay_service
        import time

        # Trigger a version change
        gameplay_service._notify_round_change(game_id)
        current_version = gameplay_service.get_round_version(game_id)

        # Act - long-poll with old version (should return immediately)
        start_time = time.time()
        response = client.get(
            f"/game/{game_id}/long-poll?version={current_version - 1}&timeout=5"
        )
        elapsed = time.time() - start_time

        # Assert - should return quickly (not wait for timeout)
        assert elapsed < 1.0  # Should be nearly instant
        assert response.status_code == status.HTTP_200_OK

    def test_long_poll_returns_aiming_interface_when_no_change(
        self, client: TestClient
    ) -> None:
        """Test that long-poll returns aiming interface when no round change occurs."""
        # Arrange
        game_id, player_id = create_test_game_with_boards(client)

        from main import gameplay_service

        # Get current version
        current_version = gameplay_service.get_round_version(game_id)

        # Act - long-poll with current version and short timeout
        response = client.get(
            f"/game/{game_id}/long-poll?version={current_version}&timeout=1"
        )

        # Assert - should return aiming interface (no change occurred)
        assert response.status_code == status.HTTP_200_OK
        html = response.text

        # Should contain aiming interface elements
        assert (
            'data-testid="aiming-interface"' in html
            or 'data-testid="shot-counter"' in html
        )

    def test_aiming_interface_template_includes_long_poll_attributes(
        self, client: TestClient
    ) -> None:
        """Test that aiming interface template includes long-poll HTMX attributes when waiting."""
        # Arrange
        game_id, player_id = create_test_game_with_boards(client)

        from main import _render_aiming_interface, gameplay_service
        from starlette.requests import Request

        # Create a mock request
        scope = {
            "type": "http",
            "method": "GET",
            "headers": [],
            "query_string": b"",
            "path": f"/game/{game_id}/aiming-interface",
        }
        request = Request(scope)

        # Get current version
        current_version = gameplay_service.get_round_version(game_id)

        # Act - render aiming interface with waiting message
        response = _render_aiming_interface(
            request,
            game_id,
            player_id,
            waiting_message="Waiting for opponent to fire...",
        )

        # Assert - should include HTMX long-poll attributes
        # HTMLResponse has a body attribute that's bytes
        html = (
            response.body.decode("utf-8")
            if isinstance(response.body, bytes)
            else str(response.body)
        )

        # Check for waiting message
        assert "Waiting for opponent" in html

        # Check for long-poll HTMX attributes
        assert "hx-get" in html
        assert f"/game/{game_id}/long-poll" in html
        assert f"version={current_version}" in html
        assert 'hx-trigger="load' in html

    @pytest.mark.asyncio
    async def test_long_poll_waits_for_round_resolution(
        self, client: TestClient
    ) -> None:
        """Test that long-poll waits for round to resolve when versions match.

        This test verifies the async waiting mechanism works correctly by:
        1. Setting up a two-player game
        2. Having player 1 fire shots (now waiting for opponent)
        3. Simulating a long-poll request that waits for round resolution
        4. Having player 2 fire shots (triggers round resolution)
        5. Verifying the long-poll returns with round results
        """
        # Arrange - create two-player game
        player_client: TestClient = TestClient(app, follow_redirects=False)
        opponent_client: TestClient = TestClient(app, follow_redirects=False)

        game_info: dict[str, str] = create_two_player_game_with_boards(
            player_client, opponent_client
        )
        game_id: str = game_info["game_id"]

        from main import gameplay_service

        # Get current round version
        current_version: int = gameplay_service.get_round_version(game_id)

        # Player aims and fires shots
        player_client.post(f"/game/{game_id}/aim-shot", data={"coord": "A1"})
        player_client.post(f"/game/{game_id}/fire-shots", data={})

        # Player is now waiting for opponent - version should be same
        assert gameplay_service.get_round_version(game_id) == current_version

        # Start long-poll in background using run_in_executor
        async def long_poll_request() -> Response:
            """Run sync TestClient request in executor to avoid blocking"""
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                lambda: player_client.get(
                    f"/game/{game_id}/long-poll?version={current_version}&timeout=10"
                ),
            )

        # Start the long-poll task
        long_poll_task = asyncio.create_task(long_poll_request())

        # Give long-poll time to start waiting (important for async event setup)
        await asyncio.sleep(0.2)

        # Opponent fires shots in executor (to avoid blocking the event loop)
        async def opponent_fires() -> None:
            """Run opponent actions in executor"""
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: opponent_client.post(
                    f"/game/{game_id}/aim-shot", data={"coord": "A1"}
                ),
            )
            await loop.run_in_executor(
                None,
                lambda: opponent_client.post(f"/game/{game_id}/fire-shots", data={}),
            )

        # Fire opponent shots
        await opponent_fires()

        # Wait for long-poll to complete (with generous timeout)
        response: Response = await asyncio.wait_for(long_poll_task, timeout=12.0)

        # Assert - response should be successful
        assert response.status_code == status.HTTP_200_OK

        # Version should have incremented
        new_version: int = gameplay_service.get_round_version(game_id)
        assert new_version > current_version

        # Response should contain round results
        html: str = response.text
        assert (
            "Round Results" in html
            or "round-results" in html
            or 'data-testid="round-results"' in html
        )

    @pytest.mark.asyncio
    async def test_long_poll_times_out_gracefully(self, client: TestClient) -> None:
        """Test that long-poll returns after timeout even if no change occurs."""
        # Arrange - create two-player game
        player_client: TestClient = TestClient(app, follow_redirects=False)
        opponent_client: TestClient = TestClient(app, follow_redirects=False)

        game_info: dict[str, str] = create_two_player_game_with_boards(
            player_client, opponent_client
        )
        game_id: str = game_info["game_id"]

        from main import gameplay_service

        # Get current round version
        current_version: int = gameplay_service.get_round_version(game_id)

        # Player aims and fires shots
        player_client.post(f"/game/{game_id}/aim-shot", data={"coord": "A1"})
        player_client.post(f"/game/{game_id}/fire-shots", data={})

        # Player is now waiting for opponent - version should be same
        assert gameplay_service.get_round_version(game_id) == current_version

        # Act - long-poll with short timeout (opponent doesn't fire)
        start_time: float = time.time()
        response: Response = player_client.get(
            f"/game/{game_id}/long-poll?version={current_version}&timeout=2"
        )
        elapsed: float = time.time() - start_time

        # Assert - should timeout after ~2 seconds
        assert 1.8 <= elapsed <= 2.5  # Allow some variance for system timing
        assert response.status_code == status.HTTP_200_OK

        # Version should still be the same (no round resolution)
        assert gameplay_service.get_round_version(game_id) == current_version

        # Should return aiming interface with waiting message
        html: str = response.text
        assert (
            'data-testid="aiming-interface"' in html
            or 'data-testid="shot-counter"' in html
            or "Waiting for opponent" in html
        )
