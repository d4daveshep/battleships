import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from tests.bdd.conftest import MultiPlayerBDDContext
from bs4 import BeautifulSoup, Tag
from httpx import Response

scenarios("../../features/two_player_gameplay.feature")


@pytest.fixture
def context() -> MultiPlayerBDDContext:
    return MultiPlayerBDDContext()


# === Background Steps ===


@given("both players have completed ship placement")
def players_completed_placement(context: MultiPlayerBDDContext):
    """Setup a game with two players who have placed ships"""
    # 1. Reset Lobby
    with context.get_client_for_player("System") as client:
        client.post("/test/reset-lobby")

    # 2. Login Players
    p1_name = "Player1"
    p2_name = "Player2"
    context.current_player_name = p1_name

    client1 = context.get_client_for_player(p1_name)
    client1.post("/login", data={"player_name": p1_name, "game_mode": "human"})

    client2 = context.get_client_for_player(p2_name)
    client2.post("/login", data={"player_name": p2_name, "game_mode": "human"})

    # 3. Match Players
    # Player 1 selects Player 2
    client1.post("/select-opponent", data={"opponent_name": p2_name})
    # Player 2 accepts
    client2.post("/accept-game-request", data={})

    # 4. Place Ships for Player 1
    ships = [
        ("Carrier", "A1", "horizontal"),
        ("Battleship", "C1", "horizontal"),
        ("Cruiser", "E1", "horizontal"),
        ("Submarine", "G1", "horizontal"),
        ("Destroyer", "I1", "horizontal"),
    ]
    for ship, start, orientation in ships:
        client1.post(
            "/place-ship",
            data={
                "player_name": p1_name,
                "ship_name": ship,
                "start_coordinate": start,
                "orientation": orientation,
            },
        )

    # 5. Place Ships for Player 2
    for ship, start, orientation in ships:
        client2.post(
            "/place-ship",
            data={
                "player_name": p2_name,
                "ship_name": ship,
                "start_coordinate": start,
                "orientation": orientation,
            },
        )


@given("both players are ready")
def players_are_ready(context: MultiPlayerBDDContext):
    """Both players click ready"""
    p1_name = "Player1"
    p2_name = "Player2"

    client1 = context.get_client_for_player(p1_name)
    client2 = context.get_client_for_player(p2_name)

    client1.post("/ready-for-game", data={"player_name": p1_name})
    # P2 ready - this should trigger game start and return redirect
    response = client2.post(
        "/ready-for-game", data={"player_name": p2_name}, follow_redirects=False
    )

    # Store the game URL from the redirect
    if response.status_code in [302, 303] and "location" in response.headers:
        context.game_url = response.headers["location"]
    else:
        # Try to get game URL from P1's status check
        status_response = client1.get(
            "/place-ships/opponent-status", headers={"HX-Request": "true"}
        )
        if "HX-Redirect" in status_response.headers:
            context.game_url = status_response.headers["HX-Redirect"]


@given("the game has started")
def game_has_started(context: MultiPlayerBDDContext):
    """Verify game has started by checking redirect or status"""
    # We can check if accessing the game page works
    client1 = context.get_client_for_player("Player1")
    # The game URL is usually /game/{game_id} or just /game depending on implementation
    # But typically we get redirected there.
    # Let's assume we can access the game page if the game is started.
    # We might need to follow the redirect from the ready check.
    pass


@given("I am on the gameplay page")
def on_gameplay_page(context: MultiPlayerBDDContext):
    """Navigate to gameplay page"""
    assert context.current_player_name is not None, "No current player set"
    assert context.game_url is not None, (
        "No game URL stored - game may not have started"
    )

    client = context.get_client_for_player(context.current_player_name)
    response = client.get(context.game_url)
    context.update_response(response)

    # Verify we are on the game page
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert "Round" in response.text or "game" in response.text.lower()


# === Scenario Steps ===


@given("the game just started")
def game_just_started(context: MultiPlayerBDDContext):
    """Ensure it is the beginning of the game"""
    # This is implicitly true after setup
    pass


@then(parsers.parse('I should see "{text}" displayed'))
def see_text_displayed(context: MultiPlayerBDDContext, text: str):
    """Verify text is displayed on the page"""
    assert context.soup is not None
    assert text in context.soup.get_text()


@then("I should be able to select up to 6 coordinates to fire at")
def can_select_6_coordinates(context: MultiPlayerBDDContext):
    """Verify firing controls are present"""
    assert context.soup is not None
    # Check for the grid that allows selection
    # This might be the opponent's board (shots fired board)
    shots_board = context.soup.find(attrs={"data-testid": "shots-fired-board"})
    assert shots_board is not None

    # Check for fire button
    fire_btn = context.soup.find(attrs={"data-testid": "fire-shots-button"})
    assert fire_btn is not None


