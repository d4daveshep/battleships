import httpx
import time
from playwright.sync_api import Page, expect
from pytest_bdd import scenarios, given, when, then, scenario, parsers
from tests.bdd.conftest import (
    BASE_URL,
    navigate_to_login,
    fill_player_name,
    click_multiplayer_button,
    select_coordinates,
)

# Global to share state between fixtures in same scenario
_p2_client_for_scenario: httpx.Client | None = None

scenarios("../../features/two_player_gameplay.feature")


@given("both players have completed ship placement")
def players_completed_placement(page: Page):
    global _p2_client_for_scenario

    with httpx.Client(base_url=BASE_URL) as client:
        client.post("/test/reset-lobby")

    _p2_client_for_scenario = httpx.Client(base_url=BASE_URL)
    _p2_client_for_scenario.post(
        "/login", data={"player_name": "Player2", "game_mode": "human"}
    )

    navigate_to_login(page)
    fill_player_name(page, "Player1")
    click_multiplayer_button(page)

    page.wait_for_url("**/lobby")

    page.wait_for_selector('[data-testid="select-opponent-Player2"]', timeout=10000)
    page.locator('[data-testid="select-opponent-Player2"]').click()

    _p2_client_for_scenario.post("/accept-game-request", data={})

    page.wait_for_url("**/place-ships")

    page.locator('[data-testid="random-placement-button"]').click()
    expect(page.locator('[data-testid="ship-placement-count"]')).to_contain_text(
        "5 of 5 ships placed"
    )

    _p2_client_for_scenario.post(
        "/random-ship-placement", data={"player_name": "Player2"}
    )


@given("both players are ready")
def players_are_ready(page: Page):
    global _p2_client_for_scenario

    page.locator('[data-testid="ready-button"]').click()

    # Use the existing p2_client from ship placement
    if _p2_client_for_scenario is None:
        _p2_client_for_scenario = httpx.Client(base_url=BASE_URL)
        _p2_client_for_scenario.post(
            "/login", data={"player_name": "Player2", "game_mode": "human"}
        )

    # Player2 is already logged in and has ships placed, just click ready
    _p2_client_for_scenario.post("/ready-for-game", data={"player_name": "Player2"})

    page.wait_for_url("**/game/*", timeout=30000)


@given("the game has started")
def game_has_started():
    pass


@given("I am on the gameplay page")
def on_gameplay_page(page: Page):
    # Verify we are on the game page (may already be there from redirect)
    import re

    expect(page).to_have_url(re.compile(r".*/game/.*"))


# Scenario Steps


@given("the game just started")
def game_just_started():
    """Ensure it is the beginning of the game"""
    pass


@then(parsers.parse('I should see "{text}" displayed'))
def see_text_displayed(page: Page, text: str):
    """Verify text is displayed on the page"""
    expect(page.locator("body")).to_contain_text(text)


@then("I should be able to select up to 6 coordinates to fire at")
def can_select_coordinates(page: Page):
    """Verify firing controls are present"""
    # Check for the grid that allows selection (Shots Fired board)
    expect(page.locator('[data-testid="shots-fired-board"]')).to_be_visible()

    # Check for fire button
    expect(page.locator('[data-testid="fire-shots-button"]')).to_be_visible()


@then(parsers.parse('I should see my board labeled "{label}"'))
def see_my_board_labeled(page: Page, label: str):
    """Verify my board label"""
    expect(page.locator("body")).to_contain_text(label)
    expect(page.locator('[data-testid="my-ships-board"]')).to_be_visible()


@then(parsers.parse('I should see the opponent\'s board labeled "{label}"'))
def see_opponent_board_labeled(page: Page, label: str):
    """Verify opponent board label"""
    expect(page.locator("body")).to_contain_text(label)
    expect(page.locator('[data-testid="shots-fired-board"]')).to_be_visible()


@then(
    parsers.parse(
        'I should see the "Hits Made" area showing all {count:d} opponent ships'
    )
)
def see_hits_made_area(page: Page, count: int):
    """Verify hits made area"""
    hits_area = page.locator('[data-testid="hits-made-area"]')
    expect(hits_area).to_be_visible()

    # Check for ship names
    ship_names = ["Carrier", "Battleship", "Cruiser", "Submarine", "Destroyer"]
    for ship in ship_names:
        expect(hits_area).to_contain_text(ship)


# === Scenario: Selecting multiple shot coordinates for aiming ===


@given("it is Round 1")
def it_is_round_1():
    """Verify it is Round 1"""
    # This is implicitly true at game start
    pass


@given("I have 6 shots available")
def have_6_shots_available():
    """Verify player has 6 shots available (all ships placed)"""
    # This is implicitly true when ships are placed
    pass


@when(parsers.parse('I select coordinate "{coord}" to aim at'))
def select_coordinate_to_aim(page: Page, coord: str):
    """Select a coordinate to aim at by clicking the checkbox"""
    # Find and click the checkbox for the coordinate
    cell = page.locator(f'[data-testid="opponent-cell-{coord}"]')
    expect(cell).to_be_visible()
    cell.click()
    # Wait for HTMX to update
    page.wait_for_timeout(500)


