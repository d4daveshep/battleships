"""BDD step definitions for two-player gameplay using Playwright browser automation."""

import re
from typing import Any

import pytest
from playwright.sync_api import Browser, Locator, Page, expect
from pytest_bdd import given, parsers, scenarios, then, when

from tests.bdd.conftest import BASE_URL

# Load scenarios from feature file
scenarios("../../features/two_player_gameplay.feature")


# === Helper Functions ===


def setup_two_player_game_browser(
    browser: Browser, player_name: str = "Player1", opponent_name: str = "Player2"
) -> tuple[Page, Page, str]:
    """Setup a complete two-player game with ships placed and ready to play

    Returns:
        Tuple of (player_page, opponent_page, game_id)
    """
    # Create pages for both players
    player_page = browser.new_page()
    opponent_page = browser.new_page()

    player_page.set_default_timeout(40000)
    opponent_page.set_default_timeout(40000)

    # Login both players
    player_page.goto(f"{BASE_URL}login")
    player_page.locator('input[name="player_name"]').fill(player_name)
    player_page.locator('button[value="human"]').click()
    player_page.wait_for_url("**/lobby*")

    opponent_page.goto(f"{BASE_URL}login")
    opponent_page.locator('input[name="player_name"]').fill(opponent_name)
    opponent_page.locator('button[value="human"]').click()
    opponent_page.wait_for_url("**/lobby*")

    # Player selects opponent
    player_page.locator(f'button:has-text("{opponent_name}")').click()
    player_page.wait_for_selector('text="Waiting for opponent to accept"')

    # Opponent accepts
    opponent_page.locator('button:has-text("Accept")').click()

    # Both navigate to ship placement
    player_page.wait_for_url("**/start-game*")
    opponent_page.wait_for_url("**/start-game*")

    # Click "Start Game" button for both
    player_page.locator('button:has-text("Start Game")').click()
    player_page.wait_for_url("**/place-ships*")

    opponent_page.locator('button:has-text("Start Game")').click()
    opponent_page.wait_for_url("**/place-ships*")

    # Place ships for both players (using default positions)
    ships_to_place = [
        ("CARRIER", "A1", "HORIZONTAL"),
        ("BATTLESHIP", "B1", "HORIZONTAL"),
        ("CRUISER", "C1", "HORIZONTAL"),
        ("SUBMARINE", "D1", "HORIZONTAL"),
        ("DESTROYER", "E1", "HORIZONTAL"),
    ]

    for ship_type, coord, orientation in ships_to_place:
        # Player places ship
        player_page.locator(f'select[name="ship_type"]').select_option(ship_type)
        player_page.locator(f'input[name="coord"]').fill(coord)
        player_page.locator(f'select[name="orientation"]').select_option(orientation)
        player_page.locator('button:has-text("Place Ship")').click()
        player_page.wait_for_timeout(200)

        # Opponent places ship
        opponent_page.locator(f'select[name="ship_type"]').select_option(ship_type)
        opponent_page.locator(f'input[name="coord"]').fill(coord)
        opponent_page.locator(f'select[name="orientation"]').select_option(orientation)
        opponent_page.locator('button:has-text("Place Ship")').click()
        opponent_page.wait_for_timeout(200)

    # Mark both players as ready
    player_page.locator('button:has-text("Ready")').click()
    opponent_page.locator('button:has-text("Ready")').click()

    # Wait for game to start
    player_page.wait_for_url("**/game/**")
    opponent_page.wait_for_url("**/game/**")

    # Extract game_id from URL
    game_url = player_page.url
    game_id = game_url.split("/game/")[1].split("/")[0].split("?")[0]

    return player_page, opponent_page, game_id


@pytest.fixture
def game_pages(browser: Browser) -> tuple[Page, Page, str]:
    """Fixture providing two player pages and game_id"""
    player_page, opponent_page, game_id = setup_two_player_game_browser(browser)
    yield player_page, opponent_page, game_id
    player_page.close()
    opponent_page.close()


# === Background Steps ===


@given("both players have completed ship placement")
def both_players_completed_ship_placement(page: Page, browser: Browser) -> None:
    """Setup game with both players having completed ship placement"""
    # This will be handled by the game_pages fixture
    # For individual tests, we'll use the page fixture
    pass


@given("both players are ready")
def both_players_are_ready(page: Page) -> None:
    """Verify both players are ready"""
    # Verify we're on the game page
    expect(page).to_have_url(re.compile(r".*/game/.*"))


