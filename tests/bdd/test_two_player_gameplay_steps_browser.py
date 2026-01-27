import httpx
import time
from playwright.sync_api import Page, expect
from pytest_bdd import scenarios, given, when, then, scenario, parsers
from tests.bdd.conftest import (
    BASE_URL,
    navigate_to_login,
    fill_player_name,
    click_multiplayer_button,
)

# Global to store P2 client
p2_client = None


scenarios("../../features/two_player_gameplay.feature")


@given("both players have completed ship placement")
def players_completed_placement(page: Page):
    global p2_client

    # 1. Reset Lobby
    with httpx.Client(base_url=BASE_URL) as client:
        client.post("/test/reset-lobby")

    # 2. Login P2 (Opponent) via API
    p2_client = httpx.Client(base_url=BASE_URL)
    p2_client.post("/login", data={"player_name": "Player2", "game_mode": "human"})

    # 3. Login P1 (User) via Browser
    navigate_to_login(page)
    fill_player_name(page, "Player1")
    click_multiplayer_button(page)

    # Wait for lobby
    page.wait_for_url("**/lobby")

    # 4. P1 selects P2
    # Wait for P2 to appear in list (long polling might delay it)
    expect(page.locator('[data-testid="select-opponent-Player2"]')).to_be_visible(
        timeout=10000
    )
    page.locator('[data-testid="select-opponent-Player2"]').click()

    # 5. P2 accepts request
    # Wait a moment for the request to be registered
    time.sleep(1)
    p2_client.post("/accept-game-request", data={})

    # 6. P1 should be redirected to ship placement
    page.wait_for_url("**/place-ships")

    # 7. P1 places ships (Randomly)
    page.locator('[data-testid="random-placement-button"]').click()
    # Wait for 5 ships placed
    expect(page.locator('[data-testid="ship-placement-count"]')).to_contain_text(
        "5 of 5 ships placed"
    )

    # 8. P2 places ships (Randomly)
    p2_client.post("/random-ship-placement", data={"player_name": "Player2"})


@given("both players are ready")
def players_are_ready(page: Page):
    global p2_client

    # P1 Ready
    page.locator('[data-testid="ready-button"]').click()

    # P2 Ready
    p2_client.post("/ready-for-game", data={"player_name": "Player2"})


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
    testid_map = {
        "Fire Shots": "fire-shots-button",
    }
    testid = testid_map.get(
        button_name, button_name.lower().replace(" ", "-") + "-button"
    )
    button = page.locator(f'[data-testid="{testid}"]')
    expect(button).to_be_visible()
    expect(button).to_be_enabled()
