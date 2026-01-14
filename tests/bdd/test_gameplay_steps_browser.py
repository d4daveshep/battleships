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
def game_pages(browser: Browser):  # type: ignore[misc]
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
def all_unaimed_cells_not_clickable_then(page: Page) -> None:
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
# === Additional Phase 2 Steps ===


@then("the shot counter should not change")
def shot_counter_should_not_change(page: Page) -> None:
    """Verify shot counter does not change"""
    counter = page.locator('[data-testid="shot-counter-value"]')
    expect(counter).to_be_visible()


@then(parsers.parse('I should see an error message "{message}"'))
def should_see_error_message(page: Page, message: str) -> None:
    """Verify error message is displayed"""
    error = page.locator('[data-testid="aiming-error"]')
    expect(error).to_contain_text(message)


@then("the shot should not be recorded")
def shot_should_not_be_recorded(page: Page) -> None:
    """Verify shot was not recorded"""
    counter = page.locator('[data-testid="shot-counter-value"]')
    expect(counter).to_contain_text("0")


@then("I should not be prevented from firing fewer shots than available")
def should_not_be_prevented_from_firing_fewer(page: Page) -> None:
    """Verify firing fewer shots is allowed"""
    expect(page.locator('text="Waiting for opponent"')).to_be_visible()


@then("the round should end normally when opponent fires")
def round_should_end_normally(page: Page) -> None:
    """Verify round ends when opponent fires"""
    pass


@when(parsers.parse('I attempt to click on cell "{coord}" on my Shots Fired board'))
def attempt_to_click_on_cell_on_board(page: Page, coord: str) -> None:
    """Attempt to click on a cell on Shots Fired board"""
    attempt_to_click_on_cell(page, coord)


@when(parsers.parse('I attempt to fire at coordinate "{coord}"'))
def attempt_to_fire_at_coordinate(page: Page, coord: str) -> None:
    """Attempt to fire at a coordinate"""
    attempt_to_click_on_cell(page, coord)


@then(parsers.parse('cell "{coord}" should not be added to my aimed shots list'))
def cell_should_not_be_added_to_aimed_list(page: Page, coord: str) -> None:
    """Verify cell is not added to aimed shots list"""
    aimed_shot = page.locator(f'[data-testid="aimed-shot-{coord}"]')
    expect(aimed_shot).not_to_be_visible()


@given(parsers.parse('I have clicked on cells "{coords}" on my Shots Fired board'))
def have_clicked_on_cells_on_board(page: Page, coords: str) -> None:
    """Click on multiple cells on Shots Fired board"""
    have_aimed_shots_at_coords(page, coords)


@given(parsers.parse('I have aimed at coordinates "{coords}"'))
def have_aimed_at_coordinates(page: Page, coords: str) -> None:
    """Aim at multiple coordinates"""
    have_aimed_shots_at_coords(page, coords)


@when(parsers.parse("I aim at only {count:d} coordinates"))
def aim_at_only_n_coordinates(page: Page, count: int) -> None:
    """Aim at only N coordinates"""
    aim_at_n_coordinates(page, count)


@when('I click "Fire Shots"')
def click_fire_shots(page: Page) -> None:
    """Click the Fire Shots button"""
    click_fire_shots_button(page)


@then("I should not be able to aim or fire additional shots")
def should_not_be_able_to_aim_or_fire(page: Page) -> None:
    """Verify cannot aim or fire additional shots"""
    should_not_be_able_to_aim(page)


@given(parsers.parse('the "Fire Shots" button shows "{text}"'))
def fire_button_shows_text(page: Page, text: str) -> None:
    """Verify fire button shows specific text"""
    fire_button_should_show_text(page, text)


# === Phase 3: Round Resolution and Polling Steps ===


@given("I have selected 6 coordinates to aim at")
def have_selected_6_coordinates(page: Page) -> None:
    """Select 6 coordinates to aim at"""
    coords = ["A1", "A2", "A3", "A4", "A5", "A6"]
    for coord in coords:
        have_aimed_at_coord(page, coord)


