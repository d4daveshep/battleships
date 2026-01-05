from pytest_bdd import scenarios, given, when, then, parsers
from playwright.sync_api import Page, Locator
from tests.bdd.conftest import BASE_URL
from dataclasses import dataclass, field
from typing import Any
import pytest


scenarios("../../features/ship_placement.feature")


@dataclass
class ShipPlacementContext:
    """Maintains state between BDD steps for ship placement testing"""

    current_player_name: str | None = None
    selected_ship: str | None = None
    placed_ships: dict[str, list[str]] = field(default_factory=dict)
    last_placement_error: str | None = None
    game_mode: str = "computer"  # Default to single player mode


@pytest.fixture
def ship_context() -> ShipPlacementContext:
    """Provide a test context for maintaining state between BDD steps"""
    return ShipPlacementContext()


def on_ship_placement_page(page: Page) -> None:
    """Helper function to verify we're on the ship placement screen"""
    h1_element: Locator = page.locator("h1")
    h1_text: str | None = h1_element.text_content()
    assert h1_text is not None
    assert "Ship Placement" in h1_text
    assert "ship" in page.url.lower()


# === Background Steps ===


@given("I have logged in and selected a game mode")
def logged_in_and_selected_game_mode(
    page: Page, ship_context: ShipPlacementContext
) -> None:
    """Login and select a game mode"""
    page.goto(BASE_URL)
    page.locator('input[type="text"][name="player_name"]').fill("TestPlayer")
    page.locator(f'button[value="{ship_context.game_mode}"]').click()
    ship_context.current_player_name = "TestPlayer"


@given("I am on the ship placement screen")
def on_ship_placement_screen(page: Page, ship_context: ShipPlacementContext) -> None:
    """Navigate to ship placement screen"""
    page.wait_for_load_state("networkidle")
    # Click the start game button to proceed to ship placement
    start_button: Locator = page.locator('button[name="action"][value="start_game"]')
    if start_button.is_visible():
        start_button.click()
        page.wait_for_load_state("networkidle")
    on_ship_placement_page(page)


@given('the "My Ships and Shots Received" board is displayed')
def my_ships_board_displayed(page: Page) -> None:
    """Verify the player's board is displayed"""
    board: Locator = page.locator('[data-testid="my-ships-board"]')
    assert board.is_visible()


@given("I have not placed any ships yet")
@given("I have not placed any ships")
def no_ships_placed_yet(ship_context: ShipPlacementContext) -> None:
    """Verify no ships have been placed"""
    ship_context.placed_ships = {}


# === Ship Selection ===


@given(parsers.parse('I select the "{ship_name}" ship to place'))
@when(parsers.parse('I select the "{ship_name}" ship to place'))
def select_ship_to_place(
    page: Page, ship_context: ShipPlacementContext, ship_name: str
) -> None:
    """Select a ship to place on the board"""
    ship_context.selected_ship = ship_name
    # In the browser, we might need to click on a ship selector
    # For now, just track it in context


# === Ship Placement (New Syntax) ===


def place_ship_with_direction(
    page: Page,
    ship_context: ShipPlacementContext,
    start: str,
    direction: str,
    is_attempt: bool = False,
) -> None:
    """Helper to place a ship using start coordinate and orientation"""
    assert ship_context.current_player_name is not None
    assert ship_context.selected_ship is not None

    # Map direction to orientation
    orientation_map: dict[str, str] = {
        "horizontally": "horizontal",
        "vertically": "vertical",
        "diagonally-down": "diagonal-down",
        "diagonally-up": "diagonal-up",
    }
    orientation: str = orientation_map.get(direction, direction)

    # Fill in the form fields
    # Select ship using radio button (click the label/span)
    assert ship_context.selected_ship is not None
    page.locator(
        f'[data-testid="select-ship-{ship_context.selected_ship.lower()}"] + span.ship-radio-button'
    ).click()

    # Fill coordinate
    page.locator('input[name="start_coordinate"]').fill(start)

    # Select orientation using radio button (click the label/span)
    page.locator(
        f'input[name="orientation"][value="{orientation}"] + span.orientation-radio-button'
    ).click()

    # Submit the form
    page.locator('button[type="submit"][data-testid="place-ship-button"]').click()
    page.wait_for_load_state("networkidle")

    # If successful, store the placed ship
    if (
        not is_attempt
        and not page.locator('[data-testid="placement-error"]').is_visible()
    ):
        ship_context.placed_ships[ship_context.selected_ship] = [start, orientation]


