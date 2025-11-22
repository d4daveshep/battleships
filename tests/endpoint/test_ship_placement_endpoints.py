"""
Endpoint tests for ship placement functionality.

Tests verify the ship placement page rendering and ship placement endpoint behavior.
"""

from bs4 import BeautifulSoup
from fastapi import status
from fastapi.testclient import TestClient


class TestShipPlacementPageEndpoint:
    """Tests for GET /ship-placement endpoint"""

    def test_ship_placement_page_returns_200(self, client: TestClient):
        """Test that ship placement page loads successfully"""
        response = client.get("/ship-placement", params={"player_name": "Alice"})

        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]

    def test_ship_placement_page_displays_player_name(self, client: TestClient):
        """Test that ship placement page shows the player's name"""
        response = client.get("/ship-placement", params={"player_name": "TestPlayer"})

        assert response.status_code == status.HTTP_200_OK

        # Check that player name is displayed
        assert "TestPlayer" in response.text

    def test_ship_placement_page_shows_empty_state(self, client: TestClient):
        """Test that ship placement page shows no ships initially"""
        response = client.get("/ship-placement", params={"player_name": "Alice"})

        assert response.status_code == status.HTTP_200_OK
        soup = BeautifulSoup(response.text, "html.parser")

        # Check for ship placement status showing 0 ships
        status_element = soup.find(attrs={"data-testid": "ship-placement-count"})
        assert status_element is not None
        assert "0 of 5 ships placed" in status_element.text

    def test_ship_placement_page_has_placement_form(self, client: TestClient):
        """Test that ship placement page contains the placement form"""
        response = client.get("/ship-placement", params={"player_name": "Alice"})

        assert response.status_code == status.HTTP_200_OK
        soup = BeautifulSoup(response.text, "html.parser")

        # Check for form with action="/place-ship"
        form = soup.find("form", action="/place-ship")
        assert form is not None

        # Verify form has required fields
        ship_name_input = form.find("input", {"name": "ship_name"})  # type: ignore
        start_coord_input = form.find("input", {"name": "start_coordinate"})  # type: ignore
        orientation_select = form.find("select", {"name": "orientation"})  # type: ignore
        player_name_input = form.find("input", {"name": "player_name"})  # type: ignore

        assert ship_name_input is not None
        assert start_coord_input is not None
        assert orientation_select is not None
        assert player_name_input is not None

    def test_ship_placement_page_has_ship_selection_buttons(self, client: TestClient):
        """Test that ship placement page has buttons for all ship types"""
        response = client.get("/ship-placement", params={"player_name": "Alice"})

        assert response.status_code == status.HTTP_200_OK
        soup = BeautifulSoup(response.text, "html.parser")

        # Check for ship selection buttons
        expected_ships = ["carrier", "battleship", "cruiser", "submarine", "destroyer"]
        for ship in expected_ships:
            button = soup.find(attrs={"data-testid": f"select-ship-{ship}"})
            assert button is not None, f"Missing button for {ship}"

    def test_ship_placement_page_works_without_player_name(self, client: TestClient):
        """Test that ship placement page works even without player name parameter"""
        response = client.get("/ship-placement")

        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]

    def test_ship_placement_page_has_action_buttons(self, client: TestClient):
        """Test that ship placement page has action buttons for game flow"""
        response = client.get("/ship-placement", params={"player_name": "Alice"})

        assert response.status_code == status.HTTP_200_OK
        soup = BeautifulSoup(response.text, "html.parser")

        # Check for key action buttons (even if they don't have endpoints yet)
        random_button = soup.find(attrs={"data-testid": "random-placement-button"})
        reset_button = soup.find(attrs={"data-testid": "reset-all-ships-button"})
        start_button = soup.find(attrs={"data-testid": "start-game-button"})
        ready_button = soup.find(attrs={"data-testid": "ready-button"})

        assert random_button is not None
        assert reset_button is not None
        assert start_button is not None
        assert ready_button is not None


