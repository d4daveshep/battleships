import pytest
import time
import threading
from bs4 import BeautifulSoup
from fastapi import status
from fastapi.testclient import TestClient
from httpx import Response
from helpers import decode_session


class TestMultiplayerShipPlacement:
    """Test suite for multiplayer ship placement endpoints"""

    @pytest.fixture
    def players_in_placement(
        self, game_paired: tuple[TestClient, TestClient]
    ) -> tuple[TestClient, TestClient]:
        """Fixture to put Alice and Bob in ship placement screen"""
        alice_client, bob_client = game_paired

        # Move Alice to placement
        alice_client.post("/start-game", data={"action": "start_game"})

        # Move Bob to placement
        bob_client.post("/start-game", data={"action": "start_game"})

        return alice_client, bob_client

    def test_initial_opponent_status(
        self, players_in_placement: tuple[TestClient, TestClient]
    ):
        """Test that initial opponent status is 'placing ships'"""
        alice_client, bob_client = players_in_placement

        # Check Alice's view of Bob
        response = alice_client.get("/place-ships/opponent-status")
        assert response.status_code == status.HTTP_200_OK

        soup = BeautifulSoup(response.text, "html.parser")
        status_text = soup.get_text()
        assert "Opponent is placing ships" in status_text
        assert "Opponent is ready" not in status_text

    def test_opponent_status_updates_when_ready(
        self, players_in_placement: tuple[TestClient, TestClient]
    ):
        """Test that status updates when opponent becomes ready"""
        alice_client, bob_client = players_in_placement

        # Bob places ships and clicks ready
        # We need to place ships first. Since we don't have a helper for placing all ships easily,
        # we can mock the ready state or place ships manually.
        # But wait, ready_for_game checks if ships are placed?
        # The endpoint implementation in main.py:
        # validated_player_name = _get_validated_player_name(request, player_name)
        # player_id = _get_player_id(request)
        # game_service.set_player_ready(player_id)
        # It doesn't seem to validate ship placement in the endpoint itself (it assumes frontend did it or service handles it).
        # Let's check game_service.set_player_ready implementation if possible, but for endpoint test,
        # we can try calling ready-for-game directly.

        bob_client.post("/ready-for-game", data={"player_name": "Bob"})

        # Check Alice's view of Bob
        response = alice_client.get("/place-ships/opponent-status")
        assert response.status_code == status.HTTP_200_OK

        soup = BeautifulSoup(response.text, "html.parser")
        status_text = soup.get_text()
        assert "Opponent is ready" in status_text

    def test_long_poll_returns_immediately_on_version_mismatch(
        self, players_in_placement: tuple[TestClient, TestClient]
    ):
        """Test that long poll returns immediately if version is different"""
        alice_client, bob_client = players_in_placement

        # Get current status to find version (though we can't easily see version in HTML without parsing)
        # But we can pass a dummy version

        start_time = time.time()
        response = alice_client.get(
            "/place-ships/opponent-status/long-poll?version=999999&timeout=5"
        )
        duration = time.time() - start_time

        assert response.status_code == status.HTTP_200_OK
        assert duration < 1.0  # Should be immediate

    def test_long_poll_waits_for_timeout(
        self, players_in_placement: tuple[TestClient, TestClient]
    ):
        """Test that long poll waits if version matches (and no change occurs)"""
        alice_client, bob_client = players_in_placement

        # We need the current version.
        # The opponent status component includes the version in the hx-get URL or a hidden field?
        # Let's check the component template or response.
        # main.py: _render_opponent_status passes "version": version
        # It renders components/opponent_status.html

        response = alice_client.get("/place-ships/opponent-status")
        soup = BeautifulSoup(response.text, "html.parser")
        # Find the hx-get attribute which contains the version
        # <div hx-get="/place-ships/opponent-status/long-poll?version={{ version }}" ...>
        div = soup.find("div", attrs={"hx-get": True})
        if not div:
            # Maybe it's on the root element of the component
            # If the response IS the component
            if soup.find("div", attrs={"hx-trigger": "load"}):
                div = soup.find("div", attrs={"hx-trigger": "load"})

        # If we can't find it easily, we can try to guess or just use 0 if it starts at 0.
        # But better to parse it.
        # Let's assume we can find it.

        # If we can't parse it, we can't test the "wait" part reliably without knowing the current version.
        # However, we can try to fetch it.

        # Let's try to find the version from the response text if possible.
        # The template uses: hx-get="/place-ships/opponent-status/long-poll?version={{ version }}"
        import re

        match = re.search(r"version=(\d+)", response.text)
        if match:
            version = match.group(1)

            start_time = time.time()
            # Use a short timeout for test
            response = alice_client.get(
                f"/place-ships/opponent-status/long-poll?version={version}&timeout=2"
            )
            duration = time.time() - start_time

            assert response.status_code == status.HTTP_200_OK
            assert duration >= 1.5  # Should wait at least close to 2 seconds
        else:
            pytest.fail("Could not extract version from opponent status component")

    def test_game_starts_when_both_ready(
        self, players_in_placement: tuple[TestClient, TestClient]
    ):
        """Test that game is created when both players are ready"""
        alice_client, bob_client = players_in_placement

        # Alice becomes ready
        alice_response = alice_client.post(
            "/ready-for-game", data={"player_name": "Alice"}, follow_redirects=False
        )
        # Alice should see "Waiting for opponent" (which is the ship placement page with is_ready=True)
        assert alice_response.status_code == status.HTTP_200_OK
        assert "Waiting for opponent" in alice_response.text

        # Bob becomes ready
        bob_response = bob_client.post(
            "/ready-for-game", data={"player_name": "Bob"}, follow_redirects=False
        )

        # Bob should be redirected to game
        assert bob_response.status_code == status.HTTP_303_SEE_OTHER
        assert "/game/" in bob_response.headers["location"]

        # Alice should also be redirected if she polls or refreshes,
        # but here we just check that the game exists.
        # We can check if Alice is redirected when she checks status
        alice_status_response = alice_client.get(
            "/place-ships/opponent-status", headers={"HX-Request": "true"}
        )
        assert alice_status_response.status_code == status.HTTP_204_NO_CONTENT
        assert "/game/" in alice_status_response.headers["HX-Redirect"]

    def test_leave_placement_redirects_to_lobby(
        self, players_in_placement: tuple[TestClient, TestClient]
    ):
        """Test that leaving placement redirects to lobby"""
        alice_client, bob_client = players_in_placement

        response = alice_client.post("/leave-placement", follow_redirects=False)

        assert response.status_code == status.HTTP_303_SEE_OTHER
        assert response.headers["location"] == "/lobby"

    def test_opponent_left_status(
        self, players_in_placement: tuple[TestClient, TestClient]
    ):
        """Test that opponent leaving updates status"""
        alice_client, bob_client = players_in_placement

        # Bob leaves
        bob_client.post("/leave-placement")

        # Alice checks status
        response = alice_client.get("/place-ships/opponent-status")

        assert response.status_code == status.HTTP_200_OK
        soup = BeautifulSoup(response.text, "html.parser")
        assert (
            "Opponent has left" in soup.get_text() or "left the game" in soup.get_text()
        )