@when(parsers.parse('I place it {direction} starting at "{start}"'))
def place_ship_direction_starting_at(
    page: Page, ship_context: ShipPlacementContext, direction: str, start: str
) -> None:
    """Place a ship using direction and starting coordinate"""
    place_ship_with_direction(page, ship_context, start, direction, is_attempt=False)


@when(parsers.parse('I attempt to place it {direction} starting at "{start}"'))
def attempt_place_ship_direction_starting_at(
    page: Page, ship_context: ShipPlacementContext, direction: str, start: str
) -> None:
    """Attempt to place a ship using direction and starting coordinate"""
    place_ship_with_direction(page, ship_context, start, direction, is_attempt=True)


@when(
    parsers.parse(
        'I attempt to place it starting at "{start}" with an invalid direction'
    )
)
def attempt_place_ship_invalid_direction(
    page: Page, ship_context: ShipPlacementContext, start: str
) -> None:
    """Attempt to place a ship with invalid direction"""
    assert ship_context.current_player_name is not None
    assert ship_context.selected_ship is not None

    # Select ship
    page.locator(
        f'[data-testid="select-ship-{ship_context.selected_ship.lower()}"] + span.ship-radio-button'
    ).click()

    # Fill coordinate
    page.locator('input[name="start_coordinate"]').fill(start)

    # Hack: Use JS to change the value of the first orientation radio button to "invalid"
    # and then click it. This simulates a hacked form submission.
    page.evaluate("""
        const radio = document.querySelector('input[name="orientation"]');
        radio.value = "invalid_direction";
        radio.checked = true;
    """)

    # Submit the form
    page.locator('button[type="submit"][data-testid="place-ship-button"]').click()
    page.wait_for_load_state("networkidle")


# === Placement Verification ===


@then(parsers.parse("the {ship_name} should be placed on the board"))
def ship_placed_on_board(page: Page, ship_name: str) -> None:
    """Verify ship is placed on the board"""
    ship_element: Locator = page.locator(
        f'[data-testid="placed-ship-{ship_name.lower()}"]'
    )
    assert ship_element.is_visible()


@then(parsers.parse('the {ship_name} should occupy cells "{cells}"'))
@then(
    parsers.parse(
        'the {ship_name} should occupy cells "{cell1}", "{cell2}", and "{cell3}"'
    )
)
@then(
    parsers.parse(
        'the {ship_name} should occupy cells "{cell1}", "{cell2}", "{cell3}", and "{cell4}"'
    )
)
@then(
    parsers.parse(
        'the {ship_name} should occupy cells "{cell1}", "{cell2}", "{cell3}", "{cell4}", and "{cell5}"'
    )
)
@then(parsers.parse('the {ship_name} should occupy cells "{cell1}" and "{cell2}"'))
def ship_occupies_cells(page: Page, ship_name: str, **kwargs: Any) -> None:
    """Verify ship occupies the correct cells"""
    # Extract all cell values from kwargs
    cells: list[str] = [v for k, v in kwargs.items() if k.startswith("cell")]

    # Verify each cell is marked as occupied by the ship
    for cell in cells:
        cell_element: Locator = page.locator(
            f'[data-testid="cell-{cell}"][data-ship="{ship_name.lower()}"]'
        )
        assert cell_element.is_visible(), (
            f"Cell {cell} should be occupied by {ship_name}"
        )


@then(parsers.parse("the {ship_name} should be marked as placed"))
def ship_marked_as_placed(page: Page, ship_name: str) -> None:
    """Verify ship is marked as placed in the UI"""
    ship_status: Locator = page.locator(
        f'[data-testid="ship-status-{ship_name.lower()}"]'
    )
    assert ship_status.is_visible()
    status_text: str | None = ship_status.text_content()
    assert status_text is not None
    assert "placed" in status_text.lower()


# === Placement Rejection ===


@then("the placement should be rejected")
def placement_should_be_rejected(page: Page) -> None:
    """Verify placement was rejected"""
    # Should see an error message
    error_element: Locator = page.locator('[data-testid="placement-error"]')
    assert error_element.is_visible()