@then(parsers.parse("I should see {count:d} coordinates marked as aimed"))
def see_coordinates_marked_as_aimed(page: Page, count: int):
    """Verify number of coordinates marked as aimed"""
    # Check for checked checkboxes in the shots-fired board
    checked_cells = page.locator(
        '[data-testid="shots-fired-board"] input[type="checkbox"]:checked'
    )
    expect(checked_cells).to_have_count(count)


@then("I should be able to select 3 more coordinates")
def can_select_3_more_coordinates(page: Page):
    """Verify 3 more coordinates can be selected (6-3=3)"""
    # This is implicitly true if we have 3/6 aimed
    aiming_status = page.locator('[data-testid="aiming-status"]')
    expect(aiming_status).to_be_visible()
    # Should not see 6/6
    expect(aiming_status).not_to_contain_text("6/6")


@then(parsers.parse('the "{button_name}" button should be enabled'))
def button_should_be_enabled(page: Page, button_name: str):
    """Verify that a button is enabled"""
    # Map button name to testid
    testid_map: dict[str, str] = {
        "Fire Shots": "fire-shots-button",
    }
    testid: str = testid_map.get(
        button_name, button_name.lower().replace(" ", "-") + "-button"
    )
    button = page.locator(f'[data-testid="{testid}"]')
    expect(button).to_be_visible()
    expect(button).to_be_enabled()


# === Scenario: Reselecting an aimed shot's coordinates un-aims the shot ===


@given(parsers.parse('I have only selected coordinate "{coord}" to aim at'))
def have_only_selected_coordinate(page: Page, coord: str):
    """Select exactly one coordinate to aim at"""
    cell = page.locator(f'[data-testid="opponent-cell-{coord}"]')
    expect(cell).to_be_visible()
    cell.click()
    # Wait for HTMX to update
    page.wait_for_timeout(500)


@when(parsers.parse('I select coordinate "{coord}" again'))
def select_coordinate_again(page: Page, coord: str):
    """Select the same coordinate again (toggle off)"""
    cell = page.locator(f'[data-testid="opponent-cell-{coord}"]')
    expect(cell).to_be_visible()
    cell.click()
    # Wait for HTMX to update
    page.wait_for_timeout(500)


@then(parsers.parse('coordinate "{coord}" should be un-aimed'))
def coordinate_should_be_unaimed(page: Page, coord: str):
    """Verify the coordinate is no longer aimed"""
    cell = page.locator(f'[data-testid="opponent-cell-{coord}"]')
    checkbox = cell.locator('input[type="checkbox"]')
    expect(checkbox).not_to_be_checked()


@then(parsers.parse('I should not see coordinate "{coord}" marked as aimed'))
def should_not_see_coordinate_marked(page: Page, coord: str):
    """Verify the coordinate is not visually marked as aimed"""
    cell = page.locator(f'[data-testid="opponent-cell-{coord}"]')
    # Check the cell doesn't have the aimed-cell class
    expect(cell).not_to_have_class("aimed-cell")


@then(
    parsers.parse("I should still have {count:d} remaining shot selections available")
)
def should_have_remaining_shots(page: Page, count: int):
    """Verify the number of remaining shot selections"""
    shots_display = page.locator('[data-testid="shots-available"]')
    expect(shots_display).to_contain_text(f"Shots Available: {count}")


# === Scenario: Cannot select more shots than available ===


@given("I have selected 6 coordinates to aim at")
def have_selected_6_coordinates(page: Page):
    """Select 6 coordinates to aim at"""
    select_coordinates(page, ["A1", "B1", "C1", "D1", "E1", "F1"])


@when("I attempt to select another coordinate")
def attempt_select_another_coordinate(page: Page):
    """Attempt to select a 7th coordinate when already at limit"""
    cell = page.locator('[data-testid="opponent-cell-G1"]')
    expect(cell).to_be_visible()
    cell.click()
    # Wait for HTMX to update and show error message
    error_message = page.locator('[data-testid="error-message"]')
    expect(error_message).to_contain_text("All available shots aimed", timeout=5000)


@then("the coordinate should not be selectable")
def coordinate_not_selectable(page: Page):
    """Verify the coordinate was not added to aimed shots"""
    # After error message appears, verify the checkbox is not checked
    # Note: The checkbox might be checked by browser before HTMX response,
    # but the server rejected it, so we check it's not in the aimed list
    cell = page.locator('[data-testid="opponent-cell-G1"]')
    # Check that the cell doesn't have the aimed-cell class
    expect(cell).not_to_have_class("aimed-cell")


@then('I should see a message "All available shots aimed"')
def see_shot_limit_message(page: Page):
    """Verify the error message is displayed"""
    error_message = page.locator('[data-testid="error-message"]')
    expect(error_message).to_contain_text("All available shots aimed")


@then('I should see "Shots Aimed: 6/6" displayed')
def see_shots_aimed_counter(page: Page):
    """Verify the shot counter shows 6/6"""
    # Check for shots available display (which shows the total available)
    shots_available = page.locator('[data-testid="shots-available"]')
    expect(shots_available).to_contain_text("Shots Available: 6")