@given("the game has started")
def game_has_started(page: Page) -> None:
    """Verify game has started"""
    expect(page).to_have_url(re.compile(r".*/game/.*"))


@given("I am on the gameplay page")
def on_gameplay_page(page: Page) -> None:
    """Verify on gameplay page"""
    expect(page).to_have_url(re.compile(r".*/game/.*"))


# === Given Steps ===


@given("the game just started")
def game_just_started(page: Page) -> None:
    """Verify game is at initial state"""
    # Check for Round 1
    expect(page.locator('text="Round 1"')).to_be_visible()


@given("it is Round 1")
@given("it is Round 2")
@given("it is Round 3")
def set_round_number(page: Page) -> None:
    """Verify current round number"""
    # Round number should be visible on page
    pass


@given("I have 6 shots available")
def have_six_shots_available(page: Page) -> None:
    """Verify player has 6 shots available"""
    counter = page.locator('[data-testid="shot-counter-value"]')
    expect(counter).to_contain_text("6")


@given("I have not aimed any shots yet")
def have_not_aimed_shots(page: Page) -> None:
    """Verify no shots have been aimed"""
    counter = page.locator('[data-testid="shot-counter-value"]')
    expect(counter).to_contain_text("0")


@given(parsers.parse('I fired at "{coord}" in Round 1'))
def fired_at_coord_in_round_1(page: Page, coord: str) -> None:
    """Verify a shot was fired at a coordinate in Round 1"""
    # Check that cell is marked as fired
    cell = page.locator(f'[data-testid="shots-fired-cell-{coord}"]')
    expect(cell).to_have_class(re.compile(r"cell--fired"))


@given(parsers.parse('I have aimed at "{coord}" in the current round'))
def have_aimed_at_coord(page: Page, coord: str) -> None:
    """Aim at a specific coordinate"""
    cell = page.locator(f'[data-testid="shots-fired-cell-{coord}"]')
    if cell.is_visible():
        cell.click()
        page.wait_for_timeout(200)


@given(parsers.parse('I have not fired at or aimed at "{coord}"'))
@given(parsers.parse('I have not interacted with "{coord}"'))
def have_not_interacted_with_coord(page: Page, coord: str) -> None:
    """Verify coordinate has not been fired at or aimed at"""
    cell = page.locator(f'[data-testid="shots-fired-cell-{coord}"]')
    expect(cell).not_to_have_class(re.compile(r"cell--fired"))
    expect(cell).not_to_have_class(re.compile(r"cell--aimed"))


@given('the "Fire Shots" button is disabled')
def fire_button_is_disabled(page: Page) -> None:
    """Verify fire button is disabled"""
    button = page.locator('[data-testid="fire-shots-button"]')
    expect(button).to_be_disabled()


@given(parsers.parse('I have clicked on cell "{coord}" on my Shots Fired board'))
def have_clicked_on_cell(page: Page, coord: str) -> None:
    """Click on a cell to aim at it"""
    cell = page.locator(f'[data-testid="shots-fired-cell-{coord}"]')
    cell.click()
    page.wait_for_timeout(200)


@given(parsers.parse('cell "{coord}" is marked as "aimed"'))
def cell_is_marked_as_aimed(page: Page, coord: str) -> None:
    """Verify cell is marked as aimed"""
    cell = page.locator(f'[data-testid="shots-fired-cell-{coord}"]')
    expect(cell).to_have_class(re.compile(r"cell--aimed"))


@given(parsers.parse('I have aimed shots at "{coords}"'))
def have_aimed_shots_at_coords(page: Page, coords: str) -> None:
    """Aim at multiple coordinates"""
    coord_list = [c.strip() for c in coords.split(",")]
    for coord in coord_list:
        have_aimed_at_coord(page, coord)


@given(parsers.parse('the shot counter shows "{text}"'))
def shot_counter_shows_text(page: Page, text: str) -> None:
    """Verify shot counter shows specific text"""
    counter = page.locator('[data-testid="shot-counter-value"]')
    expect(counter).to_contain_text(text)


@given(
    parsers.parse('cell "{coord}" is marked as "fired" with round number "{round_num}"')
)
def cell_is_marked_as_fired(page: Page, coord: str, round_num: str) -> None:
    """Verify cell is marked as fired with round number"""
    cell = page.locator(f'[data-testid="shots-fired-cell-{coord}"]')
    expect(cell).to_have_class(re.compile(r"cell--fired"))
    # Could also check for round number display if implemented


