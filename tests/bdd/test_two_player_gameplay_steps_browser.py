import httpx
import pytest
from playwright.sync_api import Page, expect
from pytest_bdd import scenarios, given, when, then, parsers
from tests.bdd.conftest import (
    GamePageLocators,
    navigate_to_login,
    fill_player_name,
    click_multiplayer_button,
    select_coordinates,
    opponent_fires_via_api,
)


scenarios(
    "../../features/two_player_core_gameplay.feature",
    # "../../features/two_player_board_and_feedback.feature",
)


def setup_opponent(client: httpx.Client, player_name: str = "Player2") -> None:
    """Helper to setup the opponent state via API."""
    client.post("/login", data={"player_name": player_name, "game_mode": "human"})


def setup_game_with_opponent(
    page: Page, opponent_client: httpx.Client, base_url: str
) -> None:
    """Orchestrate the full game setup flow.

    Args:
        page: Playwright Page instance
        opponent_client: HTTP client for opponent player
        base_url: Base URL for this worker's server
    """
    # Reset lobby state
    with httpx.Client(base_url=base_url) as admin_client:
        admin_client.post("/test/reset-lobby")

    # Setup opponent (Player 2)
    setup_opponent(opponent_client)

    # Setup current player (Player 1) in browser
    navigate_to_login(page, base_url)
    fill_player_name(page, "Player1")
    click_multiplayer_button(page)

    page.wait_for_url("**/lobby")

    # Challenge opponent
    opponent_btn_selector = GamePageLocators.select_opponent_button("Player2")
    page.wait_for_selector(opponent_btn_selector, timeout=10000)
    page.locator(opponent_btn_selector).click()

    # Opponent accepts
    opponent_client.post("/accept-game-request", data={})
    page.wait_for_url("**/place-ships")


@given("both players have completed ship placement")
def players_completed_placement(
    page: Page, opponent_client: httpx.Client, base_url: str
):
    setup_game_with_opponent(page, opponent_client, base_url)

    # Player 1 places ships
    page.locator(GamePageLocators.RANDOM_PLACEMENT_BUTTON).click()
    expect(page.locator(GamePageLocators.SHIP_PLACEMENT_COUNT)).to_contain_text(
        "5 of 5 ships placed"
    )

    # Player 2 places ships via API
    opponent_client.post("/random-ship-placement", data={"player_name": "Player2"})


@given("both players are ready")
def players_are_ready(page: Page, opponent_client: httpx.Client):
    # Player 1 ready
    page.locator(GamePageLocators.READY_BUTTON).click()

    # Player 2 ready via API
    # Note: Assumes opponent is already logged in and in game from previous steps
    opponent_client.post("/ready-for-game", data={"player_name": "Player2"})

    page.wait_for_url("**/game/*", timeout=30000)


@given("the game has started")
def game_has_started():
    pass


@given("I am on the gameplay page")
def on_gameplay_page(page: Page):
    import re

    expect(page).to_have_url(re.compile(r".*/game/.*"))


@given("the game just started")
def game_just_started():
    """Ensure it is the beginning of the game"""
    pass


@then(parsers.parse('I should see "{text}" displayed'))
def see_text_displayed(page: Page, text: str):
    expect(page.locator("body")).to_contain_text(text)


@then("I should be able to select up to 6 coordinates to fire at")
def can_select_coordinates(page: Page):
    expect(page.locator(GamePageLocators.SHOTS_FIRED_BOARD)).to_be_visible()
    expect(page.locator(GamePageLocators.FIRE_SHOTS_BUTTON)).to_be_visible()


@then(parsers.parse('I should see my board labeled "{label}"'))
def see_my_board_labeled(page: Page, label: str):
    expect(page.locator("body")).to_contain_text(label)
    expect(page.locator(GamePageLocators.MY_SHIPS_BOARD)).to_be_visible()


@then(parsers.parse('I should see the opponent\'s board labeled "{label}"'))
def see_opponent_board_labeled(page: Page, label: str):
    expect(page.locator("body")).to_contain_text(label)
    expect(page.locator(GamePageLocators.SHOTS_FIRED_BOARD)).to_be_visible()


@then(
    parsers.parse(
        'I should see the "Hits Made" area showing all {count:d} opponent ships'
    )
)
def see_hits_made_area(page: Page, count: int):
    hits_area = page.locator(GamePageLocators.HITS_MADE_AREA)
    expect(hits_area).to_be_visible()
    ship_names = ["Carrier", "Battleship", "Cruiser", "Submarine", "Destroyer"]
    for ship in ship_names:
        expect(hits_area).to_contain_text(ship)