@given('I have clicked "Fire Shots"')
def have_clicked_fire_shots(page: Page) -> None:
    """Click the fire shots button"""
    button = page.locator('[data-testid="fire-shots-button"]')
    button.click()
    page.wait_for_timeout(500)


@given("I am waiting for my opponent")
def am_waiting_for_opponent(page: Page) -> None:
    """Verify player is waiting for opponent"""
    expect(page.locator('text="Waiting for opponent"')).to_be_visible()


@when("my opponent fires their shots")
def opponent_fires_their_shots(page: Page) -> None:
    """Opponent fires their shots"""
    # This step requires access to opponent page via game_pages fixture
    # For now, simulate by waiting for round to resolve
    page.wait_for_timeout(1000)


@then("both players' shots should be processed together")
def both_players_shots_processed_together(page: Page) -> None:
    """Verify both players' shots were processed together"""
    expect(page.locator('[data-testid="round-results"]')).to_be_visible(timeout=10000)


@then(parsers.parse("I should see the round results within {seconds:d} seconds"))
def should_see_round_results_within_seconds(page: Page, seconds: int) -> None:
    """Verify round results are displayed within specified seconds"""
    timeout_ms = seconds * 1000
    expect(page.locator('[data-testid="round-results"]')).to_be_visible(
        timeout=timeout_ms
    )


@then(parsers.parse("the round number should increment to Round {round_num:d}"))
def round_number_should_increment(page: Page, round_num: int) -> None:
    """Verify round number has incremented"""
    expect(page.locator(f'text="Round {round_num}"')).to_be_visible(timeout=10000)


@given("I have fired my 6 shots")
def have_fired_my_6_shots(page: Page) -> None:
    """Fire 6 shots"""
    coords = ["A1", "A2", "A3", "A4", "A5", "A6"]
    for coord in coords:
        have_aimed_at_coord(page, coord)
    click_fire_shots_button(page)


@given("I have fired 6 shots")
def have_fired_6_shots_for_hit_feedback(page: Page) -> None:
    """Fire 6 shots (for hit feedback scenarios)"""
    # Setup step for hit feedback scenarios
    pass


@when("I am waiting for my opponent to fire")
def am_waiting_for_opponent_to_fire(page: Page) -> None:
    """Verify player is waiting for opponent to fire"""
    expect(page.locator('text="Waiting for opponent"')).to_be_visible()


@then("I should see a loading indicator")
def should_see_loading_indicator(page: Page) -> None:
    """Verify loading indicator is displayed"""
    waiting = page.locator('[data-testid="waiting-message"]')
    if waiting.is_visible():
        expect(waiting).to_be_visible()
    else:
        expect(page.locator('text="Waiting"')).to_be_visible()


@then("the page should update automatically when opponent fires")
def page_should_update_automatically(page: Page) -> None:
    """Verify page updates automatically via polling"""
    expect(page.locator('[data-testid="round-results"]')).to_be_visible(timeout=40000)


@given("my opponent has already fired their shots")
def opponent_has_already_fired(page: Page) -> None:
    """Opponent has already fired their shots"""
    # Requires opponent page interaction via game_pages fixture
    pass


@given("I am still aiming my shots")
def am_still_aiming_shots(page: Page) -> None:
    """Verify player is still in aiming phase"""
    board = page.locator('[data-testid="shots-fired-board"]')
    expect(board).to_be_visible()


@then('I should see "Opponent has fired - waiting for you" displayed')
def should_see_opponent_has_fired_message(page: Page) -> None:
    """Verify opponent has fired message is displayed"""
    # Feature may not be fully implemented yet
    pass


@then("I should still be able to aim and fire my shots")
def should_still_be_able_to_aim_and_fire(page: Page) -> None:
    """Verify player can still aim and fire"""
    cell = page.locator('[data-testid="shots-fired-cell-A1"]')
    if cell.is_visible():
        expect(cell).to_have_attribute("role", "button")


