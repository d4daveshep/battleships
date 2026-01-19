"""
Test suite for verifying the correct UI structure of the gameplay page.

This test suite ensures that the shot aiming UI follows the BDD specification:
- Right board is labeled "Shots Fired" (not "Opponent's Waters")
- Aiming interface is integrated into the right board (not a separate section)
- No separate "Aim Your Shots" section exists below the boards
- Only two board containers exist: "My Ships" and "Shots Fired"

These tests verify the fix for the shot aiming UI bug where the interface
was incorrectly split into three sections instead of two.
"""

import pytest
from fastapi.testclient import TestClient
from bs4 import BeautifulSoup


def setup_game() -> tuple[TestClient, TestClient, str]:
    """
    Helper to setup a two-player game and return clients and game_id.

    Returns:
        Tuple of (player1_client, player2_client, game_id)
    """
    from main import app

    client1 = TestClient(app, follow_redirects=False)
    client2 = TestClient(app, follow_redirects=False)

    # Reset and login
    client1.post("/test/reset-lobby")
    client1.post("/login", data={"player_name": "Player1", "game_mode": "human"})
    client2.post("/login", data={"player_name": "Player2", "game_mode": "human"})

    # Match players
    client1.post("/select-opponent", data={"opponent_name": "Player2"})
    client2.post("/accept-game-request", data={})

    # Navigate through ship placement
    resp1 = client1.get("/lobby/status/Player1")
    if resp1.status_code in [302, 303]:
        client1.get(resp1.headers["location"])

    resp2 = client2.get("/lobby/status/Player2")
    if resp2.status_code in [302, 303]:
        client2.get(resp2.headers["location"])

    # Start game
    resp1_start = client1.post(
        "/start-game", data={"action": "start_game", "player_name": "Player1"}
    )
    if resp1_start.status_code in [302, 303]:
        client1.get(resp1_start.headers["location"])

    resp2_start = client2.post(
        "/start-game", data={"action": "start_game", "player_name": "Player2"}
    )
    if resp2_start.status_code in [302, 303]:
        client2.get(resp2_start.headers["location"])

    # Place ships
    ships_to_place = [
        ("Carrier", "A1", "horizontal"),
        ("Battleship", "C1", "horizontal"),
        ("Cruiser", "E1", "horizontal"),
        ("Submarine", "G1", "horizontal"),
        ("Destroyer", "I1", "horizontal"),
    ]

    for ship_name, start_coordinate, orientation in ships_to_place:
        client1.post(
            "/place-ship",
            data={
                "player_name": "Player1",
                "ship_name": ship_name,
                "start_coordinate": start_coordinate,
                "orientation": orientation,
            },
        )
        client2.post(
            "/place-ship",
            data={
                "player_name": "Player2",
                "ship_name": ship_name,
                "start_coordinate": start_coordinate,
                "orientation": orientation,
            },
        )

    # Mark ready
    client1.post("/ready-for-game", data={"player_name": "Player1"})
    resp_ready = client2.post("/ready-for-game", data={"player_name": "Player2"})

    # Extract game_id
    game_id = None
    if resp_ready.status_code in [302, 303]:
        redirect_url = resp_ready.headers["location"]
        if "/game/" in redirect_url:
            game_id = redirect_url.split("/game/")[1].split("/")[0].split("?")[0]

    assert game_id is not None, "Game ID not found"

    return client1, client2, game_id


def test_gameplay_page_has_correct_board_labels():
    """
    Verify that the gameplay page has the correct board labels.

    Expected:
    - Left board: "My Ships"
    - Right board: "Shots Fired" (NOT "Opponent's Waters")

    This test ensures the right board is correctly labeled for shot aiming.
    """
    client1, client2, game_id = setup_game()

    # Get gameplay page
    resp = client1.get(f"/game/{game_id}")
    assert resp.status_code == 200

    soup = BeautifulSoup(resp.text, "html.parser")

    # Find all h3 elements
    h3_elements = soup.find_all("h3")
    h3_texts = [h3.get_text().strip() for h3 in h3_elements]

    # Should have "Shots Fired" label
    assert "Shots Fired" in h3_texts, (
        f"Expected 'Shots Fired' label, but found: {h3_texts}"
    )

    # Should NOT have "Opponent's Waters" label
    assert "Opponent's Waters" not in h3_texts, (
        f"Should not have 'Opponent's Waters' label, but found: {h3_texts}"
    )