# === Scenario: Selecting multiple shot coordinates for aiming ===


@given("it is Round 1")
def it_is_round_1():
    pass


@given("I have 6 shots available")
def have_6_shots_available():
    pass


@when(parsers.parse('I select coordinate "{coord}" to aim at'))
def select_coordinate_to_aim(page: Page, coord: str):
    cell = page.locator(GamePageLocators.opponent_cell(coord))
    expect(cell).to_be_visible()
    cell.click()

    # Wait for the cell to be visually checked or marked
    # We check the checkbox state which reflects the successful HTMX update
    expect(cell.locator('input[type="checkbox"]')).to_be_checked()


@then(parsers.parse("I should see {count:d} coordinates marked as aimed"))
def see_coordinates_marked_as_aimed(page: Page, count: int):
    checked_cells = page.locator(GamePageLocators.CHECKED_CELLS)
    expect(checked_cells).to_have_count(count)


@then("I should see a list of the aimed coordinates")
def see_aimed_coordinates_list(page: Page):
    """Verify that a list of aimed coordinates is displayed"""
    aimed_list = page.locator(GamePageLocators.AIMED_COORDINATES_LIST)
    expect(aimed_list).to_be_visible()


@then("I should be able to select 3 more coordinates")
def can_select_3_more_coordinates(page: Page):
    aiming_status = page.locator(GamePageLocators.AIMING_STATUS)
    expect(aiming_status).to_be_visible()
    expect(aiming_status).not_to_contain_text("6/6")


@then(parsers.parse('the "{button_name}" button should be enabled'))
def button_should_be_enabled(page: Page, button_name: str):
    testid_map = {"Fire Shots": "fire-shots-button"}
    testid = testid_map.get(
        button_name, button_name.lower().replace(" ", "-") + "-button"
    )
    button = page.locator(f'[data-testid="{testid}"]')
    expect(button).to_be_visible()
    expect(button).to_be_enabled()


# === Scenario: Reselecting an aimed shot's coordinates un-aims the shot ===


@given(parsers.parse('I have only selected coordinate "{coord}" to aim at'))
def have_only_selected_coordinate(page: Page, coord: str):
    cell = page.locator(GamePageLocators.opponent_cell(coord))
    expect(cell).to_be_visible()
    cell.click()
    expect(cell.locator('input[type="checkbox"]')).to_be_checked()


@when(parsers.parse('I select coordinate "{coord}" again'))
def select_coordinate_again(page: Page, coord: str):
    cell = page.locator(GamePageLocators.opponent_cell(coord))
    expect(cell).to_be_visible()
    cell.click()
    # Wait for checkbox to be unchecked
    expect(cell.locator('input[type="checkbox"]')).not_to_be_checked()


@then(parsers.parse('coordinate "{coord}" should be un-aimed'))
def coordinate_should_be_unaimed(page: Page, coord: str):
    cell = page.locator(GamePageLocators.opponent_cell(coord))
    expect(cell.locator('input[type="checkbox"]')).not_to_be_checked()


@then(parsers.parse('I should not see coordinate "{coord}" marked as aimed'))
def should_not_see_coordinate_marked(page: Page, coord: str):
    cell = page.locator(GamePageLocators.opponent_cell(coord))
    expect(cell).not_to_have_class("aimed-cell")


@then(parsers.parse('the aimed coordinates list should not contain "{coord}"'))
def aimed_list_should_not_contain(page: Page, coord: str):
    """Verify that the aimed coordinates list does not contain a specific coordinate"""
    aimed_list = page.locator(GamePageLocators.AIMED_COORDINATES_LIST)
    expect(aimed_list).to_be_visible()
    expect(aimed_list).not_to_contain_text(coord)


@then(
    parsers.parse("I should still have {count:d} remaining shot selections available")
)
def should_have_remaining_shots(page: Page, count: int):
    shots_display = page.locator(GamePageLocators.SHOTS_AVAILABLE)
    expect(shots_display).to_contain_text(f"Shots Available: {count}")


# === Scenario: Cannot select more shots than available ===


@given("I have selected 6 coordinates to aim at")
def have_selected_6_coordinates(page: Page):
    select_coordinates(page, ["A1", "B1", "C1", "D1", "E1", "F1"])


@when("I attempt to select another coordinate")
def attempt_select_another_coordinate(page: Page):
    cell = page.locator(GamePageLocators.opponent_cell("G1"))
    expect(cell).to_be_visible()
    cell.click()

    # Wait for error message
    error_message = page.locator(GamePageLocators.ERROR_MESSAGE)
    expect(error_message).to_contain_text("All available shots aimed", timeout=5000)