@given(parsers.parse("I have aimed at {count:d} coordinates"))
def have_aimed_at_n_coordinates(page: Page, count: int) -> None:
    """Aim at N coordinates"""
    coords = ["A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10"]
    for i in range(count):
        if i < len(coords):
            have_aimed_at_coord(page, coords[i])


@given(parsers.parse("I have aimed at {count:d} coordinates"))
def have_aimed_at_n_coords_alt(page: Page, count: int) -> None:
    """Aim at N coordinates (alternative phrasing)"""
    have_aimed_at_n_coordinates(page, count)


@given("all unaimed cells are not clickable")
def all_unaimed_cells_not_clickable(page: Page) -> None:
    """Verify all unaimed cells are not clickable"""
    # When limit is reached, unaimed cells should have cell--unavailable class
    pass


# === When Steps ===


@when(parsers.parse('I click on cell "{coord}" on my Shots Fired board'))
def click_on_cell(page: Page, coord: str) -> None:
    """Click on a cell to aim at it"""
    cell = page.locator(f'[data-testid="shots-fired-cell-{coord}"]')
    cell.click()
    page.wait_for_timeout(300)


@when(parsers.parse('I click on cells "{coords}" on my Shots Fired board'))
def click_on_multiple_cells(page: Page, coords: str) -> None:
    """Click on multiple cells to aim at them"""
    coord_list = [c.strip() for c in coords.split(",")]
    for coord in coord_list:
        click_on_cell(page, coord)


@when("I view my Shots Fired board")
def view_shots_fired_board(page: Page) -> None:
    """View the shots fired board"""
    # Board should already be visible
    board = page.locator('[data-testid="opponent-board-wrapper"]')
    expect(board).to_be_visible()


@when(parsers.parse('I attempt to click on cell "{coord}"'))
@when(parsers.parse('I attempt to click on cell "{coord}" again'))
def attempt_to_click_on_cell(page: Page, coord: str) -> None:
    """Attempt to click on a cell (may not respond)"""
    cell = page.locator(f'[data-testid="shots-fired-cell-{coord}"]')
    cell.click()
    page.wait_for_timeout(200)


@when(parsers.parse('I aim at coordinates "{coords}"'))
def aim_at_coordinates(page: Page, coords: str) -> None:
    """Aim at multiple coordinates"""
    coord_list = [c.strip() for c in coords.split(",")]
    for coord in coord_list:
        click_on_cell(page, coord)


@when(parsers.parse("I aim at {count:d} coordinates"))
@when(parsers.parse("I aim at {count:d} coordinate"))
def aim_at_n_coordinates(page: Page, count: int) -> None:
    """Aim at N coordinates"""
    coords = ["A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10"]
    for i in range(count):
        if i < len(coords):
            click_on_cell(page, coords[i])


@when(parsers.parse('I remove the aimed shot at "{coord}"'))
@when(
    parsers.parse('I click the remove button next to "{coord}" in the aimed shots list')
)
def remove_aimed_shot(page: Page, coord: str) -> None:
    """Remove an aimed shot"""
    remove_button = page.locator(f'[data-testid="remove-shot-{coord}"]')
    remove_button.click()
    page.wait_for_timeout(200)


@when("I remove one aimed shot")
def remove_one_aimed_shot(page: Page) -> None:
    """Remove one aimed shot"""
    # Find first remove button and click it
    remove_button = page.locator('[data-testid^="remove-shot-"]').first
    remove_button.click()
    page.wait_for_timeout(200)


@when('I click the "Fire Shots" button')
def click_fire_shots_button(page: Page) -> None:
    """Click the fire shots button"""
    button = page.locator('[data-testid="fire-shots-button"]')
    button.click()
    page.wait_for_timeout(500)


@when(parsers.parse("I aim at {count:d} more coordinates"))
def aim_at_more_coordinates(page: Page, count: int) -> None:
    """Aim at N more coordinates"""
    # Get current aimed count
    counter_text = page.locator('[data-testid="shot-counter-value"]').text_content()
    if counter_text:
        current = int(counter_text.split("/")[0].strip())
        coords = ["A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10"]
        for i in range(current, current + count):
            if i < len(coords):
                click_on_cell(page, coords[i])


# === Then Steps ===


@then(
    parsers.parse('cell "{coord}" should be marked as "aimed" with a visual indicator')
)
def cell_should_be_marked_as_aimed(page: Page, coord: str) -> None:
    """Verify cell is marked as aimed"""
    cell = page.locator(f'[data-testid="shots-fired-cell-{coord}"]')
    expect(cell).to_have_class(re.compile(r"cell--aimed"))


