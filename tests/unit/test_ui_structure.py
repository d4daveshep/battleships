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
    resp1_start = client1.post("/start-game", data={"action": "start_game", "player_name": "Player1"})
    if resp1_start.status_code in [302, 303]:
        client1.get(resp1_start.headers["location"])
    
    resp2_start = client2.post("/start-game", data={"action": "start_game", "player_name": "Player2"})
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
        client1.post("/place-ship", data={
            "player_name": "Player1",
            "ship_name": ship_name,
            "start_coordinate": start_coordinate,
            "orientation": orientation,
        })
        client2.post("/place-ship", data={
            "player_name": "Player2",
            "ship_name": ship_name,
            "start_coordinate": start_coordinate,
            "orientation": orientation,
        })
    
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
    assert "Shots Fired" in h3_texts, f"Expected 'Shots Fired' label, but found: {h3_texts}"
    
    # Should NOT have "Opponent's Waters" label
    assert "Opponent's Waters" not in h3_texts, f"Should not have 'Opponent's Waters' label, but found: {h3_texts}"


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
    
    assert "Aim Your Shots" not in h2_texts, f"Should not have 'Aim Your Shots' section, but found: {h2_texts}"


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
    assert len(board_containers) == 2, f"Expected 2 board containers, found {len(board_containers)}"
    
    # The second container should have "Shots Fired" as its heading
    second_container = board_containers[1]
    second_container_h3 = second_container.find("h3")
    assert second_container_h3 is not None, "Second container should have an h3 heading"
    assert "Shots Fired" in second_container_h3.get_text(), f"Second container heading should be 'Shots Fired', got: {second_container_h3.get_text()}"


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
    assert shots_fired_board is not None, "Aiming interface should contain shots-fired-board"


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
    assert aiming_interface in second_container.descendants, "Aiming interface should be inside the Shots Fired container"