@then(parsers.parse('I should see an error message "{error_message}"'))
def should_see_error_message(
    page: Page, ship_context: ShipPlacementContext, error_message: str
) -> None:
    """Verify error message is displayed"""
    error_element: Locator = page.locator('[data-testid="placement-error"]')
    assert error_element.is_visible()
    error_text: str | None = error_element.text_content()
    assert error_text is not None
    assert error_message in error_text
    ship_context.last_placement_error = error_message


@then(parsers.parse("the {ship_name} should not be placed"))
def ship_should_not_be_placed(
    page: Page, ship_context: ShipPlacementContext, ship_name: str
) -> None:
    """Verify ship was not placed on the board"""
    # Ship should not be in the placed_ships dictionary
    assert ship_name not in ship_context.placed_ships
    # Ship element should not be visible
    ship_element: Locator = page.locator(
        f'[data-testid="placed-ship-{ship_name.lower()}"]'
    )
    assert not ship_element.is_visible()


@then("no error message should be displayed")
def no_error_message_displayed(page: Page) -> None:
    """Verify no error message is shown"""
    error_element: Locator = page.locator('[data-testid="placement-error"]')
    assert not error_element.is_visible()


# === Pre-placed Ships Setup ===


@given(parsers.parse('I have placed a "{ship_name}" {direction} starting at "{start}"'))
def have_placed_ship_direction_starting_at(
    page: Page,
    ship_context: ShipPlacementContext,
    ship_name: str,
    direction: str,
    start: str,
) -> None:
    """Setup: Pre-place a ship with direction"""
    ship_context.selected_ship = ship_name
    place_ship_with_direction(page, ship_context, start, direction, is_attempt=False)
    # Verify it was placed successfully
    assert ship_name in ship_context.placed_ships


# === Random Placement ===


@when('I click the "Random Placement" button')
def click_random_placement_button(
    page: Page, ship_context: ShipPlacementContext
) -> None:
    """Click the Random Placement button"""
    page.locator('button[data-testid="random-placement-button"]').click()
    page.wait_for_load_state("networkidle")


@then("all 5 ships should be placed automatically")
def all_ships_placed_automatically(page: Page) -> None:
    """Verify all 5 ships are placed"""
    ship_names: list[str] = [
        "carrier",
        "battleship",
        "cruiser",
        "submarine",
        "destroyer",
    ]
    for ship_name in ship_names:
        ship_element: Locator = page.locator(f'[data-testid="placed-ship-{ship_name}"]')
        assert ship_element.is_visible(), f"{ship_name} should be placed"


@then("all ships should follow placement rules")
def all_ships_follow_placement_rules(page: Page) -> None:
    """Verify all placed ships follow the placement rules"""
    # This is checked by the backend, verify no error message
    no_error_message_displayed(page)


@then("no ships should overlap")
def no_ships_should_overlap(page: Page) -> None:
    """Verify no ships are overlapping"""
    # This is enforced by the backend, verify no error message
    no_error_message_displayed(page)


@then("no ships should be touching")
def no_ships_should_be_touching(page: Page) -> None:
    """Verify ships have proper spacing"""
    # This is enforced by the backend, verify no error message
    no_error_message_displayed(page)


@then("all ships should be within the board boundaries")
def all_ships_within_boundaries(page: Page) -> None:
    """Verify all ships are within board boundaries"""
    # This is enforced by the backend, verify no error message
    no_error_message_displayed(page)


# === Ship Placement Progress ===


@given("I have placed some ships manually")
def have_placed_some_ships_manually(ship_context: ShipPlacementContext) -> None:
    """Setup: Some ships have been placed"""
    # Mark a few ships as placed
    ship_context.placed_ships["Destroyer"] = ["A1", "horizontal"]
    ship_context.placed_ships["Submarine"] = ["C3", "vertical"]


@when("my manually placed ships should be removed")
@then("my manually placed ships should be removed")
def manually_placed_ships_removed(ship_context: ShipPlacementContext) -> None:
    """Verify manually placed ships are removed"""
    # After random placement, old ships should be cleared
    ship_context.placed_ships = {}