def test_gameplay_page_has_no_separate_aim_your_shots_section():
    """
    Verify that there is NO separate "Aim Your Shots" section.

    The aiming interface should be integrated into the "Shots Fired" board,
    not in a separate section below the two boards.
    """
    client1, client2, game_id = setup_game()

    # Get gameplay page
    resp = client1.get(f"/game/{game_id}")
    assert resp.status_code == 200

    soup = BeautifulSoup(resp.text, "html.parser")

    # Should NOT have a separate "Aim Your Shots" section
    h2_elements = soup.find_all("h2")
    h2_texts = [h2.get_text().strip() for h2 in h2_elements]

    assert "Aim Your Shots" not in h2_texts, (
        f"Should not have 'Aim Your Shots' section, but found: {h2_texts}"
    )


def test_gameplay_page_has_exactly_two_board_containers():
    """
    Verify that there are exactly 2 board containers.

    Expected structure:
    1. Left container: "My Ships" board
    2. Right container: "Shots Fired" board with integrated aiming interface

    This ensures the UI follows the two-column layout specified in the BDD features.
    """
    client1, client2, game_id = setup_game()

    # Get gameplay page
    resp = client1.get(f"/game/{game_id}")
    assert resp.status_code == 200

    soup = BeautifulSoup(resp.text, "html.parser")

    # Find the ship-board-container divs
    board_containers = soup.find_all("div", class_="ship-board-container")

    # Should have exactly 2 board containers (My Ships + Shots Fired)
    assert len(board_containers) == 2, (
        f"Expected 2 board containers, found {len(board_containers)}"
    )

    # The second container should have "Shots Fired" as its heading
    second_container = board_containers[1]
    second_container_h3 = second_container.find("h3")
    assert second_container_h3 is not None, "Second container should have an h3 heading"
    assert "Shots Fired" in second_container_h3.get_text(), (
        f"Second container heading should be 'Shots Fired', got: {second_container_h3.get_text()}"
    )


def test_aiming_interface_contains_shots_fired_board():
    """
    Verify that the aiming interface (loaded via HTMX) contains the shots-fired-board.

    The shots-fired-board is the interactive grid where players click to aim their shots.
    This test ensures the aiming interface includes this critical component.
    """
    client1, client2, game_id = setup_game()

    # Get aiming interface
    resp = client1.get(f"/game/{game_id}/aiming-interface")
    assert resp.status_code == 200

    soup = BeautifulSoup(resp.text, "html.parser")

    # Should contain the shots-fired-board
    shots_fired_board = soup.find(attrs={"data-testid": "shots-fired-board"})
    assert shots_fired_board is not None, (
        "Aiming interface should contain shots-fired-board"
    )


def test_aiming_interface_is_loaded_into_shots_fired_container():
    """
    Verify that the aiming interface is configured to load into the right board container.

    The aiming-interface div should be a child of the "Shots Fired" board container,
    ensuring the interactive aiming UI is integrated with the board display.
    """
    client1, client2, game_id = setup_game()

    # Get gameplay page
    resp = client1.get(f"/game/{game_id}")
    assert resp.status_code == 200

    soup = BeautifulSoup(resp.text, "html.parser")

    # Find the aiming-interface div
    aiming_interface = soup.find(id="aiming-interface")
    assert aiming_interface is not None, "Should have aiming-interface div"

    # It should be inside the second board container (Shots Fired)
    board_containers = soup.find_all("div", class_="ship-board-container")
    second_container = board_containers[1]

    # Check if aiming-interface is a descendant of the second container
    assert aiming_interface in second_container.descendants, (
        "Aiming interface should be inside the Shots Fired container"
    )