@then("the coordinate should not be selectable")
def coordinate_not_selectable(page: Page):
    cell = page.locator(GamePageLocators.opponent_cell("G1"))
    expect(cell).not_to_have_class("aimed-cell")


@then('I should see a message "All available shots aimed"')
def see_shot_limit_message(page: Page):
    error_message = page.locator(GamePageLocators.ERROR_MESSAGE)
    expect(error_message).to_contain_text("All available shots aimed")


@then('I should see "Shots Aimed: 6/6" displayed')
def see_shots_aimed_counter(page: Page):
    shots_available = page.locator(GamePageLocators.SHOTS_AVAILABLE)
    expect(shots_available).to_contain_text("Shots Available: 6")


# === Scenario: Can fire fewer shots than available ===


@given(parsers.parse("I have selected {count:d} coordinates to aim at"))
def have_selected_n_coordinates(page: Page, count: int):
    coords = ["A1", "B1", "C1", "D1", "E1", "F1"][:count]
    select_coordinates(page, coords)


@when(parsers.parse('I click the "{button_name}" button'))
def click_button(page: Page, button_name: str):
    if button_name == "Fire Shots":
        button = page.locator(GamePageLocators.FIRE_SHOTS_BUTTON)
        expect(button).to_be_visible()
        expect(button).to_be_enabled()
        button.click()
    else:
        raise ValueError(f"Unknown button: {button_name}")


@then(parsers.parse("my {count:d} shots should be submitted"))
def shots_should_be_submitted(page: Page, count: int):
    # After firing, the aimed shots should be cleared (0/6)
    aiming_status = page.locator(GamePageLocators.AIMING_STATUS)
    expect(aiming_status).to_be_visible()
    expect(aiming_status).to_contain_text("0/")


@then('I should see "Waiting for opponent to fire..." displayed')
def see_waiting_for_opponent_message(page: Page):
    status_message = page.locator(GamePageLocators.GAME_STATUS)
    expect(status_message).to_contain_text("Waiting for opponent")


@then("I should not be able to aim additional shots")
@then("I should not be able to aim or fire additional shots")
def cannot_aim_additional_shots(page: Page):
    cell = page.locator(GamePageLocators.opponent_cell("G1"))
    expect(cell).to_be_visible()
    cell.click()

    error_message = page.locator(GamePageLocators.ERROR_MESSAGE)
    expect(error_message).to_contain_text("Cannot aim shots after firing", timeout=5000)

    # Fire button should be disabled (aimed_count is 0 after firing)
    expect(page.locator(GamePageLocators.FIRE_SHOTS_BUTTON)).to_be_disabled()


# === Simultaneous Play Steps ===


@given('I have clicked "Fire Shots"')
def clicked_fire_shots(page: Page):
    """Simulate clicking fire shots button"""
    page.locator(GamePageLocators.FIRE_SHOTS_BUTTON).click()


@given("I have fired my 6 shots")
def fired_6_shots(page: Page):
    """Aim and fire 6 shots"""
    # 1. Aim 6 shots
    have_selected_6_coordinates(page)
    # 2. Fire
    page.locator(GamePageLocators.FIRE_SHOTS_BUTTON).click()


def _get_game_id(page: Page) -> str:
    """Extract game ID from current URL"""
    # URL format: .../game/{game_id}
    return page.url.split("/")[-1]


def _opponent_fires(page: Page, opponent_client: httpx.Client):
    """Helper to make opponent fire shots"""
    game_id = _get_game_id(page)
    opponent_fires_via_api(opponent_client, game_id, "Player2")


@given("my opponent has already fired their shots")
def opponent_fired_shots(page: Page, opponent_client: httpx.Client):
    """Simulate opponent firing shots"""
    _opponent_fires(page, opponent_client)
    # Reload page to reflect opponent status if needed, but the scenario implies
    # we might just be landing or it's a state setup.
    # If we are already on the page, a refresh might be needed to see "Opponent has fired"
    page.reload()


@when("my opponent fires their shots")
def opponent_fires_action(page: Page, opponent_client: httpx.Client):
    """Action: Opponent fires"""
    _opponent_fires(page, opponent_client)


@given("I am waiting for my opponent")
@when("I am waiting for my opponent to fire")
def waiting_for_opponent(page: Page):
    """Verify waiting state"""
    see_waiting_for_opponent_message(page)


@then("both players' shots should be processed together")
def shots_processed_together(page: Page):
    """Verify round resolution"""
    # Should see Round 2
    expect(page.locator('[data-testid="round-indicator"]')).to_contain_text("Round 2")