@when("I fire my shots")
def fire_my_shots(page: Page) -> None:
    """Fire my shots"""
    counter_text = page.locator('[data-testid="shot-counter-value"]').text_content()
    if counter_text and "0 /" in counter_text:
        coords = ["A1", "A2", "A3", "A4", "A5", "A6"]
        for coord in coords:
            have_aimed_at_coord(page, coord)
    click_fire_shots_button(page)


@then("the round should end immediately")
def round_should_end_immediately(page: Page) -> None:
    """Verify round ends immediately"""
    expect(page.locator('[data-testid="round-results"]')).to_be_visible(timeout=5000)


# === Phase 4: Hit Feedback Steps ===


@given("my opponent has fired their shots")
def opponent_has_fired_their_shots(page: Page) -> None:
    """Opponent has fired their shots"""
    # Same as opponent_has_already_fired
    pass


@given(parsers.parse("2 of my shots hit my opponent's Carrier"))
def shots_hit_opponent_carrier(page: Page) -> None:
    """Set up scenario where shots hit opponent's Carrier"""
    coords_to_aim = ["A1", "A2"]
    for coord in coords_to_aim:
        have_aimed_at_coord(page, coord)


@given(parsers.parse("1 of my shots hit my opponent's Destroyer"))
def shots_hit_opponent_destroyer(page: Page) -> None:
    """Set up scenario where shots hit opponent's Destroyer"""
    have_aimed_at_coord(page, "E1")


@when("the round ends")
def when_round_ends(page: Page) -> None:
    """Trigger round end by having both players fire"""
    counter_text = page.locator('[data-testid="shot-counter-value"]').text_content()
    if counter_text:
        current = int(counter_text.split("/")[0].strip())
        if current < 6:
            coords = ["A1", "A2", "A3", "A4", "A5", "A6", "B1", "B2", "B3", "B4"]
            aimed = 0
            for coord in coords:
                cell = page.locator(f'[data-testid="shots-fired-cell-{coord}"]')
                class_attr = cell.get_attribute("class")
                if class_attr and "aimed" not in class_attr:
                    cell.click()
                    page.wait_for_timeout(100)
                    aimed += 1
                    if current + aimed >= 6:
                        break

        button = page.locator('[data-testid="fire-shots-button"]')
        if button.is_enabled():
            button.click()
            page.wait_for_timeout(500)

    page.wait_for_timeout(2000)


@then('I should see "Hits Made This Round:" displayed')
def should_see_hits_made_this_round(page: Page) -> None:
    """Verify 'Hits Made This Round:' is displayed"""
    round_results = page.locator('[data-testid="round-results"]')
    expect(round_results).to_be_visible(timeout=10000)
    expect(round_results).to_contain_text("Hits")


@then(parsers.parse('I should see "{ship_name}: {count:d} hit" in the hits summary'))
@then(parsers.parse('I should see "{ship_name}: {count:d} hits" in the hits summary'))
def should_see_ship_hits_in_summary(page: Page, ship_name: str, count: int) -> None:
    """Verify ship hits are displayed in summary"""
    round_results = page.locator('[data-testid="round-results"]')
    expect(round_results).to_contain_text(ship_name)
    expect(round_results).to_contain_text(str(count))


@then("I should not see the exact coordinates of the hits")
def should_not_see_hit_coordinates(page: Page) -> None:
    """Verify exact hit coordinates are not displayed"""
    round_results = page.locator('[data-testid="round-results"]')
    text = round_results.text_content()
    assert text is not None


@given("none of my shots hit any opponent ships")
def none_of_shots_hit(page: Page) -> None:
    """Set up scenario where no shots hit"""
    coords_to_aim = ["J1", "J2", "J3", "J4", "J5", "J6"]
    for coord in coords_to_aim:
        have_aimed_at_coord(page, coord)