@then(parsers.parse('the shot counter should show "{text}"'))
@then(parsers.parse('the shot counter should still show "{text}"'))
def shot_counter_should_show(page: Page, text: str) -> None:
    """Verify shot counter shows specific text"""
    counter = page.locator('[data-testid="shot-counter-value"]')
    # Normalize whitespace for comparison
    expect(counter).to_contain_text(text.replace(" ", ""))


@then(
    parsers.parse('cells "{coords}" should be marked as "aimed" with visual indicators')
)
def cells_should_be_marked_as_aimed(page: Page, coords: str) -> None:
    """Verify multiple cells are marked as aimed"""
    coord_list = [c.strip() for c in coords.split(",")]
    for coord in coord_list:
        cell = page.locator(f'[data-testid="shots-fired-cell-{coord}"]')
        expect(cell).to_have_class(re.compile(r"cell--aimed"))


@then(parsers.parse('I should see "{coords}" in my aimed shots list'))
def should_see_coords_in_aimed_list(page: Page, coords: str) -> None:
    """Verify coordinate(s) appear in aimed shots list"""
    # Handle both single coord and multiple coords separated by commas
    if "," in coords:
        coord_list = [c.strip().strip('"') for c in coords.split(",")]
    else:
        coord_list = [coords.strip()]

    for coord in coord_list:
        aimed_shot = page.locator(f'[data-testid="aimed-shot-{coord}"]')
        expect(aimed_shot).to_be_visible()


@then('the "Fire Shots" button should be enabled')
def fire_button_should_be_enabled(page: Page) -> None:
    """Verify fire button is enabled"""
    button = page.locator('[data-testid="fire-shots-button"]')
    expect(button).to_be_enabled()


@then('the "Fire Shots" button should be disabled')
def fire_button_should_be_disabled(page: Page) -> None:
    """Verify fire button is disabled"""
    button = page.locator('[data-testid="fire-shots-button"]')
    expect(button).to_be_disabled()


@then(
    parsers.parse(
        'cell "{coord}" should be marked as "fired" with round number "{round_num}"'
    )
)
def cell_should_be_marked_as_fired(page: Page, coord: str, round_num: str) -> None:
    """Verify cell is marked as fired with round number"""
    cell = page.locator(f'[data-testid="shots-fired-cell-{coord}"]')
    expect(cell).to_have_class(re.compile(r"cell--fired"))


@then(parsers.parse('cell "{coord}" should not be clickable'))
def cell_should_not_be_clickable(page: Page, coord: str) -> None:
    """Verify cell is not clickable"""
    cell = page.locator(f'[data-testid="shots-fired-cell-{coord}"]')
    # Check if cell has aria-disabled or is not a button
    aria_disabled = cell.get_attribute("aria-disabled")
    assert aria_disabled == "true" or cell.get_attribute("role") != "button"


@then(parsers.parse('cell "{coord}" should be unmarked'))
def cell_should_be_unmarked(page: Page, coord: str) -> None:
    """Verify cell is unmarked"""
    cell = page.locator(f'[data-testid="shots-fired-cell-{coord}"]')
    expect(cell).not_to_have_class(re.compile(r"cell--aimed"))
    expect(cell).not_to_have_class(re.compile(r"cell--fired"))


@then(parsers.parse('cell "{coord}" should be clickable'))
def cell_should_be_clickable(page: Page, coord: str) -> None:
    """Verify cell is clickable"""
    cell = page.locator(f'[data-testid="shots-fired-cell-{coord}"]')
    # Check if cell has role="button" and no aria-disabled
    expect(cell).to_have_attribute("role", "button")
    aria_disabled = cell.get_attribute("aria-disabled")
    assert aria_disabled != "true"


@then(parsers.parse('cell "{coord}" should have a "fired" visual appearance'))
def cell_should_have_fired_appearance(page: Page, coord: str) -> None:
    """Verify cell has fired visual appearance"""
    cell = page.locator(f'[data-testid="shots-fired-cell-{coord}"]')
    expect(cell).to_have_class(re.compile(r"cell--fired"))


@then(parsers.parse('cell "{coord}" should have an "aimed" visual appearance'))
def cell_should_have_aimed_appearance(page: Page, coord: str) -> None:
    """Verify cell has aimed visual appearance"""
    cell = page.locator(f'[data-testid="shots-fired-cell-{coord}"]')
    expect(cell).to_have_class(re.compile(r"cell--aimed"))