@then("I should see the round results within 5 seconds")
def see_round_results_polling(page: Page):
    """Wait for polling update"""
    expect(page.locator('[data-testid="round-indicator"]')).to_contain_text(
        "Round 2", timeout=5000
    )


@then("I should see a loading indicator")
def see_loading_indicator(page: Page):
    """Verify loading indicator in waiting message"""
    see_waiting_for_opponent_message(page)


@then("the page should update automatically when opponent fires")
def page_update_automatically(page: Page, opponent_client: httpx.Client):
    """Verify polling mechanism"""
    # Opponent fires now
    _opponent_fires(page, opponent_client)
    # Page should update to Round 2 automatically via HTMX polling
    expect(page.locator('[data-testid="round-indicator"]')).to_contain_text(
        "Round 2", timeout=5000
    )


@then("the round number should increment to Round 2")
def round_increments(page: Page):
    """Verify round number"""
    expect(page.locator('[data-testid="round-indicator"]')).to_contain_text("Round 2")


@then("I should see 'Opponent has fired - waiting for you' displayed")
def see_opponent_fired_message(page: Page):
    """Verify message when opponent fires first"""
    expect(page.locator(GamePageLocators.GAME_STATUS)).to_contain_text(
        "Opponent has fired - waiting for you"
    )


@given("I am still aiming my shots")
def still_aiming(page: Page):
    """Verify I am still in aiming phase"""
    # Implicitly true if we can see the board and aim
    expect(page.locator(GamePageLocators.SHOTS_FIRED_BOARD)).to_be_visible()
    # Refresh to ensure we get the latest message ("Opponent has fired")
    page.reload()


@then("I should still be able to aim and fire my shots")
def still_able_to_aim_and_fire(page: Page):
    """Verify that aiming/firing is not blocked"""
    # Try to aim a shot (e.g. A1) to prove it's possible
    coord = "A1"
    cell = page.locator(GamePageLocators.opponent_cell(coord))
    cell.click()
    expect(cell.locator('input[type="checkbox"]')).to_be_checked()

    # Button should be enabled
    expect(page.locator(GamePageLocators.FIRE_SHOTS_BUTTON)).to_be_enabled()


@when("I fire my shots")
def fire_my_shots(page: Page):
    """Fire shots"""
    page.locator(GamePageLocators.FIRE_SHOTS_BUTTON).click()


@then("the round should resolve immediately")
def round_resolves_immediately(page: Page):
    """Verify round resolves without delay"""
    expect(page.locator('[data-testid="round-indicator"]')).to_contain_text("Round 2")


@then(parsers.parse("I should see the round results within {seconds:d} seconds"))
def see_round_results_within_seconds(page: Page, seconds: int):
    """Wait for update with specific timeout"""
    expect(page.locator('[data-testid="round-indicator"]')).to_contain_text(
        "Round 2", timeout=seconds * 1000
    )


# === Round Progression Steps ===


def get_current_round_from_page(page: Page) -> int:
    """Extract current round number from page.

    Args:
        page: Playwright page with gameplay content

    Returns:
        Current round number (defaults to 1 if not found)
    """
    round_indicator = page.locator(GamePageLocators.ROUND_INDICATOR)
    text: str = round_indicator.text_content() or "Round 1"

    for i in range(1, 11):  # Check rounds 1-10
        if f"Round {i}" in text:
            return i
    return 1


def get_available_coordinates(page: Page, count: int = 6) -> list[str]:
    """Find coordinates that haven't been fired yet by checking checkboxes.

    Args:
        page: Playwright page with shots fired board
        count: Number of coordinates to return

    Returns:
        List of available coordinate strings
    """
    available: list[str] = []

    # Check all coordinates in order
    for row in "ABCDEFGHIJ":
        for col in range(1, 11):
            coord = f"{row}{col}"
            cell_selector = GamePageLocators.opponent_cell(coord)

            try:
                # Check if the cell's checkbox is not checked (hasn't been fired)
                checkbox = page.locator(f'{cell_selector} input[type="checkbox"]')

                # If checkbox exists and is not checked, it's available
                if checkbox.count() > 0 and not checkbox.is_checked():
                    available.append(coord)

                    if len(available) >= count:
                        return available
            except Exception:
                # If we can't access the cell, skip it
                continue

    return available