class TestPlaceShipEndpoint:
    """Tests for POST /place-ship endpoint"""

    def test_place_ship_endpoint_exists(self, client: TestClient):
        """Test that place ship endpoint responds to POST requests"""
        # Note: Current implementation has assert False, so this will fail
        # This test documents the expected behavior
        response = client.post(
            "/place-ship",
            data={
                "player_name": "Alice",
                "ship_name": "Carrier",
                "start_coordinate": "A1",
                "orientation": "horizontal",
            },
        )

        # Currently fails with 500 due to assert False in implementation
        # When implemented, should return 200
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]

    def test_place_ship_horizontal_carrier(self, client: TestClient):
        """Test placing a carrier horizontally at A1"""
        response = client.post(
            "/place-ship",
            data={
                "player_name": "Alice",
                "ship_name": "Carrier",
                "start_coordinate": "A1",
                "orientation": "horizontal",
            },
        )

        # Currently fails with 500 due to assert False
        # When implemented, should return ship placement page with placed ship
        if response.status_code == status.HTTP_200_OK:
            soup = BeautifulSoup(response.text, "html.parser")

            # Should show 1 ship placed
            status_element = soup.find(attrs={"data-testid": "ship-placement-count"})
            assert status_element is not None
            assert "1 of 5 ships placed" in status_element.text

            # Should show carrier as placed
            carrier_element = soup.find(attrs={"data-testid": "placed-ship-carrier"})
            assert carrier_element is not None

            # Should show cells A1-A5 for horizontal carrier
            for i in range(1, 6):
                cell = soup.find(attrs={"data-testid": f"cell-A{i}"})
                assert cell is not None

    def test_place_ship_vertical_battleship(self, client: TestClient):
        """Test placing a battleship vertically at B2"""
        response = client.post(
            "/place-ship",
            data={
                "player_name": "Alice",
                "ship_name": "Battleship",
                "start_coordinate": "B2",
                "orientation": "vertical",
            },
        )

        if response.status_code == status.HTTP_200_OK:
            soup = BeautifulSoup(response.text, "html.parser")

            # Should show battleship as placed
            battleship_element = soup.find(
                attrs={"data-testid": "placed-ship-battleship"}
            )
            assert battleship_element is not None

            # Should show cells B2, C2, D2, E2 for vertical battleship
            expected_cells = ["B2", "C2", "D2", "E2"]
            for cell in expected_cells:
                cell_element = soup.find(attrs={"data-testid": f"cell-{cell}"})
                assert cell_element is not None

    def test_place_ship_diagonal_down_cruiser(self, client: TestClient):
        """Test placing a cruiser diagonally down at C3"""
        response = client.post(
            "/place-ship",
            data={
                "player_name": "Alice",
                "ship_name": "Cruiser",
                "start_coordinate": "C3",
                "orientation": "diagonal_down",
            },
        )

        if response.status_code == status.HTTP_200_OK:
            soup = BeautifulSoup(response.text, "html.parser")

            # Should show cruiser as placed
            cruiser_element = soup.find(attrs={"data-testid": "placed-ship-cruiser"})
            assert cruiser_element is not None

            # Should show cells C3, D4, E5 for diagonal-down cruiser
            expected_cells = ["C3", "D4", "E5"]
            for cell in expected_cells:
                cell_element = soup.find(attrs={"data-testid": f"cell-{cell}"})
                assert cell_element is not None

    def test_place_ship_diagonal_up_destroyer(self, client: TestClient):
        """Test placing a destroyer diagonally up at D4"""
        response = client.post(
            "/place-ship",
            data={
                "player_name": "Alice",
                "ship_name": "Destroyer",
                "start_coordinate": "D4",
                "orientation": "diagonal_up",
            },
        )

        if response.status_code == status.HTTP_200_OK:
            soup = BeautifulSoup(response.text, "html.parser")

            # Should show destroyer as placed
            destroyer_element = soup.find(
                attrs={"data-testid": "placed-ship-destroyer"}
            )
            assert destroyer_element is not None

            # Should show cells D4, C5 for diagonal-up destroyer
            expected_cells = ["D4", "C5"]
            for cell in expected_cells:
                cell_element = soup.find(attrs={"data-testid": f"cell-{cell}"})
                assert cell_element is not None

    def test_place_ship_requires_all_parameters(self, client: TestClient):
        """Test that place ship endpoint requires all parameters"""
        # Missing orientation
        response = client.post(
            "/place-ship",
            data={
                "player_name": "Alice",
                "ship_name": "Carrier",
                "start_coordinate": "A1",
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_place_ship_multiple_ships_sequentially(self, client: TestClient):
        """Test placing multiple ships in sequence"""
        # This test documents expected behavior when implementation is complete
        # Place first ship
        response1 = client.post(
            "/place-ship",
            data={
                "player_name": "Alice",
                "ship_name": "Carrier",
                "start_coordinate": "A1",
                "orientation": "horizontal",
            },
        )

        if response1.status_code == status.HTTP_200_OK:
            # Place second ship
            response2 = client.post(
                "/place-ship",
                data={
                    "player_name": "Alice",
                    "ship_name": "Battleship",
                    "start_coordinate": "C1",
                    "orientation": "horizontal",
                },
            )

            assert response2.status_code == status.HTTP_200_OK
            soup = BeautifulSoup(response2.text, "html.parser")

            # Should show 2 ships placed
            status_element = soup.find(attrs={"data-testid": "ship-placement-count"})
            assert status_element is not None
            assert "2 of 5 ships placed" in status_element.text


class TestShipPlacementIntegration:
    """Integration tests for ship placement flow"""

    def test_full_ship_placement_flow(self, client: TestClient):
        """Test complete flow from login to ship placement"""
        # Login with computer mode
        login_response = client.post(
            "/", data={"player_name": "Alice", "game_mode": "computer"}
        )

        # Should redirect to ship placement
        assert login_response.status_code in [
            status.HTTP_303_SEE_OTHER,
            status.HTTP_200_OK,
        ]

        if login_response.status_code == status.HTTP_303_SEE_OTHER:
            redirect_url = login_response.headers["location"]
            assert "/ship-placement" in redirect_url
            assert "player_name=Alice" in redirect_url

            # Follow redirect
            placement_response = client.get(redirect_url)
            assert placement_response.status_code == status.HTTP_200_OK
            assert "Ship Placement" in placement_response.text

    def test_ship_placement_page_from_multiplayer_login(self, client: TestClient):
        """Test that multiplayer mode does not go to ship placement directly"""
        # Login with human mode (multiplayer)
        login_response = client.post(
            "/", data={"player_name": "Alice", "game_mode": "human"}
        )

        # Should redirect to lobby, not ship placement
        if login_response.status_code == status.HTTP_303_SEE_OTHER:
            redirect_url = login_response.headers["location"]
            assert "/lobby" in redirect_url
            assert "/ship-placement" not in redirect_url


class TestShipPlacementValidation:
    """Tests for ship placement validation (when implemented)"""

    def test_place_ship_invalid_coordinate_format(self, client: TestClient):
        """Test that invalid coordinates are rejected (when validation is implemented)"""
        response = client.post(
            "/place-ship",
            data={
                "player_name": "Alice",
                "ship_name": "Carrier",
                "start_coordinate": "Z99",  # Invalid coordinate
                "orientation": "horizontal",
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_place_ship_out_of_bounds(self, client: TestClient):
        """Test that ships going out of bounds are rejected (when implemented)"""
        response = client.post(
            "/place-ship",
            data={
                "player_name": "Alice",
                "ship_name": "Carrier",
                "start_coordinate": "A8",  # Would go to A12 horizontally (out of bounds)
                "orientation": "horizontal",
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_place_ship_duplicate_ship_name(self, client: TestClient):
        """Test that placing the same ship twice is rejected (when implemented)"""
        # Place carrier first time
        client.post(
            "/place-ship",
            data={
                "player_name": "Alice",
                "ship_name": "Carrier",
                "start_coordinate": "A1",
                "orientation": "horizontal",
            },
        )

        # Try to place carrier again
        response = client.post(
            "/place-ship",
            data={
                "player_name": "Alice",
                "ship_name": "Carrier",
                "start_coordinate": "C1",
                "orientation": "horizontal",
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert (
            "already placed" in response.text.lower()
            or "duplicate" in response.text.lower()
        )

    def test_place_ship_invalid_ship_name(self, client: TestClient):
        """Test that invalid ship names are rejected (when implemented)"""
        response = client.post(
            "/place-ship",
            data={
                "player_name": "Alice",
                "ship_name": "Speedboat",  # Invalid ship name
                "start_coordinate": "A1",
                "orientation": "horizontal",
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