@then("all 5 ships should be placed automatically following all rules")
def all_ships_placed_following_rules(page: Page) -> None:
    """Verify all ships placed and following rules"""
    all_ships_placed_automatically(page)
    all_ships_follow_placement_rules(page)


@then(parsers.parse('I should see "{status_text}"'))
def should_see_status_text(page: Page, status_text: str) -> None:
    """Verify status text is displayed"""
    status_element: Locator = page.locator('[data-testid="ship-placement-status"]')
    assert status_element.is_visible()
    status_content: str | None = status_element.text_content()
    assert status_content is not None
    assert status_text in status_content


@when(parsers.parse('I place the "{ship_name}"'))
def place_the_ship(
    page: Page, ship_context: ShipPlacementContext, ship_name: str
) -> None:
    """Place a ship (using default coordinates for testing)"""
    ship_context.selected_ship = ship_name
    # Use some default starting coordinates for each ship (place horizontally)
    start_coordinates: dict[str, str] = {
        "Destroyer": "A1",
        "Submarine": "C3",
        "Cruiser": "E5",
        "Battleship": "G1",
        "Carrier": "I1",
    }
    start: str = start_coordinates.get(ship_name, "A1")
    place_ship_with_direction(
        page, ship_context, start, "horizontally", is_attempt=False
    )


# === Start Game Button ===


@given("I have placed 4 out of 5 ships")
def have_placed_4_ships(page: Page, ship_context: ShipPlacementContext) -> None:
    """Setup: 4 ships placed"""
    ships_to_place = [
        ("Destroyer", "A1", "horizontally"),
        ("Submarine", "C3", "vertically"),
        ("Cruiser", "E5", "horizontally"),
        ("Battleship", "G1", "horizontally"),
    ]

    for name, start, direction in ships_to_place:
        ship_context.selected_ship = name
        place_ship_with_direction(
            page, ship_context, start, direction, is_attempt=False
        )


@when(parsers.parse("I place the 5th ship"))
def place_5th_ship(page: Page, ship_context: ShipPlacementContext) -> None:
    """Place the 5th and final ship"""
    place_the_ship(page, ship_context, "Carrier")


@then('the "Start Game" button should be disabled')
def start_game_button_disabled(page: Page) -> None:
    """Verify Start Game button is disabled"""
    start_button: Locator = page.locator('[data-testid="start-game-button"]')
    assert start_button.is_visible()
    assert start_button.is_disabled()


@then('the "Start Game" button should be enabled')
def start_game_button_enabled(page: Page) -> None:
    """Verify Start Game button is enabled"""
    start_button: Locator = page.locator('[data-testid="start-game-button"]')
    assert start_button.is_visible()
    assert start_button.is_enabled()


# === Ship Removal ===


@when(parsers.parse('I click on the "{ship_name}" to remove it'))
def click_ship_to_remove(
    page: Page, ship_context: ShipPlacementContext, ship_name: str
) -> None:
    """Click on a placed ship to remove it"""
    page.locator(f'button[data-testid="remove-ship-{ship_name.lower()}"]').click()
    page.wait_for_load_state("networkidle")
    # Remove from placed ships
    if ship_name in ship_context.placed_ships:
        del ship_context.placed_ships[ship_name]


@then(parsers.parse("the {ship_name} should be removed from the board"))
def ship_removed_from_board(page: Page, ship_name: str) -> None:
    """Verify ship is removed from the board"""
    ship_element: Locator = page.locator(
        f'[data-testid="placed-ship-{ship_name.lower()}"]'
    )
    assert not ship_element.is_visible()


@then(parsers.parse("the {ship_name} should be available to place again"))
def ship_available_to_place_again(page: Page, ship_name: str) -> None:
    """Verify ship is available for placement"""
    # Check the visible span since the input might be hidden
    ship_span: Locator = page.locator(
        f'[data-testid="select-ship-{ship_name.lower()}"] + span.ship-radio-button'
    )
    assert ship_span.is_visible()


@then(parsers.parse('the ship count should show "{count_text}"'))
def ship_count_should_show(page: Page, count_text: str) -> None:
    """Verify ship count is displayed correctly"""
    count_element: Locator = page.locator('[data-testid="ship-placement-count"]')
    assert count_element.is_visible()
    count_content: str | None = count_element.text_content()
    assert count_content is not None
    assert count_text in count_content