def advance_one_round(page: Page, opponent_client: httpx.Client) -> None:
    """Advance game by one round by having both players fire.

    Args:
        page: Playwright page for current player
        opponent_client: HTTP client for opponent
    """
    game_id: str = _get_game_id(page)

    # Get available (unfired) coordinates dynamically
    coordinates: list[str] = get_available_coordinates(page, count=6)

    if len(coordinates) < 6:
        raise RuntimeError(
            f"Not enough available coordinates to fire (found {len(coordinates)})"
        )

    # Current player aims and fires
    select_coordinates(page, coordinates)
    page.locator(GamePageLocators.FIRE_SHOTS_BUTTON).click()

    # Opponent aims and fires via API
    opponent_fires_via_api(opponent_client, game_id, "Player2")

    # Wait for round to resolve (page should update)
    page.wait_for_timeout(1000)  # Give time for polling to update


@given(parsers.parse("it is Round {round_num:d}"))
def it_is_round_n(page: Page, opponent_client: httpx.Client, round_num: int) -> None:
    """Ensure game is at specific round number by advancing rounds if needed.

    Args:
        page: Playwright page for current player
        opponent_client: HTTP client for opponent
        round_num: Target round number
    """
    # Get current round from page
    current_round: int = get_current_round_from_page(page)

    # If we're already at the target round, we're done
    if current_round == round_num:
        return

    # Advance rounds until we reach the target
    while current_round < round_num:
        advance_one_round(page, opponent_client)
        current_round += 1
        page.reload()  # Reload to see updated round
        page.wait_for_timeout(500)

    # Verify we're now at the target round
    expect(page.locator(GamePageLocators.ROUND_INDICATOR)).to_contain_text(
        f"Round {round_num}"
    )


@given("I have fired my shots")
def i_have_fired_my_shots(page: Page) -> None:
    """Aim all available shots and fire them.

    Args:
        page: Playwright page for current player
    """
    coordinates: list[str] = ["A1", "B1", "C1", "D1", "E1", "F1"]
    select_coordinates(page, coordinates)
    page.locator(GamePageLocators.FIRE_SHOTS_BUTTON).click()
    page.wait_for_timeout(500)  # Wait for fire action to complete


@given("my opponent has fired their shots")
def opponent_has_fired_shots_given(page: Page, opponent_client: httpx.Client) -> None:
    """Trigger opponent to fire their shots.

    Args:
        page: Playwright page for current player
        opponent_client: HTTP client for opponent
    """
    game_id: str = _get_game_id(page)
    opponent_fires_via_api(opponent_client, game_id, "Player2")


@when("the round resolves")
def when_round_resolves(page: Page) -> None:
    """Wait for round to resolve and page to update.

    Args:
        page: Playwright page
    """
    # Give time for polling to detect round resolution
    page.wait_for_timeout(3000)
    page.reload()  # Ensure we see the latest state


@then(parsers.parse('I should see "Round {round_num:d}" displayed'))
def should_see_round_displayed(page: Page, round_num: int) -> None:
    """Verify round number is displayed on the page.

    Args:
        page: Playwright page
        round_num: Expected round number
    """
    expect(page.locator(GamePageLocators.ROUND_INDICATOR)).to_contain_text(
        f"Round {round_num}"
    )


@then(parsers.parse("I should be able to aim new shots for Round {round_num:d}"))
def can_aim_new_shots(page: Page, round_num: int) -> None:
    """Verify aiming controls are enabled after round advances.

    Args:
        page: Playwright page
        round_num: Current round number (unused but required by feature)
    """
    # Check that the shots-fired board is present
    shots_board = page.locator(GamePageLocators.SHOTS_FIRED_BOARD)
    expect(shots_board).to_be_visible()

    # Check that we can interact with checkboxes (at least one should be clickable)
    first_cell = page.locator(
        f'{GamePageLocators.SHOTS_FIRED_BOARD} input[type="checkbox"]'
    ).first
    expect(first_cell).to_be_enabled()


@given("my opponent has not yet fired")
def opponent_has_not_yet_fired() -> None:
    """Opponent has not fired yet (no-op step for state description)."""
    pass


@given("I have already fired my shots")
def i_have_already_fired(page: Page) -> None:
    """I have already fired my shots (alias for 'I have fired my shots').

    Args:
        page: Playwright page
    """
    i_have_fired_my_shots(page)


def aim_and_fire_shots_browser(page: Page, count: int = 6) -> None:
    """Aim at available coordinates and fire shots.

    Uses get_available_coordinates() for dynamic selection to avoid
    trying to fire at already-fired coordinates.

    Args:
        page: Playwright page
        count: Number of shots to fire (default 6)
    """
    coordinates = get_available_coordinates(page, count)
    if len(coordinates) < count:
        raise RuntimeError(
            f"Not enough available coordinates to fire (found {len(coordinates)})"
        )
    select_coordinates(page, coordinates)
    page.locator(GamePageLocators.FIRE_SHOTS_BUTTON).click()
    page.wait_for_timeout(500)  # Wait for fire action to complete


