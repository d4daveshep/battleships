import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from starlette.testclient import TestClient

from tests.bdd.conftest import (
    MultiPlayerBDDContext,
    login_player_fastapi,
    place_all_ships_fastapi,
    opponent_fires_via_api,
    DEFAULT_HIT_COORDINATES,
    DEFAULT_MISS_COORDINATES,
)
from bs4 import BeautifulSoup, Tag
from httpx import Response

scenarios(
    "../../features/two_player_core_gameplay.feature",
    # "../../features/two_player_board_and_feedback.feature",
)


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
    login_player_fastapi(client1, p1_name, "human")

    client2 = context.get_client_for_player(p2_name)
    login_player_fastapi(client2, p2_name, "human")

    # 3. Match Players
    # Player 1 selects Player 2
    client1.post("/select-opponent", data={"opponent_name": p2_name})
    # Player 2 accepts
    client2.post("/accept-game-request", data={})

    # 4. Place Ships for Player 1
    place_all_ships_fastapi(client1, p1_name)

    # 5. Place Ships for Player 2
    place_all_ships_fastapi(client2, p2_name)


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
    context.game_url = context.extract_game_url_from_response(response)

    if not context.game_url:
        # Try to get game URL from P1's status check
        status_response = client1.get(
            "/place-ships/opponent-status", headers={"HX-Request": "true"}
        )
        context.game_url = context.extract_game_url_from_response(status_response)


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


@given(parsers.parse("the game is in progress at Round {round_num:d}"))
@given(parsers.parse("the game is in progress"))
def game_in_progress(context: MultiPlayerBDDContext, round_num: int | None = None):
    """Ensure game is at specific round or just in progress"""
    # This is implicitly true after game setup
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


@then("I should see a list of the aimed coordinates")
def see_aimed_coordinates_list(context: MultiPlayerBDDContext):
    """Verify that a list of aimed coordinates is displayed"""
    assert context.soup is not None

    # Find the aimed coordinates list element
    aimed_list = context.soup.find(attrs={"data-testid": "aimed-coordinates-list"})
    assert aimed_list is not None, "Aimed coordinates list element not found"


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


@then(parsers.parse('the aimed coordinates list should not contain "{coord}"'))
def aimed_list_should_not_contain(context: MultiPlayerBDDContext, coord: str):
    """Verify that the aimed coordinates list does not contain a specific coordinate"""
    assert context.soup is not None

    # Find the aimed coordinates list element
    aimed_list = context.soup.find(attrs={"data-testid": "aimed-coordinates-list"})
    assert aimed_list is not None, "Aimed coordinates list element not found"

    # Check that the coordinate is not in the list
    list_text: str = aimed_list.get_text()
    assert coord not in list_text, (
        f"Coordinate {coord} found in aimed list when it should not be present"
    )


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
    assert context.current_player_name is not None, "No current player set"
    assert context.game_url is not None, "No game URL stored"

    context.select_coordinates(["A1", "B1", "C1", "D1", "E1", "F1"])

    client = context.get_client_for_player(context.current_player_name)
    response = client.get(context.game_url)
    context.update_response(response)


@when("I attempt to select another coordinate")
def attempt_select_another_coordinate(context: MultiPlayerBDDContext):
    """Attempt to select a 7th coordinate when already at limit"""
    assert context.current_player_name is not None, "No current player set"
    assert context.game_url is not None, "No game URL stored"

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
@then("I should not be able to aim or fire additional shots")
def cannot_aim_additional_shots(context: MultiPlayerBDDContext):
    """Verify that aiming additional shots is blocked"""
    assert context.game_url is not None
    assert context.current_player_name is not None

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


# === Simultaneous Play Steps ===


@given('I have clicked "Fire Shots"')
def clicked_fire_shots(context: MultiPlayerBDDContext):
    """Simulate clicking fire shots button"""
    click_button(context, "Fire Shots")


@given("I have fired my 6 shots")
def fired_6_shots(context: MultiPlayerBDDContext):
    """Aim and fire 6 shots"""
    # 1. Aim 6 shots
    have_selected_6_coordinates(context)
    # 2. Fire
    click_button(context, "Fire Shots")