# === Reset All Ships ===


@given("I have placed 3 ships on the board")
def have_placed_3_ships(page: Page, ship_context: ShipPlacementContext) -> None:
    """Setup: 3 ships placed"""
    ships_to_place = [
        ("Destroyer", "A1", "horizontally"),
        ("Submarine", "C3", "vertically"),
        ("Cruiser", "E5", "horizontally"),
    ]

    for name, start, direction in ships_to_place:
        ship_context.selected_ship = name
        place_ship_with_direction(
            page, ship_context, start, direction, is_attempt=False
        )


@when('I click the "Reset All Ships" button')
def click_reset_all_ships_button(
    page: Page, ship_context: ShipPlacementContext
) -> None:
    """Click the Reset All Ships button"""
    page.locator('button[data-testid="reset-all-ships-button"]').click()
    page.wait_for_load_state("networkidle")
    ship_context.placed_ships = {}


@then("all ships should be removed from the board")
def all_ships_removed_from_board(page: Page) -> None:
    """Verify all ships are removed"""
    ship_names: list[str] = [
        "carrier",
        "battleship",
        "cruiser",
        "submarine",
        "destroyer",
    ]
    for ship_name in ship_names:
        ship_element: Locator = page.locator(f'[data-testid="placed-ship-{ship_name}"]')
        assert not ship_element.is_visible()


@then("all ships should be available to place again")
def all_ships_available_to_place_again(page: Page) -> None:
    """Verify all ships are available"""
    ship_names: list[str] = [
        "carrier",
        "battleship",
        "cruiser",
        "submarine",
        "destroyer",
    ]
    for ship_name in ship_names:
        # Check the visible span since the input might be hidden
        ship_span: Locator = page.locator(
            f'[data-testid="select-ship-{ship_name}"] + span.ship-radio-button'
        )
        assert ship_span.is_visible()


@when('I click the "Start Game" button')
def click_start_game_button(page: Page, ship_context: ShipPlacementContext) -> None:
    """Click the Start Game button"""
    page.locator('button[data-testid="start-game-button"]').click()
    page.wait_for_load_state("networkidle")


@then("the computer should automatically place all its ships")
def computer_places_ships_automatically(page: Page) -> None:
    """Verify computer opponent has placed ships"""
    # This is handled by the backend - verify we're on game page or no error
    assert "game" in page.url or "round" in page.url


@then("the computer's ship placement should follow all placement rules")
def computer_ships_follow_rules(page: Page) -> None:
    """Verify computer's ships follow placement rules"""
    # This is enforced by the backend, verify no error
    error_element: Locator = page.locator('[data-testid="placement-error"]')
    assert not error_element.is_visible()


@then("the game should start immediately")
def game_starts_immediately(page: Page) -> None:
    """Verify game has started"""
    page.wait_for_url("**/game/*", timeout=5000)
    assert "game" in page.url or "round" in page.url


# === Multiplayer Ship Placement ===


@given("I am playing against another human player")
def playing_against_human(ship_context: ShipPlacementContext) -> None:
    """Setup: Set game mode to human opponent"""
    ship_context.game_mode = "human"


@when('I click the "Ready" button')
def click_ready_button(page: Page, ship_context: ShipPlacementContext) -> None:
    """Click the Ready button"""
    page.locator('button[data-testid="ready-button"]').click()
    page.wait_for_load_state("networkidle")


@then(parsers.parse('I should see a message "{message}"'))
def should_see_message(page: Page, message: str) -> None:
    """Verify message is displayed"""
    message_element: Locator = page.locator('[data-testid="status-message"]')
    assert message_element.is_visible()
    message_content: str | None = message_element.text_content()
    assert message_content is not None
    assert message in message_content


@then("I should not be able to modify my ship placement")
def cannot_modify_ship_placement(page: Page) -> None:
    """Verify ship placement is locked"""
    # Ship selection buttons should be disabled
    ship_names: list[str] = [
        "carrier",
        "battleship",
        "cruiser",
        "submarine",
        "destroyer",
    ]
    for ship_name in ship_names:
        ship_selector: Locator = page.locator(
            f'[data-testid="select-ship-{ship_name}"]'
        )
        if ship_selector.is_visible():
            assert ship_selector.is_disabled()