def test_shots_fired_board_shows_round_numbers():
    """
    Verify that the shots fired board displays round numbers on fired cells.

    When a player has fired shots in previous rounds, the shots-fired-board
    should display the round number in each fired cell.

    Expected:
    - Cells fired in round 1 show "1"
    - Cells fired in round 2 show "2"
    - Unfired cells show nothing
    """
    client1, client2, game_id = setup_game()

    # Round 1: Player 1 fires at A1, A2
    client1.post(f"/game/{game_id}/aim-shot", data={"coord": "A1"})
    client1.post(f"/game/{game_id}/aim-shot", data={"coord": "A2"})
    client1.post(f"/game/{game_id}/fire-shots", data={})

    # Player 2 fires to complete round 1
    client2.post(f"/game/{game_id}/aim-shot", data={"coord": "B1"})
    client2.post(f"/game/{game_id}/aim-shot", data={"coord": "B2"})
    client2.post(f"/game/{game_id}/fire-shots", data={})

    # Round 2: Player 1 fires at C1, C2
    client1.post(f"/game/{game_id}/aim-shot", data={"coord": "C1"})
    client1.post(f"/game/{game_id}/aim-shot", data={"coord": "C2"})
    client1.post(f"/game/{game_id}/fire-shots", data={})

    # Player 2 fires to complete round 2
    client2.post(f"/game/{game_id}/aim-shot", data={"coord": "D1"})
    client2.post(f"/game/{game_id}/aim-shot", data={"coord": "D2"})
    client2.post(f"/game/{game_id}/fire-shots", data={})

    # After round 2 completes, get aiming interface which will show round results
    # Then get it again to see round 3 aiming interface with past shots
    resp = client1.get(f"/game/{game_id}/aiming-interface")
    assert resp.status_code == 200

    # If we got round results, the aiming interface will be shown after continuing
    # For this test, we just need to get the aiming interface which should show past shots
    # Actually, let's just start round 3 by aiming a shot, which will show the board
    client1.post(f"/game/{game_id}/aim-shot", data={"coord": "E1"})

    # Now get the aiming interface which should show the shots fired board
    resp = client1.get(f"/game/{game_id}/aiming-interface")
    assert resp.status_code == 200

    soup = BeautifulSoup(resp.text, "html.parser")

    # Check round 1 shots show "1"
    cell_a1 = soup.find(attrs={"data-testid": "shots-fired-cell-A1"})
    assert cell_a1 is not None, "Cell A1 should exist"
    marker_a1 = cell_a1.find("span", class_="cell-marker--fired")
    assert marker_a1 is not None, "Cell A1 should have fired marker"
    assert marker_a1.get_text().strip() == "1", (
        f"Cell A1 should show round 1, got: {marker_a1.get_text()}"
    )

    cell_a2 = soup.find(attrs={"data-testid": "shots-fired-cell-A2"})
    assert cell_a2 is not None, "Cell A2 should exist"
    marker_a2 = cell_a2.find("span", class_="cell-marker--fired")
    assert marker_a2 is not None, "Cell A2 should have fired marker"
    assert marker_a2.get_text().strip() == "1", (
        f"Cell A2 should show round 1, got: {marker_a2.get_text()}"
    )

    # Check round 2 shots show "2"
    cell_c1 = soup.find(attrs={"data-testid": "shots-fired-cell-C1"})
    assert cell_c1 is not None, "Cell C1 should exist"
    marker_c1 = cell_c1.find("span", class_="cell-marker--fired")
    assert marker_c1 is not None, "Cell C1 should have fired marker"
    assert marker_c1.get_text().strip() == "2", (
        f"Cell C1 should show round 2, got: {marker_c1.get_text()}"
    )

    cell_c2 = soup.find(attrs={"data-testid": "shots-fired-cell-C2"})
    assert cell_c2 is not None, "Cell C2 should exist"
    marker_c2 = cell_c2.find("span", class_="cell-marker--fired")
    assert marker_c2 is not None, "Cell C2 should have fired marker"
    assert marker_c2.get_text().strip() == "2", (
        f"Cell C2 should show round 2, got: {marker_c2.get_text()}"
    )

    # Check unfired cell shows nothing
    cell_e5 = soup.find(attrs={"data-testid": "shots-fired-cell-E5"})
    assert cell_e5 is not None, "Cell E5 should exist"
    marker_e5 = cell_e5.find("span", class_="cell-marker--fired")
    assert marker_e5 is None, "Cell E5 should not have fired marker"


