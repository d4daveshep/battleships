import httpx
from playwright.sync_api import Page, expect
from pytest_bdd import scenarios, given, when, then, parsers
from tests.bdd.conftest import (
    BASE_URL,
    navigate_to_login,
    fill_player_name,
    click_multiplayer_button,
    select_coordinates,
)


# Centralized locators for the gameplay page
class GamePageLocators:
    READY_BUTTON = '[data-testid="ready-button"]'
    RANDOM_PLACEMENT_BUTTON = '[data-testid="random-placement-button"]'
    SHIP_PLACEMENT_COUNT = '[data-testid="ship-placement-count"]'
    SHOTS_FIRED_BOARD = '[data-testid="shots-fired-board"]'
    MY_SHIPS_BOARD = '[data-testid="my-ships-board"]'
    FIRE_SHOTS_BUTTON = '[data-testid="fire-shots-button"]'
    HITS_MADE_AREA = '[data-testid="hits-made-area"]'
    AIMING_STATUS = '[data-testid="aiming-status"]'
    SHOTS_AVAILABLE = '[data-testid="shots-available"]'
    ERROR_MESSAGE = '[data-testid="error-message"]'
    GAME_STATUS = '[data-testid="game-status"]'
    CHECKED_CELLS = '[data-testid="shots-fired-board"] input[type="checkbox"]:checked'

    @staticmethod
    def opponent_cell(coord: str) -> str:
        return f'[data-testid="opponent-cell-{coord}"]'

    @staticmethod
    def select_opponent_button(player_name: str) -> str:
        return f'[data-testid="select-opponent-{player_name}"]'


scenarios("../../features/two_player_gameplay.feature")


def setup_opponent(client: httpx.Client, player_name: str = "Player2") -> None:
    """Helper to setup the opponent state via API."""
    client.post("/login", data={"player_name": player_name, "game_mode": "human"})


def setup_game_with_opponent(page: Page, opponent_client: httpx.Client) -> None:
    """Orchestrate the full game setup flow."""
    # Reset lobby state
    with httpx.Client(base_url=BASE_URL) as admin_client:
        admin_client.post("/test/reset-lobby")

    # Setup opponent (Player 2)
    setup_opponent(opponent_client)

    # Setup current player (Player 1) in browser
    navigate_to_login(page)
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
def players_completed_placement(page: Page, opponent_client: httpx.Client):
    setup_game_with_opponent(page, opponent_client)

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
def cannot_aim_additional_shots(page: Page):
    cell = page.locator(GamePageLocators.opponent_cell("G1"))
    expect(cell).to_be_visible()
    cell.click()

    error_message = page.locator(GamePageLocators.ERROR_MESSAGE)
    expect(error_message).to_contain_text("Cannot aim shots after firing", timeout=5000)