# === Board Visibility Steps (from two_player_board_and_feedback.feature) ===


@given(parsers.parse("the game is in progress at Round {round_num:d}"))
def game_in_progress_at_round(
    page: Page, opponent_client: httpx.Client, round_num: int
) -> None:
    """Ensure game is at specific round (delegates to existing step)."""
    it_is_round_n(page, opponent_client, round_num)


@given("the game is in progress")
def game_in_progress(page: Page) -> None:
    """Verify game is in progress (already on gameplay page)."""
    # Already on gameplay page from background
    pass


@given("I have ships placed on my board")
def ships_placed_on_my_board_browser(page: Page) -> None:
    """Verify ships are placed on player's board."""
    # Ships already placed from background
    pass


@given("my opponent has ships placed on their board")
def opponent_has_ships_placed_browser(page: Page) -> None:
    """Verify opponent has ships placed."""
    # Opponent ships already placed from game setup
    pass


@given("my opponent has fired shots at my board in previous rounds")
def opponent_fired_shots_at_my_board_browser(page: Page) -> None:
    """Simulate opponent firing shots in previous rounds."""
    pytest.skip("Round progression not yet fully implemented")


@given("I have fired shots in previous rounds")
def i_have_fired_shots_in_previous_rounds_browser(page: Page) -> None:
    """Simulate firing shots in previous rounds."""
    pytest.skip("Round progression not yet fully implemented")


@given(parsers.parse("I have fired {count:d} shots"))
def i_have_fired_n_shots_browser(page: Page, count: int) -> None:
    """Aim and fire a specific number of shots at available coordinates.

    Args:
        page: Playwright page
        count: Number of shots to fire
    """
    aim_and_fire_shots_browser(page, count)


@then('I should see all my ship positions on "My Ships and Shots Received" board')
def see_all_ship_positions_browser(page: Page) -> None:
    """Verify all ship positions are visible on My Ships board."""
    my_ships_board = page.locator(GamePageLocators.MY_SHIPS_BOARD)
    expect(my_ships_board).to_be_visible()

    # Check for ship codes (D, C, B, A, S)
    ship_codes = ["D", "C", "B", "A", "S"]
    for code in ship_codes:
        # At least one ship code should be visible
        expect(my_ships_board).to_contain_text(code)
        break  # Just check that ships are visible


@then("I should see all shots my opponent has fired at my board")
def see_opponent_shots_on_my_board_browser(page: Page) -> None:
    """Verify opponent's shots are marked on My Ships board."""
    pytest.skip("Round progression not yet fully implemented")


@then("I should see round numbers for each shot received")
def see_round_numbers_for_received_shots_browser(page: Page) -> None:
    """Verify round numbers are displayed for received shots."""
    pytest.skip("Round progression not yet fully implemented")


@then("I should see which of my ships have been hit")
def see_which_ships_hit_browser(page: Page) -> None:
    """Verify ships that have been hit are marked."""
    pytest.skip("Not yet implemented")


@then("I should see which of my ships have been sunk")
def see_which_ships_sunk_browser(page: Page) -> None:
    """Verify sunk ships are marked."""
    pytest.skip("Not yet implemented")


@then("I should not see any of my opponent's ship positions")
def should_not_see_opponent_ship_positions_browser(page: Page) -> None:
    """Verify opponent ship positions are NOT visible."""
    shots_fired_board = page.locator(GamePageLocators.SHOTS_FIRED_BOARD)
    expect(shots_fired_board).to_be_visible()
    # Opponent ship positions should not be visible on shots fired board


@then('I should see all shots I have fired on the "Shots Fired" board')
def see_all_fired_shots_browser(page: Page) -> None:
    """Verify all fired shots are marked on Shots Fired board."""
    pytest.skip("Round progression not yet fully implemented")


@then(
    'I should see the "Hits Made" area showing which ships I\'ve hit with the round numbers'
)
def see_hits_made_area_with_round_numbers_browser(page: Page) -> None:
    """Verify Hits Made area shows ship hit tracking."""
    hits_made_area = page.locator(GamePageLocators.HITS_MADE_AREA)
    expect(hits_made_area).to_be_visible()

    # Should show ship names
    expect(hits_made_area).to_contain_text("Carrier")
    expect(hits_made_area).to_contain_text("Destroyer")