def test_my_ships_board_shows_incoming_shots():
    """
    Verify that the player's own board displays incoming shots with round numbers.

    When an opponent fires at the player's board, the player should see:
    - Round numbers on cells that were hit
    - Distinction between hits on ships vs misses

    Expected:
    - Cells hit in round 1 show "1"
    - Cells hit in round 2 show "2"
    - Unhit cells show ship codes or nothing
    """
    client1, client2, game_id = setup_game()

    # Round 1: Player 2 fires at Player 1's board (A1, A2)
    client1.post(f"/game/{game_id}/aim-shot", data={"coord": "B1"})
    client1.post(f"/game/{game_id}/aim-shot", data={"coord": "B2"})
    client1.post(f"/game/{game_id}/fire-shots", data={})

    client2.post(
        f"/game/{game_id}/aim-shot", data={"coord": "A1"}
    )  # Hits Player 1's Carrier
    client2.post(
        f"/game/{game_id}/aim-shot", data={"coord": "A2"}
    )  # Hits Player 1's Carrier
    client2.post(f"/game/{game_id}/fire-shots", data={})

    # Round 2: Player 2 fires at Player 1's board (C1, C2)
    client1.post(f"/game/{game_id}/aim-shot", data={"coord": "D1"})
    client1.post(f"/game/{game_id}/aim-shot", data={"coord": "D2"})
    client1.post(f"/game/{game_id}/fire-shots", data={})

    client2.post(
        f"/game/{game_id}/aim-shot", data={"coord": "C1"}
    )  # Hits Player 1's Battleship
    client2.post(
        f"/game/{game_id}/aim-shot", data={"coord": "C2"}
    )  # Hits Player 1's Battleship
    client2.post(f"/game/{game_id}/fire-shots", data={})

    # Get gameplay page for player 1
    resp = client1.get(f"/game/{game_id}")
    assert resp.status_code == 200

    soup = BeautifulSoup(resp.text, "html.parser")

    # Check round 1 incoming shots show "1"
    cell_a1 = soup.find(attrs={"data-testid": "player-cell-A1"})
    assert cell_a1 is not None, "Cell A1 should exist"
    # Should show round number marker for incoming shot
    marker_a1 = cell_a1.find("span", class_="incoming-shot")
    assert marker_a1 is not None, "Cell A1 should have incoming shot marker"
    assert "1" in marker_a1.get_text(), (
        f"Cell A1 should show round 1, got: {marker_a1.get_text()}"
    )

    cell_a2 = soup.find(attrs={"data-testid": "player-cell-A2"})
    assert cell_a2 is not None, "Cell A2 should exist"
    marker_a2 = cell_a2.find("span", class_="incoming-shot")
    assert marker_a2 is not None, "Cell A2 should have incoming shot marker"
    assert "1" in marker_a2.get_text(), (
        f"Cell A2 should show round 1, got: {marker_a2.get_text()}"
    )

    # Check round 2 incoming shots show "2"
    cell_c1 = soup.find(attrs={"data-testid": "player-cell-C1"})
    assert cell_c1 is not None, "Cell C1 should exist"
    marker_c1 = cell_c1.find("span", class_="incoming-shot")
    assert marker_c1 is not None, "Cell C1 should have incoming shot marker"
    assert "2" in marker_c1.get_text(), (
        f"Cell C1 should show round 2, got: {marker_c1.get_text()}"
    )

    cell_c2 = soup.find(attrs={"data-testid": "player-cell-C2"})
    assert cell_c2 is not None, "Cell C2 should exist"
    marker_c2 = cell_c2.find("span", class_="incoming-shot")
    assert marker_c2 is not None, "Cell C2 should have incoming shot marker"
    assert "2" in marker_c2.get_text(), (
        f"Cell C2 should show round 2, got: {marker_c2.get_text()}"
    )

    # Check unhit cell shows ship code only (no incoming shot marker)
    cell_a3 = soup.find(attrs={"data-testid": "player-cell-A3"})
    assert cell_a3 is not None, "Cell A3 should exist"
    marker_a3 = cell_a3.find("span", class_="incoming-shot")
    assert marker_a3 is None, "Cell A3 should not have incoming shot marker"
    # A3 is part of Carrier, should show ship code
    assert "A" in cell_a3.get_text() or cell_a3.get("data-ship") == "carrier", (
        "Cell A3 should show ship code"
    )