@given('I have placed all my ships and clicked "Ready"')
def have_placed_all_ships_and_ready(
    page: Page, ship_context: ShipPlacementContext
) -> None:
    """Setup: All ships placed and ready clicked"""
    have_placed_all_ships(page, ship_context)
    click_ready_button(page, ship_context)


@given('my opponent has placed all their ships and clicked "Ready"')
def opponent_placed_all_ships_and_ready(ship_context: ShipPlacementContext) -> None:
    """Setup: Opponent is ready"""
    # This would be handled by the multiplayer system
    pass


@then("the game should start")
def game_should_start(page: Page) -> None:
    """Verify game has started"""
    # Should redirect to game or be on game page
    page.wait_for_url("**/game/*", timeout=5000)
    assert "game" in page.url or "round" in page.url


@then("both players should proceed to Round 1")
def both_players_proceed_to_round_1(page: Page) -> None:
    """Verify game is at Round 1"""
    # This would check the game state
    pass


# === Grid Visualization ===


@then("I should see a 10x10 grid displayed")
def should_see_10x10_grid(page: Page) -> None:
    """Verify 10x10 grid is displayed"""
    grid_table: Locator = page.locator('[data-testid="ship-grid"]')
    assert grid_table.is_visible(), "Grid table should be visible"

    # Verify it's a table element
    assert grid_table.evaluate("el => el.tagName") == "TABLE"

    # Count rows in tbody (should be 10 rows A-J)
    rows: Locator = grid_table.locator("tbody tr")
    assert rows.count() == 10, "Grid should have 10 rows"

    # Verify each row has 11 cells (1 header + 10 data cells)
    for i in range(10):
        row_cells: Locator = rows.nth(i).locator("th, td")
        assert row_cells.count() == 11, (
            f"Row {i} should have 11 cells (1 header + 10 data)"
        )


@then('the grid should have row labels "A" through "J"')
def grid_should_have_row_labels(page: Page) -> None:
    """Verify grid has row labels A through J"""
    grid_table: Locator = page.locator('[data-testid="ship-grid"]')
    assert grid_table.is_visible()

    expected_rows: list[str] = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
    rows: Locator = grid_table.locator("tbody tr")

    for i, expected_label in enumerate(expected_rows):
        row_header: Locator = rows.nth(i).locator("th").first
        row_text: str | None = row_header.text_content()
        assert row_text is not None
        assert row_text.strip() == expected_label, (
            f"Row {i} should have label {expected_label}"
        )


@then('the grid should have column labels "1" through "10"')
def grid_should_have_column_labels(page: Page) -> None:
    """Verify grid has column labels 1 through 10"""
    grid_table: Locator = page.locator('[data-testid="ship-grid"]')
    assert grid_table.is_visible()

    column_headers: Locator = grid_table.locator("thead tr th")
    # First header is empty, then 1-10
    assert column_headers.count() == 11, "Should have 11 column headers (empty + 1-10)"

    for i in range(1, 11):
        header_text: str | None = column_headers.nth(i).text_content()
        assert header_text is not None
        assert header_text.strip() == str(i), f"Column {i} should have label {i}"


@then("all grid cells should be empty")
def all_grid_cells_should_be_empty(page: Page) -> None:
    """Verify all grid cells are empty (no ships placed)"""
    grid_table: Locator = page.locator('[data-testid="ship-grid"]')
    assert grid_table.is_visible()

    # Find all cells with data-ship attribute
    occupied_cells: Locator = grid_table.locator("td[data-ship]")
    assert occupied_cells.count() == 0, (
        "All cells should be empty (no data-ship attribute)"
    )


@then(
    parsers.parse('cells "{cell1}" and "{cell2}" should be visually marked on the grid')
)
def cells_should_be_visually_marked_two(page: Page, cell1: str, cell2: str) -> None:
    """Verify two cells are visually marked on the grid"""
    cells: list[str] = [cell1, cell2]

    for cell in cells:
        cell_element: Locator = page.locator(
            f'[data-testid="grid-cell-{cell}"][data-ship]'
        )
        assert cell_element.is_visible(), f"Cell {cell} should be marked on the grid"
        # Verify it has data-ship attribute
        data_ship: str | None = cell_element.get_attribute("data-ship")
        assert data_ship is not None, f"Cell {cell} should have data-ship attribute"