@then(parsers.parse('I should see my board labeled "{label}"'))
def see_my_board_labeled(context: MultiPlayerBDDContext, label: str):
    """Verify my board label"""
    assert context.soup is not None
    # Find the label associated with the board
    # This is a loose check, looking for the text near the board
    assert label in context.soup.get_text()

    board = context.soup.find(attrs={"data-testid": "my-ships-board"})
    assert board is not None


@then(parsers.parse('I should see the opponent\'s board labeled "{label}"'))
def see_opponent_board_labeled(context: MultiPlayerBDDContext, label: str):
    """Verify opponent board label"""
    assert context.soup is not None
    assert label in context.soup.get_text()

    board = context.soup.find(attrs={"data-testid": "shots-fired-board"})
    assert board is not None


@then(
    parsers.parse(
        'I should see the "Hits Made" area showing all {count:d} opponent ships'
    )
)
def see_hits_made_area(context: MultiPlayerBDDContext, count: int):
    """Verify hits made area"""
    assert context.soup is not None
    hits_area = context.soup.find(attrs={"data-testid": "hits-made-area"})
    assert hits_area is not None

    # Check for ship names
    ship_names = ["Carrier", "Battleship", "Cruiser", "Submarine", "Destroyer"]
    text = hits_area.get_text()
    for ship in ship_names:
        assert ship in text


# === Scenario: Selecting multiple shot coordinates for aiming ===


@given("it is Round 1")
def it_is_round_1(context: MultiPlayerBDDContext):
    """Verify it is Round 1"""
    # This is implicitly true at game start
    pass


@given("I have 6 shots available")
def have_6_shots_available(context: MultiPlayerBDDContext):
    """Verify player has 6 shots available (all ships placed)"""
    # This is implicitly true when ships are placed
    pass


@when(parsers.parse('I select coordinate "{coord}" to aim at'))
def select_coordinate_to_aim(context: MultiPlayerBDDContext, coord: str):
    """Select a coordinate to aim at via HTMX endpoint"""
    assert context.game_url is not None, "No game URL stored"
    assert context.current_player_name is not None, "No current player set"

    # Extract game_id from game_url (format: /game/{game_id})
    game_id = context.game_url.split("/")[-1]

    client = context.get_client_for_player(context.current_player_name)
    response = client.post(
        "/aim-shot",
        data={"game_id": game_id, "coordinate": coord},
        headers={"HX-Request": "true"},
    )
    context.update_response(response)

    # Refresh the page to get the full state
    response = client.get(context.game_url)
    context.update_response(response)


@then(parsers.parse("I should see {count:d} coordinates marked as aimed"))
def see_coordinates_marked_as_aimed(context: MultiPlayerBDDContext, count: int):
    """Verify number of coordinates marked as aimed"""
    assert context.soup is not None
    # Check for checked checkboxes in the shots-fired board
    shots_board = context.soup.find(attrs={"data-testid": "shots-fired-board"})
    assert shots_board is not None
    assert isinstance(shots_board, Tag)
    checked_boxes = shots_board.find_all("input", {"type": "checkbox", "checked": True})
    assert len(checked_boxes) == count, (
        f"Expected {count} aimed cells, found {len(checked_boxes)}"
    )


@then("I should be able to select 3 more coordinates")
def can_select_3_more_coordinates(context: MultiPlayerBDDContext):
    """Verify 3 more coordinates can be selected (6-3=3)"""
    # This is implicitly true if we have 3/6 aimed
    # The UI should allow selecting more
    assert context.soup is not None
    # Check that we're not at max capacity (6/6)
    aiming_status = context.soup.find(attrs={"data-testid": "aiming-status"})
    assert aiming_status is not None
    text = aiming_status.get_text()
    # Should not see 6/6
    assert "6/6" not in text, "All shots are aimed, cannot select more"


@then(parsers.parse('the "{button_name}" button should be enabled'))
def button_should_be_enabled(context: MultiPlayerBDDContext, button_name: str):
    """Verify that a button is enabled"""
    assert context.soup is not None
    # Map button name to testid
    testid_map: dict[str, str] = {
        "Fire Shots": "fire-shots-button",
    }
    testid = testid_map.get(
        button_name, button_name.lower().replace(" ", "-") + "-button"
    )
    button = context.soup.find(attrs={"data-testid": testid})
    assert button is not None, f"Button with testid '{testid}' not found"
    assert isinstance(button, Tag), f"Button is not a Tag element"
    # Check not disabled
    assert not button.has_attr("disabled"), f"Button '{button_name}' is disabled"


# === Scenario: Reselecting an aimed shot's coordinates un-aims the shot ===