def test_round_results_shows_hit_feedback():
    """
    Verify that round results display shows ship-based hit feedback.

    When both players fire and a round is resolved, the results should show:
    - Round number
    - Hits made by the player (ship-based, not coordinates)
    - Hits received from opponent (ship-based)
    - Button to continue to next round

    Expected:
    - "You hit: Carrier (2 hits)" format
    - "Opponent hit your: Battleship (1 hit)" format
    - No coordinate leakage
    """
    client1, client2, game_id = setup_game()

    # Round 1: Both players fire
    # Player 1 fires at Player 2's Carrier (A1, A2)
    client1.post(f"/game/{game_id}/aim-shot", data={"coord": "A1"})
    client1.post(f"/game/{game_id}/aim-shot", data={"coord": "A2"})
    fire_resp1 = client1.post(f"/game/{game_id}/fire-shots", data={})

    # Player 2 fires at Player 1's Battleship (C1, C2)
    client2.post(f"/game/{game_id}/aim-shot", data={"coord": "C1"})
    client2.post(f"/game/{game_id}/aim-shot", data={"coord": "C2"})
    fire_resp2 = client2.post(f"/game/{game_id}/fire-shots", data={})

    # After both players fire, round should be resolved
    # The fire_shots response should show round results
    assert fire_resp2.status_code == 200

    soup = BeautifulSoup(fire_resp2.text, "html.parser")

    # Check for round results component
    round_results = soup.find(attrs={"data-testid": "round-results"})
    assert round_results is not None, "Should have round results component"

    # Check round number is displayed
    assert "Round 1" in round_results.get_text(), "Should show round number"

    # Check hits made section (Player 2 hit Player 1's Battleship)
    hits_made_section = round_results.find(class_="hits-made")
    assert hits_made_section is not None, "Should have hits made section"
    hits_made_text = hits_made_section.get_text()
    assert "Battleship" in hits_made_text, "Should show ship name (Battleship)"
    assert "2" in hits_made_text, "Should show hit count (2)"
    # Ensure no coordinates are leaked
    assert "C1" not in hits_made_text, "Should not show coordinates"
    assert "C2" not in hits_made_text, "Should not show coordinates"

    # Check hits received section (Player 2 received hits on Carrier)
    hits_received_section = round_results.find(class_="hits-received")
    assert hits_received_section is not None, "Should have hits received section"
    hits_received_text = hits_received_section.get_text()
    assert "Carrier" in hits_received_text, "Should show ship name (Carrier)"
    assert "2" in hits_received_text, "Should show hit count (2)"
    # For hits RECEIVED, coordinates SHOULD be shown (player knows their own ship positions)
    assert "A1" in hits_received_text, "Should show coordinate A1 for hits received"
    assert "A2" in hits_received_text, "Should show coordinate A2 for hits received"

    # Check for continue button
    continue_button = round_results.find("button")
    assert continue_button is not None, "Should have continue button"
    assert (
        "Continue" in continue_button.get_text()
        or "Round 2" in continue_button.get_text()
    ), "Button should mention continuing or next round"