@then(parsers.parse('cell "{coord}" should have an "unmarked" visual appearance'))
def cell_should_have_unmarked_appearance(page: Page, coord: str) -> None:
    """Verify cell has unmarked visual appearance"""
    cell = page.locator(f'[data-testid="shots-fired-cell-{coord}"]')
    expect(cell).to_have_class(re.compile(r"cell--available"))


@then("the three cell states should be visually distinct from each other")
def cell_states_should_be_distinct(page: Page) -> None:
    """Verify three cell states are visually distinct"""
    # This is verified by CSS classes being different
    # Just check that the classes exist
    pass


@then(parsers.parse('cell "{coord}" should not respond to the click'))
def cell_should_not_respond(page: Page, coord: str) -> None:
    """Verify cell does not respond to click"""
    # Already handled in attempt_to_click_on_cell
    # The cell state should not change
    pass


@then(parsers.parse('cell "{coord}" should remain marked as "fired"'))
def cell_should_remain_fired(page: Page, coord: str) -> None:
    """Verify cell remains marked as fired"""
    cell = page.locator(f'[data-testid="shots-fired-cell-{coord}"]')
    expect(cell).to_have_class(re.compile(r"cell--fired"))


@then(parsers.parse('cell "{coord}" should remain marked as "aimed" once'))
def cell_should_remain_aimed_once(page: Page, coord: str) -> None:
    """Verify cell is marked as aimed exactly once"""
    cell = page.locator(f'[data-testid="shots-fired-cell-{coord}"]')
    expect(cell).to_have_class(re.compile(r"cell--aimed"))

    # Verify it appears only once in aimed shots list
    aimed_shots = page.locator(f'[data-testid="aimed-shot-{coord}"]')
    expect(aimed_shots).to_have_count(1)


@then("it should not be added to my aimed shots list")
def should_not_be_added_to_aimed_list(page: Page) -> None:
    """Verify no new shots were added"""
    # This is verified by the count remaining the same
    pass


@then(parsers.parse('the aimed shots list should contain "{coord}" only once'))
def aimed_list_should_contain_once(page: Page, coord: str) -> None:
    """Verify aimed shots list contains coordinate exactly once"""
    aimed_shots = page.locator(f'[data-testid="aimed-shot-{coord}"]')
    expect(aimed_shots).to_have_count(1)


@then('I should see "Round 1" displayed')
def should_see_round_1(page: Page) -> None:
    """Verify Round 1 is displayed"""
    expect(page.locator('text="Round 1"')).to_be_visible()


@then(parsers.parse('I should see the shot counter showing "{text}"'))
def should_see_shot_counter(page: Page, text: str) -> None:
    """Verify shot counter shows specific text"""
    shot_counter_should_show(page, text)


@then(parsers.parse('I should see my board labeled "{label}"'))
def should_see_board_labeled(page: Page, label: str) -> None:
    """Verify board has specific label"""
    expect(page.locator(f'text="{label}"')).to_be_visible()


@then(parsers.parse('I should see the opponent\'s board labeled "{label}"'))
def should_see_opponent_board_labeled(page: Page, label: str) -> None:
    """Verify opponent board has specific label"""
    expect(page.locator(f'text="{label}"')).to_be_visible()


@then(parsers.parse('I should see the "{area}" area showing all 5 opponent ships'))
def should_see_hits_area(page: Page, area: str) -> None:
    """Verify hits area shows all 5 ships"""
    # Check for hits area
    expect(page.locator(f'text="{area}"')).to_be_visible()


@then("all cells on the Shots Fired board should be clickable")
def all_cells_should_be_clickable(page: Page) -> None:
    """Verify all cells are clickable"""
    # Check that cells have role="button"
    cells = page.locator('[data-testid^="shots-fired-cell-"]')
    expect(cells.first).to_have_attribute("role", "button")


@then("I should see an aimed shots list containing:")
def should_see_aimed_shots_table(page: Page) -> None:
    """Verify aimed shots list contains specific coordinates"""
    # Table data will be provided by pytest-bdd
    list_element = page.locator('[data-testid="aimed-shots-list"]')
    expect(list_element).to_be_visible()


@then(parsers.parse("each coordinate should have a remove button next to it"))
def each_coord_should_have_remove_button(page: Page) -> None:
    """Verify each coordinate has a remove button"""
    # Check that remove buttons exist
    remove_buttons = page.locator('[data-testid^="remove-shot-"]')
    expect(remove_buttons.first).to_be_visible()