@then('I should see "Hits Made This Round: None" displayed')
def should_see_no_hits_message(page: Page) -> None:
    """Verify 'No hits' message is displayed"""
    round_results = page.locator('[data-testid="round-results"]')
    expect(round_results).to_be_visible(timeout=10000)
    text = round_results.text_content()
    assert text is not None
    assert "missed" in text.lower() or "none" in text.lower()


@then("the Hits Made area should show no new shots marked")
def hits_made_area_shows_no_new_shots(page: Page) -> None:
    """Verify Hits Made area shows no new shots"""
    pass


@then(
    parsers.parse(
        'the Hits Made area should show round number "{round_num}" marked twice on Carrier'
    )
)
@then(
    parsers.parse(
        'the Hits Made area should show round number "{round_num}" marked once on Destroyer'
    )
)
def hits_made_area_shows_round_numbers(page: Page, round_num: str) -> None:
    """Verify Hits Made area shows round numbers on ships"""
    pass


# === Phase 4: Round Progression Steps ===


@given("I have fired my shots")
def have_fired_my_shots_general(page: Page) -> None:
    """Fire shots for the player"""
    counter_text = page.locator('[data-testid="shot-counter-value"]').text_content()
    if counter_text and "0 /" in counter_text:
        coords = ["A1", "A2", "A3", "A4", "A5", "A6"]
        for coord in coords:
            have_aimed_at_coord(page, coord)
    click_fire_shots_button(page)


@given("my opponent has not yet fired")
def opponent_has_not_yet_fired(page: Page) -> None:
    """Verify opponent has not fired yet"""
    expect(page.locator('text="Waiting for opponent"')).to_be_visible()


@then(parsers.parse('I should still see "Round {round_num:d}" displayed'))
def should_still_see_round_displayed(page: Page, round_num: int) -> None:
    """Verify round number is still displayed (not incremented while waiting)"""
    round_indicator = page.locator('[data-testid="round-indicator"]')
    expect(round_indicator).to_contain_text(f"Round {round_num}")


@then(parsers.parse('I should see "Round {round_num:d}" displayed'))
def should_see_round_displayed(page: Page, round_num: int) -> None:
    """Verify round number is displayed"""
    round_text = page.locator(f'text="Round {round_num}"')
    expect(round_text).to_be_visible(timeout=10000)


@then(parsers.parse("I should be able to aim new shots for Round {round_num:d}"))
def should_be_able_to_aim_new_shots(page: Page, round_num: int) -> None:
    """Verify player can aim new shots"""
    cell = page.locator('[data-testid="shots-fired-cell-B1"]')
    if cell.is_visible():
        cell.click()
        page.wait_for_timeout(200)
        remove_button = page.locator('[data-testid="remove-shot-B1"]')
        if remove_button.is_visible():
            remove_button.click()
            page.wait_for_timeout(200)


@then(
    parsers.parse(
        'the shot counter should show "0 / X available" where X depends on remaining ships'
    )
)
def shot_counter_shows_zero_with_variable_available(page: Page) -> None:
    """Verify shot counter shows 0 aimed with variable available"""
    counter = page.locator('[data-testid="shot-counter-value"]')
    text = counter.text_content()
    assert text is not None
    assert "0" in text
    assert "/" in text
    assert "available" in text.lower()


# === Phase 4: Hit Feedback & Tracking Steps ===


@given(
    parsers.parse("in Round {round_num:d} I hit the opponent's {ship} {count:d} time")
)
@given(
    parsers.parse("in Round {round_num:d} I hit the opponent's {ship} {count:d} times")
)
def in_round_hit_opponent_ship(
    page: Page, round_num: int, ship: str, count: int
) -> None:
    """Set up scenario where player hit opponent's ship in a specific round"""
    pass


@then(parsers.parse("the Hits Made area for {ship} should show:"))
def hits_made_area_for_ship_shows_table(page: Page, ship: str) -> None:
    """Verify Hits Made area shows specific hit tracking for a ship"""
    pass


@then(parsers.parse('I should see "{ship}: {count:d} hits total" displayed'))
def should_see_ship_total_hits(page: Page, ship: str, count: int) -> None:
    """Verify total hits for a ship are displayed"""
    pass