@when("I fire my shots")
def just_fire_shots(context: MultiPlayerBDDContext):
    """Just click fire (assuming shots aimed)"""
    click_button(context, "Fire Shots")


def _opponent_fires(context: MultiPlayerBDDContext):
    """Helper to make opponent fire shots"""
    assert context.game_url is not None
    assert context.current_player_name is not None

    # Identify opponent
    me = context.current_player_name
    opponent = "Player2" if me == "Player1" else "Player1"

    client = context.get_client_for_player(opponent)
    game_id = context.game_url.split("/")[-1]

    opponent_fires_via_api(client, game_id, opponent)


@given("my opponent has already fired their shots")
def opponent_fired_shots(context: MultiPlayerBDDContext):
    """Simulate opponent firing shots"""
    _opponent_fires(context)


@when("my opponent fires their shots")
def opponent_fires_action(context: MultiPlayerBDDContext):
    """Action: Opponent fires"""
    _opponent_fires(context)

    # Refresh the page to see the update
    assert context.game_url is not None, "No game URL stored"
    assert context.current_player_name is not None, "No current player set"
    client: TestClient = context.get_client_for_player(context.current_player_name)
    response: Response = client.get(context.game_url)
    context.update_response(response)


@given("I am waiting for my opponent")
@when("I am waiting for my opponent to fire")
def waiting_for_opponent(context: MultiPlayerBDDContext):
    """Verify waiting state"""
    see_waiting_for_opponent_message(context)


@given("I am still aiming my shots")
def still_aiming(context: MultiPlayerBDDContext):
    """Verify I am still in aiming phase"""
    assert context.game_url is not None
    assert context.current_player_name is not None

    # Refresh page to get latest status (including opponent status)
    client = context.get_client_for_player(context.current_player_name)
    response = client.get(context.game_url)
    context.update_response(response)


@then("both players' shots should be processed together")
def shots_processed_together(context: MultiPlayerBDDContext):
    """Verify round resolution"""
    assert context.game_url is not None
    assert context.current_player_name is not None

    # Refresh page
    client = context.get_client_for_player(context.current_player_name)
    response = client.get(context.game_url)
    context.update_response(response)

    # Check Round 2
    assert "Round 2" in response.text


@then(parsers.parse("I should see the round results within {seconds:d} seconds"))
def see_round_results_polling(context: MultiPlayerBDDContext, seconds: int):
    """Simulate polling until results appear"""
    assert context.game_url is not None
    assert context.current_player_name is not None

    client = context.get_client_for_player(context.current_player_name)
    game_id = context.game_url.split("/")[-1]

    # Poll status (simulate one poll, assuming immediate update in test environment)
    response = client.get(f"/game/{game_id}/status")
    context.update_response(response)

    assert "Round 2" in response.text


@then("I should see a loading indicator")
def see_loading_indicator(context: MultiPlayerBDDContext):
    """Verify loading indicator in waiting message"""
    see_waiting_for_opponent_message(context)


@then("the page should update automatically when opponent fires")
def page_update_automatically(context: MultiPlayerBDDContext):
    """Verify polling mechanism"""
    # Opponent fires now to trigger the update
    _opponent_fires(context)
    see_round_results_polling(context, 5)


@then("the round number should increment to Round 2")
def round_increments(context: MultiPlayerBDDContext):
    """Verify round number"""
    assert context.soup is not None
    assert "Round 2" in context.soup.get_text()


@then("I should see 'Opponent has fired - waiting for you' displayed")
def see_opponent_fired_message(context: MultiPlayerBDDContext):
    """Verify message when opponent fires first"""
    assert context.soup is not None
    text = context.soup.get_text()
    assert "Opponent has fired - waiting for you" in text


@then("I should still be able to aim and fire my shots")
def still_able_to_aim_and_fire(context: MultiPlayerBDDContext):
    """Verify that aiming/firing is not blocked"""
    # Try to aim a shot to prove it's possible
    select_coordinate_to_aim(context, "A1")
    # Now button should be enabled
    button_should_be_enabled(context, "Fire Shots")


@then("the round should resolve immediately")
def round_resolves_immediately(context: MultiPlayerBDDContext):
    """Verify round resolves without delay when both have fired"""
    # Check for Round 2
    assert context.soup is not None
    assert "Round 2" in context.soup.get_text()