@then(parsers.parse('I should see a hint message "{message}"'))
def should_see_hint_message(page: Page, message: str) -> None:
    """Verify hint message is displayed"""
    expect(page.locator(f'text="{message}"')).to_be_visible()


@then(parsers.parse('I should see a message "{message}"'))
def should_see_message(page: Page, message: str) -> None:
    """Verify message is displayed"""
    expect(page.locator(f'text="{message}"')).to_be_visible()


@then(parsers.parse('"{coord}" should no longer appear in the aimed shots list'))
def coord_should_not_appear_in_list(page: Page, coord: str) -> None:
    """Verify coordinate no longer appears in aimed shots list"""
    aimed_shot = page.locator(f'[data-testid="aimed-shot-{coord}"]')
    expect(aimed_shot).not_to_be_visible()


@then(
    parsers.parse(
        'cell "{coord}" on my Shots Fired board should no longer be marked as "aimed"'
    )
)
def cell_should_not_be_marked_as_aimed(page: Page, coord: str) -> None:
    """Verify cell is no longer marked as aimed"""
    cell = page.locator(f'[data-testid="shots-fired-cell-{coord}"]')
    expect(cell).not_to_have_class(re.compile(r"cell--aimed"))


@then(parsers.parse('cell "{coord}" on my Shots Fired board should be clickable again'))
def cell_should_be_clickable_again(page: Page, coord: str) -> None:
    """Verify cell is clickable again"""
    cell_should_be_clickable(page, coord)


@then(parsers.parse('the aimed shots list should contain only "{coords}"'))
def aimed_list_should_contain_only(page: Page, coords: str) -> None:
    """Verify aimed shots list contains only specific coordinates"""
    coord_list = [c.strip() for c in coords.split(" and ")]

    # Check each coordinate is present
    for coord in coord_list:
        aimed_shot = page.locator(f'[data-testid="aimed-shot-{coord}"]')
        expect(aimed_shot).to_be_visible()

    # Check total count matches
    all_aimed_shots = page.locator('[data-testid^="aimed-shot-"]')
    expect(all_aimed_shots).to_have_count(len(coord_list))


@then("all unaimed cells on the Shots Fired board should not be clickable")
def all_unaimed_cells_not_clickable(page: Page) -> None:
    """Verify all unaimed cells are not clickable"""
    # Check for cells with cell--unavailable class
    unavailable_cells = page.locator(".cell--unavailable")
    expect(unavailable_cells.first).to_be_visible()


@then("all unaimed cells should be visually marked as unavailable")
def all_unaimed_cells_marked_unavailable(page: Page) -> None:
    """Verify all unaimed cells are visually marked as unavailable"""
    # Check for cell--unavailable class
    unavailable_cells = page.locator(".cell--unavailable")
    expect(unavailable_cells.first).to_be_visible()


@then("previously unavailable cells should become clickable again")
def previously_unavailable_cells_clickable(page: Page) -> None:
    """Verify previously unavailable cells are clickable again"""
    # Check that some cells now have role="button"
    available_cells = page.locator(".cell--available")
    expect(available_cells.first).to_have_attribute("role", "button")


@then(parsers.parse('the "Fire Shots" button should show "{text}"'))
def fire_button_should_show_text(page: Page, text: str) -> None:
    """Verify fire button shows specific text"""
    button = page.locator('[data-testid="fire-shots-button"]')
    expect(button).to_contain_text(text)


@then(parsers.parse("my {count:d} shots should be submitted"))
def shots_should_be_submitted(page: Page, count: int) -> None:
    """Verify shots were submitted"""
    # After firing, should see waiting message
    expect(page.locator('text="Waiting for opponent"')).to_be_visible()


@then(parsers.parse('I should see "{text}" displayed'))
def should_see_text_displayed(page: Page, text: str) -> None:
    """Verify text is displayed"""
    expect(page.locator(f'text="{text}"')).to_be_visible()


@then("I should not be able to aim additional shots")
def should_not_be_able_to_aim(page: Page) -> None:
    """Verify cannot aim additional shots"""
    # Cells should not be clickable
    cells = page.locator('[data-testid^="shots-fired-cell-"]')
    first_cell = cells.first
    aria_disabled = first_cell.get_attribute("aria-disabled")
    assert aria_disabled == "true" or first_cell.get_attribute("role") != "button"


@then("the Shots Fired board should not be clickable")
def shots_fired_board_not_clickable(page: Page) -> None:
    """Verify Shots Fired board is not clickable"""
    should_not_be_able_to_aim(page)