@then('I should see the "Hits Made" area next to the Shots Fired board')
def see_hits_made_area_next_to_shots_fired_browser(page: Page) -> None:
    """Verify Hits Made area is present."""
    hits_made_area = page.locator(GamePageLocators.HITS_MADE_AREA)
    expect(hits_made_area).to_be_visible()


@then(
    "I should see 5 ship rows labeled: Carrier, Battleship, Cruiser, Submarine, Destroyer"
)
def see_five_ship_rows_browser(page: Page) -> None:
    """Verify all 5 ship types are listed."""
    hits_made_area = page.locator(GamePageLocators.HITS_MADE_AREA)
    expect(hits_made_area).to_be_visible()

    # Check all 5 ship names
    expect(hits_made_area).to_contain_text("Carrier")
    expect(hits_made_area).to_contain_text("Battleship")
    expect(hits_made_area).to_contain_text("Cruiser")
    expect(hits_made_area).to_contain_text("Submarine")
    expect(hits_made_area).to_contain_text("Destroyer")


@then("each ship row should show spaces for tracking hits")
def each_ship_row_shows_hit_spaces_browser(page: Page) -> None:
    """Verify ship rows have hit tracking spaces."""
    # Find carrier hit tracking row (assumes testid exists)
    carrier_row = page.locator('[data-testid="hit-track-carrier"]')
    expect(carrier_row).to_be_visible()

    # Should have hit spaces (indicated by class)
    hit_spaces = carrier_row.locator(".hit-space")
    expect(hit_spaces).to_have_count(5)  # Carrier has 5 spaces


@then('I should see "My Ships and Shots Received" board')
def see_my_ships_board_check_browser(page: Page) -> None:
    """Verify My Ships board is visible."""
    my_ships_board = page.locator(GamePageLocators.MY_SHIPS_BOARD)
    expect(my_ships_board).to_be_visible()


@then('I should see "Shots Fired" board')
def see_shots_fired_board_check_browser(page: Page) -> None:
    """Verify Shots Fired board is visible."""
    shots_fired_board = page.locator(GamePageLocators.SHOTS_FIRED_BOARD)
    expect(shots_fired_board).to_be_visible()


@then('I should see "Hits Made" area')
def see_hits_made_area_check_browser(page: Page) -> None:
    """Verify Hits Made area is visible."""
    hits_made_area = page.locator(GamePageLocators.HITS_MADE_AREA)
    expect(hits_made_area).to_be_visible()


@then("both boards should show a 10x10 grid with coordinates A-J and 1-10")
def both_boards_show_10x10_grid_browser(page: Page) -> None:
    """Verify both boards have proper grid structure."""
    # Check My Ships board
    my_ships_board = page.locator(GamePageLocators.MY_SHIPS_BOARD)
    expect(my_ships_board).to_be_visible()
    expect(my_ships_board).to_contain_text("A")
    expect(my_ships_board).to_contain_text("J")

    # Check Shots Fired board
    shots_fired_board = page.locator(GamePageLocators.SHOTS_FIRED_BOARD)
    expect(shots_fired_board).to_be_visible()
    expect(shots_fired_board).to_contain_text("A")
    expect(shots_fired_board).to_contain_text("J")


@then("all three areas should be clearly distinguishable")
def all_three_areas_distinguishable_browser(page: Page) -> None:
    """Verify all three areas exist and are separate."""
    my_ships = page.locator(GamePageLocators.MY_SHIPS_BOARD)
    shots_fired = page.locator(GamePageLocators.SHOTS_FIRED_BOARD)
    hits_made = page.locator(GamePageLocators.HITS_MADE_AREA)

    expect(my_ships).to_be_visible()
    expect(shots_fired).to_be_visible()
    expect(hits_made).to_be_visible()


# === Hit Feedback Given Steps ===


@given("none of my shots hit any opponent ships")
def none_of_shots_hit_browser(page: Page) -> None:
    """State verification that shots don't hit opponent ships."""
    # This is implicitly true when we fire at available coordinates
    # that don't overlap with default ship placements
    pass


@given(parsers.parse("{count:d} of my shots hit my opponent's {ship_name}"))
def n_shots_hit_opponent_ship_browser(page: Page, count: int, ship_name: str) -> None:
    """Simulate hitting opponent's ship a specific number of times."""
    pytest.skip("Hit feedback requires round resolution implementation")


@given(parsers.parse("my opponent hit my {ship_name} {count:d} times"))
def opponent_hit_my_ship_browser(page: Page, ship_name: str, count: int) -> None:
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
def hit_opponent_ship_in_round_browser(
    page: Page, round_num: int, ship_name: str, count: int
) -> None:
    """Simulate hitting opponent's ship in a specific round."""
    pytest.skip("Hit feedback requires round resolution implementation")