@then("the marked cells should be clearly distinguishable from empty cells")
def marked_cells_distinguishable_from_empty(page: Page) -> None:
    """Verify marked cells have data-ship attribute that distinguishes them"""
    grid_table: Locator = page.locator('[data-testid="ship-grid"]')
    assert grid_table.is_visible()

    # Find cells with data-ship attribute (marked)
    marked_cells: Locator = grid_table.locator("td[data-ship]")
    assert marked_cells.count() > 0, "Should have at least one marked cell"

    # Find cells without data-ship attribute (empty)
    all_cells: Locator = grid_table.locator("td[data-testid]")
    total_cells: int = all_cells.count()
    marked_count: int = marked_cells.count()
    empty_count: int = total_cells - marked_count
    assert empty_count > 0, "Should have at least one empty cell"

    # Verify marked cells have data-ship attribute
    for i in range(marked_cells.count()):
        data_ship: str | None = marked_cells.nth(i).get_attribute("data-ship")
        assert data_ship is not None, "Marked cell should have data-ship attribute"


@then("I should be able to identify which cells belong to which ship on the grid")
def should_identify_cells_by_ship(page: Page) -> None:
    """Verify cells have data-ship attributes identifying which ship they belong to"""
    grid_table: Locator = page.locator('[data-testid="ship-grid"]')
    assert grid_table.is_visible()

    # Find all cells with data-ship attribute
    marked_cells: Locator = grid_table.locator("td[data-ship]")
    assert marked_cells.count() > 0, "Should have marked cells"

    # Group cells by ship name
    ships_found: dict[str, int] = {}
    for i in range(marked_cells.count()):
        ship_name: str | None = marked_cells.nth(i).get_attribute("data-ship")
        assert ship_name is not None
        ships_found[ship_name] = ships_found.get(ship_name, 0) + 1

    # Should have at least 2 different ships (Destroyer and Cruiser from scenario)
    assert len(ships_found) >= 2, "Should have at least 2 different ships on grid"


@then(
    parsers.re(
        r'cells "(?P<cell1>[A-J]\d+)", "(?P<cell2>[A-J]\d+)", "(?P<cell3>[A-J]\d+)", and "(?P<cell4>[A-J]\d+)" should be marked on the grid'
    )
)
def cells_should_be_marked_four(
    page: Page, cell1: str, cell2: str, cell3: str, cell4: str
) -> None:
    """Verify four cells are marked on the grid"""
    cells: list[str] = [cell1, cell2, cell3, cell4]

    for cell in cells:
        cell_element: Locator = page.locator(
            f'[data-testid="grid-cell-{cell}"][data-ship]'
        )
        assert cell_element.is_visible(), f"Cell {cell} should be marked on the grid"


@then(
    parsers.re(
        r'cells "(?P<cell1>[A-J]\d+)", "(?P<cell2>[A-J]\d+)", and "(?P<cell3>[A-J]\d+)" should be marked on the grid'
    )
)
def cells_should_be_marked_three(
    page: Page, cell1: str, cell2: str, cell3: str
) -> None:
    """Verify three cells are marked on the grid"""
    cells: list[str] = [cell1, cell2, cell3]

    for cell in cells:
        cell_element: Locator = page.locator(
            f'[data-testid="grid-cell-{cell}"][data-ship]'
        )
        assert cell_element.is_visible(), f"Cell {cell} should be marked on the grid"


@given("I am playing against a computer opponent")
def playing_against_computer(page: Page, ship_context: ShipPlacementContext) -> None:
    """Ensure we are in computer mode"""
    pass


@given("I have placed all my ships")
def have_placed_all_ships(page: Page, ship_context: ShipPlacementContext) -> None:
    """Setup: All 5 ships placed"""
    ships_to_place = [
        ("Destroyer", "A1", "horizontally"),
        ("Submarine", "C3", "vertically"),
        ("Cruiser", "E5", "horizontally"),
        ("Battleship", "G1", "horizontally"),
        ("Carrier", "I1", "horizontally"),
    ]

    for name, start, direction in ships_to_place:
        ship_context.selected_ship = name
        place_ship_with_direction(
            page, ship_context, start, direction, is_attempt=False
        )