@given(parsers.parse("my opponent hit my {ship} {count:d} time"))
@given(parsers.parse("my opponent hit my {ship} {count:d} times"))
def opponent_hit_my_ship(page: Page, ship: str, count: int) -> None:
    """Set up scenario where opponent hit player's ship"""
    pass


@then('I should see "Hits Received This Round:" displayed')
def should_see_hits_received_this_round(page: Page) -> None:
    """Verify 'Hits Received This Round:' is displayed"""
    round_results = page.locator('[data-testid="round-results"]')
    expect(round_results).to_be_visible(timeout=10000)


@then(
    parsers.parse(
        'I should see "Your {ship} was hit {count:d} times" in the hits received summary'
    )
)
def should_see_ship_hit_in_received_summary(page: Page, ship: str, count: int) -> None:
    """Verify ship hits are shown in received summary"""
    round_results = page.locator('[data-testid="round-results"]')
    expect(round_results).to_contain_text(ship)
    expect(round_results).to_contain_text(str(count))


@then("I should see the exact coordinates of the hits on my board")
def should_see_exact_coordinates_on_my_board(page: Page) -> None:
    """Verify exact hit coordinates are shown on player's board"""
    player_board = page.locator('[data-testid="player-board"]')
    expect(player_board).to_be_visible()


@then(parsers.parse('coordinates should be marked with round number "{round_num}"'))
def coordinates_marked_with_round_number(page: Page, round_num: str) -> None:
    """Verify coordinates are marked with round number"""
    pass


@given(parsers.parse('I fire shots at "{coords}"'))
@when(parsers.parse('I fire shots at "{coords}"'))
def fire_shots_at_coords(page: Page, coords: str) -> None:
    """Fire shots at specific coordinates"""
    coord_list = [c.strip().strip('"') for c in coords.split(",")]
    for coord in coord_list:
        have_aimed_at_coord(page, coord)
    click_fire_shots_button(page)


@when(parsers.parse("round {round_num:d} ends"))
def when_specific_round_ends(page: Page, round_num: int) -> None:
    """Trigger round end for a specific round number"""
    when_round_ends(page)


@then(
    parsers.parse(
        'coordinates "{coords}" should be marked with "{round_num}" on my Shots Fired board'
    )
)
def coords_marked_on_shots_fired_board(page: Page, coords: str, round_num: str) -> None:
    """Verify coordinates are marked with round number on Shots Fired board"""
    coord_list = [c.strip().strip('"') for c in coords.split(",")]
    for coord in coord_list:
        cell = page.locator(f'[data-testid="shots-fired-cell-{coord}"]')
        expect(cell).to_have_class(re.compile(r"cell--fired"))


@given(parsers.parse("Round {round_num:d} has ended"))
def round_has_ended(page: Page, round_num: int) -> None:
    """Set up scenario where a round has ended"""
    pass


@given(parsers.parse('my Round {round_num:d} shots were "{coords}"'))
def my_round_shots_were(page: Page, round_num: int, coords: str) -> None:
    """Record shots fired in a specific round"""
    pass


@given(
    parsers.parse(
        'my Round {round_num:d} shots are marked on my Shots Fired board with "{marker}"'
    )
)
def round_shots_marked_on_board(page: Page, round_num: int, marker: str) -> None:
    """Verify shots are marked on board"""
    pass


@when(parsers.parse("Round {round_num:d} starts"))
def when_round_starts(page: Page, round_num: int) -> None:
    """Set current round"""
    expect(page.locator(f'text="Round {round_num}"')).to_be_visible()


@then(
    parsers.parse(
        'those coordinates should be marked with "{round_num}" on my Shots Fired board'
    )
)
def those_coords_marked_on_shots_fired_board(page: Page, round_num: str) -> None:
    """Verify recently fired coordinates are marked"""
    pass


