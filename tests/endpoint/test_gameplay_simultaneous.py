import pytest
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from game.game_service import ShotResult, ShotStatus, Game


class TestGameplaySimultaneous:
    """Tests for simultaneous gameplay features."""

    @pytest.fixture
    def mock_game_service(self):
        with patch("routes.gameplay._get_game_service") as mock_get:
            service = MagicMock()
            mock_get.return_value = service
            yield service

    def test_fire_shot_renders_waiting_component(
        self, authenticated_client: TestClient, mock_game_service
    ):
        """
        Scenario: Player fires shots and enters waiting state.
        Expectation: Response contains the waiting component with HTMX polling.
        """
        # Mock Game Service behavior
        mock_game = MagicMock(spec=Game)
        mock_game.id = "test_game_id"
        mock_game.round = 1
        mock_game.status = "playing"  # Add this

        # Setup Players
        p1 = MagicMock()
        p1.id = "test_user_id"
        p1.name = "Alice"

        p2 = MagicMock()
        p2.id = "opponent_id"

        mock_game.player_1 = p1
        mock_game.player_2 = p2

        # Mock behavior
        mock_game.is_waiting_for_opponent.return_value = True
        mock_game.get_shots_available.return_value = 6
        mock_game.get_aimed_shots.return_value = set()

        # Mock Board
        mock_board = MagicMock()
        mock_board.get_placed_ships_for_display.return_value = {}
        mock_game.board = {p1: mock_board, p2: mock_board}

        # Setup mock_game_service to return this game
        mock_game_service.games.get.return_value = mock_game
        mock_game_service.fire_shots.return_value = ShotResult(
            ShotStatus.WAITING, mock_game
        )

        # We also need to mock _get_player_from_session
        with patch("routes.gameplay._get_player_from_session") as mock_get_player:
            mock_get_player.return_value = p1

            # Action: Fire shots
            response = authenticated_client.post(
                "/fire-shots", data={"game_id": "test_game_id", "player_name": "Alice"}
            )

            # Assertions
            assert response.status_code == 200
            # Check for HTMX polling attributes in the response HTML
            # These attributes are expected to be in the new "waiting_status.html" component
            # which we haven't created yet (RED phase).
            assert 'hx-get="/game/test_game_id/status"' in response.text
            assert 'hx-trigger="every 2s"' in response.text
            assert "Waiting for opponent" in response.text

    def test_polling_returns_updated_board(
        self, authenticated_client: TestClient, mock_game_service
    ):
        """
        Scenario: Polling checks for round update.
        """
        mock_game = MagicMock(spec=Game)
        mock_game.id = "test_game_id"
        mock_game.round = 2  # Round advanced
        mock_game.status = "playing"  # Add this

        # Setup Players
        p1 = MagicMock()

        p1.id = "test_user_id"
        p1.name = "Alice"
        p2 = MagicMock()
        p2.id = "opponent_id"

        mock_game.player_1 = p1
        mock_game.player_2 = p2

        # Mock behavior - Round resolved, so not waiting
        mock_game.is_waiting_for_opponent.return_value = False
        mock_game.get_shots_available.return_value = 6
        mock_game.get_aimed_shots.return_value = set()

        mock_board = MagicMock()
        mock_board.get_placed_ships_for_display.return_value = {}
        mock_game.board = {p1: mock_board, p2: mock_board}

        mock_game_service.games.get.return_value = mock_game

        with patch("routes.gameplay._get_player_from_session") as mock_get_player:
            mock_get_player.return_value = p1

            # Action: Poll status
            response = authenticated_client.get("/game/test_game_id/status")

            # Assertions
            assert response.status_code == 200
            assert "Round 2" in response.text
            # Should NOT have polling triggers anymore
            assert 'hx-trigger="every 2s"' not in response.text