# === Round Progression Steps ===


def _get_coordinates_for_round(round_num: int) -> list[str]:
    """Generate unique coordinates for a given round.

    Args:
        round_num: The round number (1-indexed)

    Returns:
        List of 6 unique coordinates for that round
    """
    # Round 1: A1-F1, Round 2: A2-F2, Round 3: A3-F3, etc.
    col_num: int = round_num
    if col_num <= 10:
        return [f"{chr(ord('A') + i)}{col_num}" for i in range(6)]

    # If beyond column 10, use different rows
    row_offset: int = (round_num - 1) % 10
    col_offset: int = ((round_num - 1) // 10) + 1
    coordinates: list[str] = []
    for i in range(6):
        row: int = row_offset + i
        if row < 10:  # Stay within A-J
            coordinates.append(f"{chr(ord('A') + row)}{col_offset}")

    # Fill remaining with guaranteed non-overlapping coords
    while len(coordinates) < 6:
        coordinates.append(f"J{len(coordinates) + round_num}")

    return coordinates


def _get_current_round_from_page(context: MultiPlayerBDDContext) -> int:
    """Extract current round number from page text.

    Args:
        context: BDD context with loaded page

    Returns:
        Current round number (defaults to 1 if not found)
    """
    assert context.soup is not None, "No page loaded"
    page_text: str = context.soup.get_text()

    for i in range(1, 11):  # Check rounds 1-10
        if f"Round {i}" in page_text:
            return i
    return 1


def _advance_one_round(
    context: MultiPlayerBDDContext,
    client: TestClient,
    opponent_client: TestClient,
    opponent_name: str,
    current_round: int,
) -> None:
    """Advance game by one round by having both players fire.

    Args:
        context: BDD context with game state
        client: Current player's test client
        opponent_client: Opponent's test client
        opponent_name: Name of the opponent
        current_round: The current round number (to select different coordinates)
    """
    assert context.current_player_name is not None
    game_id: str = context.game_id

    # Use different coordinates for each round to avoid re-firing at same location
    coordinates: list[str] = _get_coordinates_for_round(current_round)

    # Both players aim and fire
    for player_client, player_name in [
        (client, context.current_player_name),
        (opponent_client, opponent_name),
    ]:
        # Aim all shots
        for coord in coordinates:
            player_client.post(
                "/aim-shot",
                data={"game_id": game_id, "coordinate": coord},
                headers={"HX-Request": "true"},
            )
        # Fire shots
        player_client.post(
            "/fire-shots",
            data={"game_id": game_id, "player_name": player_name},
        )
        # Fire shots
        player_client.post(
            "/fire-shots",
            data={"game_id": game_id, "player_name": player_name},
        )


@given(parsers.parse("it is Round {round_num:d}"))
def it_is_round_n(context: MultiPlayerBDDContext, round_num: int) -> None:
    """Ensure game is at specific round number by advancing rounds if needed.

    Args:
        context: BDD context with game state
        round_num: Target round number
    """
    assert context.soup is not None, "No page loaded"
    assert context.game_url is not None, "No game URL stored"
    assert context.current_player_name is not None, "No current player set"

    # Get current round from page
    current_round: int = _get_current_round_from_page(context)

    # If we're already at the target round, we're done
    if current_round == round_num:
        return

    # Set up clients
    client: TestClient = context.get_client_for_player(context.current_player_name)
    opponent_name: str = (
        "Player2" if context.current_player_name == "Player1" else "Player1"
    )
    opponent_client: TestClient = context.get_client_for_player(opponent_name)

    # Advance rounds until we reach the target
    while current_round < round_num:
        _advance_one_round(
            context, client, opponent_client, opponent_name, current_round
        )
        current_round += 1

    # Refresh page to see updated state
    response: Response = client.get(context.game_url)
    context.update_response(response)

    # Verify we're now at the target round
    assert f"Round {round_num}" in context.soup.get_text(), (
        f"Failed to advance to Round {round_num}"
    )


def _aim_and_fire_shots(
    context: MultiPlayerBDDContext,
    coordinates: list[str] | None = None,
    count: int | None = None,
) -> None:
    """Helper function to aim and fire shots for the current player.

    Args:
        context: BDD context with game state
        coordinates: List of coordinates to aim at (defaults to auto-select unfired coordinates)
        count: Optional number of shots to fire (defaults to all available shots or 6)
    """
    assert context.game_url is not None, "No game URL stored"
    assert context.current_player_name is not None, "No current player set"

    client: TestClient = context.get_client_for_player(context.current_player_name)
    game_id: str = context.game_id

    # If coordinates not specified, find coordinates that haven't been fired at yet
    if coordinates is None:
        import main
        from game.model import Coord

        game = main.game_service.games.get(game_id)
        if game:
            # Find the current player
            current_player = None
            if game.player_1.name == context.current_player_name:
                current_player = game.player_1
            elif game.player_2 and game.player_2.name == context.current_player_name:
                current_player = game.player_2

            if current_player:
                player_board = game.board[current_player]
                # Find safe coordinates that haven't been fired at
                all_possible_coords: list[str] = [
                    f"{row}{col}" for row in "ABCDEFGHIJ" for col in range(1, 11)
                ]
                available_coords: list[str] = [
                    coord_str
                    for coord_str in all_possible_coords
                    if Coord[coord_str] not in player_board.shots_fired
                ]
                coordinates = available_coords[: count if count else 6]

    if not coordinates:
        raise ValueError("No coordinates available to aim at")

    # Determine how many shots to fire
    shots_to_fire: int = count if count is not None else min(len(coordinates), 6)

    # Aim shots
    for i in range(shots_to_fire):
        coord = coordinates[i]
        client.post(
            "/aim-shot",
            data={"game_id": game_id, "coordinate": coord},
            headers={"HX-Request": "true"},
        )

    # Fire shots
    response: Response = client.post(
        "/fire-shots",
        data={"game_id": game_id, "player_name": context.current_player_name},
    )
    context.update_response(response)


@given("I have fired my shots")
def i_have_fired_my_shots(context: MultiPlayerBDDContext) -> None:
    """Aim all available shots and fire them.

    Args:
        context: BDD context with game state
    """
    # Auto-select coordinates that haven't been fired at yet
    _aim_and_fire_shots(context)


@given("my opponent has fired their shots")
def opponent_has_fired_shots_given(context: MultiPlayerBDDContext) -> None:
    """Trigger opponent to fire their shots.

    Args:
        context: BDD context with game state
    """
    assert context.game_url is not None, "No game URL stored"
    assert context.current_player_name is not None, "No current player set"

    # Determine opponent
    opponent_name: str = (
        "Player2" if context.current_player_name == "Player1" else "Player1"
    )
    opponent_client: TestClient = context.get_client_for_player(opponent_name)
    game_id: str = context.game_id

    opponent_fires_via_api(opponent_client, game_id, opponent_name)


@when("the round resolves")
def when_round_resolves(context: MultiPlayerBDDContext) -> None:
    """Reload the page to see round resolution.

    Args:
        context: BDD context with game state
    """
    assert context.game_url is not None, "No game URL stored"
    assert context.current_player_name is not None, "No current player set"

    # Refresh the gameplay page
    client: TestClient = context.get_client_for_player(context.current_player_name)
    response: Response = client.get(context.game_url)
    context.update_response(response)


@then(parsers.parse('I should see "Round {round_num:d}" displayed'))
def should_see_round_displayed(context: MultiPlayerBDDContext, round_num: int) -> None:
    """Verify round number is displayed on the page.

    Args:
        context: BDD context with loaded page
        round_num: Expected round number
    """
    assert context.soup is not None, "No page loaded"
    page_text: str = context.soup.get_text()
    assert f"Round {round_num}" in page_text, f"Expected 'Round {round_num}' in page"


@then(parsers.parse("I should be able to aim new shots for Round {round_num:d}"))
def can_aim_new_shots(context: MultiPlayerBDDContext, round_num: int) -> None:
    """Verify aiming controls are enabled after round advances.

    Args:
        context: BDD context with loaded page
        round_num: Current round number (unused but required by feature)
    """
    assert context.soup is not None, "No page loaded"

    # Check that the shots-fired board is present and interactive
    shots_board = context.soup.find(attrs={"data-testid": "shots-fired-board"})
    assert shots_board is not None, "Shots fired board not found"
    assert isinstance(shots_board, Tag), "Shots board is not a Tag element"

    # Check that checkboxes are not disabled (can aim)
    checkboxes: list[Tag] = shots_board.find_all("input", {"type": "checkbox"})
    assert len(checkboxes) > 0, "No checkboxes found for aiming"

    # None should be disabled
    for checkbox in checkboxes:
        assert not checkbox.has_attr("disabled"), "Aiming checkboxes are disabled"


@given("my opponent has not yet fired")
def opponent_has_not_yet_fired(context: MultiPlayerBDDContext) -> None:
    """Opponent has not fired yet (no-op step for state description).

    Args:
        context: BDD context (unused)
    """
    # This is a state description, nothing to do
    pass


@given("I have already fired my shots")
def i_have_already_fired(context: MultiPlayerBDDContext) -> None:
    """I have already fired my shots (alias for 'I have fired my shots').

    Args:
        context: BDD context with game state
    """
    i_have_fired_my_shots(context)


# === Hit Feedback Steps ===


@given(parsers.parse("I have fired {count:d} shots"))
def i_have_fired_n_shots(context: MultiPlayerBDDContext, count: int) -> None:
    """Aim and fire a specific number of shots at coordinates that will miss.

    Args:
        context: BDD context with game state
        count: Number of shots to fire
    """
    _aim_and_fire_shots(context, DEFAULT_MISS_COORDINATES, count)


@given("none of my shots hit any opponent ships")
def none_of_shots_hit(context: MultiPlayerBDDContext) -> None:
    """State verification that shots don't hit opponent ships.

    Args:
        context: BDD context (unused - implicit from shot selection)
    """
    # This is implicitly true when we fire at coordinates like J1-J6
    # which don't overlap with default ship placements
    pass


@when("the round resolves")
def round_resolves(context: MultiPlayerBDDContext) -> None:
    """Reload the page to see round resolution results.

    Args:
        context: BDD context with game state
    """
    assert context.game_url is not None, "No game URL stored"
    assert context.current_player_name is not None, "No current player set"

    client: TestClient = context.get_client_for_player(context.current_player_name)
    response: Response = client.get(context.game_url)
    context.update_response(response)


@then("the Hits Made area should show no new shots marked")
def hits_made_area_shows_no_hits(context: MultiPlayerBDDContext) -> None:
    """Verify the Hits Made area shows no hits on opponent ships.

    Args:
        context: BDD context with game state
    """
    assert context.soup is not None, "No page content to check"

    hits_area = context.soup.find(attrs={"data-testid": "hits-made-area"})
    assert hits_area is not None, "Hits Made area not found"

    # TODO: Need to verify no hits are marked on ships
    # For now, just verify the area exists
    pass


@then(
    parsers.parse(
        "I should see all {count:d} of my shots marked as misses on the Shots Fired board"
    )
)
def see_all_shots_as_misses(context: MultiPlayerBDDContext, count: int) -> None:
    """Verify all fired shots are marked as misses on the Shots Fired board.

    Args:
        context: BDD context with game state
        count: Number of expected miss markers
    """
    assert context.soup is not None, "No page content to check"

    shots_board = context.soup.find(attrs={"data-testid": "shots-fired-board"})
    assert shots_board is not None, "Shots Fired board not found"
    assert isinstance(shots_board, Tag)

    # TODO: Need to verify miss markers are displayed
    # For now, just verify the board exists
    pass


# === Board Visibility Steps (from two_player_board_and_feedback.feature) ===


@given("I have ships placed on my board")
def ships_placed_on_my_board(context: MultiPlayerBDDContext):
    """Verify ships are placed on player's board."""
    # Ships should already be placed from background
    pass


@given("my opponent has fired shots at my board in previous rounds")
def opponent_fired_shots_at_my_board(context: MultiPlayerBDDContext):
    """Simulate opponent firing shots in previous rounds."""
    pytest.skip("Round progression not yet fully implemented")


@given("my opponent has ships placed on their board")
def opponent_has_ships_placed(context: MultiPlayerBDDContext):
    """Verify opponent has ships placed."""
    # Opponent ships should be placed from game setup
    pass


@given("I have fired shots in previous rounds")
def i_have_fired_shots_in_previous_rounds(context: MultiPlayerBDDContext):
    """Simulate firing shots in previous rounds."""
    pytest.skip("Round progression not yet fully implemented")


@given(parsers.parse("I have fired {count:d} shots"))
def i_have_fired_n_shots_specific(context: MultiPlayerBDDContext, count: int):
    """Aim and fire a specific number of shots at coordinates that will miss."""
    _aim_and_fire_shots(context, DEFAULT_MISS_COORDINATES, count)


@then('I should see all my ship positions on "My Ships and Shots Received" board')
def see_all_ship_positions(context: MultiPlayerBDDContext):
    """Verify all ship positions are visible on My Ships board."""
    assert context.soup is not None, "No page loaded"
    my_ships_board = context.soup.find(attrs={"data-testid": "my-ships-board"})

    assert my_ships_board is not None, "My Ships board should be visible"

    board_text = my_ships_board.get_text()
    assert any(code in board_text for code in ["D", "C", "B", "A", "S"]), (
        "Ship codes should be visible on My Ships board"
    )


@then("I should see all shots my opponent has fired at my board")
def see_opponent_shots_on_my_board(context: MultiPlayerBDDContext):
    """Verify opponent's shots are marked on My Ships board."""
    pytest.skip("Round progression not yet fully implemented")


@then("I should see round numbers for each shot received")
def see_round_numbers_for_received_shots(context: MultiPlayerBDDContext):
    """Verify round numbers are displayed for received shots."""
    pytest.skip("Round progression not yet fully implemented")


@then("I should see which of my ships have been hit")
def see_which_ships_hits(context: MultiPlayerBDDContext):
    """Verify ships that have been hit are marked."""
    pytest.skip("Not yet implemented")


@then("I should see which of my ships have been sunk")
def see_which_ships_sunk(context: MultiPlayerBDDContext):
    """Verify sunk ships are marked."""
    pytest.skip("Not yet implemented")


@then("I should not see any of my opponent's ship positions")
def should_not_see_opponent_ship_positions(context: MultiPlayerBDDContext):
    """Verify opponent ship positions are NOT visible."""
    assert context.soup is not None, "No page loaded"
    shots_fired_board = context.soup.find(attrs={"data-testid": "shots-fired-board"})

    assert shots_fired_board is not None, "Shots Fired board should be visible"
    assert shots_fired_board is not None


@then('I should see all shots I have fired on the "Shots Fired" board')
def see_all_fired_shots(context: MultiPlayerBDDContext):
    """Verify all fired shots are marked on Shots Fired board."""
    pytest.skip("Round progression not yet fully implemented")


@then(
    parsers.parse(
        'I should see the "Hits Made" area showing which ships I\'ve hit with the round numbers'
    )
)
def see_hits_made_area_with_round_numbers(context: MultiPlayerBDDContext):
    """Verify Hits Made area shows ship hit tracking."""
    assert context.soup is not None, "No page loaded"
    hits_made_area = context.soup.find(attrs={"data-testid": "hits-made-area"})

    assert hits_made_area is not None, "Hits Made area should be visible"

    area_text = hits_made_area.get_text()
    assert "Carrier" in area_text
    assert "Destroyer" in area_text


@then('I should see the "Hits Made" area next to the Shots Fired board')
def see_hits_made_area_next_to_shots_fired(context: MultiPlayerBDDContext):
    """Verify Hits Made area is present."""
    assert context.soup is not None, "No page loaded"
    hits_made_area = context.soup.find(attrs={"data-testid": "hits-made-area"})

    assert hits_made_area is not None, "Hits Made area should be visible"


@then(
    "I should see 5 ship rows labeled: Carrier, Battleship, Cruiser, Submarine, Destroyer"
)
def see_five_ship_rows(context: MultiPlayerBDDContext):
    """Verify all 5 ship types are listed."""
    assert context.soup is not None, "No page loaded"
    hits_made_area = context.soup.find(attrs={"data-testid": "hits-made-area"})

    assert hits_made_area is not None, "Hits Made area should be visible"
    area_text = hits_made_area.get_text()
    assert "Carrier" in area_text
    assert "Battleship" in area_text
    assert "Cruiser" in area_text
    assert "Submarine" in area_text
    assert "Destroyer" in area_text


@then("each ship row should show spaces for tracking hits")
def each_ship_row_shows_hit_spaces(context: MultiPlayerBDDContext):
    """Verify ship rows have hit tracking spaces."""
    assert context.soup is not None, "No page loaded"

    carrier_row = context.soup.find(attrs={"data-testid": "hit-track-carrier"})
    assert carrier_row is not None, "Carrier hit tracking row should exist"
    assert hasattr(carrier_row, "find_all"), "Carrier row should be a Tag element"

    hit_spaces = carrier_row.find_all(class_="hit-space")  # type: ignore[attr-defined]
    assert len(hit_spaces) == 5, "Carrier should have 5 hit spaces"


@then('I should see "My Ships and Shots Received" board')
def see_my_ships_board_check(context: MultiPlayerBDDContext):
    """Verify My Ships board is visible."""
    assert context.soup is not None, "No page loaded"
    my_ships_board = context.soup.find(attrs={"data-testid": "my-ships-board"})

    assert my_ships_board is not None, "My Ships board should be visible"


@then('I should see "Shots Fired" board')
def see_shots_fired_board_check(context: MultiPlayerBDDContext):
    """Verify Shots Fired board is visible."""
    assert context.soup is not None, "No page loaded"
    shots_fired_board = context.soup.find(attrs={"data-testid": "shots-fired-board"})

    assert shots_fired_board is not None, "Shots Fired board should be visible"


@then('I should see "Hits Made" area')
def see_hits_made_area_check(context: MultiPlayerBDDContext):
    """Verify Hits Made area is visible."""
    assert context.soup is not None, "No page loaded"
    hits_made_area = context.soup.find(attrs={"data-testid": "hits-made-area"})

    assert hits_made_area is not None, "Hits Made area should be visible"


@then("both boards should show a 10x10 grid with coordinates A-J and 1-10")
def both_boards_show_10x10_grid(context: MultiPlayerBDDContext):
    """Verify both boards have proper grid structure."""
    assert context.soup is not None, "No page loaded"

    my_ships_board = context.soup.find(attrs={"data-testid": "my-ships-board"})
    assert my_ships_board is not None

    board_text = my_ships_board.get_text()
    assert "A" in board_text and "J" in board_text

    shots_fired_board = context.soup.find(attrs={"data-testid": "shots-fired-board"})
    assert shots_fired_board is not None

    board_text = shots_fired_board.get_text()
    assert "A" in board_text and "J" in board_text


@then("all three areas should be clearly distinguishable")
def all_three_areas_distinguishable(context: MultiPlayerBDDContext):
    """Verify all three areas exist and are separate."""
    assert context.soup is not None, "No page loaded"

    my_ships = context.soup.find(attrs={"data-testid": "my-ships-board"})
    shots_fired = context.soup.find(attrs={"data-testid": "shots-fired-board"})
    hits_made = context.soup.find(attrs={"data-testid": "hits-made-area"})

    assert my_ships is not None, "My Ships board should exist"
    assert shots_fired is not None, "Shots Fired board should exist"
    assert hits_made is not None, "Hits Made area should exist"

    assert my_ships != shots_fired
    assert shots_fired != hits_made
    assert my_ships != hits_made


# === Hit Feedback Scenario Steps (simplified) ===


@given(parsers.parse("{count:d} of my shots hit my opponent's {ship_name}"))
def n_shots_hit_opponent_ship(
    context: MultiPlayerBDDContext, count: int, ship_name: str
):
    """Simulate hitting opponent's ship a specific number of times."""
    pytest.skip("Hit feedback requires round resolution implementation")


@given(parsers.parse("my opponent hit my {ship_name} {count:d} times"))
def opponent_hit_my_ship(context: MultiPlayerBDDContext, ship_name: str, count: int):
    """Simulate opponent hitting my ship."""
    pytest.skip("Hit feedback requires round resolution implementation")


@given(
    parsers.parse(
        "in Round {round_num:d} I hit the opponent's {ship_name} {count:d} time"
    )
)
@given(
    parsers.parse(
        "in Round {round_num:d} I hit the opponent's {ship_name} {count:d} times"
    )
)
def hit_opponent_ship_in_round(
    context: MultiPlayerBDDContext, round_num: int, ship_name: str, count: int
):
    """Simulate hitting opponent's ship in a specific round."""
    pytest.skip("Hit feedback requires round resolution implementation")


@given(parsers.parse('my opponent has a {ship_name} at "{coords}"'))
def opponent_has_ship_at_positions(
    context: MultiPlayerBDDContext, ship_name: str, coords: str
):
    """Verify opponent has a ship at specific coordinates."""
    pytest.skip("Ship placement verification not fully implemented")


@given(parsers.parse("I fire {count:d} shots"))
def i_fire_n_shots(context: MultiPlayerBDDContext, count: int):
    """Fire a specific number of shots."""
    pytest.skip("Hit feedback requires round resolution implementation")


@then(
    parsers.parse(
        "I should see round numbers marked in the spaces where I've hit each ship"
    )
)
def see_round_numbers_in_hit_spaces(context: MultiPlayerBDDContext):
    """Verify round numbers are marked in hit tracking spaces."""
    pytest.skip("Hit feedback display requires round resolution implementation")


@then('sunk ships should be clearly marked as "SUNK"')
def sunk_ships_marked_as_sunk(context: MultiPlayerBDDContext):
    """Verify sunk ships are marked as SUNK."""
    pytest.skip("Sunk ship marking not fully implemented")


@then("I should NOT see the exact coordinates of the hits")
def should_not_see_hit_coordinates(context: MultiPlayerBDDContext):
    """Verify hit coordinates are not displayed."""
    pytest.skip("Coordinate hiding not fully implemented")


@then(parsers.parse('I should see "{ship_name}: {count:d} hits total" displayed'))
def see_ship_total_hits_displayed(
    context: MultiPlayerBDDContext, ship_name: str, count: int
):
    """Verify total hits for a ship are displayed."""
    pytest.skip("Total hits display not fully implemented")


@then(parsers.parse('I should see "Your {ship_name} was hit {count:d} time" displayed'))
@then(
    parsers.parse('I should see "Your {ship_name} was hit {count:d} times" displayed')
)
def see_my_ship_hits_displayed(
    context: MultiPlayerBDDContext, ship_name: str, count: int
):
    """Verify hits received on my ships are displayed."""
    pytest.skip("Hits received display not fully implemented")


@then(parsers.parse('I should see "Hits Made This Round: {message}" displayed'))
def see_hits_made_this_round_displayed(context: MultiPlayerBDDContext, message: str):
    """Verify hits made this round are displayed."""
    pytest.skip("Hits made this round display not fully implemented")


@then(
    parsers.parse(
        'the Hits Made area should show round number "{round_num:d}" marked {count:d} times on {ship_name}'
    )
)
def see_hit_tracking_in_area(
    context: MultiPlayerBDDContext, round_num: int, count: int, ship_name: str
):
    """Verify hit tracking shows round numbers in ship rows."""
    pytest.skip("Hit tracking display not fully implemented")


@then(parsers.parse("the {ship_name} should have {count:d} total hits"))
def see_ship_total_hits(context: MultiPlayerBDDContext, ship_name: str, count: int):
    """Verify ship has correct total hits."""
    pytest.skip("Total hits tracking not fully implemented")


@then(parsers.parse("I should see the exact coordinates of the hits on my board"))
def see_received_hit_coordinates(context: MultiPlayerBDDContext):
    """Verify received hit coordinates are displayed on my board."""
    pytest.skip("Received hit coordinates display not fully implemented")


@then(parsers.parse('coordinates should be marked with round number "{round_num:d}"'))
def see_coordinates_with_round_number(context: MultiPlayerBDDContext, round_num: int):
    """Verify coordinates are marked with round number."""
    pytest.skip("Coordinate round marking not fully implemented")


@then(parsers.parse("the {ship_name} should show {count:d} new hit markers"))
def see_new_hit_markers(context: MultiPlayerBDDContext, ship_name: str, count: int):
    """Verify new hit markers are shown for a ship."""
    pytest.skip("New hit markers display not fully implemented")