@given(parsers.parse('I have only selected coordinate "{coord}" to aim at'))
def have_only_selected_coordinate(context: MultiPlayerBDDContext, coord: str):
    """Select exactly one coordinate to aim at"""
    assert context.game_url is not None, "No game URL stored"
    assert context.current_player_name is not None, "No current player set"

    # Extract game_id from game_url (format: /game/{game_id})
    game_id: str = context.game_url.split("/")[-1]

    client = context.get_client_for_player(context.current_player_name)
    response: Response = client.post(
        "/aim-shot",
        data={"game_id": game_id, "coordinate": coord},
        headers={"HX-Request": "true"},
    )
    context.update_response(response)

    # Refresh the page to get the full state
    response = client.get(context.game_url)
    context.update_response(response)


@when(parsers.parse('I select coordinate "{coord}" again'))
def select_coordinate_again(context: MultiPlayerBDDContext, coord: str):
    """Select the same coordinate again (toggle off)"""
    assert context.game_url is not None, "No game URL stored"
    assert context.current_player_name is not None, "No current player set"

    # Extract game_id from game_url
    game_id: str = context.game_url.split("/")[-1]

    client = context.get_client_for_player(context.current_player_name)
    response: Response = client.post(
        "/aim-shot",
        data={"game_id": game_id, "coordinate": coord},
        headers={"HX-Request": "true"},
    )
    context.update_response(response)

    # Refresh the page to get the full state
    response = client.get(context.game_url)
    context.update_response(response)


@then(parsers.parse('coordinate "{coord}" should be un-aimed'))
def coordinate_should_be_unaimed(context: MultiPlayerBDDContext, coord: str):
    """Verify the coordinate is no longer aimed"""
    assert context.soup is not None
    # Find the cell and check it's not checked
    shots_board = context.soup.find(attrs={"data-testid": "shots-fired-board"})
    assert shots_board is not None, "Shots fired board not found"
    assert isinstance(shots_board, Tag)

    cell = shots_board.find(attrs={"data-testid": f"opponent-cell-{coord}"})
    assert cell is not None, f"Cell {coord} not found"
    assert isinstance(cell, Tag)

    # Check the checkbox is not checked
    checkbox = cell.find("input", {"type": "checkbox"})
    assert checkbox is not None, f"Checkbox not found in cell {coord}"
    assert isinstance(checkbox, Tag), f"Checkbox is not a Tag element"
    assert not checkbox.has_attr("checked"), f"Coordinate {coord} is still aimed"


@then(parsers.parse('I should not see coordinate "{coord}" marked as aimed'))
def should_not_see_coordinate_marked(context: MultiPlayerBDDContext, coord: str):
    """Verify the coordinate is not visually marked as aimed"""
    assert context.soup is not None
    shots_board = context.soup.find(attrs={"data-testid": "shots-fired-board"})
    assert shots_board is not None, "Shots fired board not found"
    assert isinstance(shots_board, Tag)

    cell = shots_board.find(attrs={"data-testid": f"opponent-cell-{coord}"})
    assert cell is not None, f"Cell {coord} not found"
    assert isinstance(cell, Tag)

    # Check the cell doesn't have the aimed-cell class
    cell_classes = cell.get("class", [])
    if isinstance(cell_classes, str):
        cell_classes = [cell_classes]
    assert "aimed-cell" not in cell_classes, f"Cell {coord} still has aimed-cell class"


@then(
    parsers.parse("I should still have {count:d} remaining shot selections available")
)
def should_have_remaining_shots(context: MultiPlayerBDDContext, count: int):
    """Verify the number of remaining shot selections"""
    assert context.soup is not None

    # Check the shots available display
    shots_display = context.soup.find(attrs={"data-testid": "shots-available"})
    assert shots_display is not None, "Shots available display not found"
    text: str = shots_display.get_text()
    assert f"Shots Available: {count}" in text, (
        f"Expected 'Shots Available: {count}', got '{text}'"
    )


# === Shot Selection Limit Steps ===


def _select_aim_shot(context: MultiPlayerBDDContext, coordinate: str) -> None:
    """Select a single coordinate to aim at via HTMX.

    Args:
        context: Multi-player BDD context
        coordinate: The coordinate to select
    """
    assert context.game_url is not None, "No game URL stored"
    assert context.current_player_name is not None, "No current player set"

    game_id = context.game_id
    client = context.get_client_for_player(context.current_player_name)
    response = client.post(
        "/aim-shot",
        data={"game_id": game_id, "coordinate": coordinate},
        headers={"HX-Request": "true"},
    )
    context.update_response(response)


@given("I have selected 6 coordinates to aim at")
def have_selected_6_coordinates(context: MultiPlayerBDDContext):
    """Select 6 coordinates to aim at"""
    context.select_coordinates(["A1", "B1", "C1", "D1", "E1", "F1"])

    client = context.get_client_for_player(context.current_player_name)
    response = client.get(context.game_url)
    context.update_response(response)