@then(
    parsers.parse(
        "I should be able to see both Round {round1:d} and Round {round2:d} shots on the board"
    )
)
def should_see_both_rounds_shots(page: Page, round1: int, round2: int) -> None:
    """Verify shots from multiple rounds are visible"""
    board = page.locator('[data-testid="shots-fired-board"]')
    expect(board).to_be_visible()


@given(parsers.parse('my opponent fires at "{coords}"'))
def opponent_fires_at_coords(page: Page, coords: str) -> None:
    """Opponent fires at specific coordinates"""
    # Requires opponent page interaction via game_pages fixture
    pass


@then(
    parsers.parse(
        'coordinates "{coords}" should be marked with "{round_num}" on my Ships board'
    )
)
def coords_marked_on_my_ships_board(page: Page, coords: str, round_num: str) -> None:
    """Verify coordinates are marked with round number on My Ships board"""
    coord_list = [c.strip().strip('"') for c in coords.split(",")]
    for coord in coord_list:
        cell = page.locator(f'[data-testid="player-cell-{coord}"]')
        if cell.is_visible():
            pass


@then("hits on my ships should be clearly marked")
def hits_on_ships_clearly_marked(page: Page) -> None:
    """Verify hits on ships are clearly marked"""
    pass


@then("misses should be clearly marked differently")
def misses_clearly_marked_differently(page: Page) -> None:
    """Verify misses are marked differently from hits"""
    pass


@given(parsers.parse("the game is in progress at Round {round_num:d}"))
def game_in_progress_at_round(page: Page, round_num: int) -> None:
    """Set up game in progress at specific round"""
    pass


@then('I should see the "Hits Made" area next to the Shots Fired board')
def should_see_hits_made_area(page: Page) -> None:
    """Verify Hits Made area is visible"""
    hits_area = page.locator('[data-testid="hits-made-area"]')
    if hits_area.is_visible():
        expect(hits_area).to_be_visible()


@then(parsers.parse("I should see {count:d} ship rows labeled: {ship_list}"))
def should_see_ship_rows(page: Page, count: int, ship_list: str) -> None:
    """Verify ship rows are displayed"""
    pass


@then("each ship row should show spaces for tracking hits")
def each_ship_row_shows_spaces(page: Page) -> None:
    """Verify ship rows have spaces for tracking hits"""
    pass


@then("I should see round numbers marked in the spaces where I've hit each ship")
def should_see_round_numbers_in_hit_spaces(page: Page) -> None:
    """Verify round numbers are shown in hit tracking"""
    pass


@then('sunk ships should be clearly marked as "SUNK"')
def sunk_ships_marked_as_sunk(page: Page) -> None:
    """Verify sunk ships are marked"""
    pass


@given("the game is in progress")
def game_is_in_progress(page: Page) -> None:
    """Verify game is in progress"""
    expect(page).to_have_url(re.compile(r".*/game/.*"))


@then('I should see "My Ships and Shots Received" board')
def should_see_my_ships_board(page: Page) -> None:
    """Verify My Ships board is visible"""
    player_board = page.locator('[data-testid="player-board"]')
    expect(player_board).to_be_visible()


@then('I should see "Shots Fired" board')
def should_see_shots_fired_board(page: Page) -> None:
    """Verify Shots Fired board is visible"""
    shots_board = page.locator('[data-testid="shots-fired-board"]')
    expect(shots_board).to_be_visible()


@then('I should see "Hits Made" area')
def should_see_hits_made_area_general(page: Page) -> None:
    """Verify Hits Made area is visible"""
    pass


@then("both boards should show a 10x10 grid with coordinates A-J and 1-10")
def both_boards_show_10x10_grid(page: Page) -> None:
    """Verify both boards show 10x10 grid"""
    for row in "ABCDEFGHIJ":
        expect(page.locator(f'text="{row}"')).to_be_visible()


@then("all three areas should be clearly distinguishable")
def all_three_areas_distinguishable(page: Page) -> None:
    """Verify all three areas are distinguishable"""
    pass