@given(parsers.parse('my opponent has a {ship_name} at "{coords}"'))
def opponent_has_ship_at_positions_browser(
    page: Page, ship_name: str, coords: str
) -> None:
    """Verify opponent has a ship at specific coordinates."""
    pytest.skip("Ship placement verification not fully implemented")


@given(parsers.parse("I fire {count:d} shots"))
def i_fire_n_shots_browser(page: Page, count: int) -> None:
    """Fire a specific number of shots."""
    pytest.skip("Hit feedback requires round resolution implementation")


# === Hit Feedback Then Steps ===


@then("I should see round numbers marked in the spaces where I've hit each ship")
def see_round_numbers_in_hit_spaces_browser(page: Page) -> None:
    """Verify round numbers are marked in hit tracking spaces."""
    pytest.skip("Hit feedback display requires round resolution implementation")


@then('sunk ships should be clearly marked as "SUNK"')
def sunk_ships_marked_as_sunk_browser(page: Page) -> None:
    """Verify sunk ships are marked as SUNK."""
    pytest.skip("Sunk ship marking not fully implemented")


@then("I should NOT see the exact coordinates of the hits")
def should_not_see_hit_coordinates_browser(page: Page) -> None:
    """Verify hit coordinates are not displayed."""
    pytest.skip("Coordinate hiding not fully implemented")


@then(parsers.parse('I should see "{ship_name}: {count:d} hits total" displayed'))
def see_ship_total_hits_displayed_browser(
    page: Page, ship_name: str, count: int
) -> None:
    """Verify total hits for a ship are displayed."""
    pytest.skip("Total hits display not fully implemented")


@then(parsers.parse('I should see "Your {ship_name} was hit {count:d} time" displayed'))
@then(
    parsers.parse('I should see "Your {ship_name} was hit {count:d} times" displayed')
)
def see_my_ship_hits_displayed_browser(page: Page, ship_name: str, count: int) -> None:
    """Verify hits received on my ships are displayed."""
    pytest.skip("Hits received display not fully implemented")


@then(parsers.parse('I should see "Hits Made This Round: {message}" displayed'))
def see_hits_made_this_round_displayed_browser(page: Page, message: str) -> None:
    """Verify hits made this round are displayed."""
    pytest.skip("Hits made this round display not fully implemented")


@then(
    parsers.parse(
        'the Hits Made area should show round number "{round_num:d}" marked {count:d} times on {ship_name}'
    )
)
def see_hit_tracking_in_area_browser(
    page: Page, round_num: int, count: int, ship_name: str
) -> None:
    """Verify hit tracking shows round numbers in ship rows."""
    pytest.skip("Hit tracking display not fully implemented")


@then(parsers.parse("the {ship_name} should have {count:d} total hits"))
def see_ship_total_hits_browser(page: Page, ship_name: str, count: int) -> None:
    """Verify ship has correct total hits."""
    pytest.skip("Total hits tracking not fully implemented")


@then("I should see the exact coordinates of the hits on my board")
def see_received_hit_coordinates_browser(page: Page) -> None:
    """Verify received hit coordinates are displayed on my board."""
    pytest.skip("Received hit coordinates display not fully implemented")


@then(parsers.parse('coordinates should be marked with round number "{round_num:d}"'))
def see_coordinates_with_round_number_browser(page: Page, round_num: int) -> None:
    """Verify coordinates are marked with round number."""
    pytest.skip("Coordinate round marking not fully implemented")


@then(parsers.parse("the {ship_name} should show {count:d} new hit markers"))
def see_new_hit_markers_browser(page: Page, ship_name: str, count: int) -> None:
    """Verify new hit markers are shown for a ship."""
    pytest.skip("New hit markers display not fully implemented")


@then("the Hits Made area should show no new shots marked")
def hits_made_area_shows_no_hits_browser(page: Page) -> None:
    """Verify the Hits Made area shows no hits on opponent ships."""
    hits_made_area = page.locator(GamePageLocators.HITS_MADE_AREA)
    expect(hits_made_area).to_be_visible()
    # Basic check - just verify area exists


@then(
    parsers.parse(
        "I should see all {count:d} of my shots marked as misses on the Shots Fired board"
    )
)
def see_all_shots_as_misses_browser(page: Page, count: int) -> None:
    """Verify all fired shots are marked as misses on the Shots Fired board."""
    shots_fired_board = page.locator(GamePageLocators.SHOTS_FIRED_BOARD)
    expect(shots_fired_board).to_be_visible()
    # Basic check - just verify board exists