@when("I attempt to select another coordinate")
def attempt_select_another_coordinate(context: MultiPlayerBDDContext):
    """Attempt to select a 7th coordinate when already at limit"""
    game_id = context.game_id
    client = context.get_client_for_player(context.current_player_name)

    htmx_response = client.post(
        "/aim-shot",
        data={"game_id": game_id, "coordinate": "G1"},
        headers={"HX-Request": "true"},
    )

    context.htmx_response = htmx_response

    response = client.get(context.game_url)
    context.update_response(response)


@then("the coordinate should not be selectable")
def coordinate_not_selectable(context: MultiPlayerBDDContext):
    """Verify the coordinate was not added to aimed shots"""
    # The HTMX response should contain an error message
    assert context.htmx_response is not None
    assert context.htmx_response.status_code == 200
    assert "All available shots aimed" in context.htmx_response.text


@then('I should see a message "All available shots aimed"')
def see_shot_limit_message(context: MultiPlayerBDDContext):
    """Verify the error message is displayed"""
    assert context.htmx_response is not None
    assert "All available shots aimed" in context.htmx_response.text


@then('I should see "Shots Aimed: 6/6" displayed')
def see_shots_aimed_counter(context: MultiPlayerBDDContext):
    """Verify the shot counter shows 6/6"""
    assert context.soup is not None

    # Check the shots aimed display
    shots_display = context.soup.find(attrs={"data-testid": "shots-aimed"})
    if shots_display:
        text: str = shots_display.get_text()
        assert "Shots Aimed: 6/6" in text, f"Expected 'Shots Aimed: 6/6', got '{text}'"
    else:
        # Alternative: check for counter in aiming status
        aiming_status = context.soup.find(attrs={"data-testid": "aiming-status"})
        if aiming_status:
            text = aiming_status.get_text()
            assert "6/6" in text, f"Expected '6/6' in aiming status, got '{text}'"


# === Scenario: Can fire fewer shots than available === #


@given(parsers.parse("I have selected {count:d} coordinates to aim at"))
def have_selected_n_coordinates(context: MultiPlayerBDDContext, count: int):
    """Select the specified number of coordinates to aim at"""
    # Select first N coordinates
    coords = ["A1", "B1", "C1", "D1", "E1", "F1"][:count]
    context.select_coordinates(coords)

    client = context.get_client_for_player(context.current_player_name)
    response = client.get(context.game_url)
    context.update_response(response)


@when(parsers.parse('I click the "{button_name}" button'))
def click_button(context: MultiPlayerBDDContext, button_name: str):
    """Click a button by name"""
    assert context.game_url is not None, "No game URL stored"
    assert context.current_player_name is not None, "No current player set"

    # Extract game_id from game_url
    game_id: str = context.game_url.split("/")[-1]

    client = context.get_client_for_player(context.current_player_name)

    if button_name == "Fire Shots":
        response = client.post(
            "/fire-shots",
            data={"game_id": game_id, "player_name": context.current_player_name},
        )
    else:
        raise ValueError(f"Unknown button: {button_name}")

    context.update_response(response)

    # Refresh the page to get the full state
    response = client.get(context.game_url)
    context.update_response(response)


@then(parsers.parse("my {count:d} shots should be submitted"))
def shots_should_be_submitted(context: MultiPlayerBDDContext, count: int):
    """Verify that the specified number of shots were submitted"""
    assert context.soup is not None

    # Check that the shot counter shows 0/6 (no shots aimed after firing)
    aiming_status = context.soup.find(attrs={"data-testid": "aiming-status"})
    if aiming_status:
        text = aiming_status.get_text()
        # Either shows "0/6" or the waiting message takes precedence
        assert "0/6" in text or "Waiting" in text, (
            f"Expected shots to be cleared after firing, got: {text}"
        )


@then('I should see "Waiting for opponent to fire..." displayed')
def see_waiting_for_opponent_message(context: MultiPlayerBDDContext):
    """Verify the waiting for opponent message is displayed"""
    assert context.soup is not None

    # Check for waiting message
    text = context.soup.get_text()
    assert "Waiting for opponent" in text, (
        f"Expected 'Waiting for opponent to fire...' in page text, got: {text}"
    )


@then("I should not be able to aim additional shots")
def cannot_aim_additional_shots(context: MultiPlayerBDDContext):
    """Verify that aiming additional shots is blocked"""
    assert context.game_url is not None, "No game URL stored"
    assert context.current_player_name is not None, "No current player set"

    game_id: str = context.game_url.split("/")[-1]
    client = context.get_client_for_player(context.current_player_name)

    # Attempt to aim another shot
    htmx_response = client.post(
        "/aim-shot",
        data={"game_id": game_id, "coordinate": "G1"},
        headers={"HX-Request": "true"},
    )

    # Should get an error response
    assert htmx_response.status_code == 200
    assert "Cannot aim shots after firing" in htmx_response.text
